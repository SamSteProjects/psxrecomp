from hashlib import sha256
import unittest
from sdk.npc_script_compare import compare_records,authored_spans
from sdk.project import ProjectError
class ScriptComparisonTests(unittest.TestCase):
    def record(self,data,entry=2):return dict(raw_hex=data.hex(),byte_length=len(data),sha256=sha256(data).hexdigest(),script_offset=entry)
    def test_exact_relative_bytes_headers_opaque_tail_and_lengths(self):
        a=self.record(b'abcdef');b=self.record(b'aXcYef!');r=compare_records(a,b)
        self.assertEqual(r['changed_byte_count'],3);self.assertEqual(r['unchanged_common_byte_count'],4);self.assertFalse(r['script_tail_bytes_equal']);self.assertEqual(r['changes'],[dict(relative_offset=1,retail_byte=98,generated_byte=88,scope='record_header'),dict(relative_offset=3,retail_byte=100,generated_byte=89,scope='script_or_remaining_record_bytes'),dict(relative_offset=6,retail_byte=None,generated_byte=33,scope='script_or_remaining_record_bytes')])
        self.assertEqual(compare_records(a,a)['changes'],[]);self.assertTrue(compare_records(a,a)['record_bytes_equal'])
        self.assertTrue(compare_records(a,self.record(b'aXcdef'))['script_tail_bytes_equal'])
        for change in [dict(sha256='0'*64),dict(raw_hex='bad'),dict(byte_length=5),dict(script_offset=True),dict(script_offset=8)]:
            with self.assertRaises(ProjectError):compare_records(a,{**b,**change})
    def test_source_bound_authored_spans_and_no_unexplained_relabeling(self):
        from copy import deepcopy
        owner='scene://town01/actors/man-p1/0040';wait='script://town01/actors/man-p1/0040/wait/0004';run='script://town01/actors/man-p1/0040/dialogue/0007/run/0008';identifier='npc'
        a=bytes([0,8,9,0,0,10,0,0])+b'Hi?';b=bytes([0,12,9,0,0,11,0,0])+b'Yo!'
        retail=dict(self.record(a,5),byte_offset=100,record_index=40);generated=dict(self.record(b,5),byte_offset=1000,record_index=53)
        draft=dict(donor_entity_id=owner,appearance={},waits={'entries':{wait:{'duration_ticks':11}}},dialogue={'runs':{run:'Yo'}})
        base=dict(draft_id=identifier,record_index=53)
        metadata={'npc_appearance_changes':{'changes':[dict(base,field='model_index',before_byte=8,after_byte=12,source_decoded_byte_offset=101,decoded_byte_offset=1001)]},'npc_wait_changes':{'changes':[dict(base,wait_id=wait,mnemonic='WAIT_FRAMES',before_hex='0a00',after_hex='0b00',byte_length=2,source_decoded_byte_offset=105,decoded_byte_offset=1005)]},'npc_dialogue_changes':{'changes':[dict(base,run_id=run,before_hex='4869',after_hex='596f',byte_length=2,source_decoded_byte_offset=108,decoded_byte_offset=1008)]}}
        spans=authored_spans(metadata,identifier,retail,generated,draft);self.assertEqual([r['category'] for r in spans],['initial_appearance','own_wait','own_dialogue']);self.assertFalse(any(r['relative_offset']<=10<r['relative_offset']+r['byte_length'] for r in spans))
        self.assertEqual(authored_spans({},identifier,retail,generated,draft),[])
        for change in [dict(record_index=1),dict(decoded_byte_offset=1006),dict(before_hex='ffff'),dict(after_hex='0c00'),dict(wait_id=wait.replace('0040','0044'))]:
            bad=deepcopy(metadata);bad['npc_wait_changes']['changes'][0].update(change)
            with self.assertRaises(ProjectError):authored_spans(bad,identifier,retail,generated,draft)
        bad=deepcopy(metadata);bad['npc_wait_changes']['changes']*=2
        with self.assertRaises(ProjectError):authored_spans(bad,identifier,retail,generated,draft)
    def test_movement_spans_decode_source_and_preserve_unexplained_bytes(self):
        from copy import deepcopy
        from test_npc_movement import NpcMovementTests,ACTOR
        from sdk.npc_movement import patch_allocated_movement
        cases=[(b'\x23\0\x80',dict(x=128,z=192)),(b'\xa3\x07\0\x80',dict(x=128)),(b'\x4c\x51\0\x80\xab\x09',dict(x=128,z=192,move_id=10)),(b'\xcc\x07\x51\0\x80\xab\x09',dict(move_id=10)),(b'\x22\x09',dict(move_id=10)),(b'\xa2\x07\x09',dict(move_id=10))]
        for instruction,values in cases:
            context,source,candidate,allocations,target=NpcMovementTests().candidate(instruction)
            result,audit=patch_allocated_movement(context,candidate,allocations,[dict(draft_id='npc-a',donor_entity_id=ACTOR,entries={target['semantic_id']:values})])
            offset,raw,entry=source.verified_record(ACTOR);allocation=allocations['drafts'][0]
            # Allocation row spans remain final after the second clone append.
            from importer.man_layout import read_man_layout
            final=next(r for r in read_man_layout(result)['records'] if r['partition']==1 and r['record_index']==allocation['record_index'])
            start,length=final['byte_offset'],final['byte_length'];retail=dict(self.record(raw,entry),byte_offset=offset,record_index=1);generated=dict(self.record(result[start:start+length],entry),byte_offset=start,record_index=allocation['record_index']);draft=dict(donor_entity_id=ACTOR,movement=dict(donor_entity_id=ACTOR,entries={target['semantic_id']:values}));metadata={'npc_movement_changes':audit}
            spans=authored_spans(metadata,'npc-a',retail,generated,draft);self.assertEqual({r['movement_field'] for r in spans},set(values));self.assertTrue(all(r['category']=='own_movement' and r['byte_length']==1 for r in spans));self.assertEqual(authored_spans({},'npc-a',retail,generated,draft),[])
            for change in [dict(pc=True),dict(record_index=1),dict(donor_entity_id='wrong'),dict(movement_id='wrong'),dict(source_record_sha256='0'*64),dict(mnemonic='MOVE_UNKNOWN'),dict(target_context=255),dict(record_relative_byte_offset=0),dict(after_coordinate=0),dict(field='y')]:
                forged=deepcopy(metadata);forged['npc_movement_changes']['changes'][0].update(change)
                with self.assertRaises(ProjectError):authored_spans(forged,'npc-a',retail,generated,draft)
            missing=deepcopy(draft);missing['movement']['entries']={}
            with self.assertRaises(ProjectError):authored_spans(metadata,'npc-a',retail,generated,missing)
            oversized=deepcopy(metadata);oversized['npc_movement_changes']['changes']=[audit['changes'][0]]*8193
            with self.assertRaises(ProjectError):authored_spans(oversized,'npc-a',retail,generated,draft)
            forged=deepcopy(metadata);forged['npc_movement_changes']['changes']*=2
            with self.assertRaises(ProjectError):authored_spans(forged,'npc-a',retail,generated,draft)

if __name__=='__main__':unittest.main()
