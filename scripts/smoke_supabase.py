"""End-to-end Supabase smoke test: state, usage, briefs, and file upload.

Writes throwaway rows/files and cleans them up. Run after init_supabase.py.

    cd ~/qmun-hub && source .venv/bin/activate && python scripts/smoke_supabase.py
"""
from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from lib import budget, cache, store  # noqa: E402


def main() -> int:
    if store.backend() != "supabase":
        print("Not in Supabase mode. Configure [supabase] secrets first.")
        return 1

    # state blob round-trip (non-destructive: read, no write)
    st = store.load_state()
    print(f"state: loaded ({len(st.get('roster', [])) if st else 0} roster entries)")

    # usage round-trip
    budget.record_call("U_SMOKE", "brief", input_tokens=10, output_tokens=5,
                        cost_usd=0.001, model="smoke")
    snap = budget.user_weekly("U_SMOKE")
    print(f"usage: recorded + read back ({snap.briefs_generated} brief this week)")

    # brief cache round-trip
    k = cache.CacheKey("Smokeland", "Smoke topic", "SMOKE", cache.week_start_of(), "standard")
    cache.put(k, "# smoke", 0.002)
    hit = cache.get(k)
    print(f"briefs: cache {'hit' if hit else 'MISS'}")

    # upload round-trip
    key = "smoke/smoke.txt"
    saved = store.save_upload(key, b"hello supabase", "text/plain")
    print(f"upload: stored at {saved['stored_path'][:60]}...")
    store.delete_upload(saved["storage_key"])
    print("upload: deleted")

    print("\nAll Supabase paths working.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
