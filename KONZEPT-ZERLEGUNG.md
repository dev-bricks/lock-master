# KONZEPT — lock-master wird ein Stack aus drei Teilmodulen

> Entscheidung Lukas Geiger, 2026-07-26. Erarbeitet in Session „OPUS WORKSTATION".
> Status: **beschlossen, Umsetzung begonnen.** Diese Datei ist die Begründung;
> der Umsetzungsstand steht am Ende.

## Beschluss

```
lock-master  (Stack — wird als EIN Modul ausgeliefert)
  ├─ pure-locking        LOCK*.txt: Anlegen, Scannen, Prunen, Watcher/GUI
  ├─ permission-control  permissions.py, LOCK.permissions.json
  └─ team-lock           atomare O_EXCL-Claims (herausgelöst aus swarm-ai)
```

Abgeleitete Stacks:

```
comalock      = lock-master + coma        (lokal, offline, heute)
comaroshambo  = roshambo    + coma        (verteilt, Cloud, später)
swarm-ai      = Skilldokumente + team-lock (wird mitausgeliefert)
```

**Die Funktion ändert sich nicht.** Es ändert sich die Kapselung: Teilbereiche werden
einzeln versionierbar und einzeln entnehmbar. Ein Stack ist in diesem Ökosystem auch
als ein Modul lesbar und auslieferbar; das Manifest liegt bei, damit ein Nutzer
Teilordner gezielt aktualisieren kann.

Der Name `lock-master` bleibt und wandert auf den Stack: „Master" heißt, dass alles
Wichtige enthalten ist — wer nur das Sperren braucht, entnimmt `pure-locking`.

## Warum die Zerlegung risikoarm ist: die Naht existiert bereits

Geprüft am 2026-07-26 im Code, nicht vermutet:

- `permissions.py` importiert **ausschließlich Standardbibliothek** (`fnmatch`, `json`,
  `re`, `pathlib`). Kein Import aus `lock_utils`, `lock_scan` oder sonst etwas
  Lock-Bezogenem.
- Sein Docstring sagt es selbst: ein Rechtesystem, „das **neben** den `LOCK*.txt` in
  einem Projektordner liegt".
- Umgekehrt enthalten `lock_scan.py` und `lock_utils.py` **null** Treffer auf
  „permission".

Die Kopplung ist heute null. Geteilt werden nur ein Dateinamenspräfix (`LOCK.`) und
ein Ordner. Die Zerlegung schneidet also nichts auf, sondern legt eine vorhandene
Naht frei.

## Offene Frage, die durch die Zerlegung erst sichtbar wird

**Zwischen Lock und Recht gibt es keine Schiedslogik — und das ist bisher niemandem
aufgefallen, weil beides in einem Modul und einem Ordner steckt.**

Liegt in einem Projekt eine aktive `LOCK.txt` **und** eine `LOCK.permissions.json` mit
`"default": "allow"` — was gilt? Heute entscheidet das jeder Agent für sich; die beiden
Auswertungen sehen einander nie.

Das ist **bewusst als offene Frage vertagt**, nicht mitgelöst. Wer sie beantwortet,
sollte sie im Stack beantworten (`lock-master`), nicht in den Teilmodulen und schon gar
nicht in den Konsumenten — sonst entsteht die Verrechnungslogik mehrfach und
unterschiedlich.

## Gilt für alle Teile: Konvention, keine Sicherheitsgrenze

Aus dem Docstring von `permissions.py`: „Durchsetzung = **freiwillige Konvention** +
GUI/Audit (analog `LOCK*.txt`)."

Weder Locks noch Permissions werden technisch erzwungen. Das gehört in die README
**jedes** Teilmoduls, sonst importiert jemand `permission-control` und hält es für eine
Sandbox.

