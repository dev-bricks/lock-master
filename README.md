# lock-master

**EN** | [DE](README_de.md) | [ES](README_es.md) | [JA](README_ja.md) | [RU](README_ru.md) | [ZH](README_zh-Hans.md)

**Portable, config-driven file-lock system for multi-agent project coordination.**

lock-master provides a lightweight, zero-dependency locking protocol based on
plain text files. A `LOCK*.txt` file in a project directory signals that the
project or a component is currently in use -- no agent, automation, or loop
should modify that area while a valid, non-expired lock exists.

---

## Features

- **Scope-based locking:** `LOCK.txt` locks the whole project; `LOCK.<scope>.txt` locks a component. Multiple agents can work in parallel on different scopes of the same project.
- **Auto-expiry:** every lock has a configurable `expires_after` duration (default 24h). A stale-cleanup script removes forgotten locks.
- **Read-only scan:** `lock_scan.py` lists all active locks across configured roots without touching any files.
- **Markdown cache:** `lock_scan.py --write-cache` writes a `LOCK-CACHE.md` for instant status overview -- no scan needed.
- **Dry-run prune:** `prune_stale_locks.py --dry-run` previews what would be removed.
- **Zero dependencies:** pure Python standard library (3.10+).
- **Config-driven:** all roots, depth limits, skip-dirs and cache targets live in `lock_roots.json` -- no hardcoded paths.

---

## Quick Start

### 1. Copy the scripts

```
lock_utils.py
lock_scan.py
prune_stale_locks.py
LOCK_TEMPLATE.txt
```

Place them in a directory of your choice (e.g. `scripts/`).

### 2. Create `lock_roots.json`

Copy `lock_roots.example.json`, rename it to `lock_roots.json`, and replace
the placeholder paths with your actual project roots. The file is excluded from
version control by `.gitignore` (it contains local absolute paths).

```json
{
  "default_max_depth": 4,
  "shallow_depth": 2,
  "skip_dirs": [".git", ".venv", "node_modules", "__pycache__", "build", "dist"],
  "roots": [
    { "path": "/path/to/project-a" },
    { "path": "/path/to/project-b" },
    { "path": "/path/to/large-tree", "shallow": true }
  ],
  "caches": [
    {
      "name": "system-wide",
      "path": "/path/to/scripts/LOCK-CACHE.md"
    }
  ]
}
```

### 3. Create a lock

Copy `LOCK_TEMPLATE.txt` into your project directory, fill in the fields, and
rename it to `LOCK.txt` (or `LOCK.<scope>.txt` for component-level locking):

```
owner: my-agent
created: 2026-06-14T10:00
expires_after: 24h
mode: hard
purpose: Refactoring auth module
```

### 4. List active locks

```bash
python lock_scan.py
python lock_scan.py --json
```

### 5. Remove expired locks

```bash
# Preview (safe):
python prune_stale_locks.py --dry-run

# Actually remove:
python prune_stale_locks.py
```

### 6. Refresh the cache

```bash
python lock_scan.py --write-cache
```

Writes `LOCK-CACHE.md` as defined in the `"caches"` key of `lock_roots.json`.

---

## Lock File Format

Plain text, one `key: value` per line. Lines starting with `#` are comments.

| Field               | Required | Example              | Meaning |
|---------------------|----------|----------------------|---------|
| `owner`             | yes      | `my-agent`           | Who holds the lock. |
| `created`           | yes      | `2026-06-14T10:00`   | ISO timestamp; base for expiry calculation. |
| `expires_after`     | optional | `24h`, `90m`, `2d`   | Duration string. Default: `24h`. |
| `release_condition` | optional | `PR merged`          | Free-text: when can the lock be released. |
| `mode`              | optional | `hard` \| `soft`     | `hard` = no changes (default); `soft` = reads/hints ok. |
| `purpose`           | optional | `Adding feature X`   | Free-text description of what is running. |
| `scope`             | optional | `frontend`           | Informational; the **filename** is authoritative. |

If `created` is absent or unparseable, the file's mtime is used as fallback.

---

## Scope Convention

| Filename             | Scope detected | What is locked |
|----------------------|----------------|----------------|
| `LOCK.txt`           | `project`      | Entire project directory |
| `LOCK.api.txt`       | `api`          | Only the `api` component |
| `LOCK.frontend.txt`  | `frontend`     | Only the `frontend` component |
| `LOCK.my_scope.txt`  | `my_scope`     | Any freely named sub-area |

Detection regex: `^LOCK(\.[^.]+)?\.txt$` (case-insensitive).

---

## Lifecycle

```
RESPECT  -->  CLAIM  -->  RELEASE
```

1. **RESPECT:** before starting work on a project or component, check for an
   active `LOCK*.txt` covering that area. If one exists and has not expired,
   choose a different task or wait.
2. **CLAIM:** create your lock file from the template (`owner`, `created`,
   `expires_after`, `purpose`).
3. **RELEASE:** **delete your own lock file** when done. Active release is
   required; the `expires_after` timeout is only a safety net for forgotten
   locks. If work takes longer than expected, renew `created` to prevent
   premature expiry.

---

## Configuration Reference (`lock_roots.json`)

| Key                 | Type     | Default | Description |
|---------------------|----------|---------|-------------|
| `default_max_depth` | int      | `4`     | Max directory recursion depth from each root. |
| `shallow_depth`     | int      | `2`     | Depth for roots marked `"shallow": true`. |
| `skip_dirs`         | string[] | `[]`    | Directory names to skip entirely (including subtree). |
| `roots`             | object[] | `[]`    | List of `{ "path": "...", "shallow": true/false }`. |
| `caches`            | object[] | `[]`    | Cache targets: `{ "name", "path", "filter_prefix?" }`. |

**Cache entry fields:**

| Key             | Required | Description |
|-----------------|----------|-------------|
| `name`          | yes      | Display name used as the cache title. |
| `path`          | yes      | Absolute path where `LOCK-CACHE.md` is written. |
| `filter_prefix` | optional | Only include locks whose path starts with this prefix. |

If `"caches"` is omitted, `--write-cache` writes a single `LOCK-CACHE.md`
next to `lock_scan.py`.

---

## Python API

```python
from pathlib import Path
import lock_utils

project = Path("/path/to/my-project")

# Check before starting work
active = lock_utils.active_locks(project)
if active:
    print(f"Locked: {active}")
else:
    print("Free to work.")

# Parse a specific lock file
data = lock_utils.parse_lock_file(project / "LOCK.txt")
print(data["owner"], data["created"])

# Check expiry
from datetime import datetime
expired = lock_utils.is_expired(project / "LOCK.txt", now=datetime.now())
```

---

## Running Tests

```bash
python -m pytest tests/ -v
```

Requires `pytest` (`pip install pytest`).

---

## Files

```
lock-master/
├── lock_utils.py           # Core library: parse, scope, expiry
├── lock_scan.py            # CLI: list active locks, write cache
├── prune_stale_locks.py    # CLI: remove expired locks
├── LOCK_TEMPLATE.txt       # Template for creating a new lock
├── lock_roots.example.json # Annotated example config
├── LOCK-SYSTEM.md          # Canonical spec and lifecycle reference
├── tests/
│   └── test_smoke.py       # Smoke tests
├── LICENSE                 # MIT
├── CHANGELOG.md
├── TODO.md
├── SECURITY.md
├── llms.txt
└── VERSION
```

---

## Requirements

- Python 3.10+
- No third-party dependencies (standard library only)
- For tests: `pytest`

---

## License

MIT -- Copyright (c) 2026 Lukas Geiger. See [LICENSE](LICENSE).
