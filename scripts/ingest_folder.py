"""Generic folder ingester: drop docs in a folder, index them in one command.

The seed list (scripts/seed_archive.py) is a hardcoded, curated set. This script
is the everyday CLI path for adding real material; the same logic now also backs
the Director -> Curation "Reindex archive" button (see lib/ingest.py). Point it
at any folder of .md / .pdf / .docx files and it chunks, embeds, and upserts
each one into the archive. It honours whichever backend is active, so on a
deployed (Supabase) setup it writes straight to Postgres.

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
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from lib import store  # noqa: E402
from lib.ingest import VALID_DOC_TYPES, ingest_folder  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser(description="Index a folder of docs into the QMUN archive.")
    ap.add_argument("folder", help="Folder containing .md / .pdf / .docx files")
    ap.add_argument("--doc-type", choices=sorted(VALID_DOC_TYPES), default=None,
                    help="Override doc_type for all files (else inferred by extension)")
    ap.add_argument("--year", type=int, default=None, help="Year metadata for all files")
    ap.add_argument("--prefix", default="ingest", help="doc_id prefix (default: ingest)")
    args = ap.parse_args()

    print(f"Backend: {store.backend()}  |  folder: {args.folder}\n")
    result = ingest_folder(
        args.folder,
        doc_type=args.doc_type,
        year=args.year,
        prefix=args.prefix,
        log=lambda msg: print(f"  {msg}"),
    )

    for err in result["errors"]:
        print(f"  ERROR: {err}")
    if not result["indexed"] and not result["skipped"]:
        return 1

    stats = result["stats"]
    if stats:
        print(f"\nDone. +{result['total_chunks']} chunks. Archive now: "
              f"{stats['n_docs']} docs / {stats['n_chunks']} chunks.")
    print("Note: in local mode, commit data/archive.db so the deploy ships the new docs,")
    print("      or re-run this against the deployed (Supabase) backend.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
