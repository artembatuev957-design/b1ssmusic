import json
import os
from datetime import datetime
from typing import Optional

DB_FILE = "database.json"


def _load() -> dict:
    """Load database from JSON file."""
    if not os.path.exists(DB_FILE):
        return {
            "homework": {},
            "schedule": {},
            "subscribers": [],
            "schedule_file_id": None,
        }
    with open(DB_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def _save(data: dict) -> None:
    """Save database to JSON file."""
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# ── Homework ──────────────────────────────────────────────

def get_homework(subject_key: str) -> Optional[dict]:
    """Get homework for a subject."""
    db = _load()
    return db["homework"].get(subject_key)


def get_all_homework() -> dict:
    """Get all homework."""
    db = _load()
    return db["homework"]


def set_homework(subject_key: str, text: str, file_id: Optional[str] = None,
                 file_type: Optional[str] = None) -> None:
    """Set or update homework for a subject."""
    db = _load()
    db["homework"][subject_key] = {
        "text": text,
        "file_id": file_id,
        "file_type": file_type,
        "updated_at": datetime.now().strftime("%d.%m.%Y %H:%M"),
    }
    _save(db)


def clear_homework(subject_key: str) -> bool:
    """Clear homework for a subject. Returns True if existed."""
    db = _load()
    if subject_key in db["homework"]:
        del db["homework"][subject_key]
        _save(db)
        return True
    return False


def clear_all_homework() -> None:
    """Clear all homework."""
    db = _load()
    db["homework"] = {}
    _save(db)


# ── Schedule ──────────────────────────────────────────────

def get_schedule_file_id() -> Optional[str]:
    """Get the file_id of the uploaded schedule."""
    db = _load()
    return db.get("schedule_file_id")


def get_schedule_info() -> Optional[dict]:
    """Get schedule file info."""
    db = _load()
    return db.get("schedule_info")


def set_schedule(file_id: str, file_type: str, caption: Optional[str] = None) -> None:
    """Save schedule file_id."""
    db = _load()
    db["schedule_file_id"] = file_id
    db["schedule_info"] = {
        "file_id": file_id,
        "file_type": file_type,
        "caption": caption,
        "updated_at": datetime.now().strftime("%d.%m.%Y %H:%M"),
    }
    _save(db)


# ── Subscribers ───────────────────────────────────────────

def get_subscribers() -> list[int]:
    """Get all subscriber chat IDs."""
    db = _load()
    return db.get("subscribers", [])


def add_subscriber(chat_id: int) -> bool:
    """Add subscriber. Returns True if newly added."""
    db = _load()
    if chat_id not in db["subscribers"]:
        db["subscribers"].append(chat_id)
        _save(db)
        return True
    return False


def remove_subscriber(chat_id: int) -> bool:
    """Remove subscriber. Returns True if existed."""
    db = _load()
    if chat_id in db["subscribers"]:
        db["subscribers"].remove(chat_id)
        _save(db)
        return True
    return False


def subscriber_count() -> int:
    return len(get_subscribers())
