"""Retained records export their own channels, without authoring project state."""
from copy import deepcopy
from hashlib import sha256
import os
from pathlib import Path
import struct
import tempfile
import unittest
from unittest.mock import patch
from sdk.animation_allocation import prepare_record_allocation,prepare_record_activation
from sdk.scene_preview import source_key
import test_animation_glb_workflow as workflow
from test_model_primitive_workflow import http_server
from test_importer_export import parse_glb


@unittest.skipUnless(os.environ.get('LEGAIA_DISC_BIN'),'requires private retail disc')
class AllocatedAnimationExport(unittest.TestCase):
    def test_saved_retired_proposed_and_assigned_exports_keep_exact_identity(self):
        with tempfile.TemporaryDirectory() as directory:
            project=workflow.AnimationGlbWorkflow().project(directory);owner='scene://town01/actors/man-p1/0011'
            key=source_key(project);_,review=prepare_record_allocation(project,owner,[1,0,1],[],key)
            project.command(dict(type='allocate_animation_record',entity_id=owner,source_frame_indices=[1,0,1],edits=[],expected_source_key=key,review_key=review['review_key']))
            entry=review['proposed_ledger']['records'][0];record=entry['record_id'];asset=entry['donor_asset_id']
            source=project._model_source(asset,project.active_scene)
            project.translate_model_object(asset,0,[2,0,0],sha256(source).hexdigest())
            def request(**extra):return dict(scene_id=project.active_scene,record_id=record,expected_source_key=source_key(project),representation='allocated_record',**extra)
            with http_server(project) as (_,post):
                snapshot=deepcopy((project.overrides,project.model_overrides,project.undo_stack,project.redo_stack))
                status,clip=post('/api/export/allocated-animation',request(clip_fps=15));self.assertEqual(status,200,clip)
                self.assertEqual(clip['audit']['animation']['source_record']['record_sha256'],entry['record_sha256'])
                self.assertEqual(clip['audit']['frame_count'],3);self.assertEqual(clip['audit']['export_fps'],15)
                doc,binary=parse_glb(Path(clip['path']).read_bytes())
                self.assertEqual(doc['extras']['animation']['semantic_id'],f'animation://town01/authored-record/{record}')
                channel=next(c for c in doc['animations'][0]['channels'] if c['target']==dict(node=0,path='translation'))
                sampler=doc['animations'][0]['samplers'][channel['sampler']];accessor=doc['accessors'][sampler['output']];view=doc['bufferViews'][accessor['bufferView']]
                offset=view.get('byteOffset',0)+accessor.get('byteOffset',0)
                values=struct.unpack_from('<12f',binary,offset)
                self.assertEqual(values[:3],values[6:9]);self.assertEqual(values[6:9],values[9:12])
                status,posed=post('/api/export/allocated-animation',request(frame_index=2));self.assertEqual(status,200,posed)
                self.assertTrue(posed['audit']['posed']);self.assertEqual(posed['audit']['frame_index'],2)
                self.assertEqual((project.overrides,project.model_overrides,project.undo_stack,project.redo_stack),snapshot)
                files={p.name:p.read_bytes() for p in (project.root/'Exports').iterdir() if p.is_file()}
                for bad in (request(frame_index=3),request(clip_fps=True),dict(request(frame_index=0),clip_fps=15),dict(request(frame_index=0),extra=True),dict(request(frame_index=0),expected_source_key='0'*64)):
                    status,_=post('/api/export/allocated-animation',bad);self.assertEqual(status,400)
                self.assertEqual(files,{p.name:p.read_bytes() for p in (project.root/'Exports').iterdir() if p.is_file()})
                key=source_key(project);_,activation=prepare_record_activation(project,project.active_scene,record,False,key)
                project.command(dict(type='set_animation_record_active',scene_id=project.active_scene,record_id=record,active=False,expected_source_key=key,review_key=activation['review_key']))
                status,retired=post('/api/export/allocated-animation',request(clip_fps=15));self.assertEqual(status,200,retired)
                self.assertFalse(retired['audit']['animation']['saved_record']['active'])
                key=source_key(project);_,activation=prepare_record_activation(project,project.active_scene,record,True,key)
                project.command(dict(type='set_animation_record_active',scene_id=project.active_scene,record_id=record,active=True,expected_source_key=key,review_key=activation['review_key']))
                assignment=dict(entity_id=owner,record_id=record,expected_source_key=source_key(project))
                status,report=post('/api/allocated-animation-assignment-review',assignment);self.assertEqual(status,200,report)
                proposed=request(clip_fps=15);proposed.update(representation='allocated_assignment_preview',entity_id=owner,review_key=report['review_key'])
                status,export=post('/api/export/allocated-animation',proposed);self.assertEqual(status,200,export)
                self.assertEqual(export['audit']['animation']['assignment_proposal'],report)
                status,_=post('/api/allocated-animation-assignment',dict(assignment,review_key=report['review_key']));self.assertEqual(status,200)
                status,_=post('/api/export/allocated-animation',proposed);self.assertEqual(status,400)
                assigned=request(clip_fps=15);assigned.update(representation='allocated_initial_assignment',entity_id=owner)
                status,export=post('/api/export/allocated-animation',assigned);self.assertEqual(status,200,export)
                self.assertEqual(export['audit']['animation']['authored_assignment'],project.overrides[owner]['ActorAllocatedAnimation'])
                from importer.export import encode_model_glb
                files={p.name:p.read_bytes() for p in (project.root/'Exports').iterdir() if p.is_file()}
                original_overrides=deepcopy(project.overrides)
                def change_during_encoding(*args,**kwargs):
                    result=encode_model_glb(*args,**kwargs)
                    project.overrides[owner]['Transform']=dict(position=dict(x=64))
                    return result
                try:
                    with patch('importer.export.encode_model_glb',side_effect=change_during_encoding):
                        status,error=post('/api/export/allocated-animation',assigned)
                        self.assertEqual(status,400);self.assertIn('during GLB encoding',error['error'])
                    self.assertEqual(files,{p.name:p.read_bytes() for p in (project.root/'Exports').iterdir() if p.is_file()})
                finally:project.overrides=original_overrides


if __name__=='__main__':unittest.main()
