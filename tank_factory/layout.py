"""Чтение схемы цеха из factory_layout.txt."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .entities import Cell, Conveyor, Part, PartKind

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_LAYOUT_PATH = PROJECT_ROOT / "factory_layout.txt"

# Символы сетки (см. README и factory_layout.txt).
WALL = "#"
FLOOR = "."
DRONE = "D"
ASSEMBLY = "S"
CHASSIS = "H"
TURRET = "B"
CANNON = "N"

# C из методички = конвейер вправо; стрелки задают направление явно.
CONVEYOR_DIRS: dict[str, tuple[int, int]] = {
    "C": (1, 0),
    ">": (1, 0),
    "<": (-1, 0),
    "^": (0, -1),
    "v": (0, 1),
}

PART_CHARS: dict[str, PartKind] = {
    CHASSIS: PartKind.CHASSIS,
    TURRET: PartKind.TURRET,
    CANNON: PartKind.CANNON,
}

GRID_CHARS = set(CONVEYOR_DIRS) | set(PART_CHARS) | {WALL, FLOOR, DRONE, ASSEMBLY}


class LayoutError(ValueError):
    """Файл уровня есть, но формат неверный."""


@dataclass
class LayoutData:
    columns: int
    rows: int
    walls: set[Cell]
    conveyors: list[Conveyor]
    parts: list[Part]
    drone_start: Cell
    assembly_position: Cell


def _is_grid_line(line: str) -> bool:
    return len(line) >= 3 and all(ch in GRID_CHARS for ch in line)


def parse_layout_text(text: str, source_name: str = "layout") -> LayoutData:
    """Превращает текст конфига в стены, конвейеры, детали и точки старта."""
    raw_lines = text.splitlines()
    grid_rows: list[str] = []
    part_overlays: list[tuple[PartKind, int, int]] = []

    for line_no, raw in enumerate(raw_lines, start=1):
        line = raw.strip()
        if not line:
            continue
        # Комментарии: "# текст" или одиночная "#".
        if line == "#" or line.startswith("# "):
            continue
        if line.upper().startswith("PART "):
            parts = line.split()
            if len(parts) != 4:
                raise LayoutError(
                    f"{source_name}:{line_no}: ожидается PART <H|B|N> <x> <y>, получено: {raw!r}"
                )
            _, kind_char, x_text, y_text = parts
            kind_char = kind_char.upper()
            if kind_char not in PART_CHARS:
                raise LayoutError(
                    f"{source_name}:{line_no}: неизвестная деталь {kind_char!r}, допустимы H, B, N"
                )
            try:
                grid_x = int(x_text)
                grid_y = int(y_text)
            except ValueError as exc:
                raise LayoutError(
                    f"{source_name}:{line_no}: координаты детали должны быть целыми числами"
                ) from exc
            part_overlays.append((PART_CHARS[kind_char], grid_x, grid_y))
            continue

        if _is_grid_line(line):
            grid_rows.append(line)
            continue

        raise LayoutError(f"{source_name}:{line_no}: непонятная строка: {raw!r}")

    if not grid_rows:
        raise LayoutError(f"{source_name}: в файле нет строк сетки")

    columns = len(grid_rows[0])
    rows = len(grid_rows)
    if any(len(row) != columns for row in grid_rows):
        raise LayoutError(f"{source_name}: все строки сетки должны быть одной длины")

    walls: set[Cell] = set()
    conveyors: list[Conveyor] = []
    parts: list[Part] = []
    drone_start: Cell | None = None
    assembly_position: Cell | None = None

    for grid_y, row in enumerate(grid_rows):
        for grid_x, ch in enumerate(row):
            cell = (grid_x, grid_y)
            if ch == WALL:
                walls.add(cell)
            elif ch == FLOOR:
                pass
            elif ch == DRONE:
                if drone_start is not None:
                    raise LayoutError(f"{source_name}: старт дрона задан дважды")
                drone_start = cell
            elif ch == ASSEMBLY:
                if assembly_position is not None:
                    raise LayoutError(f"{source_name}: платформа сборки задана дважды")
                assembly_position = cell
            elif ch in CONVEYOR_DIRS:
                dx, dy = CONVEYOR_DIRS[ch]
                conveyors.append(Conveyor(grid_x, grid_y, dx, dy))
            elif ch in PART_CHARS:
                parts.append(Part(PART_CHARS[ch], grid_x, grid_y))
            else:
                raise LayoutError(f"{source_name}: неизвестный символ {ch!r} в ({grid_x}, {grid_y})")

    for kind, grid_x, grid_y in part_overlays:
        if not (0 <= grid_x < columns and 0 <= grid_y < rows):
            raise LayoutError(f"{source_name}: PART вне поля: ({grid_x}, {grid_y})")
        if (grid_x, grid_y) in walls:
            raise LayoutError(f"{source_name}: PART на стене: ({grid_x}, {grid_y})")
        parts.append(Part(kind, grid_x, grid_y))

    if drone_start is None:
        raise LayoutError(f"{source_name}: не найден символ D (старт дрона)")
    if assembly_position is None:
        raise LayoutError(f"{source_name}: не найден символ S (сборка)")

    return LayoutData(
        columns=columns,
        rows=rows,
        walls=walls,
        conveyors=conveyors,
        parts=parts,
        drone_start=drone_start,
        assembly_position=assembly_position,
    )


def load_layout(path: Path) -> LayoutData:
    """Читает файл уровня. FileNotFoundError пробрасывается наружу."""
    path = Path(path)
    text = path.read_text(encoding="utf-8")
    return parse_layout_text(text, source_name=str(path))
