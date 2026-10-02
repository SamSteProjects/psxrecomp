"""Exact existing world-map menu-row writes without executable collateral edits."""
from copy import deepcopy
from hashlib import sha256
import os
import struct
import unittest

from importer.core import ImportError
from importer.worldmap_authoring import WorldMapAuthoringContext, load_worldmap_authoring_context
from importer.worldmap_menu import decode_worldmap_menu, load_worldmap_menu
from test_worldmap_menu import fixture


FIRST = 'worldmap://legaia/menu/placements/0000'
SECOND = 'worldmap://legaia/menu/placements/0001'
MAPPING = {0: 'map00', 123: 'exact', 456: 'other', 65535: 'end'}


class WorldMapAuthoringTests(unittest.TestCase):
    def context(self):
        data = bytes(fixture())
        return WorldMapAuthoringContext(data, MAPPING), data

    def test_noop_and_detached_options_preserve_full_source(self):
        context, data = self.context()
        options = context.options()
        self.assertEqual(options['source_executable_sha256'], sha256(data).hexdigest())
        self.assertEqual(options['placements'][0]['values'],
                         {'name_index': 2, 'discovery_flag_index': 39, 'destination_scene_id': 123,
                          'menu_position': {'x': 10, 'y': 20}})
        self.assertEqual(options['allowed_destinations'][1],
                         {'destination_scene_id': 123, 'destination_source_label': 'exact'})
        self.assertEqual(context.patch({}), (data, []))
        self.assertEqual(context.patch({FIRST: options['placements'][0]['values']}, original=data), (data, []))
        mutated = context.options()
        mutated['placements'][0]['values']['menu_position']['x'] = 88
        mutated['names'].clear(); mutated['allowed_destinations'].clear(); mutated['limitations'].clear()
        self.assertEqual(context.options(), options)

    def test_all_fields_exact_bytes_readback_and_opaque_preservation(self):
        context, data = self.context()
        values = {'name_index': 15, 'discovery_flag_index': 287, 'destination_scene_id': 65535,
                  'menu_position': {'x': 255, 'y': 0}}
        candidate, audit = context.patch({FIRST: values})
        expected = bytearray(data)
        struct.pack_into('<BBHBB', expected, 0x64298, 15, 255, 65535, 255, 0)
        self.assertEqual(candidate, bytes(expected)); self.assertEqual(len(audit), 1)
        row = audit[0]
        self.assertEqual(row['before_value'], context.options()['placements'][0]['values'])
        self.assertEqual(row['after_value'], values)
        self.assertEqual((row['entity_id'], row['record_index'], row['file_offset'], row['byte_length']),
                         (FIRST, 0, 0x64298, 6))
        self.assertEqual(row['scope'], 'worldmap-menu-record-only')
        self.assertEqual(row['candidate_executable_sha256'], sha256(candidate).hexdigest())
        self.assertEqual({change['file_offset']: (change['before_byte'], change['after_byte']) for change in row['changed_bytes']},
                         {i: (a, b) for i, (a, b) in enumerate(zip(data, candidate)) if a != b})
        before, after = decode_worldmap_menu(data), decode_worldmap_menu(candidate)
        self.assertEqual(before['placements'][1], after['placements'][1])
        self.assertEqual(before['names'], after['names'])
        self.assertEqual(candidate[:0x64298], data[:0x64298])
        self.assertEqual(candidate[0x6429e:], data[0x6429e:])
        self.assertEqual(after['placements'][0]['name'], 'Landmark 15')
        # Audit/value results do not share the caller's mutable dictionary.
        values['menu_position']['x'] = 1
        self.assertEqual(row['after_value']['menu_position']['x'], 255)

    def test_coincident_duplicate_names_source_order_and_deterministic_audits(self):
        data = fixture()
        struct.pack_into('<BBHBB', data, 0x6429e, 2, 9, 456, 10, 20)
        context = WorldMapAuthoringContext(bytes(data), MAPPING)
        values = context.options()['placements'][0]['values']
        values.update(destination_scene_id=0, discovery_flag_index=32, menu_position={'x': 0, 'y': 255})
        edits = {SECOND: values, FIRST: values}
        candidate, audit = context.patch(edits)
        self.assertEqual(context.patch(dict(reversed(list(edits.items())))), (candidate, audit))
        self.assertEqual([row['entity_id'] for row in audit], [FIRST, SECOND])
        decoded = decode_worldmap_menu(candidate)
        self.assertEqual(len(decoded['placements']), 2)
        self.assertEqual(decoded['placements'][0]['name'], decoded['placements'][1]['name'])
        self.assertEqual(decoded['placements'][0]['menu_position'], decoded['placements'][1]['menu_position'])

    def test_shapes_id_domain_and_original_guard_fail_closed(self):
        context, data = self.context(); valid = context.options()['placements'][0]['values']
        invalid = [{}, {'name_index': 1}, dict(valid, name_index=True), dict(valid, name_index=16),
                   dict(valid, name_index=-1), dict(valid, discovery_flag_index=31),
                   dict(valid, discovery_flag_index=288), dict(valid, discovery_flag_index=True),
                   dict(valid, destination_scene_id=122), dict(valid, destination_scene_id=-1),
                   dict(valid, destination_scene_id=65536), dict(valid, destination_scene_id=True),
                   dict(valid, menu_position={'x': True, 'y': 1}),
                   dict(valid, menu_position={'x': 256, 'y': 1}),
                   dict(valid, menu_position={'x': -1, 'y': 1}),
                   dict(valid, menu_position={'x': 1.0, 'y': 1}),
                   dict(valid, menu_position={'x': 1}), dict(valid, menu_position={'x': 1, 'y': 2, 'z': 3}),
                   dict(valid, label='invented'), []]
        for value in invalid:
            with self.subTest(value=value), self.assertRaises(ImportError): context.patch({FIRST: value})
        for edits in ([], {'bad': valid}, {FIRST.replace('0000', '0002'): valid}, {False: valid},
                      {f'worldmap://legaia/menu/placements/{i:04d}': valid for i in range(65)}):
            with self.assertRaises(ImportError): context.patch(edits)
        for wrong in (data[:-1], bytearray(data), b'bad', data[:0x800] + b'\xff' + data[0x801:]):
            with self.assertRaises(ImportError): context.patch({FIRST: valid}, original=wrong)
        self.assertEqual(context.patch({}), (data, []))

    def test_source_header_table_terminator_mapping_and_metadata_guards(self):
        baseline = fixture()
        invalid = [b'bad', bytes(baseline[:0x64000]), bytearray(baseline)]
        data = bytearray(baseline); data[0] = 0; invalid.append(bytes(data))
        data = bytearray(baseline); struct.pack_into('<I', data, 0x18, 0x80080000); invalid.append(bytes(data))
        data = bytearray(baseline); data[0x64298:0x64298 + 384] = bytes(384); invalid.append(bytes(data))
        # The decoder can walk into a printable name slot. Authoring rejects
        # the placement/terminator span before it can alias a landmark name.
        data = bytearray(baseline); data[0x64298:0x6431c] = bytes(132); data[0x6431c] = 255
        self.assertEqual(decode_worldmap_menu(bytes(data))['source_record']['terminator_record_index'], 22)
        invalid.append(bytes(data))
        data = bytearray(baseline); data[0x64318] = 1; invalid.append(bytes(data))
        for data in invalid:
            with self.assertRaises(ImportError): WorldMapAuthoringContext(data, MAPPING)
        for mapping in ({}, [], {True: 'bool'}, {-1: 'bad'}, {65536: 'bad'}, {1: ''},
                        {1: 'bad label'}, {1: 'é'}, {1: b'bad'}, {i: 'x' for i in range(4097)}):
            with self.assertRaises(ImportError): WorldMapAuthoringContext(bytes(baseline), mapping)
        for source in ([], {'payload': b'bad'}, {'disc_sha256': 'bad'}, {'cdname_sha256': 'F' * 64}):
            with self.assertRaises(ImportError): WorldMapAuthoringContext(bytes(baseline), MAPPING, source)
        source = {'disc_sha256': 'a' * 64, 'cdname_sha256': 'b' * 64}
        context = WorldMapAuthoringContext(bytes(baseline), MAPPING, source)
        source['disc_sha256'] = 'c' * 64
        self.assertEqual(context.options()['source_record']['disc_sha256'], 'a' * 64)
        self.assertEqual(context.options()['destination_label_source']['sha256'], 'b' * 64)


