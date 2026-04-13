import contextlib
import json
import os
import tempfile
from typing import Dict, List

try:
    import fcntl

    _HAS_FCNTL = True
except ImportError:
    fcntl = None  # type: ignore
    _HAS_FCNTL = False

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
_DEFAULT_MEMORY = os.path.join(BASE_DIR, "memory_store.json")


def _resolve_memory_file() -> str:
    configured = (os.getenv("MEMORY_STORE_PATH") or "").strip()
    if configured:
        return os.path.abspath(configured)

    # Vercel Functions use a read-only filesystem except for /tmp.
    if os.getenv("VERCEL"):
        return os.path.join(tempfile.gettempdir(), "ai-companion-memory-store.json")

    return _DEFAULT_MEMORY


MEMORY_FILE = _resolve_memory_file()
_LOCK_FILE = f"{MEMORY_FILE}.lock"


@contextlib.contextmanager
def _file_lock():
    if not _HAS_FCNTL:
        yield
        return
    os.makedirs(os.path.dirname(MEMORY_FILE) or ".", exist_ok=True)
    with open(_LOCK_FILE, "w", encoding="utf-8") as lock_fd:
        fcntl.flock(lock_fd.fileno(), fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(lock_fd.fileno(), fcntl.LOCK_UN)


def _load() -> Dict[str, List[str]]:
    if not os.path.exists(MEMORY_FILE):
        return {}
    try:
        with open(MEMORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _save(data: Dict[str, List[str]]):
    os.makedirs(os.path.dirname(MEMORY_FILE) or ".", exist_ok=True)
    with open(MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def get_session_memories(session_id: str) -> List[str]:
    with _file_lock():
        data = _load()
        return data.get(session_id, [])


def add_session_memories(session_id: str, new_memories: List[str]):
    if not session_id or not new_memories:
        return

    with _file_lock():
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

    with _file_lock():
        data = _load()
        if session_id in data:
            del data[session_id]
            _save(data)


def set_session_memories(session_id: str, memories: List[str]):
    if not session_id:
        return

    with _file_lock():
        data = _load()
        cleaned = []

        for item in memories or []:
            text = str(item).strip()
            if text and text not in cleaned:
                cleaned.append(text)

        data[session_id] = cleaned[:50]
        _save(data)
