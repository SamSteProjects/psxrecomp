import unittest
from importer.core import ImportError
from importer.script_inspection import _instruction,inspect_record


class ScriptThreeWords(unittest.TestCase):
    def test_signed_extrema_context_and_literal_continuation(self):
        for prefix,context in [(b'\x4c',None),(b'\xcc\x07',7)]:
            for words in [[-32768,32767,-1],[0,0,0],[19788,-5300,9216]]:
                encoded=prefix+b'\xe6'+b''.join(w.to_bytes(2,'little',signed=True) for w in words)
                data=b'12345'+encoded+b'\x24';node=_instruction(data,5)
                self.assertEqual(node['mnemonic'],'FIELD_THREE_WORD_REQUEST');self.assertEqual(node['length'],len(encoded));self.assertEqual(node['target_context'],context);self.assertEqual(node['raw_hex'],encoded.hex())
                self.assertEqual(node['operands']['signed_words'],words)
                self.assertEqual(node['operands']['parameter_semantics'],'runtime_word_meanings_unresolved')
                self.assertEqual(node['operands']['runtime_binding'],'helper_owned_state_unresolved')
                self.assertEqual(node['operands']['runtime_effect'],'not_evaluated')
                self.assertEqual(node['successors'],[dict(pc=5+len(encoded),condition='encoded_continuation')])
                report=inspect_record(data,5);self.assertFalse(report['stops']);self.assertEqual(len(report['instructions']),2);self.assertFalse(report['dialogues'])
    def test_every_truncated_prefix_refuses(self):
        for prefix in [b'\x4c',b'\xcc\x07']:
            encoded=prefix+b'\xe6'+bytes(6)
            for end in range(1,len(encoded)):
                with self.assertRaises(ImportError):_instruction(encoded[:end],0)
    def test_unknown_neighbor_still_stops(self):
        data=b'\x4c\xe6'+bytes(6)+b'\x4c\xe7\x04\x21';report=inspect_record(data,0)
        self.assertEqual(len(report['instructions']),1);self.assertEqual(report['stops'][0]['pc'],8);self.assertEqual(report['status'],'partial');self.assertIn('unsupported MENU_CTRL',report['stops'][0]['reason'])
