"""Live smoke test: Anthropic API + cost computation.

Runs without Streamlit context; lib.claude reads key from secrets.toml directly.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from lib.claude import Tier, chat, compute_cost  # noqa: E402

print("Calling Haiku 4.5...")
r1 = chat(
    messages=[{"role": "user", "content": "In one sentence, what does Queen's Model UN team do?"}],
    tier=Tier.CHEAP,
    system="You are a concise assistant. One sentence only.",
    max_tokens=120,
    cache_system=False,
)
print(f"  TEXT: {r1.text}")
print(f"  IN={r1.input_tokens} OUT={r1.output_tokens} COST=${r1.cost_usd:.6f}")

print("\nCalling Sonnet 4.6 (just to verify auth/model name)...")
r2 = chat(
    messages=[{"role": "user", "content": "Say 'sonnet ok' and nothing else."}],
    tier=Tier.SMART,
    max_tokens=30,
    cache_system=False,
)
print(f"  TEXT: {r2.text}")
print(f"  IN={r2.input_tokens} OUT={r2.output_tokens} COST=${r2.cost_usd:.6f}")

print(f"\nTotal smoke-test cost: ${r1.cost_usd + r2.cost_usd:.6f}")
print("OK")
