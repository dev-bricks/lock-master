# lock-master Watcher

Optional local daemon, REST API, and browser UI for `lock-master`.

The watcher does not replace the `LOCK*.txt` protocol. Lock files remain the
authoritative source of truth; SQLite, cache files, and the UI are derived views.

## Layout

The watcher lives in `watcher/` and imports the canonical lock-master scripts
from the repository root:

- `../lock_scan.py`
- `../lock_utils.py`
- `../prune_stale_locks.py`
- `../lock_roots.json`

`lock_roots.json` is intentionally local and ignored by Git.

## Runtime Data

Runtime data is stored outside the repository by default:

```text
~/.lock_master_watcher/watcher.db
~/.lock_master_watcher/daemon_status.json
~/.lock_master_watcher/rooms.json
~/.lock_master_watcher/user_profile.json
~/.lock_master_watcher/central_files/
```

Override the directory with:

```bash
LOCK_MASTER_WATCHER_DATA=/path/to/runtime python watcher/web_server.py
```

Keeping SQLite outside synced project folders avoids WAL and cloud-sync conflicts.

## Start

From the repository root:

```bash
python watcher/lock_watcher.py --update-cache
python watcher/web_server.py --port 8095
```

On Windows:

```bat
watcher\START.bat
```

The web UI is local-only:

```text
http://127.0.0.1:8095
```

## CLI

```bash
python watcher/cli.py status --json
python watcher/cli.py history --limit 50
python watcher/cli.py scan --update-cache
python watcher/cli.py stats
python watcher/cli.py cache
python watcher/cli.py watch --update-cache
```

## API

| Endpoint | Purpose |
|---|---|
| `GET /api/stats` | database summary |
| `GET /api/settings` | intervals, DB path, daemon status |
| `GET /api/locks?status=active|all` | lock list |
| `GET /api/lock/<id>` | lock detail with events |
| `GET /api/rooms` | configured roots as rooms |
| `GET /api/room/<key>/history` | room event history |
| `POST /api/scan` | immediate full scan |
| `POST /api/prune` | run `prune_stale_locks.py` |
| `POST /api/lock` | create a lock inside configured roots |
| `GET /api/room-stats` | cached directory statistics |
| `POST /api/room-stats/refresh` | refresh directory statistics |

Write endpoints are intended for local browser use and validate local origins.

## Scan Model

- Full scan: every 60 seconds.
- Quick check of known active locks: every 20 seconds.
- Daemon heartbeat: every 5 seconds.
- Directory statistics: every 15 minutes.
- Singleton behavior: a fresh daemon on the same host is reused; a second daemon exits.
