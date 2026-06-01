"""Team state: weekly topics, conferences, assignments, roster, feedback.

Persisted through `lib.store`, which is local SQLite in dev and Supabase once
configured. Director admin reads/writes this. The whole state is one JSON blob;
all the helpers below load it, mutate, and save it back via the `edit()` cm.
"""
from __future__ import annotations

import uuid
from contextlib import contextmanager
from dataclasses import asdict, dataclass, field
from datetime import datetime

from lib import store


@dataclass
class WeeklyTopic:
    day: str           # "monday" | "thursday"
    topic: str
    committee: str
    set_at: str | None = None


@dataclass
class Conference:
    id: str
    name: str
    location: str
    start_date: str          # ISO
    end_date: str
    registration_deadline: str | None = None
    fees_per_delegate_usd: float | None = None
    notes: str | None = None


@dataclass
class Assignment:
    id: str
    conference_id: str
    delegate_name: str
    committee: str
    country_or_character: str
    status: str = "assigned"   # assigned | in_progress | submitted | done
    notes: str | None = None


@dataclass
class Delegate:
    """Roster entry. director_notes is the shared, director-only narrative
    that survives across feedback events (the "common feedback" space).
    """
    id: str
    name: str
    year: int                          # academic year 1-5
    status: str = "rookie"             # rookie | veteran
    joined_year: str | None = None     # e.g. "2025-2026"
    slack_id: str | None = None
    email: str | None = None
    director_notes: str = ""           # collaborative director-only narrative
    director_notes_updated_at: str | None = None
    director_notes_updated_by: str | None = None


@dataclass
class Social:
    """A team social event (lineskip night, formal, dinner, etc).

    attachments is a list of dicts: {filename, stored_path, mime_type,
    size_bytes, uploaded_by, uploaded_at}. Stored on disk under
    data/uploads/socials/{id}/ (gitignored).
    """
    id: str
    date: str                          # ISO date
    type: str                          # lineskip | formal | dinner | other
    location: str | None = None
    notes: str | None = None
    attachments: list[dict] = field(default_factory=list)
    created_by: str | None = None
    created_at: str | None = None


@dataclass
class Delegation:
    """An other-school MUN delegation we scout against."""
    id: str
    school: str
    strength_level: str = "unknown"    # rising | competitive | strong | dominant | unknown
    conferences_seen_at: list[str] = field(default_factory=list)
    notable_delegates: list[str] = field(default_factory=list)
    tactical_notes: str = ""
    awards_tendency: str = ""
    last_updated_at: str | None = None
    last_updated_by: str | None = None


@dataclass
class Feedback:
    """A single feedback event. Director-only by default.

    visibility: "director_only" hides from delegate; "shared_with_delegate"
    surfaces it on a future delegate-facing page (not yet built).
    """
    id: str
    delegate_name: str
    source: str                        # conference | mock | training | other
    notes: str
    tags: list[str] = field(default_factory=list)
    conference_id: str | None = None
    mock_date: str | None = None
    assigned_to: str | None = None     # director name/slack to action this
    status: str = "open"               # open | in_progress | addressed
    visibility: str = "director_only"  # director_only | shared_with_delegate
    created_by: str | None = None
    created_at: str | None = None


def _default_state() -> dict:
    return {
        "team_year": "2026-2027",
        "weekly_topics": {"monday": None, "thursday": None},
        "conferences": [],
        "assignments": [],
        "roster": [],
        "feedback": [],
        "socials": [],
        "delegations": [],
        "announcement": None,
        "team_insights_cache": None,   # {generated_at, week_start, payload}
        "settings": {
            "budget_warn_usd": 35.0,
            "budget_cap_usd": 40.0,
            "delegate_chat_turns_per_week": 30,
            "delegate_briefs_per_week": 10,
            "delegate_crisis_interactions_per_week": 5,
        },
    }


def set_announcement(text: str | None) -> None:
    from datetime import datetime
    with edit() as s:
        s["announcement"] = (
            {"text": text, "set_at": datetime.utcnow().isoformat()}
            if text and text.strip()
            else None
        )


def assignments_for_delegate(delegate_name: str) -> list[dict]:
    """Loose name match: case-insensitive, ignoring extra whitespace."""
    if not delegate_name:
        return []
    target = delegate_name.strip().lower()
    out = []
    s = load()
    confs_by_id = {c["id"]: c for c in s.get("conferences", [])}
    for a in s.get("assignments", []):
        if a["delegate_name"].strip().lower() == target:
            a_with_conf = dict(a)
            a_with_conf["conference"] = confs_by_id.get(a["conference_id"])
            out.append(a_with_conf)
    return out


