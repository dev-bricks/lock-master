r"""
prune_stale_locks.py -- System-wide stale cleanup for project locks (LOCK*.txt)

Scans all roots configured in lock_roots.json (with depth limits and
skip-lists) for LOCK*.txt files and removes expired ones:
  created + expires_after < now  (default expires_after = 24h)
Fallback for missing 'created': file mtime.
Legacy TEST.txt/TESTS.txt are NOT touched (no expiry format).

Usage:
  python prune_stale_locks.py
  python prune_stale_locks.py --dry-run
  python prune_stale_locks.py --roots-file <path>

Canonical spec: LOCK-SYSTEM.md (same directory).
Format/expiry logic: lock_utils.py.
Directory walk + config loading: lock_scan.py (DRY, no second standard).
"""

from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path

import lock_utils
from lock_scan import DEFAULT_ROOTS_FILE, iter_lock_dirs, load_config


def prune(config: dict, dry_run: bool = False) -> int:
    now = datetime.now()
    removed = 0
    kept = 0
    seen: set[Path] = set()

    for d in iter_lock_dirs(config):
        if d in seen:
            continue
        seen.add(d)
        for name, _scope, is_legacy in lock_utils.find_lock_files(d):
            if is_legacy:
                # Legacy TEST.txt/TESTS.txt: no expiry format -> do not remove.
                continue
            lock_path = d / name
            if lock_utils.is_expired(lock_path, now):
                created, expires, source = lock_utils.lock_created_and_expiry(lock_path)
                age_h = (now - created).total_seconds() / 3600
                if dry_run:
                    print(f"[would remove] {lock_path} "
                          f"(age {age_h:.1f}h, expires_after {expires}, source {source})")
                else:
                    try:
                        lock_path.unlink()
                        print(f"[removed] {lock_path} "
                              f"(age {age_h:.1f}h, expires_after {expires}, source {source})")
                    except OSError as exc:
                        print(f"[ERROR] {lock_path} could not be removed: {exc}")
                        kept += 1
                        continue
                removed += 1
            else:
                kept += 1

    verb = "would remove" if dry_run else "removed"
    print(f"prune_stale_locks: {removed} expired LOCK*.txt {verb}, "
          f"{kept} active lock(s) kept.")
    return removed


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Remove expired project locks (LOCK*.txt) across all configured roots."
    )
    parser.add_argument("--dry-run", action="store_true",
                        help="Show what would be removed without deleting anything.")
    parser.add_argument("--roots-file", default=str(DEFAULT_ROOTS_FILE),
                        help="Path to lock_roots.json.")
    args = parser.parse_args()

    config = load_config(Path(args.roots_file))
    prune(config, dry_run=args.dry_run)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
