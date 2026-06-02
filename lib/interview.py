"""Alumni interview module: operationalizes the team's MUN Claude template.

Each section's responses get composed into a markdown document and indexed
into the archive (`alumni_interview` doc type). The Mentor chatbot cites
these by name; Archive search returns them on relevant queries.

Design principles for the questions:
- Low barrier first. The form opens with a short core of a few story-shaped
  questions. Everything past your name is optional. The goal is that a busy
  alum can finish in two minutes and still leave something useful behind.
- Depth is opt-in. The longer, experience-specific questions live behind a
  "Go deeper" section for the alumni who want to give more.
- Reward anecdotes. Story-shaped answers retrieve better and the chatbot
  can cite them by name.
- Skippable by experience. GA-only and Crisis-only sections so any one
  alum doesn't see questions outside their experience.

Each section carries a `tier`: "core" sections render up front and open;
"deep" sections render collapsed inside the optional "Go deeper" group.
`INTERVIEW_SECTIONS` stays the single source of truth so the submit/compose
loop in the page works unchanged.
"""
from __future__ import annotations

from dataclasses import dataclass

INTERVIEW_SECTIONS = [
    {
        "id": "context",
        "tier": "core",
        "title": "A little about you",
        "questions": [
            "How long were you on the team and what did you get up to? "
            "Roles, committee types, conferences, any awards you want to mention. "
            "One line is plenty.",
        ],
    },
    {
        "id": "sticky_note",
        "tier": "core",
        "title": "The sticky-note advice",
        "questions": [
            "If you could give a Queen's MUN delegate ONE piece of advice "
            "and it had to fit on a sticky note, what would it be?",
        ],
    },
    {
        "id": "moment",
        "tier": "core",
        "title": "A moment that stuck",
        "questions": [
            "Tell us about one committee moment you still remember. A win, a disaster, "
            "a turning point, a room that went sideways. Whatever comes to mind first.",
        ],
    },
    {
        "id": "recurring",
        "tier": "core",
        "title": "What we keep getting wrong",
        "questions": [
            "What do Queen's delegates keep getting wrong, year after year? "
            "Be honest. This is the most useful thing you can give us, because it "
            "tells us what to drill in training.",
        ],
    },
    {
        "id": "tactical",
        "tier": "deep",
        "title": "Tactical wisdom",
        "questions": [
            "What's the single most useful thing you do in committee that you didn't "
            "learn from the Art of MUN handbook? Where did you pick it up?",
            "Tell us about a specific moment when your committee strategy fell apart "
            "and how you recovered. What was the trigger, what did you change, what happened?",
        ],
    },
    {
        "id": "first_timer",
        "tier": "deep",
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
        "tier": "deep",
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
        "tier": "deep",
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
        "tier": "deep",
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
        "tier": "deep",
        "title": "Anything else",
        "questions": [
            "What didn't we ask that we should have? What knowledge are you taking with "
            "you that future Queen's MUN should keep? Be candid.",
            "Anyone we should interview after you? (Names of teammates whose brain "
            "we'd be silly to lose.)",
        ],
    },
]


def core_sections() -> list[dict]:
    """Short, low-barrier questions shown up front."""
    return [s for s in INTERVIEW_SECTIONS if s.get("tier", "deep") == "core"]


def deep_sections() -> list[dict]:
    """Longer, experience-specific questions shown behind 'Go deeper'."""
    return [s for s in INTERVIEW_SECTIONS if s.get("tier", "deep") == "deep"]


@dataclass
class InterviewResponse:
    interviewee_name: str
    interviewee_year_grad: int
    sections: dict[str, dict[str, str]]  # section_id -> {question -> answer}
    submitted_at: str


def submit(response: InterviewResponse) -> str:
    raise NotImplementedError("Phase 3: auto-indexes into archive")
