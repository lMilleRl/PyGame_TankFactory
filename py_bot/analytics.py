"""Разбор выгрузок игры: layout, save, scores."""

from __future__ import annotations

import csv
import json
from pathlib import Path

from .config import ALLOWED_LAYOUT_CHARS, LAYOUT_PATH, SAVE_PATH, SCORES_PATH


def validate_layout_text(text: str) -> tuple[bool, str]:
    """Проверяет символы layout. C, B, S обязательны к приёму по методичке."""
    lines = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line == "#" or line.startswith("# ") or line.upper().startswith("PART "):
            continue
        lines.append(line)
    if not lines:
        return False, "В файле нет строк сетки"
    width = len(lines[0])
    if width < 3:
        return False, "Слишком узкая сетка"
    for line in lines:
        if len(line) != width:
            return False, "Строки сетки разной длины"
        bad = sorted({ch for ch in line if ch not in ALLOWED_LAYOUT_CHARS})
        if bad:
            return False, f"Недопустимые символы: {''.join(bad)}"
    has_s = any("S" in line for line in lines)
    if not has_s:
        return False, "Нет символа S (сборка)"
    return True, f"OK: {len(lines)}x{width}"


def load_layout_stats(path: Path | None = None) -> dict:
    target = Path(path) if path is not None else LAYOUT_PATH
    if not target.is_file():
        return {"exists": False}
    text = target.read_text(encoding="utf-8")
    ok, message = validate_layout_text(text)
    conveyors = 0
    parts = 0
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line == "#" or line.startswith("# "):
            continue
        if line.upper().startswith("PART "):
            parts += 1
            continue
        if all(ch in ALLOWED_LAYOUT_CHARS for ch in line):
            conveyors += sum(1 for ch in line if ch in "C><^v")
            parts += sum(1 for ch in line if ch in "HBN")
    return {
        "exists": True,
        "valid": ok,
        "message": message,
        "conveyors": conveyors,
        "parts": parts,
        "path": str(target.name),
    }


def load_save_stats(path: Path | None = None) -> dict:
    target = Path(path) if path is not None else SAVE_PATH
    if not target.is_file():
        return {"exists": False}
    raw = json.loads(target.read_text(encoding="utf-8"))
    turns = int(raw.get("turn_count", 0))
    stack = raw.get("assembly_stack", [])
    parts_done = len(stack)
    # Эффективность конвейера: детали на ход (больше = лучше).
    efficiency = round(parts_done / turns, 4) if turns > 0 else 0.0
    return {
        "exists": True,
        "turns": turns,
        "parts_assembled": parts_done,
        "status": raw.get("status", ""),
        "efficiency": efficiency,
        "drone": raw.get("drone", {}),
    }


def load_scores(path: Path | None = None) -> list[dict]:
    target = Path(path) if path is not None else SCORES_PATH
    if not target.is_file():
        return []
    with target.open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    for row in rows:
        try:
            row["efficiency"] = float(row.get("efficiency") or 0)
            row["turns"] = int(float(row.get("turns") or 0))
            row["parts_assembled"] = int(float(row.get("parts_assembled") or 0))
        except ValueError:
            row["efficiency"] = 0.0
            row["turns"] = 0
            row["parts_assembled"] = 0
    return rows


def top_by_efficiency(limit: int = 10, path: Path | None = None) -> list[dict]:
    """Рейтинг: efficiency = собранные_детали / ходы (выше лучше)."""
    rows = load_scores(path)
    rows.sort(key=lambda r: (-r["efficiency"], r["turns"], r.get("player_name", "")))
    return rows[:limit]


def player_stats(player_name: str, path: Path | None = None) -> dict:
    name = player_name.strip().lower()
    rows = [r for r in load_scores(path) if r.get("player_name", "").strip().lower() == name]
    if not rows:
        return {"found": False, "player_name": player_name}
    best = min(rows, key=lambda r: r["turns"])
    avg_eff = round(sum(r["efficiency"] for r in rows) / len(rows), 4)
    return {
        "found": True,
        "player_name": player_name,
        "games": len(rows),
        "best_turns": best["turns"],
        "avg_efficiency": avg_eff,
        "last_efficiency": rows[-1]["efficiency"],
    }
