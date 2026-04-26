from __future__ import annotations

import streamlit as st

from lib.auth import require_login
from lib.index import doc_text, index_stats, list_docs
from lib.search import hybrid_search
from lib.ui import brand_footer, inject_global_css, page_header, tag, top_nav

st.set_page_config(page_title="Archive · Queen's MUN", page_icon="🌐", layout="wide", initial_sidebar_state="collapsed")
inject_global_css()
user = require_login()
top_nav(user)

DOC_TYPE_LABELS = {
    "All": None,
    "Position paper": "position_paper",
    "Study guide": "study_guide",
    "Alumni interview": "alumni_interview",
    "Director note": "director_note",
    "Background guide": "background_guide",
    "Training": "training",
    "Misc": "misc",
}
DOC_TYPE_DISPLAY = {v: k for k, v in DOC_TYPE_LABELS.items() if v}

page_header("Archive", "Search the team's knowledge", "Past papers, study guides, alumni interviews, training docs.")

stats = index_stats()
if stats["n_docs"] == 0:
    st.warning("Archive is empty. Run `python3 scripts/seed_archive.py` to bootstrap.")
    brand_footer()
    st.stop()

# Compact filter row, no card wrapper
seeded_query = st.session_state.pop("archive_seed_query", "")
cols = st.columns([4, 1.2, 1.2, 1])
with cols[0]:
    query = st.text_input(
        "Search",
        value=seeded_query,
        placeholder="Try: crisis directives, China climate, Khmer Rouge, parli pro motions...",
        label_visibility="collapsed",
    )
with cols[1]:
    doc_type_label = st.selectbox("Type", list(DOC_TYPE_LABELS.keys()), label_visibility="collapsed")
with cols[2]:
    years = sorted({d["year"] for d in list_docs() if d["year"]}, reverse=True)
    year_choice = st.selectbox("Year", ["All years"] + years, label_visibility="collapsed")
with cols[3]:
    submitted = st.button("Search", type="primary", use_container_width=True)
if seeded_query:
    submitted = True

st.markdown("<div style='height:1.25rem;'></div>", unsafe_allow_html=True)

if submitted and query:
    doc_type = DOC_TYPE_LABELS.get(doc_type_label)
    year = year_choice if isinstance(year_choice, int) else None
    with st.spinner("Searching..."):
        hits = hybrid_search(
            query, top_k=15,
            doc_types=[doc_type] if doc_type else None,
            year=year,
            exec_visible=user.is_exec,
        )
    if not hits:
        st.info("No results. Try a different query or remove filters.")
    else:
        st.markdown(
            f"<div class='subtle' style='margin-bottom:0.75rem;'>{len(hits)} result(s)</div>",
            unsafe_allow_html=True,
        )
        for h in hits:
            badges = tag(DOC_TYPE_DISPLAY.get(h.doc_type, h.doc_type))
            if h.year:
                badges += " " + tag(str(h.year))
            if h.quality_flag == "exemplary":
                badges += " " + tag("Exemplary", accent=True)
            elif h.quality_flag == "outdated":
                badges += " " + tag("outdated")

            st.markdown(
                f"""
<div class='result-row'>
  <div class='result-title'>{h.doc_title}</div>
  <div class='result-meta'>{badges}</div>
  <div class='result-snippet'>{h.snippet}</div>
</div>
""",
                unsafe_allow_html=True,
            )
            btn_cols = st.columns([1, 1, 6])
            with btn_cols[0]:
                if st.button("Open", key=f"open_{h.chunk_id}"):
                    st.session_state["archive_open_doc"] = h.doc_id
            with btn_cols[1]:
                if st.button("Ask mentor", key=f"ask_{h.chunk_id}"):
                    st.session_state["mentor_seed_question"] = (
                        f"Help me understand the relevant parts of '{h.doc_title}' "
                        f"for someone preparing on this topic: {query}"
                    )
                    st.switch_page("pages/3_Chatbot.py")
            st.markdown("<div style='height:0.75rem;'></div>", unsafe_allow_html=True)

elif submitted and not query:
    st.error("Enter a search query.")
else:
    # Default view: indexed documents as a clean list, not a grid of cards
    st.markdown("<h2 style='font-size:1.1rem; margin-top:1rem;'>Indexed documents</h2>", unsafe_allow_html=True)
    docs = list_docs()
    visible = [d for d in docs if user.is_exec or d["visibility"] == "team"]
    for d in visible:
        badges = tag(DOC_TYPE_DISPLAY.get(d["doc_type"], d["doc_type"]))
        if d["year"]:
            badges += " " + tag(str(d["year"]))
        if d["quality_flag"] == "exemplary":
            badges += " " + tag("Exemplary", accent=True)
        st.markdown(
            f"""
<div class='doc-row'>
  <div>
    <div class='doc-row-title'>{d['title']}</div>
    <div class='doc-row-meta'>{badges} <span class='subtle'>· {d['chunk_count']} chunks · indexed {d['indexed_at'][:10]}</span></div>
  </div>
</div>
""",
            unsafe_allow_html=True,
        )
        if st.button("Open", key=f"recent_open_{d['doc_id']}"):
            st.session_state["archive_open_doc"] = d["doc_id"]

# Doc viewer below
if "archive_open_doc" in st.session_state:
    st.divider()
    doc_id = st.session_state["archive_open_doc"]
    text = doc_text(doc_id)
    if text:
        st.markdown("<h2>Document</h2>", unsafe_allow_html=True)
        st.markdown(text[:50_000])
        if len(text) > 50_000:
            st.caption(f"_(truncated; full doc is {len(text):,} chars)_")
        if st.button("Close document"):
            st.session_state.pop("archive_open_doc", None)
            st.rerun()

brand_footer()
