"""Anthropic client wrapper with prompt caching helpers.

Stub for May scaffolding. Full implementation in Phase 2 (June).
Models locked: never use Opus in prod.
"""
from __future__ import annotations

from enum import Enum

HAIKU = "claude-haiku-4-5-20251001"
SONNET = "claude-sonnet-4-6"


class Tier(str, Enum):
    CHEAP = "haiku"
    SMART = "sonnet"


def chat(messages: list[dict], *, tier: Tier = Tier.CHEAP, system: str | None = None,
         cache_system: bool = True, max_tokens: int = 1024) -> dict:
    raise NotImplementedError("Phase 2 — June")
