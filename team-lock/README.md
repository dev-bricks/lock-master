# team-lock — Platzhalter

> **Dieser Ordner enthält heute keinen Code.** Er markiert den vorgesehenen
> Platz im **lock-master**-Stack, damit die Zerlegung vollständig sichtbar ist.
> Angelegt am 2026-07-26.

| | |
|---|---|
| Stabile ID | `lock-master.team-lock` |
| Liefert | *(noch nichts — `provides` ist bewusst leer)* |
| Status | `planned` |

## Was hier einmal liegen soll

Atomare Claim-Vergabe für Agentenschwärme über `O_EXCL` — also das
wettlaufsichere „ich nehme dieses Arbeitspaket", das ein reines Dateiformat
nicht leisten kann.

Die Substanz dafür existiert bereits, aber an anderer Stelle:
`.MODULES/.ORCHESTRATION/swarm_ai/tools/team_lock.py`. Das Herauslösen ist ein
**eigener, geplanter Durchgang**.

**In diesem Lauf wurde `swarm-ai` nicht angefasst** — kein Lesen mit
Änderungsabsicht, kein Verschieben, kein Commit. Wer den Umzug durchführt,
prüft dort zuerst `git status`: vorgefundene Fremdänderungen bekommen einen
eigenen Commit.

## Nicht verwechseln: Team Locks gibt es schon

Team Locks als **Dateiformat** (`LOCK.team.<host>.txt`, koordiniert Agenten
eines Systems intern und blockiert andere Systeme) sind vollständig
implementiert — in [`../pure-locking/`](../pure-locking/), zusammen mit
`TEAM_LOCK_TEMPLATE.txt`.

Dieses Teilmodul ergänzt später nur die **atomare Vergabe**. Wer heute Team
Locks nutzen will, braucht `pure-locking` und diesen Ordner nicht.

## Gilt auch hier: Konvention, keine Sicherheitsgrenze

Wie im gesamten Stack ist Durchsetzung freiwillige Konvention plus GUI/Audit.
Ein Claim wird technisch nicht erzwungen. `O_EXCL` macht die *Vergabe*
wettlaufsicher, nicht die *Einhaltung*.

## Zerlegungsbeschluss

`../KONZEPT-ZERLEGUNG.md` im Modulroot.