def load() -> dict:
    state = store.load_state()
    if state is None:
        state = _default_state()
        store.save_state(state)
    return state


def save(state: dict) -> None:
    store.save_state(state)


@contextmanager
def edit():
    state = load()
    yield state
    save(state)


# ----- helpers -----

def set_weekly_topic(day: str, topic: str, committee: str) -> None:
    from datetime import datetime
    with edit() as s:
        s["weekly_topics"][day] = {
            "topic": topic,
            "committee": committee,
            "set_at": datetime.utcnow().isoformat(),
        }


def add_conference(c: Conference) -> None:
    with edit() as s:
        s["conferences"].append(asdict(c))


def add_assignment(a: Assignment) -> None:
    with edit() as s:
        s["assignments"].append(asdict(a))


def remove_assignment(assignment_id: str) -> None:
    with edit() as s:
        s["assignments"] = [a for a in s["assignments"] if a["id"] != assignment_id]


def assignments_for_conference(conference_id: str) -> list[dict]:
    return [a for a in load().get("assignments", []) if a["conference_id"] == conference_id]


# ----- roster -----

def _normalize_state(s: dict) -> dict:
    """Backfill any missing fields a defaulted state would have. Old state.json
    files predate the roster/feedback schema."""
    s.setdefault("roster", [])
    s.setdefault("feedback", [])
    s.setdefault("socials", [])
    s.setdefault("delegations", [])
    s.setdefault("team_insights_cache", None)
    return s


def add_delegate(d: Delegate) -> None:
    with edit() as s:
        _normalize_state(s)
        s["roster"].append(asdict(d))


def update_delegate(delegate_id: str, **fields) -> None:
    with edit() as s:
        _normalize_state(s)
        for entry in s["roster"]:
            if entry["id"] == delegate_id:
                entry.update({k: v for k, v in fields.items() if v is not None})
                return


def remove_delegate(delegate_id: str) -> None:
    with edit() as s:
        _normalize_state(s)
        s["roster"] = [d for d in s["roster"] if d["id"] != delegate_id]


def update_director_notes(delegate_id: str, notes: str, by: str | None = None) -> None:
    with edit() as s:
        _normalize_state(s)
        for entry in s["roster"]:
            if entry["id"] == delegate_id:
                entry["director_notes"] = notes
                entry["director_notes_updated_at"] = datetime.utcnow().isoformat()
                entry["director_notes_updated_by"] = by
                return


def roster_lookup(name: str) -> dict | None:
    """Loose name match: case-insensitive, ignoring extra whitespace."""
    if not name:
        return None
    target = name.strip().lower()
    for entry in load().get("roster", []):
        if entry["name"].strip().lower() == target:
            return entry
    return None


def list_roster() -> list[dict]:
    return list(load().get("roster", []))


# ----- feedback -----

def add_feedback(f: Feedback) -> None:
    with edit() as s:
        _normalize_state(s)
        s["feedback"].append(asdict(f))


def update_feedback(feedback_id: str, **fields) -> None:
    with edit() as s:
        _normalize_state(s)
        for entry in s["feedback"]:
            if entry["id"] == feedback_id:
                entry.update({k: v for k, v in fields.items() if v is not None})
                return


def remove_feedback(feedback_id: str) -> None:
    with edit() as s:
        _normalize_state(s)
        s["feedback"] = [f for f in s["feedback"] if f["id"] != feedback_id]


def feedback_for_delegate(name: str) -> list[dict]:
    if not name:
        return []
    target = name.strip().lower()
    return [
        f for f in load().get("feedback", [])
        if f["delegate_name"].strip().lower() == target
    ]


def list_feedback(*, status: str | None = None) -> list[dict]:
    rows = list(load().get("feedback", []))
    if status:
        rows = [f for f in rows if f.get("status") == status]
    return rows


# ----- socials -----

def add_social(s: Social) -> None:
    with edit() as state:
        _normalize_state(state)
        state["socials"].append(asdict(s))


def update_social(social_id: str, **fields) -> None:
    with edit() as state:
        _normalize_state(state)
        for entry in state["socials"]:
            if entry["id"] == social_id:
                entry.update({k: v for k, v in fields.items() if v is not None})
                return


def remove_social(social_id: str) -> None:
    removed_attachments: list[dict] = []
    with edit() as state:
        _normalize_state(state)
        for entry in state["socials"]:
            if entry["id"] == social_id:
                removed_attachments = list(entry.get("attachments") or [])
                break
        state["socials"] = [s for s in state["socials"] if s["id"] != social_id]
    # also nuke any uploaded files for this social
    for att in removed_attachments:
        store.delete_upload(_attachment_storage_key(att))


