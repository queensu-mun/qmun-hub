from __future__ import annotations

import sqlite3
import uuid
from datetime import date, datetime

import pandas as pd
import streamlit as st

from lib import analyze, state as state_lib
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
    "Announcement",
    "Delegates",
    "Socials",
    "Scouting",
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

# ----------------- TAB 1.5: Announcement -----------------
with tabs[1]:
    st.markdown("### Pinned message for the team")
    st.caption("Shows as a banner on every delegate's home page. Keep it short.")
    current = state.get("announcement") or {}
    text = st.text_area(
        "Message",
        value=current.get("text", ""),
        placeholder="e.g. Sign-ups for HMUN close Friday at 5pm.",
        height=80,
    )
    cols_ann = st.columns([1, 1, 4])
    if cols_ann[0].button("Pin announcement", type="primary"):
        state_lib.set_announcement(text)
        st.success("Pinned.")
        st.rerun()
    if cols_ann[1].button("Clear"):
        state_lib.set_announcement(None)
        st.success("Cleared.")
        st.rerun()
    if current.get("set_at"):
        st.caption(f"Currently pinned. Set {current['set_at'][:16].replace('T', ' ')} UTC.")

# ----------------- TAB 2: Delegates -----------------
with tabs[2]:
    st.markdown("### Delegates")
    st.caption(
        "Roster, director-only common notes, and feedback on individuals. "
        "All feedback here is director-private unless explicitly shared with the delegate."
    )

    # Refresh state inside this tab so feedback we add immediately reappears.
    state = state_lib.load()
    roster = state.get("roster", [])
    feedback = state.get("feedback", [])

    sub_roster, sub_feedback, sub_insights = st.tabs([
        f"Roster ({len(roster)})",
        f"Feedback ({len([f for f in feedback if f.get('status') != 'addressed'])} open)",
        "Team Insights",
    ])

    # ---- Roster sub-tab ----
    with sub_roster:
        if not roster:
            st.caption("No delegates yet. Add the first one below.")
        else:
            for d in roster:
                with st.container(border=True):
                    head_cols = st.columns([3, 1, 1, 1])
                    badges = tag(f"year {d.get('year', '?')}") + " " + tag(d.get("status", "rookie"))
                    head_cols[0].markdown(f"**{d['name']}**", unsafe_allow_html=True)
                    head_cols[0].markdown(badges, unsafe_allow_html=True)
                    if d.get("joined_year"):
                        head_cols[0].caption(f"Joined {d['joined_year']}")

                    new_status = head_cols[1].selectbox(
                        "Status",
                        ["rookie", "veteran"],
                        index=["rookie", "veteran"].index(d.get("status", "rookie")),
                        key=f"status_{d['id']}",
                        label_visibility="collapsed",
                    )
                    new_year = head_cols[2].number_input(
                        "Year",
                        min_value=1, max_value=6,
                        value=int(d.get("year", 1)),
                        key=f"year_{d['id']}",
                        label_visibility="collapsed",
                    )
                    if head_cols[3].button("Save", key=f"save_del_{d['id']}"):
                        state_lib.update_delegate(d["id"], status=new_status, year=int(new_year))
                        st.success("Saved.")
                        st.rerun()

                    # Director-only common notes
                    notes_val = st.text_area(
                        "Common notes (director-only)",
                        value=d.get("director_notes", ""),
                        key=f"notes_{d['id']}",
                        height=90,
                        placeholder="Standing observations: strong on policy, weak on opening speeches, prefers crisis...",
                    )
                    note_cols = st.columns([1, 1, 4])
                    if note_cols[0].button("Save notes", key=f"save_notes_{d['id']}"):
                        state_lib.update_director_notes(d["id"], notes_val, by=user.name)
                        st.success("Notes saved.")
                        st.rerun()
                    if note_cols[1].button("Remove delegate", key=f"rm_del_{d['id']}"):
                        state_lib.remove_delegate(d["id"])
                        st.success("Removed.")
                        st.rerun()
                    if d.get("director_notes_updated_at"):
                        note_cols[2].caption(
                            f"Last edited by {d.get('director_notes_updated_by') or '?'} "
                            f"on {d['director_notes_updated_at'][:10]}"
                        )

                    # Quick feedback summary for this delegate
                    delegate_fb = [f for f in feedback if f["delegate_name"].strip().lower() == d["name"].strip().lower()]
                    if delegate_fb:
                        open_count = len([f for f in delegate_fb if f.get("status") != "addressed"])
                        st.caption(f"{len(delegate_fb)} feedback entries · {open_count} open")

        with st.expander("Add delegate"):
            with st.form("add_delegate"):
                cols_d = st.columns([2, 1, 1, 1])
                name_in = cols_d[0].text_input("Name")
                year_in = cols_d[1].number_input("Year", min_value=1, max_value=6, value=1)
                status_in = cols_d[2].selectbox("Status", ["rookie", "veteran"])
                joined_in = cols_d[3].text_input("Joined", value=state.get("team_year", "2026-2027"))
                email_in = st.text_input("Email (optional)")
                slack_in = st.text_input("Slack ID (optional)")
                if st.form_submit_button("Add delegate", type="primary"):
                    if name_in.strip():
                        state_lib.add_delegate(state_lib.Delegate(
                            id=state_lib.new_id(),
                            name=name_in.strip(),
                            year=int(year_in),
                            status=status_in,
                            joined_year=joined_in.strip() or None,
                            email=email_in.strip() or None,
                            slack_id=slack_in.strip() or None,
                        ))
                        st.success("Added.")
                        st.rerun()
                    else:
                        st.error("Name required.")

    # ---- Feedback sub-tab ----
    with sub_feedback:
        roster_names = sorted({d["name"] for d in roster})
        confs = state.get("conferences", [])
        conf_lookup_fb = {c["id"]: c["name"] for c in confs}

        with st.expander("Capture new feedback", expanded=not feedback):
            with st.form("add_feedback"):
                cols_fb1 = st.columns([2, 1, 1])
                if roster_names:
                    delegate_pick = cols_fb1[0].selectbox("Delegate", roster_names + ["(other / not on roster)"])
                else:
                    delegate_pick = "(other / not on roster)"
                    cols_fb1[0].caption("No roster yet — type a name below.")
                source_in = cols_fb1[1].selectbox("Source", ["mock", "conference", "training", "other"])
                conf_options = [None] + [c["id"] for c in confs]
                conf_pick = cols_fb1[2].selectbox(
                    "Conference (if any)",
                    conf_options,
                    format_func=lambda i: "—" if i is None else conf_lookup_fb.get(i, "?"),
                )

                custom_name = ""
                if delegate_pick == "(other / not on roster)":
                    custom_name = st.text_input("Delegate name")

                notes_in = st.text_area(
                    "Notes",
                    height=120,
                    placeholder="What you observed. Be specific. Quote them if useful.",
                )
                tags_raw = st.text_input("Tags (comma-separated)", placeholder="opening-speech, bloc-leadership, research")
                cols_fb2 = st.columns([2, 2, 2])
                assigned_in = cols_fb2[0].text_input("Assign to (director)", placeholder="Who follows up")
                visibility_in = cols_fb2[1].selectbox(
                    "Visibility",
                    ["director_only", "shared_with_delegate"],
                    format_func=lambda v: "Director-only" if v == "director_only" else "Share with delegate",
                )
                status_in_fb = cols_fb2[2].selectbox("Status", ["open", "in_progress", "addressed"])

                if st.form_submit_button("Save feedback", type="primary"):
                    chosen_name = (
                        custom_name.strip()
                        if delegate_pick == "(other / not on roster)"
                        else delegate_pick
                    )
                    if not chosen_name or not notes_in.strip():
                        st.error("Delegate name and notes are both required.")
                    else:
                        tags_list = [t.strip() for t in tags_raw.split(",") if t.strip()]
                        state_lib.add_feedback(state_lib.Feedback(
                            id=state_lib.new_id(),
                            delegate_name=chosen_name,
                            source=source_in,
                            notes=notes_in.strip(),
                            tags=tags_list,
                            conference_id=conf_pick,
                            assigned_to=assigned_in.strip() or None,
                            status=status_in_fb,
                            visibility=visibility_in,
                            created_by=user.name,
                            created_at=state_lib.now_iso(),
                        ))
                        st.success("Feedback saved.")
                        st.rerun()

        # Filter row
        filter_cols = st.columns([1, 1, 1, 2])
        status_filter = filter_cols[0].selectbox(
            "Filter status",
            ["all", "open", "in_progress", "addressed"],
            key="fb_status_filter",
        )
        delegate_filter = filter_cols[1].selectbox(
            "Filter delegate",
            ["all"] + sorted({f["delegate_name"] for f in feedback}),
            key="fb_delegate_filter",
        )
        assignee_filter = filter_cols[2].selectbox(
            "Filter assignee",
            ["all"] + sorted({f.get("assigned_to") for f in feedback if f.get("assigned_to")}),
            key="fb_assignee_filter",
        )

        rows = list(feedback)
        if status_filter != "all":
            rows = [f for f in rows if f.get("status") == status_filter]
        if delegate_filter != "all":
            rows = [f for f in rows if f["delegate_name"] == delegate_filter]
        if assignee_filter != "all":
            rows = [f for f in rows if f.get("assigned_to") == assignee_filter]

        # Newest first
        rows.sort(key=lambda f: f.get("created_at") or "", reverse=True)

        if not rows:
            st.caption("No feedback matches these filters.")
        else:
            for f in rows:
                with st.container(border=True):
                    head_cols = st.columns([3, 1, 1, 1])
                    badges = tag(f.get("source", "other")) + " " + tag(f.get("status", "open"))
                    if f.get("visibility") == "shared_with_delegate":
                        badges += " " + tag("shared")
                    else:
                        badges += " " + tag("director-only")
                    head_cols[0].markdown(f"**{f['delegate_name']}**", unsafe_allow_html=True)
                    head_cols[0].markdown(badges, unsafe_allow_html=True)
                    when = (f.get("created_at") or "")[:10]
                    by = f.get("created_by") or "?"
                    head_cols[0].caption(f"By {by} on {when}")

                    new_status = head_cols[1].selectbox(
                        "Status",
                        ["open", "in_progress", "addressed"],
                        index=["open", "in_progress", "addressed"].index(f.get("status", "open")),
                        key=f"fb_status_{f['id']}",
                        label_visibility="collapsed",
                    )
                    new_assignee = head_cols[2].text_input(
                        "Assignee",
                        value=f.get("assigned_to") or "",
                        key=f"fb_assignee_{f['id']}",
                        label_visibility="collapsed",
                        placeholder="Assignee",
                    )
                    if head_cols[3].button("Save", key=f"fb_save_{f['id']}"):
                        state_lib.update_feedback(
                            f["id"],
                            status=new_status,
                            assigned_to=new_assignee.strip() or None,
                        )
                        st.success("Saved.")
                        st.rerun()

                    st.markdown(f.get("notes", ""))
                    if f.get("tags"):
                        st.markdown(" ".join(tag(t) for t in f["tags"]), unsafe_allow_html=True)
                    if f.get("conference_id"):
                        st.caption(f"Conference: {conf_lookup_fb.get(f['conference_id'], '?')}")
                    if st.button("Delete", key=f"fb_del_{f['id']}"):
                        state_lib.remove_feedback(f["id"])
                        st.rerun()

    # ---- Team Insights sub-tab ----
    with sub_insights:
        st.markdown("### Team weaknesses + training plan")
        st.caption(
            "Claude reads all feedback + roster and produces a weekly team analysis. "
            "Cached by week, regenerate when you've added significant new feedback."
        )

        cached = analyze.cached_insights()
        gen_cols = st.columns([1, 1, 4])
        if gen_cols[0].button("Generate insights", type="primary"):
            if not feedback:
                st.warning("No feedback to analyze yet.")
            else:
                with st.spinner("Analyzing..."):
                    try:
                        cached = analyze.generate(user_slack_id=user.slack_id, force=True)
                        st.success(f"Generated. Cost: ${cached.cost_usd:.4f}")
                    except Exception as e:
                        st.error(f"Failed: {e}")
        if cached and gen_cols[1].button("Clear cache"):
            analyze.clear_cache()
            st.rerun()

        if not cached:
            st.info("No insights generated yet. Click Generate above.")
        else:
            st.caption(
                f"Generated {(cached.generated_at or '')[:16].replace('T', ' ')} UTC · "
                f"week of {cached.week_start} · {cached.feedback_count} feedback entries · "
                f"${cached.cost_usd:.4f}"
            )
            if cached.summary:
                st.markdown(f"> {cached.summary}")

            if cached.weaknesses:
                st.markdown("#### Team weaknesses")
                for w in cached.weaknesses:
                    st.markdown(f"- {w}")

            if cached.training_recommendations:
                st.markdown("#### Recommended training exercises")
                for r in cached.training_recommendations:
                    st.markdown(f"- {r}")

            if cached.delegate_focus:
                st.markdown("#### Per-delegate focus areas")
                for name, areas in cached.delegate_focus.items():
                    with st.container(border=True):
                        st.markdown(f"**{name}**")
                        for a in areas:
                            st.markdown(f"- {a}")

