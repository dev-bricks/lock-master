"""Tests for the condition-lock system (v1.4.0).

Condition locks (LOCK.condition(.<scope>).txt) hold until their
release_condition is fulfilled: no time expiry, never pruned, optionally
operation-scoped via the 'operations:' field.
"""

from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import lock_utils  # noqa: E402


def _write(tmp_path: Path, name: str, content: str) -> Path:
    p = tmp_path / name
    p.write_text(content, encoding="utf-8")
    return p


class TestConditionLockNaming:
    def test_project_level_condition_lock(self):
        assert lock_utils.is_condition_lock("LOCK.condition.txt")
        assert lock_utils.scope_from_name("LOCK.condition.txt") == "project"

    def test_scoped_condition_lock(self):
        name = "LOCK.condition.publish-release.txt"
        assert lock_utils.is_condition_lock(name)
        assert lock_utils.scope_from_name(name) == "publish-release"

    def test_multi_segment_scope(self):
        name = "LOCK.condition.zenodo-upload.paper3-4.txt"
        assert lock_utils.is_condition_lock(name)
        assert lock_utils.scope_from_name(name) == "zenodo-upload.paper3-4"

    def test_other_locks_are_not_condition_locks(self):
        for name in ("LOCK.txt", "LOCK.api.txt", "LOCK.user.txt",
                     "LOCK.team.HOST.txt", "LOCK.conditioner.txt"):
            assert not lock_utils.is_condition_lock(name), name

    def test_conditioner_scope_is_plain_exclusive(self):
        # Prefix similarity must not trigger the marker.
        assert lock_utils.scope_from_name("LOCK.conditioner.txt") == "conditioner"


class TestConditionLockProtection:
    def test_condition_lock_is_protected(self):
        assert lock_utils.is_protected_lock("LOCK.condition.txt")
        assert lock_utils.is_protected_lock("LOCK.condition.publish.txt")

    def test_condition_lock_never_expires(self, tmp_path):
        lock = _write(tmp_path, "LOCK.condition.publish.txt",
                      "owner: agent\ncreated: 2020-01-01T00:00\n"
                      "release_condition: follow-ups merged\n")
        assert not lock_utils.is_expired(lock)

    def test_condition_lock_never_prunable(self, tmp_path):
        lock = _write(tmp_path, "LOCK.condition.publish.txt",
                      "owner: agent\ncreated: 2020-01-01T00:00\n"
                      "release_condition: follow-ups merged\n")
        assert not lock_utils.is_prunable(lock)

    def test_user_lock_never_expires_after_fix(self, tmp_path):
        # v1.4.0 fix: nominally expired user locks stay active.
        lock = _write(tmp_path, "LOCK.user.txt",
                      "owner: user\ncreated: 2020-01-01T00:00\n")
        assert not lock_utils.is_expired(lock)

    def test_normal_lock_still_expires(self, tmp_path):
        lock = _write(tmp_path, "LOCK.old.txt",
                      "owner: x\ncreated: 2020-01-01T00:00\n")
        assert lock_utils.is_expired(lock)
        assert lock_utils.is_prunable(lock)

    def test_active_locks_includes_condition_lock(self, tmp_path):
        _write(tmp_path, "LOCK.condition.publish.txt",
               "owner: agent\ncreated: 2020-01-01T00:00\n"
               "release_condition: follow-ups merged\n")
        _write(tmp_path, "LOCK.stale.txt",
               "owner: x\ncreated: 2020-01-01T00:00\n")
        names = [n for n, _, _ in lock_utils.active_locks(tmp_path,
                                                          datetime.now())]
        assert "LOCK.condition.publish.txt" in names
        assert "LOCK.stale.txt" not in names


class TestLockedOperations:
    def test_operations_parsed_as_list(self, tmp_path):
        lock = _write(tmp_path, "LOCK.condition.publish.txt",
                      "owner: agent\ncreated: 2026-07-04T00:00\n"
                      "release_condition: follow-ups merged\n"
                      "operations: publish-release, registry-upload\n")
        assert lock_utils.locked_operations(lock) == [
            "publish-release", "registry-upload"]

    def test_missing_operations_field_gives_empty_list(self, tmp_path):
        lock = _write(tmp_path, "LOCK.condition.publish.txt",
                      "owner: agent\ncreated: 2026-07-04T00:00\n"
                      "release_condition: follow-ups merged\n")
        assert lock_utils.locked_operations(lock) == []
