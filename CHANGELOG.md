# Changelog

All notable changes to this project will be documented in this file.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).
This project adheres to [Semantic Versioning](https://semver.org/).

---

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
