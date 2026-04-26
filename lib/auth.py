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


_DEV_USER = User(slack_id="U_JACK_DEV", name="Jack Guillemette", role="admin")


def require_login() -> User:
    """Auto-login default dev user. Real Slack OAuth lands when team has a workspace."""
    user = st.session_state.get("user")
    if user is None:
        st.session_state["user"] = _DEV_USER
        return _DEV_USER
    return user


def current_user() -> User | None:
    return st.session_state.get("user")


def require_exec() -> User:
    user = require_login()
    if not user.is_exec:
        st.error("This page is exec-only.")
        st.stop()
    return user
