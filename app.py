from __future__ import annotations

import streamlit as st

from lib import state as state_lib
from lib.auth import require_login
from lib.ui import brand_footer, inject_global_css

st.set_page_config(
    page_title="Queen's MUN",
    page_icon="🌐",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={"About": "Queen's Model UN."},
)

inject_global_css()

user = require_login()

with st.sidebar:
    st.markdown("### Queen's MUN")
    st.caption("Team workspace")
    st.divider()
    st.markdown(f"**{user.name}**")
    st.caption(user.role.title())
    if st.button("Sign out", use_container_width=True):
        st.session_state.clear()
        st.rerun()

# ---------------- Hero ----------------
state = state_lib.load()
weekly = state.get("weekly_topics", {})
mon = weekly.get("monday")
thu = weekly.get("thursday")

st.markdown(f"## Hey {user.name.split()[0] if user.name else 'there'}.")
if mon or thu:
    cols = st.columns(2)
    if mon:
        with cols[0]:
            with st.container(border=True):
                st.caption("MONDAY MOCK")
                st.markdown(f"**{mon['committee']}**")
                st.markdown(mon["topic"])
                st.page_link("pages/2_Brief.py", label="Prep a brief →")
    if thu:
        with cols[1]:
            with st.container(border=True):
                st.caption("THURSDAY MOCK")
                st.markdown(f"**{thu['committee']}**")
                st.markdown(thu["topic"])
                st.page_link("pages/2_Brief.py", label="Prep a brief →")
else:
    st.caption("No mock topics set yet this week.")

st.markdown("<br/>", unsafe_allow_html=True)

# ---------------- Quick links ----------------
left, right = st.columns([2, 1], gap="large")

with left:
    st.markdown("### Get to work")

    cols = st.columns(2)
    with cols[0]:
        with st.container(border=True):
            st.markdown("**🌍 Brief**")
            st.caption("Country, committee, topic. Get a starting point in 30 seconds.")
            st.page_link("pages/2_Brief.py", label="Open")
        with st.container(border=True):
            st.markdown("**📚 Archive**")
            st.caption("Search past papers, study guides, and what alumni said about each conference.")
            st.page_link("pages/1_Archive.py", label="Open")
    with cols[1]:
        with st.container(border=True):
            st.markdown("**💬 Chatbot**")
            st.caption("Coach you through prep, run a crisis backroom, or call a procedural ruling.")
            st.page_link("pages/3_Chatbot.py", label="Open")
        with st.container(border=True):
            st.markdown("**🎓 Training**")
            st.caption("Art of MUN, parli pro, common mistakes, awards rubric.")
            st.page_link("pages/4_Training.py", label="Open")

with right:
    if user.is_exec:
        with st.container(border=True):
            st.markdown("**🎯 Director tools**")
            st.caption("Weekly topics, conferences, assignments, archive curation, costs.")
            st.page_link("pages/5_Director.py", label="Open")
    with st.container(border=True):
        st.markdown("**🎙️ Got knowledge?**")
        st.caption(
            "If you've been to a conference or have something to share with future delegates, "
            "the alumni interview is how it gets into the team's memory."
        )
        st.page_link("pages/6_Alumni_Interview.py", label="Share what you learned")

brand_footer()
