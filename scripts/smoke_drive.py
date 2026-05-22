"""Smoke test for lib.drive against an in-memory fake Drive service.

Validates:
1. Pure extractors round-trip (text, .docx)
2. list_team_docs walks a folder tree and filters supported mimes
3. download_doc dispatches to the right extractor for each mime type
4. changed_since respects modifiedTime cutoff

No real Google credentials needed. Real-Drive validation runs once the
service-account JSON is configured in `.streamlit/secrets.toml`.
"""
from __future__ import annotations

import io
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from lib.drive import (  # noqa: E402
    DOCX_MIME,
    GOOGLE_DOC_MIME,
    GOOGLE_FOLDER_MIME,
    PDF_MIME,
    changed_since,
    download_doc,
    extract_docx_text,
    extract_text,
    list_team_docs,
)
from tests.fixtures.drive_fake import (  # noqa: E402
    FakeDriveService,
    FakeDriveStore,
    FakeFile,
    patch_media_downloader,
)


def _make_docx_bytes(paragraphs: list[str]) -> bytes:
    from docx import Document
    doc = Document()
    for p in paragraphs:
        doc.add_paragraph(p)
    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()


def main() -> int:
    patch_media_downloader()

    print("=" * 64)
    print("1. extractors")
    print("=" * 64)

    gdoc_text = "Hello from a Google Doc.\n\nSecond paragraph here."
    out = extract_text(gdoc_text.encode("utf-8"), GOOGLE_DOC_MIME)
    assert "Hello" in out and "Second paragraph" in out, out
    print(f"  google-doc round-trip: {len(out)} chars OK")

    docx_bytes = _make_docx_bytes(["Para one of a fake docx.", "Para two."])
    out = extract_docx_text(docx_bytes)
    assert "Para one" in out and "Para two" in out, out
    print(f"  docx round-trip:       {len(out)} chars OK")

    out = extract_text(docx_bytes, DOCX_MIME)
    assert "Para one" in out, out
    print(f"  extract_text dispatch: OK")

    print()
    print("=" * 64)
    print("2. list_team_docs walks folder tree")
    print("=" * 64)

    store = FakeDriveStore()
    base = "2026-04-25T12:00:00.000Z"
    store.add(FakeFile("root", "Team Drive", GOOGLE_FOLDER_MIME, base, parents=[]))
    store.add(FakeFile("sub1", "2025-26 Conferences", GOOGLE_FOLDER_MIME, base, parents=["root"]))
    store.add(FakeFile("sub2", "Background Guides", GOOGLE_FOLDER_MIME, base, parents=["root"]))

    store.add(FakeFile(
        "doc1", "Brazil position paper.docx", DOCX_MIME, base,
        parents=["sub1"], body=_make_docx_bytes(["Brazil supports.", "Climate financing matters."]),
    ))
    store.add(FakeFile(
        "doc2", "Director note.txt", "text/plain", base,
        parents=["sub1"], body=b"random debrief notes",
    ))  # text/plain is not in SUPPORTED_MIMES, should be skipped
    store.add(FakeFile(
        "doc3", "HRC background.gdoc", GOOGLE_DOC_MIME,
        "2026-04-26T08:00:00.000Z",
        parents=["sub2"], body=b"Body of HRC guide as exported plain text.",
    ))
    store.add(FakeFile(
        "doc4", "trashed-old.docx", DOCX_MIME, base,
        parents=["sub2"], body=_make_docx_bytes(["should not appear"]), trashed=True,
    ))

    svc = FakeDriveService(store)
    metas = list_team_docs(folder_id="root", service=svc, recursive=True)
    names = sorted(m.name for m in metas)
    assert names == ["Brazil position paper.docx", "HRC background.gdoc"], names
    print(f"  found {len(metas)} supported docs (text/plain + trashed correctly skipped):")
    for m in metas:
        print(f"    {m.name} [{m.mime_type}] mt={m.modified_time.isoformat()}")

    print()
    print("=" * 64)
    print("3. download_doc + extraction by mime type")
    print("=" * 64)

    d1 = download_doc("doc1", service=svc)
    assert d1.mime_type == DOCX_MIME and "Brazil supports" in d1.text, d1.text[:200]
    print(f"  doc1 (.docx): {len(d1.text)} chars  preview: {d1.text[:60]!r}")

    d3 = download_doc("doc3", service=svc)
    assert d3.mime_type == GOOGLE_DOC_MIME and "HRC guide" in d3.text, d3.text[:200]
    print(f"  doc3 (gdoc):  {len(d3.text)} chars  preview: {d3.text[:60]!r}")

    print()
    print("=" * 64)
    print("4. changed_since respects cutoff")
    print("=" * 64)

    cutoff = datetime(2026, 4, 25, 18, 0, 0, tzinfo=timezone.utc)
    deltas = changed_since(cutoff, folder_id="root", service=svc)
    delta_names = [d.name for d in deltas]
    assert delta_names == ["HRC background.gdoc"], delta_names
    print(f"  cutoff={cutoff.isoformat()} -> deltas={delta_names}")

    print()
    print("OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
