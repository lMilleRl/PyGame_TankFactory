"""JSON-сессии по user_id (stateless между перезапусками)."""

from __future__ import annotations

import json
from enum import Enum
from pathlib import Path

from .config import SESSIONS_DIR


class BotState(str, Enum):
    MENU = "MENU"
    UPLOAD = "UPLOAD"
    WAIT_NAME = "WAIT_NAME"
    BROADCAST = "BROADCAST"


def session_path(user_id: int, base: Path | None = None) -> Path:
    folder = Path(base) if base is not None else SESSIONS_DIR
    folder.mkdir(parents=True, exist_ok=True)
    return folder / f"{user_id}.json"


def load_session(user_id: int, base: Path | None = None) -> dict:
    path = session_path(user_id, base)
    if not path.is_file():
        data = {
            "user_id": user_id,
            "state": BotState.MENU.value,
            "player_name": "",
            "watch": False,
            "uploads": 0,
            "last_screen": "",
        }
        save_session(user_id, data, base)
        return data
    return json.loads(path.read_text(encoding="utf-8"))


def save_session(user_id: int, data: dict, base: Path | None = None) -> Path:
    path = session_path(user_id, base)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def set_state(user_id: int, state: BotState, base: Path | None = None) -> dict:
    data = load_session(user_id, base)
    data["state"] = state.value
    save_session(user_id, data, base)
    return data


def list_watchers(base: Path | None = None) -> list[int]:
    folder = Path(base) if base is not None else SESSIONS_DIR
    if not folder.is_dir():
        return []
    result = []
    for path in folder.glob("*.json"):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if data.get("watch"):
            result.append(int(data.get("user_id", path.stem)))
    return result
