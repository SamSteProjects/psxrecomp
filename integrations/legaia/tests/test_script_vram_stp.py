import unittest
from importer.core import ImportError
from importer.script_inspection import _instruction,inspect_record

class ScriptVramStp(unittest.TestCase):
    def test_unsigned_words_context_and_literal_continuation(self):
        for sub,mnemonic,rule in [(0xd4,'VRAM_STP_SET_REQUEST','set_bit_15_for_nonzero_pixels'),(0xd5,'VRAM_STP_CLEAR_REQUEST','clear_bit_15_except_0x8000')]:
            for prefix,context in [(b'\x4c',None),(b'\xcc\x07',7)]:
                encoded=prefix+bytes([sub])+b'\xff\xff\x00\x80';data=b'12345'+encoded+b'\x21';before=bytes(data)
                node=_instruction(data,5);self.assertEqual(node['mnemonic'],mnemonic);self.assertEqual(node['length'],len(encoded));self.assertEqual(node['target_context'],context)
                self.assertEqual(node['operands'],dict(sub_op=sub,vram_x=65535,vram_y=32768,width=16,height=1,pixel_rule=rule,asset_binding='runtime_vram_source_asset_unresolved',runtime_effect='not_evaluated',encoded_hex=(bytes([sub])+b'\xff\xff\x00\x80').hex()))
                self.assertEqual(node['successors'],[dict(pc=5+len(encoded),condition='encoded_continuation')]);self.assertEqual(node['raw_hex'],encoded.hex());self.assertEqual(data,before)
    def test_every_truncated_prefix_refuses(self):
        for sub in [0xd4,0xd5]:
            for prefix in [b'\x4c',b'\xcc\x07']:
                encoded=prefix+bytes([sub])+b'\x01\x00\x02\x00'
                for end in range(1,len(encoded)):
                    with self.assertRaises(ImportError):_instruction(encoded[:end],0)
    def test_unknown_neighbor_still_stops_and_following_instruction_is_not_invented(self):
        data=b'\x4c\xd4\x00\x00\xf9\x01\x4c\xd6\x04\x21';report=inspect_record(data,0)
        self.assertEqual(len(report['instructions']),1);self.assertEqual(report['instructions'][0]['successors'],[dict(pc=6,condition='encoded_continuation')]);self.assertEqual(report['stops'][0]['pc'],6)
        self.assertEqual(report['status'],'partial');self.assertIn('unsupported MENU_CTRL',report['stops'][0]['reason'])
