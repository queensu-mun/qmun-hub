import streamlit as st

from lib.auth import require_exec
from lib.ui import inject_global_css, page_header, pill, brand_footer

st.set_page_config(page_title="Director · QMUN Hub", page_icon="🎯", layout="wide")
inject_global_css()
user = require_exec()

page_header("🎯 Director", "Assignments, weekly topics, archive curation, cost dashboard.")

tabs = st.tabs([
    "Weekly Topics",
    "Conferences & Assignments",
    "Alumni Interviews",
    "Curation",
    "Cost Dashboard",
    "Roster",
])

with tabs[0]:
    st.markdown("### This week's mocks")
    cols = st.columns(2)
    with cols[0]:
        with st.container(border=True):
            st.markdown("**Monday — light mock** " + pill("not set"), unsafe_allow_html=True)
            st.text_input("Topic", key="mon_topic", placeholder="e.g. SDG 4 Quality Education")
            st.text_input("Committee", key="mon_committee", placeholder="e.g. SOCHUM")
    with cols[1]:
        with st.container(border=True):
            st.markdown("**Thursday — competitive** " + pill("not set"), unsafe_allow_html=True)
            st.text_input("Topic", key="thu_topic", placeholder="e.g. Cyber sovereignty")
            st.text_input("Committee", key="thu_committee", placeholder="e.g. DISEC")
    st.button("Pre-generate briefs for assigned delegates", type="primary", disabled=True, help="Brief generator lands Phase 2")

with tabs[1]:
    st.markdown("### Upcoming conferences")
    st.info("Conference calendar + assignments grid lands in Phase 3.", icon="🚧")

with tabs[2]:
    st.markdown("### Alumni interview campaign")
    st.markdown(
        "Send the MUN Claude template to alumni and graduating seniors. "
        "Responses auto-index into the archive."
    )
    st.button("Send invite link", type="primary", disabled=True, help="Phase 3")
    st.divider()
    st.markdown("**Outreach status**")
    st.caption("0 invited · 0 responded · 0 indexed")

with tabs[3]:
    st.markdown("### Archive curation")
    st.markdown("Mark docs as exemplary (boost retrieval), outdated (deprioritize), or exec-only (hide from delegates).")
    st.info("Curation lands in Phase 3.", icon="🚧")

with tabs[4]:
    st.markdown("### This month")
    cols = st.columns(4)
    cols[0].metric("Spent", "$0.00", help="Real-time API spend")
    cols[1].metric("Projected", "$0.00", help="Pace-based monthly projection")
    cols[2].metric("Cap", "$40.00")
    cols[3].metric("Active users", "0", help="Distinct users this month")
    st.info("Cost telemetry lands in Phase 2 (June).", icon="🚧")

with tabs[5]:
    st.markdown("### Team roster")
    st.caption("Pulled from Slack workspace; role overrides set here.")
    st.info("Roster sync lands in Phase 1.4.", icon="🚧")

brand_footer()
