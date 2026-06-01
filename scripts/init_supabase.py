"""One-time Supabase initializer + migrator for QMUN Hub.

Run AFTER:
  1. adding the [supabase] block to .streamlit/secrets.toml, and
  2. running scripts/supabase_schema.sql in the Supabase SQL editor.

What it does:
  - confirms the app is in Supabase mode,
  - creates the public `uploads` storage bucket if missing,
  - if the remote team_state is empty, seeds it from local data
    (data/store.db -> data/state.json -> built-in defaults),
  - reads everything back to prove the wiring works.

Idempotent: safe to run more than once. It never overwrites a non-empty
remote team_state, so re-running won't clobber live team data.

    cd ~/qmun-hub && source .venv/bin/activate && python scripts/init_supabase.py
"""
from __future__ import annotations

import json
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from lib import state as state_lib  # noqa: E402
from lib import store  # noqa: E402


def _read_local_state() -> tuple[dict, str]:
    """Best local snapshot to seed the remote with, plus where it came from."""
    local_db = store.LOCAL_DB
    if local_db.exists():
        try:
            conn = sqlite3.connect(local_db)
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                "SELECT data FROM team_state WHERE id = ?",
                (store.STATE_SINGLETON_ID,),
            ).fetchone()
            conn.close()
            if row:
                return json.loads(row["data"]), f"local store.db ({local_db})"
        except Exception:
            pass

    legacy = ROOT / "data" / "state.json"
    if legacy.exists():
        try:
            return json.loads(legacy.read_text()), f"legacy state.json ({legacy})"
        except Exception:
            pass

    return state_lib._default_state(), "built-in defaults"


def _ensure_bucket(client) -> str:
    bucket = store.UPLOAD_BUCKET
    try:
        existing = {b.name for b in client.storage.list_buckets()}
    except Exception:
        existing = set()
    if bucket in existing:
        return f"bucket '{bucket}' already exists"
    try:
        client.storage.create_bucket(bucket, options={"public": True})
        return f"created public bucket '{bucket}'"
    except Exception as e:
        # Most commonly: bucket already exists under a race / prior run.
        return f"bucket '{bucket}': {e} (continuing)"


def main() -> int:
    if store.backend() != "supabase":
        print("Supabase is NOT configured. Add the [supabase] block to")
        print(".streamlit/secrets.toml (url + service_role_key), then re-run.")
        return 1

    client = store._client()
    print("Supabase mode active.")
    print("-", _ensure_bucket(client))

    # Confirm the tables exist (clear error if the schema wasn't run yet).
    try:
        store.select_rows("usage", limit=1)
        store.select_rows("briefs", limit=1)
    except Exception as e:
        print(f"\nCould not query tables: {e}")
        print("Run scripts/supabase_schema.sql in the Supabase SQL editor first.")
        return 1

    remote = store.load_state()
    if remote is None:
        local, source = _read_local_state()
        store.save_state(local)
        print(f"- seeded team_state from {source}")
    else:
        print("- team_state already present remotely (left untouched)")

    # Read-back proof.
    back = store.load_state()
    roster = back.get("roster", []) if back else []
    print(f"- read-back ok: {len(roster)} roster entries, "
          f"{len(back.get('socials', []))} socials, "
          f"keys={sorted(back.keys())}")
    print("\nDone. The app will now persist to Supabase.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
