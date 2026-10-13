import os
import random
import struct
import unittest
from importer.core import ImportError
from importer.me_archive import encode_channel_delta, decode_channel_delta, entries, replace_entry
from importer.pipeline import _disc_context
from test_me_archive import packed


class MeEncodingTests(unittest.TestCase):
    def test_literal_oracle_and_random_wrapping_channels(self):
        rng = random.Random(94254)
        for parts, frames in [(1, 1), (1, 255), (2, 2), (17, 20), (64, 2)]:
            rows = [[rng.randrange(4096) for _ in range(6)] for _ in range(parts * frames)]
            rows[0] = [0, 15, 16, 2047, 2048, 4095]
            decoded = bytes([parts, frames]) + packed(rows)
            encoded = encode_channel_delta(decoded, 0x4f)
            self.assertEqual(encoded[0], 0x4f)
            self.assertEqual(decode_channel_delta(encoded), decoded)
            self.assertEqual(encode_channel_delta(decoded, 0x4f), encoded)
        for bad in [b'', b'\x00\x01', b'\x01\x00', b'\x01\x01' + bytes(8), b'\x41\x01' + bytes(65*9)]:
            with self.assertRaises(ImportError): encode_channel_delta(bad)
        for flag in [True, False, 0x3f, 0x80, 1.0]:
            with self.assertRaises(ImportError): encode_channel_delta(bytes([1, 1]) + bytes(9), flag)
        with self.assertRaises(ImportError): encode_channel_delta(bytes([64, 255]) + bytes(64*255*9))

    def test_fixed_span_neighbors_noop_shape_and_capacity_refusal(self):
        original = bytes([1, 1]) + bytes(9)
        encoded = encode_channel_delta(original)
        archive = b'ME\x02' + struct.pack('<2H', 0x8000 | (len(encoded)+30), len(original)) + encoded + b'Q'*30 + original + b'opaque'
        changed = bytes([1, 1]) + packed([[100, 200, 300, 400, 500, 600]])
        candidate = replace_entry(archive, 0, changed)
        record = entries(archive)[0];start, size = record['byte_offset'], record['byte_length']
        self.assertEqual(candidate[:start], archive[:start]);self.assertEqual(candidate[start+size:], archive[start+size:])
        self.assertEqual(entries(candidate)[0]['decoded'], changed)
        self.assertEqual(replace_entry(archive, 0, original), archive)
        self.assertEqual(replace_entry(archive, 1, changed)[-6:], b'opaque')
        tight = b'ME\x01' + struct.pack('<H', 0x8000 | len(encoded)) + encoded
        for index, decoded in [(0, changed), (True, original), (2, original), (0, b'\x01\x02'+bytes(18))]:
            with self.assertRaises(ImportError): replace_entry(tight, index, decoded)


@unittest.skipUnless(os.getenv('LEGAIA_DISC_BIN'), 'Private retail disc required')
class MeEncodingRetailTests(unittest.TestCase):
    def test_every_original_fits_and_changed_candidates_preserve_neighbors(self):
        with _disc_context(os.environ['LEGAIA_DISC_BIN']) as (_, _, _, archive):
            raw = archive.read_entry(archive.entry(894))
        count = accepted = refused = 0
        for player in range(4):
            for role in (1, 2):
                slot = raw[(player*3+role)*0x10800:(player*3+role+1)*0x10800]
                for record in entries(slot):
                    decoded = record['decoded'];encoded = encode_channel_delta(decoded, slot[record['byte_offset']])
                    self.assertLessEqual(len(encoded), record['byte_length']);self.assertEqual(decode_channel_delta(encoded), decoded);count += 1
                    changed = bytearray(decoded);changed[2] ^= 1
                    try: candidate = replace_entry(slot, record['entry_index'], bytes(changed))
                    except ImportError as error:
                        self.assertIn('original declared entry body', str(error));refused += 1;continue
                    start, size = record['byte_offset'], record['byte_length']
                    self.assertEqual(candidate[:start], slot[:start]);self.assertEqual(candidate[start+size:], slot[start+size:]);self.assertEqual(entries(candidate)[record['entry_index']]['decoded'], bytes(changed));accepted += 1
        self.assertEqual(count, 87);self.assertEqual(accepted+refused, 87);self.assertGreater(accepted, 0)
        print(f'{count} original ME streams fit; {accepted} one-channel candidates fit and {refused} refuse capacity', flush=True)


if __name__ == '__main__': unittest.main()
