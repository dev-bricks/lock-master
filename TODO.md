# TODO

## STATUS

| Category | Status | Notes |
|---|---|---|
| Release gate | PASS | Final Gate Check: 10 PASS / 0 FAIL / 0 WARN on 2026-06-19. |
| Tests | PASS | `python -X utf8 -m pytest -q` passes from the module root. |
| Documentation | READY | README, localized READMEs, SECURITY, CHANGELOG and LOCK-SYSTEM are present. |
| Integration | READY | Fits `.MODULES` as a standalone, zero-dependency coordination module for shared agent workspaces. |
| Known follow-ups | OPEN | Convenience scripts and CI remain backlog items below. |

## Planned

- [x] Additional language versions (es, ja, ru, zh-Hans) -- done: README_es.md, README_ja.md, README_ru.md, README_zh-Hans.md added with language switcher in all READMEs
- [ ] `lock_create.py` -- convenience script to stamp a new LOCK*.txt from the template
- [ ] Optional Telegram/webhook notification on lock expiry (prune hook)
- [ ] GitHub Actions CI: run smoke tests on push

## Ideas / Backlog

- [ ] `lock_status.py` -- per-project status check (exit 0 = no lock, exit 1 = locked)
- [ ] Integration example for cron-based stale cleanup

## Done

- [x] Initial release v1.0.0 (2026-06-14)
