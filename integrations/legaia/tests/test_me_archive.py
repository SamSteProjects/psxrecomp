"""Literal selector/wrap oracle and private complete ME archive coverage."""
import os
import struct
import unittest
from importer.core import ImportError
from importer.me_archive import decode_channel_delta, entries
from importer.pipeline import _disc_context
from importer.player_battle import _sources, assemble
from importer.player_art_animation import discover, bank_records


def packed(rows):
    result = bytearray()
    for row in rows:
        for at in (0, 2, 4):
            a, b = row[at:at + 2]
            result.extend((a & 255, b & 255, ((a >> 8) & 15) | ((b >> 4) & 0xf0)))
    return bytes(result)


def literal_source():
    initial = [0x7ff, 0x800, 1, 0xfff, 0xabc, 0]
    selectors = '1' * 6 + '01' * 6 + '001' * 6 + '0000' + '0001' * 5
    bits = bytearray((len(selectors) + 7) // 8)
    for i, bit in enumerate(selectors):
        bits[i // 8] |= int(bit) << (7 - i % 8)
    operands = [v >> 8 for v in initial] + [1] * 6 + [15] * 6 + [15, 1, 2, 3, 4, 5]
    nibbles = bytes((operands[i] << 4) | operands[i + 1] for i in range(0, len(operands), 2))
    low = bytes([2, 2] + [v & 255 for v in initial])
    return b'\x40' + struct.pack('<2H', len(bits), len(bits) + len(nibbles)) + bits + nibbles + low


class MeArchiveTests(unittest.TestCase):
    def test_all_selectors_spatial_temporal_and_wrap(self):
        # Explicit arithmetic oracle, independent of the decoder accumulator.
        expected = bytes([2, 2]) + packed([
            [2047, 2048, 1, 4095, 2748, 0], [4095, 1, 3, 4095, 1401, 1],
            [4094, 0, 2, 4094, 1400, 0], [4094, 2, 5, 2, 1405, 6]])
        self.assertEqual(decode_channel_delta(literal_source()), expected)
        archive = b'ME\x02' + struct.pack('<2H', len(expected), 0x8000 | len(literal_source())) + expected + literal_source() + b'opaque tail'
        decoded = entries(archive)
        self.assertEqual([r['decoded'] for r in decoded], [expected, expected])
        self.assertEqual([r['compressed'] for r in decoded], [False, True])

    def test_malformed_streams_tables_and_bodies_refuse(self):
        source = literal_source()
        for bad in [b'', b'wrong', source[:-1], bytes([0x80]) + source[1:],
                    source[:1] + b'\xff\xff' + source[3:], source[:3] + b'\x00\x00' + source[5:]]:
            with self.assertRaises(ImportError):
                decode_channel_delta(bad)
        for bad in [b'', b'XX\x01', b'ME\x00', b'ME\x01\x00', b'ME\x01\x00\x00', b'ME\x01\xff\x7f']:
            with self.assertRaises(ImportError):
                entries(bad)


@unittest.skipUnless(os.getenv('LEGAIA_DISC_BIN'), 'Private retail source is required')
class MeArchiveRetailTests(unittest.TestCase):
    def test_art_records_preserve_distinct_reference_roles(self):
        disc = os.environ['LEGAIA_DISC_BIN']
        catalog = discover(disc)
        self.assertEqual((len(catalog['archives']), len(catalog['streams']), len(catalog['records'])), (8, 87, 109))
        streams = {r['semantic_id']: r for r in catalog['streams']}
        for player in range(4):
            records = [r for r in catalog['records'] if r['player_index'] == player]
            self.assertEqual(len(records), [33, 35, 32, 9][player])
            self.assertEqual(sum(r['rate_alt_byte'] == 255 for r in records), 8)
            for record in records:
                self.assertIn(record['reference_stream_id'], record['eligible_stream_ids'])
                self.assertEqual(streams[record['reference_stream_id']]['stream_index'], record['stream_source'])
                self.assertEqual(record['relationship'], 'static_bank_reference_runtime_resident_archive_not_observed')
                self.assertEqual(record['source_record']['byte_length'], 0xd0)
        digest, players = _sources(disc)
        altered = bytearray(players[0][3])
        # Corrupting record0's compressed source must never produce a new bank
        # from an unqualified source shape.
        altered[16:20] = b'\xff' * 4
        with self.assertRaises(ImportError):
            bank_records(bytes(altered), 0, digest)

    def test_all_eight_archives_and_assembly_part_ranges(self):
        disc = os.environ['LEGAIA_DISC_BIN']
        with _disc_context(disc) as (_, _, _, archive):
            raw = archive.read_entry(archive.entry(894))
        _, players = _sources(disc)
        count = 0
        for player in range(4):
            _, assembly = assemble(players[player][3], [0] * 5)
            for role, expected in [(1, [17, 18, 19, 1][player]), (2, 8)]:
                slot = player * 3 + role
                records = entries(raw[slot * 0x10800:(slot + 1) * 0x10800])
                self.assertEqual(len(records), expected)
                for record in records:
                    self.assertTrue(record['compressed'])
                    self.assertEqual(record['decoded'][0], [15, 16, 15, 17][player])
                    self.assertTrue(all(i < record['decoded'][0] for i in assembly['animation_part_indices']))
                count += len(records)
        self.assertEqual(count, 87)
