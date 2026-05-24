from __future__ import annotations

from datetime import date, datetime
from pathlib import Path

import streamlit as st

from lib import state as state_lib
from lib.auth import require_login
from lib.cache import recent as recent_briefs
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

# ---------------- Pilot welcome panel ----------------
if not st.session_state.get("welcome_dismissed"):
    with st.container(border=True):
        head_col, dismiss_col = st.columns([8, 1])
        with head_col:
            st.markdown(
                "<div style='font-size:0.95rem; font-weight:600; color:var(--text); padding-top:0.1rem;'>"
                "You're in the pilot."
                "</div>",
                unsafe_allow_html=True,
            )
        with dismiss_col:
            if st.button("Got it", key="dismiss_welcome", use_container_width=True):
                st.session_state["welcome_dismissed"] = True
                st.rerun()

        st.markdown(
            "<div style='color:var(--text-muted); font-size:0.88rem; margin-top:0.25rem; margin-bottom:1rem;'>"
            "Six people testing this before the full-team launch in September. "
            "Your job: find what's broken, what's confusing, and what's actually useful."
            "</div>",
            unsafe_allow_html=True,
        )

        w1, w2, w3 = st.columns(3, gap="medium")
        with w1:
            st.markdown(
                """
<div style='border:1px solid var(--border); border-radius:8px; padding:0.85rem 1rem; background:var(--surface-2);'>
  <div style='font-weight:600; font-size:0.85rem; color:var(--text); margin-bottom:0.3rem;'>Archive</div>
  <div style='font-size:0.82rem; color:var(--text-muted); line-height:1.5;'>Search "working paper" or "crisis directive." Does it surface useful docs? Are the results ranked right?</div>
</div>
""",
                unsafe_allow_html=True,
            )
        with w2:
            st.markdown(
                """
<div style='border:1px solid var(--border); border-radius:8px; padding:0.85rem 1rem; background:var(--surface-2);'>
  <div style='font-weight:600; font-size:0.85rem; color:var(--text); margin-bottom:0.3rem;'>Brief generator</div>
  <div style='font-size:0.82rem; color:var(--text-muted); line-height:1.5;'>Generate a mock brief for any country and topic. Is the output something a delegate would actually use?</div>
</div>
""",
                unsafe_allow_html=True,
            )
        with w3:
            st.markdown(
                """
<div style='border:1px solid var(--border); border-radius:8px; padding:0.85rem 1rem; background:var(--surface-2);'>
  <div style='font-weight:600; font-size:0.85rem; color:var(--text); margin-bottom:0.3rem;'>Mentor chatbot</div>
  <div style='font-size:0.82rem; color:var(--text-muted); line-height:1.5;'>Ask it something a first-timer would ask. Does it give Queen's-specific advice or generic UN platitudes?</div>
</div>
""",
                unsafe_allow_html=True,
            )

        st.markdown(
            "<div style='color:var(--text-faint); font-size:0.8rem; margin-top:1rem;'>"
            "Feedback: iMessage or Slack Jack directly."
            "</div>",
            unsafe_allow_html=True,
        )

    st.markdown("<div style='height:1rem;'></div>", unsafe_allow_html=True)

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

with hero_right:
    if HERO_PHOTO.exists():
        st.image(str(HERO_PHOTO), use_container_width=True)
    else:
        st.markdown(
            """
<div class='hero-panel'>
  <div class='hero-panel-mark'>QM</div>
  <div class='hero-panel-title'>Queen's<br/>Model UN</div>
  <div class='hero-panel-meta'>2026 / 2027 · Team Workspace</div>
  <div class='hero-panel-tricolor'>
    <div style='background:#9D1939;'></div>
    <div style='background:#B89D5E;'></div>
    <div style='background:#4B7BBF;'></div>
  </div>
</div>
""",
            unsafe_allow_html=True,
        )

with hero_left:
    st.markdown(f"<div class='hero-display'>{first_name}.</div>", unsafe_allow_html=True)
    st.markdown(
        "<div class='lede' style='margin-top:0.75rem;'>"
        "Everything Queen's MUN needs in one place."
        "</div>",
        unsafe_allow_html=True,
    )

    cmd = st.text_input(
        "Search",
        placeholder="Search docs, countries, topics...",
        label_visibility="collapsed",
        key="home_command_bar",
    )
    if cmd:
        st.session_state["archive_seed_query"] = cmd
        st.switch_page("pages/1_Archive.py")

    st.markdown("<div style='height:0.4rem;'></div>", unsafe_allow_html=True)
    a1, a2, a3 = st.columns(3, gap="small")
    with a1:
        if st.button("Generate brief", use_container_width=True):
            st.switch_page("pages/2_Brief.py")
    with a2:
        if st.button("Ask the mentor", use_container_width=True):
            st.switch_page("pages/3_Chatbot.py")
    with a3:
        if st.button("Training guides", use_container_width=True):
            st.switch_page("pages/4_Training.py")

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

# ---------------- Upcoming socials ----------------
upcoming = state_lib.upcoming_socials(limit=3)
if upcoming:
    st.markdown("<div class='section-head'><h3>Upcoming socials</h3></div>", unsafe_allow_html=True)
    for s in upcoming:
        days_to = ""
        try:
            d = datetime.fromisoformat(s["date"]).date()
            delta = (d - date.today()).days
            if delta == 0:
                days_to = "today"
            elif delta == 1:
                days_to = "tomorrow"
            elif delta > 1:
                days_to = f"in {delta} days"
        except Exception:
            pass
        location = s.get("location") or ""
        notes = s.get("notes") or ""
        meta_bits = [s["date"]]
        if days_to:
            meta_bits.append(days_to)
        if location:
            meta_bits.append(location)

        # First image attachment (if any) gets a small thumbnail
        first_image = next(
            (a for a in (s.get("attachments") or []) if (a.get("mime_type") or "").startswith("image/")),
            None,
        )
        if first_image:
            row_cols = st.columns([1, 4])
            try:
                row_cols[0].image(first_image["stored_path"], use_container_width=True)
            except Exception:
                pass
            row_cols[1].markdown(
                f"""
<div class='activity-row' style='border:none; padding-left:0;'>
  <div>
    <div class='activity-title'>{s.get('type', 'social').title()}</div>
    <div class='activity-meta'>{' · '.join(meta_bits)}{(' · ' + notes) if notes else ''}</div>
  </div>
</div>
""",
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                f"""
<div class='activity-row'>
  <div>
    <div class='activity-title'>{s.get('type', 'social').title()}</div>
    <div class='activity-meta'>{' · '.join(meta_bits)}{(' · ' + notes) if notes else ''}</div>
  </div>
</div>
""",
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
