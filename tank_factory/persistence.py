"""Сохранения JSON, таблица рекордов CSV и настройка логов."""

from __future__ import annotations

import csv
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING

from .entities import FactoryStatus, Part, PartKind
from .layout import PROJECT_ROOT

if TYPE_CHECKING:
    from .factory import Factory

DEFAULT_LAYOUT_PATH = PROJECT_ROOT / "factory_layout.txt"
DEFAULT_SAVE_PATH = PROJECT_ROOT / "factory_save.json"
DEFAULT_SCORES_PATH = PROJECT_ROOT / "scores.csv"
DEFAULT_LOG_PATH = PROJECT_ROOT / "game_flight.log"

SCORE_FIELDS = ("timestamp", "player_name", "turns", "parts_assembled", "efficiency")


def setup_game_logging(log_path: Path | None = None) -> logging.Logger:
    """Пишет ключевые события в game_flight.log с timestamp."""
    path = Path(log_path) if log_path is not None else DEFAULT_LOG_PATH
    logger = logging.getLogger("tank_factory")
    logger.setLevel(logging.INFO)
    logger.handlers.clear()
    handler = logging.FileHandler(path, encoding="utf-8")
    handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
    logger.addHandler(handler)
    logger.propagate = False
    return logger


def factory_to_dict(factory: "Factory") -> dict:
    """Сериализует текущую пошаговую сессию."""
    carried = factory.drone.carried_part
    return {
        "turn_count": factory.turn_count,
        "status": factory.status.value,
        "message": factory.message,
        "drone": {
            "grid_x": factory.drone.grid_x,
            "grid_y": factory.drone.grid_y,
            "carried_part": None
            if carried is None
            else {"kind": int(carried.kind), "grid_x": carried.grid_x, "grid_y": carried.grid_y},
        },
        "parts": [
            {"kind": int(part.kind), "grid_x": part.grid_x, "grid_y": part.grid_y}
            for part in factory.parts
        ],
        "assembly_stack": [int(kind) for kind in factory.assembly_stack],
        "assembly_position": list(factory.assembly_position),
        "columns": factory.columns,
        "rows": factory.rows,
    }


def save_factory(factory: "Factory", path: Path | None = None) -> Path:
    """F5: записывает состояние сессии в factory_save.json."""
    target = Path(path) if path is not None else DEFAULT_SAVE_PATH
    payload = factory_to_dict(factory)
    payload["saved_at"] = datetime.now().isoformat(timespec="seconds")
    target.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return target


def load_factory_save(factory: "Factory", path: Path | None = None) -> None:
    """Восстанавливает дрона, детали и стек сборки поверх уже загруженного уровня."""
    target = Path(path) if path is not None else DEFAULT_SAVE_PATH
    raw = json.loads(target.read_text(encoding="utf-8"))
    apply_save_dict(factory, raw)


def apply_save_dict(factory: "Factory", raw: dict) -> None:
    """Накладывает словарь сохранения на объект Factory."""
    required = ("turn_count", "status", "drone", "parts", "assembly_stack")
    for key in required:
        if key not in raw:
            raise ValueError(f"В сохранении нет поля {key!r}")

    drone_data = raw["drone"]
    factory.drone.grid_x = int(drone_data["grid_x"])
    factory.drone.grid_y = int(drone_data["grid_y"])
    carried = drone_data.get("carried_part")
    if carried is None:
        factory.drone.carried_part = None
    else:
        factory.drone.carried_part = Part(
            PartKind(int(carried["kind"])),
            int(carried["grid_x"]),
            int(carried["grid_y"]),
        )

    factory.parts = [
        Part(PartKind(int(item["kind"])), int(item["grid_x"]), int(item["grid_y"]))
        for item in raw["parts"]
    ]
    factory.assembly_stack = [PartKind(int(kind)) for kind in raw["assembly_stack"]]
    factory.turn_count = int(raw["turn_count"])
    factory.status = FactoryStatus(raw["status"])
    factory.message = str(raw.get("message", "Состояние загружено из сохранения."))


def append_score(
    player_name: str,
    turns: int,
    parts_assembled: int,
    path: Path | None = None,
) -> Path:
    """Дописывает результат в scores.csv; заголовок создаётся при первом запуске."""
    target = Path(path) if path is not None else DEFAULT_SCORES_PATH
    name = player_name.strip() or "Игрок"
    efficiency = round(parts_assembled / turns, 4) if turns > 0 else 0.0
    row = {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "player_name": name,
        "turns": turns,
        "parts_assembled": parts_assembled,
        "efficiency": efficiency,
    }
    write_header = not target.is_file()
    with target.open("a", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=SCORE_FIELDS)
        if write_header:
            writer.writeheader()
        writer.writerow(row)
    return target


def read_scores(path: Path | None = None) -> list[dict]:
    """Читает таблицу рекордов; пустой список, если файла ещё нет."""
    target = Path(path) if path is not None else DEFAULT_SCORES_PATH
    if not target.is_file():
        return []
    with target.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))
