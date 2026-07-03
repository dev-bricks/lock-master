# TODO

## STATUS

| Category | Status | Notes |
|---|---|---|
| Release gate | PASS | Final Gate Check: 10 PASS / 0 FAIL / 0 WARN on 2026-06-19. |
| Tests | PASS | `python -X utf8 -m pytest -q` passes from the module root. |
| Documentation | READY | README, localized READMEs, SECURITY, CHANGELOG and LOCK-SYSTEM are present. |
| Integration | READY | Fits `.MODULES` as a standalone, zero-dependency coordination module for shared agent workspaces. |
| Known follow-ups | OPEN | Convenience scripts, CI and watcher polish remain backlog items below. |

## Review 2026-07-04 (Modul-Review-Loop, Subagent-Review — alle Funde gefixt, v1.4.1)

- [x] **(hoch)** Watcher-Daemon crashte bei jedem Scan mit existierendem Lock —
  scanner.py nutzte 5 in diesem Repo nicht existierende lock_utils-Helper
  (Drift wie beim web_server.py-Fall). Helper portiert, Daemon-Loop zusätzlich
  mit try/except abgesichert, Scanner-Regressionstests ergänzt.
- [x] **(hoch)** locks-Tabelle CHECK kannte 'user'/'condition' nicht →
  IntegrityError; Schema erweitert + Auto-Migration (Table-Rebuild) für Alt-DBs.
- [x] **(hoch)** GET-Endpunkte ohne Host-Validierung → DNS-Rebinding-Datenleck;
  Host-Header-Check (Loopback only) für ALLE Methoden.
- [x] **(mittel)** permissions.py plattformabhängiges fnmatch + rm:*-matcht-rmdir;
  jetzt fnmatchcase+casefold (überall case-insensitiv) + Wortgrenze.
- [x] **(niedrig)** lock_scan filter_prefix ohne Segmentgrenze; rooms.py
  match→fullmatch; web_server limit-Parsing → 400.
- [ ] **(Folge)** Watcher-Tests decken weiter nur Helper/Module ab — ein
  Integrationstest, der den HTTP-Server wirklich startet (echte GET/POST gegen
  127.0.0.1), fehlt noch.
- [ ] **(Folge)** Dieselben Funde in der privaten Live-Instanz
  (`_control-center/_lock_watcher`) prüfen: deren lock_utils hat die Helper
  (kein Scanner-Crash), aber CHECK-Constraint und fehlende Host-Validierung
  stammen aus gemeinsamer Abstammung und sind dort vermutlich AUCH offen.
  Beim nächsten _lock_watcher-Einsatz portieren.

## Planned

- [x] Additional language versions (es, ja, ru, zh-Hans) -- done: README_es.md, README_ja.md, README_ru.md, README_zh-Hans.md added with language switcher in all READMEs
- [x] `lock_create.py` -- convenience script to stamp a new LOCK*.txt from the template (done 2026-07-04: exclusive/scoped/team/user/condition, Validierung, Überschreibschutz, 9 Tests, README-Zeile EN/DE — Locale-READMEs es/ja/ru/zh noch ohne die neue Zeile)
- [ ] Optional Telegram/webhook notification on lock expiry (prune hook)
- [x] GitHub Actions CI: run smoke tests on push (done 2026-07-04: pytest-Matrix 3.10–3.13 auf ubuntu+windows)
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
