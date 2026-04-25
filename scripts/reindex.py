"""Nightly reindex: pull Drive -> chunk -> embed -> upsert.

Run via cron once Phase 1.3 is live:
    0 3 * * *  cd ~/qmun-hub && /usr/bin/python3 scripts/reindex.py >> logs/reindex.log 2>&1
"""
from __future__ import annotations


def main() -> int:
    raise NotImplementedError("Phase 1.3")


if __name__ == "__main__":
    raise SystemExit(main())
