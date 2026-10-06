from dataclasses import dataclass
from enum import Enum, IntEnum
from typing import TypeAlias

Cell: TypeAlias = tuple[int, int]


class PartKind(IntEnum):
    CHASSIS = 0
    TURRET = 1
    CANNON = 2


PART_NAMES = {
    PartKind.CHASSIS: "Шасси",
    PartKind.TURRET: "Башня",
    PartKind.CANNON: "Орудие",
}

PART_SHORT_NAMES = {
    PartKind.CHASSIS: "Ш",
    PartKind.TURRET: "Б",
    PartKind.CANNON: "О",
}


class FactoryStatus(Enum):
    ACTIVE = "active"
    WON = "won"


@dataclass(slots=True)
class Part:
    """Деталь цеха с координатами в клетках сетки."""

    kind: PartKind
    grid_x: int
    grid_y: int

    @property
    def position(self) -> Cell:
        return self.grid_x, self.grid_y


@dataclass(slots=True)
class Drone:
    """Дрон-сборщик может переносить не более одной детали."""

    grid_x: int
    grid_y: int
    carried_part: Part | None = None

    @property
    def position(self) -> Cell:
        return self.grid_x, self.grid_y


@dataclass(frozen=True, slots=True)
class Conveyor:
    """Клетка конвейера и единичный вектор его движения."""

    grid_x: int
    grid_y: int
    direction_x: int
    direction_y: int

    def __post_init__(self) -> None:
        if abs(self.direction_x) + abs(self.direction_y) != 1:
            raise ValueError("Вектор конвейера должен вести ровно на одну соседнюю клетку.")

    @property
    def position(self) -> Cell:
        return self.grid_x, self.grid_y

    def destination(self) -> Cell:
        return self.grid_x + self.direction_x, self.grid_y + self.direction_y
