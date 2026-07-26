# permission-control

Teilmodul des **lock-master**-Stacks. Enthält das agent-neutrale, ordner-scoped
Rechteschema `LOCK.permissions.json` — welche Aktionen in einem Projektordner
erlaubt, verboten oder rückfragepflichtig sind.

| | |
|---|---|
| Stabile ID | `lock-master.permission-control` |
| Liefert | `control.permissions` |
| Abhängigkeiten | keine (nur `fnmatch`, `json`, `re`, `pathlib`) |
| Python | ≥ 3.10 |

## Inhalt

```
permissions.py                  Parse- und Auswertungslogik
LOCK_PERMISSIONS_TEMPLATE.json  Vorlage zum Kopieren in einen Projektordner
```

## Nutzung

```python
import permissions

perm = permissions.load_permissions(project_dir)     # None, wenn keine Datei da ist
if perm:
    entscheidung = permissions.evaluate(perm, "claude", "Bash(rm -rf x)")
    # -> "allow" | "deny" | "ask"
```

Präzedenz: **`deny` > `ask` > `allow` > `default`**. Die Syntax ist an
`.claude/settings.json` angelehnt (`Bash(...)`, `Read(...)`, `mcp__vendor__tool`),
gilt aber agentenübergreifend und ordnerbezogen — sie ist nicht
Claude-Code-spezifisch.

Autoritativ ist der **Ablageort** der Datei, nicht das Feld `scope` darin.

## Was `permission-control` **nicht** ist: eine Sandbox

Das ist der wichtigste Satz dieser Datei. Durchsetzung ist **freiwillige
Konvention** plus GUI/Audit, genau wie bei `LOCK*.txt`. Dieses Modul liefert
ausschließlich Parse- und Auswertungslogik. Es hält keinen Prozess auf, fängt
keinen Syscall ab und kann von jedem Agenten ignoriert werden, der es schlicht
nicht liest.

Eine `deny`-Regel ist eine **Aussage**, keine Schranke. Wer eine erzwungene
Grenze braucht, braucht Dateisystemrechte, Container oder eine echte Sandbox.

## Was bei Teilentnahme fehlt

Wer nur diesen Ordner entnimmt, bekommt **Regeln ohne Sperren**.

- **`pure-locking` fehlt** — `LOCK*.txt` samt Anlegen, Scannen, Prunen und
  Watcher. Ohne das gibt es keinen Mechanismus, der einem zweiten Agenten
  überhaupt mitteilt, dass jemand an einem Ordner arbeitet.
- **`team-lock` fehlt** — atomare `O_EXCL`-Claims für Agentenschwärme.

Zwischen Recht und Lock gibt es bewusst **keine Schiedslogik**. Liegen eine
aktive `LOCK.txt` und eine `LOCK.permissions.json` mit `"default": "allow"`
nebeneinander, ist heute nicht definiert, was gilt — jeder Agent entscheidet es
für sich. Wer diese Frage beantwortet, sollte sie im Stack `lock-master`
beantworten, nicht hier und schon gar nicht in den Konsumenten: sonst entsteht
die Verrechnungslogik mehrfach und unterschiedlich.

## Zerlegungsbeschluss

`../KONZEPT-ZERLEGUNG.md` im Modulroot.
