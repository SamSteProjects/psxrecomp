"""Source-only whole-ground kingdom geometry; no menu coordinates or runtime."""
from copy import deepcopy
from hashlib import sha256
import json
import math
import os
from pathlib import Path
import struct
import tempfile
import unittest
from unittest.mock import patch

from importer.core import ImportError, decompress_lzs, find_scene_bundle
from importer.pipeline import _bounded_scene_range, _disc_context
from importer.textures import TextureCatalog


def fixture():
    data = bytearray(0x12000)
    data[32 + 20:32 + 22] = bytes((63, 0))
    struct.pack_into('<H', data, 32 + 22, 512)
    for index in (0, 16383):
        struct.pack_into('<H', data, 0x8000 + index * 2, 0x1001)
    # Distinct corner tiers, with the edge corner clamped to the final nibble.
    for index, tier in ((0, 1), (1, 2), (128, 3), (129, 4), (16383, 15)):
        data[0x4000 + index] = tier
    man = bytearray(0x2b)
    struct.pack_into('<16h', man, 2, *(n * 37 - 200 for n in range(16)))
    return bytes(data), bytes(man), TextureCatalog('map01', '0' * 64)


def expected_positions(data, lut):
    positions = []
    for index in range(16384):
        word = struct.unpack_from('<H', data, 0x8000 + index * 2)[0]
        if word & 0x1000:
            row, column = divmod(index, 128)
            for dx, dz in ((0, 0), (1, 0), (0, 1), (1, 1)):
                tier = data[0x4000 + min(row + dz, 127) * 128 + min(column + dx, 127)] & 15
                positions.append([(column + dx) * 128, -lut[tier], (row + dz) * 128])
    return positions


class WorldmapGeometryTests(unittest.TestCase):
    def decode(self, data, man, catalog):
        from importer.worldmap_geometry import decode_worldmap_geometry
        return decode_worldmap_geometry(data, man, catalog, scene='map01', source_record={})

    def test_independent_corner_heights_edge_clamp_and_missing_selector_no_fallback(self):
        data, man, catalog = fixture()
        before = deepcopy((data, man, catalog))
        report = self.decode(data, man, catalog)
        preview = report['preview']
        self.assertEqual(preview['vertices'], expected_positions(data, struct.unpack_from('<16h', man, 2)))
        self.assertEqual(preview['triangles'], [[0, 1, 2], [1, 3, 2], [4, 5, 6], [5, 7, 6]])
        self.assertEqual(preview['coordinate_system'], 'retail_field_y_down')
        self.assertTrue(all(texture['status'] != 'address_match' for texture in preview['textures']))
        self.assertTrue(all(material['tpage'] == 0 for material in preview['materials']))
        self.assertTrue(all(uv is None for uv in preview['triangle_uvs']))
        self.assertEqual((data, man, catalog), before)

    def test_selectors_preserve_atlas_v_direction_and_require_matched_source_texture(self):
        data, man, catalog = fixture()
        data = bytearray(data)
        data[32 + 21] = 1
        report = self.decode(bytes(data), man, catalog)
        preview = report['preview']
        self.assertEqual(preview['triangle_uvs'][:2], [[[224, 255], [255, 255], [224, 224]],
                                                    [[255, 255], [255, 224], [224, 224]]])
        self.assertTrue(all(texture['status'] != 'address_match' for texture in preview['textures']))
        self.assertTrue(all(material['tpage'] == 1 for material in preview['materials']))
        self.assertEqual(catalog.textures, [])

    def test_scene_input_source_and_geometry_budgets_fail_closed(self):
        from importer import worldmap_geometry
        data, man, catalog = fixture()
        for scene in ('town01', '../map01', '', None, True):
            with self.subTest(scene=scene), patch.object(worldmap_geometry, '_disc_context') as read, \
                    self.assertRaises(ImportError):
                worldmap_geometry.load_worldmap_geometry('never-read-disc', scene)
            read.assert_not_called()
        for malformed, bad_man in ((data[:-1], man), (data, man[:33]), ([], man), (data, [])):
            with self.subTest(data_type=type(malformed).__name__), self.assertRaises(ImportError):
                self.decode(malformed, bad_man, catalog)
        with patch.object(worldmap_geometry, 'MAX_CELLS', 1), self.assertRaises(ImportError):
            self.decode(data, man, catalog)


