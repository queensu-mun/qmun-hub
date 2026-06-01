"""Generic folder ingester: drop docs in a folder, index them in one command.

The seed list (scripts/seed_archive.py) is a hardcoded, curated set. This script
is the everyday path for adding real material before Google Drive sync is wired:
point it at any folder of .md / .pdf / .docx files and it chunks, embeds, and
upserts each one into the archive. It honours whichever backend is active, so on
a deployed (Supabase) setup it writes straight to Postgres.

    cd ~/qmun-hub && source .venv/bin/activate
    python scripts/ingest_folder.py data/incoming
    python scripts/ingest_folder.py data/incoming --doc-type position_paper --year 2026

doc_id is derived from the filename (stable, so re-running re-indexes in place
rather than duplicating). doc_type defaults by extension and can be overridden:
  .pdf  -> background_guide
  .docx -> position_paper
  .md   -> training
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from lib import store  # noqa: E402
from lib.index import Doc, index_stats, upsert_doc  # noqa: E402

_DATA_URI_IMG = re.compile(r"!\[[^\]]*\]\(data:image/[^)]+\)")
_INLINE_DATA_URI = re.compile(r"data:image/[^\s\)]+")

DOC_TYPE_BY_EXT = {".pdf": "background_guide", ".docx": "position_paper", ".md": "training"}
VALID_DOC_TYPES = {
    "position_paper", "study_guide", "alumni_interview",
    "director_note", "background_guide", "training", "misc",
}


def _slug(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")


def clean_markdown(text: str) -> str:
    text = _DATA_URI_IMG.sub("", text)
    text = _INLINE_DATA_URI.sub("", text)
    text = re.sub(r"\n{4,}", "\n\n\n", text)
    return text.strip()


def extract_pdf(path: Path) -> str:
    from pypdf import PdfReader

    reader = PdfReader(str(path))
    pages = []
    for p in reader.pages:
        try:
            pages.append(p.extract_text() or "")
        except Exception as e:
            pages.append(f"[page extract failed: {e}]")
    return "\n\n".join(pages).strip()


def extract_docx(path: Path) -> str:
    from docx import Document

    doc = Document(str(path))
    return "\n\n".join(p.text for p in doc.paragraphs if p.text.strip()).strip()


def extract(path: Path) -> str:
    ext = path.suffix.lower()
    if ext == ".md":
        return clean_markdown(path.read_text())
    if ext == ".pdf":
        return extract_pdf(path)
    if ext == ".docx":
        return extract_docx(path)
    raise ValueError(f"unsupported extension: {ext}")


def main() -> int:
    ap = argparse.ArgumentParser(description="Index a folder of docs into the QMUN archive.")
    ap.add_argument("folder", help="Folder containing .md / .pdf / .docx files")
    ap.add_argument("--doc-type", choices=sorted(VALID_DOC_TYPES), default=None,
                    help="Override doc_type for all files (else inferred by extension)")
    ap.add_argument("--year", type=int, default=None, help="Year metadata for all files")
    ap.add_argument("--prefix", default="ingest", help="doc_id prefix (default: ingest)")
    args = ap.parse_args()

    folder = Path(args.folder)
    if not folder.is_dir():
        print(f"Not a folder: {folder}")
        return 1

    files = sorted(
        p for p in folder.iterdir()
        if p.is_file() and p.suffix.lower() in DOC_TYPE_BY_EXT
    )
    if not files:
        print(f"No .md / .pdf / .docx files in {folder}")
        return 1

    print(f"Backend: {store.backend()}  |  {len(files)} file(s) in {folder}\n")
    total_chunks = 0
    for path in files:
        try:
            text = extract(path)
        except Exception as e:
            print(f"  SKIP {path.name}: extract failed ({e})")
            continue
        if not text.strip():
            print(f"  SKIP {path.name}: empty after extract")
            continue

        doc_type = args.doc_type or DOC_TYPE_BY_EXT[path.suffix.lower()]
        doc = Doc(
            doc_id=f"{args.prefix}_{_slug(path.stem)}",
            title=path.stem.replace("_", " ").strip(),
            source=str(path),
            doc_type=doc_type,
            text=text,
            year=args.year,
            metadata={"ingested_from": path.name},
        )
        n = upsert_doc(doc)
        total_chunks += n
        print(f"  indexed {path.name}  ->  {doc.doc_id}  ({n} chunks, {doc_type})")

    stats = index_stats()
    print(f"\nDone. +{total_chunks} chunks. Archive now: "
          f"{stats['n_docs']} docs / {stats['n_chunks']} chunks.")
    print("Note: in local mode, commit data/archive.db so the deploy ships the new docs,")
    print("      or re-run this against the deployed (Supabase) backend.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
