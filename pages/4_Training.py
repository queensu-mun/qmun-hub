from __future__ import annotations

from pathlib import Path

import streamlit as st

from lib.auth import require_login
from lib.index import doc_text, list_docs
from lib.ui import brand_footer, inject_global_css, page_header, top_nav

st.set_page_config(page_title="Training · Queen's MUN", page_icon="🌐", layout="wide", initial_sidebar_state="collapsed")
inject_global_css()
user = require_login()
top_nav(user)

ROOT = Path(__file__).resolve().parent.parent
SEED = ROOT / "data" / "seed"

page_header("Training", "The handbook", "Art of MUN, parli pro, awards rubric, common mistakes, the social side.")

tabs = st.tabs([
    "Art of MUN",
    "Parli Pro",
    "Awards Rubric",
    "Common Mistakes",
    "Social Glue",
    "Research Framework",
])

# ----- Art of MUN: pull from indexed archive (auto-imported) -----
with tabs[0]:
    st.markdown("### The Art of MUN (25-26)")
    st.caption(
        "Russell Van Raalte (23/24), edited by Jake Louhikari, Jack Guillemette, "
        "Savannah Summers (current 25-26 directorate)."
    )
    docs = list_docs()
    art = next((d for d in docs if d["doc_id"] == "seed_art_of_mun_25_26"), None)
    if art:
        text = doc_text("seed_art_of_mun_25_26")
        if text:
            with st.container(border=True):
                st.markdown(text[:80_000])
                if len(text) > 80_000:
                    st.caption(f"_(showing first 80,000 chars; full doc is {len(text):,})_")
    else:
        st.info(
            "Art of MUN not yet indexed. Run `python3 scripts/seed_archive.py` to bootstrap.",
            icon="🚧",
        )

# ----- Parli Pro -----
with tabs[1]:
    parli_path = SEED / "parli_pro_cheatsheet.md"
    if parli_path.exists():
        st.markdown(parli_path.read_text())
    else:
        st.warning("parli_pro_cheatsheet.md missing from data/seed/.")

# ----- Awards Rubric -----
with tabs[2]:
    rubric_path = SEED / "awards_rubric.md"
    if rubric_path.exists():
        st.markdown(rubric_path.read_text())
    else:
        st.warning("awards_rubric.md missing from data/seed/.")

# ----- Common Mistakes -----
with tabs[3]:
    st.markdown("# Common Mistakes (and how to avoid them)")
    st.markdown("""
### In committee

- **Reading from notes in formal speeches.** Memorize at least your opener. Eye contact wins rooms.
- **Vague operative clauses.** "Encourage cooperation" is filler. "Calls upon X to allocate Y by Z date" is a clause.
- **Over-motioning.** Chairs notice when you call moderated caucuses to dominate floor time. Three motions a session is plenty.
- **Treating unmoderated caucus as a break.** It's the most important time. Build your bloc, draft your paper, poach signatories.
- **Ignoring small delegations.** They are votes you need at end of debate. Add them as signatories early.

### In research

- **Not reading the study guide.** Chairs notice within 10 minutes of debate.
- **Hallucinating resolution numbers.** If you're not sure, say "[verify]" or describe the resolution by content. Faking a UN reference loses awards.
- **Generic position papers.** "Pakistan supports peace and security" tells the chair nothing. Specific Pakistani policy positions on the actual topic matter.
- **Stopping at Wikipedia.** UN.org has the actual voting records. Use it.

### Pre-conference

- **Position paper at the last minute.** Quality drops, you submit late, chair docks you, and you've lost ~10% of your award shot.
- **Not reading the rules of procedure.** Some conferences run NAIMUN-style, some THIMUN-style, some have quirks. Read the doc.
- **Skipping the Monday meetings.** This is where you find out who's going where, who you'll bloc with, and what mocks are worth practicing.

### Social

- **Skipping the bar after Monday meetings.** Only about 20 of 100 members come. It's the unofficial second meeting, and how you actually break into the team.
- **Not debriefing with your delegation post-conference.** What worked, what didn't, what would you tell your past self before that first session? This is how the team gets better year over year.
""")

# ----- Social Glue -----
with tabs[4]:
    st.markdown("# How to actually be on the team")
    st.markdown("""
The team is socially tight. That's part of why it's good in committee. It can also be intimidating
to walk in as a first-timer, especially against people who are confident public speakers.

### Two ways in

**Show up to the bar after Monday meetings.** This is the unofficial second meeting. The
conversations there are where you actually become part of the team. About 20 of 100 members
come most weeks; we want more.

**Go to conferences.** A weekend of shared travel, shared committee stress, and shared
decompression makes the team feel like a team. You'll come back closer with five or six people
than you ever could from just the meetings.

### The honest version

If you skip both, you'll feel like an outsider regardless of how strong your delegate work is.
The team's competitive performance is downstream of its social cohesion, not the other way around.
Awards follow effort, and effort follows feeling like part of the room.
""")

# ----- Research Framework -----
with tabs[5]:
    st.markdown("# The three-question framework")
    st.markdown("""
The team's standard prep methodology. Works for any country, any topic, GA or crisis.
The Brief generator on the Brief page is built around it.

### 1. Where does my country actually stand?

- What domestic actions have they taken on this issue?
- What's their UN voting record on related resolutions?
- What political constraints at home shape the position? (Lobbies, opposition, base voters.)
- Do they have a stated foreign policy doctrine that applies?

### 2. What's the international landscape?

- What past international action exists? (Treaties, conferences, resolutions, agency reports.)
- Major bloc dynamics on this topic. (G77, NAM, Western bloc, regional organizations.)
- What happens next if this committee does nothing?
- Who's pushing and who's blocking?

### 3. What's my strategy?

- What does winning look like? Be specific. "Support a strong resolution" is not specific.
- Which bloc do I lead, join, or split?
- Which operative clauses do I push, and which do I block?
- Who are my natural allies, and who can I pull off opposing blocs?

### Why three questions

The same shape works for position papers (three paragraphs), opening speeches (three beats),
caucus pitches (three talking points), and crisis directives (situation, response, escalation).
Once you've used it a few times you stop having to think about it.
""")

st.divider()
st.caption("📥 Want to contribute alumni knowledge? Use the Alumni Interview page (link in the sidebar).")

brand_footer()
