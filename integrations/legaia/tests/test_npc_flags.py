"""Final-clone flag ownership, preserved upper bits and unsupported side effects."""
from copy import deepcopy
from hashlib import sha256
from unittest import TestCase
from importer.core import ImportError as NativeError
from importer.flag_authoring import FlagAuthoringContext
from importer.man_actor_structure import append_actor_donor
from importer.man_layout import read_man_layout
from sdk.npc_flags import patch_allocated_flags
from sdk.project import ProjectError
from test_importer_dialogue_authoring import fixture,ACTOR
from test_wait_authoring import END

class NpcFlagsTests(TestCase):
    def fixture(self,instruction):
        source,candidate=fixture(instruction+END);context=FlagAuthoringContext(source);allocations={'drafts':[]}
        for id in ('npc-a','npc-b'):
            candidate,row=append_actor_donor(candidate,sha256(candidate).hexdigest(),1);allocations['drafts'].append(dict(row,draft_id=id))
        return context,candidate,allocations

    def test_all_supported_banks_ops_and_extended_targets_change_only_owned_bits(self):
        for opcode in range(0x2b,0x34):
            for extended in (False,True):
                instruction=bytes([opcode|(0x80 if extended else 0)])+(b'\x07' if extended else b'')+b'\xe2'
                context,candidate,allocations=self.fixture(instruction);target=context.options(ACTOR)['targets'][0];request=lambda id,bit:dict(draft_id=id,donor_entity_id=ACTOR,entries={target['semantic_id']:dict(bit=bit)})
                result,audit=patch_allocated_flags(context,candidate,allocations,[request('npc-a',3),request('npc-b',4)])
                changed=[i for i,(a,b) in enumerate(zip(candidate,result)) if a!=b];self.assertEqual(changed,sorted(r['decoded_byte_offset'] for r in audit['changes']));self.assertEqual(len(changed),2);self.assertEqual(read_man_layout(result),read_man_layout(candidate))
                for row in audit['changes']:self.assertEqual(row['before_byte']&0xe0,row['after_byte']&0xe0)
                for bit in (2,3,4):
                    result,_=patch_allocated_flags(context,candidate,allocations,[request('npc-a',bit)]);self.assertEqual(len(result),len(candidate))

    def test_noop_preimages_unknown_owners_and_duplicate_allocations_reject(self):
        context,candidate,allocations=self.fixture(b'\xae\x07\xe2');target=context.options(ACTOR)['targets'][0];request=dict(draft_id='npc-a',donor_entity_id=ACTOR,entries={target['semantic_id']:dict(bit=2)})
        final=next(r for r in read_man_layout(candidate)['records'] if r['partition']==1 and r['record_index']==allocations['drafts'][0]['record_index']);source_at=context._source.verified_record(ACTOR)[0];at=final['byte_offset']+target['decoded_byte_offset']-source_at
        for offset in (at,at-1,at-2):
            forged=bytearray(candidate);forged[offset]^=0x20
            with self.assertRaises((ProjectError,NativeError)):patch_allocated_flags(context,bytes(forged),allocations,[request])
        for fields in (dict(bit=True),dict(bit=-1),dict(bit=32),dict(bit=1,flags=0)):
            bad=deepcopy(request);bad['entries'][target['semantic_id']]=fields
            with self.assertRaises((ProjectError,NativeError)):patch_allocated_flags(context,candidate,allocations,[bad])
        for bad in (dict(request,draft_id='missing'),dict(request,donor_entity_id=ACTOR.replace('0001','0002')),dict(request,entries={target['semantic_id'].replace('0001','0002'):dict(bit=3)})):
            with self.assertRaises((ProjectError,NativeError)):patch_allocated_flags(context,candidate,allocations,[bad])
        with self.assertRaises(ProjectError):patch_allocated_flags(context,candidate,allocations,[request,request])
        bad=deepcopy(allocations);bad['drafts'][0]['record_index']=1
        with self.assertRaises(ProjectError):patch_allocated_flags(context,candidate,bad,[request])
        bad=deepcopy(allocations);bad['drafts'][0]['byte_length']+=1
        with self.assertRaises(ProjectError):patch_allocated_flags(context,candidate,bad,[request])

    def test_unsupported_width_side_effects_and_stopped_paths_reject(self):
        for instruction in (b'\x2b\xf0',b'\x31\xe8',b'\x32\xea',b'\x2e\xe2\x7f'):
            context,candidate,allocations=self.fixture(instruction);owner=ACTOR;entry=context._source.verified_record(owner)[2];request=dict(draft_id='npc-a',donor_entity_id=owner,entries={f'script://{owner.removeprefix("scene://")}/flag-bit/{entry:04x}':dict(bit=3)})
            with self.assertRaises((ProjectError,NativeError)):patch_allocated_flags(context,candidate,allocations,[request])
        for instruction,bit in ((b'\x2b\xe2',16),(b'\x31\xe2',8),(b'\x32\xe2',10)):
            context,candidate,allocations=self.fixture(instruction);target=context.options(ACTOR)['targets'][0]
            with self.assertRaises(NativeError):patch_allocated_flags(context,candidate,allocations,[dict(draft_id='npc-a',donor_entity_id=ACTOR,entries={target['semantic_id']:dict(bit=bit)})])

    def test_review_history_persistence_donor_guards_http_and_repetition(self):
        from tempfile import TemporaryDirectory
        from pathlib import Path
        from unittest.mock import patch
        from sdk.project import ProjectService
        from sdk.npc_flags import source,review
        from sdk.draft_repeat import preview as repeat_preview
        from test_project_workflow import synthetic_scene
        from test_model_primitive_workflow import http_server
        context,_,_=self.fixture(b'\xae\x07\xe2');target=context.options(ACTOR)['targets'][0]
        with TemporaryDirectory() as directory:
            p=ProjectService(Path(directory));p.import_metadata(synthetic_scene());p.command(dict(type='create_actor_draft',donor_entity_id=ACTOR,name='Resident',position=dict(x=128,z=256)));id=next(iter(p.actor_drafts));before=deepcopy(p.actor_drafts);imports=deepcopy(p.imports);depth=len(p.undo_stack)
            with patch.object(ProjectService,'_flag_context',return_value=context):
                request=dict(entity_id=id,entries={target['semantic_id']:dict(bit=3)});report=review(p,request);self.assertEqual(p.actor_drafts,before);self.assertEqual(len(p.undo_stack),depth)
                with self.assertRaises(ProjectError):p.command(dict(type='set_actor_draft_flags',**request,review_key='0'*64))
                p.actor_drafts[id]['position']['x']=192
                with self.assertRaises(ProjectError):p.command(dict(type='set_actor_draft_flags',**request,review_key=report['review_key']))
                p.actor_drafts[id]['position']['x']=128
                p.command(dict(type='set_actor_draft_flags',**request,review_key=report['review_key']));after=deepcopy(p.actor_drafts);self.assertEqual(source(p,id)['options']['targets'][0]['effective_values'],dict(bit=3));self.assertEqual(len(p.undo_stack),depth+1)
                report=review(p,request);p.command(dict(type='set_actor_draft_flags',**request,review_key=report['review_key']));self.assertEqual(len(p.undo_stack),depth+1)
                p.undo();self.assertEqual(p.actor_drafts,before);p.redo();self.assertEqual(ProjectService.open(p.save()).actor_drafts,after)
                self.assertEqual(repeat_preview(p,dict(entity_id=id,count=1,step=dict(x=64,z=0),name='Flags copy'))['copies'][0]['draft']['flags'],after[id]['flags'])
                with self.assertRaises(ProjectError):p.command(dict(type='create_npc_preset',entity_id=id,name='Flag preset'))
                for value in (dict(donor_entity_id='wrong',entries=request['entries']),dict(donor_entity_id=ACTOR,entries={target['semantic_id']:dict(bit=True)})):
                    bad=deepcopy(after[id]);bad['flags']=value
                    with self.assertRaises(ProjectError):p._validate_actor_draft(id,bad)
                with http_server(p) as (server,post):
                    server.RequestHandlerClass.log_message=lambda *args:None
                    self.assertEqual(post('/api/npc-flags-source',dict(entity_id=id))[0],200)
                    self.assertEqual(post('/api/npc-flags-review',dict(entity_id=id,entries={target['semantic_id']:dict(bit=32)}))[0],400)
                    self.assertEqual(post('/api/npc-flags-source',dict(entity_id=id,extra=1))[0],400)
                clear=dict(entity_id=id,entries={});report=review(p,clear);p.command(dict(type='set_actor_draft_flags',**clear,review_key=report['review_key']));self.assertEqual(p.actor_drafts,before);self.assertEqual(p.imports,imports)
                p.mode='live'
                with self.assertRaises(ProjectError):source(p,id)
