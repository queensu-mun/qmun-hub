"""Alumni interview module: operationalizes the team's MUN Claude template.

Each section's responses get composed into a markdown document and indexed
into the archive (`alumni_interview` doc type). The Mentor chatbot cites
these by name; Archive search returns them on relevant queries.

Design principles for the questions:
- Force specifics. "What's a moment when..." beats "Describe the team."
- Reward anecdotes. Story-shaped answers retrieve better and the chatbot
  can cite them by name.
- Skippable by experience. GA-only and Crisis-only sections so any one
  alum doesn't see questions outside their experience.
- ~20 minutes total if written substantively. Bullet-point answers fine.

Stub for May scaffolding. Full submit() implementation in Phase 3 (July).
"""
from __future__ import annotations

from dataclasses import dataclass

INTERVIEW_SECTIONS = [
    {
        "id": "context",
        "title": "Quick context",
        "questions": [
            "How many years were you on the team, and what roles did you hold? "
            "(e.g. delegate, exec, director, social chair)",
            "Which committee types did you do most? (GA, Specialized Agency, Crisis, UNSC, mix)",
            "Which conferences did you attend, and any awards or honors picked up? "
            "(e.g. \"NCSC LIII fall 2025, UNSC Cambodia, Verbal Commendation\")",
        ],
    },
    {
        "id": "sticky_note",
        "title": "The sticky-note advice",
        "questions": [
            "If you could give a Queen's MUN delegate ONE piece of advice "
            "and it had to fit on a sticky note, what would it be, and why? "
            "Be specific. Generic advice is useless to a first-timer.",
        ],
    },
    {
        "id": "tactical",
        "title": "Tactical wisdom",
        "questions": [
            "What's the single most useful thing you do in committee that you didn't "
            "learn from the Art of MUN handbook? Where did you pick it up?",
            "Tell us about a specific moment when your committee strategy fell apart "
            "and how you recovered. What was the trigger, what did you change, what happened?",
            "What do Queen's delegates collectively keep getting wrong, year after year? "
            "Be honest. This is the most valuable thing you can give us, because it "
            "tells us what to drill in training.",
        ],
    },
    {
        "id": "first_timer",
        "title": "For first-timers (this becomes Mentor chatbot context)",
        "questions": [
            "What would you tell yourself the night before your very first conference? "
            "Tactical, social, emotional, whatever you wish someone had told you.",
            "Name one concrete habit a first-timer can adopt in their very first "
            "session that pays off for the entire weekend. What does it look like in practice?",
            "Best piece of advice you ever got from someone senior on the team, "
            "and (if you remember) who gave it to you?",
        ],
    },
    {
        "id": "ga",
        "title": "GA / SA delegates only (skip if mostly crisis)",
        "questions": [
            "Tell us about a specific moment where bloc dynamics decided the outcome. "
            "Who was in the room, what was the play, how did it land?",
            "What separates a working paper that wins awards from one that just passes? "
            "Concrete clauses, sponsor lists, merge moves, whatever you've actually seen work.",
        ],
    },
    {
        "id": "crisis",
        "title": "Crisis delegates only (skip if mostly GA)",
        "questions": [
            "Walk us through a personal arc that actually worked. What was your character's "
            "goal, what moves did you make, what did the backroom give back, how did it end?",
            "What separates a great crisis directive from a forgettable one? "
            "Give a specific example of each if you can.",
            "What does Queen's do well in crisis, and what do we consistently miss? "
            "(We have no backroom staff and can't run crisis mocks. This question fills that gap.)",
        ],
    },
    {
        "id": "conferences",
        "title": "Conference-specific intel",
        "questions": [
            "For each major conference you attended, give us a short paragraph on: "
            "the vibe, what chairs actually reward, awards politics, and anything "
            "quirky about how it runs. Two or three sentences per conference is plenty. "
            "This is the intel future delegates can't get anywhere else.",
        ],
    },
    {
        "id": "open",
        "title": "Anything else",
        "questions": [
            "What didn't we ask that we should have? What knowledge are you taking with "
            "you that future Queen's MUN should keep? Be candid.",
            "Anyone we should interview after you? (Names of teammates whose brain "
            "we'd be silly to lose.)",
        ],
    },
]


@dataclass
class InterviewResponse:
    interviewee_name: str
    interviewee_year_grad: int
    sections: dict[str, dict[str, str]]  # section_id -> {question -> answer}
    submitted_at: str


def submit(response: InterviewResponse) -> str:
    raise NotImplementedError("Phase 3: auto-indexes into archive")
