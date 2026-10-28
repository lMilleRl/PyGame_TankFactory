import tempfile
import unittest
from pathlib import Path

from tank_factory.entities import PartKind
from tank_factory.factory import Factory
from tank_factory.layout import LayoutError, load_layout, parse_layout_text
from tank_factory.persistence import (
    append_score,
    apply_save_dict,
    factory_to_dict,
    read_scores,
    save_factory,
)


SAMPLE = """
##########
#........#
#.>>>>>vv#
#......vv#
#......vv#
#......vv#
#.>>>v.vv#
#....v.v.#
#D...>..S#
##########
PART H 2 2
PART B 8 2
PART N 2 6
"""


class LayoutTests(unittest.TestCase):
    def test_parse_default_layout_matches_hardcoded_factory(self):
        layout = parse_layout_text(SAMPLE)
        factory = Factory.from_layout_data(layout)
        builtin = Factory()

        self.assertEqual(factory.columns, 10)
        self.assertEqual(factory.rows, 10)
        self.assertEqual(factory.drone_position, builtin.drone_position)
        self.assertEqual(factory.assembly_position, builtin.assembly_position)
        self.assertEqual(factory.walls, builtin.walls)
        self.assertEqual(set(factory.conveyors), set(builtin.conveyors))
        for conveyor_pos, conveyor in factory.conveyors.items():
            other = builtin.conveyors[conveyor_pos]
            self.assertEqual(
                (conveyor.direction_x, conveyor.direction_y),
                (other.direction_x, other.direction_y),
            )
        self.assertEqual(
            {(p.kind, p.position) for p in factory.parts},
            {(p.kind, p.position) for p in builtin.parts},
        )

    def test_missing_file_raises_file_not_found(self):
        with self.assertRaises(FileNotFoundError):
            load_layout(Path("/tmp/no_such_factory_layout_12345.txt"))

    def test_bad_symbol_raises_layout_error(self):
        with self.assertRaises(LayoutError):
            parse_layout_text("####\n#DZX#\n#..S#\n####\n")

    def test_missing_drone_raises_layout_error(self):
        with self.assertRaises(LayoutError):
            parse_layout_text("####\n#..S#\n#...#\n####\n")

    def test_part_on_grid_symbol(self):
        text = "#####\n#D.H#\n#..S#\n#B.N#\n#####\n"
        layout = parse_layout_text(text)
        kinds = {part.kind for part in layout.parts}
        self.assertEqual(kinds, {PartKind.CHASSIS, PartKind.TURRET, PartKind.CANNON})

    def test_c_alias_is_right_conveyor(self):
        text = "#####\n#D.C#\n#..S#\n#...#\n#####\n"
        layout = parse_layout_text(text)
        conveyor = layout.conveyors[0]
        self.assertEqual((conveyor.direction_x, conveyor.direction_y), (1, 0))


class PersistenceTests(unittest.TestCase):
    def test_save_and_load_roundtrip(self):
        factory = Factory()
        factory.move_drone(1, 0)
        factory.move_drone(0, -1)
        payload = factory_to_dict(factory)

        restored = Factory()
        apply_save_dict(restored, payload)
        self.assertEqual(restored.turn_count, factory.turn_count)
        self.assertEqual(restored.drone_position, factory.drone_position)
        self.assertEqual(
            [(p.kind, p.position) for p in restored.parts],
            [(p.kind, p.position) for p in factory.parts],
        )

    def test_save_factory_writes_json_file(self):
        factory = Factory()
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "factory_save.json"
            save_factory(factory, path)
            self.assertTrue(path.is_file())
            text = path.read_text(encoding="utf-8")
            self.assertIn("turn_count", text)

    def test_scores_csv_writes_header_once(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "scores.csv"
            append_score("Mark", 40, 3, path)
            append_score("Anna", 35, 3, path)
            rows = read_scores(path)
            self.assertEqual(len(rows), 2)
            header = path.read_text(encoding="utf-8").splitlines()[0]
            self.assertEqual(header, "timestamp,player_name,turns,parts_assembled,efficiency")
            self.assertEqual(rows[0]["player_name"], "Mark")
            self.assertAlmostEqual(float(rows[0]["efficiency"]), 3 / 40, places=4)

    def test_create_for_game_falls_back_when_file_missing(self):
        factory = Factory.create_for_game(Path("/tmp/missing_layout_for_tests.txt"))
        self.assertEqual(factory.columns, 10)
        self.assertIn("не найден", factory.message)


if __name__ == "__main__":
    unittest.main()
