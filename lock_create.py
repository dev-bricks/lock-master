#!/usr/bin/env python3
"""lock_create.py -- stamp a new LOCK*.txt into a project directory.

Convenience companion to LOCK_TEMPLATE.txt: builds the correct file name for
exclusive, scoped, team, user and condition locks, fills in the standard
fields and refuses to clobber an existing lock unless --force is given.

Examples:

    python lock_create.py /path/to/project --owner my-agent --purpose "refactor"
    python lock_create.py /path/to/project --scope docs --expires 90m
    python lock_create.py /path/to/project --team LAPTOP --scope assets
    python lock_create.py /path/to/project --user
    python lock_create.py /path/to/project --condition --scope publish \
        --release-condition "PR #42 merged"

Zero dependencies (Python 3.10+). See LOCK-SYSTEM.md for the semantics.
"""
from __future__ import annotations

import argparse
import platform
import sys
from datetime import datetime
from pathlib import Path

from lock_utils import is_lock_file

_SCOPE_OK = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-"


def _check_segment(value: str, what: str) -> str:
    """Validate a file-name segment (scope or team host)."""
    if not value or any(c not in _SCOPE_OK for c in value):
        raise SystemExit(
            f"error: invalid {what} {value!r} -- allowed: letters, digits, '_', '-'"
        )
    return value


def build_lock_name(scope: str | None, team_host: str | None,
                    user: bool, condition: bool) -> str:
    """Build the LOCK*.txt file name from the requested lock kind."""
    if sum(bool(x) for x in (team_host, user, condition)) > 1:
        raise SystemExit("error: --team, --user and --condition are mutually exclusive")
    parts: list[str] = ["LOCK"]
    if user:
        parts.append("user")
    elif condition:
        parts.append("condition")
    elif team_host:
        parts.append("team")
    if scope:
        parts.append(_check_segment(scope, "scope"))
    if team_host:
        parts.append(_check_segment(team_host, "team host"))
    parts.append("txt")
    return ".".join(parts)


def build_lock_body(args: argparse.Namespace, scope_label: str) -> str:
    """Render the key: value body of the lock file."""
    lines = [
        f"owner: {args.owner}",
        f"created: {datetime.now().strftime('%Y-%m-%dT%H:%M')}",
        f"host: {args.host}",
    ]
    if args.user:
        lines.append("removable_by: user")
    elif args.condition:
        # Condition locks never expire by time; the condition gates removal.
        pass
    else:
        lines.append(f"expires_after: {args.expires}")
    if args.release_condition:
        lines.append(f"release_condition: {args.release_condition}")
    lines.append(f"mode: {args.mode}")
    if args.purpose:
        lines.append(f"purpose: {args.purpose}")
    lines.append(f"scope: {scope_label}")
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Create a LOCK*.txt in a project directory."
    )
    parser.add_argument("project_dir", type=Path,
                        help="project directory that should be locked")
    parser.add_argument("--scope", default=None,
                        help="component scope (LOCK.<scope>.txt); default: whole project")
    parser.add_argument("--team", metavar="HOST", default=None,
                        help="create a team lock for this system host name")
    parser.add_argument("--user", action="store_true",
                        help="create a user lock (only the user removes it)")
    parser.add_argument("--condition", action="store_true",
                        help="create a condition lock (requires --release-condition)")
    parser.add_argument("--owner", default=None,
                        help="lock owner (default: lock_create/<host>)")
    parser.add_argument("--host", default=None,
                        help="host name (default: this machine's name)")
    parser.add_argument("--expires", default="24h",
                        help="expiry duration for time-based locks (default: 24h)")
    parser.add_argument("--mode", choices=("hard", "soft"), default="hard",
                        help="hard = no changes (default), soft = read/notice ok")
    parser.add_argument("--purpose", default=None,
                        help="free-text: why the area is locked")
    parser.add_argument("--release-condition", default=None,
                        help="free-text release condition (required for --condition)")
    parser.add_argument("--force", action="store_true",
                        help="overwrite an existing lock file of the same name")
    args = parser.parse_args(argv)

    if args.condition and not args.release_condition:
        parser.error("--condition requires --release-condition")

    project_dir: Path = args.project_dir
    if not project_dir.is_dir():
        raise SystemExit(f"error: not a directory: {project_dir}")

    args.host = args.host or platform.node() or "unknown"
    args.owner = args.owner or f"lock_create/{args.host}"

    name = build_lock_name(args.scope, args.team, args.user, args.condition)
    if not is_lock_file(name):  # defence in depth: must match the canonical regex
        raise SystemExit(f"error: generated name {name!r} is not a valid lock name")

    lock_path = project_dir / name
    if lock_path.exists() and not args.force:
        raise SystemExit(
            f"error: {lock_path} already exists (use --force to overwrite)"
        )

    scope_label = args.scope or "project"
    lock_path.write_text(build_lock_body(args, scope_label), encoding="utf-8")
    print(f"created: {lock_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
