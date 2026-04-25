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

with st.sidebar:
    st.markdown("### Mode")
    selected = st.radio(
        "Chatbot mode",
        mode_options,
        format_func=lambda m: mode_label[m],
        label_visibility="collapsed",
        key="chat_mode_select",
    )
    st.caption(MODE_DESCRIPTIONS[selected])

    if selected == ChatMode.CRISIS_BACKROOM and user.is_exec:
        st.divider()
        st.markdown("### Scenario")
        st.caption("Director-set context for this crisis session.")
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
            st.success("Scenario saved.")

    st.divider()
    snap = user_weekly(user.slack_id)
    st.markdown("**This week**")
    st.caption(f"Mentor / Chair turns: {snap.chat_turns} / 30")
    st.caption(f"Crisis interactions: {snap.crisis_interactions} / 5")
    st.caption(f"Spent: ${snap.estimated_cost_usd:.4f}")

    if st.button("Clear conversation", use_container_width=True):
        st.session_state.pop("chat_history_by_mode", None)
        st.rerun()

page_header("Chatbot", mode_label[selected], MODE_DESCRIPTIONS[selected])

# Per-mode history (keep separate so switching modes doesn't pollute context)
if "chat_history_by_mode" not in st.session_state:
    st.session_state["chat_history_by_mode"] = {}
history_key = selected.value
history = st.session_state["chat_history_by_mode"].setdefault(history_key, [])

for msg in history:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

prompt = st.chat_input("Type a message..." if selected != ChatMode.CRISIS_BACKROOM else "Send a crisis note...")
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
