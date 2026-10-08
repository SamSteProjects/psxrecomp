"""Destination authoring delegates exact source NPC bytes and one history step."""
from copy import deepcopy
import json, os
from pathlib import Path
import tempfile, unittest
from sdk.npc_arrival_authoring import review, source_view
from sdk.npc_arrival_preview import source_key
from sdk.npc_transitions import review as source_review
from sdk.npc_current_script import inspect
from sdk.project import ProjectError, ProjectService
from sdk.scene_preview import source_key as scene_key
from sdk.project_copy import source_key as copy_key
from importer.pipeline import import_scene
from test_model_primitive_workflow import http_server
import test_npc_transition_workflow as workflow


@unittest.skipUnless(os.environ.get('LEGAIA_DISC_BIN'), 'Private Retail disc required')
class NpcArrivalAuthoring(unittest.TestCase):
    def test_retail_bytes_partial_ownership_review_apply_noop_history_and_http(self):
        with tempfile.TemporaryDirectory() as raw:
            p, entity=workflow.NpcTransitionWorkflow().project(raw)
            p.import_metadata(import_scene(os.environ['LEGAIA_DISC_BIN'],'town01'),os.environ['LEGAIA_DISC_BIN'])
            p.active_scene='scene://map02'
            p.command(dict(type='create_actor_draft',donor_entity_id=workflow.OWNER,name='Independent arrival',position=dict(x=192,z=576)))
            second=next(k for k in p.actor_drafts if k!=entity)
            for identity,values in [(entity,dict(direction_encoded=248)),(second,dict(entry_x_encoded=0,entry_z_encoded=255,direction_encoded=7))]:
                body=dict(entity_id=identity,entries={workflow.TARGET:values});r=source_review(p,body)
                p.command(dict(type='set_actor_draft_transitions',**body,review_key=r['review_key']))
            p.command(dict(type='set_transition_entry',entity_id=workflow.OWNER,transition_id=workflow.TARGET,values=dict(direction_encoded=3)))
            before=deepcopy((p._document(),p.undo_stack,p.redo_stack,p.imports,p.overrides))
            current=inspect(p,entity);request=dict(entity_id=entity,transition_id=workflow.TARGET,project_inputs_key=source_key(p),destination_source_key=scene_key(p),arrival=dict(x=128,z=192,facing_sector=7))
            report=review(p,request)
            expected=bytearray.fromhex(current['inspection']['record']['raw_hex']);self.assertEqual(expected[62:65],bytes([31,30,248]));expected[62:65]=bytes([128,1,255])
            self.assertEqual(report['native_review']['inspection']['record']['raw_hex'],expected.hex())
            self.assertEqual(report['proposed_encoded'],dict(entry_x_encoded=128,entry_z_encoded=1,direction_encoded=255))
            self.assertEqual(before,(p._document(),p.undo_stack,p.redo_stack,p.imports,p.overrides))
            with http_server(p) as (_,post):
                self.assertEqual(post('/api/npc-arrival-review',request),(200,report))
                for bad in ({**request,'arrival':dict(x=65)},{**request,'project_inputs_key':'0'*64},{**request,'destination_source_key':'0'*64},{**request,'arrival':dict(y=1)}):
                    self.assertEqual(post('/api/npc-arrival-review',bad)[0],400)
            p.command(dict(type='set_actor_draft_arrival',**request,review_key=report['review_key']))
            self.assertEqual(inspect(p,entity)['inspection']['record']['raw_hex'],expected.hex())
            self.assertEqual(len(p.undo_stack),len(before[1])+1);self.assertEqual(p.active_scene,'scene://map02')
            self.assertEqual(p.actor_drafts[second],before[0]['actor_drafts'][second])
            self.assertEqual(p.imports,before[3]);self.assertEqual(p.overrides,before[4])
            after=deepcopy(p._document());p.undo();self.assertEqual(p._document(),before[0]);p.redo();self.assertEqual(p._document(),after)
            self.assertEqual(ProjectService.open(p.save())._document(),after)
            noop={**request,'project_inputs_key':source_key(p),'destination_source_key':scene_key(p)}
            unchanged=deepcopy((p._document(),p.undo_stack,p.redo_stack));r=review(p,noop);self.assertFalse(r['authored_change'])
            p.command(dict(type='set_actor_draft_arrival',**noop,review_key=r['review_key']));self.assertEqual(unchanged,(p._document(),p.undo_stack,p.redo_stack))
            with self.assertRaises(ProjectError):p.command(dict(type='set_actor_draft_arrival',**request,review_key=report['review_key']))
            p.active_scene='scene://town01';self.assertEqual(source_view(p,entity).active_scene,'scene://map02');self.assertEqual(p.active_scene,'scene://town01')
            with self.assertRaisesRegex(ProjectError,'qualified destination'):review(p,{**noop,'destination_source_key':scene_key(p)})
            p.active_scene='scene://map02';p.mode='live'
            with self.assertRaises(ProjectError):review(p,{**noop,'project_inputs_key':source_key(p)})
            p.mode='edit';p.undo()
            evidence=os.environ.get('LEGAIA_NPC_ARRIVAL_AUTHORING_EVIDENCE')
            if evidence:
                root=Path(evidence);root.mkdir(parents=True,exist_ok=True)
                state=dict(project=dict(mode='edit'),scene=dict(id=p.active_scene),scenes=[dict(id=s) for s in p.imports],actor_drafts=p.actor_drafts,project_copy_source_key=copy_key(p),npc_arrival_preview_state_key=source_key(p),scene_preview_source_key=scene_key(p))
                fresh={**request,'project_inputs_key':source_key(p),'destination_source_key':scene_key(p)}
                (root/'retail.json').write_text(json.dumps(dict(request=fresh,report=review(p,fresh),state=state)),encoding='utf-8')


if __name__=='__main__':unittest.main()