def list_socials() -> list[dict]:
    """All socials, sorted by date ascending."""
    rows = list(load().get("socials", []))
    rows.sort(key=lambda s: s.get("date") or "")
    return rows


def upcoming_socials(limit: int = 3) -> list[dict]:
    """Next N socials with date >= today."""
    today = datetime.utcnow().date().isoformat()
    rows = [s for s in list_socials() if (s.get("date") or "") >= today]
    return rows[:limit]


def _safe_filename(name: str) -> str:
    """Strip path separators and unsafe chars from a user-supplied filename."""
    name = name.replace("\\", "/").rsplit("/", 1)[-1]
    return "".join(c for c in name if c.isalnum() or c in ("-", "_", ".", " ")).strip() or "file"


def _attachment_storage_key(att: dict) -> str:
    """Stable deletion handle for an attachment.

    New attachments carry an explicit `storage_key`. Legacy attachments (saved
    before the store layer) only have a local `stored_path`; derive a relative
    key from it so local deletion still works.
    """
    if att.get("storage_key"):
        return att["storage_key"]
    stored = att.get("stored_path", "")
    marker = "uploads/"
    idx = stored.replace("\\", "/").find(marker)
    return stored.replace("\\", "/")[idx + len(marker):] if idx != -1 else ""


def add_social_attachment(
    social_id: str,
    *,
    filename: str,
    data: bytes,
    mime_type: str | None,
    uploaded_by: str | None = None,
) -> dict:
    """Store a file via the store layer and append it to the social's attachments."""
    safe = _safe_filename(filename)

    # De-dupe against this social's existing attachment names (no filesystem
    # probing, so it works the same in local and Supabase modes).
    existing = set()
    s = load()
    for entry in s.get("socials", []):
        if entry["id"] == social_id:
            existing = {a.get("filename") for a in (entry.get("attachments") or [])}
            break
    name = safe
    if name in existing:
        stem, _, ext = safe.rpartition(".")
        base, suffix = (stem, "." + ext) if stem else (safe, "")
        n = 1
        while name in existing:
            name = f"{base}_{n}{suffix}"
            n += 1

    rel_key = f"socials/{social_id}/{name}"
    stored = store.save_upload(rel_key, data, mime_type)

    attachment = {
        "filename": name,
        "stored_path": stored["stored_path"],
        "storage_key": stored["storage_key"],
        "mime_type": mime_type or "application/octet-stream",
        "size_bytes": len(data),
        "uploaded_by": uploaded_by,
        "uploaded_at": datetime.utcnow().isoformat(),
    }

    with edit() as state:
        _normalize_state(state)
        for entry in state["socials"]:
            if entry["id"] == social_id:
                entry.setdefault("attachments", []).append(attachment)
                return attachment

    # social not found, clean up the orphan file
    store.delete_upload(rel_key)
    raise ValueError(f"Social {social_id} not found")


def remove_social_attachment(social_id: str, filename: str) -> None:
    """Delete an attachment file and remove it from the social's attachments list."""
    with edit() as state:
        _normalize_state(state)
        for entry in state["socials"]:
            if entry["id"] == social_id:
                kept = []
                for att in entry.get("attachments") or []:
                    if att["filename"] == filename:
                        store.delete_upload(_attachment_storage_key(att))
                    else:
                        kept.append(att)
                entry["attachments"] = kept
                return


# ----- delegations (other-school scouting) -----

def add_delegation(d: Delegation) -> None:
    with edit() as state:
        _normalize_state(state)
        state["delegations"].append(asdict(d))


def update_delegation(delegation_id: str, **fields) -> None:
    with edit() as state:
        _normalize_state(state)
        for entry in state["delegations"]:
            if entry["id"] == delegation_id:
                entry.update({k: v for k, v in fields.items() if v is not None})
                entry["last_updated_at"] = datetime.utcnow().isoformat()
                return


def remove_delegation(delegation_id: str) -> None:
    with edit() as state:
        _normalize_state(state)
        state["delegations"] = [d for d in state["delegations"] if d["id"] != delegation_id]


def list_delegations() -> list[dict]:
    rows = list(load().get("delegations", []))
    rows.sort(key=lambda d: d.get("school", "").lower())
    return rows


def new_id() -> str:
    return str(uuid.uuid4())[:8]


def now_iso() -> str:
    return datetime.utcnow().isoformat()
