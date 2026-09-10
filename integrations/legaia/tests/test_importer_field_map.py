"""Independent lookup inversion, bounded tables and private retail evidence."""
from contextlib import nullcontext
import json
import os
from pathlib import Path
import struct
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from importer.core import ImportError, ProtEntry
from importer.field_map import _decode, _rectangles, load_field_map_catalog, preview_field_map


def block():
    data = bytearray(0x2000)
    struct.pack_into('<hh', data, 2, 18, 1)
    data[18:22] = bytes([4, 5, 6, 7])
    struct.pack_into('<hh', data, 6, 24, 2)
    data[24:32] = bytes([8, 9, 10, 0, 8, 9, 11, 1])
    struct.pack_into('<hh', data, 14, 34, 1)
    data[34:42] = bytes([6, 4, 6, 4, 3, 0, 0, 0])
    return data


class FieldMapTests(unittest.TestCase):
    def setUp(self):
        self.entry = ProtEntry(1, 100, 8, 36)
        self.following = ProtEntry(2, 136, 8, 8)
        self.data = bytearray(0x12000)
        self.data[0x10000:] = block()
        self.data[0x4000] = 0xF0  # Negative-Z row is not drawable.
        self.data[0x4000 + 128] = 0xF3
        self.fallback = block()
        self.fallback[27] = 7  # Unsupported gate survives as explicit unknown.

    def decode(self):
        return _decode('fixture', '0' * 64, self.entry, bytes(self.data),
                       (self.following, bytes(self.fallback)))

    def test_catalog_has_stable_provenance_no_payload_and_preserves_duplicates(self):
        report, grid = self.decode()
        self.assertEqual(report, self.decode()[0])
        self.assertEqual(len(report['assets']), 7)
        collision = report['assets'][0]
        self.assertEqual((collision['wall_cell_count'], collision['blocked_subcell_count']), (2, 8))
        self.assertEqual(collision['source_record']['byte_offset'], 0x4000)
        self.assertEqual(collision['source_record']['prot_entry_name'], 'fixture')
        ids = [a['semantic_id'] for a in report['assets']]
        self.assertEqual(len(ids), len(set(ids)))
        teleport, bind, trigger, region, unknown, fallback = report['assets'][1:]
        self.assertEqual(teleport['destination_world'], {'x': 448, 'z': 512})
        self.assertEqual(bind['script_reference']['partition'], 0)
        self.assertEqual(bind['table_kind'], 1)
        self.assertEqual(trigger['script_reference']['partition'], 2)
        self.assertEqual(region['tile_bounds'], {'x_min': 6, 'x_max': 8, 'z_min': 2, 'z_max': 4})
        self.assertEqual(unknown['status'], 'unknown_gate')
        self.assertIsNone(unknown['script_reference']['partition'])
        self.assertEqual(fallback['table_source'], 'fallback')
        self.assertEqual(fallback['source_record']['prot_entry_index'], 2)
        self.assertEqual(fallback['source_record']['byte_offset'], 28)
        encoded = json.dumps(report)
        for key in ('"data"', '"grid"', '"raw_hex"', '"rectangles"', '"text"'):
            self.assertNotIn(key, encoded)

    def test_every_rectangle_inverts_reference_lookup_including_integer_edges(self):
        # All 65,024 canonical quadrants, not only hand-picked cell centers.
        rectangles = _rectangles(bytes([0xF0]) * 16384)
        self.assertEqual(len(rectangles), 127 * 128 * 4)
        for rect in rectangles:
            for x, z in ((rect['x_min'] + 1, rect['z_min']),
                         (rect['x_max'], rect['z_max'] - 1)):
                zc = (z >> 6) + 2
                xc = ((x + 0x3F) >> 6) - 1
                col = int(xc / 2) & 127  # Rust division truncates toward zero.
                row = (zc - (zc >> 31)) >> 1
                quadrant = ((zc & 1) << 1) | (xc & 1)
                self.assertEqual((col, row, quadrant), (rect['column'], rect['row'], rect['quadrant']))
        # Lower nibble is not a wall, and row0 is intentionally excluded.
        grid = bytearray([15] * 16384)
        grid[0] = 0xF0
        self.assertEqual(_rectangles(bytes(grid)), [])

    def test_ramp_adjustments_preserve_signed_values_quadrants_and_lookup_order(self):
        struct.pack_into('<hh', self.data, 0x1000A, 44, 2)
        self.data[0x1002C:0x10034] = bytes([25, 26, 252, 0xE4, 25, 26, 128, 0])
        struct.pack_into('<hh', self.fallback, 10, 44, 1)
        self.fallback[44:48] = bytes([25, 26, 127, 0x1B])
        collision = self.decode()[0]['assets'][0]
        rows = collision['elevation_overrides']
        self.assertEqual(collision['elevation_override_count'], 3)
        self.assertEqual([r['table_source'] for r in rows], ['primary', 'primary', 'fallback'])
        self.assertEqual([r['coarse_signed'] for r in rows], [-4, -128, 127])
        self.assertEqual([r['subcell_delta_y'] for r in rows],
                         [[128, 112, 96, 80], [4096] * 4, [-4112, -4096, -4080, -4064]])
        self.assertEqual(rows[0]['source_record']['byte_offset'], 0x1002C)
        self.assertEqual(rows[2]['source_record']['byte_offset'], 44)
        self.assertEqual(rows[2]['source_record']['prot_entry_index'], 2)

    def test_malformed_tables_and_wrong_footprint_fail_closed(self):
        for header, value in ((2, -1), (4, -1), (2, 0), (4, 32767), (6, 20)):
            bad = bytearray(self.data)
            struct.pack_into('<h', bad, 0x10000 + header, value)
            with self.subTest(header=header, value=value), self.assertRaises(ImportError):
                _decode('fixture', '0' * 64, self.entry, bytes(bad), None)
        with self.assertRaises(ImportError):
            _decode('fixture', '0' * 64, self.entry, bytes(self.data[:-1]), None)
        with self.assertRaises(ImportError):
            _decode('fixture', '0' * 64, self.entry, bytes(self.data), (self.following, b'\0' * 18))
        for offset, count in ((19, 1), (8190, 1), (-1, 0), (0, -1)):
            bad = bytearray(self.data)
            struct.pack_into('<hh', bad, 0x1000A, offset, count)
            with self.subTest(kind2=(offset, count)), self.assertRaises(ImportError):
                _decode('fixture', '0' * 64, self.entry, bytes(bad), None)

    def test_loader_reads_extended_first_entry_and_only_bounded_contiguous_fallback(self):
        reads = []
        archive = SimpleNamespace(SECTOR=2048, entries=[self.entry, self.following],
            node=SimpleNamespace(extent_lba=50, size=1000000),
            entry=lambda n: self.entry if n == 1 else self.following,
            read_entry=lambda entry, extended: reads.append(('map', entry.index, extended)) or bytes(self.data),
            image=SimpleNamespace(read_user=lambda *args: reads.append(args) or bytes(self.fallback)))
        with patch('importer.field_map._disc_context', side_effect=lambda _: nullcontext((None, '0' * 64, {}, archive))), \
             patch('importer.field_map._bounded_scene_range', return_value=(1, 3)):
            catalog = load_field_map_catalog('disc', 'fixture')
            preview = preview_field_map('disc', 'fixture', catalog['assets'][0]['semantic_id'])
            self.assertEqual(len(preview['rectangles']), 4)
            self.assertEqual(preview['excluded_subcell_count'], 4)
            self.assertEqual(reads[0], ('map', 1, True))
            self.assertEqual(reads[1], (50, 136 * 2048, 0x2000, 1000000))
            self.following = ProtEntry(2, 137, 8, 8)
            reads.clear()
            report = load_field_map_catalog('disc', 'fixture')
            self.assertEqual(len(reads), 1)
            self.assertTrue(any('Fallback trigger table unavailable' in s for s in report['limitations']))
            self.entry = ProtEntry(1, 100, 8, 35)
            with self.assertRaisesRegex(ImportError, 'footprint'):
                load_field_map_catalog('disc', 'fixture')
        for scene in (None, '', '../fixture', 'é'):
            with self.assertRaises(ImportError):
                load_field_map_catalog('disc', scene)
        for asset in (None, {}, 'collision://other/field-map', 'trigger://fixture/field-map'):
            with self.assertRaises(ImportError):
                preview_field_map('disc', 'fixture', asset)


