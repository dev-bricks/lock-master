"""Konfiguration für den lock-master Watcher."""

from __future__ import annotations

import os
import sys
from pathlib import Path

# Pfad-Konstanten
WATCHER_DIR: Path = Path(__file__).resolve().parent
REPO_ROOT: Path = WATCHER_DIR.parent
SCRIPTS_DIR: Path = REPO_ROOT

# DB außerhalb synchronisierter Projektordner halten (WAL-Sidecars + Sync = Korruptionsrisiko)
_DATA_ENV = "LOCK_MASTER_WATCHER_DATA"
_LOCAL_DATA_DIR: Path = Path(os.environ.get(_DATA_ENV, Path.home() / ".lock_master_watcher")).expanduser()
_LOCAL_DATA_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH: Path = _LOCAL_DATA_DIR / "watcher.db"
DAEMON_STATUS_PATH: Path = _LOCAL_DATA_DIR / "daemon_status.json"

# Intervalle in Sekunden
FULL_SCAN_INTERVAL: int = 60
CHECK_INTERVAL: int = 20

# Repo-Root zum Python-Path hinzufügen, damit lock_utils und lock_scan importierbar sind
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import lock_scan as _lock_scan


def load_scan_config() -> dict:
    """Wrapper um lock_scan.load_config() mit dem Standard-Roots-File."""
    return _lock_scan.load_config(_lock_scan.DEFAULT_ROOTS_FILE)
