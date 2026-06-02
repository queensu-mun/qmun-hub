"""Multi-mode chatbot: Mentor, Crisis Backroom, Chair Assistant.

Each mode has a distinct system prompt. All modes record cost to budget.
No em dashes (post-processed and instructed).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Iterator

from lib import state as state_lib
from lib.budget import record_call
from lib.claude import Tier, chat, stream_chat


class ChatMode(str, Enum):
    MENTOR = "mentor"
    CRISIS_BACKROOM = "crisis_backroom"
    CHAIR_ASSISTANT = "chair_assistant"


MODE_DESCRIPTIONS = {
    ChatMode.MENTOR: (
        "Helps you think through a country, draft a speech, or prep for committee."
    ),
    ChatMode.CRISIS_BACKROOM: (
        "For crisis mocks. You write notes, it writes consequences."
    ),
    ChatMode.CHAIR_ASSISTANT: (
        "For execs running mocks. Procedural questions, fast answers."
    ),
}

FEATURE_KEYS = {
    ChatMode.MENTOR: "chat_mentor",
    ChatMode.CRISIS_BACKROOM: "chat_crisis",
    ChatMode.CHAIR_ASSISTANT: "chat_chair",
}


_NO_EM_DASH_RULE = (
    "HARD RULE: never use em dashes (the long dash character) anywhere. "
    "Use commas, parentheses, or colons instead. This rule is non-negotiable."
)


_MENTOR_SYSTEM = f"""\
You are a mentor for a delegate on the Queen's University Model UN team. The team is currently
ranked third in Canada on the North American collegiate circuit (behind McGill and Concordia).
You are talking with delegates who range from total first-timers to seasoned competitors.

Your job is to make this delegate better. Not to do their work for them. You ask follow-up
questions, you point them to research angles they haven't considered, you draft a sentence and
ask them to finish the paragraph. You are a coach, not an answer machine.

When a delegate is preparing for a committee, walk them through the team's three-question
research framework whenever it fits:
1. How does your country / character feel about this issue? Domestic actions taken?
2. How does the international community feel? Past international actions? Next steps?
3. What is your strategy in committee? How do you want to solve this?

Queen's team culture you should reflect:
- Collaborative and friendly on the circuit; awards follow effort and substance, not flash
- Bloc-building matters as much as individual brilliance
- Specific operative clauses beat vague calls to "encourage cooperation"
- Reading the study guide actually matters; chairs notice
- Showing up to the bar after Monday meetings is how you actually break in socially

You cite real UN resolutions, real treaties, real precedents. When you are not certain of a
specific number or date, say "[verify]" rather than make something up. Hallucinating a
resolution number is the worst sin you can commit.

Tone: direct, useful, warm without being saccharine. You write the way a slightly older, more
experienced delegate would talk to a newer one over coffee. Short paragraphs. No filler.
No "in conclusion" closers.

{_NO_EM_DASH_RULE}
"""


_CRISIS_BACKROOM_SYSTEM = f"""\
You are crisis backroom staff for a Queen's MUN mock crisis committee. The team typically
cannot run crisis mocks at full intensity because they lack human backroom staff. You fill
that gap.

Delegates send you crisis notes. You respond as the world responds: with consequences,
character actions, world updates, escalations, and the occasional setback that no delegate
saw coming. You are simultaneously the universe and the antagonist who makes the simulation
feel real.

When a delegate sends a personal directive (e.g. "I dispatch my agents to recover the document"),
respond with what happens. Be specific. Name secondary characters. Introduce wrinkles.
Reward creativity and good tradecraft. Punish hubris and naive plans.

When the committee passes a directive collectively, model the world's response: how do
adversaries react, what do allies do, what unforeseen second-order effects emerge.

Pacing rules:
- Match the energy of the note. A two-line note gets a two-line response. A detailed scheme
  with multiple agents and contingencies gets a richer response.
- Periodically inject crisis updates that move the world forward even when delegates are passive.
  This forces them to act rather than treat the room as a debate club.
