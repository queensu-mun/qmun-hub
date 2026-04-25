import streamlit as st

from lib.auth import require_login
from lib.chat import ChatMode, MODE_DESCRIPTIONS
from lib.ui import inject_global_css, page_header, brand_footer

st.set_page_config(page_title="Chatbot · QMUN Hub", page_icon="💬", layout="wide")
inject_global_css()
user = require_login()

mode_label = {
    ChatMode.MENTOR: "🎓 Mentor",
    ChatMode.CRISIS_BACKROOM: "🌀 Crisis Backroom",
    ChatMode.CHAIR_ASSISTANT: "🧑‍⚖️ Chair Assistant",
}

with st.sidebar:
    st.markdown("### Mode")
    mode_options = [ChatMode.MENTOR, ChatMode.CRISIS_BACKROOM, ChatMode.CHAIR_ASSISTANT]
    if not user.is_exec:
        mode_options = [ChatMode.MENTOR]
    selected = st.radio(
        "Chatbot mode",
        mode_options,
        format_func=lambda m: mode_label[m],
        label_visibility="collapsed",
    )
    st.caption(MODE_DESCRIPTIONS[selected])
    st.divider()
    st.markdown("**This week**")
    st.caption("Mentor turns: 0 / 30")
    st.caption("Crisis interactions: 0 / 5")

page_header(mode_label[selected], MODE_DESCRIPTIONS[selected])

if "chat_history" not in st.session_state:
    st.session_state["chat_history"] = []

for msg in st.session_state["chat_history"]:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

prompt = st.chat_input("Ask anything... (chat backend lands Phase 3, July)")
if prompt:
    st.session_state["chat_history"].append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    with st.chat_message("assistant"):
        st.info("Chatbot backend lands in Phase 3 (July). Echoing your prompt for now.", icon="🚧")
        st.markdown(f"_You said:_ {prompt}")
    st.session_state["chat_history"].append(
        {"role": "assistant", "content": f"_(stub)_ You said: {prompt}"}
    )

brand_footer()
