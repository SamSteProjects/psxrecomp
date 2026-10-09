import struct
import unittest
from importer.script_inspection import inspect_record,MAX_MESSAGE_TOKENS
from importer.branch_authoring import _branch


class TextActorPayloadDecode(unittest.TestCase):
    def test_native_payload_token_widths_and_atomic_parent_continuation(self):
        for header in [b'\x4c',b'\xcc\x07']:
            for payload,nonzero in [(b'\x00',False),(b'\x1e',True),(b'\x1f\x5e\xc0\x00\xff\x00',True)]:
                record=header+b'\xe1'+payload+b'\x21\x26\xfe\xff';at=len(header)+1+len(payload)
                report=inspect_record(record,0);self.assertFalse(report['stops']);self.assertFalse(report['dialogues'])
                n=report['instructions'][0];self.assertEqual(n['mnemonic'],'TEXT_ACTOR_PAYLOAD_REQUEST')
                self.assertEqual(n['length'],at);self.assertEqual(n['raw_hex'],record[:at].hex())
                self.assertEqual(n['operands']['embedded_payload']['length'],len(payload))
                self.assertEqual(n['operands']['embedded_payload']['pc'],len(header)+1)
                self.assertEqual(n['operands']['embedded_payload']['terminator'],payload[-1])
                self.assertEqual(n['operands']['nonzero_first_byte'],nonzero)
                self.assertEqual(n['operands']['payload_ownership'],'runtime_text_actor_not_parent_dialogue')
                self.assertEqual(n['successors'],[dict(pc=at,condition='encoded_continuation')]);self.assertIsNone(_branch(record,n))
                self.assertEqual([n['pc'] for n in report['instructions']],[0,at,at+1])

    def test_truncation_and_bounded_token_count_refuse_without_text_recovery(self):
        for record in [b'\x4c\xe1',b'\x4c\xe1\xc0',b'\x4c\xe1\xc0\x00',b'\xcc\x07\xe1Hello',b'\x4c\xe1'+b'A'*MAX_MESSAGE_TOKENS+b'\x00']:
            report=inspect_record(record,0);self.assertTrue(report['stops']);self.assertFalse(report['instructions']);self.assertFalse(report['dialogues'])

    def test_branch_into_child_payload_refuses_ambiguous_parent_boundaries(self):
        record=b'\x4d\x00\x00\x00\x00'+struct.pack('<H',10-5)+b'\x4c\xe1\x1f\x21\x00\x21\x26\xfe\xff'
        report=inspect_record(record,0);self.assertTrue(report['stops']);self.assertFalse(report['instructions']);self.assertFalse(report['dialogues'])
        self.assertTrue(any('inside' in r['reason'] or 'overlap' in r['reason'] for r in report['stops']))
