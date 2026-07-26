r"""
permissions.py -- Kompatibilitaets-Shim (lock-master Stack)

Die Implementierung liegt seit der Stack-Zerlegung (2026-07-26) in
    permission-control/permissions.py

Diese Datei haelt die flache Einstiegsflaeche des Modulroots stabil:
`import permissions` und `python permissions.py` funktionieren unveraendert.

Kein Re-Export, sondern Selbstersetzung: das echte Modul wird unter DIESEM
Namen geladen und in sys.modules an die Stelle des Shims gesetzt. Es entsteht
also kein zweites Modulobjekt und keine Teilmenge des Namensraums -- Aufrufer
bekommen das Original (gleiche Funktionen, gleiche Konstanten, `__file__`
zeigt auf die reale Datei). Damit ist es gleichgueltig, ob ein Aufrufer den
Modulroot oder `permission-control/` auf sys.path hat.

Siehe KONZEPT-ZERLEGUNG.md, Abschnitt "Kompatibilitaets-Shims im Root".
"""

import importlib.util
import sys
from pathlib import Path

_REAL = Path(__file__).resolve().parent / "permission-control" / "permissions.py"

if not _REAL.is_file():  # pragma: no cover - Schutz vor Teilentnahme des Roots
    raise ImportError(
        f"lock-master: Teilmodul permission-control fehlt (erwartet: {_REAL}). "
        "Der Shim im Modulroot setzt den vollstaendigen Stack voraus."
    )

_DIR = str(_REAL.parent)
if _DIR not in sys.path:
    sys.path.insert(0, _DIR)

_spec = importlib.util.spec_from_file_location(__name__, _REAL)
_module = importlib.util.module_from_spec(_spec)
sys.modules[__name__] = _module
_spec.loader.exec_module(_module)
