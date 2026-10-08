"""System selector qualification against source syntax and Retail helpers."""
import hashlib
import os
import struct
import unittest
from importer.pipeline import _disc_context
from importer.script_inspection import inspect_record


class SystemFlagTests(unittest.TestCase):
    def test_normal_selector_space_and_encoded_edges(self):
        for index in range(4096):
            for route, name in ((5,'SET'),(6,'CLEAR'),(7,'TEST')):
                body=bytes(((route<<4)|(index>>8),index&255))+(b'\x02\0' if route==7 else b'')+b'\x21'
                row=inspect_record(body,0)['instructions'][0]
                self.assertEqual(row['operands']['index'],index)
                self.assertEqual(row['mnemonic'],'SYSFLAG_'+name)
                self.assertIsNone(row['target_context'])
                self.assertEqual(row['length'],4 if route==7 else 2)
                self.assertEqual(row['successors'],[dict(pc=4,condition='flag_set'),dict(pc=4,condition='flag_clear')] if route==7 else [dict(pc=2,condition='encoded_continuation')])

    @unittest.skipUnless(os.environ.get('LEGAIA_DISC_BIN'),'Private Retail disc required')
    def test_retail_msb_first_byte_helpers_and_dispatch_calls(self):
        with _disc_context(os.environ['LEGAIA_DISC_BIN']) as (image,_,_,a):
            overlay=a.read_entry(a.entry(897),extended=True)
            exe=image.read_file(image.find('SCUS_942.54'))
        self.assertEqual(hashlib.sha256(overlay).hexdigest(),'216f846db5ab085a295cef4064747380a06c995caa3e1b2773e78a1d349f126b')
        self.assertEqual(hashlib.sha256(exe).hexdigest(),'292256e2e66db42727f613406785e444254d3f699569e611f65fcf1c6d2f3482')
        load=struct.unpack_from('<I',exe,0x18)[0]
        def word(at): return struct.unpack_from('<I',exe,at-load+0x800)[0]
        # index>>3 byte address, low3 mask, 0x80>>shift, byte store.
        for start,expected in ((0x8003CE08,[0x3C028008,0x24424140,0x000428C3,0x00A22821,0x30840007,0x24020080,0x90A31618,0x00821007,0x00621825,0x03E00008,0xA0A31618]),
                               (0x8003CE34,[0x3C028008,0x24424140,0x000428C3,0x00A22821,0x30840007,0x24020080,0x00821007,0x90A31618,0x00021027,0x00621824,0x03E00008,0xA0A31618]),
                               (0x8003CE64,[0x3C038008,0x24634140,0x000410C3,0x00431021,0x90431618,0x30840007,0x24020080,0x00821007,0x00621824])):
            self.assertEqual([word(start+4*i) for i in range(len(expected))],expected)
        for at,expected in ((0x801E3590,0x0C00F382),(0x801E35B8,0x0C00F38D),(0x801E35E0,0x0C00F399),(0x801E359C,0x27DE0002),(0x801E35C4,0x27DE0002),(0x801E35EC,0x27C20002),(0x801E3620,0x27DE0004)):
            self.assertEqual(struct.unpack_from('<I',overlay,at-0x801CE818)[0],expected)


if __name__=='__main__':unittest.main()