@unittest.skipUnless(os.environ.get('LEGAIA_DISC_BIN'), 'requires private unchanged retail disc')
class RetailWorldmapGeometryTests(unittest.TestCase):
    def check_kingdom(self, scene):
        from importer.worldmap_geometry import load_worldmap_geometry
        disc = os.environ['LEGAIA_DISC_BIN']
        with _disc_context(disc) as (_, disc_hash, mapping, archive):
            start, end = _bounded_scene_range(archive, mapping, scene)
            data = archive.read_entry(archive.entry(start), extended=True)
            bundle, raw = find_scene_bundle(archive, start, end)
            self.assertEqual(len(bundle.descriptors), 7)
            self.assertEqual(bundle.descriptors[2].type_byte, 3)
            descriptor = bundle.descriptors[2]
            at = bundle.table_offset + descriptor.data_offset
            man, consumed = decompress_lzs(raw[at:], descriptor.size)
            lut = struct.unpack_from('<16h', man, 2)
            before = (sha256(data).hexdigest(), sha256(raw).hexdigest(), sha256(man).hexdigest())
            report = load_worldmap_geometry(disc, scene)
            preview = report['preview']
            self.assertEqual(report['schema_version'], 'legaia.worldmap-geometry.v1')
            self.assertEqual(report['semantic_id'], f'asset://{scene}/worldmap/walk-ground')
            self.assertEqual(report['scene'], scene)
            self.assertEqual(preview['vertices'], expected_positions(data, lut))
            visible = sum(bool(struct.unpack_from('<H', data, 0x8000 + i * 2)[0] & 0x1000)
                          for i in range(16384))
            self.assertEqual(len(preview['vertices']), visible * 4)
            self.assertEqual(len(preview['triangles']), visible * 2)
            self.assertGreater(visible, 0)
            self.assertTrue(all(math.isfinite(value) for position in preview['vertices'] for value in position))
            for texture in preview['textures']:
                self.assertIn(texture['status'], ('address_match', 'missing', 'ambiguous', 'unsupported'))
                if texture['status'] == 'address_match':
                    self.assertGreater(len(texture['rgba']), 0)
                    self.assertEqual(len(texture['rgba']), 4 * len(texture['stp']))
                    self.assertTrue(texture['source_ids'])
                    self.assertTrue(all(identity.startswith(f'texture://{scene}/kingdom/') for identity in texture['source_ids']))
            self.assertEqual(before, (sha256(data).hexdigest(), sha256(raw).hexdigest(), sha256(man).hexdigest()))
            source = report['source_record']
            self.assertEqual(source['disc_sha256'], disc_hash)
            self.assertEqual(source['map_entry_index'], start)
            self.assertEqual(source['map_sha256'], before[0])
            self.assertEqual(source['man_slot']['slot_index'], 2)
            self.assertEqual(source['man_slot']['descriptor_type'], 3)
            self.assertEqual(source['man_slot']['decoded_sha256'], before[2])
            self.assertEqual(source['floor_lut_sha256'], sha256(man[2:34]).hexdigest())
            self.assertEqual(source['texture_slot']['slot_index'], 0)
            self.assertEqual(source['texture_slot']['descriptor_type'], 1)
            self.assertEqual(source['bundle_physical_byte_offset'], archive.entry(bundle.entry_index).start_lba * 2048 + bundle.table_offset)
            self.assertEqual(report['floor_height_lut'], list(lut))
            json.dumps(source, allow_nan=False)
            json.dumps(report['metrics'], allow_nan=False)
            self.assertTrue(report['limitations'])
            from importer.pipeline import import_scene
            from sdk.project import ProjectService, ProjectError
            from sdk.worldmap_authoring import state_key
            from sdk.worldmap_geometry import inspect
            private = Path(__file__).resolve().parents[3] / 'local-output/sdk-20260909'
            private.mkdir(parents=True, exist_ok=True)
            with tempfile.TemporaryDirectory(prefix='world-ground-readonly-', dir=private) as directory:
                project = ProjectService(Path(directory))
                project.import_metadata(import_scene(disc, 'town01'), disc)
                project.save()
                before_state = deepcopy((project._document(), project.imports, project.undo_stack,
                                         project.redo_stack, project.selected))
                files = {str(path.relative_to(project.root)): path.read_bytes()
                         for path in project.root.rglob('*') if path.is_file()}
                key = state_key(project)
                inspected = inspect(project, scene, key)
                self.assertEqual(inspected['preview']['vertices'], preview['vertices'])
                self.assertEqual(inspected['project_source_key'], key)
                self.assertEqual(inspected['representation'], 'retail-source')
                self.assertFalse(inspected['project_changed'])
                self.assertFalse(inspected['authored_geometry'])
                self.assertFalse(inspected['gameplay_verified'])
                self.assertEqual((project._document(), project.imports, project.undo_stack,
                                  project.redo_stack, project.selected), before_state)
                self.assertEqual({str(path.relative_to(project.root)): path.read_bytes()
                                  for path in project.root.rglob('*') if path.is_file()}, files)
                with patch('importer.worldmap_geometry.load_worldmap_geometry') as read:
                    with self.assertRaises(ProjectError):
                        inspect(project, scene, 'stale')
                    project.mode = 'live'
                    with self.assertRaises(ProjectError):
                        inspect(project, scene, state_key(project))
                    read.assert_not_called()

    def test_drake_kingdom_map01(self):
        self.check_kingdom('map01')

    def test_sebucus_kingdom_map02(self):
        self.check_kingdom('map02')

    def test_karisto_kingdom_map03(self):
        self.check_kingdom('map03')


if __name__ == '__main__':
    unittest.main()
