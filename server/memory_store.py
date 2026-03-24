import json
import os
from typing import Dict, List

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MEMORY_FILE = os.path.join(BASE_DIR, "memory_store.json")


def _load() -> Dict[str, List[str]]:
    if not os.path.exists(MEMORY_FILE):
        return {}
    try:
        with open(MEMORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _save(data: Dict[str, List[str]]):
    print("saving memory file:", MEMORY_FILE)
    print("saving memory data:", data)
    with open(MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def get_session_memories(session_id: str) -> List[str]:
    data = _load()
    return data.get(session_id, [])


def add_session_memories(session_id: str, new_memories: List[str]):
    if not session_id or not new_memories:
        return

    data = _load()
    old_memories = data.get(session_id, [])

    merged = old_memories[:]
    for item in new_memories:
        item = item.strip()
        if item and item not in merged:
            merged.append(item)

    data[session_id] = merged[:20]
    _save(data)

def delete_session_memories(session_id: str):
    if not session_id:
        return

    data = _load()
    if session_id in data:
        del data[session_id]
        _save(data)