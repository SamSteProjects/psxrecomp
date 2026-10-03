"""Independent kingdom MAP seeds and slot1 source model qualification."""
from copy import deepcopy
from hashlib import sha256
import os
from pathlib import Path
import struct
import tempfile
import unittest

from importer.core import ImportError, decompress_lzs, find_scene_bundle
from importer.pipeline import _bounded_scene_range, _disc_context


def expected_seeds(data, lut):
    """PIN field_objects sweep, derived directly without importer helpers."""
    result = []
    for index in range(16384):
        cell = struct.unpack_from('<H', data, 0x8000 + index * 2)[0]
        row, column = divmod(index, 128)
        record_id = cell & 511
        at = record_id * 32
        x, y, z, dc, dr, rx, ry, rz = struct.unpack_from('<3h2b3H', data, at)
        pool, flags = struct.unpack_from('<2H', data, at + 16)
        placed = bool(flags & 4)
        decoration = bool(cell & 0x1000 and pool and flags & 2 and not placed)
        if not placed and not decoration:
            continue
        if placed and not (0 <= column + dc < 128 and 0 <= row + dr < 128):
            continue
        tier = data[0x4000 + index] & 15
        result.append(dict(cell_index=index, object_record_index=record_id, model_pool_index=pool,
                           source_position=[column * 128 + x + 64, -lut[tier] + y, row * 128 - z + 64],
                           object_record_sha256=sha256(data[at:at + 32]).hexdigest(),
                           supported=record_id not in (1, 2, 3) and rx == rz == 0))
    return result


def fixture():
    data = bytearray(0x12000)
    lut = [n * 23 for n in range(16)]
    for record, flags in ((10, 4), (11, 2), (12, 1), (13, 4)):
        struct.pack_into('<3h2b3H', data, record * 32, -17, 9, -31, 0, 0, 0, 1024, 0)
        struct.pack_into('<2H', data, record * 32 + 16, 1, flags)
    # Placed seeding needs no walk-visible cell bit; decoration does.
    for index, word in ((129, 10), (130, 0x100b), (131, 11), (132, 0x100c), (0, 13)):
        struct.pack_into('<H', data, 0x8000 + index * 2, word)
        data[0x4000 + index] = 3
    data[13 * 32 + 6] = 255  # Off-grid placed footprint anchor excludes it.
    return bytes(data), lut


class WorldmapPlacementTests(unittest.TestCase):
    def test_source_seed_gates_positions_record_hashes_and_unknown_tilt_coverage(self):
        from importer.worldmap_placements import decode_worldmap_placements
        data, lut = fixture()
        before = deepcopy((data, lut))
        result = decode_worldmap_placements(data, lut, scene='map01')
        self.assertEqual(len(result['placements']), 2)
        self.assertEqual(len(result['unresolved']), 1)
        self.assertIn('footprint anchor', result['unresolved'][0]['reason'])
        oracle = expected_seeds(data, lut)
        self.assertEqual(len(oracle), 2)
        for row, expected in zip(result['placements'], oracle):
            self.assertEqual([row['source_position'][axis] for axis in 'xyz'], expected['source_position'])
            self.assertEqual(row['object_record_index'], expected['object_record_index'])
            self.assertEqual(row['model_pool_index'], expected['model_pool_index'])
            self.assertEqual(row['source_record_sha256'], expected['object_record_sha256'])
        self.assertEqual((data, lut), before)
        unsupported = bytearray(data)
        struct.pack_into('<H', unsupported, 10 * 32 + 8, 1)
        result = decode_worldmap_placements(bytes(unsupported), lut, scene='map01')
        self.assertEqual(len(result['placements']), 1)
        self.assertEqual(len(result['unresolved']), 2)

    def test_foreign_scene_malformed_tables_and_floor_lut_fail_closed(self):
        from importer.worldmap_placements import decode_worldmap_placements, _pack_spans
        data, lut = fixture()
        for scene in ('town01', '../map01', None, True):
            with self.subTest(scene=scene), self.assertRaises(ImportError):
                decode_worldmap_placements(data, lut, scene=scene)
        for source, floors in ((data[:-1], lut), ([], lut), (data, lut[:-1]),
                               (data, [32768] * 16), (data, [True] * 16)):
            with self.subTest(source_type=type(source).__name__), self.assertRaises(ImportError):
                decode_worldmap_placements(source, floors, scene='map01')
        valid_pack = struct.pack('<3I', 2, 3, 15) + bytes(96)
        self.assertEqual(_pack_spans(valid_pack), [(12, 60), (60, 108)])
        for values in ((2, 2, 15), (2, 3, 3), (2, 15, 3), (2, 3, 255), (129, 3, 15)):
            with self.subTest(directory=values), self.assertRaises(ImportError):
                _pack_spans(struct.pack('<3I', *values) + bytes(96))


