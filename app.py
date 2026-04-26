from __future__ import annotations

import streamlit as st
import streamlit.components.v1 as components

from lib import state as state_lib
from lib.auth import require_login
from lib.cache import recent as recent_briefs
from lib.icons import hero_illustration
from lib.ui import brand_footer, inject_global_css, top_nav

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

with hero_right:
    components.html(hero_illustration(), height=320)

st.markdown("<div style='height:2.5rem;'></div>", unsafe_allow_html=True)

# ---------------- This week ----------------
if mon or thu:
    st.markdown("<div class='section-head'><h3>This week</h3></div>", unsafe_allow_html=True)

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
else:
    st.markdown("<div class='section-head'><h3>This week</h3></div>", unsafe_allow_html=True)
    st.markdown(
        "<div class='subtle' style='padding: 1rem 0 2rem;'>"
        "No mock topics set. The director can set them in "
        "<a href='/Director' style='color:var(--accent); border-bottom:none;'>Director tools</a>."
        "</div>",
        unsafe_allow_html=True,
    )

# ---------------- Recent activity ----------------
st.markdown("<div class='section-head'><h3>Recent briefs</h3></div>", unsafe_allow_html=True)

briefs = recent_briefs(limit=4)
if briefs:
    for b in briefs:
        st.markdown(
            f"""
<div class='activity-row'>
  <div>
    <div class='activity-title'>{b['country']} <span class='activity-sep'>·</span> {b['committee']}</div>
    <div class='activity-meta'>{b['topic']}</div>
  </div>
  <div class='activity-tag'>{b['depth']}</div>
</div>
""",
            unsafe_allow_html=True,
        )
else:
    st.markdown(
        "<div class='subtle' style='padding: 0.75rem 0 0;'>"
        "No briefs generated yet this week. <a href='/Brief' style='color:var(--accent); border-bottom:none;'>Generate your first →</a>"
        "</div>",
        unsafe_allow_html=True,
    )

brand_footer()
