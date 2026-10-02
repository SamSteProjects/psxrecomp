"""Source footprints invert the two distinct retail field quantizers."""
from copy import deepcopy
from pathlib import Path
import struct
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from importer.core import ProtEntry
from importer.field_map import _decode
from sdk.field_spatial import build_field_spatial
from sdk.project import ProjectError


def table(kinds):
    block = bytearray(0x2000)
    offset = 18
    for kind in range(4):
        rows = kinds.get(kind, [])
        struct.pack_into('<hh', block, kind * 4 + 2, offset, len(rows))
        for row in rows:
            block[offset:offset + len(row)] = bytes(row)
            offset += len(row)
    return bytes(block)


def preview(primary=None, fallback=None):
    primary = {0: [(0, 127, 2, 3)],
               1: [(8, 9, 10, 0), (8, 9, 11, 1)],
               3: [(6, 4, 6, 4, 3, 0, 0, 0)]} if primary is None else primary
    fallback = {1: [(8, 9, 12, 7), (8, 9, 13, 1)]} if fallback is None else fallback
    data = bytes(0x10000) + table(primary)
    catalog, _ = _decode('fixture', 'a' * 64, ProtEntry(4, 100, 8, 36), data,
                         (ProtEntry(5, 136, 8, 8), table(fallback)))
    return {'asset': catalog['assets'][0], 'coordinate_system': 'psx_guest_xz',
            'triggers': [row for row in catalog['assets'] if row['asset_kind'] == 'trigger'],
            'regions': [row for row in catalog['assets'] if row['asset_kind'] == 'region']}


def replace(value, path, replacement):
    target = value
    for key in path[:-1]:
        target = target[key]
    target[path[-1]] = replacement


