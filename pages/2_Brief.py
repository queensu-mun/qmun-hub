import streamlit as st

from lib.auth import require_login
from lib.ui import inject_global_css, page_header, brand_footer

st.set_page_config(page_title="Brief · QMUN Hub", page_icon="🌍", layout="wide")
inject_global_css()
user = require_login()

page_header(
    "🌍 Country Brief Generator",
    "Backbone is the team's 3-question framework: country position → international context → committee strategy.",
)

with st.container(border=True):
    st.markdown("**Generate a brief**")
    cols = st.columns([1, 1, 1])
    with cols[0]:
        country = st.text_input("Country / Character", placeholder="e.g. Brazil, Henry Kissinger")
    with cols[1]:
        committee = st.text_input("Committee", placeholder="e.g. ECOSOC, UNSC, JCC: WW2 Allies")
    with cols[2]:
        depth = st.radio("Depth", ["Mock (1-pg, ~$0.01)", "Conference (full, ~$0.05)"], horizontal=False)
    topic = st.text_area("Topic", placeholder="e.g. Sustainable financing for climate adaptation in SIDS", height=80)
    notes = st.text_area("Optional notes / framing", placeholder="Anything specific about the conference, scenario, or your delegate strategy.", height=68)

    btn_cols = st.columns([1, 1, 4])
    with btn_cols[0]:
        st.button("Generate brief", type="primary", use_container_width=True, disabled=True, help="Brief generator lands in Phase 2 (June)")
    with btn_cols[1]:
        st.button("Bulk generate", use_container_width=True, disabled=True, help="Director-only bulk mode")

st.markdown("<br/>", unsafe_allow_html=True)
st.markdown("### Recent briefs")
st.markdown(
    "<div class='qmun-muted'>Brief generator (Phase 2 · June). "
    f"Once live, your last 10 generated briefs surface here.</div>",
    unsafe_allow_html=True,
)

brand_footer()
