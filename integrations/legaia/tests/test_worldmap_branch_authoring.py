"""World P0 branch changes retain authored operands and dormant source anchors."""
import unittest
from importer.core import ImportError
from importer.worldmap_branch_authoring import branch_record_options, patch_branch_record
from importer.script_operand_composition import compose_script_operands
from importer.system_flag_authoring import patch_system_flag_selector
from sdk.worldmap_script_operands import patch_world_movement

END=b'\x3f\0\0\x06town01\1\2\3opaque'
# Entry2: jump2 -> NOP5; system-test6 -> MOVE_TO10; scene-change13.
RECORD=b'\0\0\x26\x02\0\x21\x71\x02\x02\0\x23\x60\x19'+END

class WorldBranchRecordTests(unittest.TestCase):
    def test_retains_unreachable_authored_operands_and_selector_header(self):
        candidate,_=compose_script_operands(RECORD,2,[(patch_system_flag_selector,6,{'index':4095}),(patch_world_movement,10,{'x':64,'z':16384})])
        result,audit,graph=patch_branch_record(RECORD,2,{2:{'target_pc':2}},operand_record=candidate,base_offset=64)
        self.assertEqual(result,candidate[:3]+b'\xff\xff'+candidate[5:])
        self.assertEqual(audit[0]['decoded_byte_offset'],67)
        self.assertIn(10,graph['unreachable_source_pcs'])
        dormant=next(n for n in graph['unvisited_instructions'] if n['pc']==10)
        self.assertEqual(dormant['operands']['target_position'],{'x':64,'y':None,'z':16384})
        self.assertEqual(next(n for n in graph['unvisited_instructions'] if n['pc']==6)['operands']['index'],4095)
        self.assertEqual(graph['stops'],[])

    def test_two_branch_words_preserve_sysflag_and_noop(self):
        result,audit,graph=patch_branch_record(RECORD,2,{2:{'target_pc':6},6:{'target_pc':13}})
        self.assertEqual(result[:3],RECORD[:3]);self.assertEqual(result[3:5],b'\x03\0');self.assertEqual(result[6:8],b'\x71\x02');self.assertEqual(result[8:10],b'\x05\0')
        self.assertEqual(len(audit),2);self.assertEqual(graph['stops'],[])
        self.assertEqual(patch_branch_record(RECORD,2,{2:{'target_pc':5}})[:2],(RECORD,[]))
        self.assertEqual(patch_branch_record(RECORD,2,{6:{'target_pc':13},2:{'target_pc':6}})[0],result)

    def test_header_opaque_preimage_and_unsupported_boundaries_refuse(self):
        for pc,values in [(True,{'target_pc':2}),(5,{'target_pc':2}),(2,{'target_pc':3}),(2,{'target_pc':0}),(2,{'target_pc':len(RECORD)}),(2,{'target_pc':True}),(2,{'target_pc':32768}),(2,{'target_pc':2,'extra':1})]:
            with self.subTest(pc=pc,values=values),self.assertRaises(ImportError):patch_branch_record(RECORD,2,{pc:values})
        for at in [0,3,len(RECORD)-1,6]:
            candidate=bytearray(RECORD);candidate[at]^=0x10
            with self.subTest(at=at),self.assertRaises(ImportError):patch_branch_record(RECORD,2,{2:{'target_pc':2}},operand_record=bytes(candidate))
        with self.assertRaises(ImportError):patch_branch_record(RECORD,2,{},base_offset=True)
        # A caller cannot smuggle an unrequested branch change into its operand
        # baseline, even if that edge still lands at an original boundary.
        candidate=RECORD[:8]+b'\x05\0'+RECORD[10:]
        with self.assertRaisesRegex(ImportError,'unaudited branch'):
            patch_branch_record(RECORD,2,{},operand_record=candidate)

    def test_noop_composition_retains_all_source_bytes_and_source_is_immutable(self):
        result,audit,graph=patch_branch_record(RECORD,2,{})
        self.assertEqual(result,RECORD);self.assertEqual(audit,[]);self.assertEqual(graph['unreachable_source_pcs'],[])
        with self.assertRaises(ImportError):branch_record_options(bytearray(RECORD),2)
        with self.assertRaises(ImportError):branch_record_options(RECORD,True)
        with self.assertRaises(ImportError):patch_branch_record(RECORD,2,[],operand_record=RECORD)

    def test_unknown_source_stops_are_not_bypassed(self):
        record=b'\0\0\x26\x02\0\x7f'
        self.assertIsNotNone(branch_record_options(record,2)['reason'])
        with self.assertRaises(ImportError):patch_branch_record(record,2,{2:{'target_pc':2}})

if __name__=='__main__':unittest.main()
