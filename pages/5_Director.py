from __future__ import annotations

import sqlite3
import uuid
from datetime import date, datetime

import pandas as pd
import streamlit as st

from lib import state as state_lib
from lib.auth import require_exec
from lib.budget import current_monthly, top_users
from lib.index import DB_PATH as INDEX_DB, list_docs
from lib.search import clear_cache as clear_search_cache
from lib.ui import brand_footer, inject_global_css, page_header, tag, top_nav

st.set_page_config(page_title="Director · Queen's MUN", page_icon="🌐", layout="wide", initial_sidebar_state="collapsed")
inject_global_css()
user = require_exec()
top_nav(user)

page_header("Director", "Run the team", "Weekly topics, conferences, assignments, archive curation, costs.")

tabs = st.tabs([
    "Weekly Topics",
    "Conferences",
    "Assignments",
    "Curation",
    "Cost Dashboard",
    "Alumni Outreach",
])

state = state_lib.load()

# ----------------- TAB 1: Weekly Topics -----------------
with tabs[0]:
    st.markdown("### This week's mocks")
    st.caption("Set the topic + committee for each weekly mock; the brief generator uses these.")
    cols = st.columns(2)
    for i, day in enumerate(["monday", "thursday"]):
        with cols[i]:
            with st.container(border=True):
                existing = state["weekly_topics"].get(day) or {}
                title = "Monday, light mock" if day == "monday" else "Thursday, competitive"
                badge = tag("set" if existing else "not set")
                st.markdown(f"**{title}** &nbsp;{badge}", unsafe_allow_html=True)
                topic = st.text_input("Topic", value=existing.get("topic", ""), key=f"{day}_topic")
                committee = st.text_input("Committee", value=existing.get("committee", ""), key=f"{day}_committee")
                if st.button("Save", key=f"save_{day}", type="primary"):
                    if topic and committee:
                        state_lib.set_weekly_topic(day, topic, committee)
                        st.success("Saved.")
                        st.rerun()
                    else:
                        st.error("Topic and committee required.")
                if existing.get("set_at"):
                    st.caption(f"Set {existing['set_at'][:10]}")

# ----------------- TAB 2: Conferences -----------------
with tabs[1]:
    st.markdown("### Upcoming and recent conferences")
    confs = state.get("conferences", [])
    if confs:
        df = pd.DataFrame(confs)[["name", "location", "start_date", "end_date", "registration_deadline", "fees_per_delegate_usd"]]
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.caption("No conferences yet.")

    with st.expander("Add conference"):
        with st.form("add_conf"):
            name = st.text_input("Name", placeholder="HMUN, NCSC, McGill SSUNS...")
            location = st.text_input("Location")
            cols_d = st.columns(3)
            start_d = cols_d[0].date_input("Start date")
            end_d = cols_d[1].date_input("End date")
            reg_d = cols_d[2].date_input("Registration deadline (optional)", value=None)
            fees = st.number_input("Fees per delegate (USD)", min_value=0.0, step=10.0, value=0.0)
            notes = st.text_area("Notes", height=80)
            if st.form_submit_button("Add", type="primary"):
                if name and location:
                    state_lib.add_conference(state_lib.Conference(
                        id=str(uuid.uuid4())[:8],
                        name=name,
                        location=location,
                        start_date=start_d.isoformat(),
                        end_date=end_d.isoformat(),
                        registration_deadline=reg_d.isoformat() if reg_d else None,
                        fees_per_delegate_usd=fees if fees > 0 else None,
                        notes=notes or None,
                    ))
                    st.success("Conference added.")
                    st.rerun()
                else:
                    st.error("Name and location required.")

# ----------------- TAB 3: Assignments -----------------
with tabs[2]:
    st.markdown("### Delegate assignments")
    confs = state.get("conferences", [])
    assignments = state.get("assignments", [])

    if not confs:
        st.info("Add a conference first.")
    else:
        conf_lookup = {c["id"]: c["name"] for c in confs}
        if assignments:
            df = pd.DataFrame(assignments)
            df["conference"] = df["conference_id"].map(conf_lookup)
            display_cols = ["conference", "delegate_name", "committee", "country_or_character", "status", "notes"]
            st.dataframe(df[display_cols], use_container_width=True, hide_index=True)
        else:
            st.caption("No assignments yet.")

        with st.expander("Add assignment"):
            with st.form("add_assignment"):
                conf_id = st.selectbox(
                    "Conference",
                    [c["id"] for c in confs],
                    format_func=lambda i: conf_lookup[i],
                )
                cols_a = st.columns(3)
                delegate = cols_a[0].text_input("Delegate name")
                committee = cols_a[1].text_input("Committee")
                country = cols_a[2].text_input("Country / Character")
                notes = st.text_area("Notes", height=60)
                if st.form_submit_button("Add", type="primary"):
                    if delegate and committee and country:
                        state_lib.add_assignment(state_lib.Assignment(
                            id=str(uuid.uuid4())[:8],
                            conference_id=conf_id,
                            delegate_name=delegate,
                            committee=committee,
                            country_or_character=country,
                            notes=notes or None,
                        ))
                        st.success("Assignment added.")
                        st.rerun()
                    else:
                        st.error("Delegate, committee, and country required.")

