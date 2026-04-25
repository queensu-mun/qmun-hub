"""Per-user weekly token caps + global monthly USD cap.

Stub for May scaffolding. Full implementation in Phase 2 (June).
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date


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

    @property
    def fraction_used(self) -> float:
        return self.spent_usd / self.cap_usd if self.cap_usd else 0.0

    @property
    def should_warn(self) -> bool:
        return self.spent_usd >= self.warn_usd

    @property
    def should_block(self) -> bool:
        return self.spent_usd >= self.cap_usd


def check_user_quota(user_slack_id: str, feature: str) -> bool:
    raise NotImplementedError("Phase 2")


def record_call(user_slack_id: str, feature: str, input_tokens: int, output_tokens: int,
                cached_input_tokens: int = 0, model: str = "haiku") -> None:
    raise NotImplementedError("Phase 2")


def current_monthly() -> MonthlyBudget:
    raise NotImplementedError("Phase 2")
