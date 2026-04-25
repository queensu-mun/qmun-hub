import streamlit as st

from lib.auth import require_login
from lib.ui import inject_global_css, page_header, brand_footer

st.set_page_config(page_title="Training · QMUN Hub", page_icon="🎓", layout="wide")
inject_global_css()
user = require_login()

page_header("🎓 Training", "Reference handbook, parli pro, how-to-win guides — zero AI cost.")

tabs = st.tabs([
    "Art of MUN",
    "How to win — GA",
    "How to win — Crisis",
    "Parli Pro",
    "Awards Rubric",
    "Common Mistakes",
    "Social Glue",
])

with tabs[0]:
    st.markdown("### The Art of MUN (25-26)")
    st.caption("Imported from Russell Van Raalte (23/24), edited by current directorate.")
    st.info("Auto-imports from Drive in Phase 3 (July). Doc ID: `1phmTrEY6lXNx4Lk5IIxlXn7BGkQNMYEAdxFUp5o5fhQ`", icon="📄")

with tabs[1]:
    st.markdown("### How to win — General Assembly")
    st.caption("By Jack Guillemette.")
    st.info("Locate Jack's GA-win doc in Drive and import here.", icon="📄")

with tabs[2]:
    st.markdown("### How to win — Crisis")
    st.caption("By Jake Louhikari.")
    st.info("Locate Jake's crisis-win doc in Drive and import here.", icon="📄")

with tabs[3]:
    st.markdown("### Parliamentary Procedure Cheat Sheet")
    st.markdown("**Points:** Order · Personal Privilege · Inquiry · Information")
    st.markdown("**Motions:** Open/Close debate · Moderated caucus (topic, time) · Unmoderated · Table · Adjourn")
    st.markdown("**Voting:** Procedural (simple majority) vs. Substantive (sometimes 2/3) · Right of Reply · Divide the Question")

with tabs[4]:
    st.markdown("### Awards Rubric")
    st.caption("Compiled across major North American conferences.")
    st.info("Per-conference rubric breakdown lands in Phase 3.", icon="🚧")

with tabs[5]:
    st.markdown("### Common Mistakes (and how to avoid them)")
    st.markdown("- Reading from notes in formal speeches")
    st.markdown("- Vague operative clauses (\"encourage cooperation\")")
    st.markdown("- Ignoring small delegations — they're votes")
    st.markdown("- Treating unmod as a break")
    st.markdown("- Not reading the study guide")

with tabs[6]:
    st.markdown("### Social Glue")
    st.markdown(
        "Two ways to break in socially: **show up to the bar** after Monday meetings, "
        "and **go to conferences**. Only ~20 of 100 members come to the bar each week — "
        "we want more. The smaller-group bonding is what makes us a better team in the room."
    )

brand_footer()
