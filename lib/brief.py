"""Country brief generator using the Queen's MUN team's 3-question framework.

1. How does your country/character feel about this issue? Domestic actions taken?
2. How does the international community feel? Past international actions? Next steps?
3. What is your strategy in committee? How do you want to solve this?
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterator, Literal

from lib import state as state_lib
from lib.budget import record_call
from lib.cache import CacheKey, get as cache_get, put as cache_put, week_start_of
from lib.claude import Tier, chat, stream_chat

Depth = Literal["mock", "conference"]


@dataclass
class BriefRequest:
    country: str
    topic: str
    committee: str
    depth: Depth
    notes: str | None = None
    user_slack_id: str = "anonymous"
    delegate_name: str | None = None     # if known, brief tailors to roster status


def _delegate_context_block(name: str | None) -> str:
    """Look up delegate in roster; return a coaching context block, else ''."""
    if not name:
        return ""
    entry = state_lib.roster_lookup(name)
    if not entry:
        return ""
    status = entry.get("status", "rookie")
    year = entry.get("year")
    if status == "rookie":
        guidance = (
            "This delegate is new to the Queen's MUN team. Prioritize procedural "
            "fundamentals and confidence-building. Define jargon the first time "
            "it appears. Lean toward 1-2 strong, simple operative clauses they can "
            "actually deliver, over a complex bloc strategy they cannot execute yet."
        )
    else:
        guidance = (
            "This delegate is a returning veteran. Skip the basics. Push for "
            "tactical edge: bloc-flipping, parliamentary procedure manipulation, "
            "high-leverage operative clauses. Treat them as someone aiming for an "
            "award-tier performance."
        )
    return (
        "\n\n--- DELEGATE CONTEXT ---\n"
        f"Delegate: {entry['name']} (year {year}, {status})\n"
        f"Coaching note: {guidance}\n"
    )


@dataclass
class Brief:
    markdown: str
    cost_usd: float
    cache_hit: bool
    archive_citations: list[str] = field(default_factory=list)


_THREE_Q_FRAMEWORK = """\
Queen's MUN's three-question research framework:

1. **Country / Character position.** How does the represented party feel about this issue?
   - Domestic actions taken
   - Voting record at the UN (cite real resolution numbers when known)
   - Domestic political constraints that shape the position
2. **International context.** How does the international community feel?
   - Major bloc dynamics relevant to this topic
   - Past international action (treaties, resolutions, conferences) with citations
   - Likely next steps absent intervention
3. **Committee strategy.** What is the represented party's strategy in this committee?
   - Goals (be specific: what does winning look like?)
   - Bloc to lead, join, or split
   - Concrete operative clauses to push or block
"""

_MOCK_INSTRUCTIONS = """\
You are generating a **MOCK BRIEF** for a 2-hour Queen's MUN practice committee.
- Length: ~1 page (400-600 words)
- Format: markdown, with the three sections above as ## headings
- Tone: tight, scannable, gives the delegate enough to speak intelligently in 30 minutes of prep
- Skip exhaustive background; assume the delegate will read the study guide separately
"""

_CONFERENCE_INSTRUCTIONS = """\
You are generating a **CONFERENCE BRIEF** for an actual North American collegiate MUN conference.
- Length: full multi-page (1200-2000 words)
- Format: markdown, with the three sections above as ## headings, each section subdivided
- Cite real UN resolutions by number where applicable. If unsure of a resolution number, say "[verify]" rather than invent.
- End with a final section: ## Five proposed operative clauses
  - Lead with the strongest, most concrete, most enforceable
  - Each clause should be ready to drop into a working paper verbatim
- End with a final section: ## Common traps
  - Pitfalls specific to this country/topic combination that can sink an inexperienced delegate
"""

_BASE_SYSTEM = """\
You are an experienced Model UN coach for the Queen's University team (currently 3rd in Canada,
with strength on the North American collegiate circuit). You generate research briefs for
delegates that strictly follow Queen's three-question framework.

You write in a direct, useful tone. No filler. No hedging. No "in conclusion" paragraphs.
You cite real UN resolutions, real treaties, real precedents. When you're not certain of a
specific number or date, you mark it with "[verify]" rather than fabricate. Hallucinating
a resolution number is the worst sin you can commit.

You write in markdown. You use bold sparingly to mark a delegate's likely strongest moves.

**HARD RULE: never use em dashes (the long dash character).** Do not use it in headers, prose, or anywhere else. Use one of these instead, depending on the function:
- For a parenthetical aside: use parentheses or commas. Wrong: "Brazil, a BRICS leader, voted yes." (good). "Brazil — a BRICS leader — voted yes." (forbidden).
- For an explanation or expansion: use a colon. Wrong: "China's strategy is clear: block Chapter VII framing." (good). "China's strategy — block Chapter VII framing." (forbidden).
- For separating title and subtitle in a header: use a vertical bar or colon. Wrong: "China | Conference Brief" or "China: Conference Brief" (good). "China — Conference Brief" (forbidden).
- Use regular hyphens for compound words (e.g. "non-interference") and en dashes for date ranges if needed (e.g. "1975-1979" with regular hyphen is fine).

This rule is non-negotiable. Re-read your output before finalizing and remove any em dashes you wrote.

The team's three-question framework, which you must follow as the brief's section structure:

{framework}

