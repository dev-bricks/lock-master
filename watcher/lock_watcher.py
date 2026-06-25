"""
Lock-File-Watcher: Daemon mit Dual-Scan-Rhythmus.

Aufruf:
  PYTHONIOENCODING=utf-8 python lock_watcher.py
  PYTHONIOENCODING=utf-8 python lock_watcher.py --once
  PYTHONIOENCODING=utf-8 python lock_watcher.py --update-cache

Ohne Argumente: Daemon-Modus (Endlosloop).
--once: genau ein Full-Scan, dann beenden.
--update-cache: LOCK-CACHE.md nach jedem Full-Scan aktualisieren.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import signal
import socket
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

# Eigene Module (gleicher Ordner)
sys.path.insert(0, str(Path(__file__).resolve().parent))
import config
import dir_stats
import rooms as rooms_mod
import scanner
import storage

# lock_scan aus dem lock-master Repo-Root für optionale Cache-Updates
sys.path.insert(0, str(config.SCRIPTS_DIR))

STATS_SCAN_INTERVAL: int = 900  # 15 Minuten
HEARTBEAT_INTERVAL: int = 5
STALE_DAEMON_SECONDS: int = max(180, config.FULL_SCAN_INTERVAL * 3)


def _now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


def load_daemon_status() -> dict | None:
    """Lädt den letzten Daemon-Heartbeat."""
    try:
        return json.loads(config.DAEMON_STATUS_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def _pid_is_running(pid: int) -> bool:
    if pid <= 0:
        return False
    if os.name == "nt":
        try:
            result = subprocess.run(
                ["tasklist", "/FI", f"PID eq {pid}", "/FO", "CSV", "/NH"],
                capture_output=True,
                text=True,
                timeout=2,
            )
        except (OSError, subprocess.TimeoutExpired):
            return False
        if result.returncode != 0:
            return False
        for row in csv.reader(result.stdout.splitlines()):
            if len(row) >= 2 and row[1] == str(pid):
                return True
        return False
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    return True


def _status_age_seconds(status: dict, now: datetime | None = None) -> int | None:
    last_seen = status.get("last_seen")
    if not last_seen:
        return None
    try:
        seen = datetime.fromisoformat(str(last_seen))
    except ValueError:
        return None
    now = now or datetime.now()
    return int((now - seen).total_seconds())


def _daemon_status_is_fresh(status: dict | None) -> bool:
    if not status:
        return False
    if status.get("host") != socket.gethostname():
        return False
    try:
        pid = int(status.get("pid", 0))
    except (TypeError, ValueError):
        return False
    age = _status_age_seconds(status)
    if age is None or age > STALE_DAEMON_SECONDS:
        return False
    return _pid_is_running(pid)


def get_running_daemon_status() -> dict | None:
    status = load_daemon_status()
    return status if _daemon_status_is_fresh(status) else None


def _write_daemon_status(update_cache: bool, started_at: str) -> None:
    status = {
        "pid": os.getpid(),
        "host": socket.gethostname(),
        "started_at": started_at,
        "last_seen": _now_iso(),
        "update_cache": update_cache,
        "db_path": str(config.DB_PATH),
    }
    tmp_path = config.DAEMON_STATUS_PATH.with_suffix(".tmp")
    tmp_path.write_text(json.dumps(status, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp_path.replace(config.DAEMON_STATUS_PATH)


def _clear_daemon_status(pid: int) -> None:
    status = load_daemon_status()
    if not status:
        return
    try:
        current_pid = int(status.get("pid", 0))
    except (TypeError, ValueError):
        current_pid = 0
    if current_pid == pid:
        try:
            config.DAEMON_STATUS_PATH.unlink()
        except OSError:
            pass


def _run_full_scan(db: storage.LockDB, cfg: dict, update_cache: bool) -> dict:
    """Führt einen Full-Scan durch, reconciled Ergebnisse mit DB.
    Gibt Stats-Dict zurück: {new, modified, expired, deleted, total}."""
    started = _now_iso()
    scan_results = scanner.full_scan(cfg)
    scanned_paths = {r["path"] for r in scan_results}

    stats = {"new": 0, "modified": 0, "expired": 0, "deleted": 0, "total": len(scan_results)}

    for lock_data in scan_results:
        path = lock_data["path"]
        existing = db.get_lock_by_path(path)

        if existing is None:
            lock_id = db.upsert_lock(lock_data)
            db.record_event(lock_id, "detected")
            stats["new"] += 1
        elif existing.get("status") == "deleted":
            lock_data["status"] = "active"
            lock_id = db.upsert_lock(lock_data)
            db.record_event(lock_id, "renewed")
            stats["new"] += 1
        elif existing.get("status") == "expired" and not lock_data.get("is_expired"):
            lock_data["status"] = "active"
            lock_id = db.upsert_lock(lock_data)
            db.record_event(lock_id, "renewed")
            stats["new"] += 1
        else:
            lock_id = existing["id"]
            changed = (
                existing.get("owner") != lock_data.get("owner")
                or existing.get("purpose") != lock_data.get("purpose")
                or existing.get("raw_content") != lock_data.get("raw_content")
            )
            if changed:
                db.upsert_lock(lock_data)
                db.record_event(lock_id, "modified")
                stats["modified"] += 1
            else:
                db.upsert_lock(lock_data)

            if lock_data.get("is_expired") and existing.get("status") == "active":
                db.mark_expired(lock_id, _now_iso())
                stats["expired"] += 1

    # Aktive DB-Locks die im Scan nicht auftauchen → gelöscht
    known_active = db.get_known_active_paths()
    for known_path in known_active:
        if known_path not in scanned_paths:
            lock_entry = db.get_lock_by_path(known_path)
            if lock_entry and lock_entry.get("status") == "active":
                # Full-scans may miss a subtree temporarily (cloud-sync/FS errors).
                # Verify the specific file before turning an active lock into deleted.
                check_result = scanner.check_paths([known_path]).get(known_path)
                if check_result is not None:
                    lock_id = db.upsert_lock(check_result)
                    if check_result.get("is_expired"):
                        db.mark_expired(lock_id, _now_iso())
                        stats["expired"] += 1
                    continue
                db.mark_deleted(lock_entry["id"], _now_iso())
                stats["deleted"] += 1

    finished = _now_iso()
    db.record_scan("full", started, finished, stats)

    if update_cache:
        try:
            import cache_writer
            cache_writer.generate_cache(db)
        except Exception as exc:
            print(f"[{_now_iso()}] Cache-Update fehlgeschlagen: {exc}", file=sys.stderr)

    return stats


def _run_quick_check(db: storage.LockDB) -> None:
    """Prüft nur bekannte aktive Locks auf Änderungen/Löschungen."""
    known_active = db.get_known_active_paths()
    if not known_active:
        return

    results = scanner.check_paths(known_active)
    changed = False

    for path, data in results.items():
        lock_entry = db.get_lock_by_path(path)
        if lock_entry is None:
            continue
        lock_id = lock_entry["id"]

        if data is None:
            if lock_entry.get("status") == "active":
                db.mark_deleted(lock_id, _now_iso())
                print(f"[{_now_iso()}] Quick-Check: gelöscht → {path}")
                changed = True
        elif data.get("is_expired") and lock_entry.get("status") == "active":
            db.mark_expired(lock_id, _now_iso())
            print(f"[{_now_iso()}] Quick-Check: abgelaufen → {path}")
            changed = True

    _ = changed  # Logging erfolgt inline oben


def _run_stats_scan(db: storage.LockDB) -> None:
    """Scannt Verzeichnis-Statistiken für alle Räume."""
    all_rooms = rooms_mod._get_rooms()
    cfg = config.load_scan_config()
    skipped = set(cfg.get("skip_dirs", []))
    stats_map = dir_stats.scan_all_rooms(all_rooms, skipped)
    db.upsert_room_stats_batch(stats_map)


def run_daemon(update_cache: bool) -> None:
    """Endlosloop mit Dual-Scan-Rhythmus."""
    existing = get_running_daemon_status()
    if existing is not None:
        print(
            f"[{_now_iso()}] Lock-Watcher läuft bereits "
            f"(PID {existing.get('pid')}, Host {existing.get('host')}, "
            f"letzter Heartbeat {existing.get('last_seen')})."
        )
        return

    started_at = _now_iso()
    _write_daemon_status(update_cache, started_at)
    cfg = config.load_scan_config()
    db = storage.LockDB(config.DB_PATH)

    shutdown_requested = False

    def _handle_signal(signum, frame):
        nonlocal shutdown_requested
        shutdown_requested = True

    signal.signal(signal.SIGINT, _handle_signal)
    signal.signal(signal.SIGTERM, _handle_signal)

    print(f"[{_now_iso()}] Lock-Watcher gestartet. "
          f"Full-Scan alle {config.FULL_SCAN_INTERVAL}s, Quick-Check alle {config.CHECK_INTERVAL}s.")

    last_full_scan: float = 0.0
    last_check: float = 0.0
    last_stats_scan: float = 0.0
    last_heartbeat: float = 0.0

    try:
        while not shutdown_requested:
            now = time.monotonic()

            if now - last_heartbeat >= HEARTBEAT_INTERVAL:
                _write_daemon_status(update_cache, started_at)
                last_heartbeat = time.monotonic()

            if now - last_full_scan >= config.FULL_SCAN_INTERVAL:
                stats = _run_full_scan(db, cfg, update_cache)
                last_full_scan = time.monotonic()
                print(
                    f"[{_now_iso()}] Full-Scan: {stats['total']} aktiv, "
                    f"{stats['new']} neu, {stats['modified']} geändert, "
                    f"{stats['expired']} abgelaufen, {stats['deleted']} gelöscht"
                )
                # Quick-Check-Timer nach Full-Scan zurücksetzen (kein Doppelcheck)
                last_check = time.monotonic()

            elif now - last_check >= config.CHECK_INTERVAL:
                _run_quick_check(db)
                last_check = time.monotonic()

            now2 = time.monotonic()
            if now2 - last_stats_scan >= STATS_SCAN_INTERVAL:
                try:
                    _run_stats_scan(db)
                    last_stats_scan = time.monotonic()
                    print(f"[{_now_iso()}] Stats-Scan abgeschlossen.")
                except Exception as exc:
                    print(f"[{_now_iso()}] Stats-Scan fehlgeschlagen: {exc}", file=sys.stderr)

            time.sleep(1)

    finally:
        db.close()
        _clear_daemon_status(os.getpid())
        print(f"[{_now_iso()}] Lock-Watcher beendet.")


def run_once(update_cache: bool) -> None:
    """Genau ein Full-Scan, dann beenden."""
    cfg = config.load_scan_config()
    db = storage.LockDB(config.DB_PATH)
    try:
        print(f"[{_now_iso()}] Lock-Watcher --once: starte Full-Scan.")
        stats = _run_full_scan(db, cfg, update_cache)
        print(
            f"[{_now_iso()}] Full-Scan abgeschlossen: {stats['total']} aktiv, "
            f"{stats['new']} neu, {stats['modified']} geändert, "
            f"{stats['expired']} abgelaufen, {stats['deleted']} gelöscht"
        )
    finally:
        db.close()


def main() -> int:
    parser = argparse.ArgumentParser(description="Lock-File-Watcher Daemon")
    parser.add_argument(
        "--once",
        action="store_true",
        help="Genau einen Full-Scan ausführen und beenden.",
    )
    parser.add_argument(
        "--update-cache",
        action="store_true",
        help="LOCK-CACHE.md nach jedem Full-Scan aktualisieren.",
    )
    args = parser.parse_args()

    if args.once:
        run_once(args.update_cache)
    else:
        run_daemon(args.update_cache)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
