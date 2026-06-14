# Security Policy

## Supported Versions

| Version | Supported |
|---------|-----------|
| 1.x     | Yes       |

## Reporting a Vulnerability

If you discover a security vulnerability, please report it responsibly:

1. **Do not open a public issue.**
2. **Use GitHub Private Vulnerability Reporting:**
   `Security` → `Advisories` → `New draft security advisory`
3. Include a description, reproduction steps, and potential impact.

If private vulnerability reporting is not enabled in this repository,
contact the maintainer through GitHub directly and do not publish details
in a public issue.

## Scope

- File system access: the scripts read and optionally delete `LOCK*.txt` files
  in directories listed in `lock_roots.json`. An attacker controlling that
  config file could point the scripts at unintended directories.
- `lock_roots.json` should not be world-writable.
- `prune_stale_locks.py` deletes files -- use `--dry-run` to preview before
  running in automated contexts.

## Response Time

For smaller solo projects, response times may vary. Critical issues will be
prioritised. Please allow reasonable time before public disclosure.
