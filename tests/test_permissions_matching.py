"""Regression tests for permissions.py rule matching (2026-07-04 review)."""

from __future__ import annotations

import permissions


def test_matching_is_case_insensitive_on_every_platform():
    # Same behaviour on Windows and POSIX: deny rules must not be
    # bypassable via letter case anywhere.
    assert permissions.matches("Write(C:/data/CREDENTIALS/key.txt)",
                               "Write(*/credentials/*)")
    assert permissions.matches("write(x)", "Write(*)")


def test_prefix_rules_respect_word_boundaries():
    assert permissions.matches("Bash(rm -rf x)", "Bash(rm:*)")
    assert permissions.matches("Bash(rm)", "Bash(rm:*)")
    # 'rm:*' must NOT capture rmdir
    assert not permissions.matches("Bash(rmdir x)", "Bash(rm:*)")


def test_double_star_still_matches_everything():
    assert permissions.matches("Read(anything/at/all)", "Read(**)")
