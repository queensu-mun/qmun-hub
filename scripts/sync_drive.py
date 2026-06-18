"""Pull the team Google Drive folder into the archive in one command.

Companion to scripts/ingest_folder.py (which indexes local files). This one pulls
straight from the configured team Drive folder via a service account, so it's the
path for keeping the archive in step with Drive without uploading files by hand.
Honours the active backend, so run it against the deployed (Supabase) setup to
update the live archive.

    cd ~/qmun-hub && source .venv/bin/activate
    python scripts/sync_drive.py            # incremental (changed since last sync)
    python scripts/sync_drive.py --full     # re-pull everything in the folder
    python scripts/sync_drive.py --folder <id>   # override the configured folder

Needs [google].service_account_path + [google].shared_drive_folder_id in
.streamlit/secrets.toml, and the folder shared with the service account's email.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from lib import drive_sync, store  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser(description="Sync the team Drive folder into the QMUN archive.")
    ap.add_argument("--full", action="store_true", help="Re-pull every file (ignore last-sync watermark)")
    ap.add_argument("--folder", default=None, help="Override the configured folder id")
    ap.add_argument("--doc-type", default=None, help="Force one doc_type for all files (else inferred)")
    args = ap.parse_args()

    if not drive_sync.is_configured():
        print("Google Drive isn't configured. Add [google].service_account_path and")
        print("[google].shared_drive_folder_id to .streamlit/secrets.toml, then share the")
        print("folder with the service account's email. See DEPLOY.md.")
        return 1

    mode = "full" if args.full else "incremental"
    print(f"Backend: {store.backend()}  |  mode: {mode}\n")

    result = drive_sync.sync_drive(
        folder_id=args.folder,
        full=args.full,
        default_doc_type=args.doc_type,
        log=lambda msg: print(f"  {msg}"),
    )

    for fname, reason in result["skipped"]:
        print(f"  SKIP {fname}: {reason}")
    for err in result["errors"]:
        print(f"  ERROR: {err}")

    if result["errors"] and not result["indexed"]:
        return 1

    n_ok = len(result["indexed"])
    print(f"\nDone. Indexed {n_ok} doc(s), +{result['total_chunks']} chunks.")
    stats = result["stats"]
    if stats:
        print(f"Archive now: {stats['n_docs']} docs / {stats['n_chunks']} chunks.")
    print("Note: in local mode, commit data/archive.db so the deploy ships the new docs,")
    print("      or re-run this against the deployed (Supabase) backend.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
