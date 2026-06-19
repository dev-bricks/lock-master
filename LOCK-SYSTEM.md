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
- `LOCK.team.<host>.txt` -- Team Lock for the whole project (see below).
- `LOCK.team.<scope>.<host>.txt` -- Team Lock for a specific component (see below).
- Multiple agents can work in parallel on different components of the same
  project using different scoped locks.
- Detection regex: `^LOCK(\.[A-Za-z0-9_-]+(\.[A-Za-z0-9_-]+)*)?\.txt$`
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

---

## Lock Types: Exclusive vs. Team

### Exclusive Lock (default)

`LOCK.txt` or `LOCK.<scope>.txt` -- locks the area for all systems and all
agents. No other system or agent may modify the locked area while the lock
is active. Use this when only one system should work in an area at a time.

### Team Lock

`LOCK.team.<host>.txt` or `LOCK.team.<scope>.<host>.txt` -- coordinates
multiple agents **within one system** (e.g. several parallel agents on the
same machine). It signals "my system is active here; other systems should
stay out."

**Why per-system, not cross-system?** Cloud-sync latency (30 s -- 5 min
with OneDrive, Dropbox, or other shared filesystems) makes real-time
coordination across system boundaries unreliable. Each system manages its
own agents internally via the Team Lock; cross-system exclusion is achieved
by the presence of the Team Lock file itself (other systems see it and stay
out).

**When a second system wants to enter the same scope:**
- If the scopes do not overlap: it may create its own
  `LOCK.team.<scope>.<its-host>.txt` for its slice.
- If the scopes overlap: treat the existing Team Lock like an Exclusive Lock
  -- wait or choose a different task.

**Conflict copies (cloud-sync rename collision):** When two systems write
a Team Lock simultaneously, one rename wins and one becomes a conflict copy.
The system whose file survived continues; the other must back off and retry.
On NTFS and most cloud-sync filesystems, a rename within the same directory
is atomic and can be used as a lightweight claim mechanism.

### Required content of a Team Lock file

A Team Lock must contain all four sections (use `TEAM_LOCK_TEMPLATE.txt`):

1. **Presence log** -- loop ID, agent name, role, main task, start time.
   Every agent checks in here before working; removes its entry when done.
2. **File/folder claims + queue** -- who is editing what; who is waiting.
3. **Tool/software/MCP claims + queue** -- exclusive resources (e.g. a
   running server, a DB connection, a specific MCP tool). Only claim what
   is truly exclusive; keep claims tight.
4. **Messages, tips, lessons learned** -- short handovers, warnings, notes
   for other agents on the same team.

### Team Lock coordination rules

- **Check in before working:** add your presence entry before touching files.
- **Rotate roles when requested** by the team coordinator (first-in agent
  or designated lead).
- **Choose a complementary slice** if a resource is already claimed; do not
  double-claim.
- **Update claims on task change:** if you switch to a different area,
  update your claim immediately.
- **Respect queue order:** agents listed as waiting in the queue have
  priority when the resource becomes free.
- **Clean up on exit:** remove your presence entry and your claims. Delete
  the Team Lock file only when the presence log is fully empty.

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
