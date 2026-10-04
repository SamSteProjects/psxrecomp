"""One Retail retained GLB workflow: roundtrip, growth, Preview and atomic Apply."""
from copy import deepcopy
import base64
import os
from pathlib import Path
import struct
import tempfile
import unittest
from sdk.animation_allocation import prepare_record_allocation
from sdk.animation_record_ledger import compose
from sdk.scene_preview import source_key
from sdk.project import ProjectService
import test_animation_glb_workflow as workflow
from test_model_primitive_workflow import http_server
from test_importer_export import parse_glb
from test_animation_glb import encode


@unittest.skipUnless(os.environ.get('LEGAIA_DISC_BIN'),'requires private retail disc')
class RetainedAnimationGlb(unittest.TestCase):
    def test_bound_roundtrip_explicit_growth_and_reference_transaction(self):
        with tempfile.TemporaryDirectory() as directory:
            project=workflow.AnimationGlbWorkflow().project(directory);owner='scene://town01/actors/man-p1/0011'
            key=source_key(project);edits=[dict(frame_index=1,object_index=0,translation=dict(x=9))]
            _,allocation=prepare_record_allocation(project,owner,[1,0,1],edits,key)
            project.command(dict(type='allocate_animation_record',entity_id=owner,source_frame_indices=[1,0,1],edits=edits,expected_source_key=key,review_key=allocation['review_key']))
            record=allocation['proposed_ledger']['records'][0]['record_id']
            with http_server(project) as (_,post):
                assignment=dict(entity_id=owner,record_id=record,expected_source_key=source_key(project))
                status,review=post('/api/allocated-animation-assignment-review',assignment);self.assertEqual(status,200,review)
                status,_=post('/api/allocated-animation-assignment',dict(assignment,review_key=review['review_key']));self.assertEqual(status,200)
                key=source_key(project)
                status,export=post('/api/export/allocated-animation',dict(scene_id=project.active_scene,record_id=record,expected_source_key=key,representation='allocated_initial_assignment',entity_id=owner,clip_fps=15))
                self.assertEqual(status,200,export);self.assertEqual(export['binding']['schema_version'],'legaia.animation-record-glb-binding.v1')
                self.assertTrue(Path(export['binding_path']).is_file())
                content=Path(export['path']).read_bytes()
                request=dict(scene_id=project.active_scene,record_id=record,expected_source_key=key,source_frame_indices=[1,0,1],binding=export['binding'],glb_base64=base64.b64encode(content).decode())
                before=deepcopy((project.overrides,project.undo_stack,project.redo_stack))
                status,noop=post('/api/animation-record-glb-review',request);self.assertEqual(status,200,noop);self.assertFalse(noop['project_change'])
                status,_=post('/api/animation-record-glb-import',dict(request,review_key=noop['review_key']));self.assertEqual(status,200)
                self.assertEqual((project.overrides,project.undo_stack,project.redo_stack),before)
                doc,binary=parse_glb(content);binary=bytearray(binary)
                channel=next(c for c in doc['animations'][0]['channels'] if c['target']==dict(node=0,path='translation'))
                sampler=doc['animations'][0]['samplers'][channel['sampler']];accessor=doc['accessors'][sampler['output']];view=doc['bufferViews'][accessor['bufferView']]
                at=view.get('byteOffset',0)+accessor.get('byteOffset',0);desired=struct.unpack_from('<f',binary,at)[0]+3
                struct.pack_into('<f',binary,at,desired);changed=encode(doc,bytes(binary))
                request=dict(request,source_frame_indices=[1,0,1,0],glb_base64=base64.b64encode(changed).decode())
                status,review=post('/api/animation-record-glb-review',request);self.assertEqual(status,200,review)
                self.assertTrue(review['project_change']);self.assertEqual(review['analysis']['frame_count'],4)
                self.assertEqual(review['content_review']['after']['record_id'],record)
                self.assertEqual(set(review['content_review']['assignment_updates']),{owner})
                status,pose=post('/api/animation-record-glb-pose',dict(request,review_key=review['review_key']));self.assertEqual(status,200,pose)
                self.assertEqual(len(pose['frames']),4);self.assertEqual(pose['frames'][0]['object_transforms'][0]['translation'][0],desired)
                self.assertEqual(pose['frames'][1]['object_transforms'][0]['translation'][0],9)
                self.assertEqual(pose['animation']['glb_import_proposal'],review)
                self.assertEqual((project.overrides,project.undo_stack,project.redo_stack),before)
                for bad in (dict(request,binding=dict(request['binding'],record_id='wrong')),dict(request,source_frame_indices=[True]),dict(request,glb_base64='invalid!'),dict(request,extra=True)):
                    status,_=post('/api/animation-record-glb-review',bad);self.assertEqual(status,400)
                status,_=post('/api/animation-record-glb-import',dict(request,review_key='0'*64));self.assertEqual(status,400)
                changed_file=dict(request,glb_base64=base64.b64encode(content).decode(),review_key=review['review_key'])
                status,_=post('/api/animation-record-glb-import',changed_file);self.assertEqual(status,400)
                self.assertEqual((project.overrides,project.undo_stack,project.redo_stack),before)
                status,state=post('/api/animation-record-glb-import',dict(request,review_key=review['review_key']));self.assertEqual(status,200,state)
                self.assertEqual(project.overrides[owner]['ActorAllocatedAnimation']['record_sha256'],review['content_review']['candidate_record_sha256'])
                self.assertEqual(len(project.undo_stack),len(before[1])+1)
                after=deepcopy(project.overrides);project.undo();self.assertEqual(project.overrides,before[0]);project.redo();self.assertEqual(project.overrides,after)
                status,_=post('/api/animation-record-glb-review',request);self.assertEqual(status,400)
                reopened=ProjectService.open(project.save());self.assertEqual(reopened.overrides,project.overrides)
                self.assertEqual(compose(reopened,reopened.active_scene)[0],compose(project,project.active_scene)[0])
                from sdk.build_review import review as build_review
                assessment=build_review(reopened);self.assertTrue(assessment['normal_build_ready'],assessment['blockers'])


if __name__=='__main__':unittest.main()
