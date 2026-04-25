"""Live smoke test: all three chatbot modes."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from lib.chat import ChatMode, CrisisScenario, respond  # noqa: E402

print("=" * 72)
print("MENTOR mode")
print("=" * 72)
text, cost = respond(
    ChatMode.MENTOR,
    [{"role": "user", "content": "I'm representing Pakistan in a DISEC committee on autonomous weapons. First time at a real conference. Where do I start?"}],
    user_slack_id="U_TEST",
)
print(text)
print(f"\n--- ${cost:.5f} ---")

print("\n" + "=" * 72)
print("CRISIS BACKROOM mode")
print("=" * 72)
scenario = CrisisScenario(
    committee="USSR Politburo, Cuban Missile Crisis 1962",
    time_period="October 22, 1962, 8 PM Moscow time",
    initial_situation="Kennedy has just announced the naval quarantine of Cuba. The Politburo is in emergency session. Khrushchev wants options.",
    active_characters=["Khrushchev", "Gromyko", "Malinovsky", "Mikoyan"],
    tone_notes="Tense, historically grounded. Reward delegates who think about strategic restraint as well as escalation.",
)
text, cost = respond(
    ChatMode.CRISIS_BACKROOM,
    [{"role": "user", "content": "As Defense Minister Malinovsky, I issue a personal directive: covertly increase the alert level of our R-12 missiles already in Cuba to firing readiness, but do NOT inform the Americans. I want to be ready if Kennedy escalates. Two trusted officers carry the order to General Pliyev directly."}],
    user_slack_id="U_TEST",
    scenario=scenario,
)
print(text)
print(f"\n--- ${cost:.5f} ---")

print("\n" + "=" * 72)
print("CHAIR ASSISTANT mode")
print("=" * 72)
text, cost = respond(
    ChatMode.CHAIR_ASSISTANT,
    [{"role": "user", "content": "A delegate is yielding their remaining 30 seconds to another delegate, but that other delegate is currently on the speakers list. Is that in order?"}],
    user_slack_id="U_TEST",
)
print(text)
print(f"\n--- ${cost:.5f} ---")

print("\nOK")
