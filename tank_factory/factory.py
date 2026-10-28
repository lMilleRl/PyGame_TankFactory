from collections import Counter
from collections.abc import Iterable
from pathlib import Path

from .constants import (
    ASSEMBLY_ORDER,
    ASSEMBLY_POSITION,
    CONVEYOR_LAYOUT,
    DEFAULT_DRONE_START,
    DEFAULT_WALLS,
    GRID_COLUMNS,
    GRID_ROWS,
    INITIAL_PARTS,
)
from .entities import Cell, Conveyor, Drone, FactoryStatus, Part, PartKind, PART_NAMES
from .layout import DEFAULT_LAYOUT_PATH, LayoutData, LayoutError, load_layout


class Factory:
    """Состояние цеха и правила пошаговой сборки танка."""

    def __init__(
        self,
        columns: int = GRID_COLUMNS,
        rows: int = GRID_ROWS,
        drone_start: Cell | None = None,
        assembly_position: Cell | None = None,
        parts: Iterable[Part] | None = None,
        conveyors: Iterable[Conveyor] | None = None,
        walls: Iterable[Cell] | None = None,
    ) -> None:
        if columns < 3 or rows < 3:
            raise ValueError("Размер сетки должен быть не меньше 3 x 3.")

        is_default_board = columns == GRID_COLUMNS and rows == GRID_ROWS
        self.columns = columns
        self.rows = rows
        self.drone = Drone(*(drone_start or (DEFAULT_DRONE_START if is_default_board else (1, 1))))
        self.assembly_position = assembly_position or (
            ASSEMBLY_POSITION if is_default_board else (columns - 2, rows - 2)
        )

        if parts is None:
            part_specs = INITIAL_PARTS if is_default_board else ()
            self.parts = [Part(kind, grid_x, grid_y) for kind, grid_x, grid_y in part_specs]
        else:
            self.parts = [Part(part.kind, part.grid_x, part.grid_y) for part in parts]

        if conveyors is None:
            conveyor_specs = CONVEYOR_LAYOUT if is_default_board else ()
            conveyor_list = [Conveyor(*spec) for spec in conveyor_specs]
        else:
            conveyor_list = list(conveyors)
        self.conveyors = {conveyor.position: conveyor for conveyor in conveyor_list}
        if len(self.conveyors) != len(conveyor_list):
            raise ValueError("На одной клетке не может быть несколько конвейеров.")

        self.walls = set(walls) if walls is not None else set(
            DEFAULT_WALLS if is_default_board else self._border_walls(columns, rows)
        )
        self.assembly_stack: list[PartKind] = []
        self.turn_count = 0
        self.status = FactoryStatus.ACTIVE
        self.message = "Конвейеры везут детали к зонам ожидания у сборочной платформы."
        self._validate_layout()

    @classmethod
    def from_layout_data(cls, layout: LayoutData) -> "Factory":
        return cls(
            columns=layout.columns,
            rows=layout.rows,
            drone_start=layout.drone_start,
            assembly_position=layout.assembly_position,
            parts=layout.parts,
            conveyors=layout.conveyors,
            walls=layout.walls,
        )

    @classmethod
    def from_layout_file(cls, path: Path | None = None) -> "Factory":
        """Загружает уровень из factory_layout.txt."""
        layout_path = Path(path) if path is not None else DEFAULT_LAYOUT_PATH
        return cls.from_layout_data(load_layout(layout_path))

    @classmethod
    def create_for_game(cls, path: Path | None = None) -> "Factory":
        """
        Старт игры: читает конфиг уровня.
        При отсутствии или порче файла возвращает встроенную схему и пишет сообщение.
        """
        layout_path = Path(path) if path is not None else DEFAULT_LAYOUT_PATH
        try:
            factory = cls.from_layout_file(layout_path)
            factory.message = f"Уровень загружен из {layout_path.name}."
            return factory
        except FileNotFoundError:
            factory = cls()
            factory.message = f"Файл уровня не найден ({layout_path.name}), использована встроенная схема."
            return factory
        except (LayoutError, ValueError, OSError) as exc:
            factory = cls()
            factory.message = f"Ошибка формата уровня: {exc}. Использована встроенная схема."
            return factory

    @staticmethod
    def _border_walls(columns: int, rows: int) -> set[Cell]:
        return (
            {(x, 0) for x in range(columns)}
            | {(x, rows - 1) for x in range(columns)}
            | {(0, y) for y in range(rows)}
            | {(columns - 1, y) for y in range(rows)}
        )

    def _validate_layout(self) -> None:
        if not self._inside(self.drone.position) or self.drone.position in self.walls:
            raise ValueError("Начальная позиция дрона должна быть свободной клеткой поля.")
        if not self._inside(self.assembly_position) or self.assembly_position in self.walls:
            raise ValueError("Сборочная платформа должна находиться внутри цеха.")
        if any(not self._inside(wall) for wall in self.walls):
            raise ValueError("Стена находится за пределами игрового поля.")

        part_positions = [part.position for part in self.parts]
        if len(set(part_positions)) != len(part_positions):
            raise ValueError("Две детали не могут занимать одну клетку.")
        if any(not self._inside(position) or position in self.walls for position in part_positions):
            raise ValueError("Деталь должна находиться на свободной клетке поля.")
        if any(not self._inside(position) or position in self.walls for position in self.conveyors):
            raise ValueError("Конвейер должен находиться на свободной клетке поля.")

    def _inside(self, position: Cell) -> bool:
        grid_x, grid_y = position
        return 0 <= grid_x < self.columns and 0 <= grid_y < self.rows

    @property
    def drone_position(self) -> Cell:
        return self.drone.position

    @property
    def required_part(self) -> PartKind | None:
        if len(self.assembly_stack) >= len(ASSEMBLY_ORDER):
            return None
        return ASSEMBLY_ORDER[len(self.assembly_stack)]

    @property
    def assembly_indices(self) -> list[int]:
        return [part_kind.value for part_kind in self.assembly_stack]

    def get_part_at(self, position: Cell) -> Part | None:
        return next((part for part in self.parts if part.position == position), None)

    def move_drone(self, direction_x: int, direction_y: int) -> bool:
        """Двигает дрон на одну соседнюю клетку и завершает ход конвейеров."""
        if self.status is FactoryStatus.WON:
            return False
        if abs(direction_x) + abs(direction_y) != 1:
            raise ValueError("За один шаг дрон может пройти только одну клетку по прямой.")

        target = (
            self.drone.grid_x + direction_x,
            self.drone.grid_y + direction_y,
        )
        if not self._inside(target) or target in self.walls:
            self.message = "Путь перекрыт стеной или границей цеха."
            return False

        self.drone.grid_x, self.drone.grid_y = target
        self._finish_turn("Дрон переместился на одну клетку.")
        return True

    def interact(self) -> bool:
        """Берёт деталь, кладёт её на пол или устанавливает на платформу."""
        if self.status is FactoryStatus.WON:
            return False

        if self.drone.carried_part is None:
            part = self.get_part_at(self.drone.position)
            if part is None:
                self.message = "На этой клетке нет детали для захвата."
                return False
            self.parts.remove(part)
            self.drone.carried_part = part
            self._finish_turn(f"Дрон поднял деталь «{PART_NAMES[part.kind]}».")
            return True

        part = self.drone.carried_part
        if self.drone.position == self.assembly_position:
            if part.kind is not self.required_part:
                expected_name = PART_NAMES[self.required_part] if self.required_part is not None else ""
                self.message = f"Нарушен порядок: следующая деталь — «{expected_name}»."
                return False

            self.assembly_stack.append(part.kind)
            self.drone.carried_part = None
            if self.is_assembly_complete():
                self.status = FactoryStatus.WON
                message = "Танк собран: последовательность [шасси, башня, орудие] верна."
            else:
                message = f"Деталь «{PART_NAMES[part.kind]}» установлена на платформу."
            self._finish_turn(message)
            return True

        if self.get_part_at(self.drone.position) is not None:
            self.message = "Клетка занята другой деталью — положить сюда нельзя."
            return False

        part.grid_x, part.grid_y = self.drone.position
        self.parts.append(part)
        self.drone.carried_part = None
        self._finish_turn(f"Дрон положил деталь «{PART_NAMES[part.kind]}».")
        return True

    def is_assembly_complete(self) -> bool:
        """Проверяет, что индексы стека точно равны [0, 1, 2]."""
        return self.assembly_indices == [part_kind.value for part_kind in ASSEMBLY_ORDER]

    def _finish_turn(self, message: str) -> None:
        self.turn_count += 1
        moved_parts = self._advance_conveyors()
        if moved_parts:
            message = f"{message} По конвейерам перемещено деталей: {moved_parts}."
        self.message = message

    def _advance_conveyors(self) -> int:
        """Сдвигает детали одновременно, чтобы результат не зависел от порядка списка."""
        positions = [part.position for part in self.parts]
        intended_moves: dict[int, Cell] = {}

        for index, part in enumerate(self.parts):
            conveyor = self.conveyors.get(part.position)
            if conveyor is None:
                continue
            destination = conveyor.destination()
            if self._inside(destination) and destination not in self.walls:
                intended_moves[index] = destination

        destinations = Counter(intended_moves.values())
        intended_moves = {
            index: destination
            for index, destination in intended_moves.items()
            if destinations[destination] == 1
        }

        # Если одна деталь остановилась, она остаётся препятствием для следующих деталей.
        while True:
            stationary_positions = {
                position for index, position in enumerate(positions) if index not in intended_moves
            }
            blocked = {
                index
                for index, destination in intended_moves.items()
                if destination in stationary_positions
            }
            if not blocked:
                break
            for index in blocked:
                intended_moves.pop(index)

        for index, destination in intended_moves.items():
            self.parts[index].grid_x, self.parts[index].grid_y = destination
        return len(intended_moves)
