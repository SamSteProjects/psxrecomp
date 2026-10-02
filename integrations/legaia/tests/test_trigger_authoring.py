"""Primary trigger X/Z writes preserve destinations, binding bytes and other MAP data."""
from hashlib import sha256
import json
import os
from pathlib import Path
import struct
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from importer.core import ImportError, ProtEntry
from importer.field_map import _decode
from importer.trigger_authoring import (MAX_PRIMARY_TRIGGER_RECORDS, patch_field_triggers,
                                        trigger_authoring_options)


SCENE = 'fixture'


def source_map():
    data = bytearray((index * 37 + 11) & 255 for index in range(0x12000))
    tables = {0: (0x20, [(4, 5, 63, 63), (4, 5, 255, 0)]),
              1: (0x40, [(8, 9, 35, 0), (8, 9, 38, 1), (255, 0, 200, 7)]),
              2: (0x60, [(6, 7, 128, 0xAB), (8, 9, 5, 0xFF)]),
              3: (0x70, [(3, 7, 5, 9, 0, 0x91, 0xAB, 0xEF), (5, 9, 5, 9, 7, 1, 2, 3)])}
    for kind, (offset, rows) in tables.items():
        struct.pack_into('<hh', data, 0x10002 + 4 * kind, offset, len(rows))
        stride = 8 if kind == 3 else 4
        for index, row in enumerate(rows):
            start = 0x10000 + offset + index * stride
            data[start:start + stride] = bytes(row)
    return bytes(data)


def edit(kind=0, index=0, **values):
    row = next(row for row in trigger_authoring_options(source_map(), SCENE)['records']
               if row['table_kind'] == kind and row['record_index'] == index)
    return {'trigger_id': row['trigger_id'], 'tile_x': row['encoded']['tile_x'],
            'tile_z': row['encoded']['tile_z'], **values}


