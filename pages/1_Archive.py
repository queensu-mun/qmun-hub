import streamlit as st

from lib.auth import require_login
from lib.index import doc_text, index_stats, list_docs
from lib.search import hybrid_search
from lib.ui import brand_footer, inject_global_css, page_header, pill

st.set_page_config(page_title="Archive · QMUN Hub", page_icon="📚", layout="wide")
inject_global_css()
user = require_login()

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

page_header("📚 Archive", "Search past papers, study guides, alumni interviews, and director notes.")

stats = index_stats()
if stats["n_docs"] == 0:
    st.warning("Archive is empty. Run `python3 scripts/seed_archive.py` to bootstrap with seed docs.")
    brand_footer()
    st.stop()

with st.container(border=True):
    cols = st.columns([3, 1, 1, 1])
    with cols[0]:
        query = st.text_input(
            "Search",
            placeholder="e.g. crisis directives, China climate policy, prisoners rights, Khmer Rouge...",
            label_visibility="collapsed",
        )
    with cols[1]:
        doc_type_label = st.selectbox(
            "Type", list(DOC_TYPE_LABELS.keys()), label_visibility="collapsed",
        )
    with cols[2]:
        years = sorted({d["year"] for d in list_docs() if d["year"]}, reverse=True)
        year_choice = st.selectbox("Year", ["All years"] + years, label_visibility="collapsed")
    with cols[3]:
        submitted = st.button("Search", type="primary", use_container_width=True)

st.markdown("<br/>", unsafe_allow_html=True)

if submitted and query:
    doc_type = DOC_TYPE_LABELS.get(doc_type_label)
    year = year_choice if isinstance(year_choice, int) else None

    with st.spinner("Searching..."):
        hits = hybrid_search(
            query,
            top_k=15,
            doc_types=[doc_type] if doc_type else None,
            year=year,
            exec_visible=user.is_exec,
        )

    if not hits:
        st.info("No results. Try a different query or remove filters.")
    else:
        st.markdown(f"<div class='qmun-muted'>{len(hits)} result(s)</div>", unsafe_allow_html=True)
        for h in hits:
            with st.container(border=True):
                title_cols = st.columns([5, 1])
                with title_cols[0]:
                    badges = pill(DOC_TYPE_DISPLAY.get(h.doc_type, h.doc_type))
                    if h.year:
                        badges += " " + pill(str(h.year))
                    if h.quality_flag == "exemplary":
                        badges += " " + pill("⭐ exemplary")
                    elif h.quality_flag == "outdated":
                        badges += " " + pill("outdated")
                    st.markdown(f"**{h.doc_title}** &nbsp;{badges}", unsafe_allow_html=True)
                with title_cols[1]:
                    st.markdown(
                        f"<div style='text-align:right' class='qmun-muted'>"
                        f"score {h.score:.2f}<br/>"
                        f"<span style='font-size:0.7rem;'>vec {h.vector_score:.2f} | bm25 {h.bm25_score:.2f}</span>"
                        f"</div>",
                        unsafe_allow_html=True,
                    )
                st.markdown(f"> {h.snippet}")
                btn_cols = st.columns([1, 1, 5])
                with btn_cols[0]:
                    if st.button("Open document", key=f"open_{h.chunk_id}"):
                        st.session_state["archive_open_doc"] = h.doc_id
                with btn_cols[1]:
                    if st.button("Ask mentor", key=f"ask_{h.chunk_id}"):
                        st.session_state["mentor_seed_question"] = (
                            f"Help me understand the relevant parts of '{h.doc_title}' for "
                            f"someone preparing on this topic: {query}"
                        )
                        st.switch_page("pages/3_Chatbot.py")
elif submitted and not query:
    st.error("Enter a search query.")
else:
    # Default view: show recent indexed docs
    st.markdown("### Indexed documents")
    docs = list_docs()
    visible = [d for d in docs if user.is_exec or d["visibility"] == "team"]
    cols_per_row = 2
    rows = [visible[i : i + cols_per_row] for i in range(0, len(visible), cols_per_row)]
    for row in rows:
        cols = st.columns(cols_per_row)
        for col, d in zip(cols, row):
            with col:
                with st.container(border=True):
                    badges = pill(DOC_TYPE_DISPLAY.get(d["doc_type"], d["doc_type"]))
                    if d["year"]:
                        badges += " " + pill(str(d["year"]))
                    if d["quality_flag"] == "exemplary":
                        badges += " " + pill("⭐ exemplary")
                    st.markdown(f"**{d['title']}**", unsafe_allow_html=True)
                    st.markdown(badges, unsafe_allow_html=True)
                    st.caption(f"{d['chunk_count']} chunks · indexed {d['indexed_at'][:10]}")
                    if st.button("Open", key=f"recent_open_{d['doc_id']}"):
                        st.session_state["archive_open_doc"] = d["doc_id"]

# Doc viewer modal-ish (below results)
if "archive_open_doc" in st.session_state:
    st.divider()
    doc_id = st.session_state["archive_open_doc"]
    text = doc_text(doc_id)
    if text:
        st.markdown("### Document")
        with st.container(border=True):
            st.markdown(text[:50_000])  # cap to keep page snappy
            if len(text) > 50_000:
                st.caption(f"_(truncated; full doc is {len(text):,} chars)_")
        if st.button("Close"):
            st.session_state.pop("archive_open_doc", None)
            st.rerun()

st.divider()
st.markdown("### Index status")
cols = st.columns(4)
cols[0].metric("Documents", stats["n_docs"])
cols[1].metric("Chunks", stats["n_chunks"])
cols[2].metric("Doc types", len(stats["by_type"]))
with cols[3]:
    st.caption("By type:")
    for t, n in sorted(stats["by_type"].items(), key=lambda x: -x[1]):
        st.caption(f"  {DOC_TYPE_DISPLAY.get(t, t)}: {n}")

brand_footer()