**Teilentnahme-Warnung:** Wer nur `pure-locking` zieht, bekommt Sperren ohne
Deny-Regeln. Weil beide nie interagiert haben, geht dabei keine Verrechnung verloren —
die Regeln selbst aber schon. Gehört in die README von `pure-locking`.

## KRITISCH — die deployten Einstiegspunkte dürfen nicht brechen

`~/OneDrive/_scripts/lock_scan.py` und `~/OneDrive/_scripts/prune_stale_locks.py` sind
**deployte Kopien** dieses Moduls (Plan-D-Muster §10.4). Sie werden mit **absolutem
Pfad** als Pflicht-Lockcheck genannt in:

- `~/CLAUDE.md` (Abschnitt „Projekt-Sperren")
- `.TOPICS/CLAUDE.md`
- `_scripts/LOCK-SYSTEM.md`
- `_control-center/_tasks/CLAUDE.md` (Loop-Ablauf, Schritt 2)

Ändert die Zerlegung, was diese Dateien importieren, **bricht der Lockcheck jedes
Agenten im ganzen System — und zwar still**, weil ein fehlgeschlagener Scan wie „keine
Locks" aussieht.

**Abnahmekriterium:** Nach jedem Umbauschritt den Befehl aus `~/CLAUDE.md` **wörtlich**
ausführen und bestätigen, dass er scannt. Die beiden Einstiegspunkte bleiben stabil,
unabhängig von der inneren Paketierung.

## Ausdrücklich NICHT Teil dieses Umbaus

- **Kein Plan-D-Umzug.** lock-master liegt in OneDrive; die Migration nach
  `C:\_Local_DEV\repos\` ist laut `.MCP/TODO.md` ein eigener, geplanter Durchgang, weil
  MCP-Profilpfade darauf zeigen. Beides zugleich zu tun ließe keinen sauberen Rückweg.
- **Kein TOM_lm-Anschluss.** `_TOM-lm` / `build-your-users-mind` hält Willensbildung
  (Prosa, Belegkette, Konfidenz, „🔴 = eskalieren statt raten"), lock-master hält
  Durchsetzung (Muster, deterministische Auswertung). Die Richtung ist
  **TOM_lm → lock-master, niemals umgekehrt**, und der Übertrag bleibt ein bewusster
  Akt. Würde eine Vorhersage mit mittlerer Konfidenz automatisch zu einer
  `allow`-Regel, wäre eine Vermutung unsichtbar in eine Berechtigung gewaschen — in der
  `LOCK.permissions.json` steht keine Konfidenz mehr. Zusätzlich liegt auf
  `build-your-users-mind` bis ca. 12.08.2026 ein **User-Lock** (Judging-Hold).
- **Kein Roshambo-Anschluss jetzt.** Roshambo ersetzt später die Speicherung
  (`LOCK*.txt` → DB-Tabelle). Die Packliste `.STACKS/NEW-STACK_ROSHAMBO.md` führt
  `lock-master` heute in einer Zeile mit „Lease-Semantik … (`deny > ask > allow`)" —
  das vermischt beide Teile. **Nachzuziehen nach der Zerlegung:** `pure-locking`
  liefert die Leases, `permission-control` die Auswertungsordnung.

## Umsetzungsstand

- [x] Konzept beschlossen und begründet (diese Datei)
- [ ] `ellmos-module.v2.json` je Teilmodul
- [ ] Physische Trennung `pure-locking` / `permission-control` / `team-lock`
- [ ] `team-lock` aus `swarm-ai/tools/team_lock.py` herauslösen (vorher dort
      `git status` prüfen — Fremdänderungen bekommen einen eigenen Commit)
- [ ] Abnahmetest: Lockcheck-Befehl aus `~/CLAUDE.md` wörtlich, muss scannen
- [ ] `modules.catalog.json` neu erzeugen (Registry-Drift nicht vergrößern)
- [ ] `NEW-STACK_COMALOCK.md` → `validate_composition.py` → `stacks.catalog.json`
      → `STACK-MAPPING.md`
