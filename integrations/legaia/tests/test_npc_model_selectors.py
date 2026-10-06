"""Independent NPC selector words preserve imported and composed bytes."""
from copy import deepcopy
from hashlib import sha256
import unittest
from importer.core import ImportError as NativeError
from importer.man_actor_structure import append_actor_donor
from importer.man_layout import read_man_layout
from importer.model_selector_authoring import ModelSelectorAuthoringContext
from importer.wait_authoring import WaitAuthoringContext
from sdk.npc_model_selectors import patch_allocated_model_selectors
from sdk.npc_waits import patch_allocated_waits
from sdk.project import ProjectError
from test_importer_dialogue_authoring import fixture,ACTOR
from test_model_selector_authoring import END

class NpcModelSelectorTests(unittest.TestCase):
    def fixture(self,extended=False):
        source,candidate=fixture((b'\xcc\x07\x50' if extended else b'\x4c\x50')+b'\xef\0\x4a\x0a\0'+END)
        context=ModelSelectorAuthoringContext(source);allocations={'drafts':[]}
        for id in ('npc-a','npc-b'):
            candidate,row=append_actor_donor(candidate,sha256(candidate).hexdigest(),1);allocations['drafts'].append(dict(row,draft_id=id))
        target=context.options(ACTOR)['targets'][0]
        return context,candidate,allocations,target

    def test_signed_words_final_offsets_two_clones_and_retained_wait(self):
        for extended in (False,True):
            for a,b in ((-32768,32767),(-1,240),(0,239)):
                context,candidate,allocations,target=self.fixture(extended)
                waits=WaitAuthoringContext(context._source);wait=waits.options(ACTOR)['targets'][0]
                candidate,wait_audit=patch_allocated_waits(waits,candidate,allocations,[dict(draft_id=id,donor_entity_id=ACTOR,entries={wait['semantic_id']:dict(duration_ticks=value)}) for id,value in [('npc-a',11),('npc-b',22)]])
                requests=[dict(draft_id=id,donor_entity_id=ACTOR,entries={target['semantic_id']:dict(model_selector_signed=value)}) for id,value in [('npc-a',a),('npc-b',b)]]
                result,audit=patch_allocated_model_selectors(context,candidate,allocations,requests);self.assertEqual(read_man_layout(result),read_man_layout(candidate));allowed=set()
                for row,value in zip(audit['changes'],[a,b]):
                    at=row['decoded_byte_offset'];self.assertEqual(int.from_bytes(result[at:at+2],'little',signed=True),value);self.assertNotEqual(at,row['source_decoded_byte_offset']);self.assertEqual(row['target_context'],7 if extended else None);allowed.update(range(at,at+2))
                self.assertTrue(all(x==y for i,(x,y) in enumerate(zip(candidate,result)) if i not in allowed))
                for row in wait_audit['changes']:
                    at=row['decoded_byte_offset'];self.assertEqual(result[at:at+2],candidate[at:at+2])
                self.assertFalse(audit['gameplay_verified'])
                noop,_=patch_allocated_model_selectors(context,candidate,allocations,[dict(requests[0],entries={target['semantic_id']:dict(model_selector_signed=239)})]);self.assertEqual(noop,candidate)

    def test_typed_source_ownership_allocation_and_noop_preimages(self):
        context,candidate,allocations,target=self.fixture(True);id=target['semantic_id'];request=dict(draft_id='npc-a',donor_entity_id=ACTOR,entries={id:dict(model_selector_signed=240)})
        for fields in (dict(model_selector_signed=True),dict(model_selector_signed=-32769),dict(model_selector_signed=32768),dict(model_selector_signed=1.5),dict(model_selector_signed=0,asset_id='invented')):
            with self.assertRaises((ProjectError,NativeError)):patch_allocated_model_selectors(context,candidate,allocations,[dict(request,entries={id:fields})])
        for altered in ([request,request],[dict(request,donor_entity_id=ACTOR[:-4]+'0000')],[dict(request,entries={id[:-4]+'ffff':dict(model_selector_signed=0)})]):
            with self.assertRaises((ProjectError,NativeError)):patch_allocated_model_selectors(context,candidate,allocations,altered)
        layout=read_man_layout(candidate);record=next(r for r in layout['records'] if r['partition']==1 and r['record_index']==allocations['drafts'][0]['record_index']);start=record['byte_offset'];relative=target['decoded_byte_offset']-context._source.verified_record(ACTOR)[0]
        for at in range(target['pc'],relative+2):
            forged=bytearray(candidate);forged[start+at]^=1
            for value in (239,240):
                with self.assertRaises((ProjectError,NativeError)):patch_allocated_model_selectors(context,bytes(forged),allocations,[dict(request,entries={id:dict(model_selector_signed=value)})])
        forged=deepcopy(allocations);forged['drafts'][0]['record_index']=1
        with self.assertRaises(ProjectError):patch_allocated_model_selectors(context,candidate,forged,[request])
        source,_=fixture(b'\x4c\x50\xef\0\xff');self.assertFalse(ModelSelectorAuthoringContext(source).options(ACTOR)['supported'])

    def test_project_review_history_repetition_and_http_contract(self):
        from tempfile import TemporaryDirectory
        from pathlib import Path
        from unittest.mock import patch
        from sdk.project import ProjectService
        from sdk.npc_model_selectors import source,review
        from sdk.draft_repeat import preview
        from test_project_workflow import synthetic_scene
        from test_model_primitive_workflow import http_server
        context,_,_,target=self.fixture(True);selector=target['semantic_id']
        with TemporaryDirectory() as directory:
            p=ProjectService(Path(directory));p.import_metadata(synthetic_scene());p.command(dict(type='create_actor_draft',donor_entity_id=ACTOR,name='Resident',position=dict(x=128,z=256)));id=next(iter(p.actor_drafts));before=deepcopy(p.actor_drafts)
            with patch.object(ProjectService,'_model_selector_context',return_value=context):
                request=dict(entity_id=id,entries={selector:dict(model_selector_signed=-1)});accepted=review(p,request);self.assertEqual(p.actor_drafts,before)
                p.actor_drafts[id]['position']['x']=192
                with self.assertRaises(ProjectError):p.command(dict(type='set_actor_draft_model_selectors',**request,review_key=accepted['review_key']))
                p.actor_drafts[id]['position']['x']=128;p.command(dict(type='set_actor_draft_model_selectors',**request,review_key=accepted['review_key']));after=deepcopy(p.actor_drafts);self.assertEqual(source(p,id)['options']['targets'][0]['effective_values'],dict(model_selector_signed=-1));p.undo();self.assertEqual(p.actor_drafts,before);p.redo();self.assertEqual(ProjectService.open(p.save()).actor_drafts,after)
                self.assertEqual(preview(p,dict(entity_id=id,count=1,step=dict(x=64,z=0),name='Selector copy'))['copies'][0]['draft']['model_selectors'],after[id]['model_selectors'])
                with self.assertRaises(ProjectError):p.command(dict(type='create_npc_preset',entity_id=id,name='Selector resident'))
                with http_server(p) as (server,post):
                    server.RequestHandlerClass.log_message=lambda *args:None
                    self.assertEqual(post('/api/npc-model-selectors-source',dict(entity_id=id))[0],200)
                    self.assertEqual(post('/api/npc-model-selectors-review',dict(entity_id=id,entries={selector:dict(model_selector_signed=True)}))[0],400)
                clear=dict(entity_id=id,entries={});accepted=review(p,clear);p.command(dict(type='set_actor_draft_model_selectors',**clear,review_key=accepted['review_key']));self.assertEqual(p.actor_drafts,before)
                p.mode='live'
                with self.assertRaises(ProjectError):source(p,id)

    def test_owned_branch_composes_selector_before_skipping_original_instruction(self):
        from tempfile import TemporaryDirectory
        from pathlib import Path
        from unittest.mock import patch
        from importer.branch_authoring import BranchAuthoringContext
        from sdk.project import ProjectService
        from sdk.npc_branches import review as branch_review,patch_allocated_branches
        from sdk.npc_model_selectors import review as selector_review
        from test_project_workflow import synthetic_scene
        source,man=fixture(b'\x26\x02\0\x4c\x50\xef\0\x26\xf8\xff');selectors=ModelSelectorAuthoringContext(source);branches=BranchAuthoringContext(source);selector=selectors.options(ACTOR)['targets'][0]['semantic_id'];branch=branches.options(ACTOR)['targets'][0]['semantic_id']
        with TemporaryDirectory() as directory:
            p=ProjectService(Path(directory));p.import_metadata(synthetic_scene());p.command(dict(type='create_actor_draft',donor_entity_id=ACTOR,name='Skipped selector',position=dict(x=128,z=256)));id=next(iter(p.actor_drafts))
            with patch.object(ProjectService,'_model_selector_context',return_value=selectors),patch.object(ProjectService,'_branch_context',return_value=branches):
                request=dict(entity_id=id,entries={selector:dict(model_selector_signed=-1)});accepted=selector_review(p,request);p.command(dict(type='set_actor_draft_model_selectors',**request,review_key=accepted['review_key']))
                request=dict(entity_id=id,entries={branch:dict(target_pc=12)});accepted=branch_review(p,request);self.assertIn(8,accepted['changes'][0]['unreachable_source_pcs']);p.command(dict(type='set_actor_draft_branches',**request,review_key=accepted['review_key']))
                candidate,row=append_actor_donor(man,sha256(man).hexdigest(),1);allocation={'drafts':[dict(row,draft_id=id)]};candidate,selector_audit=patch_allocated_model_selectors(selectors,candidate,allocation,[dict(draft_id=id,**p.actor_drafts[id]['model_selectors'])]);result,_=patch_allocated_branches(branches,candidate,allocation,[dict(draft_id=id,**p.actor_drafts[id]['branches'])]);at=selector_audit['changes'][0]['decoded_byte_offset'];self.assertEqual(result[at:at+2],b'\xff\xff')

if __name__=='__main__':unittest.main()
