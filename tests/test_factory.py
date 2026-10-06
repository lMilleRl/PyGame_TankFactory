import unittest

from tank_factory.constants import ASSEMBLY_ORDER, GRID_COLUMNS, GRID_ROWS
from tank_factory.entities import Conveyor, FactoryStatus, Part, PartKind
from tank_factory.factory import Factory


class FactoryMovementTests(unittest.TestCase):
    def make_factory(
        self,
        *,
        drone_start=(1, 1),
        assembly_position=(4, 4),
        parts=(),
        conveyors=(),
        walls=(),
    ):
        return Factory(
            columns=6,
            rows=6,
            drone_start=drone_start,
            assembly_position=assembly_position,
            parts=parts,
            conveyors=conveyors,
            walls=walls,
        )

    def test_default_factory_is_a_ten_by_ten_grid(self):
        factory = Factory()

        self.assertEqual((factory.columns, factory.rows), (GRID_COLUMNS, GRID_ROWS))
        self.assertEqual(len(factory.parts), 3)
        self.assertEqual(factory.assembly_indices, [])

    def test_arrow_step_moves_drone_exactly_one_cell(self):
        factory = Factory()
        start = factory.drone_position

        self.assertTrue(factory.move_drone(1, 0))
        self.assertEqual(factory.drone_position, (start[0] + 1, start[1]))
        self.assertEqual(factory.turn_count, 1)

    def test_diagonal_or_multi_cell_move_is_rejected(self):
        factory = Factory()

        with self.assertRaises(ValueError):
            factory.move_drone(1, 1)
        with self.assertRaises(ValueError):
            factory.move_drone(2, 0)

    def test_wall_and_grid_edge_block_movement_without_advancing_turn(self):
        factory = self.make_factory(drone_start=(1, 1), walls={(2, 1)})

        self.assertFalse(factory.move_drone(1, 0))
        self.assertEqual(factory.drone_position, (1, 1))
        self.assertEqual(factory.turn_count, 0)

        edge_factory = self.make_factory(drone_start=(0, 1), walls=())
        self.assertFalse(edge_factory.move_drone(-1, 0))
        self.assertEqual(edge_factory.drone_position, (0, 1))
        self.assertEqual(edge_factory.turn_count, 0)

    def test_conveyor_moves_loose_part_one_cell_after_a_turn(self):
        part = Part(PartKind.CHASSIS, 2, 2)
        factory = self.make_factory(
            parts=[part],
            conveyors=[Conveyor(2, 2, 1, 0)],
        )

        factory.move_drone(0, 1)

        self.assertEqual(factory.parts[0].position, (3, 2))

    def test_adjacent_conveyors_move_parts_simultaneously_not_in_a_chain(self):
        factory = self.make_factory(
            parts=[Part(PartKind.CHASSIS, 1, 2), Part(PartKind.TURRET, 2, 2)],
            conveyors=[Conveyor(1, 2, 1, 0), Conveyor(2, 2, 1, 0)],
        )

        factory.move_drone(0, 1)

        self.assertEqual([part.position for part in factory.parts], [(2, 2), (3, 2)])

    def test_conveyor_does_not_overwrite_parts_that_compete_for_same_cell(self):
        factory = self.make_factory(
            parts=[Part(PartKind.CHASSIS, 1, 2), Part(PartKind.TURRET, 3, 2)],
            conveyors=[Conveyor(1, 2, 1, 0), Conveyor(3, 2, -1, 0)],
        )

        factory.move_drone(0, 1)

        self.assertEqual([part.position for part in factory.parts], [(1, 2), (3, 2)])

    def test_conveyor_stops_part_at_stationary_part(self):
        factory = self.make_factory(
            parts=[Part(PartKind.CHASSIS, 1, 2), Part(PartKind.TURRET, 2, 2)],
            conveyors=[Conveyor(1, 2, 1, 0)],
        )

        factory.move_drone(0, 1)

        self.assertEqual([part.position for part in factory.parts], [(1, 2), (2, 2)])

    def test_part_not_on_conveyor_stays_in_place(self):
        factory = self.make_factory(parts=[Part(PartKind.CANNON, 3, 3)])

        factory.move_drone(0, 1)

        self.assertEqual(factory.parts[0].position, (3, 3))

    def test_invalid_conveyor_vector_is_rejected(self):
        with self.assertRaises(ValueError):
            Conveyor(2, 2, 1, 1)


