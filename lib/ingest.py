"""Folder ingestion: extract, chunk, embed, upsert every doc in a folder.

Shared by two callers:
- scripts/ingest_folder.py (the original CLI path)
- the Director -> Curation "Reindex archive" button, so newly uploaded docs
  become searchable without SSH.

doc_id is derived from the filename (stable, so re-running re-indexes in place
rather than duplicating). doc_type defaults by extension and can be overridden:
  .pdf  -> background_guide
  .docx -> position_paper
  .md   -> training
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Callable

from lib.index import Doc, index_stats, upsert_doc

ROOT = Path(__file__).resolve().parent.parent
INCOMING_DIR = ROOT / "data" / "incoming"

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


def ingest_folder(
    folder: Path | str,
    *,
    doc_type: str | None = None,
    year: int | None = None,
    prefix: str = "ingest",
    log: Callable[[str], None] | None = None,
) -> dict:
    """Index every supported file in `folder`. Honours the active backend
    (local SQLite or Supabase), same as lib/index.upsert_doc.

    Returns a result dict:
      indexed:      [{file, doc_id, chunks, doc_type}]
      skipped:      [(filename, reason)]
      errors:       [str]
      total_chunks: int
      stats:        index_stats() after the run (None if nothing ran)
    """
    log = log or (lambda msg: None)
    folder = Path(folder)
    result: dict = {"indexed": [], "skipped": [], "errors": [], "total_chunks": 0, "stats": None}

    if not folder.is_dir():
        result["errors"].append(f"Not a folder: {folder}")
        return result
    files = sorted(
        p for p in folder.iterdir()
        if p.is_file() and p.suffix.lower() in DOC_TYPE_BY_EXT
    )
    if not files:
        result["errors"].append(f"No .md / .pdf / .docx files in {folder}")
        return result

    for path in files:
        try:
            text = extract(path)
        except Exception as e:
            result["skipped"].append((path.name, f"extract failed ({e})"))
            log(f"SKIP {path.name}: extract failed ({e})")
            continue
        if not text.strip():
            result["skipped"].append((path.name, "empty after extract"))
            log(f"SKIP {path.name}: empty after extract")
            continue

        dt = doc_type or DOC_TYPE_BY_EXT[path.suffix.lower()]
        doc = Doc(
            doc_id=f"{prefix}_{_slug(path.stem)}",
            title=path.stem.replace("_", " ").strip(),
            source=str(path),
            doc_type=dt,
            text=text,
            year=year,
            metadata={"ingested_from": path.name},
        )
        try:
            n = upsert_doc(doc)
        except Exception as e:
            result["errors"].append(f"{path.name}: index failed ({e})")
            log(f"ERROR {path.name}: index failed ({e})")
            continue
        result["indexed"].append(
            {"file": path.name, "doc_id": doc.doc_id, "chunks": n, "doc_type": dt}
        )
        result["total_chunks"] += n
        log(f"Indexed {path.name} -> {doc.doc_id} ({n} chunks, {dt})")

    result["stats"] = index_stats()
    return result
