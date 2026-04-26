from __future__ import annotations

from datetime import date, datetime

import streamlit as st

from lib import state as state_lib
from lib.auth import require_login
from lib.ui import brand_footer, inject_global_css, page_header, tag, top_nav

st.set_page_config(page_title="Socials · Queen's MUN", page_icon="🌐", layout="wide", initial_sidebar_state="collapsed")
inject_global_css()
user = require_login()
top_nav(user)

page_header("Socials", "Lineskip nights, formals, team dinners", "Updated by the directors. Show up.")


def _human_size(n: int) -> str:
    for unit in ("B", "KB", "MB"):
        if n < 1024:
            return f"{n:.0f} {unit}"
        n /= 1024
    return f"{n:.1f} GB"


def _days_label(iso: str) -> str:
    try:
        d = datetime.fromisoformat(iso).date()
        delta = (d - date.today()).days
        if delta == 0:
            return "today"
        if delta == 1:
            return "tomorrow"
        if delta > 1:
            return f"in {delta} days"
        if delta == -1:
            return "yesterday"
        return f"{abs(delta)} days ago"
    except Exception:
        return ""


socials = state_lib.list_socials()
today = date.today().isoformat()
upcoming = [s for s in socials if (s.get("date") or "") >= today]
past = [s for s in socials if (s.get("date") or "") < today]


def _render(s: dict) -> None:
    with st.container(border=True):
        head_cols = st.columns([3, 1])
        badges = tag(s.get("type", "other"))
        attachments = s.get("attachments") or []
        head_cols[0].markdown(f"**{s.get('date')}**", unsafe_allow_html=True)
        head_cols[0].markdown(badges, unsafe_allow_html=True)
        if s.get("location"):
            head_cols[0].caption(s["location"])
        if s.get("notes"):
            head_cols[0].markdown(s["notes"])
        head_cols[1].markdown(
            f"<div class='subtle' style='text-align:right;'>{_days_label(s.get('date',''))}</div>",
            unsafe_allow_html=True,
        )

        if attachments:
            for att in attachments:
                mime = att.get("mime_type", "")
                if mime.startswith("image/"):
                    try:
                        st.image(att["stored_path"], width=420)
                    except Exception:
                        pass
                else:
                    try:
                        file_bytes = open(att["stored_path"], "rb").read()
                        st.download_button(
                            f"Download {att['filename']}  ({_human_size(att.get('size_bytes', 0))})",
                            data=file_bytes,
                            file_name=att["filename"],
                            mime=mime,
                            key=f"pub_dl_{s['id']}_{att['filename']}",
                        )
                    except FileNotFoundError:
                        st.caption(f"~~{att['filename']}~~ (file missing)")


st.markdown("### Upcoming")
if upcoming:
    for s in upcoming:
        _render(s)
else:
    st.caption("Nothing scheduled. Check back, or ping the directors.")

if past:
    st.markdown("### Past")
    for s in past[::-1][:10]:
        _render(s)

brand_footer()