# ----------------- TAB 3: Socials -----------------
with tabs[3]:
    st.markdown("### Socials")
    st.caption("Lineskip nights, formals, team dinners. Upcoming socials surface on the home page for everyone.")

    socials = state_lib.list_socials()
    today = date.today().isoformat()

    if socials:
        for s in socials:
            past = (s.get("date") or "") < today
            with st.container(border=True):
                cols_s = st.columns([3, 1, 1])
                badges = tag(s.get("type", "other"))
                if past:
                    badges += " " + tag("past")
                cols_s[0].markdown(f"**{s.get('date')}** · {s.get('location') or ''}", unsafe_allow_html=True)
                cols_s[0].markdown(badges, unsafe_allow_html=True)
                if s.get("notes"):
                    cols_s[0].caption(s["notes"])
                if s.get("created_by"):
                    cols_s[0].caption(f"Added by {s['created_by']}")
                if cols_s[2].button("Remove", key=f"rm_social_{s['id']}"):
                    state_lib.remove_social(s["id"])
                    st.rerun()
    else:
        st.caption("No socials yet.")

    with st.expander("Add social", expanded=not socials):
        with st.form("add_social"):
            cols_a = st.columns([1, 1, 2])
            date_in = cols_a[0].date_input("Date")
            type_in = cols_a[1].selectbox("Type", ["lineskip", "formal", "dinner", "other"])
            location_in = cols_a[2].text_input("Location", placeholder="Stages, Donald Gordon, ...")
            notes_in = st.text_area("Notes", height=70, placeholder="Anything the team should know.")
            if st.form_submit_button("Add social", type="primary"):
                state_lib.add_social(state_lib.Social(
                    id=state_lib.new_id(),
                    date=date_in.isoformat(),
                    type=type_in,
                    location=location_in.strip() or None,
                    notes=notes_in.strip() or None,
                    created_by=user.name,
                    created_at=state_lib.now_iso(),
                ))
                st.success("Added.")
                st.rerun()

