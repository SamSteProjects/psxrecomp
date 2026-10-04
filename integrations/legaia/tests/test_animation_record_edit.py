"""Retained content and all initial references publish as one Undo entry."""
from copy import deepcopy
import os
from pathlib import Path
import tempfile
import unittest
from sdk.animation_allocation import prepare_record_allocation,prepare_record_activation
from sdk.project import ProjectService
from sdk.scene_preview import source_key
from sdk.animation_record_ledger import compose
import test_animation_glb_workflow as workflow
from test_model_primitive_workflow import http_server


@unittest.skipUnless(os.environ.get('LEGAIA_DISC_BIN'),'requires private retail disc')
class AnimationRecordEdit(unittest.TestCase):
    def test_active_assigned_edit_preview_atomic_history_reopen_and_retired_edit(self):
        with tempfile.TemporaryDirectory() as directory:
            project=workflow.AnimationGlbWorkflow().project(directory);owner='scene://town01/actors/man-p1/0011'
            key=source_key(project);_,allocation=prepare_record_allocation(project,owner,[1,0,1],[],key)
            project.command(dict(type='allocate_animation_record',entity_id=owner,source_frame_indices=[1,0,1],edits=[],expected_source_key=key,review_key=allocation['review_key']))
            record=allocation['proposed_ledger']['records'][0]['record_id']
            with http_server(project) as (_,post):
                assignment=dict(entity_id=owner,record_id=record,expected_source_key=source_key(project))
                status,review=post('/api/allocated-animation-assignment-review',assignment);self.assertEqual(status,200,review)
                status,_=post('/api/allocated-animation-assignment',dict(assignment,review_key=review['review_key']));self.assertEqual(status,200)
                key=source_key(project)
                status,original=post('/api/animation-record-pose',dict(scene_id=project.active_scene,record_id=record,expected_source_key=key));self.assertEqual(status,200)
                value=original['frames'][0]['object_transforms'][0]['translation'][0]^1
                request=dict(scene_id=project.active_scene,record_id=record,source_frame_indices=[1,0,1,0],
                    edits=[dict(frame_index=0,object_index=0,translation=dict(x=value))],expected_source_key=key)
                before=deepcopy((project.overrides,project.undo_stack,project.redo_stack))
                status,review=post('/api/animation-record-edit-review',request);self.assertEqual(status,200,review)
                self.assertEqual(review['record_id'],record);self.assertIn(owner,review['assignment_updates'])
                self.assertNotEqual(review['before']['record_sha256'],review['after']['record_sha256'])
                status,pose=post('/api/animation-record-edit-pose',dict(request,review_key=review['review_key']));self.assertEqual(status,200,pose)
                self.assertEqual(len(pose['frames']),4);self.assertEqual(pose['frames'][0]['object_transforms'][0]['translation'][0],value)
                self.assertEqual(pose['animation']['representation'],'allocated_record_edit_preview')
                self.assertEqual((project.overrides,project.undo_stack,project.redo_stack),before)
                for bad in (dict(request,source_frame_indices=[]),dict(request,source_frame_indices=[True]),dict(request,edits=[dict(frame_index=0,object_index=0,rotation_psx=dict(x=1))]),dict(request,record_id='missing'),dict(request,extra=True)):
                    status,_=post('/api/animation-record-edit-review',bad);self.assertEqual(status,400)
                status,_=post('/api/animation-record-edit',dict(request,review_key='0'*64));self.assertEqual(status,400)
                self.assertEqual((project.overrides,project.undo_stack,project.redo_stack),before)
                status,state=post('/api/animation-record-edit',dict(request,review_key=review['review_key']));self.assertEqual(status,200,state)
                ledger=deepcopy(project.overrides[project.active_scene]['AnimationRecords'])
                self.assertEqual(ledger['records'][0]['record_id'],record)
                self.assertEqual(project.overrides[owner]['ActorAllocatedAnimation']['record_sha256'],review['after']['record_sha256'])
                self.assertEqual(len(project.undo_stack),len(before[1])+1)
                after=deepcopy(project.overrides);project.undo();self.assertEqual(project.overrides,before[0]);project.redo();self.assertEqual(project.overrides,after)
                status,_=post('/api/animation-record-edit',dict(request,review_key=review['review_key']));self.assertEqual(status,400)
                noop=dict(request,expected_source_key=source_key(project))
                status,unchanged=post('/api/animation-record-edit-review',noop);self.assertEqual(status,200,unchanged);self.assertFalse(unchanged['project_change'])
                count=len(project.undo_stack);status,_=post('/api/animation-record-edit',dict(noop,review_key=unchanged['review_key']));self.assertEqual(status,200);self.assertEqual(len(project.undo_stack),count)
                path=project.save();reopened=ProjectService.open(path)
                self.assertEqual(reopened.overrides,project.overrides);self.assertEqual(compose(reopened,reopened.active_scene)[0],compose(project,project.active_scene)[0])
                from sdk.build_review import review as build_review
                assessment=build_review(reopened);self.assertTrue(assessment['normal_build_ready'],assessment['blockers'])
                clear=dict(entity_id=owner,record_id=None,expected_source_key=source_key(project))
                status,review=post('/api/allocated-animation-assignment-review',clear);self.assertEqual(status,200)
                status,_=post('/api/allocated-animation-assignment',dict(clear,review_key=review['review_key']));self.assertEqual(status,200)
                key=source_key(project);_,retirement=prepare_record_activation(project,project.active_scene,record,False,key)
                project.command(dict(type='set_animation_record_active',scene_id=project.active_scene,record_id=record,active=False,expected_source_key=key,review_key=retirement['review_key']))
                request=dict(request,source_frame_indices=[0,1],edits=[],expected_source_key=source_key(project))
                status,review=post('/api/animation-record-edit-review',request);self.assertEqual(status,200,review)
                status,_=post('/api/animation-record-edit',dict(request,review_key=review['review_key']));self.assertEqual(status,200)
                self.assertIn(record,project.overrides[project.active_scene]['AnimationRecords']['removed_record_ids'])
                status,pose=post('/api/animation-record-pose',dict(scene_id=project.active_scene,record_id=record,expected_source_key=source_key(project)));self.assertEqual(status,200,pose)
                self.assertEqual(len(pose['frames']),2);self.assertFalse(pose['animation']['saved_record']['active'])


if __name__=='__main__':unittest.main()
