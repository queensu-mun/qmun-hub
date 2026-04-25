"""Multi-mode chatbot: Mentor, Crisis Backroom, Chair/Dais Assistant.

Stub for May scaffolding. Full implementation in Phase 3 (July).
"""
from __future__ import annotations

from enum import Enum


class ChatMode(str, Enum):
    MENTOR = "mentor"
    CRISIS_BACKROOM = "crisis_backroom"
    CHAIR_ASSISTANT = "chair_assistant"


MODE_DESCRIPTIONS = {
    ChatMode.MENTOR: (
        "Default. Mentor for delegates — research, position prep, opening speeches. "
        "Grounded in archive, cites sources. Cheap (Haiku)."
    ),
    ChatMode.CRISIS_BACKROOM: (
        "Acts as crisis staff for mock crisis committees. Responds to delegates' crisis notes "
        "with directives, character actions, world updates, escalations. Solves the team's "
        "lack-of-backroom-staff gap. Sonnet on demand."
    ),
    ChatMode.CHAIR_ASSISTANT: (
        "For execs running mocks — points/motions adjudication, time-keeping, "
        "'is this in order?' calls. Cheap (Haiku)."
    ),
}


def respond(mode: ChatMode, history: list[dict], scenario: dict | None = None) -> dict:
    raise NotImplementedError("Phase 3")
