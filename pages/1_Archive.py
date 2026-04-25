import streamlit as st

from lib.auth import require_login
from lib.ui import inject_global_css, page_header, pill, brand_footer

st.set_page_config(page_title="Archive · QMUN Hub", page_icon="📚", layout="wide")
inject_global_css()
user = require_login()

page_header("📚 Archive", "Search past papers, study guides, alumni interviews, and director notes.")

with st.container(border=True):
    cols = st.columns([3, 1, 1, 1])
    with cols[0]:
        query = st.text_input("Search", placeholder="e.g. China climate financing, NCSC UNSC fall 2025...", label_visibility="collapsed")
    with cols[1]:
        doc_type = st.selectbox("Type", ["All", "Position paper", "Study guide", "Alumni interview", "Director note", "Background guide"], label_visibility="collapsed")
    with cols[2]:
        year = st.selectbox("Year", ["All years", 2026, 2025, 2024, 2023, 2022], label_visibility="collapsed")
    with cols[3]:
        submitted = st.button("Search", type="primary", use_container_width=True)

st.markdown("<br/>", unsafe_allow_html=True)

if not query:
    st.markdown("### Recent additions")
    st.markdown(
        "<div class='qmun-muted'>Indexing pipeline lands in Phase 1.3 (May). "
        "Once Drive is connected, recently-modified docs surface here.</div>",
        unsafe_allow_html=True,
    )
else:
    st.info("Search backend lands in Phase 1.3 — indexing pipeline + hybrid search.", icon="🚧")
    with st.container(border=True):
        st.markdown("**Example result card** " + pill("Position paper") + " " + pill("2025"), unsafe_allow_html=True)
        st.caption("NCSC · UNSC · China · Cambodia situation")
        st.markdown("> ...the People's Republic of China affirms its commitment to non-interference while...")
        st.button("Open document", key="example_open")

brand_footer()
