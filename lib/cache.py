"""Brief cache keyed by (country, topic, committee, week)."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date


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


def get(key: CacheKey) -> str | None:
    raise NotImplementedError("Phase 2")


def put(key: CacheKey, brief_markdown: str) -> None:
    raise NotImplementedError("Phase 2")
