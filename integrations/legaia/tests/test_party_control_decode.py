import unittest
from importer.script_inspection import inspect_record


class PartyControlDecode(unittest.TestCase):
    def test_both_headers_all_selectors_preserve_literal_continuation(self):
        for header in [b'\x4c',b'\xcc\x07']:
            for nibble,name in [(0,'PARTY_LEADER_REQUEST'),(0x20,'PARTY_VIEW_SWAP_REQUEST')]:
                for low in range(16):
                    record=header+bytes([nibble+low])+b'\x26\xff\xff'
                    original=bytes(record);report=inspect_record(record,0)
                    self.assertFalse(report['stops']);node=report['instructions'][0]
                    self.assertEqual(node['length'],len(header)+1)
                    self.assertEqual(node['raw_hex'],record[:len(header)+1].hex())
                    self.assertEqual(node['target_context'],7 if len(header)==2 else None)
                    self.assertEqual(node['mnemonic'],name)
                    self.assertEqual(node['operands']['party_selector'],low&7)
                    self.assertEqual(node['successors'],[{'pc':len(header)+1,'condition':'encoded_continuation'}])
                    self.assertEqual(node['operands']['party_binding'],'runtime_party_identity_unresolved')
                    self.assertEqual(node['operands']['runtime_effect'],'not_evaluated')
                    self.assertEqual(record,original)

    def test_truncation_unknown_neighbors_and_record_offsets(self):
        for record in [b'\x4c',b'\xcc',b'\xcc\x07',b'\x4c\x00\xff',b'\x4c\x20\xff']:
            self.assertTrue(inspect_record(record,0)['stops'])
        report=inspect_record(bytes(5)+b'\x4c\x2f\x26\xff\xff',5)
        self.assertEqual([n['pc'] for n in report['instructions']],[5,7]);self.assertFalse(report['stops'])
        for sub in [0x93,0xe1,0xb0]:
            report=inspect_record(b'\x4c'+bytes([sub])+b'\x21',0)
            self.assertFalse(report['instructions']);self.assertTrue(report['stops'])
