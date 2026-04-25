from __future__ import annotations

from pathlib import Path

import streamlit as st

from lib.auth import require_login
from lib.index import doc_text, list_docs
from lib.ui import brand_footer, inject_global_css, page_header

st.set_page_config(page_title="Training · QMUN Hub", page_icon="🎓", layout="wide")
inject_global_css()
user = require_login()

ROOT = Path(__file__).resolve().parent.parent
SEED = ROOT / "data" / "seed"

page_header("🎓 Training", "Reference handbook, parli pro, awards rubrics, common mistakes. Zero AI cost on this page.")

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

- **Skipping the bar after Monday meetings.** Per Jack's notes: only ~20 of 100 members come. Going is how you actually break into the team.
- **Not debriefing with your delegation post-conference.** What worked, what didn't, what would you tell your past self before that first session? This is how the team gets better year over year.
""")

# ----- Social Glue -----
with tabs[4]:
    st.markdown("# Social Glue")
    st.markdown("""
The Queen's MUN team is socially tight. Per Jack's MUN Claude self-interview:

> It can be intimidating to walk onto a team of socially tight individuals who are really good
> at public speaking. The two ways to break in socially are by **showing up to the bar** after
> Monday meetings and by **going to conferences**. Going to the bar makes us a better team
> because we are closer and our friends; we encourage all new members to come, but we need
> more — only about 20 people a week join out of a 100-person team.

### What this means for first-timers

- The post-Monday-meeting bar trip is the unofficial second meeting. The conversations there
  are where you actually become part of the team.
- Conferences are accelerated bonding. A weekend of shared travel, shared committee stress,
  and shared decompression makes the team feel like a team.
- If you skip both, you'll feel like an outsider regardless of how good your delegate work is.

### What this means for the directorate

- The team's competitive performance is downstream of its social cohesion.
- Awards follow effort and substance, but the willingness to put in effort follows feeling
  like part of the room.
- Bar attendance is a leading indicator of how well the team will travel together.
""")

# ----- Research Framework -----
with tabs[5]:
    st.markdown("# Queen's three-question research framework")
    st.markdown("""
The team's standard research methodology, used to prep any country / character on any topic.
Encoded into the Brief Generator on the Brief page.

### Question 1: Country / character position

> How does my country (or character) feel about this issue?

- What domestic actions has the country already taken on this issue?
- What's their voting record at the UN on related resolutions?
- What domestic political constraints shape the position? (Lobbies, opposition pressure, base voters)
- Do they have a stated foreign policy doctrine that applies here?

### Question 2: International context

> How does the international community feel about this issue?

- What past international actions exist? (Treaties, conferences, resolutions, UN agency reports)
- Major bloc dynamics relevant to this topic (G77, NAM, Western bloc, regional organizations)
- What are the next steps absent intervention by this committee?
- Who are the issue advocates and who are the blockers?

### Question 3: Committee strategy

> What is my country's strategy in this committee?

- What does winning look like? (Specific, not "support a strong resolution")
- Which bloc do I lead, join, or split?
- What concrete operative clauses do I push, and which do I block?
- Who are my natural allies, and who can I pull off opposing blocs?

### Why three questions

This same framework works for position papers (3 paragraphs), opening speeches (3 beats),
unmoderated caucus pitches (3 talking points), and crisis directives (situation, response,
escalation). Once internalized, it scales.
""")

st.divider()
st.caption("📥 Want to contribute alumni knowledge? Use the Alumni Interview page (link in the sidebar).")

brand_footer()