# ----------------- TAB 4: Scouting (other delegations) -----------------
with tabs[4]:
    st.markdown("### Scouting: other delegations")
    st.caption(
        "Information bank on other schools' MUN teams: how they fight, who their stars are, where to expect them."
    )

    delegations = state_lib.list_delegations()

    # Quick filter
    if delegations:
        strength_filter = st.selectbox(
            "Filter by strength",
            ["all", "rising", "competitive", "strong", "dominant", "unknown"],
            key="delegation_strength_filter",
        )
        rows_d = delegations if strength_filter == "all" else [d for d in delegations if d.get("strength_level") == strength_filter]

        for d in rows_d:
            with st.container(border=True):
                head_cols = st.columns([3, 1, 1])
                head_cols[0].markdown(f"**{d['school']}**")
                strength_label = tag(d.get("strength_level", "unknown"))
                head_cols[0].markdown(strength_label, unsafe_allow_html=True)
                if d.get("conferences_seen_at"):
                    head_cols[0].caption("Seen at: " + ", ".join(d["conferences_seen_at"]))
                if d.get("last_updated_at"):
                    head_cols[0].caption(
                        f"Updated by {d.get('last_updated_by') or '?'} on {d['last_updated_at'][:10]}"
                    )

                with st.expander("Edit / view detail", expanded=False):
                    new_strength = st.selectbox(
                        "Strength",
                        ["unknown", "rising", "competitive", "strong", "dominant"],
                        index=["unknown", "rising", "competitive", "strong", "dominant"].index(d.get("strength_level", "unknown")),
                        key=f"d_strength_{d['id']}",
                    )
                    confs_csv = st.text_input(
                        "Conferences seen at (comma-separated)",
                        value=", ".join(d.get("conferences_seen_at") or []),
                        key=f"d_confs_{d['id']}",
                    )
                    notable_csv = st.text_input(
                        "Notable delegates (comma-separated)",
                        value=", ".join(d.get("notable_delegates") or []),
                        key=f"d_notable_{d['id']}",
                    )
                    tact = st.text_area(
                        "Tactical notes",
                        value=d.get("tactical_notes", ""),
                        height=110,
                        key=f"d_tact_{d['id']}",
                        placeholder="How they speak, how they bloc, what they go for, where they break.",
                    )
                    awards = st.text_area(
                        "Awards tendency",
                        value=d.get("awards_tendency", ""),
                        height=70,
                        key=f"d_awards_{d['id']}",
                        placeholder="What they win, where, how often.",
                    )
                    edit_cols = st.columns([1, 1, 4])
                    if edit_cols[0].button("Save", key=f"save_deleg_{d['id']}"):
                        state_lib.update_delegation(
                            d["id"],
                            strength_level=new_strength,
                            conferences_seen_at=[c.strip() for c in confs_csv.split(",") if c.strip()],
                            notable_delegates=[n.strip() for n in notable_csv.split(",") if n.strip()],
                            tactical_notes=tact,
                            awards_tendency=awards,
                            last_updated_by=user.name,
                        )
                        st.success("Saved.")
                        st.rerun()
                    if edit_cols[1].button("Remove", key=f"rm_deleg_{d['id']}"):
                        state_lib.remove_delegation(d["id"])
                        st.rerun()

                # Quick read view (outside expander) so it's scannable
                if d.get("tactical_notes"):
                    st.markdown(d["tactical_notes"])
                if d.get("awards_tendency"):
                    st.caption(f"Awards: {d['awards_tendency']}")
                if d.get("notable_delegates"):
                    st.caption("Notable: " + ", ".join(d["notable_delegates"]))
    else:
        st.caption("No delegations scouted yet. Add the first below.")

    with st.expander("Add delegation"):
        with st.form("add_delegation"):
            cols_n = st.columns([2, 1])
            school_in = cols_n[0].text_input("School", placeholder="McGill, Concordia, U of T...")
            strength_in = cols_n[1].selectbox(
                "Strength",
                ["unknown", "rising", "competitive", "strong", "dominant"],
            )
            confs_in = st.text_input(
                "Conferences seen at (comma-separated)",
                placeholder="HMUN, NCSC, McGill SSUNS",
            )
            notable_in = st.text_input(
                "Notable delegates (comma-separated)",
                placeholder="Sarah K., Alex P.",
            )
            tact_in = st.text_area(
                "Tactical notes",
                height=110,
                placeholder="Aggressive on procedure. Strong bloc discipline. Weak on crisis pivots.",
            )
            awards_in = st.text_area("Awards tendency", height=70, placeholder="Best Delegate ratio ~30% on procedural committees.")
            if st.form_submit_button("Add", type="primary"):
                if school_in.strip():
                    state_lib.add_delegation(state_lib.Delegation(
                        id=state_lib.new_id(),
                        school=school_in.strip(),
                        strength_level=strength_in,
                        conferences_seen_at=[c.strip() for c in confs_in.split(",") if c.strip()],
                        notable_delegates=[n.strip() for n in notable_in.split(",") if n.strip()],
                        tactical_notes=tact_in,
                        awards_tendency=awards_in,
                        last_updated_at=state_lib.now_iso(),
                        last_updated_by=user.name,
                    ))
                    st.success("Added.")
                    st.rerun()
                else:
                    st.error("School name required.")

