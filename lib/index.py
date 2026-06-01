"""Indexing pipeline: chunk, embed (Voyage), store in SQLite + numpy.

Storage strategy: SQLite for chunk text + metadata; embeddings as numpy float32
BLOBs in the same row. At our scale (target ~500-2000 chunks), brute-force cosine
in numpy is millisecond-fast and avoids the sqlite-vec compilation headache on
macOS LibreSSL builds.
"""
from __future__ import annotations

import json
import os
import re
import sqlite3
import time
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime
from functools import lru_cache
from pathlib import Path
from typing import Iterable

import numpy as np
import voyageai

from lib import store

ROOT = Path(__file__).resolve().parent.parent
DB_PATH = ROOT / "data" / "archive.db"
EMBED_MODEL = "voyage-3"
EMBED_DIM = 1024

# Postgres table names in Supabase mode (see scripts/supabase_schema.sql).
SB_DOCS = "archive_docs"
SB_CHUNKS = "archive_chunks"

SCHEMA = """
CREATE TABLE IF NOT EXISTS docs (
    doc_id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    source TEXT NOT NULL,
    doc_type TEXT NOT NULL,
    year INTEGER,
    metadata TEXT NOT NULL,
    indexed_at TEXT NOT NULL,
    visibility TEXT NOT NULL DEFAULT 'team',
    quality_flag TEXT
);

CREATE TABLE IF NOT EXISTS chunks (
    chunk_id TEXT PRIMARY KEY,
    doc_id TEXT NOT NULL,
    ord INTEGER NOT NULL,
    text TEXT NOT NULL,
    token_estimate INTEGER NOT NULL,
    embedding BLOB NOT NULL,
    FOREIGN KEY (doc_id) REFERENCES docs(doc_id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_chunks_doc ON chunks(doc_id);
"""


@dataclass
class Doc:
    doc_id: str
    title: str
    source: str          # e.g. drive_id, local_path, alumni_interview_uuid
    doc_type: str        # position_paper | study_guide | alumni_interview | director_note | background_guide | training | misc
    text: str
    year: int | None = None
    metadata: dict = field(default_factory=dict)
    visibility: str = "team"     # team | exec_only
    quality_flag: str | None = None  # exemplary | outdated | None


@dataclass
class Chunk:
    chunk_id: str
    doc_id: str
    ord: int
    text: str
    token_estimate: int


@contextmanager
def _conn():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    try:
        conn.executescript(SCHEMA)
        yield conn
        conn.commit()
    finally:
        conn.close()


# --------------------------- Supabase backend ---------------------------
# In Supabase mode the archive lives in Postgres so docs indexed after deploy
# (alumni interviews, director uploads) survive the ephemeral filesystem.
# Embeddings are stored as jsonb float arrays; search is still the in-memory
# hybrid (BM25 + numpy cosine) in lib/search.py, so pgvector is unnecessary at
# this scale and would not help the keyword half of the fusion anyway.

def _supabase() -> bool:
    return store.backend() == "supabase"


def _sb_fetch_all(table: str, *, columns: str = "*", order: str | None = None) -> list[dict]:
    """Page through a table 1000 rows at a time (PostgREST's default cap)."""
    client = store._client()
    rows: list[dict] = []
    start, step = 0, 1000
    while True:
        q = client.table(table).select(columns)
        if order:
            q = q.order(order)
        batch = q.range(start, start + step - 1).execute().data or []
        rows.extend(batch)
        if len(batch) < step:
            return rows
        start += step


@lru_cache(maxsize=1)
def _voyage_key() -> str:
    if env := os.environ.get("VOYAGE_API_KEY"):
        return env
    try:
        import streamlit as st
        return st.secrets["voyage"]["api_key"]
    except Exception:
        pass
    secrets_path = ROOT / ".streamlit" / "secrets.toml"
    import toml
    return toml.load(secrets_path)["voyage"]["api_key"]


