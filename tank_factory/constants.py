from .entities import PartKind

APP_TITLE = "Танковый завод — вариант 19"
WINDOW_WIDTH = 1280
WINDOW_HEIGHT = 820
FPS = 60

GRID_COLUMNS = 10
GRID_ROWS = 10
CELL_SIZE = 56
GRID_ORIGIN_X = 48
GRID_ORIGIN_Y = 150
PANEL_X = 648
PANEL_TOP = 132
PANEL_WIDTH = 596

DEFAULT_DRONE_START = (1, 8)
ASSEMBLY_POSITION = (8, 8)
ASSEMBLY_ORDER = (PartKind.CHASSIS, PartKind.TURRET, PartKind.CANNON)
INITIAL_PARTS = (
    (PartKind.CHASSIS, 2, 2),
    (PartKind.TURRET, 8, 2),
    (PartKind.CANNON, 2, 6),
)
CONVEYOR_LAYOUT = (
    (2, 2, 1, 0),
    (3, 2, 1, 0),
    (4, 2, 1, 0),
    (5, 2, 1, 0),
    (6, 2, 1, 0),
    (7, 2, 0, 1),
    (7, 3, 0, 1),
    (7, 4, 0, 1),
    (7, 5, 0, 1),
    (7, 6, 0, 1),
    (7, 7, 0, 1),
    (8, 2, 0, 1),
    (8, 3, 0, 1),
    (8, 4, 0, 1),
    (8, 5, 0, 1),
    (8, 6, 0, 1),
    (2, 6, 1, 0),
    (3, 6, 1, 0),
    (4, 6, 1, 0),
    (5, 6, 0, 1),
    (5, 7, 0, 1),
    (5, 8, 1, 0),
)

PALETTE = {
    "background": (19, 25, 29),
    "background_grid": (27, 35, 39),
    "panel": (29, 38, 43),
    "panel_light": (38, 49, 55),
    "cell": (39, 49, 54),
    "cell_alt": (43, 54, 59),
    "wall": (76, 88, 92),
    "wall_dark": (45, 54, 58),
    "conveyor": (33, 66, 76),
    "assembly": (77, 92, 58),
    "assembly_light": (181, 197, 91),
    "drone": (77, 191, 181),
    "drone_dark": (31, 103, 102),
    "accent": (224, 172, 73),
    "accent_light": (248, 207, 123),
    "text": (235, 239, 231),
    "text_muted": (160, 174, 174),
    "success": (108, 193, 127),
    "danger": (218, 105, 89),
    "outline": (75, 91, 96),
}

PART_COLORS = {
    PartKind.CHASSIS: (219, 171, 76),
    PartKind.TURRET: (111, 183, 191),
    PartKind.CANNON: (228, 126, 91),
}

DEFAULT_WALLS = frozenset(
    {(x, 0) for x in range(GRID_COLUMNS)}
    | {(x, GRID_ROWS - 1) for x in range(GRID_COLUMNS)}
    | {(0, y) for y in range(GRID_ROWS)}
    | {(GRID_COLUMNS - 1, y) for y in range(GRID_ROWS)}
)
