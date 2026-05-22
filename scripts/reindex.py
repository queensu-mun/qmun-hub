"""Pull deltas from Google Drive -> chunk -> embed -> upsert.

Run nightly via cron once Drive integration is wired up:

    0 3 * * * cd ~/qmun-hub && /usr/bin/python3 scripts/reindex.py >> logs/reindex.log 2>&1

Without Drive configured, this script is a no-op that prints a helpful
message. Seed-only setups should use `scripts/seed_archive.py` instead.

Doc identity: each Drive file's `file_id` becomes our `doc_id`. The doc's
`indexed_at` column tracks when we last embedded it; anything modified on
Drive since that timestamp is reindexed.
"""
from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from lib import drive  # noqa: E402
from lib.index import Doc, _conn, upsert_doc  # noqa: E402

DOC_TYPE_BY_MIME = {
    drive.GOOGLE_DOC_MIME: "training",
    drive.PDF_MIME: "background_guide",
    drive.DOCX_MIME: "position_paper",
}


def _last_indexed_at_by_source() -> dict[str, datetime]:
    out: dict[str, datetime] = {}
    with _conn() as c:
        rows = c.execute("SELECT source, indexed_at FROM docs").fetchall()
    for source, indexed_at in rows:
        if not indexed_at:
            continue
        try:
            out[source] = datetime.fromisoformat(indexed_at)
        except ValueError:
            continue
    return out


def main() -> int:
    if not drive._is_configured():
        print("Drive isn't configured. Skipping reindex.")
        print("  - Configure [google].service_account_path and shared_drive_folder_id in secrets.toml")
        print("  - Or use scripts/seed_archive.py for seed-only setups.")
        return 0

    print("Listing team docs from Drive...")
    metas = drive.list_team_docs()
    print(f"  found {len(metas)} supported docs")

    last_seen = _last_indexed_at_by_source()
    deltas = []
    for m in metas:
        prev = last_seen.get(m.file_id)
        if prev is None or m.modified_time.replace(tzinfo=None) > prev:
            deltas.append(m)

    print(f"  {len(deltas)} need reindexing")
    if not deltas:
        return 0

    for m in deltas:
        print(f"  fetching {m.name} ({m.mime_type})...")
        d = drive.download_doc(m.file_id)
        if not d.text.strip():
            print(f"    empty body, skipping")
            continue
        doc = Doc(
            doc_id=m.file_id,
            title=m.name,
            source=m.file_id,
            doc_type=DOC_TYPE_BY_MIME.get(m.mime_type, "misc"),
            text=d.text,
            metadata={"drive_modified_time": m.modified_time.isoformat()},
        )
        n = upsert_doc(doc)
        print(f"    indexed {n} chunks")

    print("Done.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
