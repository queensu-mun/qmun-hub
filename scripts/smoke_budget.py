"""Smoke test: budget tracking + per-user quotas + monthly aggregation."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from lib.budget import (  # noqa: E402
    DB_PATH,
    check_user_quota,
    current_monthly,
    record_call,
    top_users,
    user_weekly,
)

# Clean slate for the test
if DB_PATH.exists():
    DB_PATH.unlink()

# Simulate a few calls
record_call("U_JACK", "chat_mentor", input_tokens=200, output_tokens=80, cost_usd=0.0008, model="haiku")
record_call("U_JACK", "brief", input_tokens=2400, output_tokens=600, cost_usd=0.012, model="sonnet")
record_call("U_JAKE", "chat_crisis", input_tokens=1200, output_tokens=400, cost_usd=0.0066, model="sonnet")

snap = user_weekly("U_JACK")
print(f"U_JACK weekly: chat={snap.chat_turns} briefs={snap.briefs_generated} crisis={snap.crisis_interactions} cost=${snap.estimated_cost_usd:.4f}")
assert snap.chat_turns == 1 and snap.briefs_generated == 1, snap

ok, msg = check_user_quota("U_JACK", "chat_mentor")
print(f"U_JACK chat quota: ok={ok} msg='{msg}'")
assert ok

monthly = current_monthly()
print(f"Monthly: spent=${monthly.spent_usd:.4f} cap=${monthly.cap_usd:.2f} projected=${monthly.projected_usd:.4f}")
assert monthly.spent_usd > 0

print("Top users this month:", top_users(5))
print("OK")
