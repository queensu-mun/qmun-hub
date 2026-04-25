from __future__ import annotations

import streamlit as st

from lib.auth import require_login
from lib.ui import inject_global_css, page_header, brand_footer

st.set_page_config(
    page_title="QMUN Hub",
    page_icon="🌐",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={"About": "Queen's MUN — institutional knowledge + delegate training."},
)

inject_global_css()

user = require_login()

with st.sidebar:
    st.markdown("### 🌐 QMUN Hub")
    st.caption("Queen's Model UN")
    st.divider()
    st.markdown(f"**{user.name}**")
    st.caption(user.role.title())
    if st.button("Sign out", use_container_width=True):
        st.session_state.clear()
        st.rerun()

page_header(
    "Welcome to QMUN Hub",
    "Institutional knowledge, training, and AI tools for the Queen's MUN team.",
)

cols = st.columns(3, gap="large")
with cols[0]:
    with st.container(border=True):
        st.markdown("### 📚 Archive")
        st.caption("Search past papers, study guides, alumni interviews.")
        st.page_link("pages/1_Archive.py", label="Open Archive", icon="📚")
with cols[1]:
    with st.container(border=True):
        st.markdown("### 🌍 Brief")
        st.caption("Generate country briefs for mocks and conferences.")
        st.page_link("pages/2_Brief.py", label="Generate Brief", icon="🌍")
with cols[2]:
    with st.container(border=True):
        st.markdown("### 💬 Chatbot")
        st.caption("Mentor, Crisis Backroom, or Chair Assistant.")
        st.page_link("pages/3_Chatbot.py", label="Open Chatbot", icon="💬")

cols2 = st.columns(3, gap="large")
with cols2[0]:
    with st.container(border=True):
        st.markdown("### 🎓 Training")
        st.caption("Art of MUN, parli pro, how-to-win guides.")
        st.page_link("pages/4_Training.py", label="Open Training", icon="🎓")
with cols2[1]:
    if user.is_exec:
        with st.container(border=True):
            st.markdown("### 🎯 Director")
            st.caption("Assignments, weekly topics, curation, costs.")
            st.page_link("pages/5_Director.py", label="Director Tools", icon="🎯")
    else:
        with st.container(border=True):
            st.markdown("### 🎯 Director")
            st.caption("Exec-only tools.")
            st.markdown("_Restricted_")

brand_footer()