class TriggerAuthoringTests(unittest.TestCase):
    def test_options_match_imported_rows_and_detach_metadata_without_payload(self):
        source = source_map()
        options = trigger_authoring_options(source, SCENE)
        catalog = _decode(SCENE, '0' * 64, ProtEntry(1, 100, 8, 36), source, None)[0]
        imported = [row for row in catalog['assets'] if row['asset_kind'] == 'trigger']
        self.assertEqual(options['source_sha256'], sha256(source).hexdigest())
        self.assertEqual([(row['table_kind'], row['record_index']) for row in options['records']],
                         [(0, 0), (0, 1), (1, 0), (1, 1), (1, 2)])
        for row, asset in zip(options['records'], imported):
            self.assertEqual(row['trigger_id'], asset['semantic_id'])
            self.assertEqual(row['encoded'], asset['encoded'])
            self.assertEqual(row['byte_offset'], asset['source_record']['byte_offset'])
            self.assertEqual(row['byte_length'], 4)
            self.assertEqual(row['sha256'], asset['source_record']['sha256'])
            self.assertEqual(row['tile_bounds'], {'x_min': row['encoded']['tile_x'],
                             'x_max': row['encoded']['tile_x'] + 1,
                             'z_min': row['encoded']['tile_z'], 'z_max': row['encoded']['tile_z'] + 1})
        self.assertEqual(set(options['records'][0]), {'trigger_id', 'table_kind', 'record_index',
                         'byte_offset', 'byte_length', 'sha256', 'encoded', 'tile_bounds'})
        json.dumps(options)
        options['records'][0]['encoded']['tile_x'] = 99
        options['records'][0]['tile_bounds']['x_min'] = 99
        self.assertEqual(trigger_authoring_options(source, SCENE)['records'][0]['encoded']['tile_x'], 4)
        self.assertEqual(trigger_authoring_options(source, SCENE)['records'][0]['tile_bounds']['x_min'], 4)

    def test_empty_and_inherited_edits_are_byte_identical(self):
        source = source_map()
        digest = sha256(source).hexdigest()
        self.assertEqual(patch_field_triggers(source, digest, SCENE, []), (source, []))
        edits = [edit(row['table_kind'], row['record_index'])
                 for row in trigger_authoring_options(source, SCENE)['records']]
        self.assertEqual(patch_field_triggers(source, digest, SCENE, edits), (source, []))
        empty = bytearray(source)
        for kind in (0, 1):
            struct.pack_into('<hh', empty, 0x10002 + 4 * kind, 0, 0)
        empty = bytes(empty)
        self.assertEqual(trigger_authoring_options(empty, SCENE)['records'], [])
        self.assertEqual(patch_field_triggers(empty, sha256(empty).hexdigest(), SCENE, []), (empty, []))

    def test_only_coordinates_change_and_all_diffs_have_exact_byte_audits(self):
        source = source_map()
        edits = [edit(0, 0, tile_x=1, tile_z=2), edit(1, 0, tile_x=250, tile_z=251),
                 edit(1, 1, tile_x=250, tile_z=251), edit(1, 2, tile_x=252, tile_z=253)]
        result, audit = patch_field_triggers(source, sha256(source).hexdigest(), SCENE, edits[::-1])
        self.assertEqual((result, audit), patch_field_triggers(source, sha256(source).hexdigest(), SCENE, edits))
        expected = bytearray(source)
        by_id = {row['trigger_id']: row for row in trigger_authoring_options(source, SCENE)['records']}
        expected_audit = []
        for item in edits:
            row = by_id[item['trigger_id']]
            for delta, field in enumerate(('tile_x', 'tile_z')):
                offset = row['byte_offset'] + delta
                expected[offset] = item[field]
                expected_audit.append({'trigger_id': item['trigger_id'], 'table_kind': row['table_kind'],
                    'record_index': row['record_index'], 'field': 'trigger.' + field,
                    'byte_offset': offset, 'before_value': source[offset], 'after_value': item[field],
                    'scope': 'source-MAP-trigger-cell-only'})
            self.assertEqual(result[row['byte_offset'] + 2:row['byte_offset'] + 4],
                             source[row['byte_offset'] + 2:row['byte_offset'] + 4])
        self.assertEqual(result, bytes(expected))
        self.assertEqual(audit, expected_audit)
        self.assertEqual({offset for offset, pair in enumerate(zip(source, result)) if pair[0] != pair[1]},
                         {row['byte_offset'] for row in audit})
        self.assertEqual(patch_field_triggers(result, sha256(result).hexdigest(), SCENE, edits), (result, []))
        # Unknown gate 7 remains exactly 7; known coordinates can move without
        # inventing script semantics, object-grid paints or runtime activation.
        self.assertEqual(trigger_authoring_options(result, SCENE)['records'][-1]['encoded'],
                         {'tile_x': 252, 'tile_z': 253, 'record_index': 200, 'gate': 7})

    def test_coincident_cells_keep_distinct_source_identities_and_order(self):
        source = source_map()
        options = trigger_authoring_options(source, SCENE)
        edits = [{'trigger_id': row['trigger_id'], 'tile_x': 255, 'tile_z': 0} for row in options['records']]
        result, _ = patch_field_triggers(source, options['source_sha256'], SCENE, edits)
        current = trigger_authoring_options(result, SCENE)
        self.assertEqual([row['trigger_id'] for row in current['records']],
                         [row['trigger_id'] for row in options['records']])
        self.assertTrue(all(row['tile_bounds'] == {'x_min': 255, 'x_max': 256,
                         'z_min': 0, 'z_max': 1} for row in current['records']))
        for before, after in zip(options['records'], current['records']):
            for field in ('dest_x', 'dest_z', 'record_index', 'gate'):
                if field in before['encoded']:
                    self.assertEqual(before['encoded'][field], after['encoded'][field])

    def test_invalid_shapes_identities_byte_values_duplicates_and_hashes_fail_closed(self):
        source, item = source_map(), edit()
        digest = sha256(source).hexdigest()
        invalid = [None, {}, [None], [item, item], [item] * (MAX_PRIMARY_TRIGGER_RECORDS + 1),
                   [{key: value for key, value in item.items() if key != 'tile_z'}]]
        for forbidden in ('dest_x', 'dest_z', 'record_index', 'gate', 'table_kind', 'height'):
            invalid.append([{**item, forbidden: 0}])
        for identifier in (None, {}, 'trigger://other/field-map/primary/kind-0/0000',
                           'trigger://fixture/field-map/fallback/kind-1/0000',
                           'trigger://fixture/field-map/primary/kind-2/0000',
                           'trigger://fixture/field-map/primary/kind-0/0002',
                           'trigger://fixture/field-map/primary/kind-0/0', item['trigger_id'] + '/',
                           'region://fixture/field-map/primary/0000'):
            invalid.append([{**item, 'trigger_id': identifier}])
        for field in ('tile_x', 'tile_z'):
            for value in (True, -1, 256, 1.0, '1', None):
                invalid.append([{**item, field: value}])
        for edits in invalid:
            with self.subTest(edits=str(edits)[:90]), self.assertRaises(ImportError):
                patch_field_triggers(source, digest, SCENE, edits)
        for stale in (None, {}, '0' * 64, digest.upper(), digest[:-1]):
            with self.subTest(hash=stale), self.assertRaises(ImportError):
                patch_field_triggers(source, stale, SCENE, [])

    def test_all_table_spans_and_source_footprints_are_qualified_even_without_edits(self):
        source = source_map()
        for invalid in (None, bytearray(source), source[:-1], source + b'\0'):
            with self.subTest(source_type=type(invalid)), self.assertRaises(ImportError):
                trigger_authoring_options(invalid, SCENE)
        for scene in (None, '', '../fixture', 'é', 'fixture/primary'):
            with self.subTest(scene=scene), self.assertRaises(ImportError):
                trigger_authoring_options(source, scene)
        for kind in range(4):
            for offset, count in ((-1, 0), (0, -1), (17, 1), (0x1FFF, 1), (0x20, 32767)):
                bad = bytearray(source)
                struct.pack_into('<hh', bad, 0x10002 + 4 * kind, offset, count)
                bad = bytes(bad)
                with self.subTest(kind=kind, bounds=(offset, count)), self.assertRaises(ImportError):
                    patch_field_triggers(bad, sha256(bad).hexdigest(), SCENE, [])
        for kind, offset in ((1, 0x20), (2, 0x20), (3, 0x40), (3, 0x60)):
            bad = bytearray(source)
            struct.pack_into('<h', bad, 0x10002 + 4 * kind, offset)
            with self.subTest(overlap=(kind, offset)), self.assertRaisesRegex(ImportError, 'overlap'):
                trigger_authoring_options(bytes(bad), SCENE)

    def test_physical_row_budget_accepts_last_row_without_truncation(self):
        source = bytearray(0x12000)
        struct.pack_into('<hh', source, 0x10002, 18, MAX_PRIMARY_TRIGGER_RECORDS)
        source = bytes(source)
        options = trigger_authoring_options(source, SCENE)
        self.assertEqual(len(options['records']), 2043)
        last = options['records'][-1]
        self.assertEqual(last['trigger_id'], 'trigger://fixture/field-map/primary/kind-0/2042')
        requested = {'trigger_id': last['trigger_id'], 'tile_x': 255, 'tile_z': 255}
        result, audit = patch_field_triggers(source, options['source_sha256'], SCENE, [requested])
        self.assertEqual([row['byte_offset'] for row in audit], [last['byte_offset'], last['byte_offset'] + 1])
        self.assertEqual(len(result), 0x12000)
        overflow = bytearray(source)
        struct.pack_into('<h', overflow, 0x10004, MAX_PRIMARY_TRIGGER_RECORDS + 1)
        with self.assertRaises(ImportError):
            trigger_authoring_options(bytes(overflow), SCENE)


