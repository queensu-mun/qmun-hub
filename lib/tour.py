"""New-delegate walkthrough: a guided tour that actually navigates the app.

A modal (st.dialog) can't survive st.switch_page, so the tour is an inline
banner pinned to the top of every page. `render_banner(user)` is called from
`top_nav` (so it shows on whatever page you land on); "Next"/"Back" advance the
step AND navigate to that step's page, so you read each step while looking at
the real page it describes.

Completion is persisted per-user (name-keyed, since pilot mode has no per-user
store) via `lib.state`, so it auto-opens only once. The "Take a quick tour"
button on the home page replays it anytime.
"""
from __future__ import annotations

import streamlit as st

from lib import icons
from lib import state as state_lib


def steps_for(user) -> list[dict]:
    """Tour content + the page each step lives on. Director step is exec/admin only."""
    steps = [
        {
            "page": "app.py",
            "icon": icons.globe,
            "title": "Welcome to QMUN Hub",
            "body": "This is the team's workspace: institutional knowledge, prep "
                    "tools, and training in one place. This quick tour walks you "
                    "through each part. You can replay it anytime from this home page.",
        },
        {
            "page": "pages/2_Brief.py",
            "icon": icons.brief,
            "title": "Generate a brief",
            "body": "This is the brief generator. Pick a country, committee, and "
                    "topic and it builds a structured prep brief on the team's "
                    "three-question framework. Use it for mocks or real conferences.",
        },
        {
            "page": "pages/1_Archive.py",
            "icon": icons.archive,
            "title": "Search the archive",
            "body": "Past papers, training guides, background guides, and alumni "
                    "interviews, all searchable. Every document opens in a clean "
                    "inline reader, so you never have to download to read.",
        },
        {
            "page": "pages/3_Chatbot.py",
            "icon": icons.chat,
            "title": "Ask the mentor",
            "body": "A chatbot that gives Queen's-specific advice, not generic UN "
                    "platitudes. Ask what a first-timer should know, how to handle a "
                    "bloc, or anything you'd ask a senior delegate.",
        },
        {
            "page": "pages/4_Training.py",
            "icon": icons.book,
            "title": "Training guides",
            "body": "Short, practical guides: unmod tactics, resolution writing, "
                    "crisis directives, formal-debate speaking, and more. Read these "
                    "before your first conference.",
        },
        {
            "page": "pages/6_Alumni_Interview.py",
            "icon": icons.users,
            "title": "Leave something behind",
            "body": "When you've got experience worth keeping, this short form turns "
                    "it into searchable knowledge for future delegates. Even one "
                    "answer helps.",
        },
    ]
    if getattr(user, "is_exec", False):
        steps.append({
            "page": "pages/5_Director.py",
            "icon": icons.target,
            "title": "Director tools",
            "body": "Run the team: set weekly mock topics, manage the roster and "
                    "private delegate feedback, generate insight reports, track "
                    "scouting, and (admins only) handle team finances.",
        })
    return steps


def maybe_autostart(user) -> None:
    """Open the tour once for a delegate who hasn't completed it.

    Marks completion immediately so it never auto-fires again, even if the user
    refreshes or skips mid-tour. The replay button ignores this.
    """
    if st.session_state.get("tour_active") or st.session_state.get("_tour_autostarted"):
        return
    st.session_state["_tour_autostarted"] = True
    if not state_lib.has_completed_tour(getattr(user, "name", "")):
        st.session_state["tour_active"] = True
        st.session_state["tour_step"] = 0
        state_lib.mark_tour_completed(getattr(user, "name", ""))


def start() -> None:
    """Replay the tour from the beginning (used by the 'Take a quick tour' button)."""
    st.session_state["tour_active"] = True
    st.session_state["tour_step"] = 0


def _end() -> None:
    st.session_state["tour_active"] = False


def render_banner(user) -> None:
    """Inline tour banner pinned to the top of the page. Call from top_nav."""
    if not st.session_state.get("tour_active"):
        return
    steps = steps_for(user)
    i = max(0, min(st.session_state.get("tour_step", 0), len(steps) - 1))
    step = steps[i]
    last = i == len(steps) - 1

    st.markdown(
        f"""
<div class='tour-banner'>
  <div class='tour-banner-head'>
    <span class='tour-banner-icon'>{step['icon'](size=20)}</span>
    <span class='tour-banner-title'>{step['title']}</span>
    <span class='tour-banner-step'>Step {i + 1} of {len(steps)}</span>
  </div>
  <div class='tour-banner-body'>{step['body']}</div>
  <div class='tour-banner-bar'><div class='tour-banner-fill' style='width:{int((i + 1) / len(steps) * 100)}%;'></div></div>
</div>
""",
        unsafe_allow_html=True,
    )

    c1, c2, c3, _ = st.columns([1, 1, 1, 4])
    with c1:
        if st.button("Back", key="tour_back", use_container_width=True, disabled=(i == 0)):
            st.session_state["tour_step"] = i - 1
            st.switch_page(steps[i - 1]["page"])
    with c2:
        if st.button("Skip tour", key="tour_skip", use_container_width=True):
            _end()
            st.rerun()
    with c3:
        if st.button("Finish" if last else "Next", key="tour_next",
                     type="primary", use_container_width=True):
            if last:
                _end()
                st.rerun()
            else:
                st.session_state["tour_step"] = i + 1
                st.switch_page(steps[i + 1]["page"])
