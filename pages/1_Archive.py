from __future__ import annotations

from pathlib import Path

import streamlit as st

from lib.auth import require_login
from lib.index import doc_text, index_stats, list_docs
from lib.search import hybrid_search
from lib.ui import brand_footer, inject_global_css, page_header, top_nav

st.set_page_config(page_title="Archive · Queen's MUN", page_icon="🌐", layout="wide", initial_sidebar_state="collapsed")
inject_global_css()
user = require_login()
top_nav(user)

DOC_TYPE_LABELS = {
    "All types": None,
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


def _meta_line(doc_type: str, year: int | None, quality: str | None, extra: str = "") -> str:
    parts = [DOC_TYPE_DISPLAY.get(doc_type, doc_type)]
    if year:
        parts.append(str(year))
    if quality == "exemplary":
        parts.append("⭐ exemplary")
    elif quality == "outdated":
        parts.append("outdated")
    if extra:
        parts.append(extra)
    return " · ".join(parts)


# ---------------- Doc viewer (takes over the page when a doc is open) ----------------
if "archive_open_doc" in st.session_state:
    doc_id = st.session_state["archive_open_doc"]
    doc_meta = next((d for d in list_docs() if d["doc_id"] == doc_id), None)

    if st.button("← Back to archive", key="archive_doc_back"):
        if "archive_return_query" in st.session_state:
            st.session_state["archive_seed_query"] = st.session_state.pop("archive_return_query")
        st.session_state.pop("archive_open_doc", None)
        st.rerun()

    st.markdown("<div style='height:1rem;'></div>", unsafe_allow_html=True)

    # Centered reading column so long-form text doesn't span the full page width.
    _, mid, _ = st.columns([1, 5, 1])
    with mid:
        if doc_meta:
            st.markdown(f"### {doc_meta['title']}")
            st.caption(_meta_line(doc_meta["doc_type"], doc_meta["year"], doc_meta["quality_flag"]))
            st.markdown("<div style='height:0.75rem;'></div>", unsafe_allow_html=True)

        source = (doc_meta or {}).get("source", "") or ""
        is_pdf = source.lower().endswith(".pdf")
        pdf_path = Path(source) if is_pdf else None

        if is_pdf and pdf_path and pdf_path.exists():
            # PDFs render poorly as extracted text. Offer the original instead.
            st.info(
                "This is a PDF. The extracted text is searchable via the Archive search, "
                "but for reading, download the original below."
            )
            with open(pdf_path, "rb") as f:
                st.download_button(
                    "⬇ Download original PDF",
                    data=f.read(),
                    file_name=pdf_path.name,
                    mime="application/pdf",
                    type="primary",
                )
            with st.expander("Show indexed text anyway"):
                text = doc_text(doc_id)
                if text:
                    st.markdown(text[:80_000])
                    if len(text) > 80_000:
                        st.caption(f"_(truncated; full extracted text is {len(text):,} chars)_")
                else:
                    st.caption("No indexed text available.")
        else:
            # Markdown / text doc — render inline in the reading column.
            text = doc_text(doc_id)
            if text:
                st.markdown(text[:80_000])
                if len(text) > 80_000:
                    st.caption(f"_(truncated; full doc is {len(text):,} chars)_")
            else:
                st.warning("No text available for this document.")

    brand_footer()
    st.stop()


# ---------------- Search bar (single line) ----------------
seeded_query = st.session_state.pop("archive_seed_query", "")
all_years = sorted({d["year"] for d in list_docs() if d["year"]}, reverse=True)

search_cols = st.columns([6, 1.5, 1.2, 1])
with search_cols[0]:
    query = st.text_input(
        "Search",
        value=seeded_query,
        placeholder="Search the archive...",
        label_visibility="collapsed",
    )
with search_cols[1]:
    doc_type_label = st.selectbox("Type", list(DOC_TYPE_LABELS.keys()), label_visibility="collapsed")
with search_cols[2]:
    year_choice = st.selectbox("Year", ["All years"] + all_years, label_visibility="collapsed")
with search_cols[3]:
    submitted = st.button("Search", type="primary", use_container_width=True)
if seeded_query:
    submitted = True

st.markdown("<div style='height:1.5rem;'></div>", unsafe_allow_html=True)

# ---------------- Results or default doc list ----------------
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
        st.caption(f"{len(hits)} result{'s' if len(hits) != 1 else ''}")
        for h in hits:
            st.markdown(f"#### {h.doc_title}")
            st.caption(_meta_line(h.doc_type, h.year, h.quality_flag))
            st.markdown(f"> {h.snippet}")
            row = st.columns([1, 1, 6])
            with row[0]:
                if st.button("Open", key=f"open_{h.chunk_id}"):
                    st.session_state["archive_open_doc"] = h.doc_id
                    st.session_state["archive_return_query"] = query
                    st.rerun()
            with row[1]:
                if st.button("Ask mentor", key=f"ask_{h.chunk_id}"):
                    st.session_state["mentor_seed_question"] = (
                        f"Help me understand the relevant parts of '{h.doc_title}' "
                        f"for someone preparing on this topic: {query}"
                    )
                    st.switch_page("pages/3_Chatbot.py")
            st.markdown("<hr style='margin: 1.25rem 0;'/>", unsafe_allow_html=True)

elif submitted and not query:
    st.error("Enter a search query.")
else:
    # Default: simple list of indexed docs
    st.markdown(
        "<div class='subtle' style='text-transform:uppercase; letter-spacing:0.12em; font-size:0.7rem; "
        "font-weight:600; margin-bottom:0.75rem;'>All documents</div>",
        unsafe_allow_html=True,
    )
    docs = list_docs()
    visible = [d for d in docs if user.is_exec or d["visibility"] == "team"]
    for d in visible:
        title_col, meta_col, btn_col = st.columns([4, 3, 1])
        with title_col:
            st.markdown(f"**{d['title']}**")
        with meta_col:
            st.caption(_meta_line(d["doc_type"], d["year"], d["quality_flag"], f"{d['chunk_count']} chunks"))
        with btn_col:
            if st.button("Open", key=f"recent_open_{d['doc_id']}", use_container_width=True):
                st.session_state["archive_open_doc"] = d["doc_id"]
                st.rerun()
        st.markdown("<hr style='margin: 0.75rem 0;'/>", unsafe_allow_html=True)

brand_footer()
