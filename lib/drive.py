"""Google Drive integration.

Stub for May scaffolding. Full implementation lands in Phase 1.2:
- service account auth
- list/download files from a shared folder
- change detection via modifiedTime
- chunking-friendly extraction (Docs, PDFs, .docx)
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass
class DriveDoc:
    file_id: str
    name: str
    mime_type: str
    modified_time: datetime
    parents: list[str]
    text: str


def list_team_docs() -> list[DriveDoc]:
    raise NotImplementedError("Phase 1.2 — Google Cloud project + service account required first.")


def download_doc(file_id: str) -> DriveDoc:
    raise NotImplementedError("Phase 1.2")