@unittest.skipUnless(os.environ.get('LEGAIA_DISC_BIN'), 'requires private retail disc')
class RetailWorldMapAuthoringTests(unittest.TestCase):
    def test_fresh_retail_source_exact_row_write_and_readback(self):
        path = os.environ['LEGAIA_DISC_BIN']
        context = load_worldmap_authoring_context(path)
        options = context.options(); original = context._executable
        retail = load_worldmap_menu(path)
        self.assertEqual(options['source_record'], retail['source_record'])
        self.assertEqual(options['names'], retail['names'])
        self.assertEqual(options['source_record']['sha256'], '292256e2e66db42727f613406785e444254d3f699569e611f65fcf1c6d2f3482')
        self.assertEqual(len(options['placements']), 20)
        self.assertEqual(options['source_record']['terminator_record_index'], 20)
        self.assertEqual(options['source_record']['name_table_file_offset'] -
                         (options['source_record']['table_file_offset'] + 21 * 6), 2)
        entries = {row['semantic_id']: row['values'] for row in options['placements']}
        self.assertEqual(context.patch(entries, original=original), (original, []))
        value = deepcopy(entries[FIRST]); value['menu_position']['x'] += 1
        candidate, audit = context.patch({FIRST: value}, original=original)
        self.assertEqual([i for i, (a, b) in enumerate(zip(original, candidate)) if a != b], [0x6429c])
        self.assertEqual(audit[0]['changed_bytes'], [{'file_offset': 0x6429c, 'before_byte': 96, 'after_byte': 97}])
        decoded = decode_worldmap_menu(candidate)
        self.assertEqual(decoded['placements'][0]['menu_position'], {'x': 97, 'y': 25})
        self.assertEqual(decoded['placements'][1:], decode_worldmap_menu(original)['placements'][1:])
        self.assertEqual(decoded['names'], options['names'])
        self.assertEqual(context._executable, original)


if __name__ == '__main__': unittest.main()
