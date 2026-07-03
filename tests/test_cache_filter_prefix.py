"""Regression test: cache filter_prefix must match on path-segment boundaries."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

import lock_scan


def _record(path: str) -> dict:
    return {
        "path": path,
        "scope": "project",
        "owner": "test",
        "created": "2026-07-04T00:00",
        "remaining": "23h",
        "legacy": False,
    }


def test_filter_prefix_does_not_leak_sibling_directories(tmp_path: Path):
    locks = [
        _record(r"C:\ws\SOFTWARE\proj\LOCK.txt"),
        _record(r"C:\ws\SOFTWARE-ARCHIVE\old\LOCK.txt"),
        _record(r"C:\ws\SOFTWARE2\x\LOCK.txt"),
    ]
    cache_file = tmp_path / "cache.md"
    config = {"caches": [{
        "name": "scoped",
        "path": str(cache_file),
        "filter_prefix": r"C:\ws\SOFTWARE",
    }]}

    results = lock_scan.write_caches(locks, datetime.now(), config)

    assert results == [(cache_file, 1)]
    content = cache_file.read_text(encoding="utf-8")
    assert "SOFTWARE-ARCHIVE" not in content
    assert "SOFTWARE2" not in content
