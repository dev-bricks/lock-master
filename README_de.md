# lock-master

[EN](README.md) | **DE** | [ES](README_es.md) | [JA](README_ja.md) | [RU](README_ru.md) | [ZH](README_zh-Hans.md)

**Portables, config-gesteuertes Datei-Sperrsystem für Multi-Agenten-Projektkoordination.**

lock-master bietet ein leichtgewichtiges, abhängigkeitsfreies Sperrprotokoll auf Basis von Klartextdateien. Eine `LOCK*.txt`-Datei in einem Projektordner signalisiert, dass das Projekt oder eine Komponente gerade in Bearbeitung ist -- kein Agent, keine Automation und kein autonomer Loop verändert diesen Bereich, solange eine gültige, nicht abgelaufene Sperre existiert.

---

## Features

- **Scope-basiertes Sperren:** `LOCK.txt` sperrt das gesamte Projekt; `LOCK.<scope>.txt` sperrt eine Komponente. Mehrere Agenten können parallel an verschiedenen Scopes desselben Projekts arbeiten.
- **Auto-Verfall:** jede Sperre hat eine konfigurierbare `expires_after`-Dauer (Standard 24h). Ein Cleanup-Script entfernt vergessene Sperren.
- **Read-only-Scan:** `lock_scan.py` listet alle aktiven Sperren über alle konfigurierten Roots, ohne Dateien zu verändern.
- **Markdown-Cache:** `lock_scan.py --write-cache` schreibt eine `LOCK-CACHE.md` für einen schnellen Überblick ohne Scan.
- **Dry-run-Prune:** `prune_stale_locks.py --dry-run` zeigt vorab, was entfernt würde.
- **Keine Abhängigkeiten:** reine Python-Standardbibliothek (3.10+).
- **Config-gesteuert:** alle Roots, Tiefenbegrenzungen, Skip-Verzeichnisse und Cache-Ziele liegen in `lock_roots.json` -- keine hartkodieren Pfade im Code.

---

## Schnellstart

### 1. Scripts kopieren

```
lock_utils.py
lock_scan.py
prune_stale_locks.py
LOCK_TEMPLATE.txt
```

In ein Verzeichnis deiner Wahl legen (z. B. `scripts/`).

### 2. `lock_roots.json` erstellen

`lock_roots.example.json` kopieren, zu `lock_roots.json` umbenennen und die Platzhalter-Pfade durch echte Projektpfade ersetzen. Die Datei wird von `.gitignore` ausgeschlossen (sie enthält lokale absolute Pfade).

```json
{
  "default_max_depth": 4,
  "shallow_depth": 2,
  "skip_dirs": [".git", ".venv", "node_modules", "__pycache__", "build", "dist"],
  "roots": [
    { "path": "/pfad/zu/projekt-a" },
    { "path": "/pfad/zu/projekt-b" },
    { "path": "/pfad/zu/grossem-baum", "shallow": true }
  ],
  "caches": [
    {
      "name": "systemweit",
      "path": "/pfad/zu/scripts/LOCK-CACHE.md"
    }
  ]
}
```

### 3. Sperre anlegen

`LOCK_TEMPLATE.txt` in den Projektordner kopieren, Felder ausfüllen und in `LOCK.txt` (oder `LOCK.<scope>.txt` für Komponenten-Sperren) umbenennen:

```
owner: mein-agent
created: 2026-06-14T10:00
expires_after: 24h
mode: hard
purpose: Auth-Modul refaktorieren
```

### 4. Aktive Sperren anzeigen

```bash
python lock_scan.py
python lock_scan.py --json
```

### 5. Abgelaufene Sperren entfernen

```bash
# Vorschau (löscht nichts):
python prune_stale_locks.py --dry-run

# Tatsächlich entfernen:
python prune_stale_locks.py
```

### 6. Cache aktualisieren

```bash
python lock_scan.py --write-cache
```

Schreibt `LOCK-CACHE.md` gemäß den Einträgen im `"caches"`-Schlüssel von `lock_roots.json`.

---

## Lock-Dateiformat

Klartext, eine `key: value`-Einstellung pro Zeile. Zeilen mit `#` sind Kommentare.

| Feld                | Pflicht | Beispiel             | Bedeutung |
|---------------------|---------|----------------------|-----------|
| `owner`             | ja      | `mein-agent`         | Wer hält die Sperre. |
| `created`           | ja      | `2026-06-14T10:00`   | ISO-Zeitstempel; Basis für Verfallsberechnung. |
| `expires_after`     | optional | `24h`, `90m`, `2d`  | Dauer-String. Standard: `24h`. |
| `release_condition` | optional | `PR gemergt`        | Freitext: wann kann die Sperre freigegeben werden. |
| `mode`              | optional | `hard` \| `soft`    | `hard` = keine Änderungen (Standard); `soft` = Lesen/Hinweis ok. |
| `purpose`           | optional | `Feature X hinzufügen` | Freitext-Beschreibung der laufenden Arbeit. |
| `scope`             | optional | `frontend`           | Nur informativ; der **Dateiname** ist autoritativ. |

