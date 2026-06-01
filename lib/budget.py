"""Per-user weekly token caps + global monthly USD cap.

Usage rows are persisted through `lib.store` (local SQLite in dev, Supabase
once configured). Aggregation is done in Python: the data volume is a team's
worth of rows, so this stays simple and identical across both backends.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta

from lib import store


@dataclass
class UsageSnapshot:
    user_slack_id: str
    week_start: date
    chat_turns: int
    briefs_generated: int
    crisis_interactions: int
    estimated_cost_usd: float


@dataclass
class MonthlyBudget:
    month: str
    spent_usd: float
    cap_usd: float
    warn_usd: float
    projected_usd: float

    @property
    def fraction_used(self) -> float:
        return self.spent_usd / self.cap_usd if self.cap_usd else 0.0

    @property
    def should_warn(self) -> bool:
        return self.spent_usd >= self.warn_usd or self.projected_usd >= self.cap_usd

    @property
    def should_block(self) -> bool:
        return self.spent_usd >= self.cap_usd


def _settings() -> dict:
    defaults = {"cap": 40.0, "warn": 35.0, "chat_per_week": 30, "briefs_per_week": 10, "crisis_per_week": 5}
    try:
        import streamlit as st
        app = st.secrets["app"]
        return {
            "cap": float(app.get("budget_monthly_usd_cap", defaults["cap"])),
            "warn": float(app.get("budget_monthly_usd_warn", defaults["warn"])),
            "chat_per_week": int(app.get("delegate_chat_turns_per_week", defaults["chat_per_week"])),
            "briefs_per_week": int(app.get("delegate_briefs_per_week", defaults["briefs_per_week"])),
            "crisis_per_week": int(app.get("delegate_crisis_interactions_per_week", defaults["crisis_per_week"])),
        }
    except Exception:
        return defaults


def _week_start(d: date | None = None) -> date:
    d = d or date.today()
    return d - timedelta(days=d.weekday())


def record_call(
    user_slack_id: str,
    feature: str,
    *,
    input_tokens: int,
    output_tokens: int,
    cached_input_tokens: int = 0,
    cache_write_tokens: int = 0,
    cost_usd: float,
    model: str,
) -> None:
    store.insert_row(
        "usage",
        {
            "ts": datetime.utcnow().isoformat(),
            "user_slack_id": user_slack_id,
            "feature": feature,
            "model": model,
            "input_tokens": input_tokens,
            "cached_input_tokens": cached_input_tokens,
            "cache_write_tokens": cache_write_tokens,
            "output_tokens": output_tokens,
            "cost_usd": cost_usd,
        },
    )


def user_weekly(user_slack_id: str) -> UsageSnapshot:
    week_start = _week_start()
    rows = store.select_rows(
        "usage",
        where_eq={"user_slack_id": user_slack_id},
        since=("ts", week_start.isoformat()),
    )
    counts: dict[str, list] = {}
    for r in rows:
        n, c = counts.get(r["feature"], (0, 0.0))
        counts[r["feature"]] = (n + 1, c + (r.get("cost_usd") or 0.0))
    chat = counts.get("chat_mentor", (0, 0))[0] + counts.get("chat_chair", (0, 0))[0]
    crisis = counts.get("chat_crisis", (0, 0))[0]
    briefs = counts.get("brief", (0, 0))[0]
    cost = sum(c for _, c in counts.values())
    return UsageSnapshot(
        user_slack_id=user_slack_id,
        week_start=week_start,
        chat_turns=chat,
        briefs_generated=briefs,
        crisis_interactions=crisis,
        estimated_cost_usd=cost,
    )


def check_user_quota(user_slack_id: str, feature: str) -> tuple[bool, str]:
    s = _settings()
    snap = user_weekly(user_slack_id)
    if feature in ("chat_mentor", "chat_chair") and snap.chat_turns >= s["chat_per_week"]:
        return False, f"You've hit your weekly chat cap ({s['chat_per_week']}). Resets Monday."
    if feature == "brief" and snap.briefs_generated >= s["briefs_per_week"]:
        return False, f"You've hit your weekly brief cap ({s['briefs_per_week']}). Resets Monday."
    if feature == "chat_crisis" and snap.crisis_interactions >= s["crisis_per_week"]:
        return False, f"You've hit your weekly crisis cap ({s['crisis_per_week']}). Resets Monday."
    return True, ""


def current_monthly() -> MonthlyBudget:
    s = _settings()
    now = datetime.utcnow()
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    days_in_month = (month_start.replace(month=month_start.month % 12 + 1, day=1) - month_start).days if month_start.month != 12 else 31
    days_elapsed = max(1, (now - month_start).days + 1)

    rows = store.select_rows("usage", since=("ts", month_start.isoformat()))
    spent = sum((r.get("cost_usd") or 0.0) for r in rows)

    projected = spent / days_elapsed * days_in_month
    return MonthlyBudget(
        month=now.strftime("%Y-%m"),
        spent_usd=float(spent),
        cap_usd=s["cap"],
        warn_usd=s["warn"],
        projected_usd=float(projected),
    )


def top_users(limit: int = 10) -> list[tuple[str, float, int]]:
    """Return [(user_slack_id, total_cost_usd, call_count), ...] for current month."""
    month_start = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    rows = store.select_rows("usage", since=("ts", month_start.isoformat()))
    agg: dict[str, list] = {}
    for r in rows:
        c, n = agg.get(r["user_slack_id"], (0.0, 0))
        agg[r["user_slack_id"]] = (c + (r.get("cost_usd") or 0.0), n + 1)
    ranked = sorted(agg.items(), key=lambda kv: kv[1][0], reverse=True)[:limit]
    return [(u, float(c), int(n)) for u, (c, n) in ranked]
