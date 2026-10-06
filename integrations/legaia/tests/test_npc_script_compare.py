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
if __name__=='__main__':unittest.main()