@unittest.skipUnless(os.environ.get('LEGAIA_DISC_BIN'), 'requires private retail disc')
class RetailFieldMapTests(unittest.TestCase):
    def test_town01_source_counts_hashes_and_private_preview(self):
        from importer.pipeline import _disc_context
        disc = os.environ['LEGAIA_DISC_BIN']
        with _disc_context(disc):
            report = load_field_map_catalog(disc, 'town01')
            collision = report['assets'][0]
            self.assertEqual(collision['source_record']['prot_entry_index'], 1)
            self.assertEqual(collision['source_record']['prot_start_lba'], 203)
            self.assertEqual(collision['source_record']['sha256'],
                             'a216ec1aff2e26fda5235fd63d9f6c75ae13fb623719a02f8fdba0d03f7718d6')
            self.assertEqual((collision['wall_cell_count'], collision['blocked_subcell_count']), (1297, 4228))
            self.assertEqual(len(report['assets']), 1 + 11 + 37 + 14 + 51)
            # Same unmodified town01 tiles as private cold-run checkpoint09/10.
            ramps = collision['elevation_overrides']
            for tile, expected in (((25, 26), 128), ((25, 25), 96)):
                first = next(r for r in ramps if (r['tile_x'], r['tile_z']) == tile)
                self.assertEqual(first['subcell_delta_y'], [expected] * 4)
            preview = preview_field_map(disc, 'town01', collision['semantic_id'])
            self.assertEqual(len(preview['triggers']), 99)
            self.assertEqual(len(preview['regions']), 14)
            self.assertLessEqual(len(preview['rectangles']), 4228)
            self.assertGreater(len(preview['rectangles']), 4000)
            self.assertTrue(all(t['encoded']['gate'] == 1 for t in preview['triggers'] if t['table_source'] == 'fallback'))
            json.dumps(report)


if __name__ == '__main__':
    unittest.main()
