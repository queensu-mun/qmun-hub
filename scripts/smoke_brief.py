"""Live smoke test: generate a mock brief + a conference brief, print costs.

Uses Jack's NCSC fall 2025 UNSC Cambodia prep as the conference test case
(per memory: he has personal ground-truth on this committee).
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from lib.brief import BriefRequest, generate  # noqa: E402

print("=" * 72)
print("MOCK BRIEF (Haiku)")
print("=" * 72)
t0 = time.time()
mock = generate(BriefRequest(
    country="Brazil",
    topic="Sustainable financing for climate adaptation in Small Island Developing States",
    committee="ECOSOC",
    depth="mock",
    user_slack_id="U_JACK_TEST",
))
print(f"\n{mock.markdown}\n")
print(f"--- {time.time() - t0:.1f}s, ${mock.cost_usd:.5f}, cache_hit={mock.cache_hit} ---")

print("\n" + "=" * 72)
print("CONFERENCE BRIEF (Sonnet)")
print("=" * 72)
t0 = time.time()
conf = generate(BriefRequest(
    country="China",
    topic="The situation in Cambodia (post-Khmer Rouge tribunal accountability and regional stability)",
    committee="UNSC",
    depth="conference",
    notes="NCSC LIII fall 2025 simulation. Jack has personal ground-truth on this committee — compare against his actual position paper for sanity check.",
    user_slack_id="U_JACK_TEST",
))
print(f"\n{conf.markdown}\n")
print(f"--- {time.time() - t0:.1f}s, ${conf.cost_usd:.5f}, cache_hit={conf.cache_hit} ---")

print("\n" + "=" * 72)
print("CACHE HIT TEST: re-request the mock brief")
print("=" * 72)
t0 = time.time()
mock2 = generate(BriefRequest(
    country="Brazil",
    topic="Sustainable financing for climate adaptation in Small Island Developing States",
    committee="ECOSOC",
    depth="mock",
    user_slack_id="U_JACK_TEST",
))
print(f"--- {time.time() - t0:.2f}s, ${mock2.cost_usd:.5f}, cache_hit={mock2.cache_hit} ---")
assert mock2.cache_hit, "Expected cache hit on identical request"

print(f"\nTotal new spend: ${mock.cost_usd + conf.cost_usd:.4f}")
print("OK")
