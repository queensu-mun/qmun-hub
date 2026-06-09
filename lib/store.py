"""Storage backend abstraction: local files (dev) or Supabase (deployed).

Two modes, chosen by whether `[supabase]` secrets are configured:

- **Local mode** (no Supabase secrets): team state lives in `data/store.db`
  (SQLite), uploads under `data/uploads/`. This is the dev default and behaves
  like a normal single-machine app.
- **Supabase mode** (`[supabase].url` + `service_role_key` set): team state in a
  Postgres `team_state` JSONB row, usage/briefs in Postgres tables, uploads in a
  Supabase Storage bucket. Survives ephemeral-filesystem redeploys (Streamlit
  Cloud / Railway), which is the whole point.

Mirrors the graceful-degradation pattern in `lib/auth.py`: the app works in
local mode with zero config, and flips to the durable backend the moment the
keys are present. Nothing else in the codebase needs to know which mode is live.

State is a single JSON blob (one Postgres row / one SQLite row). Postgres makes
each whole-blob write atomic, so this is already safer than the old single-file
state.json under concurrent editors, though it is still last-writer-wins on the
whole blob. For a ~35-person team where writes are almost all director-only,
that is acceptable. Splitting into per-entity tables is a future step if needed.
"""
from __future__ import annotations

import json
import os
import sqlite3
from contextlib import contextmanager
from functools import lru_cache
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
LOCAL_DB = DATA_DIR / "store.db"
LOCAL_UPLOAD_ROOT = DATA_DIR / "uploads"
UPLOAD_BUCKET = "uploads"
STATE_SINGLETON_ID = "singleton"

_LOCAL_SCHEMA = """
CREATE TABLE IF NOT EXISTS team_state (
    id TEXT PRIMARY KEY,
    data TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS usage (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ts TEXT NOT NULL,
    user_slack_id TEXT NOT NULL,
    feature TEXT NOT NULL,
    model TEXT NOT NULL,
    input_tokens INTEGER NOT NULL,
    cached_input_tokens INTEGER NOT NULL,
    cache_write_tokens INTEGER NOT NULL,
    output_tokens INTEGER NOT NULL,
    cost_usd REAL NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_usage_user_ts ON usage(user_slack_id, ts);
CREATE INDEX IF NOT EXISTS idx_usage_ts ON usage(ts);
CREATE TABLE IF NOT EXISTS briefs (
    cache_key TEXT PRIMARY KEY,
    country TEXT NOT NULL,
    topic TEXT NOT NULL,
    committee TEXT NOT NULL,
    week_start TEXT NOT NULL,
    depth TEXT NOT NULL,
    markdown TEXT NOT NULL,
    cost_usd REAL NOT NULL,
    created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_briefs_created ON briefs(created_at);
CREATE TABLE IF NOT EXISTS chat_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_slack_id TEXT NOT NULL,
    mode TEXT NOT NULL,
    role TEXT NOT NULL,
    content TEXT NOT NULL,
    ts TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_chat_history_user_mode ON chat_history(user_slack_id, mode, id);
"""


# --------------------------------------------------------------------------
# Config + backend selection
# --------------------------------------------------------------------------

def _secret_section(name: str) -> dict:
    """Read a secrets section, working both inside Streamlit and in plain scripts."""
    try:
        import streamlit as st

        return dict(st.secrets[name])
    except Exception:
        pass
    # Fallback: read .streamlit/secrets.toml directly (e.g. CLI scripts).
    try:
        import toml

        path = Path(__file__).resolve().parent.parent / ".streamlit" / "secrets.toml"
        if path.exists():
            return dict(toml.loads(path.read_text()).get(name, {}))
    except Exception:
        pass
    return {}


@lru_cache(maxsize=1)
def backend() -> str:
    """'supabase' if configured, else 'local'. Cached per process.

    `QMUN_FORCE_LOCAL=1` forces local mode even when Supabase secrets are
    present. This lets us run/test the app against `data/store.db` without
    mutating live team state (the local secrets.toml carries [supabase], so
    every plain `streamlit run` would otherwise hit production).
    """
    if os.environ.get("QMUN_FORCE_LOCAL"):
        return "local"
    s = _secret_section("supabase")
    if s.get("url") and s.get("service_role_key"):
        return "supabase"
    return "local"


@lru_cache(maxsize=1)
def _client():
    """Lazily build and cache the Supabase client."""
    from supabase import create_client

    s = _secret_section("supabase")
    return create_client(s["url"], s["service_role_key"])


@contextmanager
def _local_conn():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(LOCAL_DB)
    conn.row_factory = sqlite3.Row
    try:
        conn.executescript(_LOCAL_SCHEMA)
        yield conn
        conn.commit()
    finally:
        conn.close()


# --------------------------------------------------------------------------
# Team state (singleton JSON blob)
# --------------------------------------------------------------------------

def load_state() -> dict | None:
    """Return the stored team-state dict, or None if nothing has been saved yet."""
    if backend() == "supabase":
        resp = (
            _client()
            .table("team_state")
            .select("data")
            .eq("id", STATE_SINGLETON_ID)
            .limit(1)
            .execute()
        )
        rows = resp.data or []
        return rows[0]["data"] if rows else None

    with _local_conn() as c:
        row = c.execute(
            "SELECT data FROM team_state WHERE id = ?", (STATE_SINGLETON_ID,)
        ).fetchone()
    return json.loads(row["data"]) if row else None