@lru_cache(maxsize=1)
def _voyage_client() -> voyageai.Client:
    return voyageai.Client(api_key=_voyage_key())


# ----------------------------- Chunking -----------------------------

_PARA_SPLIT = re.compile(r"\n\s*\n")


def chunk_text(text: str, *, target_tokens: int = 600, overlap_tokens: int = 80) -> list[str]:
    """Paragraph-aware sliding window. Token estimate = chars / 4 (rough)."""
    text = text.strip()
    if not text:
        return []
    paragraphs = [p.strip() for p in _PARA_SPLIT.split(text) if p.strip()]
    target_chars = target_tokens * 4
    overlap_chars = overlap_tokens * 4

    chunks: list[str] = []
    cur: list[str] = []
    cur_chars = 0
    for p in paragraphs:
        if cur_chars + len(p) <= target_chars:
            cur.append(p)
            cur_chars += len(p) + 2
            continue
        # Flush current
        if cur:
            chunks.append("\n\n".join(cur))
        # Start new chunk, carrying overlap from end of previous
        if chunks and overlap_chars > 0:
            tail = chunks[-1][-overlap_chars:]
            cur = [tail, p]
            cur_chars = len(tail) + len(p) + 2
        else:
            cur = [p]
            cur_chars = len(p)
        # If single paragraph too long, hard-split it
        if len(p) > target_chars * 1.5:
            chunks[-1] if chunks else None
            sub = [p[i : i + target_chars] for i in range(0, len(p), target_chars - overlap_chars)]
            chunks.extend(sub[:-1])
            cur = [sub[-1]]
            cur_chars = len(sub[-1])
    if cur:
        chunks.append("\n\n".join(cur))
    return chunks


def _token_estimate(text: str) -> int:
    return max(1, len(text) // 4)


# ----------------------------- Embeddings -----------------------------


# Voyage free tier: 3 RPM / 10K TPM. The TPM limit is the binding constraint.
# Set VOYAGE_PAID=1 to disable throttling once a payment method is added.
_FREE_TIER_BATCH = 8          # ~4800 tokens per batch, leaves headroom for variability
_FREE_TIER_INTERVAL_S = 32.0  # 2 batches/min = ~9600 tokens/min, just under 10K TPM
_PAID_TIER_BATCH = 64
_PAID_TIER_INTERVAL_S = 0.0


def _is_paid_tier() -> bool:
    return bool(os.environ.get("VOYAGE_PAID"))


_last_call_at: float = 0.0


def embed_batch(texts: list[str], *, input_type: str = "document") -> tuple[list[np.ndarray], int]:
    """Returns (embeddings, total_tokens). Throttled for Voyage free tier."""
    global _last_call_at
    client = _voyage_client()
    paid = _is_paid_tier()
    batch_size = _PAID_TIER_BATCH if paid else _FREE_TIER_BATCH
    interval = _PAID_TIER_INTERVAL_S if paid else _FREE_TIER_INTERVAL_S

    all_embs: list[np.ndarray] = []
    total = 0
    for i in range(0, len(texts), batch_size):
        if interval > 0 and _last_call_at:
            wait = interval - (time.time() - _last_call_at)
            if wait > 0:
                time.sleep(wait)
        batch = texts[i : i + batch_size]
        resp = client.embed(batch, model=EMBED_MODEL, input_type=input_type)
        _last_call_at = time.time()
        all_embs.extend(np.array(e, dtype=np.float32) for e in resp.embeddings)
        total += resp.total_tokens
    return all_embs, total


# ----------------------------- Persist -----------------------------


def upsert_doc(doc: Doc) -> int:
    """Index or re-index a doc. Returns number of chunks created."""
    chunks = chunk_text(doc.text)
    if not chunks:
        return 0
    embeddings, _tokens = embed_batch(chunks, input_type="document")
    indexed_at = datetime.utcnow().isoformat()

    if _supabase():
        client = store._client()
        # Re-index = replace: drop old chunks, upsert the doc, insert fresh chunks.
        client.table(SB_CHUNKS).delete().eq("doc_id", doc.doc_id).execute()
        client.table(SB_DOCS).upsert(
            {
                "doc_id": doc.doc_id, "title": doc.title, "source": doc.source,
                "doc_type": doc.doc_type, "year": doc.year, "metadata": doc.metadata,
                "indexed_at": indexed_at, "visibility": doc.visibility,
                "quality_flag": doc.quality_flag,
            },
            on_conflict="doc_id",
        ).execute()
        rows = [
            {
                "chunk_id": f"{doc.doc_id}::{i}", "doc_id": doc.doc_id, "ord": i,
                "text": text, "token_estimate": _token_estimate(text),
                "embedding": emb.tolist(),
            }
            for i, (text, emb) in enumerate(zip(chunks, embeddings))
        ]
        for j in range(0, len(rows), 200):  # keep request payloads modest
            client.table(SB_CHUNKS).insert(rows[j : j + 200]).execute()
        return len(chunks)

    with _conn() as c:
        c.execute("DELETE FROM chunks WHERE doc_id = ?", (doc.doc_id,))
        c.execute(
            "INSERT OR REPLACE INTO docs "
            "(doc_id, title, source, doc_type, year, metadata, indexed_at, visibility, quality_flag) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                doc.doc_id, doc.title, doc.source, doc.doc_type, doc.year,
                json.dumps(doc.metadata), indexed_at,
                doc.visibility, doc.quality_flag,
            ),
        )
        for i, (text, emb) in enumerate(zip(chunks, embeddings)):
            chunk_id = f"{doc.doc_id}::{i}"
            c.execute(
                "INSERT INTO chunks (chunk_id, doc_id, ord, text, token_estimate, embedding) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (chunk_id, doc.doc_id, i, text, _token_estimate(text), emb.tobytes()),
            )
    return len(chunks)


