"""Brief cache keyed by (country, topic, committee, week, depth). SQLite-backed."""
from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "brief_cache.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS briefs (
    cache_key TEXT PRIMARY KEY,
    country TEXT NOT NULL,
    topic TEXT NOT NULL,
    committee TEXT NOT NULL,
    week_start TEXT NOT NULL,
    depth TEXT NOT NULL,
    markdown TEXT NOT NULL,
    cost_usd REAL NOT NULL,
    created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_briefs_week ON briefs(week_start);
"""


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


@contextmanager
def _conn():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    try:
        conn.executescript(SCHEMA)
        yield conn
        conn.commit()
    finally:
        conn.close()


def week_start_of(d: date | None = None) -> date:
    d = d or date.today()
    return d - timedelta(days=d.weekday())


def get(key: CacheKey) -> tuple[str, float] | None:
    """Return (markdown, original_cost) if hit, else None."""
    with _conn() as c:
        row = c.execute(
            "SELECT markdown, cost_usd FROM briefs WHERE cache_key = ?",
            (key.to_key(),),
        ).fetchone()
    return (row[0], float(row[1])) if row else None


def put(key: CacheKey, markdown: str, cost_usd: float) -> None:
    with _conn() as c:
        c.execute(
            "INSERT OR REPLACE INTO briefs "
            "(cache_key, country, topic, committee, week_start, depth, markdown, cost_usd, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                key.to_key(),
                key.country,
                key.topic,
                key.committee,
                key.week_start.isoformat(),
                key.depth,
                markdown,
                cost_usd,
                datetime.utcnow().isoformat(),
            ),
        )


def recent(limit: int = 10) -> list[dict]:
    with _conn() as c:
        rows = c.execute(
            "SELECT country, topic, committee, week_start, depth, cost_usd, created_at "
            "FROM briefs ORDER BY created_at DESC LIMIT ?",
            (limit,),
        ).fetchall()
    return [
        {
            "country": r[0], "topic": r[1], "committee": r[2],
            "week_start": r[3], "depth": r[4], "cost_usd": r[5], "created_at": r[6],
        }
        for r in rows
    ]
