r"""
lock_utils.py -- Canonical logic for project locks (LOCK*.txt)

Single source of truth for the LOCK file format and the scope/expiry logic
across all configured roots (see lock_roots.json).

Canonical spec (lifecycle, tiers, scripts): LOCK-SYSTEM.md (same directory).

Convention:
  - LOCK.txt            = entire project locked      (scope = "project")
  - LOCK.<scope>.txt    = only this component locked (scope = "<scope>")
                          free scope name (sub-area/sub-folder),
                          e.g. LOCK.frontend.txt, LOCK.web.txt, LOCK.api.txt
  - Detection regex: ^LOCK(\.[^.]+)?\.txt$
  - Legacy (deprecated, do not create): TEST.txt / TESTS.txt

File format (one setting per line, stdlib parser, no extra dependency):
  - Lines starting with '#' = comment, blank lines = ignored.
  - Otherwise split on the FIRST ':'; trim key/value; key lowercased.
  Fields:
    owner             (required)  Who holds the lock.
    created           (required)  ISO YYYY-MM-DDTHH:MM (base for expiry).
    expires_after     (optional)  e.g. "24h" / "48h" / "90m". Default = 24h.
    release_condition (optional)  Free-text release condition.
    mode              (optional)  "hard" (default) | "soft".
    purpose           (optional)  Free-text description.
    scope             (optional)  Informational only; AUTHORITATIVE is the filename.
"""

from __future__ import annotations

import re
from datetime import datetime, timedelta
from pathlib import Path

# Current lock files: LOCK.txt + LOCK.<scope>.txt
LOCK_RE = re.compile(r"^LOCK(?:\.([^.]+))?\.txt$", re.IGNORECASE)
# Legacy locks (still recognised, but marked as deprecated)
LEGACY_LOCK_NAMES = ("TEST.txt", "TESTS.txt")

DEFAULT_EXPIRES = timedelta(hours=24)

# Duration strings: "24h", "48h", "90m", "30s", "2d"
_DURATION_RE = re.compile(r"^\s*(\d+)\s*([smhd])\s*$", re.IGNORECASE)
_DURATION_UNITS = {"s": "seconds", "m": "minutes", "h": "hours", "d": "days"}


def scope_from_name(name: str) -> str | None:
    """Derive scope from filename. LOCK.txt -> 'project',
    LOCK.<scope>.txt -> '<scope>'. Returns None if not a lock filename."""
    m = LOCK_RE.match(name)
    if not m:
        return None
    return m.group(1) if m.group(1) else "project"


def is_lock_file(name: str) -> bool:
    return LOCK_RE.match(name) is not None


def parse_lock_file(lock_path: Path) -> dict[str, str]:
    """Parse a LOCK file into a key:value dict (keys lowercased)."""
    data: dict[str, str] = {}
    try:
        text = lock_path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return data
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if ":" not in stripped:
            continue
        key, value = stripped.split(":", 1)
        data[key.strip().lower()] = value.strip()
    return data


def parse_duration(value: str | None) -> timedelta:
    """'24h'/'90m'/... -> timedelta. Defaults to 24h if missing or unparseable."""
    if not value:
        return DEFAULT_EXPIRES
    m = _DURATION_RE.match(value)
    if not m:
        return DEFAULT_EXPIRES
    amount = int(m.group(1))
    unit = _DURATION_UNITS[m.group(2).lower()]
    return timedelta(**{unit: amount})


def _parse_created(value: str | None) -> datetime | None:
    """Parse ISO timestamp from 'created' field (T or space separator,
    seconds optional)."""
    if not value:
        return None
    candidate = value.strip().replace("T", " ")
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d"):
        try:
            return datetime.strptime(candidate, fmt)
        except ValueError:
            continue
    return None


def lock_created_and_expiry(lock_path: Path) -> tuple[datetime, timedelta, str]:
    """Return (created, expires_after, source).
    source = 'header' if created came from the file, else 'mtime' (fallback)."""
    data = parse_lock_file(lock_path)
    created = _parse_created(data.get("created"))
    expires = parse_duration(data.get("expires_after"))
    if created is not None:
        return created, expires, "header"
    mtime = datetime.fromtimestamp(lock_path.stat().st_mtime)
    return mtime, expires, "mtime"


def is_expired(lock_path: Path, now: datetime | None = None) -> bool:
    now = now or datetime.now()
    created, expires, _ = lock_created_and_expiry(lock_path)
    return now > created + expires


def lock_host(lock_path: Path) -> str | None:
    """Machine/hostname from the 'host' field of the LOCK file.

    Identifies which system currently holds the lock (cross-system
    coordination). Returns None when the field is absent (backwards
    compatible)."""
    return parse_lock_file(lock_path).get("host") or None


def find_lock_files(project_dir: Path, include_legacy: bool = True):
    """Find all lock files in a project root directory.
    Returns: list of (name, scope, is_legacy)."""
    results = []
    for hit in sorted(project_dir.glob("*.txt")):
        if not hit.is_file():
            continue
        scope = scope_from_name(hit.name)
        if scope is not None:
            results.append((hit.name, scope, False))
    if include_legacy:
        for legacy in LEGACY_LOCK_NAMES:
            for hit in project_dir.glob(legacy):
                if hit.is_file():
                    results.append((hit.name, "project", True))
    return sorted(set(results))


def active_locks(project_dir: Path, now: datetime | None = None):
    """Non-expired lock files. Returns list of (name, scope, is_legacy).
    Legacy locks (TEST.txt/TESTS.txt) have no expiry format -> always treated
    as active (stale cleanup only applies to LOCK*.txt)."""
    now = now or datetime.now()
    out = []
    for name, scope, is_legacy in find_lock_files(project_dir):
        lock_path = project_dir / name
        if is_legacy:
            out.append((name, scope, is_legacy))
            continue
        if not is_expired(lock_path, now):
            out.append((name, scope, is_legacy))
    return out
