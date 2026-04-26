from __future__ import annotations

from datetime import date, datetime
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

from lib import state as state_lib
from lib.auth import require_login
from lib.cache import recent as recent_briefs
from lib.icons import hero_illustration
from lib.ui import brand_footer, inject_global_css, top_nav

ROOT = Path(__file__).resolve().parent
HERO_PHOTO = ROOT / "assets" / "hero.jpg"

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

state = state_lib.load()
weekly = state.get("weekly_topics", {})
mon = weekly.get("monday")
thu = weekly.get("thursday")
announcement = state.get("announcement")
first_name = user.name.split()[0] if user.name else "there"
my_assignments = state_lib.assignments_for_delegate(user.name)

# ---------------- Announcement banner ----------------
if announcement and announcement.get("text"):
    st.markdown(
        f"""
<div class='qmun-announce'>
  <div class='qmun-announce-dot'></div>
  <div class='qmun-announce-label'>From the director</div>
  <div>{announcement['text']}</div>
</div>
""",
        unsafe_allow_html=True,
    )

# ---------------- Hero ----------------
hero_left, hero_right = st.columns([1.2, 1], gap="large")

with hero_left:
    st.markdown(f"<div class='hero-display'>{first_name}.</div>", unsafe_allow_html=True)
    st.markdown(
        "<div class='lede' style='margin-top:0.75rem;'>"
        "Everything Queen's MUN needs in one place."
        "</div>",
        unsafe_allow_html=True,
    )

    # Command bar
    cb_cols = st.columns([5, 1])
    with cb_cols[0]:
        cmd = st.text_input(
            "Search the archive, prep a country, ask a question...",
            placeholder="Search the archive, prep a country, ask a question...",
            label_visibility="collapsed",
            key="home_command_bar",
        )
    with cb_cols[1]:
        action = st.selectbox(
            "Action",
            ["Search", "Brief", "Ask"],
            label_visibility="collapsed",
            key="home_command_action",
        )

    if cmd:
        if action == "Search":
            st.session_state["archive_seed_query"] = cmd
            st.switch_page("pages/1_Archive.py")
        elif action == "Brief":
            st.session_state["brief_seed_topic"] = cmd
            st.switch_page("pages/2_Brief.py")
        elif action == "Ask":
            st.session_state["mentor_seed_question"] = cmd
            st.switch_page("pages/3_Chatbot.py")

with hero_right:
    if HERO_PHOTO.exists():
        st.image(str(HERO_PHOTO), use_container_width=True)
    else:
        components.html(hero_illustration(), height=280)
        st.markdown(
            "<div class='subtle' style='font-size:0.72rem; text-align:right; margin-top:4px; color:var(--text-faint);'>"
            "Drop a photo at <code>assets/hero.jpg</code> to replace this illustration."
            "</div>",
            unsafe_allow_html=True,
        )

st.markdown("<div style='height:2.5rem;'></div>", unsafe_allow_html=True)

# ---------------- Your prep status (delegates) ----------------
if my_assignments:
    st.markdown("<div class='section-head'><h3>Your prep</h3></div>", unsafe_allow_html=True)
    border_styles = ["", "gold", "blue"]

    cols = st.columns(min(len(my_assignments), 3), gap="medium")
    for i, a in enumerate(my_assignments[:3]):
        conf = a.get("conference") or {}
        when = conf.get("start_date", "")
        days_to = ""
        if when:
            try:
                d = datetime.fromisoformat(when).date()
                delta = (d - date.today()).days
                if delta > 0:
                    days_to = f" · in {delta} days"
                elif delta == 0:
                    days_to = " · today"
                elif delta > -7:
                    days_to = f" · {abs(delta)} days ago"
            except Exception:
                pass

        with cols[i % len(cols)]:
            style = border_styles[i % len(border_styles)]
            st.markdown(
                f"""
<div class='prep-card {style}'>
  <div class='prep-conf'>{conf.get('name', 'Conference')}</div>
  <div class='prep-role'>{a['country_or_character']} <span class='subtle' style='font-weight:500;'>·</span> {a['committee']}</div>
  <div class='prep-when'>{when or ''}{days_to}</div>
  <div class='prep-checks'>
    <span class='pending'>○ Brief</span>
    <span class='pending'>○ Position paper</span>
    <span class='pending'>○ Mock</span>
  </div>
</div>
""",
                unsafe_allow_html=True,
            )
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
elif user.is_exec:
    st.markdown("<div class='section-head'><h3>This week</h3></div>", unsafe_allow_html=True)
    st.markdown(
        "<div class='subtle' style='padding: 1rem 0 2rem;'>"
        "No mock topics set. Configure in "
        "<a href='/Director' style='color:var(--accent); border-bottom:none;'>Director tools</a>."
        "</div>",
        unsafe_allow_html=True,
    )

# ---------------- Recent briefs ----------------
briefs = recent_briefs(limit=4)
if briefs:
    st.markdown("<div class='section-head'><h3>Recent briefs</h3></div>", unsafe_allow_html=True)
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

brand_footer()
