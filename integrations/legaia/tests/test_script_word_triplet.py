import unittest
from importer.core import ImportError
from importer.script_inspection import _instruction,inspect_record

class ScriptWordTriplet(unittest.TestCase):
    def test_selector_signed_words_context_and_source_only_offset(self):
        for prefix,context in [(b'\x4c',None),(b'\xcc\x07',7)]:
            encoded=prefix+b'\xd8\xff\x00\x80\xff\x7f\xff\xff';data=b'12345'+encoded+b'\x21';node=_instruction(data,5)
            self.assertEqual(node['mnemonic'],'FIELD_WORD_TRIPLET_REQUEST');self.assertEqual(node['length'],len(encoded));self.assertEqual(node['target_context'],context);self.assertEqual(node['raw_hex'],encoded.hex())
            self.assertEqual(node['operands']['selector'],255);self.assertEqual(node['operands']['signed_words'],[-32768,32767,-1]);self.assertEqual(node['operands']['runtime_offset'],'unknown');self.assertEqual(node['operands']['first_word_adjustment'],'runtime_offset_then_signed_16_wrap');self.assertEqual(node['operands']['runtime_effect'],'not_evaluated')
            self.assertEqual(node['successors'],[dict(pc=5+len(encoded),condition='encoded_continuation')])
    def test_every_truncated_prefix_refuses(self):
        for prefix in [b'\x4c',b'\xcc\x07']:
            encoded=prefix+b'\xd8\x01'+bytes(6)
            for end in range(1,len(encoded)):
                with self.assertRaises(ImportError):_instruction(encoded[:end],0)
    def test_unknown_neighbor_still_stops(self):
        data=b'\x4c\xd8\x00'+bytes(6)+b'\x4c\xd6\x04\x21';report=inspect_record(data,0)
        self.assertEqual(len(report['instructions']),1);self.assertEqual(report['stops'][0]['pc'],9);self.assertEqual(report['status'],'partial');self.assertIn('unsupported MENU_CTRL',report['stops'][0]['reason'])