# ----------------- TAB 4: Curation -----------------
with tabs[3]:
    st.markdown("### Archive curation")
    st.caption("Mark documents as exemplary (boost in retrieval), outdated (deprioritize), or exec-only (hide from delegates).")

    docs = list_docs()
    if not docs:
        st.caption("Archive is empty. Run `python3 scripts/seed_archive.py` to bootstrap.")
    else:
        for d in docs:
            with st.container(border=True):
                cols = st.columns([4, 2, 2, 2, 1])
                badges = tag(d["doc_type"])
                if d["year"]:
                    badges += " " + tag(str(d["year"]))
                cols[0].markdown(f"**{d['title']}**", unsafe_allow_html=True)
                cols[0].markdown(badges, unsafe_allow_html=True)
                cols[0].caption(f"{d['chunk_count']} chunks · indexed {d['indexed_at'][:10]}")

                quality = cols[1].selectbox(
                    "Quality",
                    ["", "exemplary", "outdated"],
                    index=["", "exemplary", "outdated"].index(d["quality_flag"] or ""),
                    key=f"quality_{d['doc_id']}",
                    label_visibility="collapsed",
                )
                visibility = cols[2].selectbox(
                    "Visibility",
                    ["team", "exec_only"],
                    index=["team", "exec_only"].index(d["visibility"]),
                    key=f"vis_{d['doc_id']}",
                    label_visibility="collapsed",
                )
                if cols[3].button("Save", key=f"curate_{d['doc_id']}"):
                    with sqlite3.connect(INDEX_DB) as c:
                        c.execute(
                            "UPDATE docs SET quality_flag = ?, visibility = ? WHERE doc_id = ?",
                            (quality or None, visibility, d["doc_id"]),
                        )
                    clear_search_cache()
                    st.success("Saved.")
                    st.rerun()
                if cols[4].button("Delete", key=f"del_{d['doc_id']}"):
                    from lib.index import delete_doc
                    delete_doc(d["doc_id"])
                    clear_search_cache()
                    st.success("Deleted.")
                    st.rerun()

# ----------------- TAB 5: Cost Dashboard -----------------
with tabs[4]:
    st.markdown("### This month")
    monthly = current_monthly()
    cols = st.columns(4)
    cols[0].metric("Spent", f"${monthly.spent_usd:.2f}")
    cols[1].metric("Projected", f"${monthly.projected_usd:.2f}", delta=f"of ${monthly.cap_usd:.0f} cap")
    cols[2].metric("Cap", f"${monthly.cap_usd:.0f}")
    cols[3].metric("Headroom", f"${max(0, monthly.cap_usd - monthly.projected_usd):.2f}")

    if monthly.should_block:
        st.error(f"⚠️ Hit monthly cap. New API calls blocked until next month.")
    elif monthly.should_warn:
        st.warning(f"⚠️ Approaching monthly cap. Projected ${monthly.projected_usd:.2f} of ${monthly.cap_usd:.0f}.")
    else:
        st.success(f"On track. {monthly.fraction_used * 100:.0f}% of cap used.")

    st.markdown("### Top users this month")
    rows = top_users(20)
    if rows:
        df = pd.DataFrame(rows, columns=["user_slack_id", "cost_usd", "calls"])
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.caption("No usage yet this month.")

# ----------------- TAB 6: Alumni Outreach -----------------
with tabs[5]:
    st.markdown("### Alumni interview campaign")
    st.markdown(
        "Send the structured interview to graduating seniors and alumni. "
        "Responses get auto-indexed into the Archive so future delegates can search them."
    )
    st.info("Standalone interview submission page lives at /Alumni_Interview (publicly accessible). "
            "Director-side response viewer + 'mark as indexed' workflow lands next.", icon="🚧")

    # Quick stub: list any indexed alumni interviews
    docs = list_docs()
    interviews = [d for d in docs if d["doc_type"] == "alumni_interview"]
    st.markdown(f"### Indexed interviews ({len(interviews)})")
    for d in interviews:
        with st.container(border=True):
            st.markdown(f"**{d['title']}**")
            st.caption(f"{d['chunk_count']} chunks · indexed {d['indexed_at'][:10]}")

brand_footer()
