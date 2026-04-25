from __future__ import annotations

import streamlit as st

from lib.auth import require_login
from lib.brief import BriefRequest, generate_streaming
from lib.budget import current_monthly
from lib.cache import recent
from lib.ui import brand_footer, inject_global_css, page_header, tag

st.set_page_config(page_title="Brief · QMUN Hub", page_icon="🌍", layout="wide")
inject_global_css()
user = require_login()

page_header("Brief", "A starting point on any country", "Built around the team's three-question framework. Mock or full conference depth.")

with st.container(border=True):
    cols = st.columns([1, 1, 1])
    with cols[0]:
        country = st.text_input("Country or character", placeholder="Brazil, Henry Kissinger...")
    with cols[1]:
        committee = st.text_input("Committee", placeholder="ECOSOC, UNSC, JCC: WW2 Allies...")
    with cols[2]:
        depth_label = st.radio(
            "Depth",
            ["Mock (one page)", "Conference (full)"],
            horizontal=False,
            help="Mock takes ~10s, conference takes ~60s and pulls more detail.",
        )
        depth = "mock" if depth_label.startswith("Mock") else "conference"

    topic = st.text_area(
        "Topic",
        placeholder="Sustainable financing for climate adaptation in SIDS",
        height=80,
    )
    notes = st.text_area(
        "Anything else worth knowing? (optional)",
        placeholder="Conference, scenario, your strategy, what you're stuck on.",
        height=68,
    )

    btn_cols = st.columns([1, 1, 4])
    with btn_cols[0]:
        generate_btn = st.button("Generate brief", type="primary", use_container_width=True)
    with btn_cols[1]:
        clear_btn = st.button("Clear", use_container_width=True)

if clear_btn:
    st.session_state.pop("last_brief", None)
    st.rerun()

if generate_btn:
    if not (country and committee and topic):
        st.error("Country, committee, and topic are all required.")
    else:
        req = BriefRequest(
            country=country.strip(),
            committee=committee.strip(),
            topic=topic.strip(),
            depth=depth,
            notes=notes.strip() if notes else None,
            user_slack_id=user.slack_id,
        )

        st.markdown("### Brief")
        placeholder = st.empty()
        accumulated = ""
        final_brief = None

        with st.spinner("Generating..." if depth == "mock" else "Generating full conference brief (~60s)..."):
            for delta, result in generate_streaming(req):
                if result is None:
                    accumulated += delta
                    placeholder.markdown(accumulated)
                else:
                    final_brief = result
                    placeholder.markdown(result.markdown)

        if final_brief:
            st.session_state["last_brief"] = {
                "markdown": final_brief.markdown,
                "cost": final_brief.cost_usd,
                "cache_hit": final_brief.cache_hit,
                "country": req.country,
                "committee": req.committee,
                "topic": req.topic,
                "depth": req.depth,
            }
            badge = "Cache hit · $0.00" if final_brief.cache_hit else f"Generated · ${final_brief.cost_usd:.4f}"
            st.markdown(f"<div class='subtle'>{badge}</div>", unsafe_allow_html=True)

elif "last_brief" in st.session_state:
    b = st.session_state["last_brief"]
    st.markdown("### Brief")
    st.markdown(b["markdown"])
    badge = "Cache hit · $0.00" if b["cache_hit"] else f"Generated · ${b['cost']:.4f}"
    st.markdown(f"<div class='subtle'>{badge}</div>", unsafe_allow_html=True)

st.divider()

# Sidebar-ish info on recent + monthly
left, right = st.columns([2, 1])
with left:
    st.markdown("### Recent briefs (this week's cache)")
    items = recent(limit=8)
    if not items:
        st.caption("No briefs generated yet.")
    else:
        for it in items:
            with st.container(border=True):
                cols = st.columns([3, 1])
                cols[0].markdown(f"**{it['country']}** · {it['committee']}")
                cols[0].caption(it["topic"])
                cols[1].markdown(tag(it["depth"]) + f" <span class='subtle'>${it['cost_usd']:.3f}</span>", unsafe_allow_html=True)

with right:
    st.markdown("### This month")
    monthly = current_monthly()
    st.metric("Spent", f"${monthly.spent_usd:.2f}")
    st.metric("Projected", f"${monthly.projected_usd:.2f}", delta=f"of ${monthly.cap_usd:.0f} cap")
    if monthly.should_warn:
        st.warning("Approaching monthly cap.")

brand_footer()
