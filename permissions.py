r"""
permissions.py — Agent-neutrales Rechte-Schema fuer LOCK.permissions(.json)

Zweck: Ein ordner-scoped, von ALLEN Agenten (Claude, Codex, Gemini, Kimi, ...)
lesbares Rechtesystem, das neben den LOCK*.txt in einem Projektordner liegt.
Die Syntax ist an `.claude/settings.json` angelehnt (allow/deny/ask + Pattern
wie `Bash(...)`, `Read(...)`, `mcp__vendor__tool`), aber agent-uebergreifend und
ordner-bezogen (welche Projekte/Aktionen sind tabu), NICHT Claude-Code-spezifisch.

Durchsetzung = freiwillige Konvention + GUI/Audit (analog LOCK*.txt). Diese Datei
liefert nur die Parse-/Eval-Logik; kein Agent wird hierdurch technisch gezwungen.

Schema (LOCK.permissions.json):
  {
    "format": "lock-permissions-v1",
    "scope": "project",                 # informativ; autoritativ ist der Ablageort
    "owner": "user",
    "default": "allow",                 # "allow" | "deny" | "ask" — wenn keine Regel matcht
    "rules": {
      "allow": ["Read(**)", "Bash(python:*)"],
      "deny":  ["Bash(rm:*)", "Write(**/CREDENTIALS/**)", "mcp__*__delete*"],
      "ask":   ["Write(**)"]
    },
    "applies_to_agents": ["claude", "codex", "gemini", "kimi", "*"]
  }

Aktions-Strings (was ein Agent tun will), gleiche Form wie die Regeln:
  "Read(a.txt)", "Bash(rm -rf x)", "Write(/p/CREDENTIALS/x)", "mcp__fc__delete_file", "WebSearch"

Praezedenz: deny > ask > allow > default.
"""

from __future__ import annotations

import fnmatch
import json
import re
from pathlib import Path

PERMISSIONS_FILENAMES = ("LOCK.permissions.json", "LOCK.permissions.txt")

_ACTION_RE = re.compile(r"^\s*([A-Za-z0-9_*?\[\]-]+)\s*(?:\((.*)\)\s*)?$", re.DOTALL)


def _split(token: str) -> tuple[str, str | None]:
    """Zerlegt 'Tool(arg)' -> ('Tool', 'arg'); 'Tool' -> ('Tool', None)."""
    m = _ACTION_RE.match(token.strip())
    if not m:
        return token.strip(), None
    tool = m.group(1)
    arg = m.group(2)
    return tool, (arg if arg is not None else None)


def _arg_matches(action_arg: str | None, rule_arg: str | None) -> bool:
    """Argument-Matching zwischen Aktion und Regel.

    - Regel ohne Argument -> matcht jede Aktion desselben Tools.
    - Regel-Arg '**' -> matcht alles.
    - Regel-Arg mit ':' -> Praefix-Match auf den Teil vor ':' (z. B. 'rm:*' matcht
      'rm -rf x'; angelehnt an .claude 'Bash(cmd:*)').
    - sonst -> glob (fnmatch); '**' wird wie '*' behandelt.
    """
    if rule_arg is None:
        return True
    if action_arg is None:
        action_arg = ""
    if rule_arg.strip() in ("**", "*"):
        return True
    if ":" in rule_arg:
        prefix = rule_arg.split(":", 1)[0].strip()
        return action_arg.strip().startswith(prefix)
    pattern = rule_arg.replace("**", "*")
    return fnmatch.fnmatch(action_arg, pattern)


def matches(action: str, rule: str) -> bool:
    """True, wenn der Aktions-String von der Regel erfasst wird."""
    a_tool, a_arg = _split(action)
    r_tool, r_arg = _split(rule)
    if not fnmatch.fnmatch(a_tool, r_tool):
        return False
    return _arg_matches(a_arg, r_arg)


def applies_to(perm: dict, agent: str) -> bool:
    """True, wenn das Permission-Objekt fuer diesen Agenten gilt."""
    agents = perm.get("applies_to_agents") or ["*"]
    return "*" in agents or agent in agents


def evaluate(perm: dict, agent: str, action: str) -> str:
    """Wertet eine Aktion gegen ein Permission-Objekt aus.

    Returns 'allow' | 'deny' | 'ask'. Praezedenz deny > ask > allow > default.
    Gilt das Objekt nicht fuer den Agenten (applies_to_agents), wird der
    default zurueckgegeben (das Objekt entfaltet keine Wirkung)."""
    default = perm.get("default", "allow")
    if not applies_to(perm, agent):
        return default
    rules = perm.get("rules") or {}
    for decision in ("deny", "ask", "allow"):
        for rule in rules.get(decision, []) or []:
            if matches(action, rule):
                return decision
    return default


def load_permissions(project_dir: Path) -> dict | None:
    """Laedt LOCK.permissions.json (oder .txt als JSON) aus einem Projektordner.
    Returns das Dict oder None, wenn keine (gueltige) Datei vorhanden ist."""
    for name in PERMISSIONS_FILENAMES:
        path = project_dir / name
        if not path.is_file():
            continue
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return None
    return None
