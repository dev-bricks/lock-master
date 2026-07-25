# Changelog

All notable changes to this project will be documented in this file.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).
This project adheres to [Semantic Versioning](https://semver.org/).

---

## [1.4.2] - 2026-07-25

### Added & Improved

- **Pyproject Metadata**: Added standardized `pyproject.toml` (PEP 621) with package metadata, URLs, keywords, and `pytest` configuration (`[tool.pytest.ini_options]`).
- **Discoverability & Badges**: Added Shields.io badges (Python, License, Multi-Agent Lock Protocol, LLM Indexing) and LLM indexing callouts (`> [!NOTE]`) to `README.md` and `README_de.md`.
- **LLM Index Refresh**: Updated `llms.txt` header timestamp to `2026-07-25`.

## [1.4.1] - 2026-07-04

### Fixed

- **Watcher daemon no longer crashes on its first scan.** `watcher/scanner.py`
  called five `lock_utils` helpers that only existed in a downstream fork of the
  library, not in this repo (`lock_name_parts`, `lock_type_from_name`,
  `normalize_lock_fields`, `parse_team_lock_sections`, `compute_expires_at`) —
  any tree containing a single `LOCK*.txt` killed the daemon with an
  `AttributeError` within one scan interval. The helpers are now part of
  `lock_utils.py`, and the daemon loop additionally guards full scans and quick
  checks so one failing scan can never terminate the process.
- **Watcher DB accepts user and condition locks.** The `locks` table CHECK
  constraint only knew `exclusive/team/legacy`, so v1.3.0 user locks and v1.4.0
  condition locks could never be persisted (`IntegrityError`). New databases use
  the extended constraint; existing databases are migrated automatically
  (table rebuild, rows preserved).
- **Web UI: Host-header validation against DNS rebinding.** All HTTP handlers
  now verify that the `Host` header is a loopback address (`127.0.0.1`,
  `localhost`, `[::1]`, with the served port). Previously GET endpoints
  (`/api/locks`, `/api/room-file/...`, `/api/settings`, ...) were readable by a
  malicious web page via DNS rebinding; the earlier CORS fix only covered
  write endpoints.
- `permissions.py`: rule matching is now platform-consistent and deliberately
  case-insensitive everywhere (`fnmatchcase` + casefold) — previously the same
  `LOCK.permissions.json` decided differently on Windows vs. POSIX, and deny
  rules could be bypassed by letter case on POSIX. Prefix rules (`rm:*`) now
  respect word boundaries and no longer capture e.g. `rmdir`.
- `lock_scan.py`: cache `filter_prefix` now matches on path-segment boundaries
  (`.../SOFTWARE` no longer leaks locks from `.../SOFTWARE-ARCHIVE`).
- `watcher/rooms.py`: notes filename validation uses `fullmatch` (an embedded
  trailing newline no longer passes).
- `watcher/web_server.py`: invalid `limit` query values return 400 instead of
  an unhandled traceback.

### Added

- `lock_create.py`: convenience script that stamps a new `LOCK*.txt` (exclusive,
  scoped, team, user, condition) with validation and overwrite protection.
- GitHub Actions CI (`.github/workflows/tests.yml`): pytest on Python
  3.10–3.13, Ubuntu + Windows.
- 19 new tests (suite 45 → 64): scanner/storage regression tests including a
  CHECK-constraint migration test, host-validation tests, permissions matching
  tests, cache filter tests, and full `lock_create.py` coverage.

## [1.4.0] - 2026-07-04

### Added

- **Condition Locks** (`LOCK.condition.txt` / `LOCK.condition.<scope>.txt`): condition-based,
  operation-scoped locks. They do NOT expire by time; they hold until the condition in the
  required `release_condition:` field is fulfilled. Prune and bulk-unlock never touch them.
  Unlike user locks, any agent may remove a condition lock once it has verifiably fulfilled
  the release condition (documenting the fulfilment when removing). New helpers in
  `lock_utils.py`: `is_condition_lock()`, `locked_operations()`; `scope_from_name()`
  understands the `condition` marker; `is_protected_lock()` now covers user + condition locks.
- **`operations:` field** (comma-separated): names the operations a lock forbids
  (e.g. `operations: publish-release, registry-upload`); everything not listed remains
  explicitly allowed. Primary use case: block a specific release/upload pipeline until
  review follow-ups are done, while normal development stays unrestricted.
- `lock_scan.py` reports type-aware status: `until condition met: ...` for condition
  locks, `user-held (no time expiry)` for user locks, and exposes `operations` /
  `release_condition` in JSON output.
- Test suite: `tests/test_condition_lock_system.py` (naming, protection, no-expiry,
  active-listing, operations parsing).

### Fixed

- **Protected locks never expire by time** in `lock_utils.is_expired()`: previously a
  nominally expired user lock dropped out of `active_locks()` / `lock_scan.py` output even
  though the spec defines user locks as valid until the user removes them. Protected locks
  (user + condition) now always report as active until removed.

---

## [1.3.0] - 2026-06-27

### Added

- **User Locks** (`LOCK.user.txt` / `LOCK.user.<scope>.txt`): user-owned full locks that are
  removed ONLY by the user (manually or via the watcher GUI). Agents and the stale-cleanup
  never touch them, even when nominally expired. New helpers in `lock_utils.py`:
  `is_user_lock()`, `is_protected_lock()`, `is_prunable()`; `scope_from_name()` understands the
  `user` marker.
- **`LOCK.permissions` permission scheme** (`permissions.py` + `LOCK_PERMISSIONS_TEMPLATE.json`):
  agent-neutral, folder-scoped allow/deny/ask rules (syntax borrowed from `.claude` —
  `Bash(...)`, `Read(...)`, `mcp__x__*`), readable by all agents. `evaluate()` precedence
  deny > ask > allow > default.
- **Bulk lock / immediate lockdown** (`bulk_lock.py`): guard-protected (`commit` flag),
  idempotent, reversible (`created_by: bulk` marker + session manifest). Never touches user
  locks — a folder holding a (even expired) user lock is treated as permanently locked.

### Changed

- `prune_stale_locks.py` now uses `is_prunable()` — user locks are never pruned.

### Notes

- Mirrored from the running `_scripts/` instance (canonical there); this module is the
  user-neutral publishable copy.

## [1.2.0] - 2026-06-19

### Added

- **Team Locks** (`LOCK.team.<host>.txt` / `LOCK.team.<scope>.<host>.txt`): new lock
  type for coordinating multiple agents within the same system. A Team Lock bundles four
  structured sections -- presence log, file/folder claims + queue, tool/MCP claims + queue,
  and messages/tips -- in a single file. Other systems treat the file as an Exclusive Lock.
- **`TEAM_LOCK_TEMPLATE.txt`**: ready-to-use template for Team Locks with all four required
  sections, inline comments, and neutral placeholders.
- **Cloud-Ready support**: Team Locks are designed for shared filesystems (OneDrive, Dropbox).
  Rename-based claiming is atomic on NTFS / most cloud-sync filesystems. Conflict-copy handling
  documented in `LOCK-SYSTEM.md`.
- `is_team_lock(name)` in `lock_utils.py`: returns `True` for `LOCK.team.*` filenames.

### Changed

- **Detection regex** updated from `^LOCK(\.[^.]+)?\.txt$` to
  `^LOCK(\.[A-Za-z0-9_-]+(\.[A-Za-z0-9_-]+)*)?\.txt$` to support multi-segment names
  (e.g. `LOCK.team.LAPTOP.txt`, `LOCK.team.frontend.SERVER-01.txt`).
- `scope_from_name()` updated: Team Locks return the correct component scope
  (or `'project'` when no component segment is present).
- `LOCK-SYSTEM.md`: added "Lock Types: Exclusive vs. Team" section with coordination rules,
  cloud-sync guidance, and conflict-copy handling.
- `README.md` (EN) and `README_de.md` (DE): added Team Lock and Cloud-Ready sections,
  updated scope convention table, updated file tree.
- `llms.txt`: added Team Lock and Cloud-Ready entries; updated `Last-checked` to 2026-06-19.

## [1.1.0] - 2026-06-16

### Added

- **`host` field** in the LOCK file format (optional): the machine/hostname that
  holds the lock, for cross-system coordination — makes visible **which** system
  locked an area. Backwards compatible: `lock_host()` accessor returns `None` when
  the field is absent. Documented in `LOCK-SYSTEM.md`, `LOCK_TEMPLATE.txt` and READMEs.
- `host_is_reachable()` stub in `prune_stale_locks.py` (prepared hook for future
  host-reachability-aware stale cleanup, e.g. via Tailscale ping; not yet active).

## [Unreleased]

### Added

- Optional `watcher/` integration: localhost daemon, SQLite-backed event/history
  store, REST API, static Web UI, room map, user lock creation, prune action,
  cache refresh, daemon heartbeat, and same-host singleton detection.
- `watcher/README.md` documenting runtime data, start commands, CLI, API, and
  scan model.

### Fixed

- Hardened watcher web API path and header handling for CodeQL path-injection
  and HTTP response-splitting findings.

### Documentation

- Added README entry tables and discovery/disambiguation context for multi-agent
  workspace locking, Codex/Claude/Gemini coordination, and `LOCK*.txt` search.
- Standardized `llms.txt` with `Last-checked`, Audience, Search Phrases, and
  Disambiguation sections.

## [1.0.0] - 2026-06-14

### Added

- `lock_utils.py` -- canonical library for LOCK file parsing, scope detection, expiry logic
- `lock_scan.py` -- read-only system-wide active-lock overview; config-driven cache output via `--write-cache`
- `prune_stale_locks.py` -- remove expired LOCK*.txt files with `--dry-run` support
- `LOCK_TEMPLATE.txt` -- copy-paste template for creating a new lock file
- `lock_roots.example.json` -- annotated example configuration with placeholder paths
- `LOCK-SYSTEM.md` -- canonical spec: lifecycle, tiers, format reference, script usage
- `tests/test_smoke.py` -- smoke tests: scope detection, expiry logic, dry-run prune
- `README.md` (EN) and `README_de.md` (DE) -- project documentation
- `SECURITY.md` -- vulnerability reporting policy
- `llms.txt` -- machine-readable project summary for LLM tools
- MIT License
