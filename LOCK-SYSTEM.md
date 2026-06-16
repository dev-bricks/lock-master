# LOCK-SYSTEM -- Project Locks for Multi-Agent Coordination

**Scope:** All project roots listed in your `lock_roots.json`.
**Canonical spec:** This file. Script-level docs are in the individual `.py` files.
**Updated:** 2026-06-14

---

## Purpose

Central coordination principle for parallel work by multiple agents, automated
loops, or humans: a `LOCK*.txt` file in a project directory signals that the
project or a component is in use -- no agent or automated loop modifies that
area while a valid, non-expired lock exists.

---

## Quick Overview: Who Holds What?

Fastest ways to see active locks (in order of speed):

1. **Search tool (fastest, live):** search for `LOCK*.txt` files in the
   relevant root using your file-search tooling.
2. **Cache file (no scan needed):** read the auto-generated `LOCK-CACHE.md`
   (written by `lock_scan.py --write-cache`).
3. **Script:** `python lock_scan.py` (read-only list) or
   `python lock_scan.py --write-cache` (refresh cache).

The `LOCK*.txt` files themselves are always authoritative; the cache is a
derived quick-index only.

---

## Scope via Filename (FILENAME IS AUTHORITATIVE)

- `LOCK.txt` -- entire project locked (scope = `project`).
- `LOCK.<scope>.txt` -- only that component locked; free scope name
  (sub-area / sub-folder), e.g. `LOCK.frontend.txt`, `LOCK.api.txt`,
  `LOCK.mobile.txt`.
- Multiple agents can work in parallel on different components of the same
  project using different scoped locks.
- Detection regex: `^LOCK(\.[^.]+)?\.txt$`
- Legacy `TEST.txt` / `TESTS.txt` -- deprecated, do not create new ones
  (still recognised as a lock, but not subject to automatic expiry).

---

## File Format (one setting per line, `key: value`)

Template: `LOCK_TEMPLATE.txt`. Lines starting with `#` = comment; blank lines
are ignored.

| Field              | Required | Meaning |
|--------------------|----------|---------|
| `owner`            | yes      | Who holds the lock (agent / user / automation). |
| `created`          | yes      | ISO timestamp `YYYY-MM-DDTHH:MM` (base for expiry). |
| `host`             | optional | Machine/hostname holding the lock — which system locked it (cross-system). |
| `expires_after`    | optional | e.g. `24h` / `48h` / `90m`. Default = `24h`. |
| `release_condition`| optional | Free text: what must happen for the lock to be released. |
| `mode`             | optional | `hard` (no changes, default) \| `soft` (reads/hints ok). |
| `purpose`          | optional | Free text: why locked / what is running. |
| `scope`            | optional | Informational only; the filename is authoritative. |

If `created` is missing or unparseable, the file's mtime is used as fallback
for expiry calculation.

---

## Two Tiers of Enforcement

**Tier 1 -- RESPECT (always required, everywhere):**
Before modifying any project or component, check whether a non-expired
`LOCK*.txt` exists for the affected area (the project-wide `LOCK.txt` blocks
everything). If one exists and has not expired: do not touch it -- pick another
project or wait. This applies system-wide to every agent in every pipeline.

**Tier 2 -- CREATE (optional unless mandated):**
Actively creating a lock at the start of work is not universally required.
- If a project marks itself with `LOCK-required: yes` in its documentation,
  creating a lock is mandatory there.
- Otherwise: recommended whenever parallel work is possible.

**Fallback / precedence:** This spec is the system-wide default.
Project-specific rules take local precedence (more specific beats more general):
a project may declare stricter requirements (e.g. mandatory creation) or use
a custom scope name.

---

## Lifecycle: RESPECT -> CLAIM -> RELEASE

1. **RESPECT:** check for an active lock on the area before working.
2. **CLAIM:** create your own `LOCK.txt` or `LOCK.<scope>.txt` from the
   template (`owner`, ISO `created`, `expires_after`, `purpose`).
3. **RELEASE:** delete the lock file you created when done. Active release
   by the creator is required; the 24h expiry is only a safety net for
   forgotten locks. If work takes longer, renew `created` so the lock does
   not expire prematurely.

---

## Scripts

Place all scripts in the same directory as `lock_roots.json`.
On Windows, always set `PYTHONIOENCODING=utf-8` (cp1252 default encoding).

**List active locks system-wide (read-only):**
```
python lock_scan.py
python lock_scan.py --json
```

**Remove expired locks:**
```
# Preview first (deletes nothing):
python prune_stale_locks.py --dry-run
# Actually remove:
python prune_stale_locks.py
```

**Refresh LOCK-CACHE.md:**
```
python lock_scan.py --write-cache
```
Writes cache file(s) as defined in `lock_roots.json` ("caches" key).

**Custom roots file:**
```
python lock_scan.py --roots-file /path/to/my_roots.json
python prune_stale_locks.py --roots-file /path/to/my_roots.json
```

**Scan performance:** `lock_roots.json` controls `default_max_depth` (default 4),
`shallow_depth` (default 2, for roots with `"shallow": true` for large trees),
and `skip_dirs` (directories skipped including their subtrees, e.g.
`node_modules`, `.venv`, `.git`, `build`, `releases`).

---

## Library

`lock_utils.py` is the canonical format/scope/expiry library. Import it
from your own scripts rather than re-implementing the logic.
