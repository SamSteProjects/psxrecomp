"""Real donor arrival viewport metadata, immutable inspection and stale guards."""
from copy import deepcopy
import json, os
from pathlib import Path
import tempfile, unittest
from unittest.mock import patch
from sdk.npc_arrival_preview import inspect, source_key
from sdk.npc_transitions import review
from sdk.project import ProjectError
from sdk.project_copy import source_key as copy_key
from sdk.scene_preview import source_key as scene_key
from importer.pipeline import import_scene
from test_model_primitive_workflow import http_server
import test_npc_transition_workflow as workflow


@unittest.skipUnless(os.environ.get('LEGAIA_DISC_BIN'), 'Private Retail disc required')
class NpcArrivalPreview(unittest.TestCase):
    def test_retail_current_destination_http_readonly_and_freshness(self):
        with tempfile.TemporaryDirectory() as raw:
            p, entity = workflow.NpcTransitionWorkflow().project(raw)
            p.import_metadata(import_scene(os.environ['LEGAIA_DISC_BIN'], 'town01'), os.environ['LEGAIA_DISC_BIN'])
            p.active_scene = 'scene://map02'
            request = dict(entity_id=entity, entries={workflow.TARGET:dict(entry_x_encoded=0,entry_z_encoded=255,direction_encoded=7)})
            accepted=review(p,request)
            p.command(dict(type='set_actor_draft_transitions',**request,review_key=accepted['review_key']))
            body=dict(entity_id=entity,transition_id=workflow.TARGET,project_source_key=copy_key(p))
            before=deepcopy((p._document(),p.undo_stack,p.redo_stack,p.dirty))
            report=inspect(p,body)
            row=report['source']['options']['transitions'][0]
            self.assertEqual(report['destination_source_key'],scene_key(p))
            self.assertEqual(report['destination_scene_id'],'scene://map02')
            self.assertEqual(row['values'],dict(entry_x_encoded=31,entry_z_encoded=30,direction_encoded=0))
            self.assertEqual(row['effective_values'],dict(entry_x_encoded=0,entry_z_encoded=255,direction_encoded=7))
            self.assertFalse(report['height_known']);self.assertFalse(report['runtime_verified'])
            with http_server(p) as (_,post):
                status, response=post('/api/npc-arrival-preview',body)
                self.assertEqual(status,200);self.assertEqual(response,report)
                for invalid in ({**body,'runtime_position':{}},{**body,'project_source_key':'0'*64},{**body,'transition_id':workflow.TARGET+'x'},{**body,'entity_id':workflow.OWNER}):
                    self.assertEqual(post('/api/npc-arrival-preview',invalid)[0],400)
            with patch('sdk.npc_arrival_preview._verify',side_effect=ProjectError('Destination changed')):
                with self.assertRaisesRegex(ProjectError,'Destination changed'):inspect(p,body)
            self.assertEqual(before,(p._document(),p.undo_stack,p.redo_stack,p.dirty))
            stable=source_key(p);p.active_scene='scene://town01'
            self.assertEqual(stable,source_key(p))
            with self.assertRaises(ProjectError):inspect(p,body)
            p.active_scene='scene://map02';p.mode='live'
            with self.assertRaises(ProjectError):inspect(p,{**body,'project_source_key':copy_key(p)})
            p.mode='edit'
            evidence=os.environ.get('LEGAIA_NPC_ARRIVAL_PREVIEW_EVIDENCE')
            if evidence:
                root=Path(evidence);root.mkdir(parents=True,exist_ok=True)
                state=dict(project=dict(mode='edit'),scene=dict(id=p.active_scene),scenes=[dict(id=s) for s in p.imports],actor_drafts=p.actor_drafts,project_copy_source_key=copy_key(p),npc_arrival_preview_state_key=source_key(p),scene_preview_source_key=scene_key(p))
                (root/'retail.json').write_text(json.dumps(dict(request=body,report=report,state=state)),encoding='utf-8')


if __name__=='__main__':unittest.main()
