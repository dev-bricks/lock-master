# TODO

## Planned

- [ ] Additional language versions (es, ja, ru, zh-Hans) -- in progress, being produced by dedicated translation agent from the EN README
- [ ] `lock_create.py` -- convenience script to stamp a new LOCK*.txt from the template
- [ ] Optional Telegram/webhook notification on lock expiry (prune hook)
- [ ] GitHub Actions CI: run smoke tests on push

## Ideas / Backlog

- [ ] `lock_status.py` -- per-project status check (exit 0 = no lock, exit 1 = locked)
- [ ] Integration example for cron-based stale cleanup

## Done

- [x] Initial release v1.0.0 (2026-06-14)
