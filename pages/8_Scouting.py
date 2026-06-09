from __future__ import annotations

import streamlit as st

from lib import state as state_lib
from lib.auth import require_login
from lib.ui import brand_footer, inject_global_css, page_header, tag, top_nav

st.set_page_config(page_title="Scouting · Queen's MUN", page_icon="🌐", layout="wide", initial_sidebar_state="collapsed")
inject_global_css()
user = require_login()
top_nav(user)

page_header(
    "Scouting",
    "Other delegations on the circuit",
    "Built from alumni intel and director observations. Know who you're sitting across from.",
)

# Published only: drafts wait in the Director -> Scouting queue.
delegations = state_lib.list_delegations(status="published")

if not delegations:
    st.markdown(
        """
<div style='padding:3rem 0 2rem; text-align:center;'>
  <div style='font-size:1.1rem; font-weight:600; color:var(--text); margin-bottom:0.5rem;'>No scouting reports yet</div>
  <div style='color:var(--text-muted); font-size:0.9rem; max-width:420px; margin:0 auto; line-height:1.6;'>
    This page builds from alumni intel and director observations. Reports on rival delegations
    will appear here as the team documents conferences.
  </div>
</div>
""",
        unsafe_allow_html=True,
    )
else:
    # Strength filter
    strength_filter = st.selectbox(
        "Filter by strength",
        ["all", "rising", "competitive", "strong", "dominant", "unknown"],
        key="public_scouting_filter",
    )
    rows = delegations if strength_filter == "all" else [d for d in delegations if d.get("strength_level") == strength_filter]

    if not rows:
        st.caption("No delegations match this filter.")
    for d in rows:
        with st.container(border=True):
            head_cols = st.columns([3, 1])
            head_cols[0].markdown(f"**{d['school']}**")
            badges = tag(d.get("strength_level", "unknown"))
            head_cols[0].markdown(badges, unsafe_allow_html=True)
            if d.get("conferences_seen_at"):
                head_cols[0].caption("Seen at: " + ", ".join(d["conferences_seen_at"]))
            if d.get("last_updated_at"):
                head_cols[1].markdown(
                    f"<div class='subtle' style='text-align:right;'>updated {d['last_updated_at'][:10]}</div>",
                    unsafe_allow_html=True,
                )

            if d.get("tactical_notes"):
                st.markdown(d["tactical_notes"])
            if d.get("awards_tendency"):
                st.caption(f"Awards: {d['awards_tendency']}")
            if d.get("notable_delegates"):
                st.caption("Notable: " + ", ".join(d["notable_delegates"]))

brand_footer()
