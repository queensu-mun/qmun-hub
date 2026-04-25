"""Local team state: weekly topics, conferences, assignments, roster.

Persisted to data/state.json. Director admin reads/writes this.
"""
from __future__ import annotations

import json
from contextlib import contextmanager
from dataclasses import asdict, dataclass, field
from pathlib import Path

STATE_PATH = Path(__file__).resolve().parent.parent / "data" / "state.json"


@dataclass
class WeeklyTopic:
    day: str           # "monday" | "thursday"
    topic: str
    committee: str
    set_at: str | None = None


@dataclass
class Conference:
    id: str
    name: str
    location: str
    start_date: str          # ISO
    end_date: str
    registration_deadline: str | None = None
    fees_per_delegate_usd: float | None = None
    notes: str | None = None


@dataclass
class Assignment:
    id: str
    conference_id: str
    delegate_name: str
    committee: str
    country_or_character: str
    status: str = "assigned"   # assigned | in_progress | submitted | done
    notes: str | None = None


def _default_state() -> dict:
    return {
        "team_year": "2026-2027",
        "weekly_topics": {"monday": None, "thursday": None},
        "conferences": [],
        "assignments": [],
        "roster": [],
        "settings": {
            "budget_warn_usd": 35.0,
            "budget_cap_usd": 40.0,
            "delegate_chat_turns_per_week": 30,
            "delegate_briefs_per_week": 10,
            "delegate_crisis_interactions_per_week": 5,
        },
    }


def load() -> dict:
    if not STATE_PATH.exists():
        STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
        STATE_PATH.write_text(json.dumps(_default_state(), indent=2))
    return json.loads(STATE_PATH.read_text())


def save(state: dict) -> None:
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    STATE_PATH.write_text(json.dumps(state, indent=2))


@contextmanager
def edit():
    state = load()
    yield state
    save(state)


# ----- helpers -----

def set_weekly_topic(day: str, topic: str, committee: str) -> None:
    from datetime import datetime
    with edit() as s:
        s["weekly_topics"][day] = {
            "topic": topic,
            "committee": committee,
            "set_at": datetime.utcnow().isoformat(),
        }


def add_conference(c: Conference) -> None:
    with edit() as s:
        s["conferences"].append(asdict(c))


def add_assignment(a: Assignment) -> None:
    with edit() as s:
        s["assignments"].append(asdict(a))


def remove_assignment(assignment_id: str) -> None:
    with edit() as s:
        s["assignments"] = [a for a in s["assignments"] if a["id"] != assignment_id]


def assignments_for_conference(conference_id: str) -> list[dict]:
    return [a for a in load().get("assignments", []) if a["conference_id"] == conference_id]
