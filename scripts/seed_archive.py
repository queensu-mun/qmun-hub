"""One-time seed: index Art of MUN, MUN Claude self-interview, and 3 background guides
that we already pulled from Drive into data/seed/.

Re-runnable; upserts on doc_id.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from lib.index import Doc, index_stats, upsert_doc  # noqa: E402

SEED = ROOT / "data" / "seed"

# Strip base64-encoded image data URIs that bloat markdown exports
_DATA_URI_IMG = re.compile(r"!\[[^\]]*\]\(data:image/[^)]+\)")
_INLINE_DATA_URI = re.compile(r"data:image/[^\s\)]+")


def clean_markdown(text: str) -> str:
    text = _DATA_URI_IMG.sub("", text)
    text = _INLINE_DATA_URI.sub("", text)
    # Collapse runs of blank lines
    text = re.sub(r"\n{4,}", "\n\n\n", text)
    return text.strip()


def extract_pdf(path: Path) -> str:
    from pypdf import PdfReader
    reader = PdfReader(str(path))
    pages = []
    for p in reader.pages:
        try:
            t = p.extract_text() or ""
        except Exception as e:
            t = f"[page extract failed: {e}]"
        pages.append(t)
    return "\n\n".join(pages).strip()


SOURCES = [
    {
        "doc_id": "seed_art_of_mun_25_26",
        "title": "The Art of MUN (25-26)",
        "doc_type": "training",
        "year": 2025,
        "path": SEED / "art_of_mun_25_26.md",
        "kind": "markdown",
        "metadata": {
            "author": "Russell Van Raalte (23/24), edited by Jake Louhikari, Jack Guillemette, Savannah Summers",
            "scope": "Full delegate handbook: parli pro, position papers, draft resolutions, crisis, SAs",
        },
        "quality_flag": "exemplary",
    },
    {
        "doc_id": "seed_mun_claude_self_interview",
        "title": "MUN Claude · Jack's self-interview (institutional knowledge intake)",
        "doc_type": "alumni_interview",
        "year": 2026,
        "path": SEED / "mun_claude_self_interview.md",
        "kind": "markdown",
        "metadata": {
            "author": "Jack Guillemette",
            "scope": "Filled-out version of the alumni interview template; covers team prep timeline, research framework, mock cadence, social culture",
        },
        "quality_flag": "exemplary",
    },
    {
        "doc_id": "seed_hrc_bg",
        "title": "HRC Background Guide",
        "doc_type": "background_guide",
        "year": 2020,
        "path": SEED / "HRC_background_guide.pdf",
        "kind": "pdf",
        "metadata": {"committee": "Human Rights Council"},
    },
    {
        "doc_id": "seed_global_commission_prisoners_bg",
        "title": "Global Commission on the Rights of Prisoners · Background Guide",
        "doc_type": "background_guide",
        "year": 2022,
        "path": SEED / "global_commission_prisoners_rights_bg.pdf",
        "kind": "pdf",
        "metadata": {"committee": "Global Commission on the Rights of Prisoners"},
    },
    {
        "doc_id": "seed_sdg4_sochum_bg",
        "title": "SDG 4 · Quality Education (SOCHUM) Background Guide",
        "doc_type": "background_guide",
        "year": 2019,
        "path": SEED / "SDG4_quality_education_SOCHUM.pdf",
        "kind": "pdf",
        "metadata": {"committee": "SOCHUM", "topic": "SDG 4 - Quality Education"},
    },
    {
        "doc_id": "seed_parli_pro_cheatsheet",
        "title": "Parliamentary Procedure Cheat Sheet",
        "doc_type": "training",
        "year": 2026,
        "path": SEED / "parli_pro_cheatsheet.md",
        "kind": "markdown",
        "metadata": {"scope": "Quick reference: points, motions, yields, voting thresholds"},
        "quality_flag": "exemplary",
    },
    {
        "doc_id": "seed_awards_rubric",
        "title": "Awards Rubric (North American Collegiate Circuit)",
        "doc_type": "training",
        "year": 2026,
        "path": SEED / "awards_rubric.md",
        "kind": "markdown",
        "metadata": {"scope": "What chairs evaluate; conference-specific weighting; what wins and loses awards"},
        "quality_flag": "exemplary",
    },
]


def main() -> int:
    total_chunks = 0
    for src in SOURCES:
        path: Path = src["path"]
        if not path.exists():
            print(f"  SKIP (missing): {path}")
            continue
        if src["kind"] == "markdown":
            text = clean_markdown(path.read_text())
        elif src["kind"] == "pdf":
            text = extract_pdf(path)
        else:
            raise ValueError(src["kind"])

        if not text.strip():
            print(f"  SKIP (empty after extract): {src['title']}")
            continue

        doc = Doc(
            doc_id=src["doc_id"],
            title=src["title"],
            source=str(path.relative_to(ROOT)),
            doc_type=src["doc_type"],
            year=src.get("year"),
            text=text,
            metadata=src.get("metadata", {}),
            visibility="team",
            quality_flag=src.get("quality_flag"),
        )
        n = upsert_doc(doc)
        total_chunks += n
        print(f"  INDEXED: {src['title']:60s} {n:4d} chunks  ({len(text):>8} chars)")

    stats = index_stats()
    print(f"\nTotal chunks across index: {stats['n_chunks']} ({stats['n_docs']} docs)")
    print(f"By type: {stats['by_type']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
