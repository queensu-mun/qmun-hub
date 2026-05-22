"""Slack OAuth + role-based access.

Two modes:
- **Dev mode** (no `[slack].client_id` in secrets): auto-login as a hardcoded
  dev user so local development isn't gated on a real Slack workspace.
- **Production** (Slack app registered, client_id + client_secret in secrets):
  standard OAuth v2 user-token flow via `https://slack.com/oauth/v2/authorize`.

The User shape is identical in both modes; the `_resolve_role` mapping (admin /
exec / delegate) is driven by `[app].admin_slack_user_ids` and
`[app].exec_slack_user_ids` in secrets.
"""
from __future__ import annotations

import secrets as _pysecrets
from dataclasses import dataclass
from typing import Literal
from urllib.parse import urlencode

import httpx
import streamlit as st

Role = Literal["delegate", "exec", "admin"]

SLACK_AUTHORIZE_URL = "https://slack.com/oauth/v2/authorize"
SLACK_TOKEN_URL = "https://slack.com/api/oauth.v2.access"
SLACK_USERS_INFO_URL = "https://slack.com/api/users.info"

USER_SCOPES = "users:read,users.profile:read"


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


def _slack_secrets() -> dict:
    try:
        return dict(st.secrets["slack"])
    except (KeyError, FileNotFoundError):
        return {}


def _is_oauth_configured() -> bool:
    s = _slack_secrets()
    return bool(s.get("client_id")) and bool(s.get("client_secret"))


def _resolve_role(slack_id: str) -> Role:
    try:
        admins = list(st.secrets["app"].get("admin_slack_user_ids", []))
        execs = list(st.secrets["app"].get("exec_slack_user_ids", []))
    except (KeyError, FileNotFoundError):
        admins, execs = [], []
    if slack_id in admins:
        return "admin"
    if slack_id in execs:
        return "exec"
    return "delegate"


_DEV_USER = User(slack_id="U_JACK_DEV", name="Jack Guillemette", role="admin")


# ----- OAuth flow -----

def _build_authorize_url(state: str) -> str:
    s = _slack_secrets()
    params = {
        "client_id": s["client_id"],
        "user_scope": USER_SCOPES,
        "redirect_uri": s["redirect_uri"],
        "state": state,
    }
    return f"{SLACK_AUTHORIZE_URL}?{urlencode(params)}"


def _exchange_code(code: str) -> dict:
    s = _slack_secrets()
    resp = httpx.post(
        SLACK_TOKEN_URL,
        data={
            "client_id": s["client_id"],
            "client_secret": s["client_secret"],
            "code": code,
            "redirect_uri": s["redirect_uri"],
        },
        timeout=10.0,
    )
    resp.raise_for_status()
    payload = resp.json()
    if not payload.get("ok"):
        raise RuntimeError(f"Slack token exchange failed: {payload.get('error', 'unknown')}")
    return payload


def _fetch_user_identity(user_token: str, user_id: str) -> dict:
    resp = httpx.get(
        SLACK_USERS_INFO_URL,
        params={"user": user_id},
        headers={"Authorization": f"Bearer {user_token}"},
        timeout=10.0,
    )
    resp.raise_for_status()
    payload = resp.json()
    if not payload.get("ok"):
        raise RuntimeError(f"Slack users.info failed: {payload.get('error', 'unknown')}")
    return payload["user"]


def _user_from_identity(identity: dict) -> User:
    slack_id = identity["id"]
    profile = identity.get("profile", {}) or {}
    name = profile.get("real_name") or profile.get("display_name") or identity.get("name") or slack_id
    return User(slack_id=slack_id, name=name, role=_resolve_role(slack_id))


def _render_signin_panel() -> None:
    state = _pysecrets.token_urlsafe(24)
    st.session_state["_oauth_state"] = state
    url = _build_authorize_url(state)
    st.markdown(
        f"""
<div style='max-width: 480px; margin: 6rem auto; text-align: center; padding: 2.5rem 2rem;
            border: 1px solid rgba(0,0,0,0.08); border-radius: 14px; background: #fafafa;'>
  <div style='font-size: 1.4rem; font-weight: 600; margin-bottom: 0.5rem;'>Queen's MUN</div>
  <div style='color: #666; font-size: 0.95rem; margin-bottom: 2rem;'>Sign in to access the team workspace.</div>
  <a href='{url}' style='display: inline-block; padding: 0.7rem 1.4rem; background: #4A154B;
        color: #fff; border-radius: 8px; text-decoration: none; font-weight: 500;'>
    Sign in with Slack
  </a>
</div>
""",
        unsafe_allow_html=True,
    )


def _handle_oauth_callback() -> User | None:
    """If query params carry an OAuth code, exchange it. Returns the User or None."""
    qp = st.query_params
    code = qp.get("code")
    state = qp.get("state")
    if not code or not state:
        return None

    expected = st.session_state.get("_oauth_state")
    if expected and state != expected:
        st.error("OAuth state mismatch. Try signing in again.")
        st.query_params.clear()
        st.session_state.pop("_oauth_state", None)
        return None

    payload = _exchange_code(code)
    authed = payload.get("authed_user") or {}
    user_token = authed.get("access_token")
    user_id = authed.get("id")
    if not user_token or not user_id:
        raise RuntimeError("Slack response missing authed_user fields.")

    identity = _fetch_user_identity(user_token, user_id)
    user = _user_from_identity(identity)

    st.session_state["user"] = user
    st.session_state.pop("_oauth_state", None)
    st.query_params.clear()
    return user


# ----- Public API -----

def require_login() -> User:
    """Return the current user, prompting Slack OAuth if configured.

    Behavior:
    - If a User is already in session, return it.
    - If Slack OAuth isn't configured, auto-login as the dev user.
    - If Slack OAuth IS configured: handle the callback if we're returning
      from Slack, otherwise render the sign-in panel and stop the page.
    """
    user = st.session_state.get("user")
    if user is not None:
        return user

    if not _is_oauth_configured():
        st.session_state["user"] = _DEV_USER
        return _DEV_USER

    callback_user = _handle_oauth_callback()
    if callback_user is not None:
        return callback_user

    _render_signin_panel()
    st.stop()


def current_user() -> User | None:
    return st.session_state.get("user")


def require_exec() -> User:
    user = require_login()
    if not user.is_exec:
        st.error("This page is exec-only.")
        st.stop()
    return user


def sign_out() -> None:
    st.session_state.pop("user", None)
    st.session_state.pop("_oauth_state", None)
