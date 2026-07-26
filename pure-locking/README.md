# pure-locking

Teilmodul des **lock-master**-Stacks. Enthält das Sperren selbst: `LOCK*.txt`
anlegen, scannen, prunen, in Serie setzen — plus den optionalen Watcher mit
REST-API und Web-UI.

| | |
|---|---|
| Stabile ID | `lock-master.pure-locking` |
| Liefert | `control.locks` |
| Abhängigkeiten | keine (nur Python-Standardbibliothek) |
| Python | ≥ 3.10 |

## Inhalt

```
lock_utils.py             Format-, Ablauf- und Typlogik (Exclusive/Team/User/Condition)
lock_scan.py              Read-only-Übersicht aller aktiven Locks über alle Roots
lock_create.py            Baut korrekte Dateinamen und Kopfzeilen für einen neuen Lock
prune_stale_locks.py      Entfernt abgelaufene Locks (User-Locks bleiben unangetastet)
bulk_lock.py              Sperrt/entsperrt viele Projektordner in einem Zug
watcher/                  Optionaler localhost-Daemon, REST-API, Web-UI
LOCK_TEMPLATE.txt         Vorlage für einen Exclusive Lock
TEAM_LOCK_TEMPLATE.txt    Vorlage für einen Team Lock
lock_roots.example.json   Kommentierte Beispielkonfiguration mit Platzhalterpfaden
```

## Nutzung

Die Dateien importieren einander flach und laufen direkt aus diesem Ordner:

```bash
python lock_scan.py
python lock_scan.py --json
python prune_stale_locks.py --dry-run
python watcher/lock_watcher.py --update-cache
python watcher/web_server.py --port 8095
```

`lock_roots.example.json` kopieren, zu `lock_roots.json` umbenennen und die
Platzhalterpfade durch echte Projektpfade ersetzen. `lock_roots.json` ist von
`.gitignore` erfasst, weil es lokale absolute Pfade enthält.

Aus dem Modulroot des Stacks funktionieren dieselben Aufrufe unverändert
(`python lock_scan.py`) — dort liegen Kompatibilitäts-Shims, die auf diese
Dateien zeigen.

## Was `pure-locking` **nicht** ist: eine Sicherheitsgrenze

Durchsetzung ist **freiwillige Konvention** plus GUI/Audit. Ein Lock hindert
technisch niemanden daran, eine Datei zu ändern — er teilt eine Absicht mit.
Wer eine erzwungene Grenze braucht, braucht Dateisystemrechte, keinen Lock.

## Was bei Teilentnahme fehlt

Wer nur diesen Ordner entnimmt, bekommt **Sperren ohne Deny-Regeln**.

- **`permission-control` fehlt** — das ordner-scoped Rechteschema
  `LOCK.permissions.json` (allow/deny/ask). Weil Locks und Rechte in diesem
  Stack nie miteinander interagiert haben, geht dabei **keine Verrechnung**
  verloren; die Regeln selbst aber schon. Ein Projekt, dessen Schutz auf einer
  `deny`-Regel beruht, ist danach ungeschützt, ohne dass etwas fehlschlägt.
- **`team-lock` fehlt** — atomare `O_EXCL`-Claims. Team Locks als *Dateiformat*
  (`LOCK.team.<host>.txt`) sind hier vollständig enthalten; was fehlt, ist die
  wettlaufsichere Claim-Vergabe für Agentenschwärme.

Es gibt bewusst **keine Schiedslogik** zwischen Lock und Recht: Liegen eine
aktive `LOCK.txt` und eine `LOCK.permissions.json` mit `"default": "allow"`
nebeneinander, entscheidet das heute jeder Agent für sich. Diese Frage gehört
in den Stack `lock-master`, nicht hierher.

## Kanonische Spezifikation

`../LOCK-SYSTEM.md` im Modulroot. Zerlegungsbeschluss und Begründung:
`../KONZEPT-ZERLEGUNG.md`.
