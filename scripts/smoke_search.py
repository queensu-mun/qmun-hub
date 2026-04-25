"""Smoke test the hybrid search backend against the current index."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from lib.search import hybrid_search  # noqa: E402

queries = [
    "what should I do in unmoderated caucus",
    "how to write a strong opening speech",
    "research framework for a country position",
    "social culture of the team and going to the bar",
    "crisis committee directives",
]

for q in queries:
    print(f"\n=== {q} ===")
    hits = hybrid_search(q, top_k=3, exec_visible=True)
    if not hits:
        print("  (no hits)")
        continue
    for h in hits:
        print(f"  [{h.score:.2f}] {h.doc_title} (vec={h.vector_score:.2f}, bm25={h.bm25_score:.2f})")
        print(f"    {h.snippet[:200]}")
