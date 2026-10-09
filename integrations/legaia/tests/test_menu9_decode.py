import struct
import unittest
from importer.script_inspection import inspect_record


class Menu9Decode(unittest.TestCase):
    def test_fixed_forms_and_literal_continuations_both_headers(self):
        for header in [b'\x4c',b'\xcc\x07']:
            forms=[(bytes([sub,5])+struct.pack('<hhh',-32768,0,32767),'FIELD_FADE_REQUEST') for sub in [0x90,0x91,0x92]]
            forms += [(b'\x9e'+struct.pack('<16h',*range(-8,8)),'FIELD_TABLE_COPY'),(b'\x9f','FIELD_CALLBACK_REGISTER')]
            for payload,name in forms:
                at=len(header)+len(payload);record=header+payload+b'\x26\xff\xff'
                report=inspect_record(record,0);self.assertFalse(report['stops'])
                node=report['instructions'][0];self.assertEqual(node['mnemonic'],name)
                self.assertEqual(node['length'],at);self.assertEqual(node['raw_hex'],record[:at].hex())
                self.assertEqual(node['successors'],[dict(pc=at,condition='encoded_continuation')])
                self.assertEqual(node['target_context'],7 if len(header)==2 else None)
                self.assertEqual(node['operands']['runtime_effect'],'not_evaluated')
                if name=='FIELD_FADE_REQUEST':self.assertEqual(node['operands']['signed_words'],[-32768,0,32767])
                if name=='FIELD_TABLE_COPY':self.assertEqual(node['operands']['signed_words'],list(range(-8,8)))
                if name=='FIELD_CALLBACK_REGISTER':self.assertEqual(node['operands']['callback_activation'],'not_observed')

    def test_truncated_words_and_unknown_subops_do_not_recover(self):
        for header in [b'\x4c',b'\xcc\x07']:
            for payload in [b'\x90'+bytes(7),b'\x9e'+bytes(32)]:
                for cut in range(1,len(payload)):
                    report=inspect_record(header+payload[:cut],0)
                    self.assertFalse(report['instructions']);self.assertTrue(report['stops'])
            for sub in range(0x93,0x9e):
                report=inspect_record(header+bytes([sub])+b'\x21',0)
                self.assertFalse(report['instructions']);self.assertTrue(report['stops'])

    def test_callback_parent_continues_even_when_target_bytes_unknown(self):
        report=inspect_record(b'\x4c\x9f\xff',0)
        self.assertEqual(len(report['instructions']),1)
        self.assertEqual(report['instructions'][0]['successors'],[dict(pc=2,condition='encoded_continuation')])
        self.assertEqual(report['stops'][0]['pc'],2)
        self.assertFalse(any(n['pc']==0 for n in report['instructions'][0]['successors']))
