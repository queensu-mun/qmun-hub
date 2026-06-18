"""Drive -> archive sync orchestration.

`lib/drive.py` is the pure Drive I/O layer (list, download, extract). `lib/index.py`
is the archive (chunk, embed, upsert). This module is the bridge between them: it
pulls every supported doc from the configured team folder and indexes it into the
searchable archive, honouring whichever backend is active (local SQLite or Supabase),
exactly like `lib/ingest.ingest_folder` does for local files.

Two callers:
- `scripts/sync_drive.py` (CLI)
- the Director -> Curation "Sync from Drive" button

Stable identity: each Drive file becomes a doc with `doc_id = "drive_<fileId>"`, so
re-syncing re-indexes a changed file in place rather than duplicating it. Renames and
edits in Drive are picked up; the Drive file id is the durable key.

Incremental: the last successful sync time is stored in team settings
(`drive_last_sync`). A normal sync only fetches files changed since then; pass
`full=True` to re-pull everything.

Configuration lives in `[google]` in `.streamlit/secrets.toml`
(`service_account_path` + `shared_drive_folder_id`); see `lib/drive.py`.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Callable

from lib import drive, state
from lib.index import Doc, index_stats, upsert_doc

# Setting key for the incremental-sync watermark.
_LAST_SYNC_KEY = "drive_last_sync"

# Drive mime -> archive doc_type default. Refined per-file by `doc_type_for`.
_MIME_DEFAULT = {
    drive.GOOGLE_DOC_MIME: "misc",
    drive.PDF_MIME: "background_guide",
    drive.DOCX_MIME: "position_paper",
}

# Filename keyword -> doc_type. First match wins; order matters (most specific first).
_NAME_RULES: list[tuple[tuple[str, ...], str]] = [
    (("working paper", "draft resolution", "wp -", "wp_", " wp ", "resolution"), "position_paper"),
    (("background", "study guide", "guide", "briefing", "primer"), "background_guide"),
    (("position paper", "policy"), "position_paper"),
    (("agenda", "minutes", "meeting", "memo", "announcement"), "director_note"),
    (("training", "how to", "handbook", "art of mun", "tactics"), "training"),
]


def is_configured() -> bool:
    """True when [google] secrets are present so a sync can actually run."""
    return drive._is_configured()


def doc_type_for(name: str, mime_type: str) -> str:
    """Best-effort archive doc_type from a Drive file's name + mime."""
    low = name.lower()
    for keywords, dt in _NAME_RULES:
        if any(k in low for k in keywords):
            return dt
    return _MIME_DEFAULT.get(mime_type, "misc")


def _drive_url(file_id: str, mime_type: str) -> str:
    if mime_type == drive.GOOGLE_DOC_MIME:
        return f"https://docs.google.com/document/d/{file_id}/edit"
    return f"https://drive.google.com/file/d/{file_id}/view"


def last_sync() -> datetime | None:
    raw = state.get_setting(_LAST_SYNC_KEY)
    if not raw:
        return None
    try:
        return datetime.fromisoformat(raw)
    except (ValueError, TypeError):
        return None


def sync_drive(
    folder_id: str | None = None,
    *,
    full: bool = False,
    default_doc_type: str | None = None,
    log: Callable[[str], None] | None = None,
) -> dict:
    """Pull the configured team folder into the archive.

    full=False (default): only fetch files modified since the last successful sync.
    full=True: re-pull everything in the folder.

    Returns an `ingest_folder`-shaped result dict:
      indexed:      [{file, doc_id, chunks, doc_type}]
      skipped:      [(name, reason)]
      errors:       [str]
      total_chunks: int
      stats:        index_stats() after the run (None if nothing ran)
      synced_at:    ISO timestamp of this run's watermark (None on hard failure)
    """
    log = log or (lambda msg: None)
    result: dict = {
        "indexed": [], "skipped": [], "errors": [],
        "total_chunks": 0, "stats": None, "synced_at": None,
    }

    if not is_configured():
        result["errors"].append(
            "Google Drive isn't configured. Add [google].service_account_path and "
            "[google].shared_drive_folder_id to secrets."
        )
        return result

    # Stamp the watermark at the START of the run so edits made mid-sync are caught
    # next time rather than silently skipped.
    run_started = datetime.now(timezone.utc)
    cutoff = None if full else last_sync()

    try:
        if cutoff is not None:
            metas = drive.changed_since(cutoff, folder_id=folder_id)
            log(f"Incremental sync: {len(metas)} file(s) changed since {cutoff.isoformat()}.")
        else:
            metas = drive.list_team_docs(folder_id)
            log(f"Full sync: {len(metas)} supported file(s) in folder.")
    except Exception as e:
        result["errors"].append(f"Drive listing failed: {e}")
        return result

    for meta in metas:
        try:
            doc = drive.download_doc(meta.file_id)
        except Exception as e:
            result["skipped"].append((meta.name, f"download failed ({e})"))
            log(f"SKIP {meta.name}: download failed ({e})")
            continue

        text = (doc.text or "").strip()
        if not text:
            result["skipped"].append((meta.name, "empty after extract"))
            log(f"SKIP {meta.name}: empty after extract")
            continue

        dt = default_doc_type or doc_type_for(meta.name, meta.mime_type)
        archive_doc = Doc(
            doc_id=f"drive_{meta.file_id}",
            title=meta.name,
            source=_drive_url(meta.file_id, meta.mime_type),
            doc_type=dt,
            text=text,
            metadata={
                "drive_file_id": meta.file_id,
                "drive_mime": meta.mime_type,
                "drive_modified": meta.modified_time.isoformat(),
                "ingested_from": "google_drive",
            },
        )
        try:
            n = upsert_doc(archive_doc)
        except Exception as e:
            result["errors"].append(f"{meta.name}: index failed ({e})")
            log(f"ERROR {meta.name}: index failed ({e})")
            continue

        result["indexed"].append(
            {"file": meta.name, "doc_id": archive_doc.doc_id, "chunks": n, "doc_type": dt}
        )
        result["total_chunks"] += n
        log(f"Indexed {meta.name} -> {archive_doc.doc_id} ({n} chunks, {dt})")

    # Only advance the watermark + report stats if the run got far enough to list.
    result["stats"] = index_stats()
    result["synced_at"] = run_started.isoformat()
    state.update_settings(**{_LAST_SYNC_KEY: run_started.isoformat()})
    return result
