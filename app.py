from __future__ import annotations

import streamlit as st

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
from lib.ui import (
    brand_footer,
    feature_card,
    inject_global_css,
    sidebar_brand,
    user_chip,
)

st.set_page_config(
    page_title="Queen's MUN",
    page_icon="🌐",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={"About": "Queen's Model UN."},
)

inject_global_css()

user = require_login()

# ---------------- Sidebar ----------------
with st.sidebar:
    st.markdown(sidebar_brand(), unsafe_allow_html=True)
    st.markdown(user_chip(user.name, user.role.title()), unsafe_allow_html=True)
    if st.button("Sign out", use_container_width=True):
        st.session_state.clear()
        st.rerun()

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
        "Everything Queen's MUN needs in one place. "
        "Brief generation, archive search, training, and a chatbot that knows the team's playbook."
        "</div>",
        unsafe_allow_html=True,
    )

    # Quick stats
    from lib.index import index_stats
    stats = index_stats()
    confs = state.get("conferences", [])
    st.markdown(
        f"""
<div class='stat-line'>
  <div><span class='stat-num'>{stats['n_docs']}</span> docs indexed</div>
  <div><span class='stat-num'>{stats['n_chunks']}</span> chunks searchable</div>
  <div><span class='stat-num'>{len(confs)}</span> conferences tracked</div>
</div>
""",
        unsafe_allow_html=True,
    )

with hero_right:
    st.markdown(hero_illustration(), unsafe_allow_html=True)

st.markdown("<div style='height: 3rem;'></div>", unsafe_allow_html=True)

# ---------------- This week ----------------
if mon or thu:
    st.markdown("<div class='eyebrow'>This week</div>", unsafe_allow_html=True)
    st.markdown("<h2 style='margin-top: 0.5rem;'>What's on deck</h2>", unsafe_allow_html=True)
    st.markdown("<div style='height: 1.25rem;'></div>", unsafe_allow_html=True)

    cols = st.columns(2, gap="medium")
    if mon:
        with cols[0]:
            with st.container(border=True):
                st.markdown(
                    f"""
<div class='week-card-day'>Monday Mock</div>
<div class='week-card-committee'>{mon['committee']}</div>
<div class='week-card-topic'>{mon['topic']}</div>
""",
                    unsafe_allow_html=True,
                )
                st.page_link("pages/2_Brief.py", label="Prep a brief →")
    if thu:
        with cols[1]:
            with st.container(border=True):
                st.markdown(
                    f"""
<div class='week-card-day'>Thursday Mock</div>
<div class='week-card-committee'>{thu['committee']}</div>
<div class='week-card-topic'>{thu['topic']}</div>
""",
                    unsafe_allow_html=True,
                )
                st.page_link("pages/2_Brief.py", label="Prep a brief →")
    st.markdown("<div style='height: 3rem;'></div>", unsafe_allow_html=True)

# ---------------- Quick links ----------------
st.markdown("<div class='eyebrow'>Get to work</div>", unsafe_allow_html=True)
st.markdown("<h2 style='margin-top: 0.5rem;'>Tools</h2>", unsafe_allow_html=True)
st.markdown("<div style='height: 1.25rem;'></div>", unsafe_allow_html=True)

cols = st.columns(3, gap="medium")
features_top = [
    (brief(size=22), "Brief", "Generate a starting point on any country, topic, or committee.", "pages/2_Brief.py"),
    (archive(size=22), "Archive", "Search past papers, study guides, and alumni interviews.", "pages/1_Archive.py"),
    (chat(size=22), "Chatbot", "Mentor for prep, backroom for crisis mocks, parli pro for chairs.", "pages/3_Chatbot.py"),
]
for col, (icon, title, blurb, path) in zip(cols, features_top):
    with col:
        with st.container(border=True):
            feature_card(icon_svg=icon, title=title, blurb=blurb)
            st.page_link(path, label="Open →")

st.markdown("<div style='height: 1rem;'></div>", unsafe_allow_html=True)

cols2 = st.columns(3, gap="medium")
features_bottom = [
    (book(size=22), "Training", "Art of MUN, parli pro cheat sheet, awards rubric, common mistakes.", "pages/4_Training.py"),
    (mic(size=22), "Tell us what you know", "Share what you learned with the team. Five minutes, future-proofs the playbook.", "pages/6_Alumni_Interview.py"),
]
if user.is_exec:
    features_bottom.append(
        (target(size=22), "Director tools", "Weekly topics, conferences, assignments, costs, archive curation.", "pages/5_Director.py")
    )
else:
    # Spacer for visual symmetry on delegate view
    features_bottom.append((None, None, None, None))

for col, (icon, title, blurb, path) in zip(cols2, features_bottom):
    with col:
        if icon is None:
            st.markdown("&nbsp;", unsafe_allow_html=True)
        else:
            with st.container(border=True):
                feature_card(icon_svg=icon, title=title, blurb=blurb)
                st.page_link(path, label="Open →")

brand_footer()
