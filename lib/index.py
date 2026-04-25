"""Indexing pipeline: chunk -> embed (Voyage) -> SQLite-vec upsert.

Stub for May scaffolding. Full implementation lands in Phase 1.3.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

DB_PATH = Path("data/archive.db")


@dataclass
class Chunk:
    doc_id: str
    chunk_id: str
    text: str
    metadata: dict


def init_db() -> None:
    raise NotImplementedError("Phase 1.3")


def chunk_doc(text: str, *, target_tokens: int = 600, overlap: int = 80) -> list[str]:
    raise NotImplementedError("Phase 1.3")


def embed_batch(texts: list[str]) -> list[list[float]]:
    raise NotImplementedError("Phase 1.3 — needs Voyage API key")


def upsert_chunks(chunks: list[Chunk]) -> int:
    raise NotImplementedError("Phase 1.3")
