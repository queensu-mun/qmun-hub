from __future__ import annotations

import streamlit as st

from lib.auth import require_login
from lib.budget import check_user_quota, user_weekly
from lib.chat import (
    MODE_DESCRIPTIONS,
    ChatMode,
    CrisisScenario,
    FEATURE_KEYS,
    stream_respond,
)
from lib.ui import brand_footer, inject_global_css, page_header, top_nav

st.set_page_config(page_title="Chatbot · Queen's MUN", page_icon="🌐", layout="wide", initial_sidebar_state="collapsed")
inject_global_css()
user = require_login()
top_nav(user)

mode_label = {
    ChatMode.MENTOR: "Mentor",
    ChatMode.CRISIS_BACKROOM: "Crisis Backroom",
    ChatMode.CHAIR_ASSISTANT: "Chair Assistant",
}
mode_options = [ChatMode.MENTOR]
if user.is_exec:
    mode_options = [ChatMode.MENTOR, ChatMode.CRISIS_BACKROOM, ChatMode.CHAIR_ASSISTANT]

# Track selected mode in session
if "chat_mode_select" not in st.session_state:
    st.session_state["chat_mode_select"] = ChatMode.MENTOR

# ----------------- Mode selector (compact horizontal radio) -----------------
selected = st.radio(
    "Mode",
    mode_options,
    format_func=lambda m: mode_label[m],
    horizontal=True,
    label_visibility="collapsed",
    key="chat_mode_select",
)

# Page title + lede for selected mode
st.markdown(f"<h1 style='margin-top:0.75rem;'>{mode_label[selected]}</h1>", unsafe_allow_html=True)
st.markdown(f"<div class='lede'>{MODE_DESCRIPTIONS[selected]}</div>", unsafe_allow_html=True)

# ----------------- Layout: chat (left), context rail (right) -----------------
chat_col, rail_col = st.columns([3, 1], gap="large")

with rail_col:
    snap = user_weekly(user.slack_id)
    st.markdown(
        f"<div class='subtle' style='text-transform:uppercase; letter-spacing:0.12em; font-size:0.7rem; "
        f"font-weight:600; margin-bottom:0.5rem;'>This week</div>",
        unsafe_allow_html=True,
    )
    st.markdown(
        f"<div class='subtle'>Mentor / Chair turns: <span style='color:var(--text); font-weight:600;'>{snap.chat_turns}</span> / 30</div>",
        unsafe_allow_html=True,
    )
    st.markdown(
        f"<div class='subtle'>Crisis interactions: <span style='color:var(--text); font-weight:600;'>{snap.crisis_interactions}</span> / 5</div>",
        unsafe_allow_html=True,
    )
    st.markdown(
        f"<div class='subtle'>Spent: <span style='color:var(--text); font-weight:600;'>${snap.estimated_cost_usd:.4f}</span></div>",
        unsafe_allow_html=True,
    )

    st.markdown("<div style='height:1.5rem;'></div>", unsafe_allow_html=True)

    if selected == ChatMode.CRISIS_BACKROOM and user.is_exec:
        with st.expander("Scenario context", expanded=not bool(st.session_state.get("crisis_committee"))):
            committee = st.text_input("Committee", value=st.session_state.get("crisis_committee", ""))
            time_period = st.text_input("Time period", value=st.session_state.get("crisis_period", ""))
            situation = st.text_area("Initial situation", height=80, value=st.session_state.get("crisis_situation", ""))
            characters = st.text_area("Active characters (comma-separated)", height=60, value=st.session_state.get("crisis_chars", ""))
            tone = st.text_area("Tone / director notes", height=60, value=st.session_state.get("crisis_tone", ""))
            if st.button("Save scenario", use_container_width=True):
                st.session_state["crisis_committee"] = committee
                st.session_state["crisis_period"] = time_period
                st.session_state["crisis_situation"] = situation
                st.session_state["crisis_chars"] = characters
                st.session_state["crisis_tone"] = tone
                st.success("Saved.")

    if st.button("Clear conversation", use_container_width=True):
        st.session_state.pop("chat_history_by_mode", None)
        st.rerun()

with chat_col:
    if "chat_history_by_mode" not in st.session_state:
        st.session_state["chat_history_by_mode"] = {}
    history_key = selected.value
    history = st.session_state["chat_history_by_mode"].setdefault(history_key, [])

    for msg in history:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    prompt = st.chat_input("Type a message..." if selected != ChatMode.CRISIS_BACKROOM else "Send a crisis note...")
    seeded_prompt = st.session_state.pop("mentor_seed_question", None)
    if seeded_prompt and not prompt:
        prompt = seeded_prompt
    if prompt:
        feature = FEATURE_KEYS[selected]
        ok, msg = check_user_quota(user.slack_id, feature)
        if not ok:
            st.error(msg)
            st.stop()

        history.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        scenario = None
        if selected == ChatMode.CRISIS_BACKROOM and st.session_state.get("crisis_committee"):
            chars_raw = st.session_state.get("crisis_chars", "")
            scenario = CrisisScenario(
                committee=st.session_state.get("crisis_committee", ""),
                time_period=st.session_state.get("crisis_period", ""),
                initial_situation=st.session_state.get("crisis_situation", ""),
                active_characters=[c.strip() for c in chars_raw.split(",") if c.strip()],
                tone_notes=st.session_state.get("crisis_tone") or None,
            )

        with st.chat_message("assistant"):
            placeholder = st.empty()
            accumulated = ""
            cost = 0.0
            for delta, c in stream_respond(
                selected,
                history,
                user_slack_id=user.slack_id,
                scenario=scenario,
                delegate_name=user.name,
            ):
                if c is None:
                    accumulated += delta
                    placeholder.markdown(accumulated)
                else:
                    cost = c

            history.append({"role": "assistant", "content": accumulated})
            if cost > 0:
                st.caption(f"_${cost:.5f}_")

brand_footer()
