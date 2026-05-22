"""In-memory fake of the Google Drive v3 service used by lib.drive.

Mimics the surface that lib.drive consumes:
  service.files().list(q=..., fields=..., pageSize=..., pageToken=..., ...).execute()
  service.files().get(fileId=..., fields=..., ...).execute()
  service.files().get_media(fileId=..., ...)
  service.files().export_media(fileId=..., mimeType=...)

For get_media / export_media, the returned object is consumed by
googleapiclient.http.MediaIoBaseDownload — we substitute a tiny shim that
satisfies the same interface used in lib.drive._fetch_bytes.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class FakeFile:
    file_id: str
    name: str
    mime_type: str
    modified_time: str
    parents: list[str]
    body: bytes = b""
    trashed: bool = False

    def to_meta_dict(self) -> dict:
        return {
            "id": self.file_id,
            "name": self.name,
            "mimeType": self.mime_type,
            "modifiedTime": self.modified_time,
            "parents": list(self.parents),
            "trashed": self.trashed,
        }


class _FakeRequest:
    def __init__(self, payload: Any):
        self._payload = payload

    def execute(self) -> Any:
        return self._payload


class _FakeMediaRequest:
    """Stand-in for the request object passed to MediaIoBaseDownload."""
    def __init__(self, body: bytes):
        self.body = body


class _FakeFiles:
    def __init__(self, store: "FakeDriveStore"):
        self._store = store

    def list(self, q: str = "", fields: str = "", pageSize: int = 100,
             pageToken: str | None = None, **_kwargs) -> _FakeRequest:
        # Parse the parents filter `'<id>' in parents and trashed = false`.
        parent_id: str | None = None
        if " in parents" in q:
            head = q.split(" in parents")[0].strip()
            parent_id = head.strip("'\" ")

        files = [
            f.to_meta_dict()
            for f in self._store.files
            if not f.trashed and (parent_id is None or parent_id in f.parents)
        ]
        return _FakeRequest({"files": files, "nextPageToken": None})

    def get(self, fileId: str, fields: str = "", **_kwargs) -> _FakeRequest:
        f = self._store.by_id(fileId)
        if f is None:
            raise KeyError(fileId)
        return _FakeRequest(f.to_meta_dict())

    def get_media(self, fileId: str, **_kwargs) -> _FakeMediaRequest:
        f = self._store.by_id(fileId)
        if f is None:
            raise KeyError(fileId)
        return _FakeMediaRequest(f.body)

    def export_media(self, fileId: str, mimeType: str = "text/plain", **_kwargs) -> _FakeMediaRequest:
        f = self._store.by_id(fileId)
        if f is None:
            raise KeyError(fileId)
        # In the fake, body for Google Docs is already plain UTF-8 text bytes.
        return _FakeMediaRequest(f.body)


@dataclass
class FakeDriveStore:
    files: list[FakeFile] = field(default_factory=list)

    def by_id(self, file_id: str) -> FakeFile | None:
        for f in self.files:
            if f.file_id == file_id:
                return f
        return None

    def add(self, f: FakeFile) -> None:
        self.files.append(f)


class FakeDriveService:
    def __init__(self, store: FakeDriveStore):
        self._files = _FakeFiles(store)

    def files(self) -> _FakeFiles:
        return self._files


def patch_media_downloader() -> None:
    """Monkey-patch googleapiclient.http.MediaIoBaseDownload to read from our shim.

    The real downloader expects an HTTP-backed request object. Our fake yields
    a `_FakeMediaRequest` with `.body`. We swap in a tiny replacement that
    writes `.body` straight into the buffer.
    """
    import googleapiclient.http as gapi_http

    class _FakeDownloader:
        def __init__(self, fd, request):
            self._fd = fd
            self._req = request

        def next_chunk(self):
            self._fd.write(self._req.body)
            return None, True

    gapi_http.MediaIoBaseDownload = _FakeDownloader  # type: ignore[assignment]
