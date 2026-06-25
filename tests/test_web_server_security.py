"""Security-focused tests for watcher.web_server helpers."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "watcher"))

import web_server  # noqa: E402


def test_resolve_within_blocks_traversal(tmp_path: Path):
    assert web_server._resolve_within(tmp_path, "../secret.md") is None
    assert web_server._resolve_within(tmp_path, "/tmp/secret.md") is None


def test_resolve_within_allows_safe_child(tmp_path: Path):
    assert web_server._resolve_within(tmp_path, "notes.md") == (tmp_path / "notes.md").resolve()


def test_safe_md_filename_rejects_paths_and_empty_values():
    assert web_server._safe_md_filename("") is None
    assert web_server._safe_md_filename("../notes.md") is None
    assert web_server._safe_md_filename("notes") == "notes.md"


def test_safe_header_value_blocks_response_splitting():
    assert web_server._safe_header_value("http://127.0.0.1:8095") == "http://127.0.0.1:8095"
    assert web_server._safe_header_value("http://127.0.0.1:8095\r\nX-Bad: 1") is None


def test_canonical_allowed_origin_never_reflects_untrusted_header():
    assert web_server._canonical_allowed_origin(8095, "http://127.0.0.1:8095") == (
        "http://127.0.0.1:8095"
    )
    assert web_server._canonical_allowed_origin(8095, "http://localhost:8095") == (
        "http://localhost:8095"
    )
    assert web_server._canonical_allowed_origin(8095, "http://[::1]:8095") == (
        "http://[::1]:8095"
    )
    assert web_server._canonical_allowed_origin(8095, "http://evil.test:8095") is None
    assert web_server._canonical_allowed_origin(8095, "http://127.0.0.1:8095\r\nX-Bad: 1") is None