@unittest.skipUnless(os.environ.get('LEGAIA_DISC_BIN'), 'requires private retail disc')
class RetailTriggerAuthoringTests(unittest.TestCase):
    def test_town01_exact_fresh_primary_source_write_and_immutable_payloads(self):
        from importer.field_map import load_field_map_catalog
        from importer.pipeline import _bounded_scene_range, _disc_context
        disc = os.environ['LEGAIA_DISC_BIN']
        with _disc_context(disc) as (_, _, mapping, archive):
            start, _ = _bounded_scene_range(archive, mapping, 'town01')
            source = archive.read_entry(archive.entry(start), extended=True)
            catalog = load_field_map_catalog(disc, 'town01')
        options = trigger_authoring_options(source, 'town01')
        primary = [row for row in catalog['assets'] if row['asset_kind'] == 'trigger' and
                   row['table_source'] == 'primary']
        self.assertEqual(len(options['records']), 48)
        self.assertEqual(options['source_sha256'],
                         '60ecaa14978708f8696d60c12f6e98a88cdb19c2e63c7cae8f1c967a1214eb3b')
        for row, asset in zip(options['records'], primary):
            self.assertEqual(row['trigger_id'], asset['semantic_id'])
            self.assertEqual(row['sha256'], asset['source_record']['sha256'])
            self.assertEqual(row['encoded'], asset['encoded'])
        inherited = [{'trigger_id': row['trigger_id'], 'tile_x': row['encoded']['tile_x'],
                      'tile_z': row['encoded']['tile_z']} for row in options['records']]
        self.assertEqual(patch_field_triggers(source, options['source_sha256'], 'town01', inherited), (source, []))
        row = options['records'][0]
        requested = {'trigger_id': row['trigger_id'], 'tile_x': (row['encoded']['tile_x'] + 1) % 256,
                     'tile_z': (row['encoded']['tile_z'] + 1) % 256}
        result, audit = patch_field_triggers(source, options['source_sha256'], 'town01', [requested])
        self.assertEqual(len(audit), 2)
        self.assertEqual([index for index, pair in enumerate(zip(source, result)) if pair[0] != pair[1]],
                         [row['byte_offset'], row['byte_offset'] + 1])
        self.assertEqual(result[row['byte_offset'] + 2:row['byte_offset'] + 4],
                         source[row['byte_offset'] + 2:row['byte_offset'] + 4])
        self.assertEqual(sha256(source).hexdigest(), options['source_sha256'])


if __name__ == '__main__':
    unittest.main()
