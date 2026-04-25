"""Country brief generator — backbone is Jack's 3-question research framework.

1. How does your country/character feel about this issue? Domestic actions taken?
2. How does the international community feel? Past international actions? Next steps?
3. What is your strategy in committee? How do you want to solve this?

Stub for May scaffolding. Full implementation in Phase 2 (June).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

Depth = Literal["mock", "conference"]


@dataclass
class BriefRequest:
    country: str
    topic: str
    committee: str
    depth: Depth
    notes: str | None = None


@dataclass
class Brief:
    markdown: str
    cost_usd: float
    cache_hit: bool
    archive_citations: list[str]


THREE_QUESTION_PROMPT = """\
Generate a Model UN country brief using Queen's MUN team's 3-question research framework:

1. **Country position**: How does {country} feel about this issue? What domestic actions have they taken?
2. **International context**: How does the international community feel? What past international actions exist?
   What are the likely next steps?
3. **Committee strategy**: What is {country}'s strategy going into this committee on this topic?
   How do they want to solve this issue?

Topic: {topic}
Committee: {committee}
Depth: {depth}
"""


def generate(req: BriefRequest) -> Brief:
    raise NotImplementedError("Phase 2")