class AssemblyTests(unittest.TestCase):
    def test_pickup_removes_part_from_floor_and_conveyors_ignore_carried_part(self):
        factory = self.make_factory(
            drone_start=(2, 2),
            parts=[Part(PartKind.CHASSIS, 2, 2)],
            conveyors=[Conveyor(2, 2, 1, 0)],
        )

        self.assertTrue(factory.interact())
        self.assertEqual(factory.parts, [])
        self.assertIsNotNone(factory.drone.carried_part)
        self.assertEqual(factory.drone.carried_part.position, (2, 2))

        factory.move_drone(0, 1)

        self.assertEqual(factory.drone.carried_part.position, (2, 2))

    def test_wrong_part_is_rejected_and_remains_with_drone(self):
        factory = self.make_factory(
            drone_start=(1, 1),
            assembly_position=(1, 1),
            parts=[Part(PartKind.TURRET, 1, 1)],
        )

        self.assertTrue(factory.interact())
        self.assertFalse(factory.interact())
        self.assertEqual(factory.assembly_indices, [])
        self.assertEqual(factory.drone.carried_part.kind, PartKind.TURRET)
        self.assertEqual(factory.status, FactoryStatus.ACTIVE)
        self.assertIn("Шасси", factory.message)

    def test_parts_are_assembled_only_in_chassis_turret_cannon_order(self):
        factory = self.make_factory(
            drone_start=(1, 1),
            assembly_position=(4, 4),
            parts=[
                Part(PartKind.CHASSIS, 1, 1),
                Part(PartKind.TURRET, 2, 1),
                Part(PartKind.CANNON, 3, 1),
            ],
        )

        for part_kind in ASSEMBLY_ORDER:
            part = next(part for part in factory.parts if part.kind is part_kind)
            factory.drone.grid_x, factory.drone.grid_y = part.position
            self.assertTrue(factory.interact())
            factory.drone.grid_x, factory.drone.grid_y = factory.assembly_position
            self.assertTrue(factory.interact())

        self.assertEqual(factory.assembly_indices, [0, 1, 2])
        self.assertTrue(factory.is_assembly_complete())
        self.assertEqual(factory.status, FactoryStatus.WON)
        self.assertFalse(factory.move_drone(1, 0))

    def test_default_level_can_be_completed_with_grid_moves(self):
        factory = Factory()

        def move_to(destination):
            while factory.drone.grid_x < destination[0]:
                self.assertTrue(factory.move_drone(1, 0))
            while factory.drone.grid_x > destination[0]:
                self.assertTrue(factory.move_drone(-1, 0))
            while factory.drone.grid_y < destination[1]:
                self.assertTrue(factory.move_drone(0, 1))
            while factory.drone.grid_y > destination[1]:
                self.assertTrue(factory.move_drone(0, -1))

        move_to((1, 2))
        move_to((5, 2))
        self.assertEqual(factory.get_part_at((5, 2)).kind, PartKind.CHASSIS)
        self.assertTrue(factory.interact())
        move_to(factory.assembly_position)
        self.assertTrue(factory.interact())

        for part_kind, position in (
            (PartKind.TURRET, (7, 2)),
            (PartKind.CANNON, (2, 7)),
        ):
            move_to(position)
            self.assertTrue(factory.interact())
            move_to(factory.assembly_position)
            self.assertTrue(factory.interact())

        self.assertEqual(factory.assembly_indices, [0, 1, 2])
        self.assertEqual(factory.status, FactoryStatus.WON)

    def test_factory_rejects_interaction_when_no_part_is_under_drone(self):
        factory = self.make_factory()

        self.assertFalse(factory.interact())
        self.assertEqual(factory.turn_count, 0)

    def make_factory(self, **kwargs):
        defaults = {
            "columns": 6,
            "rows": 6,
            "drone_start": (1, 1),
            "assembly_position": (4, 4),
            "parts": (),
            "conveyors": (),
            "walls": (),
        }
        defaults.update(kwargs)
        return Factory(**defaults)


if __name__ == "__main__":
    unittest.main()