# ----------------------------- Read -----------------------------


@dataclass
class IndexedChunk:
    chunk_id: str
    doc_id: str
    ord: int
    text: str
    embedding: np.ndarray
    doc_title: str
    doc_type: str
    year: int | None
    visibility: str
    quality_flag: str | None
    metadata: dict


def load_all_chunks() -> list[IndexedChunk]:
    if _supabase():
        docs = {d["doc_id"]: d for d in _sb_fetch_all(SB_DOCS)}
        out: list[IndexedChunk] = []
        for r in _sb_fetch_all(SB_CHUNKS):
            d = docs.get(r["doc_id"])
            if not d:
                continue
            out.append(IndexedChunk(
                chunk_id=r["chunk_id"], doc_id=r["doc_id"], ord=r["ord"], text=r["text"],
                embedding=np.array(r["embedding"], dtype=np.float32),
                doc_title=d["title"], doc_type=d["doc_type"], year=d.get("year"),
                visibility=d.get("visibility", "team"), quality_flag=d.get("quality_flag"),
                metadata=d.get("metadata") or {},
            ))
        return out

    with _conn() as c:
        rows = c.execute(
            "SELECT c.chunk_id, c.doc_id, c.ord, c.text, c.embedding, "
            "d.title, d.doc_type, d.year, d.visibility, d.quality_flag, d.metadata "
            "FROM chunks c JOIN docs d ON d.doc_id = c.doc_id"
        ).fetchall()
    out: list[IndexedChunk] = []
    for r in rows:
        emb = np.frombuffer(r[4], dtype=np.float32)
        out.append(IndexedChunk(
            chunk_id=r[0], doc_id=r[1], ord=r[2], text=r[3], embedding=emb,
            doc_title=r[5], doc_type=r[6], year=r[7],
            visibility=r[8], quality_flag=r[9],
            metadata=json.loads(r[10]) if r[10] else {},
        ))
    return out