def save_state(data: dict) -> None:
    if backend() == "supabase":
        _client().table("team_state").upsert(
            {"id": STATE_SINGLETON_ID, "data": data}, on_conflict="id"
        ).execute()
        return

    with _local_conn() as c:
        c.execute(
            "INSERT OR REPLACE INTO team_state (id, data) VALUES (?, ?)",
            (STATE_SINGLETON_ID, json.dumps(data)),
        )


# --------------------------------------------------------------------------
# Generic small tables (usage, briefs)
# --------------------------------------------------------------------------

def insert_row(table: str, row: dict) -> None:
    if backend() == "supabase":
        _client().table(table).insert(row).execute()
        return
    cols = ", ".join(row.keys())
    placeholders = ", ".join("?" for _ in row)
    with _local_conn() as c:
        c.execute(
            f"INSERT INTO {table} ({cols}) VALUES ({placeholders})",
            tuple(row.values()),
        )


def upsert_row(table: str, row: dict, *, key: str) -> None:
    if backend() == "supabase":
        _client().table(table).upsert(row, on_conflict=key).execute()
        return
    cols = ", ".join(row.keys())
    placeholders = ", ".join("?" for _ in row)
    with _local_conn() as c:
        c.execute(
            f"INSERT OR REPLACE INTO {table} ({cols}) VALUES ({placeholders})",
            tuple(row.values()),
        )


def select_rows(
    table: str,
    *,
    where_eq: dict | None = None,
    since: tuple[str, str] | None = None,
    order_desc: str | None = None,
    limit: int | None = None,
) -> list[dict]:
    """Fetch rows as dicts. `since` = (column, iso_value) means column >= value.

    Aggregation (sums, group-by) is done in Python by callers: the data volume
    here is tiny (a team's worth of usage/brief rows), so this stays simple and
    backend-agnostic rather than pushing SQL/PostgREST aggregation differences.
    """
    if backend() == "supabase":
        q = _client().table(table).select("*")
        for col, val in (where_eq or {}).items():
            q = q.eq(col, val)
        if since:
            q = q.gte(since[0], since[1])
        if order_desc:
            q = q.order(order_desc, desc=True)
        if limit:
            q = q.limit(limit)
        return list(q.execute().data or [])

    clauses, params = [], []
    for col, val in (where_eq or {}).items():
        clauses.append(f"{col} = ?")
        params.append(val)
    if since:
        clauses.append(f"{since[0]} >= ?")
        params.append(since[1])
    sql = f"SELECT * FROM {table}"
    if clauses:
        sql += " WHERE " + " AND ".join(clauses)
    if order_desc:
        sql += f" ORDER BY {order_desc} DESC"
    if limit:
        sql += " LIMIT ?"
        params.append(limit)
    with _local_conn() as c:
        return [dict(r) for r in c.execute(sql, tuple(params)).fetchall()]


def delete_rows(table: str, *, where_eq: dict | None = None, id_in: list | None = None) -> None:
    """Delete rows matching equality filters and/or an explicit id list.

    Refuses to run with no filters at all: a bare DELETE on a whole table is
    never what callers here want.
    """
    if not where_eq and not id_in:
        return
    if backend() == "supabase":
        q = _client().table(table).delete()
        for col, val in (where_eq or {}).items():
            q = q.eq(col, val)
        if id_in:
            q = q.in_("id", id_in)
        q.execute()
        return
    clauses, params = [], []
    for col, val in (where_eq or {}).items():
        clauses.append(f"{col} = ?")
        params.append(val)
    if id_in:
        clauses.append(f"id IN ({', '.join('?' for _ in id_in)})")
        params.extend(id_in)
    with _local_conn() as c:
        c.execute(f"DELETE FROM {table} WHERE " + " AND ".join(clauses), tuple(params))


# --------------------------------------------------------------------------
# Uploads (binary objects)
# --------------------------------------------------------------------------

def save_upload(rel_key: str, data: bytes, content_type: str | None) -> dict:
    """Store a file under `rel_key`. Returns {stored_path, storage_key}.

    `stored_path` is what display code (st.image) consumes: a local filesystem
    path in local mode, a public URL in Supabase mode. `storage_key` is the
    stable handle used for deletion.
    """
    content_type = content_type or "application/octet-stream"
    if backend() == "supabase":
        client = _client()
        client.storage.from_(UPLOAD_BUCKET).upload(
            rel_key,
            data,
            {"content-type": content_type, "upsert": "true"},
        )
        url = client.storage.from_(UPLOAD_BUCKET).get_public_url(rel_key)
        return {"stored_path": url, "storage_key": rel_key}

    target = LOCAL_UPLOAD_ROOT / rel_key
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(data)
    return {"stored_path": str(target), "storage_key": rel_key}


def delete_upload(storage_key: str) -> None:
    if not storage_key:
        return
    if backend() == "supabase":
        try:
            _client().storage.from_(UPLOAD_BUCKET).remove([storage_key])
        except Exception:
            pass
        return
    # Local: storage_key is a path relative to the upload root.
    target = LOCAL_UPLOAD_ROOT / storage_key
    target.unlink(missing_ok=True)
