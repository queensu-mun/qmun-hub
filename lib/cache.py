"""Brief cache keyed by (country, topic, committee, week, depth).

Persisted through `lib.store` (local SQLite in dev, Supabase once configured).
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta

from lib import store


@dataclass
class CacheKey:
    country: str
    topic: str
    committee: str
    week_start: date
    depth: str

    def to_key(self) -> str:
        parts = [self.country, self.topic, self.committee, self.week_start.isoformat(), self.depth]
        return "|".join(p.strip().lower() for p in parts)


def week_start_of(d: date | None = None) -> date:
    d = d or date.today()
    return d - timedelta(days=d.weekday())


def get(key: CacheKey) -> tuple[str, float] | None:
    """Return (markdown, original_cost) if hit, else None."""
    rows = store.select_rows("briefs", where_eq={"cache_key": key.to_key()}, limit=1)
    if not rows:
        return None
    r = rows[0]
    return (r["markdown"], float(r["cost_usd"]))


def put(key: CacheKey, markdown: str, cost_usd: float) -> None:
    store.upsert_row(
        "briefs",
        {
            "cache_key": key.to_key(),
            "country": key.country,
            "topic": key.topic,
            "committee": key.committee,
            "week_start": key.week_start.isoformat(),
            "depth": key.depth,
            "markdown": markdown,
            "cost_usd": cost_usd,
            "created_at": datetime.utcnow().isoformat(),
        },
        key="cache_key",
    )


def recent(limit: int = 10) -> list[dict]:
    rows = store.select_rows("briefs", order_desc="created_at", limit=limit)
    return [
        {
            "country": r["country"], "topic": r["topic"], "committee": r["committee"],
            "week_start": r["week_start"], "depth": r["depth"],
            "cost_usd": r["cost_usd"], "created_at": r["created_at"],
        }
        for r in rows
    ]
