from __future__ import annotations

import streamlit as st

from lib import state as state_lib
from lib.auth import require_login
from lib.ui import brand_footer, inject_global_css, page_header, tag, top_nav

st.set_page_config(page_title="My Feedback · Queen's MUN", page_icon="🌐", layout="wide", initial_sidebar_state="collapsed")
inject_global_css()
user = require_login()
top_nav(user)

page_header(
    "My Feedback",
    "What your directors shared with you",
    "Feedback from mocks, conferences, and training that a director chose to share. Use it to target your next session.",
)

# Only entries about THIS user that a director explicitly shared. Everyone,
# execs included, sees just their own here; the full feedback bank stays in
# Director -> Delegates.
entries = state_lib.shared_feedback_for_delegate(user.name)

SOURCE_ORDER = ["conference", "mock", "training", "other"]
SOURCE_TITLES = {
    "conference": "Conference",
    "mock": "Mocks",
    "training": "Training",
    "other": "Other",
}

if not entries:
    st.markdown(
        """
<div style='padding:3rem 0 2rem; text-align:center;'>
  <div style='font-size:1.1rem; font-weight:600; color:var(--text); margin-bottom:0.5rem;'>No shared feedback yet</div>
  <div style='color:var(--text-muted); font-size:0.9rem; max-width:440px; margin:0 auto; line-height:1.6;'>
    When a director shares feedback from a mock, conference, or training session with you,
    it shows up here. Nothing yet just means nothing has been shared, not that nothing was noticed.
  </div>
</div>
""",
        unsafe_allow_html=True,
    )
else:
    conf_names = {c["id"]: c["name"] for c in state_lib.load().get("conferences", [])}

    by_source: dict[str, list[dict]] = {}
    for f in entries:
        by_source.setdefault(f.get("source") or "other", []).append(f)

    sources = SOURCE_ORDER + sorted(s for s in by_source if s not in SOURCE_ORDER)
    for source in sources:
        rows = by_source.get(source)
        if not rows:
            continue
        rows.sort(key=lambda f: f.get("created_at") or "", reverse=True)
        st.markdown(f"### {SOURCE_TITLES.get(source, source.title())}")
        for f in rows:
            with st.container(border=True):
                badges = tag(f.get("source", "other"))
                if f.get("conference_id") and f["conference_id"] in conf_names:
                    badges += " " + tag(conf_names[f["conference_id"]])
                st.markdown(badges, unsafe_allow_html=True)
                st.markdown(f.get("notes", ""))
                if f.get("tags"):
                    st.markdown(" ".join(tag(t) for t in f["tags"]), unsafe_allow_html=True)
                when = (f.get("created_at") or "")[:10]
                by = f.get("created_by") or "a director"
                st.caption(f"From {by}" + (f" on {when}" if when else ""))

brand_footer()