def list_docs() -> list[dict]:
    if _supabase():
        from collections import Counter

        counts = Counter(r["doc_id"] for r in _sb_fetch_all(SB_CHUNKS, columns="doc_id"))
        docs = _sb_fetch_all(SB_DOCS)
        docs.sort(key=lambda d: d.get("indexed_at") or "", reverse=True)
        return [
            {
                "doc_id": d["doc_id"], "title": d["title"], "doc_type": d["doc_type"],
                "year": d.get("year"), "visibility": d.get("visibility", "team"),
                "quality_flag": d.get("quality_flag"), "indexed_at": d.get("indexed_at"),
                "source": d.get("source"), "chunk_count": counts.get(d["doc_id"], 0),
            }
            for d in docs
        ]

    with _conn() as c:
        rows = c.execute(
            "SELECT d.doc_id, d.title, d.doc_type, d.year, d.visibility, d.quality_flag, "
            "d.indexed_at, d.source, COUNT(c.chunk_id) "
            "FROM docs d LEFT JOIN chunks c ON c.doc_id = d.doc_id "
            "GROUP BY d.doc_id ORDER BY d.indexed_at DESC"
        ).fetchall()
    return [
        {
            "doc_id": r[0], "title": r[1], "doc_type": r[2], "year": r[3],
            "visibility": r[4], "quality_flag": r[5],
            "indexed_at": r[6], "source": r[7], "chunk_count": r[8],
        }
        for r in rows
    ]


def doc_text(doc_id: str) -> str | None:
    """Reassemble the full text of a doc from its chunks (for inline view)."""
    if _supabase():
        rows = (
            store._client().table(SB_CHUNKS)
            .select("text").eq("doc_id", doc_id).order("ord").execute().data or []
        )
        return "\n\n".join(r["text"] for r in rows) if rows else None

    with _conn() as c:
        rows = c.execute(
            "SELECT text FROM chunks WHERE doc_id = ? ORDER BY ord", (doc_id,)
        ).fetchall()
    if not rows:
        return None
    return "\n\n".join(r[0] for r in rows)


def delete_doc(doc_id: str) -> None:
    if _supabase():
        client = store._client()
        client.table(SB_CHUNKS).delete().eq("doc_id", doc_id).execute()
        client.table(SB_DOCS).delete().eq("doc_id", doc_id).execute()
        return
    with _conn() as c:
        c.execute("DELETE FROM chunks WHERE doc_id = ?", (doc_id,))
        c.execute("DELETE FROM docs WHERE doc_id = ?", (doc_id,))


def update_doc_curation(doc_id: str, *, quality_flag: str | None, visibility: str) -> None:
    """Update a doc's quality flag + visibility (the Director curation controls)."""
    if _supabase():
        store._client().table(SB_DOCS).update(
            {"quality_flag": quality_flag, "visibility": visibility}
        ).eq("doc_id", doc_id).execute()
        return
    with _conn() as c:
        c.execute(
            "UPDATE docs SET quality_flag = ?, visibility = ? WHERE doc_id = ?",
            (quality_flag, visibility, doc_id),
        )


def index_stats() -> dict:
    if _supabase():
        from collections import Counter

        docs = _sb_fetch_all(SB_DOCS, columns="doc_type")
        n_chunks = (
            store._client().table(SB_CHUNKS)
            .select("chunk_id", count="exact").limit(1).execute().count or 0
        )
        return {
            "n_docs": len(docs),
            "n_chunks": n_chunks,
            "by_type": dict(Counter(d["doc_type"] for d in docs)),
        }

    with _conn() as c:
        n_docs = c.execute("SELECT COUNT(*) FROM docs").fetchone()[0]
        n_chunks = c.execute("SELECT COUNT(*) FROM chunks").fetchone()[0]
        by_type = dict(c.execute(
            "SELECT doc_type, COUNT(*) FROM docs GROUP BY doc_type"
        ).fetchall())
    return {"n_docs": n_docs, "n_chunks": n_chunks, "by_type": by_type}
