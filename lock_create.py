r"""
lock_create.py -- Kompatibilitaets-Shim (lock-master Stack)

Die Implementierung liegt seit der Stack-Zerlegung (2026-07-26) in
    pure-locking/lock_create.py

Diese Datei haelt die flache Einstiegsflaeche des Modulroots stabil:
`import lock_create` und `python lock_create.py` funktionieren unveraendert -- das ist
die Zusage aus KONZEPT-ZERLEGUNG.md, Abschnitt "KRITISCH".

Kein Re-Export, sondern Selbstersetzung: das echte Modul wird unter DIESEM
Namen geladen und in sys.modules an die Stelle des Shims gesetzt. Es entsteht
kein zweites Modulobjekt und keine Teilmenge des Namensraums -- Aufrufer
bekommen das Original (gleiche Funktionen, gleiche Konstanten, `__file__`
zeigt auf die reale Datei). Wird der Shim als Skript gestartet, ist
`__name__ == "__main__"`, sodass der `main()`-Block des Originals greift.

pure-locking/ wird dabei an den Anfang von sys.path gesetzt, damit die flachen
Nachbar-Importe des Originals (z. B. `import lock_utils` in lock_scan.py)
dort und nicht wieder ueber die Shims aufloesen.
"""

import importlib.util
import sys
from pathlib import Path

_REAL = Path(__file__).resolve().parent / "pure-locking" / "lock_create.py"

if not _REAL.is_file():  # pragma: no cover - Schutz vor Teilentnahme des Roots
    raise ImportError(
        f"lock-master: Teilmodul pure-locking fehlt (erwartet: {_REAL}). "
        "Der Shim im Modulroot setzt den vollstaendigen Stack voraus."
    )

_DIR = str(_REAL.parent)
if _DIR not in sys.path:
    sys.path.insert(0, _DIR)

_spec = importlib.util.spec_from_file_location(__name__, _REAL)
_module = importlib.util.module_from_spec(_spec)
sys.modules[__name__] = _module
_spec.loader.exec_module(_module)
