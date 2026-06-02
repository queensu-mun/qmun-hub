"""Hybrid search: vector cosine (Voyage embeddings) + BM25 keyword.

For our scale (target ~500-2000 chunks), brute-force numpy cosine is fast enough.
Hybrid score = alpha * cosine_normalized + (1 - alpha) * bm25_normalized.
"""
from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from typing import Literal

import numpy as np
from rank_bm25 import BM25Okapi

from lib.index import IndexedChunk, embed_batch, load_all_chunks

DocType = Literal[
    "position_paper", "study_guide", "alumni_interview",
    "director_note", "background_guide", "training", "misc",
]


@dataclass
class SearchHit:
    chunk_id: str
    doc_id: str
    doc_title: str
    doc_type: str
    year: int | None
    snippet: str
    score: float
    vector_score: float
    bm25_score: float
    quality_flag: str | None


_TOKEN_RE = __import__("re").compile(r"[A-Za-z0-9]+")


def _tokenize(text: str) -> list[str]:
    return [t.lower() for t in _TOKEN_RE.findall(text)]


@lru_cache(maxsize=1)
def _build_bm25_state() -> tuple[list[IndexedChunk], BM25Okapi, np.ndarray]:
    """Cache index in memory. Invalidated by clear_cache()."""
    chunks = load_all_chunks()
    if not chunks:
        return [], BM25Okapi([[""]]), np.zeros((0, 1024), dtype=np.float32)
    tokenized = [_tokenize(c.text) for c in chunks]
    bm25 = BM25Okapi(tokenized)
    matrix = np.stack([c.embedding for c in chunks])
    # Normalize for cosine
    norms = np.linalg.norm(matrix, axis=1, keepdims=True)
    matrix = matrix / np.clip(norms, 1e-8, None)
    return chunks, bm25, matrix


def clear_cache() -> None:
    _build_bm25_state.cache_clear()


def hybrid_search(
    query: str,
    *,
    top_k: int = 20,
    alpha: float = 0.6,
    doc_types: list[str] | None = None,
    year: int | None = None,
    exec_visible: bool = False,
) -> list[SearchHit]:
    """alpha = vector weight (0=pure BM25, 1=pure vector). Default 0.6 favors semantic."""
    chunks, bm25, matrix = _build_bm25_state()
    if not chunks:
        return []

    # Vector score
    q_emb_list, _ = embed_batch([query], input_type="query")
    q_emb = q_emb_list[0]
    q_emb = q_emb / max(float(np.linalg.norm(q_emb)), 1e-8)
    vec_scores = matrix @ q_emb  # cosine since both normalized; range [-1, 1]
    vec_scores = (vec_scores + 1.0) / 2.0  # to [0, 1]

    # BM25 score
    bm_scores = np.array(bm25.get_scores(_tokenize(query)), dtype=np.float32)
    bm_max = float(bm_scores.max()) if bm_scores.size else 0.0
    if bm_max > 0:
        bm_scores = bm_scores / bm_max  # to [0, 1]

    # Combine
    combined = alpha * vec_scores + (1.0 - alpha) * bm_scores

    # Quality flag boosts
    for i, c in enumerate(chunks):
        if c.quality_flag == "exemplary":
            combined[i] *= 1.15
        elif c.quality_flag == "outdated":
            combined[i] *= 0.6

    # Filters
    keep = np.ones(len(chunks), dtype=bool)
    for i, c in enumerate(chunks):
        if doc_types and c.doc_type not in doc_types:
            keep[i] = False
            continue
        if year is not None and c.year != year:
            keep[i] = False
            continue
        if not exec_visible and c.visibility == "exec_only":
            keep[i] = False

    combined[~keep] = -1.0

    # Top-k by chunk, then dedupe to one hit per doc (keep highest-scoring chunk per doc)
    order = np.argsort(-combined)
    seen_docs: set[str] = set()
    hits: list[SearchHit] = []
    for idx in order:
        if combined[idx] < 0:
            break
        c = chunks[int(idx)]
        if c.doc_id in seen_docs:
            continue
        seen_docs.add(c.doc_id)
        hits.append(SearchHit(
            chunk_id=c.chunk_id,
            doc_id=c.doc_id,
            doc_title=c.doc_title,
            doc_type=c.doc_type,
            year=c.year,
            snippet=_make_snippet(c.text, query),
            score=float(combined[int(idx)]),
            vector_score=float(vec_scores[int(idx)]),
            bm25_score=float(bm_scores[int(idx)]) if bm_scores.size else 0.0,
            quality_flag=c.quality_flag,
        ))
        if len(hits) >= top_k:
            break
    return hits


@dataclass
class Passage:
    doc_id: str
    doc_title: str
    doc_type: str
    text: str


def retrieve_passages(
    query: str,
    *,
    doc_types: list[str] | None = None,
    top_k: int = 4,
    alpha: float = 0.6,
    exec_visible: bool = True,
) -> list[Passage]:
    """Top matching chunks with FULL text, for feeding RAG context into the
    mentor / brief generators (not the browse UI). Unlike hybrid_search this
    does NOT dedupe per doc, so multiple strong passages from one rich interview
    can all surface.
    """
    chunks, bm25, matrix = _build_bm25_state()
    if not chunks:
        return []

    q_emb_list, _ = embed_batch([query], input_type="query")
    q_emb = q_emb_list[0]
    q_emb = q_emb / max(float(np.linalg.norm(q_emb)), 1e-8)
    vec_scores = (matrix @ q_emb + 1.0) / 2.0

    bm_scores = np.array(bm25.get_scores(_tokenize(query)), dtype=np.float32)
    bm_max = float(bm_scores.max()) if bm_scores.size else 0.0
    if bm_max > 0:
        bm_scores = bm_scores / bm_max

    combined = alpha * vec_scores + (1.0 - alpha) * bm_scores

    keep = np.ones(len(chunks), dtype=bool)
    for i, c in enumerate(chunks):
        if doc_types and c.doc_type not in doc_types:
            keep[i] = False
            continue
        if not exec_visible and c.visibility == "exec_only":
            keep[i] = False
    combined[~keep] = -1.0

    order = np.argsort(-combined)
    out: list[Passage] = []
    for idx in order:
        if combined[int(idx)] < 0:
            break
        c = chunks[int(idx)]
        out.append(Passage(c.doc_id, c.doc_title, c.doc_type, c.text))
        if len(out) >= top_k:
            break
    return out


def _make_snippet(text: str, query: str, *, target_chars: int = 280) -> str:
    """Find first occurrence of any query token; return surrounding window."""
    tokens = _tokenize(query)
    lower = text.lower()
    pos = -1
    for t in tokens:
        p = lower.find(t)
        if p != -1 and (pos == -1 or p < pos):
            pos = p
    if pos == -1:
        return text[:target_chars] + ("..." if len(text) > target_chars else "")
    start = max(0, pos - target_chars // 3)
    end = min(len(text), start + target_chars)
    snippet = text[start:end]
    if start > 0:
        snippet = "..." + snippet
    if end < len(text):
        snippet = snippet + "..."
    return snippet
