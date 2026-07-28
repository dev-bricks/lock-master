r"""
lock_status.py -- Kompatibilitaets-Shim (lock-master Stack)

Die Implementierung liegt seit der Stack-Zerlegung (2026-07-26) in
    pure-locking/lock_status.py

Diese Datei haelt die flache Einstiegsflaeche des Modulroots stabil:
`import lock_status` und `python lock_status.py` funktionieren unveraendert.
"""

import importlib.util
import sys
from pathlib import Path

_REAL = Path(__file__).resolve().parent / "pure-locking" / "lock_status.py"

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
