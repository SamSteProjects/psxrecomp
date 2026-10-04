"""Reviewed allocated poses use the native clip and Current authored geometry."""
from copy import deepcopy
from hashlib import sha256
import os
import tempfile
import unittest

from importer.animation import pose_vertices
from sdk.project import digest
from sdk.scene_preview import source_key
import test_animation_glb_workflow as workflow
from test_model_primitive_workflow import http_server


@unittest.skipUnless(os.environ.get('LEGAIA_DISC_BIN'),'requires private retail disc')
class AnimationAllocationPose(unittest.TestCase):
    def test_options_and_pose_review_keep_project_unchanged_and_compose_current_shape(self):
        with tempfile.TemporaryDirectory() as directory:
            project = workflow.AnimationGlbWorkflow().project(directory)
            owner = 'scene://town01/actors/man-p1/0011'
            options = project.animation_authoring_options(owner)
            asset = options['binding']['asset_semantic_id']
            original = project._model_source(asset,project.active_scene)
            project.translate_model_object(asset,0,[2,0,0],sha256(original).hexdigest())
            before = digest(dict(overrides=project.overrides,models=project.model_overrides,undo=project.undo_stack))
            with http_server(project) as (_,post):
                status,available = post('/api/animation-record-allocation-options',dict(entity_id=owner,expected_source_key=source_key(project)))
                self.assertEqual(status,200,available)
                self.assertEqual(available['donor_animation_id'],options['binding']['semantic_id'])
                self.assertEqual(available['donor_frame_count'],options['binding']['frame_count'])
                self.assertTrue(available['build_available'])
                body = dict(entity_id=owner,expected_source_key=source_key(project),source_frame_indices=[1,0,1,0],edits=[])
                status,review = post('/api/animation-record-allocation-preview',body)
                self.assertEqual(status,200,review)
                status,preview = post('/api/animation-record-allocation-pose-preview',dict(body,review_key=review['review_key']))
                self.assertEqual(status,200,preview)
                self.assertEqual(preview['report'],review)
                self.assertEqual(preview['semantic_id'],asset)
                self.assertEqual(preview['authored_shape']['asset_sha256'],project.model_overrides[asset]['asset_sha256'])
                animation = preview['animation']
                self.assertEqual(animation['representation'],'allocation_preview')
                self.assertEqual(animation['semantic_id'],review['animation_id'])
                self.assertFalse(animation['association']['runtime_assigned'])
                self.assertEqual(animation['source_record']['record_sha256'],review['proposed_ledger']['records'][-1]['record_sha256'])
                self.assertEqual(len(preview['frames']),4)
                self.assertEqual(preview['frames'][0]['vertices'],preview['frames'][2]['vertices'])
                self.assertEqual(preview['frames'][1]['vertices'],preview['frames'][3]['vertices'])
                for frame in preview['frames']:
                    expected = pose_vertices(preview['vertices'],preview['objects'],frame['object_transforms'])
                    self.assertEqual(frame['vertices'],expected)
                for bad in (dict(body,review_key='0'*64),dict(body,review_key=review['review_key'],source_frame_indices=[0]),
                            dict(body,review_key=review['review_key'],expected_source_key='0'*64)):
                    status,_ = post('/api/animation-record-allocation-pose-preview',bad)
                    self.assertEqual(status,400)
                self.assertEqual(digest(dict(overrides=project.overrides,models=project.model_overrides,undo=project.undo_stack)),before)


if __name__ == '__main__': unittest.main()
