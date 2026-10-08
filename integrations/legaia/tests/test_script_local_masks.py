"""Literal retail handler evidence and normal/extended decoding ownership."""
import hashlib
import os
import struct
import unittest

from importer.pipeline import _disc_context
from importer.script_inspection import inspect_record


class LocalMaskTests(unittest.TestCase):
    def test_decoder_masks_and_context(self):
        for sub, and_mask, or_mask in ((0x35, 0xFF7F, 0x020A), (0x36, 0xFFFF, 0x028A)):
            for extended in (False, True):
                data = bytes((0xCC, 7, sub, 0x21)) if extended else bytes((0x4C, sub, 0x21))
                row = inspect_record(data, 0)['instructions'][0]
                self.assertEqual(row['length'], 3 if extended else 2)
                self.assertEqual(row['target_context'], 7 if extended else None)
                self.assertEqual(row['operands'], dict(sub_op=sub, can_yield=False,
                                 flag_word='actor_local_flags', and_mask=and_mask,
                                 or_mask=or_mask, runtime_effect='not_evaluated', encoded_hex=f'{sub:02x}'))
                self.assertEqual(row['successors'], [dict(pc=row['length'], condition='encoded_continuation')])
                self.assertEqual(row['raw_hex'], data[:row['length']].hex())
        for sub in (0x30, 0x31, 0x34, 0x37, 0x3B):
            row = inspect_record(bytes((0x4C, sub, 0x21)), 0)['instructions'][0]
            self.assertNotIn('and_mask', row['operands'])

    @unittest.skipUnless(os.environ.get('LEGAIA_DISC_BIN'), 'Private retail disc not supplied')
    def test_retail_handler_dispatch_and_delay_slot_store(self):
        with _disc_context(os.environ['LEGAIA_DISC_BIN']) as (_, _, _, archive):
            data = archive.read_entry(archive.entry(897), extended=True)
        self.assertEqual(hashlib.sha256(data).hexdigest(),
                         '216f846db5ab085a295cef4064747380a06c995caa3e1b2773e78a1d349f126b')
        def word(address):
            return struct.unpack_from('<I', data, address - 0x801CE818)[0]
        # Outer nibble 3 and inner low-nibble dispatch table ownership.
        self.assertEqual(word(0x801CEE6C), 0x801E0F00)
        self.assertEqual(word(0x801CEECC), 0x801E0F84)
        self.assertEqual(word(0x801CEED0), 0x801E0F9C)
        self.assertEqual(word(0x801E0F00), 0x3263000F)
        self.assertEqual(word(0x801E0F10), 0x2442EEB8)
        # LHU ctx+62, PC+2, masks, jump and its SH16 delay slot.
        self.assertEqual([word(0x801E0F84 + i * 4) for i in range(6)],
                         [0x96A20062, 0x27DE0002, 0x3042FF7F, 0x3442020A, 0x08078D89, 0xA6A20062])
        self.assertEqual([word(0x801E0F9C + i * 4) for i in range(5)],
                         [0x96A20062, 0x27DE0002, 0x3442028A, 0x08078D89, 0xA6A20062])


if __name__ == '__main__':
    unittest.main()
