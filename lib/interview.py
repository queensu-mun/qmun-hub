"""Alumni interview module — operationalizes Jack's MUN Claude template.

Stub for May scaffolding. Full implementation in Phase 3 (July).
"""
from __future__ import annotations

from dataclasses import dataclass

INTERVIEW_SECTIONS = [
    {
        "id": "team_culture",
        "title": "Queen's Team Culture & Preparation",
        "questions": [
            "How does the team prepare before a conference? What's the timeline?",
            "How do you divide research responsibilities within a delegation?",
            "Do you do practice sessions or mock debates? What do those look like?",
            "What does a first-timer need to know that the handbook doesn't cover? Unwritten rules, social dynamics, what to pack, what to expect emotionally.",
            "What's the team's general philosophy — aggressive vs. collaborative, awards-focused vs. experience-focused? Has it shifted over time?",
            "How do you assign delegates to committees? What makes someone a good fit for crisis vs. GA vs. specialized?",
            "What's the team dynamic during a conference? Do you debrief between sessions? Help each other?",
        ],
    },
    {
        "id": "conference_intel",
        "title": "Conference-Specific Intel",
        "questions": [
            "What surprised you about this conference?",
            "What did chairs actually reward? (procedural skill? substance? collaboration? flashiness?)",
            "What strategies worked? What flopped?",
            "Specific anecdotes — bloc that fell apart, crisis note that changed the game, merge negotiation, speech that landed or bombed.",
            "How did judging actually work vs. what they claimed?",
            "What's the vibe? How does the room feel compared to other conferences?",
            "How big were the committees? How experienced were other delegates?",
            "Anything specific about venue, logistics, scheduling that affected performance?",
        ],
        "per_conference": True,
    },
    {
        "id": "tactical",
        "title": "Tactical Wisdom",
        "questions": [
            "What mistakes do Queen's delegates keep making year after year?",
            "What's overrated in MUN?",
            "What's underrated?",
            "Best position papers you've seen — what made them stand out?",
            "Worst position papers — what tanked them?",
            "Crisis notes: what kind get results vs. what staff ignore?",
            "Unmod tactics: how do you actually approach strangers, form blocs, handle a poach?",
            "How do you handle a committee where you're outmatched?",
            "How do you handle a committee where chairs are bad or disorganized?",
            "What do you wish someone had told you before your first conference?",
        ],
    },
    {
        "id": "working_papers",
        "title": "Working Papers & Resolutions",
        "questions": [
            "Walk me through how a working paper actually gets written in committee. Who starts it? How do you divide clauses? What tools (laptop, paper, Google Docs)?",
            "What makes a working paper merge succeed vs. fail?",
            "Have you seen creative or unusual operative clauses that impressed chairs?",
            "What's the difference between a working paper that wins awards and one that just passes?",
        ],
    },
    {
        "id": "position_papers",
        "title": "Position Papers Specifically",
        "questions": [
            "Do you write them the night before or weeks in advance? What's realistic?",
            "How much do position papers actually matter for awards at the conferences you've attended?",
            "What feedback have you gotten from chairs on your papers?",
            "Do you have a research process? Specific sources you always check?",
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
    raise NotImplementedError("Phase 3 — auto-indexes into archive")