# ----------------- TAB 5: Conferences -----------------
with tabs[5]:
    st.markdown("### Conferences")
    confs = state.get("conferences", [])
    if confs:
        for c in confs:
            fees = f"${c['fees_per_delegate_usd']:.0f}" if c.get("fees_per_delegate_usd") else "—"
            reg = c.get("registration_deadline") or "—"
            st.markdown(
                f"""
<div class='doc-row'>
  <div>
    <div class='doc-row-title'>{c['name']}</div>
    <div class='doc-row-meta subtle'>{c['location']} · {c['start_date']} → {c['end_date']} · reg by {reg} · {fees}/delegate</div>
  </div>
</div>
""",
                unsafe_allow_html=True,
            )
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

# ----------------- TAB 6: Assignments -----------------
with tabs[6]:
    st.markdown("### Delegate assignments")
    confs = state.get("conferences", [])
    assignments = state.get("assignments", [])

    if not confs:
        st.info("Add a conference first.")
    else:
        conf_lookup = {c["id"]: c["name"] for c in confs}
        if assignments:
            for a in assignments:
                conf_name = conf_lookup.get(a["conference_id"], "?")
                st.markdown(
                    f"""
<div class='doc-row'>
  <div>
    <div class='doc-row-title'>{a['delegate_name']} <span class='subtle' style='font-weight:500;'>·</span> {a['country_or_character']}</div>
    <div class='doc-row-meta subtle'>{conf_name} · {a['committee']} · {a.get('status', 'assigned')}</div>
  </div>
</div>
""",
                    unsafe_allow_html=True,
                )
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

# ----------------- TAB 7: Curation -----------------
with tabs[7]:
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

# ----------------- TAB 8: Cost Dashboard -----------------
with tabs[8]:
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
        for u, cost, calls in rows:
            st.markdown(
                f"""
<div class='doc-row'>
  <div>
    <div class='doc-row-title'>{u}</div>
    <div class='doc-row-meta subtle'>{calls} call{'s' if calls != 1 else ''}</div>
  </div>
  <div style='font-family:Inter Tight, sans-serif; font-weight:600; color:var(--text);'>${cost:.4f}</div>
</div>
""",
                unsafe_allow_html=True,
            )
    else:
        st.caption("No usage yet this month.")

# ----------------- TAB 9: Alumni Outreach -----------------
with tabs[9]:
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
