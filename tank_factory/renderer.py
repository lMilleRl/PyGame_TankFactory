from pathlib import Path

import pygame

from .constants import (
    ASSEMBLY_ORDER,
    CELL_SIZE,
    GRID_ORIGIN_X,
    GRID_ORIGIN_Y,
    PANEL_TOP,
    PANEL_WIDTH,
    PANEL_X,
    PALETTE,
    PART_COLORS,
    WINDOW_HEIGHT,
    WINDOW_WIDTH,
)
from .entities import FactoryStatus, PartKind, PART_NAMES
from .factory import Factory

ASSET_DIRECTORY = Path(__file__).resolve().parent.parent / "assets"
PART_ASSET_FILES = {
    PartKind.CHASSIS: "chassis.png",
    PartKind.TURRET: "turret.png",
    PartKind.CANNON: "cannon.png",
}
CONVEYOR_ASSET_FILES = {
    (0, -1): "conveyor_vertical.png",
    (1, 0): "conveyor_horizontal.png",
    (0, 1): "conveyor_vertical.png",
    (-1, 0): "conveyor_horizontal.png",
}
TILE_ASSET_FILES = {
    "floor": "floor.png",
    "wall": "wall.png",
    "assembly": "assembly.png",
}


class Renderer:
    """Рисует меню, сетку цеха, панель состояния и финальный экран."""

    def __init__(self) -> None:
        self.fonts: dict[tuple[int, bool], pygame.font.Font] = {}
        self.sprite_cache: dict[tuple[int, int, int], pygame.Surface] = {}
        self.part_sprites = {part_kind: self._load_asset(filename) for part_kind, filename in PART_ASSET_FILES.items()}
        self.conveyor_sprites = {direction: self._load_asset(filename) for direction, filename in CONVEYOR_ASSET_FILES.items()}
        self.tile_sprites = {tile_name: self._load_asset(filename) for tile_name, filename in TILE_ASSET_FILES.items()}
        self.drone_sprite = self._load_asset("drone.png")

    @staticmethod
    def _load_asset(filename: str) -> pygame.Surface:
        path = ASSET_DIRECTORY / filename
        if not path.is_file():
            raise FileNotFoundError(f"Required renderer asset is missing: {path}")
        return pygame.image.load(str(path)).convert_alpha()

    def _draw_sprite(self, surface: pygame.Surface, image: pygame.Surface, rect: pygame.Rect) -> None:
        image_width, image_height = image.get_size()
        scale = min(rect.width // image_width, rect.height // image_height)
        if scale:
            size = image_width * scale, image_height * scale
        else:
            factor = min(rect.width / image_width, rect.height / image_height)
            size = max(1, round(image_width * factor)), max(1, round(image_height * factor))

        cache_key = id(image), *size
        scaled = self.sprite_cache.get(cache_key)
        if scaled is None:
            scaled = image if size == image.get_size() else pygame.transform.scale(image, size)
            self.sprite_cache[cache_key] = scaled
        surface.blit(scaled, scaled.get_rect(center=rect.center))

    def _font(self, size: int, bold: bool = False) -> pygame.font.Font:
        key = size, bold
        if key not in self.fonts:
            self.fonts[key] = pygame.font.SysFont("segoeui", size, bold=bold)
        return self.fonts[key]

    def _text(
        self,
        surface: pygame.Surface,
        text: str,
        position: tuple[int, int],
        size: int = 18,
        color: tuple[int, int, int] | None = None,
        bold: bool = False,
        centered: bool = False,
    ) -> pygame.Rect:
        rendered = self._font(size, bold).render(text, True, color or PALETTE["text"])
        rect = rendered.get_rect()
        if centered:
            rect.center = position
        else:
            rect.topleft = position
        surface.blit(rendered, rect)
        return rect

    def _rounded_panel(
        self,
        surface: pygame.Surface,
        rect: pygame.Rect,
        fill: tuple[int, int, int] | None = None,
        border: tuple[int, int, int] | None = None,
        radius: int = 12,
    ) -> None:
        pygame.draw.rect(surface, fill or PALETTE["panel"], rect, border_radius=radius)
        if border:
            pygame.draw.rect(surface, border, rect, width=1, border_radius=radius)

    def _draw_background_grid(self, surface: pygame.Surface) -> None:
        for x in range(0, WINDOW_WIDTH, 64):
            pygame.draw.line(surface, PALETTE["background_grid"], (x, 0), (x, WINDOW_HEIGHT))
        for y in range(0, WINDOW_HEIGHT, 64):
            pygame.draw.line(surface, PALETTE["background_grid"], (0, y), (WINDOW_WIDTH, y))

    def draw_menu(self, surface: pygame.Surface) -> None:
        surface.fill(PALETTE["background"])
        self._draw_background_grid(surface)
        self._text(surface, "TANK FACTORY", (68, 46), 18, PALETTE["accent"], True)
        self._text(surface, "ТАНКОВЫЙ ЗАВОД", (68, 88), 44, PALETTE["text"], True)
        self._text(surface, "Лабораторная работа 1  /  вариант 19", (72, 146), 21, PALETTE["text_muted"])

        preview_panel = pygame.Rect(56, 206, 514, 500)
        self._rounded_panel(surface, preview_panel, PALETTE["panel"], PALETTE["outline"])
        self._text(surface, "ЦЕХ 19", (82, 226), 16, PALETTE["accent"], True)
        self._draw_board(surface, Factory(), (112, 270), 42, coordinates=False)

        info_panel = pygame.Rect(604, 206, 620, 500)
        self._rounded_panel(surface, info_panel, PALETTE["panel"], PALETTE["outline"])
        self._text(surface, "ЗАДАЧА СМЕНЫ", (642, 238), 15, PALETTE["accent"], True)
        self._text(surface, "Собери танк по шагам", (642, 270), 30, PALETTE["text"], True)
        self._text(surface, "Доставь три детали на сборочную платформу.", (642, 322), 19, PALETTE["text_muted"])

        for index, part_kind in enumerate(ASSEMBLY_ORDER):
            row_y = 374 + index * 52
            self._draw_part_icon(surface, part_kind, pygame.Rect(646, row_y, 38, 38))
            self._text(surface, f"{index + 1}.  {PART_NAMES[part_kind]}", (704, row_y + 4), 20)

        self._rounded_panel(surface, pygame.Rect(642, 548, 534, 78), PALETTE["panel_light"])
        self._text(surface, "Стрелки — шаг    Пробел — взять / положить", (664, 566), 16)
        self._text(surface, "Конвейеры перемещают свободные детали.", (664, 592), 16, PALETTE["text_muted"])
        self._rounded_panel(surface, pygame.Rect(642, 644, 250, 42), PALETTE["accent"])
        self._text(surface, "ENTER  —  НАЧАТЬ", (767, 665), 16, PALETTE["background"], True, centered=True)
        self._text(surface, "R — перезапуск   M — меню   Esc — выход", (910, 655), 15, PALETTE["text_muted"])

    def draw_game(self, surface: pygame.Surface, factory: Factory) -> None:
        surface.fill(PALETTE["background"])
        self._draw_background_grid(surface)
        self._text(surface, "ТАНКОВЫЙ ЗАВОД", (48, 34), 30, PALETTE["text"], True)
        self._text(surface, "ВАРИАНТ 19  /  ПОШАГОВАЯ СБОРКА  /  СЕТКА 10 x 10", (50, 78), 14, PALETTE["text_muted"], True)
        self._rounded_panel(surface, pygame.Rect(1068, 38, 176, 42), PALETTE["panel_light"], PALETTE["outline"])
        self._text(surface, f"ХОД {factory.turn_count:02d}", (1156, 59), 16, PALETTE["accent_light"], True, centered=True)

        self._draw_board(surface, factory, (GRID_ORIGIN_X, GRID_ORIGIN_Y), CELL_SIZE, coordinates=True)
        self._draw_factory_panel(surface, factory)
        self._text(
            surface,
            "КОНВЕЙЕРЫ СДВИГАЮТ ДЕТАЛИ НА ОДНУ КЛЕТКУ ПОСЛЕ УСПЕШНОГО ДЕЙСТВИЯ",
            (GRID_ORIGIN_X, 728),
            13,
            PALETTE["text_muted"],
        )

    def draw_victory(self, surface: pygame.Surface, factory: Factory) -> None:
        self.draw_game(surface, factory)
        overlay = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        overlay.fill((10, 16, 20, 210))
        surface.blit(overlay, (0, 0))

        card = pygame.Rect(330, 246, 620, 324)
        self._rounded_panel(surface, card, PALETTE["panel"], PALETTE["success"], 18)
        self._text(surface, "СБОРКА ЗАВЕРШЕНА", (640, 298), 16, PALETTE["success"], True, centered=True)
        self._text(surface, "Танк готов к отправке", (640, 354), 32, PALETTE["text"], True, centered=True)
        self._text(surface, "Последовательность [0, 1, 2] соблюдена.", (640, 414), 19, PALETTE["text_muted"], centered=True)
        self._text(surface, f"Потрачено ходов: {factory.turn_count}", (640, 452), 17, PALETTE["text"], centered=True)
        self._rounded_panel(surface, pygame.Rect(442, 500, 396, 44), PALETTE["success"])
        self._text(surface, "ENTER / R — новая смена     M — меню", (640, 522), 16, PALETTE["background"], True, centered=True)

    def _draw_board(
        self,
        surface: pygame.Surface,
        factory: Factory,
        origin: tuple[int, int],
        cell_size: int,
        coordinates: bool,
    ) -> None:
        origin_x, origin_y = origin
        board_rect = pygame.Rect(origin_x - 4, origin_y - 4, factory.columns * cell_size + 8, factory.rows * cell_size + 8)
        pygame.draw.rect(surface, PALETTE["panel"], board_rect, border_radius=12)

        if coordinates:
            for grid_x in range(factory.columns):
                self._text(
                    surface,
                    str(grid_x),
                    (origin_x + grid_x * cell_size + cell_size // 2, origin_y - 15),
                    12,
                    PALETTE["text_muted"],
                    centered=True,
                )
            for grid_y in range(factory.rows):
                self._text(
                    surface,
                    str(grid_y),
                    (origin_x - 17, origin_y + grid_y * cell_size + cell_size // 2),
                    12,
                    PALETTE["text_muted"],
                    centered=True,
                )

        for grid_y in range(factory.rows):
            for grid_x in range(factory.columns):
                position = grid_x, grid_y
                rect = pygame.Rect(origin_x + grid_x * cell_size, origin_y + grid_y * cell_size, cell_size, cell_size)
                inset = rect.inflate(-3, -3)
                if position in factory.walls:
                    self._draw_wall(surface, inset)
                    continue

                self._draw_sprite(surface, self.tile_sprites["floor"], inset)
                conveyor = factory.conveyors.get(position)
                if conveyor:
                    self._draw_conveyor(surface, inset, conveyor.direction_x, conveyor.direction_y)
                if position == factory.assembly_position:
                    self._draw_assembly_tile(surface, inset, len(factory.assembly_stack))

                part = factory.get_part_at(position)
                if part is not None:
                    self._draw_part_icon(surface, part.kind, inset.inflate(-5, -5))
                if factory.drone.position == position:
                    carried_kind = factory.drone.carried_part.kind if factory.drone.carried_part else None
                    self._draw_drone(surface, inset, carried_kind)

        pygame.draw.rect(surface, PALETTE["outline"], board_rect, width=1, border_radius=12)

    def _draw_wall(self, surface: pygame.Surface, rect: pygame.Rect) -> None:
        self._draw_sprite(surface, self.tile_sprites["wall"], rect)

    def _draw_conveyor(self, surface: pygame.Surface, rect: pygame.Rect, direction_x: int, direction_y: int) -> None:
        self._draw_sprite(surface, self.conveyor_sprites[(direction_x, direction_y)], rect)
        center_x, center_y = rect.center
        start = center_x - direction_x * 11, center_y - direction_y * 11
        end = center_x + direction_x * 12, center_y + direction_y * 12
        pygame.draw.line(surface, PALETTE["drone"], start, end, max(2, rect.width // 14))
        wing = max(5, rect.width // 7)
        left_wing = end[0] - direction_x * wing - direction_y * wing, end[1] - direction_y * wing + direction_x * wing
        right_wing = end[0] - direction_x * wing + direction_y * wing, end[1] - direction_y * wing - direction_x * wing
        pygame.draw.line(surface, PALETTE["drone"], end, left_wing, max(2, rect.width // 14))
        pygame.draw.line(surface, PALETTE["drone"], end, right_wing, max(2, rect.width // 14))

    def _draw_assembly_tile(self, surface: pygame.Surface, rect: pygame.Rect, stack_size: int) -> None:
        self._draw_sprite(surface, self.tile_sprites["assembly"], rect)
        pygame.draw.rect(surface, PALETTE["assembly_light"], rect, width=2, border_radius=5)
        self._text(surface, "СБОРКА", rect.center, max(10, rect.width // 4), PALETTE["text"], True, centered=True)
        slot_width = max(5, (rect.width - 20) // 3)
        for index in range(3):
            slot = pygame.Rect(rect.left + 6 + index * (slot_width + 3), rect.bottom - 10, slot_width, 4)
            color = PALETTE["success"] if index < stack_size else PALETTE["wall_dark"]
            pygame.draw.rect(surface, color, slot, border_radius=2)

    def _draw_part_icon(self, surface: pygame.Surface, part_kind: PartKind, rect: pygame.Rect) -> None:
        self._draw_sprite(surface, self.part_sprites[part_kind], rect)

    def _draw_drone(self, surface: pygame.Surface, rect: pygame.Rect, carried_kind: PartKind | None) -> None:
        self._draw_sprite(surface, self.drone_sprite, rect.inflate(-3, -3))
        if carried_kind is not None:
            pygame.draw.circle(surface, PART_COLORS[carried_kind], (rect.right - 7, rect.top + 7), max(4, rect.width // 9))

    def _draw_factory_panel(self, surface: pygame.Surface, factory: Factory) -> None:
        outer = pygame.Rect(PANEL_X, PANEL_TOP, PANEL_WIDTH, 580)
        self._rounded_panel(surface, outer, PALETTE["panel"], PALETTE["outline"])
        self._text(surface, "ПАНЕЛЬ ДИСПЕТЧЕРА", (PANEL_X + 18, PANEL_TOP + 12), 17, PALETTE["accent"], True)

        status_rect = pygame.Rect(PANEL_X + 14, PANEL_TOP + 44, PANEL_WIDTH - 28, 98)
        self._rounded_panel(surface, status_rect, PALETTE["panel_light"])
        self._text(surface, "СООБЩЕНИЕ", (status_rect.left + 14, status_rect.top + 10), 12, PALETTE["text_muted"], True)
        self._text(surface, f"ХОД {factory.turn_count:02d}", (status_rect.right - 90, status_rect.top + 9), 12, PALETTE["accent_light"], True)
        for line_index, line in enumerate(self._wrap(factory.message, status_rect.width - 28, 16)[:2]):
            self._text(surface, line, (status_rect.left + 14, status_rect.top + 31 + line_index * 20), 16)
        self._text(
            surface,
            f"ДРОН  ({factory.drone.grid_x}, {factory.drone.grid_y})",
            (status_rect.left + 14, status_rect.bottom - 21),
            12,
            PALETTE["text_muted"],
            True,
        )

        assembly_rect = pygame.Rect(PANEL_X + 14, PANEL_TOP + 154, PANEL_WIDTH - 28, 170)
        self._rounded_panel(surface, assembly_rect, PALETTE["panel_light"])
        self._text(surface, "ПОРЯДОК СБОРКИ", (assembly_rect.left + 14, assembly_rect.top + 10), 12, PALETTE["text_muted"], True)
        gap = 8
        card_width = (assembly_rect.width - 28 - gap * 2) // 3
        for index, part_kind in enumerate(ASSEMBLY_ORDER):
            card = pygame.Rect(assembly_rect.left + 14 + index * (card_width + gap), assembly_rect.top + 37, card_width, 112)
            assembled = index < len(factory.assembly_stack)
            is_next = index == len(factory.assembly_stack) and factory.status is FactoryStatus.ACTIVE
            border = PALETTE["success"] if assembled else PALETTE["accent"] if is_next else PALETTE["outline"]
            self._rounded_panel(surface, card, PALETTE["panel"], border, 9)
            self._draw_part_icon(surface, part_kind, pygame.Rect(card.centerx - 19, card.top + 9, 38, 38))
            self._text(surface, f"{index + 1}. {PART_NAMES[part_kind]}", (card.centerx, card.top + 66), 14, PALETTE["text"], True, centered=True)
            state_text = "ГОТОВО" if assembled else "СЛЕДУЮЩАЯ" if is_next else "ОЖИДАЕТ"
            state_color = PALETTE["success"] if assembled else PALETTE["accent_light"] if is_next else PALETTE["text_muted"]
            self._text(surface, state_text, (card.centerx, card.bottom - 13), 10, state_color, True, centered=True)

        parts_rect = pygame.Rect(PANEL_X + 14, PANEL_TOP + 334, PANEL_WIDTH - 28, 132)
        self._rounded_panel(surface, parts_rect, PALETTE["panel_light"])
        self._text(surface, "ДЕТАЛИ В ЦЕХУ", (parts_rect.left + 14, parts_rect.top + 10), 12, PALETTE["text_muted"], True)
        for index, part_kind in enumerate(ASSEMBLY_ORDER):
            row_y = parts_rect.top + 34 + index * 27
            self._draw_part_icon(surface, part_kind, pygame.Rect(parts_rect.left + 13, row_y, 30, 23))
            self._text(surface, PART_NAMES[part_kind], (parts_rect.left + 54, row_y + 3), 14)
            if part_kind in factory.assembly_stack:
                location = "НА ПЛАТФОРМЕ"
                location_color = PALETTE["success"]
            elif factory.drone.carried_part is not None and factory.drone.carried_part.kind is part_kind:
                location = "У ДРОНА"
                location_color = PALETTE["accent_light"]
            else:
                part = next((item for item in factory.parts if item.kind is part_kind), None)
                location = f"({part.grid_x}, {part.grid_y})" if part else "НЕТ НА ПОЛЕ"
                location_color = PALETTE["text_muted"]
            self._text(surface, location, (parts_rect.right - 145, row_y + 4), 12, location_color, True)

        controls_rect = pygame.Rect(PANEL_X + 14, PANEL_TOP + 476, PANEL_WIDTH - 28, 92)
        self._rounded_panel(surface, controls_rect, PALETTE["panel_light"])
        self._text(surface, "УПРАВЛЕНИЕ", (controls_rect.left + 14, controls_rect.top + 8), 12, PALETTE["text_muted"], True)
        self._text(surface, "СТРЕЛКИ  —  шаг", (controls_rect.left + 14, controls_rect.top + 34), 13)
        self._text(surface, "SPACE  —  взять / положить", (controls_rect.left + 220, controls_rect.top + 34), 13)
        self._text(surface, "R  —  заново", (controls_rect.left + 14, controls_rect.top + 59), 13, PALETTE["text_muted"])
        self._text(surface, "M  —  меню", (controls_rect.left + 220, controls_rect.top + 59), 13, PALETTE["text_muted"])

    def _wrap(self, text: str, max_width: int, font_size: int) -> list[str]:
        font = self._font(font_size)
        lines: list[str] = []
        current = ""
        for word in text.split():
            candidate = f"{current} {word}".strip()
            if current and font.size(candidate)[0] > max_width:
                lines.append(current)
                current = word
            else:
                current = candidate
        if current:
            lines.append(current)
        return lines