class FieldSpatialTests(unittest.TestCase):
    def test_restores_source_order_preserves_duplicates_and_detaches_metadata(self):
        source = preview()
        original = deepcopy(source)
        document = build_field_spatial(source)
        records = document['records']
        self.assertEqual([row['id'] for row in records], [
            'trigger://fixture/field-map/primary/kind-0/0000',
            'trigger://fixture/field-map/primary/kind-1/0000',
            'trigger://fixture/field-map/primary/kind-1/0001',
            'region://fixture/field-map/primary/0000',
            'trigger://fixture/field-map/fallback/kind-1/0000',
            'trigger://fixture/field-map/fallback/kind-1/0001'])
        self.assertEqual([row['trigger_type'] for row in records],
                         ['intra_scene_teleport', 'object_bind', 'partition_2_trigger',
                          None, 'unknown_gate', 'partition_2_trigger'])
        self.assertEqual(records[1]['world_bounds'], records[2]['world_bounds'])
        self.assertEqual(records[1]['world_bounds'], records[4]['world_bounds'])
        self.assertEqual(records[0]['world_center'], {'x': 64, 'y': 0, 'z': 16320})
        expected_keys = {'id', 'kind', 'label', 'table_source', 'table_kind', 'record_index',
                         'trigger_type', 'world_bounds', 'world_center', 'source_tile_bounds',
                         'source_record', 'activation', 'height_status'}
        for row in records:
            self.assertEqual(set(row), expected_keys)
            self.assertEqual((row['activation'], row['height_status'], row['world_center']['y']),
                             ('not_evaluated', 'unknown', 0))
        self.assertEqual(document, build_field_spatial(source))
        records[0]['source_record']['disc']['sha256'] = 'b' * 64
        records[1]['source_tile_bounds'].clear()
        records[3]['world_bounds'].clear()
        document['quantization']['trigger']['world_bias'] = 3
        self.assertEqual(source, original)

    def test_trigger_cells_use_raw_quantization_including_byte_domain_edges(self):
        source = preview({0: [(tile, 255 - tile, 1, 2) for tile in range(256)]}, {})
        document = build_field_spatial(source)
        self.assertEqual(document['quantization']['trigger'],
                         {'tile_size': 128, 'world_bias': 0, 'rule': 'tile = world >> 7'})
        for tile, record in enumerate(document['records']):
            bounds = record['world_bounds']
            for axis, expected in (('x', tile), ('z', 255 - tile)):
                low, high = bounds[axis + '_min'], bounds[axis + '_max']
                self.assertEqual(high - low, 128)
                self.assertEqual([value >> 7 for value in (low, low + 1, high - 1)], [expected] * 3)
                self.assertEqual((low - 1) >> 7, expected - 1)
                self.assertEqual(high >> 7, expected + 1)
        self.assertEqual(document['records'][-1]['world_bounds']['x_max'], 32768)
        self.assertEqual(document['records'][-1]['activation'], 'not_evaluated')

    def test_regions_normalize_reversed_and_degenerate_bounds_with_signed_bias(self):
        source = preview({3: [(255, 0, 255, 0, 0, 0, 0, 0),
                              (10, 9, 2, 3, 1, 0, 0, 0)]}, {})
        document = build_field_spatial(source)
        self.assertEqual(document['quantization']['region'],
                         {'tile_size': 128, 'world_bias': 64, 'rule': 'tile = (world - 64) >> 7'})
        first, second = document['records']
        self.assertEqual(first['source_tile_bounds'], {'x_min': 255, 'x_max': 257, 'z_min': -2, 'z_max': 0})
        self.assertEqual(first['world_bounds'], {'x_min': 32704, 'x_max': 32960, 'z_min': -192, 'z_max': 64})
        self.assertEqual(first['world_center'], {'x': 32832, 'y': 0, 'z': -64})
        self.assertEqual(second['source_tile_bounds'], {'x_min': 2, 'x_max': 10, 'z_min': 3, 'z_max': 9})
        for record in (first, second):
            for axis in ('x', 'z'):
                low, high = (record['world_bounds'][axis + end] for end in ('_min', '_max'))
                tlo, thi = (record['source_tile_bounds'][axis + end] for end in ('_min', '_max'))
                self.assertEqual((low - 64) >> 7, tlo)
                self.assertEqual((high - 1 - 64) >> 7, thi - 1)
                self.assertEqual((low - 1 - 64) >> 7, tlo - 1)
                self.assertEqual((high - 64) >> 7, thi)
        bad = deepcopy(source)
        bad['regions'][0]['tile_bounds']['z_min'] = 0
        with self.assertRaises(ProjectError):
            build_field_spatial(bad)

    def test_source_identity_shapes_hashes_and_sizes_fail_closed(self):
        source = preview()
        cases = [
            (('coordinate_system',), 'editor'),
            (('triggers', 0, 'encoded', 'tile_x'), 5),
            (('asset', 'semantic_id'), 'collision://other/field-map'),
            (('asset', 'source_record', 'byte_length'), 1),
            (('asset', 'source_record', 'disc', 'serial'), 'other'),
            (('triggers', 0, 'semantic_id'), 'trigger://fixture/field-map/primary/kind-0/0001'),
            (('triggers', 0, 'record_index'), True),
            (('triggers', 0, 'table_kind'), True),
            (('triggers', 0, 'encoded', 'tile_x'), -1),
            (('triggers', 0, 'encoded', 'tile_x'), True),
            (('triggers', 0, 'encoded', 'tile_z'), 256),
            (('triggers', 0, 'destination_world', 'x'), 0),
            (('triggers', 1, 'script_reference', 'partition'), True),
            (('triggers', 0, 'source_record', 'prot_entry_name'), 'other'),
            (('triggers', 0, 'source_record', 'disc', 'sha256'), 'b' * 64),
            (('triggers', 0, 'source_record', 'sha256'), 'g' * 64),
            (('triggers', 0, 'source_record', 'containing_span_sha256'), 'a'),
            (('triggers', 0, 'source_record', 'byte_length'), 8),
            (('triggers', 0, 'source_record', 'byte_offset'), 0x12000),
            (('triggers', 0, 'source_record', 'containing_span_byte_offset'), 0),
            (('triggers', 0, 'source_record', 'containing_span_byte_length'), 1),
            (('triggers', 0, 'source_record', 'record_index'), 1),
            (('triggers', 0, 'source_record', 'table_kind'), 1),
            (('triggers', 0, 'source_record', 'prot_entry_index'), 3),
            (('triggers', 3, 'source_record', 'prot_start_lba'), 137),
            (('regions', 0, 'tile_bounds', 'x_max'), 9),
            (('regions', 0, 'source_record', 'byte_length'), 4),
        ]
        for path, value in cases:
            bad = deepcopy(source)
            replace(bad, path, value)
            with self.subTest(path=path, value=value), self.assertRaises(ProjectError):
                build_field_spatial(bad)
        for payload in ({'world_bounds': {'x_min': 0}}, {'source_record': dict(source['triggers'][0]['source_record'], raw_hex='00')}):
            bad = deepcopy(source)
            bad['triggers'][0].update(payload)
            with self.subTest(payload=payload), self.assertRaises(ProjectError):
                build_field_spatial(bad)

    def test_duplicates_row_aliases_missing_indices_and_bounds_are_rejected(self):
        source = preview()
        duplicate = deepcopy(source)
        duplicate['triggers'].append(deepcopy(duplicate['triggers'][0]))
        missing = deepcopy(source)
        del missing['triggers'][1]
        inconsistent = deepcopy(source)
        inconsistent['triggers'][1]['source_record']['containing_span_sha256'] = 'b' * 64
        aliased = deepcopy(source)
        offset = aliased['triggers'][0]['source_record']['byte_offset']
        aliased['triggers'][1]['source_record']['byte_offset'] = offset
        aliased['triggers'][2]['source_record']['byte_offset'] = offset + 4
        oversized = deepcopy(source)
        oversized['triggers'] = [source['triggers'][0]] * 4097
        for bad in (duplicate, missing, inconsistent, aliased, oversized):
            with self.assertRaises(ProjectError):
                build_field_spatial(bad)
        empty = build_field_spatial(preview({}, {}))
        self.assertEqual(empty['records'], [])
        self.assertEqual(empty['scene_id'], 'scene://fixture')


if __name__ == '__main__':
    unittest.main()