The team's prep philosophy:
- Mock briefs are short and tactical (delegate has 30 min to prep, then speaks for 2 hours)
- Conference briefs are full and strategic (delegate has days to prep, then speaks for ~12 hours over a weekend)
- For both: substance over performance. Specific operative clauses beat vague calls to "encourage cooperation".
- Bloc-building matters as much as individual brilliance
- Awards follow effort and substance: chairs reward delegates who clearly know their country's actual interests

Output ONLY the brief itself in markdown. Do not include preamble, meta-commentary, or "here is the brief".
""".format(framework=_THREE_Q_FRAMEWORK)


def _build_system(depth: Depth, delegate_name: str | None = None) -> str:
    instructions = _MOCK_INSTRUCTIONS if depth == "mock" else _CONFERENCE_INSTRUCTIONS
    delegate_block = _delegate_context_block(delegate_name)
    return f"{_BASE_SYSTEM}\n\n---\n\n{instructions}{delegate_block}"


def _scrub_em_dashes(text: str) -> str:
    """Replace em/en dashes used as punctuation with safe alternatives.

    Heuristic: if surrounded by spaces, treat as parenthetical and use ', '.
    Otherwise (rare; usually dates), replace with regular hyphen.
    """
    text = text.replace(" — ", ", ").replace(" – ", ", ")
    text = text.replace("—", "-").replace("–", "-")
    return text


def _archive_brief_context(query: str, max_passages: int = 3) -> str:
    """Pull the most relevant passages from the team archive (background guides,
    sample position papers, training material, alumni wisdom) to ground the brief
    in how Queen's actually prepares committees like this one."""
    if not query.strip():
        return ""
    try:
        from lib.search import retrieve_passages
        passages = retrieve_passages(
            query,
            doc_types=["background_guide", "position_paper", "training", "alumni_interview"],
            top_k=max_passages,
        )
    except Exception:
        return ""
    if not passages:
        return ""
    blocks = [f'From "{p.doc_title}":\n{p.text.strip()}' for p in passages]
    return (
        "\n\n--- QUEEN'S ARCHIVE (how this team has prepped, written, and argued committees "
        "like this; weave in any relevant tactical, structural, or conference-specific insight) ---\n"
        + "\n\n".join(blocks)
    )


def _build_user_message(req: BriefRequest) -> str:
    parts = [
        f"**Country / Character:** {req.country}",
        f"**Committee:** {req.committee}",
        f"**Topic:** {req.topic}",
    ]
    if req.notes:
        parts.append(f"**Director / delegate notes:** {req.notes}")
    parts.append("\nGenerate the brief.")
    msg = "\n".join(parts)
    archive = _archive_brief_context(f"{req.committee} {req.topic}")
    return msg + archive


def generate(req: BriefRequest, *, force_refresh: bool = False) -> Brief:
    key = CacheKey(
        country=req.country,
        topic=req.topic,
        committee=req.committee,
        week_start=week_start_of(),
        depth=req.depth,
    )

    if not force_refresh:
        if hit := cache_get(key):
            md, original_cost = hit
            return Brief(markdown=md, cost_usd=0.0, cache_hit=True, archive_citations=[])

    tier = Tier.CHEAP if req.depth == "mock" else Tier.SMART
    max_tokens = 1200 if req.depth == "mock" else 4000

    system = _build_system(req.depth, req.delegate_name)
    user = _build_user_message(req)

    result = chat(
        messages=[{"role": "user", "content": user}],
        tier=tier,
        system=system,
        cache_system=True,
        max_tokens=max_tokens,
        temperature=0.7,
    )

    clean = _scrub_em_dashes(result.text)
    cache_put(key, clean, result.cost_usd)
    record_call(
        req.user_slack_id,
        "brief",
        input_tokens=result.input_tokens,
        cached_input_tokens=result.cached_input_tokens,
        cache_write_tokens=result.cache_write_tokens,
        output_tokens=result.output_tokens,
        cost_usd=result.cost_usd,
        model=result.model,
    )

    return Brief(markdown=clean, cost_usd=result.cost_usd, cache_hit=False)


def generate_streaming(req: BriefRequest) -> Iterator[tuple[str, Brief | None]]:
    """Stream brief markdown deltas; final yield is ('', Brief)."""
    key = CacheKey(
        country=req.country,
        topic=req.topic,
        committee=req.committee,
        week_start=week_start_of(),
        depth=req.depth,
    )
    if hit := cache_get(key):
        md, _cost = hit
        yield md, Brief(markdown=md, cost_usd=0.0, cache_hit=True)
        return

    tier = Tier.CHEAP if req.depth == "mock" else Tier.SMART
    max_tokens = 1200 if req.depth == "mock" else 4000
    system = _build_system(req.depth, req.delegate_name)
    user = _build_user_message(req)

    final = None
    for delta, result in stream_chat(
        messages=[{"role": "user", "content": user}],
        tier=tier,
        system=system,
        cache_system=True,
        max_tokens=max_tokens,
        temperature=0.7,
    ):
        if result is None:
            yield delta, None
        else:
            final = result

    if final is None:
        return

    clean = _scrub_em_dashes(final.text)
    cache_put(key, clean, final.cost_usd)
    record_call(
        req.user_slack_id,
        "brief",
        input_tokens=final.input_tokens,
        cached_input_tokens=final.cached_input_tokens,
        cache_write_tokens=final.cache_write_tokens,
        output_tokens=final.output_tokens,
        cost_usd=final.cost_usd,
        model=final.model,
    )
    yield "", Brief(markdown=clean, cost_usd=final.cost_usd, cache_hit=False)
