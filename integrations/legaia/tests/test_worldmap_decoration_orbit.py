"""Pivot rotations preserve native ownership, descendants and atomic failure."""
from copy import deepcopy
from math import cos, sin, tau, floor
from unittest import TestCase

from importer.worldmap_placement_allocation import allocate
from importer.worldmap_placements import decode_worldmap_placements
from sdk.worldmap_decoration_group import revised_binding
from sdk.project import ProjectError
from test_worldmap_decoration_group import group_fixture


class WorldDecorationOrbitTests(TestCase):
    def test_rotations_source_preservation_and_native_words(self):
        for model in (False, True):
            raw, heights, _, rows, current, binding = group_fixture(model)
            held = deepcopy(binding)
            ids = sorted(r['placement_id'] for r in rows[:2])
            before = decode_worldmap_placements(current, heights, scene='map01')['placements']
            indexed = {r['source_cell']: r for r in before}
            pivot = indexed[rows[0]['target_cell']]['source_position']
            for angle in (1, 128, 512, 1024, 2048, 3072, -1024):
                with self.subTest(model=model, angle=angle):
                    delta = dict(x=7, y=-3, z=9, yaw_units=angle, orbit_pivot=ids[0])
                    updated = revised_binding(raw, heights, binding, ids, delta)
                    data = raw
                    for op in updated['operations']:
                        data, _ = allocate(data, heights, 'map01', op['requests'])
                    after = {r['source_cell']: r for r in
                             decode_worldmap_placements(data, heights, scene='map01')['placements']}
                    for row in rows[:2]:
                        old = indexed[row['target_cell']]
                        position = old['source_position']
                        radians = angle * tau / 4096
                        dx, dz = position['x'] - pivot['x'], position['z'] - pivot['z']
                        expected = dict(
                            x=floor(pivot['x'] + cos(radians) * dx + sin(radians) * dz + 0.5) + 7,
                            y=position['y'] - 3,
                            z=floor(pivot['z'] - sin(radians) * dx + cos(radians) * dz + 0.5) - 9)
                        self.assertEqual(after[row['target_cell']]['source_position'], expected)
                        self.assertEqual(after[row['target_cell']]['source_rotation_psx']['y'] & 4095,
                                         (old['source_rotation_psx']['y'] + angle) % 4096)
                    self.assertEqual(after[rows[2]['target_cell']], indexed[rows[2]['target_cell']])
                    self.assertEqual(binding, held)

    def test_invalid_pivots_angles_and_overflow_are_atomic(self):
        raw, heights, _, rows, _, binding = group_fixture()
        ids = sorted(r['placement_id'] for r in rows[:2])
        held = deepcopy(binding)
        base = dict(x=0, y=0, z=0, yaw_units=1024, orbit_pivot=ids[0])
        for delta in ({**base, 'orbit_pivot': 'foreign'}, {**base, 'orbit_pivot': None},
                      {**base, 'yaw_units': 0}, {**base, 'yaw_units': True}, {**base, 'x': 65535}):
            with self.subTest(delta=delta), self.assertRaises(ProjectError):
                revised_binding(raw, heights, binding, ids, delta)
            self.assertEqual(binding, held)
