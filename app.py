from __future__ import annotations

import streamlit as st
import streamlit.components.v1 as components

from lib import state as state_lib
from lib.auth import require_login
from lib.icons import (
    archive,
    book,
    brief,
    chat,
    hero_illustration,
    mic,
    target,
)
from lib.index import index_stats
from lib.ui import (
    brand_footer,
    feature_tile,
    inject_global_css,
    top_nav,
)

st.set_page_config(
    page_title="Queen's MUN",
    page_icon="🌐",
    layout="wide",
    initial_sidebar_state="collapsed",
    menu_items={"About": "Queen's Model UN."},
)

inject_global_css()
user = require_login()
top_nav(user)

# ---------------- Hero ----------------
state = state_lib.load()
weekly = state.get("weekly_topics", {})
mon = weekly.get("monday")
thu = weekly.get("thursday")
first_name = user.name.split()[0] if user.name else "there"

hero_left, hero_right = st.columns([1.1, 1], gap="large")

with hero_left:
    st.markdown("<div class='eyebrow'>Welcome back</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='hero-display'>{first_name}.</div>", unsafe_allow_html=True)
    st.markdown(
        "<div class='lede' style='margin-top:1.25rem;'>"
        "Everything Queen's MUN needs in one place. Brief generation, archive search, "
        "training, and a chatbot that knows the team's playbook."
        "</div>",
        unsafe_allow_html=True,
    )
    stats = index_stats()
    confs = state.get("conferences", [])
    st.markdown(
        f"""
<div class='stat-line'>
  <div><span class='stat-num'>{stats['n_docs']}</span>docs indexed</div>
  <div><span class='stat-num'>{stats['n_chunks']}</span>chunks searchable</div>
  <div><span class='stat-num'>{len(confs)}</span>conferences tracked</div>
</div>
""",
        unsafe_allow_html=True,
    )

with hero_right:
    components.html(hero_illustration(), height=320)

st.markdown("<div style='height:3rem;'></div>", unsafe_allow_html=True)

# ---------------- This week ----------------
if mon or thu:
    st.markdown(
        "<div class='section-head'><h3>This week</h3>"
        "<a href='/Director' class='section-aux'>Manage in Director →</a></div>",
        unsafe_allow_html=True,
    )

    cells = []
    if mon:
        cells.append(
            f"""
<div class='week-cell'>
  <div class='week-cell-day'>Monday Mock</div>
  <div class='week-cell-committee'>{mon['committee']}</div>
  <div class='week-cell-topic'>{mon['topic']}</div>
</div>
"""
        )
    if thu:
        cells.append(
            f"""
<div class='week-cell gold'>
  <div class='week-cell-day'>Thursday Mock</div>
  <div class='week-cell-committee'>{thu['committee']}</div>
  <div class='week-cell-topic'>{thu['topic']}</div>
</div>
"""
        )
    st.markdown(f"<div class='week-strip'>{''.join(cells)}</div>", unsafe_allow_html=True)

# ---------------- Tools ----------------
st.markdown("<div class='section-head'><h3>Tools</h3></div>", unsafe_allow_html=True)

cols = st.columns(3, gap="large")
with cols[0]:
    feature_tile(
        icon_svg=brief(size=22),
        title="Brief",
        blurb="Generate a starting point on any country, topic, or committee.",
        page_path="pages/2_Brief.py",
    )
with cols[1]:
    feature_tile(
        icon_svg=archive(size=22),
        title="Archive",
        blurb="Search past papers, study guides, and alumni interviews.",
        page_path="pages/1_Archive.py",
    )
with cols[2]:
    feature_tile(
        icon_svg=chat(size=22),
        title="Chatbot",
        blurb="Mentor for prep, backroom for crisis, parli pro for chairs.",
        page_path="pages/3_Chatbot.py",
    )

st.markdown("<div style='height:1.5rem;'></div>", unsafe_allow_html=True)

cols2 = st.columns(3, gap="large")
with cols2[0]:
    feature_tile(
        icon_svg=book(size=22),
        title="Training",
        blurb="Art of MUN, parli pro cheat sheet, awards rubric, common mistakes.",
        page_path="pages/4_Training.py",
    )
with cols2[1]:
    feature_tile(
        icon_svg=mic(size=22),
        title="Tell us what you know",
        blurb="Share what you learned with the team. Five minutes, future-proofs the playbook.",
        page_path="pages/6_Alumni_Interview.py",
    )
with cols2[2]:
    if user.is_exec:
        feature_tile(
            icon_svg=target(size=22),
            title="Director tools",
            blurb="Weekly topics, conferences, assignments, costs, archive curation.",
            page_path="pages/5_Director.py",
        )

brand_footer()
