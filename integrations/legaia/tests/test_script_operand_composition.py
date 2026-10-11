import unittest
from copy import deepcopy
from importer.core import ImportError
from importer.animation_operand_authoring import patch_animation_operands_target
from importer.effect_color_authoring import patch_effect_color_target
from importer.script_operand_composition import compose_script_operands
from test_effect_color_authoring import END


class ScriptOperandCompositionTests(unittest.TestCase):
    def setUp(self):
        # P0 header, extended actor animation dispatch, ordinary color dispatch.
        self.record=b'\0\0\xcc\x07\x81\x01\x02\x03\x04\x05\x06\x07\x34\x0f\x01\x02\x03\x04\0'+END
        self.animation=(patch_animation_operands_target,2,dict(model_id=0x030201,animation_frame=0x0504,tween_frames=1))
        self.color=(patch_effect_color_target,12,dict(red=255,green=0,blue=1,intensity=-32768))

    def test_mixed_writers_literal_bytes_and_order_independence(self):
        expected=self.record[:10]+b'\1\0'+self.record[12:14]+b'\xff\0\1\0\x80'+END
        for requests in ([self.animation,self.color],[self.color,self.animation]):
            candidate,audit=compose_script_operands(self.record,2,requests,base_offset=100)
            self.assertEqual(candidate,expected)
            self.assertEqual([c['decoded_byte_offset'] for c in audit],[110,114])
            self.assertEqual(audit[0]['target_context'],7)
            self.assertEqual(audit[1]['after_values'],self.color[2])
        self.assertEqual(self.record[10:12],b'\x06\x07')

    def test_duplicate_ownership_refused_even_for_identical_values(self):
        with self.assertRaises(ImportError):compose_script_operands(self.record,2,[self.color,self.color])

    def test_exact_retail_requests_and_empty_requests_are_noop(self):
        animation=(patch_animation_operands_target,2,dict(model_id=0x030201,animation_frame=0x0504,tween_frames=0x0706))
        color=(patch_effect_color_target,12,dict(red=1,green=2,blue=3,intensity=4))
        self.assertEqual(compose_script_operands(self.record,2,[animation,color]),(self.record,[]))
        self.assertEqual(compose_script_operands(self.record,2,[]),(self.record,[]))

    def test_forged_writer_audits_and_unreported_changes_refused(self):
        candidate,audit=patch_effect_color_target(self.record,2,12,self.color[2],base_offset=100)
        mutations=[dict(byte_length=4),dict(record_relative_byte_offset=True),dict(decoded_byte_offset=115),
                   dict(source_record_sha256='0'*64),dict(pc=2),dict(before_hex='00'*5),dict(after_hex='00'*5)]
        outcomes=[(candidate,[]),(candidate+b'\0',audit)]
        for mutation in mutations:
            changed=deepcopy(audit);changed[0].update(mutation);outcomes.append((candidate,changed))
        unrelated=bytearray(candidate);unrelated[-1]^=1;outcomes.append((bytes(unrelated),audit))
        for outcome in outcomes:
            with self.subTest(outcome=outcome):
                writer=lambda *args,**kwargs:outcome
                with self.assertRaises(ImportError):compose_script_operands(self.record,2,[(writer,12,{})],base_offset=100)

    def test_combined_graph_rejects_audited_opcode_change(self):
        # A forged writer can make a self-consistent byte audit; graph proof must
        # still reject turning the color dispatch into another instruction.
        from hashlib import sha256
        candidate=self.record[:12]+b'\0'+self.record[13:]
        audit=[dict(record_relative_byte_offset=12,decoded_byte_offset=12,byte_length=1,
                    source_record_sha256=sha256(self.record).hexdigest(),pc=12,
                    before_hex='34',after_hex='00')]
        with self.assertRaises(ImportError):
            compose_script_operands(self.record,2,[(lambda *a,**k:(candidate,audit),12,{})])


if __name__=='__main__':unittest.main()
