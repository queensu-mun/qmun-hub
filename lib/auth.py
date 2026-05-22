"""Slack OAuth + role-based access.

Three modes, tried in order:
- **Slack OAuth** (`[slack].client_id` + `client_secret` configured): full OAuth
  v2 user-token flow. Production path once the QMUN Slack app is registered.
- **Pilot gate** (`[app].pilot_passcode` set, no Slack OAuth): shared passcode +
  name form. Roles resolved by name against `pilot_admin_names` / `pilot_exec_names`.
  Used for the exec pilot before Slack OAuth is wired up.
- **Dev fallback** (neither configured): auto-login as `_DEV_USER`. Local dev only.
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


# ----- Pilot gate -----

def _is_pilot_configured() -> bool:
    try:
        return bool(st.secrets["app"].get("pilot_passcode"))
    except (KeyError, FileNotFoundError):
        return False


def _resolve_pilot_role(name: str) -> Role:
    try:
        admins = list(st.secrets["app"].get("pilot_admin_names", []))
        execs = list(st.secrets["app"].get("pilot_exec_names", []))
    except (KeyError, FileNotFoundError):
        admins, execs = [], []
    n = name.strip().lower()
    if any(a.strip().lower() == n for a in admins):
        return "admin"
    if any(e.strip().lower() == n for e in execs):
        return "exec"
    return "delegate"


def _render_pilot_gate() -> "User | None":
    """Render the passcode sign-in form. Returns User on success, None if waiting."""
    try:
        correct = st.secrets["app"].get("pilot_passcode", "")
    except (KeyError, FileNotFoundError):
        correct = ""

    _, col, _ = st.columns([1, 2, 1])
    with col:
        st.markdown(
            """
<div style='text-align:center; padding:3.5rem 0 1.75rem;'>
  <div style='font-family:"Fraunces",serif; font-size:1.9rem; color:#0d1b3e;
              font-weight:700; letter-spacing:-0.02em;'>Queen's MUN</div>
  <div style='color:#777; font-size:0.88rem; margin-top:0.35rem; letter-spacing:0.01em;'>
    Pilot workspace
  </div>
</div>
""",
            unsafe_allow_html=True,
        )

        with st.form("pilot_gate"):
            name = st.text_input("Your name", placeholder="e.g. Jane Doe")
            code = st.text_input("Pilot code", type="password", placeholder="Ask Jack")
            submitted = st.form_submit_button("Sign in", use_container_width=True, type="primary")

        if st.session_state.get("_pilot_error"):
            st.error(st.session_state["_pilot_error"])

    if submitted:
        name = name.strip()
        if not name:
            st.session_state["_pilot_error"] = "Enter your name."
            st.rerun()
        elif code.strip() != correct:
            st.session_state["_pilot_error"] = "Wrong code. Check with Jack."
            st.rerun()
        else:
            st.session_state.pop("_pilot_error", None)
            role = _resolve_pilot_role(name)
            user = User(
                slack_id="PILOT_" + name.replace(" ", "_"),
                name=name,
                role=role,
            )
            st.session_state["user"] = user
            return user

    return None


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
    """Return the current user. Mode depends on secrets configuration.

    Priority:
    1. Already in session: return immediately.
    2. Slack OAuth configured: run OAuth flow.
    3. Pilot passcode configured: show passcode gate.
    4. Neither: auto-login as dev user (local dev only).
    """
    user = st.session_state.get("user")
    if user is not None:
        return user

    if _is_oauth_configured():
        callback_user = _handle_oauth_callback()
        if callback_user is not None:
            return callback_user
        _render_signin_panel()
        st.stop()

    if _is_pilot_configured():
        pilot_user = _render_pilot_gate()
        if pilot_user is None:
            st.stop()
        return pilot_user

    st.session_state["user"] = _DEV_USER
    return _DEV_USER


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
    st.session_state.pop("_pilot_error", None)
