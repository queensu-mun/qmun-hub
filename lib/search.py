"""Hybrid search: vector (SQLite-vec) + keyword (BM25).

Stub for May scaffolding. Full implementation lands in Phase 1.3.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

DocType = Literal["position_paper", "study_guide", "alumni_interview", "director_note", "background_guide", "training"]


@dataclass
class SearchHit:
    doc_id: str
    chunk_id: str
    title: str
    snippet: str
    score: float
    doc_type: DocType
    year: int | None
    metadata: dict


def hybrid_search(
    query: str,
    *,
    top_k: int = 20,
    doc_types: list[DocType] | None = None,
    year: int | None = None,
    exec_visible: bool = False,
) -> list[SearchHit]:
    raise NotImplementedError("Phase 1.3")
