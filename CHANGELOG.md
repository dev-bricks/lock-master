# Changelog

All notable changes to this project will be documented in this file.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).
This project adheres to [Semantic Versioning](https://semver.org/).

---

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
