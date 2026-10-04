"""Saved and retired clip inspection reconstructs exact captured poses."""
from copy import deepcopy
from hashlib import sha256
import os
from pathlib import Path
import tempfile
import unittest

from sdk.project import digest, ProjectService
from sdk.scene_preview import source_key
import test_animation_glb_workflow as workflow
from test_model_primitive_workflow import http_server


@unittest.skipUnless(os.environ.get('LEGAIA_DISC_BIN'),'requires private retail disc')
class AnimationRecordLibrary(unittest.TestCase):
    def test_saved_retired_pose_and_lifecycle_after_reopen(self):
        with tempfile.TemporaryDirectory() as directory:
            project = workflow.AnimationGlbWorkflow().project(directory)
            owner = 'scene://town01/actors/man-p1/0011'
            with http_server(project) as (_,post):
                request = dict(entity_id=owner,expected_source_key=source_key(project),source_frame_indices=[1,0,1],edits=[])
                status,review = post('/api/animation-record-allocation-preview',request)
                self.assertEqual(status,200,review)
                status,_ = post('/api/animation-record-allocation',dict(request,review_key=review['review_key']))
                self.assertEqual(status,200)
                status,library = post('/api/animation-record-library',dict(scene_id=project.active_scene,expected_source_key=source_key(project)))
                self.assertEqual(status,200,library)
                row = library['records'][0]
                self.assertTrue(row['active'])
                self.assertEqual(row['record_sha256'],review['proposed_ledger']['records'][0]['record_sha256'])
                pose_request = dict(scene_id=project.active_scene,record_id=row['record_id'],expected_source_key=source_key(project))
                before = digest(dict(overrides=project.overrides,models=project.model_overrides,undo=project.undo_stack))
                status,pose = post('/api/animation-record-pose',pose_request)
                self.assertEqual(status,200,pose)
                self.assertEqual(pose['animation']['saved_record'],row)
                self.assertNotIn('record_index',pose['animation']['source_record'])
                self.assertEqual(pose['frames'][0]['vertices'],pose['frames'][2]['vertices'])
                self.assertEqual(digest(dict(overrides=project.overrides,models=project.model_overrides,undo=project.undo_stack)),before)
                for bad in (dict(pose_request,record_id='missing'),dict(pose_request,expected_source_key='0'*64),dict(pose_request,extra=True)):
                    status,_ = post('/api/animation-record-pose',bad)
                    self.assertEqual(status,400)
                activation = dict(pose_request,active=False)
                status,change = post('/api/animation-record-activation-preview',activation)
                self.assertEqual(status,200,change)
                status,_ = post('/api/animation-record-activation',dict(activation,review_key=change['review_key']))
                self.assertEqual(status,200)
                status,_ = post('/api/animation-record-pose',pose_request)
                self.assertEqual(status,400,'retirement invalidates the old scene key')
            project.save()
            reopened = ProjectService.open(Path(project.root))
            self.assertEqual(reopened.overrides,project.overrides)
            options = reopened.animation_authoring_options(owner)
            retail = reopened.animation_channel_values(owner,0,0)['retail']['translation']['x']
            reopened.command(dict(type='set_animation_channels',entity_id=owner,value=dict(
                animation_id=options['binding']['semantic_id'],source_record_sha256=options['binding']['source_record']['record_sha256'],
                edits=[dict(frame_index=0,object_index=0,translation={'x':retail^1})])))
            asset = row['donor_asset_id']
            original = reopened._model_source(asset,reopened.active_scene)
            reopened.translate_model_object(asset,0,[2,0,0],sha256(original).hexdigest())
            with http_server(reopened) as (_,post):
                fresh = dict(scene_id=reopened.active_scene,record_id=row['record_id'],expected_source_key=source_key(reopened))
                status,retired = post('/api/animation-record-pose',fresh)
                self.assertEqual(status,200,retired)
                self.assertFalse(retired['animation']['saved_record']['active'])
                self.assertEqual(retired['animation']['source_record']['record_sha256'],row['record_sha256'])
                self.assertEqual(retired['authored_shape']['asset_sha256'],reopened.model_overrides[asset]['asset_sha256'])
                self.assertNotEqual(retired['frames'][0]['vertices'],pose['frames'][0]['vertices'])
                self.assertEqual([frame['object_transforms'] for frame in retired['frames']],
                                 [frame['object_transforms'] for frame in pose['frames']],
                                 'later shared donor edits must not alter the saved capture')
                before = deepcopy(reopened.overrides)
                status,change = post('/api/animation-record-activation-preview',dict(fresh,active=True))
                self.assertEqual(status,200,change)
                self.assertEqual(reopened.overrides,before)
                status,_ = post('/api/animation-record-activation',dict(fresh,active=True,review_key=change['review_key']))
                self.assertEqual(status,200)
                self.assertEqual(reopened.overrides[reopened.active_scene]['AnimationRecords']['records'][0]['record_sha256'],row['record_sha256'])


if __name__ == '__main__': unittest.main()