Fehlt `created` oder ist nicht parsebar, wird die Datei-mtime als Fallback verwendet.

---

## Scope-Konvention

| Dateiname            | Erkannter Scope | Was gesperrt ist |
|----------------------|-----------------|------------------|
| `LOCK.txt`           | `project`       | Gesamtes Projektverzeichnis |
| `LOCK.api.txt`       | `api`           | Nur die `api`-Komponente |
| `LOCK.frontend.txt`  | `frontend`      | Nur die `frontend`-Komponente |
| `LOCK.my_scope.txt`  | `my_scope`      | Beliebig benannter Teilbereich |

Erkennungsregex: `^LOCK(\.[^.]+)?\.txt$` (case-insensitive).

---

## Lebenszyklus

```
BEACHTEN  -->  CLAIMEN  -->  FREIGEBEN
```

1. **BEACHTEN:** Vor Arbeitsbeginn an einem Projekt oder einer Komponente prüfen, ob eine aktive `LOCK*.txt` für den betroffenen Bereich existiert. Wenn ja und nicht abgelaufen: anderes Projekt wählen oder warten.
2. **CLAIMEN:** eigene Lock-Datei nach Vorlage anlegen (`owner`, `created`, `expires_after`, `purpose`).
3. **FREIGEBEN:** die **selbst angelegte Lock-Datei löschen**, wenn fertig. Aktives Freigeben durch den Ersteller ist Pflicht; der `expires_after`-Timeout ist nur ein Sicherheitsnetz für vergessene Sperren. Bei längerer Laufzeit `created` erneuern, damit die Sperre nicht vorzeitig verfällt.

---

## Konfigurationsreferenz (`lock_roots.json`)

| Schlüssel           | Typ      | Standard | Beschreibung |
|---------------------|----------|----------|--------------|
| `default_max_depth` | int      | `4`      | Maximale Rekursionstiefe ab jedem Root. |
| `shallow_depth`     | int      | `2`      | Tiefe für Roots mit `"shallow": true`. |
| `skip_dirs`         | string[] | `[]`     | Verzeichnisnamen, die komplett übersprungen werden (inkl. Unterbaum). |
| `roots`             | object[] | `[]`     | Liste von `{ "path": "...", "shallow": true/false }`. |
| `caches`            | object[] | `[]`     | Cache-Ziele: `{ "name", "path", "filter_prefix?" }`. |

**Cache-Eintrags-Felder:**

| Schlüssel       | Pflicht | Beschreibung |
|-----------------|---------|--------------|
| `name`          | ja      | Anzeigename, der als Cache-Titel verwendet wird. |
| `path`          | ja      | Absoluter Pfad, in den `LOCK-CACHE.md` geschrieben wird. |
| `filter_prefix` | optional | Nur Locks einschließen, deren Pfad mit diesem Präfix beginnt. |

Fehlt `"caches"`, schreibt `--write-cache` eine einzige `LOCK-CACHE.md` neben `lock_scan.py`.

---

## Python-API

```python
from pathlib import Path
import lock_utils

projekt = Path("/pfad/zu/meinem-projekt")

# Vor Arbeitsbeginn prüfen
aktiv = lock_utils.active_locks(projekt)
if aktiv:
    print(f"Gesperrt: {aktiv}")
else:
    print("Frei zum Arbeiten.")

# Eine konkrete Lock-Datei parsen
data = lock_utils.parse_lock_file(projekt / "LOCK.txt")
print(data["owner"], data["created"])

# Verfall prüfen
from datetime import datetime
abgelaufen = lock_utils.is_expired(projekt / "LOCK.txt", now=datetime.now())
```

---

## Tests ausführen

```bash
python -m pytest tests/ -v
```

Erfordert `pytest` (`pip install pytest`).

---

## Dateistruktur

```
lock-master/
├── lock_utils.py           # Kernbibliothek: Parsen, Scope, Verfall
├── lock_scan.py            # CLI: aktive Sperren auflisten, Cache schreiben
├── prune_stale_locks.py    # CLI: abgelaufene Sperren entfernen
├── LOCK_TEMPLATE.txt       # Vorlage für neue Lock-Dateien
├── lock_roots.example.json # Annotiertes Beispiel-Config
├── LOCK-SYSTEM.md          # Kanonische Spec und Lebenszyklus-Referenz
├── tests/
│   └── test_smoke.py       # Smoke-Tests
├── LICENSE                 # MIT
├── CHANGELOG.md
├── TODO.md
├── SECURITY.md
├── llms.txt
└── VERSION
```

---

## Anforderungen

- Python 3.10+
- Keine Drittanbieter-Abhängigkeiten (nur Standardbibliothek)
- Für Tests: `pytest`

---

## Lizenz

MIT -- Copyright (c) 2026 Lukas Geiger. Siehe [LICENSE](LICENSE).
