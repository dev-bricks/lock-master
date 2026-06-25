"""Directory-Statistiken für Raum-Kacheln. Sammelt Datei-/Ordner-Counts und Größen."""

from __future__ import annotations

import os
import time
from datetime import datetime


_CODE_EXT = frozenset({
    '.py', '.js', '.ts', '.tsx', '.jsx', '.lua', '.luau', '.rs', '.go', '.java',
    '.c', '.cpp', '.h', '.hpp', '.cs', '.css', '.scss', '.html', '.htm',
    '.sh', '.ps1', '.bat', '.cmd', '.sql', '.rb', '.php', '.swift', '.kt',
    '.r', '.m', '.vue', '.svelte',
})

_HUMAN_EXT = frozenset({
    '.doc', '.docx', '.pdf', '.odt', '.rtf', '.pptx', '.ppt',
    '.xlsx', '.xls', '.pages', '.numbers', '.key',
})

_LLM_EXT = frozenset({
    '.txt', '.md', '.json', '.yaml', '.yml', '.toml', '.ini', '.cfg',
    '.csv', '.xml', '.log', '.rst', '.tex', '.bib', '.jsonl',
})

_MEDIA_EXT = frozenset({
    '.png', '.jpg', '.jpeg', '.gif', '.svg', '.webp', '.bmp', '.ico', '.tif', '.tiff',
    '.mp4', '.mp3', '.wav', '.webm', '.avi', '.mov', '.mkv', '.flac', '.ogg',
    '.obj', '.fbx', '.glb', '.gltf',
})


def classify(ext: str) -> str:
    ext = ext.lower()
    if ext in _CODE_EXT:
        return 'code'
    if ext in _HUMAN_EXT:
        return 'human'
    if ext in _LLM_EXT:
        return 'llm'
    if ext in _MEDIA_EXT:
        return 'media'
    return 'other'


def scan_room(abs_path: str, skipped_dirs: set[str] | None = None,
              timeout: float = 30.0) -> dict:
    """Scannt ein Verzeichnis rekursiv via os.scandir und liefert Statistiken."""
    if skipped_dirs is None:
        skipped_dirs = set()

    result = {
        'file_count': 0,
        'folder_count': 0,
        'total_bytes': 0,
        'type_code': 0,
        'type_human': 0,
        'type_llm': 0,
        'type_media': 0,
        'type_other': 0,
        'scanned_at': datetime.now().isoformat(timespec='seconds'),
    }

    deadline = time.monotonic() + timeout
    stack = [abs_path]

    while stack:
        if time.monotonic() > deadline:
            break
        current = stack.pop()
        try:
            with os.scandir(current) as it:
                for entry in it:
                    if time.monotonic() > deadline:
                        break
                    try:
                        if entry.is_dir(follow_symlinks=False):
                            if entry.name not in skipped_dirs:
                                result['folder_count'] += 1
                                stack.append(entry.path)
                        elif entry.is_file(follow_symlinks=False):
                            result['file_count'] += 1
                            try:
                                st = entry.stat(follow_symlinks=False)
                                attrs = getattr(st, 'st_file_attributes', 0)
                                if not (attrs & 0x00400000):
                                    result['total_bytes'] += st.st_size
                            except OSError:
                                pass
                            ext = os.path.splitext(entry.name)[1]
                            cat = classify(ext)
                            result[f'type_{cat}'] += 1
                    except OSError:
                        continue
        except OSError:
            continue

    return result


def scan_all_rooms(rooms: list[dict], skipped_dirs: set[str] | None = None,
                   timeout_per_room: float = 30.0) -> dict[str, dict]:
    """Scannt alle Räume und gibt ein Dict room_key → stats zurück."""
    results = {}
    for room in rooms:
        key = room.get('key', '')
        abs_path = room.get('abs_path', '')
        if not abs_path or not os.path.isdir(abs_path):
            continue
        try:
            results[key] = scan_room(abs_path, skipped_dirs, timeout_per_room)
        except Exception:
            continue
    return results
