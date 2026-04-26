"""Team weakness + training-strategy analyzer.

Reads roster + feedback, runs Sonnet, returns a structured report directors
use to plan training. Cached weekly in state.json so repeated views are free.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from datetime import date

from lib import state as state_lib
from lib.budget import record_call
from lib.cache import week_start_of
from lib.claude import Tier, chat


@dataclass
class TeamInsights:
    weaknesses: list[str] = field(default_factory=list)
    training_recommendations: list[str] = field(default_factory=list)
    delegate_focus: dict[str, list[str]] = field(default_factory=dict)
    summary: str = ""
    generated_at: str | None = None
    week_start: str | None = None
    feedback_count: int = 0
    cost_usd: float = 0.0

    def to_dict(self) -> dict:
        return {
            "weaknesses": self.weaknesses,
            "training_recommendations": self.training_recommendations,
            "delegate_focus": self.delegate_focus,
            "summary": self.summary,
            "generated_at": self.generated_at,
            "week_start": self.week_start,
            "feedback_count": self.feedback_count,
            "cost_usd": self.cost_usd,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "TeamInsights":
        return cls(**{k: d[k] for k in d if k in cls.__dataclass_fields__})


_SYSTEM = """\
You are an experienced Model UN coach reviewing director feedback on a collegiate
MUN team (Queen's University, currently 3rd in Canada). Your job is to read raw
feedback notes and synthesize:

1. Team-level weaknesses — recurring patterns across multiple delegates
2. Training recommendations — specific, runnable training exercises that target
   those weaknesses (e.g. "30-minute moderated caucus drill on bloc-flipping
   when you've lost the lead sponsor", not "work on bloc dynamics")
3. Per-delegate focus areas — for each delegate with multiple feedback entries,
   the 1-2 things they should work on

Be specific. Do not generalize. Quote feedback when it sharpens a recommendation.
Distinguish recurring patterns (multiple delegates, multiple events) from one-off
observations.

HARD RULE: never use em dashes (the long dash character). Use commas, parentheses,
or colons instead. Use regular hyphens for compound words.

You MUST output a single JSON object with these keys (and no other text):
{
  "summary": "2-3 sentence overall read on the team's current state",
  "weaknesses": ["pattern 1", "pattern 2", ...],
  "training_recommendations": ["concrete exercise 1", "concrete exercise 2", ...],
  "delegate_focus": {
    "Delegate Name": ["focus area 1", "focus area 2"],
    ...
  }
}

Output ONLY the JSON. No preamble, no markdown fences.
"""


def _build_user_message(roster: list[dict], feedback: list[dict]) -> str:
    if not feedback:
        return "There is no feedback yet. Return an empty analysis."

    roster_by_name = {d["name"].strip().lower(): d for d in roster}

    lines = ["# ROSTER\n"]
    if roster:
        for d in roster:
            year = d.get("year")
            status = d.get("status", "rookie")
            lines.append(f"- {d['name']} (year {year}, {status})")
    else:
        lines.append("(no roster yet)")

    lines.append("\n# FEEDBACK\n")
    for f in feedback:
        name = f["delegate_name"]
        roster_match = roster_by_name.get(name.strip().lower())
        status_tag = ""
        if roster_match:
            status_tag = f" [{roster_match.get('status', 'rookie')}, year {roster_match.get('year', '?')}]"
        tags = ", ".join(f.get("tags") or [])
        tag_str = f" tags=[{tags}]" if tags else ""
        source = f.get("source", "other")
        when = f.get("created_at") or f.get("mock_date") or "?"
        lines.append(f"## {name}{status_tag} — {source} — {when[:10]}{tag_str}")
        lines.append(f.get("notes", "").strip())
        lines.append("")

    lines.append("Generate the JSON analysis now.")
    return "\n".join(lines)


def _scrub(text: str) -> str:
    return text.replace(" — ", ", ").replace(" – ", ", ").replace("—", "-").replace("–", "-")


def _parse_json(text: str) -> dict:
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    return json.loads(text)


def cached_insights() -> TeamInsights | None:
    s = state_lib.load()
    cache = s.get("team_insights_cache")
    if not cache:
        return None
    return TeamInsights.from_dict(cache)


def _save_cache(insights: TeamInsights) -> None:
    with state_lib.edit() as s:
        state_lib._normalize_state(s)
        s["team_insights_cache"] = insights.to_dict()


def clear_cache() -> None:
    with state_lib.edit() as s:
        state_lib._normalize_state(s)
        s["team_insights_cache"] = None


def generate(*, user_slack_id: str = "anonymous", force: bool = False) -> TeamInsights:
    """Generate or fetch this week's team insights.

    If a cached insight exists for the current week and force=False, returns it.
    """
    week = week_start_of().isoformat()

    if not force:
        cached = cached_insights()
        if cached and cached.week_start == week:
            return cached

    s = state_lib.load()
    roster = s.get("roster", [])
    feedback = s.get("feedback", [])

    user_msg = _build_user_message(roster, feedback)

    result = chat(
        messages=[{"role": "user", "content": user_msg}],
        tier=Tier.SMART,
        system=_SYSTEM,
        cache_system=True,
        max_tokens=2500,
        temperature=0.4,
    )

    text = _scrub(result.text)
    try:
        payload = _parse_json(text)
    except json.JSONDecodeError:
        payload = {
            "summary": "Analyzer returned malformed JSON. Raw output below.",
            "weaknesses": [text[:500]],
            "training_recommendations": [],
            "delegate_focus": {},
        }

    record_call(
        user_slack_id,
        "team_insights",
        input_tokens=result.input_tokens,
        cached_input_tokens=result.cached_input_tokens,
        cache_write_tokens=result.cache_write_tokens,
        output_tokens=result.output_tokens,
        cost_usd=result.cost_usd,
        model=result.model,
    )

    insights = TeamInsights(
        summary=payload.get("summary", ""),
        weaknesses=payload.get("weaknesses", []) or [],
        training_recommendations=payload.get("training_recommendations", []) or [],
        delegate_focus=payload.get("delegate_focus", {}) or {},
        generated_at=state_lib.now_iso(),
        week_start=week,
        feedback_count=len(feedback),
        cost_usd=result.cost_usd,
    )
    _save_cache(insights)
    return insights
