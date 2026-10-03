"""Native MENUE2 request extent; inspection does not play or author FMVs."""
import hashlib
import os
import struct
import unittest
from importer.pipeline import _disc_context
from importer.script_inspection import inspect_record
from importer.branch_authoring import _branch

class FmvTriggerDecode(unittest.TestCase):
    def test_signed_ids_and_unread_trailing_bytes_both_headers(self):
        for extended in (False, True):
            for fmv_id in (-32768, -1, 0, 32767):
                header = bytes((0xcc, 9)) if extended else b'\x4c'
                data = header + b'\xe2' + struct.pack('<h', fmv_id) + b'\x1f\x26' + b'\x21\x26\xfe\xff'
                report = inspect_record(data, 0)
                self.assertFalse(report['stops'])
                row = report['instructions'][0]
                self.assertEqual(row['mnemonic'], 'FMV_TRIGGER_REQUEST')
                self.assertEqual(row['length'], len(header) + 5)
                self.assertEqual(row['target_context'], 9 if extended else None)
                self.assertEqual(row['operands']['fmv_id_signed'], fmv_id)
                self.assertEqual(row['operands']['trailing_bytes'], [31, 38])
                self.assertEqual(row['operands']['native_writes'], {'0x8007BA78': 'fmv_id_signed', '0x8007B83C': 26})
                self.assertEqual(row['operands']['runtime_effect'], 'not_evaluated')
                self.assertEqual(row['successors'], [{'pc': len(header)+5, 'condition': 'encoded_continuation'}])
                self.assertIsNone(_branch(data, row))
                self.assertEqual(report['dialogues'], [])

    def test_full_extent_required_and_unknown_tail_not_recovered(self):
        for extended in (False, True):
            header = bytes((0xcc, 9)) if extended else b'\x4c'
            full = header + b'\xe2\x01\x00\x1f\x26'
            for length in range(1, len(full)):
                report = inspect_record(full[:length], 0)
                self.assertEqual(report['instructions'], [])
                self.assertTrue(report['stops'])
            report = inspect_record(full+b'\x00\x1fHidden\0', 0)
            self.assertEqual(len(report['instructions']), 1)
            self.assertTrue(report['stops'])
            self.assertEqual(report['dialogues'], [])

@unittest.skipUnless(os.environ.get('LEGAIA_DISC_BIN'), 'requires private retail disc')
class RetailFmvTriggerProof(unittest.TestCase):
    def test_hash_bound_signed_loader_request_writes_and_advanced_return(self):
        with _disc_context(os.environ['LEGAIA_DISC_BIN']) as (image, _, _, archive):
            data = archive.read_entry(archive.entry(897), extended=True)
            exe = image.read_file(image.find('SCUS_942.54'))
        self.assertEqual(hashlib.sha256(data).hexdigest(), '216f846db5ab085a295cef4064747380a06c995caa3e1b2773e78a1d349f126b')
        self.assertEqual(hashlib.sha256(exe).hexdigest(), '292256e2e66db42727f613406785e444254d3f699569e611f65fcf1c6d2f3482')
        word = lambda a: struct.unpack_from('<I', data, a-0x801ce818)[0]
        for address, expected in ((0x801cf010, 0x801e30e4), (0x801e30e4, 0x0c00f3a7),
                (0x801e30e8, 0x26c40001), (0x801e30ec, 0x27de0006), (0x801e30f0, 0x3c038008),
                (0x801e30f4, 0xa462ba78), (0x801e30fc, 0x2402001a), (0x801e3100, 0x08078d89),
                (0x801e3104, 0xa462b83c), (0x801e3624, 0x03c01021)):
            self.assertEqual(word(address), expected, hex(address))
        base = struct.unpack_from('<I', exe, 0x18)[0]
        exe_word = lambda a: struct.unpack_from('<I', exe, 0x800+a-base)[0]
        self.assertEqual(exe_word(0x8003ceac), 0x00021400)
        self.assertEqual(exe_word(0x8003ceb0), 0x03e00008)
        self.assertEqual(exe_word(0x8003ceb4), 0x00021403)

if __name__ == '__main__':
    unittest.main()
