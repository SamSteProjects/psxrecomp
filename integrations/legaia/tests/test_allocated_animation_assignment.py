from hashlib import sha256
import os
import tempfile
import unittest

from sdk.animation_allocation import prepare_record_allocation,prepare_record_activation
from sdk.project import digest
from sdk.scene_preview import source_key
import test_animation_glb_workflow as workflow
from test_model_primitive_workflow import http_server


@unittest.skipUnless(os.environ.get('LEGAIA_DISC_BIN'),'requires private retail disc')
class AllocatedAnimationAssignment(unittest.TestCase):
    def test_readonly_review_pose_rebases_native_selector_after_other_clip_retirement(self):
        with tempfile.TemporaryDirectory() as directory:
            project=workflow.AnimationGlbWorkflow().project(directory);owner='scene://town01/actors/man-p1/0011';ids=[]
            for sequence in ([1,0,1],[0,1,0,1]):
                key=source_key(project);_,review=prepare_record_allocation(project,owner,sequence,[],key)
                project.command(dict(type='allocate_animation_record',entity_id=owner,source_frame_indices=sequence,
                    edits=[],expected_source_key=key,review_key=review['review_key']))
                ids.append(review['proposed_ledger']['records'][-1]['record_id'])
            asset=project.animation_authoring_options(owner)['binding']['asset_semantic_id']
            original=project._model_source(asset,project.active_scene)
            project.translate_model_object(asset,0,[2,0,0],sha256(original).hexdigest())
            with http_server(project) as (_,post):
                before=digest(dict(overrides=project.overrides,models=project.model_overrides,undo=project.undo_stack))
                request=dict(entity_id=owner,record_id=ids[1],expected_source_key=source_key(project))
                status,review=post('/api/allocated-animation-assignment-review',request)
                self.assertEqual(status,200,review)
                self.assertEqual(review['native_animation_id'],71)
                self.assertFalse(review['capabilities']['apply'])
                self.assertEqual(review['proposed_component']['record_id'],ids[1])
                status,pose=post('/api/allocated-animation-assignment-pose',dict(request,review_key=review['review_key']))
                self.assertEqual(status,200,pose)
                self.assertEqual(pose['report'],review)
                self.assertEqual(pose['animation']['entity_id'],owner)
                self.assertEqual(len(pose['frames']),4)
                self.assertEqual(pose['authored_shape']['asset_sha256'],project.model_overrides[asset]['asset_sha256'])
                self.assertEqual(pose['frames'][0]['vertices'],pose['frames'][2]['vertices'])
                self.assertEqual(before,digest(dict(overrides=project.overrides,models=project.model_overrides,undo=project.undo_stack)))
                other=next(a['semantic_id'] for a in project.imports[project.active_scene]['actors']
                    if a['model_reference'].get('asset_semantic_id')!=review['proposed_component']['model_asset_id'])
                for bad in (dict(request,entity_id=other),dict(request,record_id='missing'),dict(request,expected_source_key='0'*64),dict(request,extra=True)):
                    status,_=post('/api/allocated-animation-assignment-review',bad);self.assertEqual(status,400)
                status,_=post('/api/allocated-animation-assignment-pose',dict(request,review_key='0'*64));self.assertEqual(status,400)
                key=source_key(project);_,change=prepare_record_activation(project,project.active_scene,ids[0],False,key)
                project.command(dict(type='set_animation_record_active',scene_id=project.active_scene,record_id=ids[0],
                    active=False,expected_source_key=key,review_key=change['review_key']))
                status,_=post('/api/allocated-animation-assignment-pose',dict(request,review_key=review['review_key']));self.assertEqual(status,400)
                request['expected_source_key']=source_key(project)
                status,fresh=post('/api/allocated-animation-assignment-review',request)
                self.assertEqual(status,200,fresh)
                self.assertEqual(fresh['native_animation_id'],70)
                self.assertEqual(fresh['proposed_component'],review['proposed_component'])
                self.assertNotEqual(fresh['review_key'],review['review_key'])


if __name__=='__main__':unittest.main()