@unittest.skipUnless(os.environ.get('LEGAIA_DISC_BIN'), 'requires private unchanged retail disc')
class RetailWorldmapPlacementTests(unittest.TestCase):
    def check_kingdom(self, scene, count, models, pack_count):
        from importer.assets import decode_tmd
        from importer.worldmap_geometry import load_worldmap_geometry
        from test_worldmap_geometry import expected_positions
        with _disc_context(os.environ['LEGAIA_DISC_BIN']) as (_, _, mapping, archive):
            start, end = _bounded_scene_range(archive, mapping, scene)
            data = archive.read_entry(archive.entry(start), extended=True)
            bundle, raw = find_scene_bundle(archive, start, end)
            descriptor = bundle.descriptors[2]
            man, _ = decompress_lzs(raw[bundle.table_offset + descriptor.data_offset:], descriptor.size)
            lut = struct.unpack_from('<16h', man, 2)
            descriptor = bundle.descriptors[1]
            pool, _ = decompress_lzs(raw[bundle.table_offset + descriptor.data_offset:], descriptor.size)
            self.assertEqual(struct.unpack_from('<I', pool)[0], pack_count)
            offsets = [value * 4 for value in struct.unpack_from(f'<{pack_count}I', pool, 4)]
            ranges = list(zip(offsets, offsets[1:] + [len(pool)]))
            seeds = expected_seeds(data, lut)
            self.assertEqual(len(seeds), count)
            self.assertEqual(len({s['model_pool_index'] for s in seeds}), models)
            self.assertTrue(all(s['supported'] for s in seeds))
            result = load_worldmap_geometry(os.environ['LEGAIA_DISC_BIN'], scene)
            self.assertEqual(result['preview']['vertices'], expected_positions(data, lut))
            self.assertEqual(result['source_record']['map_sha256'], sha256(data).hexdigest())
            graph = result['scene_graph']
            self.assertLessEqual(len(graph['assets']), 128)
            self.assertLessEqual(len(graph['entities']), 512)
            self.assertLessEqual(sum(len(a['preview']['triangles']) for a in graph['assets']), 200000)
            assets = {a['asset_id']: a for a in graph['assets']}
            self.assertEqual(len(assets), len(graph['assets']))
            ground = assets[result['semantic_id']]
            self.assertEqual(ground['preview']['vertices'], result['preview']['vertices'])
            entities = [row for row in graph['entities'] if row['asset_id'] != result['semantic_id']]
            self.assertEqual(len(entities), count)
            self.assertEqual(len({row['asset_id'] for row in entities}), models)
            by_cell = {row['source_cell']: row for row in entities}
            self.assertEqual(len(by_cell), count)
            for seed in seeds:
                row = by_cell[seed['cell_index']]
                self.assertEqual([row['source_position'][axis] for axis in 'xyz'], seed['source_position'])
                self.assertEqual(row['object_record_index'], seed['object_record_index'])
                self.assertEqual(row['model_pool_index'], seed['model_pool_index'])
                self.assertEqual(row['source_record_sha256'], seed['object_record_sha256'])
                self.assertEqual(row['source_to_world'][12:15], seed['source_position'])
                self.assertEqual(row['runtime_visibility'], 'not_evaluated')
                self.assertEqual(row['runtime_resting_position'], 'unknown')
                a, b = ranges[seed['model_pool_index']]
                source = pool[a:b]
                preview = assets[row['asset_id']]['preview']
                decoded = decode_tmd(source)
                for field in ('vertices', 'triangles', 'triangle_uvs', 'triangle_colors', 'triangle_materials'):
                    self.assertEqual(preview[field], decoded[field])
            self.assertEqual(graph['coverage']['resolved_count'], count)
            self.assertEqual(graph['coverage']['unresolved_count'], 0)
            self.assertEqual(graph['coverage']['inspected_cell_count'], 16384)
            self.assertEqual(graph['metrics']['asset_count'], models + 1)
            self.assertEqual(graph['metrics']['entity_count'], count + 1)
            self.assertLessEqual(graph['metrics']['drawn_triangle_count'], 200000)
            self.assertFalse(result['gameplay_verified'])
            self.assertEqual(data, archive.read_entry(archive.entry(start), extended=True))
            from importer.pipeline import import_scene
            from sdk.project import ProjectService
            from sdk.worldmap_authoring import state_key
            from sdk.worldmap_geometry import inspect
            private = Path(__file__).resolve().parents[3] / 'local-output/sdk-20260909'
            private.mkdir(parents=True, exist_ok=True)
            with tempfile.TemporaryDirectory(prefix='world-seed-readonly-', dir=private) as directory:
                project = ProjectService(Path(directory))
                document = import_scene(os.environ['LEGAIA_DISC_BIN'], 'town01')
                project.import_metadata(document, os.environ['LEGAIA_DISC_BIN'])
                project.command(dict(type='create_actor_draft', donor_entity_id=document['actors'][1]['semantic_id'],
                                     position={'x': 64, 'z': 64}, name='Deferred verification'))
                project.save()
                before = deepcopy((project._document(), project.imports, project.undo_stack,
                                   project.redo_stack, project.selected))
                files = {str(path.relative_to(project.root)): path.read_bytes()
                         for path in project.root.rglob('*') if path.is_file()}
                inspected = inspect(project, scene, state_key(project))
                self.assertEqual(inspected['scene_graph']['metrics'], graph['metrics'])
                self.assertEqual(inspected['preview']['vertices'], result['preview']['vertices'])
                self.assertFalse(inspected['authored_geometry'])
                self.assertFalse(inspected['project_changed'])
                self.assertEqual((project._document(), project.imports, project.undo_stack,
                                  project.redo_stack, project.selected), before)
                self.assertEqual({str(path.relative_to(project.root)): path.read_bytes()
                                  for path in project.root.rglob('*') if path.is_file()}, files)

    def test_drake_source_seeds_and_models(self):
        self.check_kingdom('map01', 301, 26, 40)

    def test_sebucus_source_seeds_and_models(self):
        self.check_kingdom('map02', 272, 22, 36)

    def test_karisto_source_seeds_and_models(self):
        self.check_kingdom('map03', 236, 26, 56)


if __name__ == '__main__':
    unittest.main()