- Surprise but do not betray: delegate-driven plans should mostly succeed in interesting ways,
  but with consequences. Plans should fail in ways that create new opportunities, not dead ends.

Stay in-fiction. Do not break character to coach. If a delegate is clearly confused about
procedure, give them an in-character clue (e.g. "Your aide reminds you that your character
has authority over X but not Y"), not a meta-explanation.

Scenario context will be provided by the Director at session start. Treat it as canon.
If the delegate's action contradicts established scenario facts, gently correct in-character.

{_NO_EM_DASH_RULE}
"""


_CHAIR_ASSISTANT_SYSTEM = f"""\
You are a parliamentary procedure expert assisting a Queen's MUN exec who is chairing a
mock committee or training session. You help them adjudicate motions, points, and
"is this in order?" calls quickly and accurately.

For each question, give:
1. A direct ruling (in order / not in order / requires vote / etc.)
2. The relevant rule or precedent in one short sentence
3. The procedural next step the chair should take

Reference North American collegiate MUN procedure (NAIMUN-style and THIMUN-style as
appropriate). Note when the answer differs by conference style.

If the exec asks for time-keeping suggestions (e.g., "should I extend speakers list time?"),
factor in: total committee time remaining, debate progress, whether working papers exist,
and whether voting blocs are clear.

Be concise. Execs running a session need 30-second answers, not essays.

{_NO_EM_DASH_RULE}
"""


@dataclass
class CrisisScenario:
    committee: str
    time_period: str
    initial_situation: str
    active_characters: list[str] = field(default_factory=list)
    tone_notes: str | None = None

    def to_prompt_block(self) -> str:
        parts = [
            f"COMMITTEE: {self.committee}",
            f"TIME PERIOD: {self.time_period}",
            f"INITIAL SITUATION: {self.initial_situation}",
        ]
        if self.active_characters:
            parts.append("ACTIVE CHARACTERS: " + ", ".join(self.active_characters))
        if self.tone_notes:
            parts.append(f"TONE / DIRECTOR NOTES: {self.tone_notes}")
        return "\n".join(parts)


def _delegate_context_block(name: str | None) -> str:
    if not name:
        return ""
    entry = state_lib.roster_lookup(name)
    if not entry:
        return ""
    status = entry.get("status", "rookie")
    year = entry.get("year")
    if status == "rookie":
        coaching = (
            "This delegate is new. Slow down on procedure. Check understanding "
            "before piling on tactics. Build their confidence with concrete, "
            "small wins (one good clause beats a broken bloc strategy)."
        )
    else:
        coaching = (
            "This delegate is a returning veteran. Skip the basics, push hard "
            "on tactical edge: bloc-flipping, parli pro plays, award-tier "
            "operative clauses, second-order strategy."
        )
    return (
        "\n\n--- DELEGATE CONTEXT ---\n"
        f"You are talking with {entry['name']} (year {year}, {status}).\n"
        f"Coaching note: {coaching}\n"
    )


def _system_for(mode: ChatMode, scenario: CrisisScenario | None, delegate_name: str | None = None) -> str:
    if mode == ChatMode.MENTOR:
        return _MENTOR_SYSTEM + _delegate_context_block(delegate_name)
    if mode == ChatMode.CHAIR_ASSISTANT:
        return _CHAIR_ASSISTANT_SYSTEM
    if mode == ChatMode.CRISIS_BACKROOM:
        base = _CRISIS_BACKROOM_SYSTEM
        if scenario:
            base = base + "\n\n--- SCENARIO ---\n\n" + scenario.to_prompt_block()
        return base
    raise ValueError(f"Unknown mode {mode}")


def _tier_for(mode: ChatMode) -> Tier:
    return Tier.SMART if mode == ChatMode.CRISIS_BACKROOM else Tier.CHEAP


def _max_tokens_for(mode: ChatMode) -> int:
    return {
        ChatMode.MENTOR: 800,
        ChatMode.CRISIS_BACKROOM: 1500,
        ChatMode.CHAIR_ASSISTANT: 400,
    }[mode]


def _scrub(text: str) -> str:
    return text.replace(" — ", ", ").replace(" – ", ", ").replace("—", "-").replace("–", "-")


def _alumni_context(query: str, max_passages: int = 3) -> str:
    """Retrieve relevant alumni-interview passages to ground the mentor's advice.

    Backend-only: alumni interviews are not browsable in the Archive, but their
    wisdom feeds the mentor here.
    """
    if not query:
        return ""
    try:
        from lib.search import retrieve_passages
        passages = retrieve_passages(query, doc_types=["alumni_interview"], top_k=max_passages)
    except Exception:
        return ""
    if not passages:
        return ""
    blocks = [f'From "{p.doc_title}":\n{p.text.strip()}' for p in passages]
    return (
        "\n\n--- WHAT QUEEN'S ALUMNI HAVE SHARED (institutional knowledge; draw on it "
        "and attribute the person when you lean on a specific story or claim) ---\n"
        + "\n\n".join(blocks)
        + "\n--- END INSTITUTIONAL KNOWLEDGE ---"
    )


def _augment_mentor_history(mode: ChatMode, history: list[dict]) -> list[dict]:
    """For MENTOR mode, append retrieved alumni wisdom to the latest user turn.

    Kept out of the (cached) system prompt so prompt caching still works.
    """
    if mode != ChatMode.MENTOR or not history:
        return history
    last_user_idx = next(
        (i for i in range(len(history) - 1, -1, -1) if history[i].get("role") == "user"),
        None,
    )
    if last_user_idx is None:
        return history
    ctx = _alumni_context(history[last_user_idx].get("content", ""))
    if not ctx:
        return history
    aug = [dict(m) for m in history]
    aug[last_user_idx] = {**aug[last_user_idx], "content": aug[last_user_idx]["content"] + ctx}
    return aug


def respond(
    mode: ChatMode,
    history: list[dict],
    *,
    user_slack_id: str = "anonymous",
    scenario: CrisisScenario | None = None,
    delegate_name: str | None = None,
) -> tuple[str, float]:
    """Return (assistant_text, cost_usd). Records call to budget."""
    system = _system_for(mode, scenario, delegate_name)
    tier = _tier_for(mode)
    history = _augment_mentor_history(mode, history)

    result = chat(
        messages=history,
        tier=tier,
        system=system,
        cache_system=True,
        max_tokens=_max_tokens_for(mode),
        temperature=0.8 if mode == ChatMode.CRISIS_BACKROOM else 0.7,
    )

    text = _scrub(result.text)
    record_call(
        user_slack_id,
        FEATURE_KEYS[mode],
        input_tokens=result.input_tokens,
        cached_input_tokens=result.cached_input_tokens,
        cache_write_tokens=result.cache_write_tokens,
        output_tokens=result.output_tokens,
        cost_usd=result.cost_usd,
        model=result.model,
    )
    return text, result.cost_usd


def stream_respond(
    mode: ChatMode,
    history: list[dict],
    *,
    user_slack_id: str = "anonymous",
    scenario: CrisisScenario | None = None,
    delegate_name: str | None = None,
) -> Iterator[tuple[str, float | None]]:
    """Yield (text_delta, None) until done, then ('', cost_usd)."""
    system = _system_for(mode, scenario, delegate_name)
    tier = _tier_for(mode)
    history = _augment_mentor_history(mode, history)

    final = None
    for delta, result in stream_chat(
        messages=history,
        tier=tier,
        system=system,
        cache_system=True,
        max_tokens=_max_tokens_for(mode),
        temperature=0.8 if mode == ChatMode.CRISIS_BACKROOM else 0.7,
    ):
        if result is None:
            yield _scrub(delta), None
        else:
            final = result

    if final is None:
        return

    record_call(
        user_slack_id,
        FEATURE_KEYS[mode],
        input_tokens=final.input_tokens,
        cached_input_tokens=final.cached_input_tokens,
        cache_write_tokens=final.cache_write_tokens,
        output_tokens=final.output_tokens,
        cost_usd=final.cost_usd,
        model=final.model,
    )
    yield "", final.cost_usd
