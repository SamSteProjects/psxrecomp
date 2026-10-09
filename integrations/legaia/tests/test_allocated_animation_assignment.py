from hashlib import sha256
from copy import deepcopy
import json
import os
from pathlib import Path
import tempfile
import unittest

from sdk.animation_allocation import prepare_record_allocation,prepare_record_activation
from sdk.project import digest,ProjectService,ProjectError
from sdk.build_review import review as build_review
from sdk.scene_preview import source_key
import test_animation_glb_workflow as workflow
from test_model_primitive_workflow import http_server


@unittest.skipUnless(os.environ.get('LEGAIA_DISC_BIN'),'requires private retail disc')
class AllocatedAnimationAssignment(unittest.TestCase):
    def test_review_apply_history_save_open_reference_guards_scene_pose_and_clear(self):
        with tempfile.TemporaryDirectory() as directory:
            project=workflow.AnimationGlbWorkflow().project(directory);owner='scene://town01/actors/man-p1/0011'
            key=source_key(project);_,allocation=prepare_record_allocation(project,owner,[1,0,1],[],key)
            project.command(dict(type='allocate_animation_record',entity_id=owner,source_frame_indices=[1,0,1],
                edits=[],expected_source_key=key,review_key=allocation['review_key']))
            identity=allocation['proposed_ledger']['records'][-1]['record_id']
            with http_server(project) as (server,post):
                request=dict(entity_id=owner,record_id=identity,expected_source_key=source_key(project))
                status,review=post('/api/allocated-animation-assignment-review',request);self.assertEqual(status,200,review)
                before=deepcopy(project.overrides);count=len(project.undo_stack)
                status,_=post('/api/allocated-animation-assignment',dict(request,review_key='0'*64));self.assertEqual(status,400)
                self.assertEqual(project.overrides,before);self.assertEqual(len(project.undo_stack),count)
                status,state=post('/api/allocated-animation-assignment',dict(request,review_key=review['review_key']));self.assertEqual(status,200,state)
                binding=project.overrides[owner]['ActorAllocatedAnimation'];self.assertEqual(binding,review['proposed_component'])
                self.assertEqual(len(project.undo_stack),count+1);self.assertNotEqual(source_key(project),request['expected_source_key'])
                project.undo();self.assertEqual(project.overrides,before);project.redo();self.assertEqual(project.overrides[owner]['ActorAllocatedAnimation'],binding)
                from sdk.animation_glb import _snapshot
                with self.assertRaisesRegex(ProjectError,'retained-record GLB editor'):_snapshot(project,owner,30)
                _,capture=prepare_record_allocation(project,owner,[0],[],source_key(project))
                self.assertEqual(capture['source_allocated_entry']['record_id'],identity)
                self.assertEqual(capture['requested_source_frame_indices'],[0])
                status,_=post('/api/allocated-animation-assignment',dict(request,review_key=review['review_key']));self.assertEqual(status,400)
                retained=deepcopy((project.overrides,project.undo_stack,project.redo_stack))
                key=source_key(project)
                status,_=post('/api/animation-record-activation-preview',dict(scene_id=project.active_scene,record_id=identity,
                    active=False,expected_source_key=key));self.assertEqual(status,400)
                with self.assertRaisesRegex(ProjectError,'still assigned'):
                    project.command(dict(type='set_animation_record_active',scene_id=project.active_scene,record_id=identity,
                        active=False,expected_source_key=key,review_key='0'*64))
                self.assertEqual((project.overrides,project.undo_stack,project.redo_stack),retained)
                reset=next(row for row in project.component_reviews(project.active_scene) if row['component']=='AnimationRecords')
                with self.assertRaises(ProjectError):project.command(dict(type='revert_authored_component',entity_id=project.active_scene,
                    component='AnimationRecords',review_key=reset['review_key']))
                self.assertEqual((project.overrides,project.undo_stack,project.redo_stack),retained)
                assigned=server.actor_initial_animation_preview(owner)
                self.assertEqual(assigned['animation']['authored_assignment'],binding)
                self.assertEqual(assigned['animation']['representation'],'allocated_initial_assignment')
                status,scene=post('/api/scene-preview',{})
                self.assertEqual(status,200,scene)
                row=next(row for row in scene['entities'] if row['entity_id']==owner)
                self.assertTrue(row['renderable']);self.assertEqual(row['pose_kind'],'authored_allocated_initial_animation_frame0')
                geometry=next(item['preview'] for item in scene['assets'] if item['geometry_key']==row['geometry_key'])
                self.assertEqual(geometry['vertices'],assigned['frames'][0]['vertices'])
                # Original bindings support draft donors; they are not extra scene entities.
                self.assertNotEqual(server.scene_previews._bindings[owner+'/retail-draft-source']['geometry_key'],row['geometry_key'])
            path=project.save();saved=path.read_bytes();raw=json.loads(saved)
            raw['authored']=dict(reversed(list(raw['authored'].items())));path.write_text(json.dumps(raw),encoding='utf-8')
            reopened=ProjectService.open(path);self.assertEqual(reopened.overrides[owner]['ActorAllocatedAnimation'],binding)
            offline=json.loads(saved);offline['retail_source']['disc_path']=str(Path(directory)/'missing.bin');path.write_text(json.dumps(offline),encoding='utf-8')
            self.assertEqual(ProjectService.open(path).overrides[owner]['ActorAllocatedAnimation'],binding)
            malformed=json.loads(saved);malformed['authored'][owner]['ActorAllocatedAnimation']['record_sha256']='0'*64
            path.write_text(json.dumps(malformed),encoding='utf-8')
            with self.assertRaises(ProjectError):ProjectService.open(path)
            path.write_bytes(saved)
            files={str(p.relative_to(project.root)):p.read_bytes() for p in project.root.rglob('*') if p.is_file()}
            assessment=build_review(reopened);self.assertTrue(assessment['normal_build_ready'],assessment['blockers'])
            self.assertEqual(files,{str(p.relative_to(project.root)):p.read_bytes() for p in project.root.rglob('*') if p.is_file()})
            with http_server(reopened) as (_,post):
                request=dict(entity_id=owner,record_id=None,expected_source_key=source_key(reopened))
                status,clear=post('/api/allocated-animation-assignment-review',request);self.assertEqual(status,200,clear)
                status,_=post('/api/allocated-animation-assignment',dict(request,review_key=clear['review_key']));self.assertEqual(status,200)
                self.assertNotIn('ActorAllocatedAnimation',reopened.overrides.get(owner,{}));reopened.undo()
                self.assertEqual(reopened.overrides[owner]['ActorAllocatedAnimation'],binding)

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
                self.assertTrue(review['capabilities']['apply'])
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
