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

    def test_facing_spans_source_flags_dispatch_and_composed_parked_guards(self):
        from copy import deepcopy
        from test_npc_facing import NpcFacingTests,ACTOR
        from sdk.npc_facing import patch_allocated_facing
        from importer.man_layout import read_man_layout
        for instruction in (b'\x38\xa3\x80',b'\xb8\x07\xa3\x80',b'\x4c\x51\0\x80\xb3\x09',b'\xcc\x07\x51\0\x80\xb3\x09'):
            context,candidate,allocations,target=NpcFacingTests().fixture(instruction);values=dict(sector=7)
            result,audit=patch_allocated_facing(context,candidate,allocations,[dict(draft_id='npc-a',donor_entity_id=ACTOR,entries={target['semantic_id']:values})])
            offset,raw,entry=context._source.verified_record(ACTOR);index=allocations['drafts'][0]['record_index'];final=next(r for r in read_man_layout(result)['records'] if r['partition']==1 and r['record_index']==index);start,length=final['byte_offset'],final['byte_length']
            retail=dict(self.record(raw,entry),byte_offset=offset,record_index=1);generated=dict(self.record(result[start:start+length],entry),byte_offset=start,record_index=index);draft=dict(donor_entity_id=ACTOR,facing=dict(donor_entity_id=ACTOR,entries={target['semantic_id']:values}));metadata={'npc_facing_changes':audit}
            spans=authored_spans(metadata,'npc-a',retail,generated,draft);self.assertEqual(len(spans),1);self.assertEqual(spans[0]['category'],'own_facing');self.assertEqual(spans[0]['byte_length'],1)
            for change in (dict(pc=True),dict(record_index=1),dict(donor_entity_id='wrong'),dict(facing_id='wrong'),dict(source_record_sha256='0'*64),dict(mnemonic='UNKNOWN'),dict(target_context=255),dict(record_relative_byte_offset=0),dict(after_sector=0),dict(field='flags'),dict(before_byte=0)):
                forged=deepcopy(metadata);forged['npc_facing_changes']['changes'][0].update(change)
                with self.assertRaises(ProjectError):authored_spans(forged,'npc-a',retail,generated,draft)
            for changed in ({},dict(sector=3),dict(sector=True)):
                forged=deepcopy(draft);forged['facing']['entries'][target['semantic_id']]=changed
                with self.assertRaises(ProjectError):authored_spans(metadata,'npc-a',retail,generated,forged)
            forged=deepcopy(metadata);forged['npc_facing_changes']['changes']*=2
            with self.assertRaises(ProjectError):authored_spans(forged,'npc-a',retail,generated,draft)
            changed=bytearray(bytes.fromhex(generated['raw_hex']));pc=target['pc'];header=2 if target['target_context'] is not None else 1
            if target['mnemonic']=='NPC_RUN':changed[pc+header+1:pc+header+3]=b'\xff\xff'
            else:changed[pc+header+1]=0
            bad=dict(self.record(bytes(changed),entry),byte_offset=start,record_index=index)
            with self.assertRaises(ProjectError):authored_spans(metadata,'npc-a',retail,bad,draft)


    def test_flag_spans_source_width_upper_bits_dispatch_and_receipt_guards(self):
        from copy import deepcopy
        from test_npc_flags import NpcFlagsTests,ACTOR
        from sdk.npc_flags import patch_allocated_flags
        from importer.man_layout import read_man_layout
        for opcode in range(0x2b,0x34):
            for extended in (False,True):
                instruction=bytes([opcode|(128 if extended else 0)])+(b'\x07' if extended else b'')+b'\xe2'
                context,candidate,allocations=NpcFlagsTests().fixture(instruction);target=context.options(ACTOR)['targets'][0];values=dict(bit=3)
                result,audit=patch_allocated_flags(context,candidate,allocations,[dict(draft_id='npc-a',donor_entity_id=ACTOR,entries={target['semantic_id']:values})])
                offset,raw,entry=context._source.verified_record(ACTOR);index=allocations['drafts'][0]['record_index'];final=next(r for r in read_man_layout(result)['records'] if r['partition']==1 and r['record_index']==index);start,length=final['byte_offset'],final['byte_length']
                retail=dict(self.record(raw,entry),byte_offset=offset,record_index=1);generated=dict(self.record(result[start:start+length],entry),byte_offset=start,record_index=index);draft=dict(donor_entity_id=ACTOR,flags=dict(donor_entity_id=ACTOR,entries={target['semantic_id']:values}));metadata={'npc_flags_changes':audit}
                spans=authored_spans(metadata,'npc-a',retail,generated,draft);self.assertEqual(len(spans),1);self.assertEqual(spans[0]['category'],'own_flag');self.assertEqual(spans[0]['byte_length'],1);self.assertEqual(authored_spans({},'npc-a',retail,generated,draft),[])
                for change in (dict(pc=True),dict(record_index=1),dict(donor_entity_id='wrong'),dict(flag_id='wrong'),dict(source_record_sha256='0'*64),dict(mnemonic='UNKNOWN'),dict(target_context=255),dict(record_relative_byte_offset=0),dict(after_bit=0),dict(field='upper_flags'),dict(before_byte=0)):
                    forged=deepcopy(metadata);forged['npc_flags_changes']['changes'][0].update(change)
                    with self.assertRaises(ProjectError):authored_spans(forged,'npc-a',retail,generated,draft)
                for changed in ({},dict(bit=2),dict(bit=True),dict(bit=32),dict(bit=3,flags=0)):
                    forged=deepcopy(draft);forged['flags']['entries'][target['semantic_id']]=changed
                    with self.assertRaises(ProjectError):authored_spans(metadata,'npc-a',retail,generated,forged)
                forged=deepcopy(metadata);forged['npc_flags_changes']['changes']*=2
                with self.assertRaises(ProjectError):authored_spans(forged,'npc-a',retail,generated,draft)
                for relative in (target['pc'],target['decoded_byte_offset']-offset):
                    changed=bytearray(bytes.fromhex(generated['raw_hex']));changed[relative]^=128;bad=dict(self.record(bytes(changed),entry),byte_offset=start,record_index=index)
                    with self.assertRaises(ProjectError):authored_spans(metadata,'npc-a',retail,bad,draft)

    def test_branch_spans_native_words_receipts_and_retained_unreachable_operands(self):
        from copy import deepcopy
        from test_npc_branches import NpcBranchesTests,ACTOR
        from test_branch_authoring import family_script
        from sdk.npc_branches import patch_allocated_branches
        from importer.man_layout import read_man_layout
        for family in ('JMP_REL','COND_JMP','BBOX_TEST','FLAG_WORD_BRANCH','SYSFLAG_TEST'):
            for extended in (False,True):
                if family=='SYSFLAG_TEST' and extended:continue
                script,_,_,_=family_script(family,extended);context,candidate,allocations=NpcBranchesTests().fixture(script);target=context.options(ACTOR)['targets'][0];values=dict(target_pc=5)
                result,audit=patch_allocated_branches(context,candidate,allocations,[dict(draft_id='npc-a',donor_entity_id=ACTOR,entries={target['semantic_id']:values})]);offset,raw,entry=context._source.verified_record(ACTOR);index=allocations['drafts'][0]['record_index'];final=next(r for r in read_man_layout(result)['records'] if r['partition']==1 and r['record_index']==index);start,length=final['byte_offset'],final['byte_length']
                retail=dict(self.record(raw,entry),byte_offset=offset,record_index=1);generated=dict(self.record(result[start:start+length],entry),byte_offset=start,record_index=index);draft=dict(donor_entity_id=ACTOR,branches=dict(donor_entity_id=ACTOR,entries={target['semantic_id']:values}));metadata={'npc_branches_changes':audit}
                spans=authored_spans(metadata,'npc-a',retail,generated,draft);self.assertEqual(len(spans),1);self.assertEqual(spans[0]['category'],'own_branch');self.assertEqual(spans[0]['byte_length'],2)
                for change in (dict(pc=True),dict(record_index=1),dict(donor_entity_id='wrong'),dict(branch_id='wrong'),dict(source_record_sha256='0'*64),dict(effective_record_sha256='0'*64),dict(candidate_record_sha256='0'*64),dict(mnemonic='UNKNOWN'),dict(target_context=255),dict(condition='wrong'),dict(after_target_pc=6),dict(unreachable_source_pcs=[999]),dict(changed_bytes=[])):
                    forged=deepcopy(metadata);forged['npc_branches_changes']['changes'][0].update(change)
                    with self.assertRaises(ProjectError):authored_spans(forged,'npc-a',retail,generated,draft)
                forged=deepcopy(metadata);forged['npc_branches_changes']['changes']*=2
                with self.assertRaises(ProjectError):authored_spans(forged,'npc-a',retail,generated,draft)

    def test_branch_skipped_movement_facing_and_wait_still_have_exact_explanations(self):
        from test_npc_branches import NpcBranchesTests,ACTOR
        from importer.movement_authoring import MovementAuthoringContext
        from importer.facing_authoring import FacingAuthoringContext
        from importer.wait_authoring import WaitAuthoringContext
        from importer.man_layout import read_man_layout
        from sdk.npc_movement import patch_allocated_movement
        from sdk.npc_facing import patch_allocated_facing
        from sdk.npc_waits import patch_allocated_waits
        from sdk.npc_branches import patch_allocated_branches
        context,candidate,allocations=NpcBranchesTests().fixture(b'\x26\x02\0\x4c\x51\0\x80\xb3\x09\x4a\x0a\0\x26\xf3\xff')
        draft=dict(donor_entity_id=ACTOR);metadata={}
        for field,adapter,patcher,values in [('movement',MovementAuthoringContext,patch_allocated_movement,dict(x=128,z=192,move_id=10)),('facing',FacingAuthoringContext,patch_allocated_facing,dict(sector=7)),('waits',WaitAuthoringContext,patch_allocated_waits,dict(duration_ticks=11))]:
            native=adapter(context._source);target=native.options(ACTOR)['targets'][0];draft[field]=dict(donor_entity_id=ACTOR,entries={target['semantic_id']:values});candidate,audit=patcher(native,candidate,allocations,[dict(draft_id='npc-a',**draft[field])]);metadata['npc_'+('wait' if field=='waits' else field)+'_changes']=audit
        branch=context.options(ACTOR)['targets'][0];draft['branches']=dict(donor_entity_id=ACTOR,entries={branch['semantic_id']:dict(target_pc=17)});result,audit=patch_allocated_branches(context,candidate,allocations,[dict(draft_id='npc-a',**draft['branches'])]);metadata['npc_branches_changes']=audit
        offset,raw,entry=context._source.verified_record(ACTOR);index=allocations['drafts'][0]['record_index'];final=next(r for r in read_man_layout(result)['records'] if r['partition']==1 and r['record_index']==index);start,length=final['byte_offset'],final['byte_length'];retail=dict(self.record(raw,entry),byte_offset=offset,record_index=1);generated=dict(self.record(result[start:start+length],entry),byte_offset=start,record_index=index)
        self.assertIn(8,audit['changes'][0]['unreachable_source_pcs']);self.assertEqual({s['category'] for s in authored_spans(metadata,'npc-a',retail,generated,draft)},{'own_movement','own_facing','own_wait','own_branch'})

    def test_model_selector_explanations_signed_words_source_dispatch_and_forgery(self):
        from copy import deepcopy
        from test_npc_model_selectors import NpcModelSelectorTests,ACTOR
        from sdk.npc_model_selectors import patch_allocated_model_selectors
        from importer.man_layout import read_man_layout
        for extended in (False,True):
            for n in (-32768,-1,0,239,240,32767):
                context,candidate,allocations,target=NpcModelSelectorTests().fixture(extended);values=dict(model_selector_signed=n)
                result,audit=patch_allocated_model_selectors(context,candidate,allocations,[dict(draft_id='npc-a',donor_entity_id=ACTOR,entries={target['semantic_id']:values})])
                offset,raw,entry=context._source.verified_record(ACTOR);index=allocations['drafts'][0]['record_index'];final=next(r for r in read_man_layout(result)['records'] if r['partition']==1 and r['record_index']==index);start,length=final['byte_offset'],final['byte_length']
                retail=dict(self.record(raw,entry),byte_offset=offset,record_index=1);generated=dict(self.record(result[start:start+length],entry),byte_offset=start,record_index=index);draft=dict(donor_entity_id=ACTOR,model_selectors=dict(donor_entity_id=ACTOR,entries={target['semantic_id']:values}));metadata={'npc_model_selectors_changes':audit}
                spans=authored_spans(metadata,'npc-a',retail,generated,draft)
                if n==239:
                    self.assertEqual(spans,[]);continue
                self.assertEqual(len(spans),1);self.assertEqual(spans[0]['category'],'own_model_selector');self.assertEqual(spans[0]['byte_length'],2)
                for change in (dict(pc=True),dict(record_index=1),dict(donor_entity_id='wrong'),dict(model_selector_id='wrong'),dict(source_record_sha256='0'*64),dict(mnemonic='UNKNOWN'),dict(target_context=255),dict(record_relative_byte_offset=0),dict(after_selector=True),dict(field='asset_id'),dict(before_hex='0000')):
                    forged=deepcopy(metadata);forged['npc_model_selectors_changes']['changes'][0].update(change)
                    with self.assertRaises(ProjectError):authored_spans(forged,'npc-a',retail,generated,draft)
                for fields in ({},dict(model_selector_signed=True),dict(model_selector_signed=32768)):
                    forged=deepcopy(draft);forged['model_selectors']['entries'][target['semantic_id']]=fields
                    with self.assertRaises(ProjectError):authored_spans(metadata,'npc-a',retail,generated,forged)
                forged=deepcopy(metadata);forged['npc_model_selectors_changes']['changes']*=2
                with self.assertRaises(ProjectError):authored_spans(forged,'npc-a',retail,generated,draft)
                mutated=bytearray.fromhex(generated['raw_hex']);mutated[target['pc']+1]^=1;forged=dict(generated,raw_hex=mutated.hex())
                with self.assertRaises(ProjectError):authored_spans(metadata,'npc-a',retail,forged,draft)

    def test_skipped_model_selector_remains_explained_against_source_boundaries(self):
        from hashlib import sha256
        from test_importer_dialogue_authoring import fixture,ACTOR
        from importer.model_selector_authoring import ModelSelectorAuthoringContext
        from importer.branch_authoring import BranchAuthoringContext
        from importer.man_actor_structure import append_actor_donor
        from importer.man_layout import read_man_layout
        from sdk.npc_model_selectors import patch_allocated_model_selectors
        from sdk.npc_branches import patch_allocated_branches
        source,man=fixture(b'\x26\x02\0\x4c\x50\xef\0\x26\xf8\xff');selectors=ModelSelectorAuthoringContext(source);branches=BranchAuthoringContext(source);selector=selectors.options(ACTOR)['targets'][0]['semantic_id'];branch=branches.options(ACTOR)['targets'][0]['semantic_id'];candidate,row=append_actor_donor(man,sha256(man).hexdigest(),1);allocation={'drafts':[dict(row,draft_id='npc-a')]}
        selector_values={selector:dict(model_selector_signed=-1)};branch_values={branch:dict(target_pc=12)};candidate,selector_audit=patch_allocated_model_selectors(selectors,candidate,allocation,[dict(draft_id='npc-a',donor_entity_id=ACTOR,entries=selector_values)]);result,branch_audit=patch_allocated_branches(branches,candidate,allocation,[dict(draft_id='npc-a',donor_entity_id=ACTOR,entries=branch_values)])
        self.assertIn(8,branch_audit['changes'][0]['unreachable_source_pcs']);offset,raw,entry=source.verified_record(ACTOR);final=next(r for r in read_man_layout(result)['records'] if r['partition']==1 and r['record_index']==row['record_index']);start,length=final['byte_offset'],final['byte_length'];retail=dict(self.record(raw,entry),byte_offset=offset,record_index=1);generated=dict(self.record(result[start:start+length],entry),byte_offset=start,record_index=row['record_index']);draft=dict(donor_entity_id=ACTOR,model_selectors=dict(donor_entity_id=ACTOR,entries=selector_values),branches=dict(donor_entity_id=ACTOR,entries=branch_values))
        spans=authored_spans(dict(npc_model_selectors_changes=selector_audit,npc_branches_changes=branch_audit),'npc-a',retail,generated,draft);self.assertEqual({r['category'] for r in spans},{'own_model_selector','own_branch'})

if __name__=='__main__':unittest.main()
