# TODO

## STATUS

| Category | Status | Notes |
|---|---|---|
| Release gate | PASS | Final Gate Check: 10 PASS / 0 FAIL / 0 WARN on 2026-06-19. |
| Tests | PASS | `python -X utf8 -m pytest -q` passes from the module root. |
| Documentation | READY | README, localized READMEs, SECURITY, CHANGELOG and LOCK-SYSTEM are present. |
| Integration | READY | Fits `.MODULES` as a standalone, zero-dependency coordination module for shared agent workspaces. |
| Known follow-ups | OPEN | Convenience scripts, CI and watcher polish remain backlog items below. |

## Planned

- [x] Additional language versions (es, ja, ru, zh-Hans) -- done: README_es.md, README_ja.md, README_ru.md, README_zh-Hans.md added with language switcher in all READMEs
- [ ] `lock_create.py` -- convenience script to stamp a new LOCK*.txt from the template
- [ ] Optional Telegram/webhook notification on lock expiry (prune hook)
- [ ] GitHub Actions CI: run smoke tests on push
- [ ] Watcher UI polish after longer real-world daemon runs: empty roots, very large roots, stale daemon messaging, mobile layout
- [ ] **Drift check 2026-07-03:** `watcher/web_server.py` in the private live instance
      (`_control-center/_lock_watcher/web_server.py`, ~37.7 KB) has grown well past this
      mirror's `watcher/web_server.py` (~30.6 KB) since the 2026-06-27 sync: new endpoints for
      room-stats refresh, bulk-lock/prune wiring and ticket/doc-scanner integration were added.
      `watcher/config.py` here is intentionally NOT re-synced (it uses a portable
      `LOCK_MASTER_WATCHER_DATA`/`REPO_ROOT` scheme vs. the private instance's OneDrive-specific
      parent-walk auto-discovery -- different by design, do not overwrite). Before porting the
      web_server.py delta: strip anything tied to the private control-center's ticket/doc-scanner
      paths so the portable copy stays user-neutral. Only `watcher/START.bat`'s auto-open-browser
      tweak was ported so far (2026-07-03).

## Ideas / Backlog

- [ ] `lock_status.py` -- per-project status check (exit 0 = no lock, exit 1 = locked)
- [ ] Integration example for cron-based stale cleanup
- [ ] Optional installer/launcher wrapper for `watcher/` on non-Windows systems

## Done

- [x] Portable `watcher/` integration added: localhost daemon, REST API, Web UI, SQLite runtime outside the repo (2026-06-25)
- [x] `.MODULES/README.md` entry registered for module discoverability (2026-06-21)
- [x] Initial release v1.0.0 (2026-06-14)
