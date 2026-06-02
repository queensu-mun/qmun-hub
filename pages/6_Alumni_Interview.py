"""Public-ish alumni interview form. No login required (just name + grad year)."""
from __future__ import annotations

import re
import uuid
from datetime import datetime

import streamlit as st

from lib.index import Doc, upsert_doc
from lib.interview import INTERVIEW_SECTIONS, core_sections, deep_sections
from lib.search import clear_cache as clear_search_cache
from lib.auth import current_user
from lib.ui import brand_footer, inject_global_css, page_header, top_nav

st.set_page_config(page_title="Contribute · Queen's MUN", page_icon="🌐", layout="wide", initial_sidebar_state="collapsed")
inject_global_css()
_u = current_user()
if _u:
    top_nav(_u)

page_header(
    "Contribute",
    "Tell us what you know",
    "What you learned at Queen's MUN walks out the door when you graduate. This is how it stays.",
)

with st.container(border=True):
    cols = st.columns([3, 1])
    with cols[0]:
        name = st.text_input("Your name", placeholder="As you'd like it credited (or leave blank for anonymous)")
    with cols[1]:
        grad_year = st.number_input("Graduation year", min_value=2010, max_value=2035, value=2026, step=1)

st.caption(
    "Answer as much or as little as you like. Everything past your name is optional, "
    "and even one answer is worth leaving behind. Bullet points are fine. War stories "
    "are better. Your answers aren't posted publicly. They quietly coach current "
    "delegates through the mentor chatbot and prep tools, so be candid."
)

# Initialize response state
if "interview_responses" not in st.session_state:
    st.session_state["interview_responses"] = {}
responses = st.session_state["interview_responses"]


def _render_question(section: dict, q: str) -> None:
    key = f"{section['id']}::{q[:60]}"
    responses[key] = st.text_area(
        q,
        value=responses.get(key, ""),
        height=110,
        key=f"input_{key}",
        label_visibility="visible",
    )


# Core: short, low-barrier, shown up front.
for section in core_sections():
    st.markdown(f"#### {section['title']}")
    for q in section["questions"]:
        _render_question(section, q)

# Deep: longer, experience-specific, opt-in.
st.markdown("<div style='height:0.5rem;'></div>", unsafe_allow_html=True)
with st.expander("Go deeper (optional)", expanded=False):
    st.caption(
        "For the alumni who want to give more. Tactical lessons, GA and crisis "
        "specifics, conference-by-conference intel. Skip anything that doesn't apply."
    )
    for section in deep_sections():
        st.markdown(f"**{section['title']}**")
        for q in section["questions"]:
            _render_question(section, q)

st.divider()

submit_cols = st.columns([1, 1, 4])
with submit_cols[0]:
    submit = st.button("Submit interview", type="primary", use_container_width=True)
with submit_cols[1]:
    if st.button("Clear all", use_container_width=True):
        st.session_state["interview_responses"] = {}
        st.rerun()


def _slugify(s: str) -> str:
    s = re.sub(r"[^A-Za-z0-9]+", "_", s.strip().lower())
    return s[:50] or "anonymous"


if submit:
    answered = {k: v.strip() for k, v in responses.items() if v.strip()}
    if not answered:
        st.error("You haven't answered any questions yet.")
    elif not name.strip():
        st.error("Please add your name (or 'Anonymous') before submitting.")
    else:
        # Compose markdown doc
        lines = [
            f"# Alumni Interview · {name.strip()}",
            f"_Class of {grad_year} · submitted {datetime.utcnow().date().isoformat()}_",
            "",
        ]
        for section in INTERVIEW_SECTIONS:
            section_answered = [
                (q, responses[f"{section['id']}::{q[:60]}"].strip())
                for q in section["questions"]
                if responses.get(f"{section['id']}::{q[:60]}", "").strip()
            ]
            if not section_answered:
                continue
            lines.append(f"## {section['title']}")
            lines.append("")
            for q, a in section_answered:
                lines.append(f"### {q}")
                lines.append("")
                lines.append(a)
                lines.append("")
        markdown = "\n".join(lines)

        doc_id = f"alumni_{_slugify(name)}_{grad_year}_{uuid.uuid4().hex[:6]}"
        doc = Doc(
            doc_id=doc_id,
            title=f"Alumni Interview · {name.strip()} (Class of {grad_year})",
            source=f"alumni_interview/{doc_id}",
            doc_type="alumni_interview",
            text=markdown,
            year=int(grad_year),
            metadata={"interviewee": name.strip(), "grad_year": int(grad_year)},
            visibility="team",
        )
        with st.spinner("Saving and indexing your interview..."):
            n = upsert_doc(doc)
        clear_search_cache()
        st.success(
            "Submitted. Thank you, this will quietly help coach future Queen's delegates "
            "through the mentor and prep tools."
        )
        st.session_state["interview_responses"] = {}

brand_footer()
