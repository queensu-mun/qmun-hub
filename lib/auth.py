"""Slack OAuth + role-based access.

Stub for May scaffolding. Real Slack OAuth flow lands in Phase 1.4.
For local dev, set DEV_USER in secrets.toml or use the dev sign-in form.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import streamlit as st

Role = Literal["delegate", "exec", "admin"]


@dataclass
class User:
    slack_id: str
    name: str
    role: Role

    @property
    def is_exec(self) -> bool:
        return self.role in ("exec", "admin")

    @property
    def is_admin(self) -> bool:
        return self.role == "admin"


def _resolve_role(slack_id: str) -> Role:
    try:
        admins = st.secrets["app"].get("admin_slack_user_ids", [])
        execs = st.secrets["app"].get("exec_slack_user_ids", [])
    except (KeyError, FileNotFoundError):
        admins, execs = [], []
    if slack_id in admins:
        return "admin"
    if slack_id in execs:
        return "exec"
    return "delegate"


def _dev_login_form() -> User | None:
    st.markdown("# 🌐 QMUN Hub")
    st.caption("Dev sign-in (Slack OAuth wired up in Phase 1.4)")
    with st.form("dev_login"):
        name = st.text_input("Display name", value="Jack Guillemette")
        slack_id = st.text_input("Slack user ID", value="U_JACK_ID")
        submitted = st.form_submit_button("Sign in", type="primary")
    if submitted and name and slack_id:
        user = User(slack_id=slack_id, name=name, role=_resolve_role(slack_id))
        st.session_state["user"] = user
        st.rerun()
    return None


def require_login() -> User:
    user = st.session_state.get("user")
    if user is None:
        _dev_login_form()
        st.stop()
    return user


def current_user() -> User | None:
    return st.session_state.get("user")


def require_exec() -> User:
    user = require_login()
    if not user.is_exec:
        st.error("This page is exec-only.")
        st.stop()
    return user
