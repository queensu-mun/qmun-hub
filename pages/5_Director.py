from __future__ import annotations

import uuid
from datetime import date, datetime
from pathlib import Path

import pandas as pd
import streamlit as st

from lib import analyze, state as state_lib
from lib.auth import require_exec
from lib.budget import current_monthly, top_users
from lib.index import list_docs
from lib.search import clear_cache as clear_search_cache
from lib.ui import brand_footer, inject_global_css, page_header, tag, top_nav

st.set_page_config(page_title="Director · Queen's MUN", page_icon="🌐", layout="wide", initial_sidebar_state="collapsed")
inject_global_css()
user = require_exec()
top_nav(user)

page_header("Director", "Run the team", "Weekly topics, conferences, assignments, archive curation, costs.")

tabs = st.tabs([
    "Weekly Topics",
    "Announcement & Socials",
    "Delegates",
    "Scouting",
    "Conferences",
    "Assignments",
    "Curation",
    "API Costs",
    "Alumni Outreach",
    "Finance",
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

# ----------------- TAB 1: Announcement & Socials -----------------
with tabs[1]:
    # ----- Announcement -----
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

    st.divider()

    # ----- Socials editing (public read view lives at /Socials) -----
    st.markdown("### Socials")
    st.caption(
        "Lineskip nights, formals, team dinners. Anyone on the team can browse these "
        "at the Socials page. Attach flyers, posters, sign-up sheets per event."
    )

    socials = state_lib.list_socials()
    today = date.today().isoformat()

    def _human_size(n: int) -> str:
        for unit in ("B", "KB", "MB"):
            if n < 1024:
                return f"{n:.0f} {unit}"
            n /= 1024
        return f"{n:.1f} GB"

    if socials:
        for s in socials:
            past_event = (s.get("date") or "") < today
            with st.container(border=True):
                cols_s = st.columns([3, 1, 1])
                badges = tag(s.get("type", "other"))
                if past_event:
                    badges += " " + tag("past")
                attachments = s.get("attachments") or []
                if attachments:
                    badges += " " + tag(f"{len(attachments)} file" + ("s" if len(attachments) != 1 else ""))
                cols_s[0].markdown(f"**{s.get('date')}** · {s.get('location') or ''}", unsafe_allow_html=True)
                cols_s[0].markdown(badges, unsafe_allow_html=True)
                if s.get("notes"):
                    cols_s[0].caption(s["notes"])
                if s.get("created_by"):
                    cols_s[0].caption(f"Added by {s['created_by']}")
                if cols_s[2].button("Remove", key=f"rm_social_{s['id']}"):
                    state_lib.remove_social(s["id"])
                    st.rerun()

                if attachments:
                    st.markdown("**Attachments**")
                    for att in attachments:
                        att_cols = st.columns([3, 1, 1])
                        mime = att.get("mime_type", "")
                        is_image = mime.startswith("image/")
                        att_cols[0].markdown(
                            f"`{att['filename']}` <span class='subtle'>· {_human_size(att.get('size_bytes', 0))}</span>",
                            unsafe_allow_html=True,
                        )
                        if att.get("uploaded_by"):
                            att_cols[0].caption(
                                f"Uploaded by {att['uploaded_by']} on {(att.get('uploaded_at') or '')[:10]}"
                            )
                        try:
                            file_bytes = open(att["stored_path"], "rb").read()
                            att_cols[1].download_button(
                                "Download",
                                data=file_bytes,
                                file_name=att["filename"],
                                mime=mime,
                                key=f"dl_{s['id']}_{att['filename']}",
                                use_container_width=True,
                            )
                        except FileNotFoundError:
                            att_cols[1].caption("file missing")
                        if att_cols[2].button("Delete", key=f"rm_att_{s['id']}_{att['filename']}"):
                            state_lib.remove_social_attachment(s["id"], att["filename"])
                            st.rerun()
                        if is_image:
                            try:
                                st.image(att["stored_path"], width=320)
                            except Exception:
                                pass

                uploaded = st.file_uploader(
                    "Add files",
                    type=["png", "jpg", "jpeg", "webp", "gif", "pdf"],
                    accept_multiple_files=True,
                    key=f"upload_{s['id']}",
                )
                if uploaded:
                    for f in uploaded:
                        try:
                            state_lib.add_social_attachment(
                                s["id"],
                                filename=f.name,
                                data=f.getvalue(),
                                mime_type=f.type,
                                uploaded_by=user.name,
                            )
                        except Exception as e:
                            st.error(f"Upload failed for {f.name}: {e}")
                    st.success(f"Uploaded {len(uploaded)} file(s).")
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
                st.success("Added. Expand the social to attach files.")
                st.rerun()

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
                    cols_fb1[0].caption("No roster yet. Type a name below.")
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

                    # Per-entry share toggle. Default stays director-only; flipping
                    # this on surfaces the entry on the delegate's My Feedback page.
                    shared_now = f.get("visibility") == "shared_with_delegate"
                    shared_new = st.toggle(
                        "Visible to delegate",
                        value=shared_now,
                        key=f"fb_vis_{f['id']}",
                        help="When on, this entry appears on the delegate's My Feedback page. Off keeps it director-only.",
                    )
                    if shared_new != shared_now:
                        state_lib.update_feedback(
                            f["id"],
                            visibility="shared_with_delegate" if shared_new else "director_only",
                        )
                        st.rerun()

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

# ----------------- TAB 3: Scouting (other delegations) -----------------
with tabs[3]:
    st.markdown("### Scouting: other delegations")
    st.caption(
        "Information bank on other schools' MUN teams: how they fight, who their stars are, where to expect them. "
        "The team-facing read view lives at the Scouting page. Long-term, alumni interview responses will populate "
        "this database automatically; for now, add manual entries here."
    )

    # ---- Drafts queue (deposited by the scouting content process) ----
    drafts = state_lib.list_delegations(status="draft")
    if drafts:
        st.markdown(f"#### Drafts awaiting review ({len(drafts)})")
        st.caption(
            "Deposited automatically (see docs/SCOUTING_DRAFTS.md). Approve to publish "
            "to the team-facing Scouting page, or discard. Drafts are never shown to the team."
        )
        for d in drafts:
            with st.container(border=True):
                head_cols = st.columns([3, 1])
                head_cols[0].markdown(f"**{d['school']}** &nbsp;{tag('draft', accent=True)} {tag(d.get('strength_level', 'unknown'))}", unsafe_allow_html=True)
                if d.get("conferences_seen_at"):
                    head_cols[0].caption("Seen at: " + ", ".join(d["conferences_seen_at"]))
                if d.get("last_updated_by"):
                    head_cols[0].caption(f"Submitted by {d['last_updated_by']} on {(d.get('last_updated_at') or '')[:10]}")
                if d.get("tactical_notes"):
                    st.markdown(d["tactical_notes"])
                if d.get("awards_tendency"):
                    st.caption(f"Awards: {d['awards_tendency']}")
                if d.get("notable_delegates"):
                    st.caption("Notable: " + ", ".join(d["notable_delegates"]))
                draft_cols = st.columns([1.2, 1, 4])
                if draft_cols[0].button("Approve and publish", key=f"approve_draft_{d['id']}", type="primary"):
                    state_lib.publish_delegation(d["id"], by=user.name)
                    st.success("Published.")
                    st.rerun()
                if draft_cols[1].button("Discard", key=f"discard_draft_{d['id']}"):
                    state_lib.remove_delegation(d["id"])
                    st.rerun()
        st.divider()

    delegations = state_lib.list_delegations(status="published")

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

# ----------------- TAB 4: Conferences -----------------
with tabs[4]:
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
            # Per-conference brief gate. Default off: delegates assigned to this
            # conference only see Conference depth on the Brief page once this is on.
            briefs_on = bool(c.get("briefs_enabled"))
            briefs_new = st.toggle(
                "Conference briefs enabled",
                value=briefs_on,
                key=f"conf_briefs_{c['id']}",
                help="When on, delegates assigned to this conference can generate full conference briefs. Execs always can.",
            )
            if briefs_new != briefs_on:
                state_lib.update_conference(c["id"], briefs_enabled=briefs_new)
                st.rerun()
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

# ----------------- TAB 5: Assignments -----------------
with tabs[5]:
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

# ----------------- TAB 6: Curation -----------------
with tabs[6]:
    st.markdown("### Archive curation")
    st.caption("Mark documents as exemplary (boost in retrieval), outdated (deprioritize), or exec-only (hide from delegates).")

    # ---- Sync from Drive: pull the team folder straight into the archive ----
    from lib import drive_sync

    with st.container(border=True):
        st.markdown("#### Sync from Drive")
        if not drive_sync.is_configured():
            st.caption(
                "Pull documents straight from the team Google Drive folder into the "
                "searchable archive. Not connected yet."
            )
            st.info(
                "To connect: a Google Cloud **service account** key and the team folder id go "
                "in the app's secrets under `[google]`, and the folder is shared with the "
                "service account's email. Setup steps are in `DEPLOY.md`. Until then, use "
                "**Reindex archive** below to upload files by hand."
            )
        else:
            last = drive_sync.last_sync()
            st.caption(
                "Pull every supported doc (Google Docs, PDF, Word) from the team Drive folder "
                "into the archive. Re-running re-indexes changed files in place."
                + (f" Last sync: {last.strftime('%Y-%m-%d %H:%M UTC')}." if last else " Never synced yet.")
            )
            full_resync = st.checkbox(
                "Full re-pull (ignore last-sync, re-index everything)",
                key="drive_full_resync",
            )
            drive_running = st.session_state.get("drive_sync_running", False)
            if st.button("Sync from Drive", type="primary", disabled=drive_running, key="drive_sync_btn"):
                st.session_state["drive_sync_running"] = True
                st.rerun()

            if drive_running:
                try:
                    with st.status("Syncing from Drive...", expanded=True) as status_box:
                        result = drive_sync.sync_drive(
                            full=st.session_state.get("drive_full_resync", False),
                            log=status_box.write,
                        )
                        status_box.update(label="Drive sync finished.", state="complete")
                except Exception as e:
                    result = {"indexed": [], "skipped": [], "errors": [f"Drive sync failed: {e}"],
                              "total_chunks": 0, "stats": None, "synced_at": None}
                finally:
                    st.session_state["drive_sync_running"] = False
                st.session_state["drive_sync_result"] = result
                clear_search_cache()
                st.rerun()

            last_sync_run = st.session_state.get("drive_sync_result")
            if last_sync_run:
                n_ok = len(last_sync_run["indexed"])
                summary = f"Synced {n_ok} doc{'s' if n_ok != 1 else ''} ({last_sync_run['total_chunks']} chunks)."
                if last_sync_run["stats"]:
                    summary += f" Archive now: {last_sync_run['stats']['n_docs']} docs / {last_sync_run['stats']['n_chunks']} chunks."
                if n_ok:
                    st.success(summary)
                elif not last_sync_run["errors"]:
                    st.info("No changed files since last sync.")
                for fname, reason in last_sync_run["skipped"]:
                    st.warning(f"Skipped {fname}: {reason}")
                for err in last_sync_run["errors"]:
                    st.error(err)

    # ---- Reindex: upload docs + one-click ingest, no SSH needed ----
    from lib.ingest import INCOMING_DIR, ingest_folder

    with st.container(border=True):
        st.markdown("#### Reindex archive")
        st.caption(
            "Indexes every .md / .pdf / .docx in `data/incoming` into the searchable archive "
            "(chunk, embed, upsert). Re-running re-indexes changed files in place. "
            "Upload below or drop files in the folder, then click once."
        )

        new_files = st.file_uploader(
            "Add documents to data/incoming",
            type=["md", "pdf", "docx"],
            accept_multiple_files=True,
            key="curation_incoming_upload",
        )
        if new_files and st.button("Save uploads to data/incoming", key="curation_save_uploads"):
            INCOMING_DIR.mkdir(parents=True, exist_ok=True)
            for f in new_files:
                safe_name = Path(f.name).name
                (INCOMING_DIR / safe_name).write_bytes(f.getvalue())
            st.success(f"Saved {len(new_files)} file(s). Now click Reindex archive.")

        reindex_running = st.session_state.get("reindex_running", False)
        if st.button("Reindex archive", type="primary", disabled=reindex_running, key="reindex_btn"):
            st.session_state["reindex_running"] = True
            st.rerun()

        if reindex_running:
            try:
                with st.status("Reindexing archive...", expanded=True) as status_box:
                    result = ingest_folder(INCOMING_DIR, log=status_box.write)
                    status_box.update(label="Reindex finished.", state="complete")
            except Exception as e:
                result = {"indexed": [], "skipped": [], "errors": [f"Reindex failed: {e}"],
                          "total_chunks": 0, "stats": None}
            finally:
                st.session_state["reindex_running"] = False
            st.session_state["reindex_result"] = result
            clear_search_cache()
            st.rerun()

        last_run = st.session_state.get("reindex_result")
        if last_run:
            n_ok = len(last_run["indexed"])
            summary = f"Indexed {n_ok} doc{'s' if n_ok != 1 else ''} ({last_run['total_chunks']} chunks)."
            if last_run["stats"]:
                summary += f" Archive now: {last_run['stats']['n_docs']} docs / {last_run['stats']['n_chunks']} chunks."
            if n_ok:
                st.success(summary)
            for fname, reason in last_run["skipped"]:
                st.warning(f"Skipped {fname}: {reason}")
            for err in last_run["errors"]:
                st.error(err)

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
                    from lib.index import update_doc_curation
                    update_doc_curation(
                        d["doc_id"], quality_flag=quality or None, visibility=visibility
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

# ----------------- TAB 7: API Costs (admin-only) -----------------
with tabs[7]:
    if not user.is_admin:
        st.info("API cost tracking is admin-only.")
    else:
        st.caption("What the app itself spends on AI (Anthropic + Voyage). For team money, see the Finance tab.")
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

# ----------------- TAB 8: Alumni Outreach -----------------
with tabs[8]:
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

# ----------------- TAB 9: Finance (admin-only) -----------------
with tabs[9]:
    if not user.is_admin:
        st.info("Finance is admin-only.")
    else:
        st.caption("Track team money: dues, income, expenses, and budget lines. All amounts in CAD.")
        summary = state_lib.finance_summary()
        cards = st.columns(4)
        cards[0].metric("Net balance", f"${summary['net']:,.2f}")
        cards[1].metric("Money in", f"${summary['income'] + summary['collected_dues']:,.2f}")
        cards[2].metric("Expenses", f"${summary['expense']:,.2f}")
        cards[3].metric("Outstanding dues", f"${summary['outstanding_dues']:,.2f}")
        caption_bits = []
        if summary["collected_dues"]:
            caption_bits.append(f"Dues collected: ${summary['collected_dues']:,.2f}")
        if summary["budgeted"]:
            caption_bits.append(f"Budgeted (planned): ${summary['budgeted']:,.2f}")
        if caption_bits:
            st.caption(" · ".join(caption_bits))

        confs = state.get("conferences", [])
        conf_names = {c["id"]: c["name"] for c in confs}
        roster = state.get("roster", [])
        roster_names = [d["name"] for d in roster]

        # ---- Dues roster: who has / hasn't paid ----
        st.markdown("### Dues")
        dues_amount = float(state_lib.get_setting("dues_amount_cad", 0.0) or 0.0)
        dcols = st.columns([2, 1, 3])
        new_amt = dcols[0].number_input(
            "Dues per member (CAD)", min_value=0.0, step=5.0, value=dues_amount, key="dues_amount_input",
        )
        if dcols[1].button("Save", key="save_dues_amount", use_container_width=True):
            state_lib.update_settings(dues_amount_cad=float(new_amt))
            st.success("Dues amount saved.")
            st.rerun()

        if not roster:
            st.caption("No roster yet. Add delegates in the Delegates tab to track dues.")
        else:
            # Map each roster member (case-insensitive name) to their dues entry.
            dues_by_member = {}
            for f in state_lib.list_finances(kind="due"):
                if f.get("category") == "dues" and f.get("delegate_name"):
                    dues_by_member.setdefault(f["delegate_name"].strip().lower(), f)

            uninvoiced = [m for m in roster if m["name"].strip().lower() not in dues_by_member]
            paid_n = sum(1 for f in dues_by_member.values() if f.get("status") in ("paid", "reconciled"))
            st.caption(f"{paid_n} paid · {len(dues_by_member) - paid_n} outstanding · {len(uninvoiced)} not invoiced")

            if dues_amount > 0 and uninvoiced:
                if st.button(f"Invoice all {len(uninvoiced)} uninvoiced at ${dues_amount:,.0f}", key="invoice_all"):
                    for m in uninvoiced:
                        state_lib.add_finance_entry(state_lib.FinanceEntry(
                            id=state_lib.new_id(), kind="due",
                            description=f"{state.get('team_year', '')} dues".strip(),
                            amount_cad=dues_amount, date=date.today().isoformat(),
                            category="dues", delegate_name=m["name"], status="outstanding",
                            created_by=user.name, created_at=state_lib.now_iso(),
                        ))
                    st.rerun()

            for m in roster:
                entry = dues_by_member.get(m["name"].strip().lower())
                drow = st.columns([4, 2, 1.6])
                if entry is None:
                    badge = tag("not invoiced")
                    amt_txt = "—"
                elif entry.get("status") in ("paid", "reconciled"):
                    badge = tag("paid")
                    amt_txt = f"${entry['amount_cad']:,.0f}"
                else:
                    badge = tag("outstanding", accent=True)
                    amt_txt = f"${entry['amount_cad']:,.0f}"
                drow[0].markdown(f"{m['name']} &nbsp; {badge}", unsafe_allow_html=True)
                drow[1].markdown(
                    f"<div style='text-align:right;font-family:Inter Tight,sans-serif;"
                    f"font-weight:600;'>{amt_txt}</div>", unsafe_allow_html=True,
                )
                with drow[2]:
                    if entry is None:
                        if dues_amount > 0 and st.button("Invoice", key=f"inv_{m['id']}", use_container_width=True):
                            state_lib.add_finance_entry(state_lib.FinanceEntry(
                                id=state_lib.new_id(), kind="due",
                                description=f"{state.get('team_year', '')} dues".strip(),
                                amount_cad=dues_amount, date=date.today().isoformat(),
                                category="dues", delegate_name=m["name"], status="outstanding",
                                created_by=user.name, created_at=state_lib.now_iso(),
                            ))
                            st.rerun()
                    elif entry.get("status") not in ("paid", "reconciled"):
                        if st.button("Mark paid", key=f"duespaid_{entry['id']}", use_container_width=True):
                            state_lib.update_finance_entry(entry["id"], status="paid")
                            st.rerun()
                    else:
                        if st.button("Mark unpaid", key=f"duesunpaid_{entry['id']}", use_container_width=True):
                            state_lib.update_finance_entry(entry["id"], status="outstanding")
                            st.rerun()

        # ---- Per-conference roll-up ----
        if confs:
            st.markdown("### By conference")
            fins = state_lib.list_finances()
            roll = []
            for c in confs:
                cid = c["id"]
                exp = sum(f["amount_cad"] for f in fins if f["kind"] == "expense" and f.get("conference_id") == cid)
                money_in = sum(
                    f["amount_cad"] for f in fins
                    if f.get("conference_id") == cid and (
                        f["kind"] == "income" or (f["kind"] == "due" and f.get("status") in ("paid", "reconciled"))
                    )
                )
                n_del = len(state_lib.assignments_for_conference(cid))
                roll.append({
                    "Conference": c["name"],
                    "Delegates": n_del,
                    "Expenses": exp,
                    "Money in": money_in,
                    "Cost / delegate": (exp / n_del) if n_del else exp,
                })
            df_roll = pd.DataFrame(roll)
            st.dataframe(
                df_roll, hide_index=True, use_container_width=True,
                column_config={
                    "Expenses": st.column_config.NumberColumn(format="$%.2f"),
                    "Money in": st.column_config.NumberColumn(format="$%.2f"),
                    "Cost / delegate": st.column_config.NumberColumn(format="$%.2f"),
                },
            )

        st.markdown("### Add entry")
        with st.expander("Add a finance entry"):
            with st.form("add_finance"):
                fcols = st.columns(3)
                kind = fcols[0].selectbox(
                    "Type", state_lib.FINANCE_KINDS,
                    format_func=lambda k: {
                        "due": "Due (owed to team)", "income": "Income (received)",
                        "expense": "Expense (spent)", "budget": "Budget (planned)",
                    }[k],
                )
                category = fcols[1].selectbox("Category", state_lib.FINANCE_CATEGORIES)
                fin_date = fcols[2].date_input("Date")
                description = st.text_input("Description", placeholder="e.g. NCSC registration, fall dues, bus rental")
                acols = st.columns(3)
                amount = acols[0].number_input("Amount (CAD)", min_value=0.0, step=10.0, value=0.0)
                status = acols[1].selectbox("Status", state_lib.FINANCE_STATUSES)
                conf_choice = acols[2].selectbox(
                    "Conference (optional)", ["—"] + [c["name"] for c in confs],
                )
                delegate_choice = st.selectbox(
                    "Delegate (optional, for dues / who-owes)", ["—"] + roster_names,
                )
                fnotes = st.text_area("Notes", height=70)
                if st.form_submit_button("Add entry", type="primary"):
                    if description and amount > 0:
                        conf_id = next((c["id"] for c in confs if c["name"] == conf_choice), None)
                        state_lib.add_finance_entry(state_lib.FinanceEntry(
                            id=state_lib.new_id(),
                            kind=kind,
                            description=description,
                            amount_cad=float(amount),
                            date=fin_date.isoformat(),
                            category=category,
                            conference_id=conf_id,
                            delegate_name=delegate_choice if delegate_choice != "—" else None,
                            status=status,
                            notes=fnotes or None,
                            created_by=user.name,
                            created_at=state_lib.now_iso(),
                        ))
                        st.success("Entry added.")
                        st.rerun()
                    else:
                        st.error("Description and a non-zero amount are required.")

        st.markdown("### Entries")
        filt = st.columns(2)
        kind_filter = filt[0].selectbox("Filter by type", ["All"] + state_lib.FINANCE_KINDS, key="fin_kind_filter")
        status_filter = filt[1].selectbox("Filter by status", ["All"] + state_lib.FINANCE_STATUSES, key="fin_status_filter")
        entries = state_lib.list_finances(
            kind=None if kind_filter == "All" else kind_filter,
            status=None if status_filter == "All" else status_filter,
        )
        if not entries:
            st.caption("No finance entries yet.")
        for f in entries:
            sign = "-" if f["kind"] == "expense" else "+" if f["kind"] in ("income", "due") else ""
            tagline = f"{f['kind']} · {f.get('category', 'other')} · {f.get('status', 'outstanding')} · {f.get('date', '')}"
            if f.get("delegate_name"):
                tagline += f" · {f['delegate_name']}"
            if f.get("conference_id") and f["conference_id"] in conf_names:
                tagline += f" · {conf_names[f['conference_id']]}"
            row = st.columns([5, 1.4, 1.1, 0.9])
            with row[0]:
                st.markdown(
                    f"""
<div class='doc-row'>
  <div>
    <div class='doc-row-title'>{f['description']}</div>
    <div class='doc-row-meta subtle'>{tagline}</div>
  </div>
  <div style='font-family:Inter Tight, sans-serif; font-weight:600; color:var(--text);'>{sign}${f['amount_cad']:,.2f}</div>
</div>
""",
                    unsafe_allow_html=True,
                )
            with row[1]:
                if f.get("status") != "paid" and f["kind"] in ("due", "expense", "income"):
                    if st.button("Mark paid", key=f"finpaid_{f['id']}", use_container_width=True):
                        state_lib.update_finance_entry(f["id"], status="paid")
                        st.rerun()
            with row[2]:
                if f.get("status") != "reconciled":
                    if st.button("Reconcile", key=f"finrec_{f['id']}", use_container_width=True):
                        state_lib.update_finance_entry(f["id"], status="reconciled")
                        st.rerun()
            with row[3]:
                if st.button("Delete", key=f"findel_{f['id']}", use_container_width=True):
                    state_lib.remove_finance_entry(f["id"])
                    st.rerun()

        # ---- CSV export ----
        all_entries = state_lib.list_finances()
        if all_entries:
            df_exp = pd.DataFrame(all_entries)
            if "conference_id" in df_exp.columns:
                df_exp.insert(0, "conference", df_exp["conference_id"].map(conf_names))
            st.download_button(
                "⬇ Export all entries (CSV)",
                data=df_exp.to_csv(index=False),
                file_name="qmun_finances.csv",
                mime="text/csv",
            )

brand_footer()
