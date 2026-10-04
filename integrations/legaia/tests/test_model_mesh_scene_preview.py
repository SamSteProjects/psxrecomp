"""Reviewed GLB topology composes through existing scene pose ownership."""
import base64
from copy import deepcopy
from hashlib import sha256
from types import SimpleNamespace
import unittest
from unittest.mock import patch
from importer.assets import decode_tmd
from importer.animation import pose_vertices
from importer.model_authoring import preview_model_shape
from sdk import model_mesh_append,model_object_allocation
from sdk.scene_preview import preview_shape_instances
from test_model_object_ledger import clone_request
import test_model_mesh_replace_group as fixtures
from test_model_primitive_workflow import http_server


class MeshScenePreviewTests(unittest.TestCase):
    def fixture(self,cloned=False):
        h=fixtures.MeshGroupReplacementTests();self.addCleanup(h.doCleanups)
        p,asset,donor,content=h.fixture()
        if cloned:
            with patch('sdk.model_object_allocation.source_key',return_value='a'*64):
                source=model_object_allocation.source(p,asset,'a'*64)
                requests=[clone_request(source['topology'],source['object_identities'][0],2800)]
                report=model_object_allocation.review(p,asset,requests,source['effective_sha256'],'a'*64)
                p.apply_model_object_allocations(asset,requests,source['effective_sha256'],'a'*64,report['review_key'])
            source=model_mesh_append.source(p,asset,'a'*64)
            donor=next(f['face_id'] for f in source['topology']['faces'] if f['object_index']==1)
        current=p.read_model_replacement(asset,p.model_overrides[asset]);raw=decode_tmd(current)
        if cloned:
            # Construct the same qualified full Current geometry as the native preview composer.
            base=p._model_source(asset,p.active_scene)
            raw=preview_model_shape(decode_tmd(base),current,p.model_overrides[asset])
        raw['authored_shape']=deepcopy(p.model_overrides[asset])
        transforms=[dict(object_index=0,translation=[12,7,-3],rotation_psx=[0,0,1024])]
        posed=deepcopy(raw);posed.update(posed=True,pose={'object_transforms':transforms})
        if not cloned:posed['vertices']=pose_vertices(raw['vertices'],raw['objects'],transforms)
        else:
            posed['pose']['unposed_object_indices']=[1]
            posed['pose']['pose_scope']='verified_existing_channels_with_explicit_unposed_native_objects'
        scene=dict(scene_id=p.active_scene,entities=[dict(entity_id='one',asset_id=asset,renderable=True,geometry_key='raw'),dict(entity_id='two',asset_id=asset,renderable=True,geometry_key='raw'),dict(entity_id='posed',asset_id=asset,renderable=True,geometry_key='posed'),dict(entity_id='missing',asset_id=asset,renderable=False,reason='Unavailable')],assets=[dict(asset_id=asset,geometry_key='raw',preview=raw),dict(asset_id=asset,geometry_key='posed',preview=posed)])
        return p,asset,donor,content,scene

    def test_http_reprepares_review_and_preserves_scene_and_project(self):
        p,asset,donor,content,scene=self.fixture();source=model_mesh_append.source(p,asset,'a'*64)
        args=(asset,content,donor,source['effective_sha256'],'a'*64)
        report=model_mesh_append.review(p,*args,new_group=True,replace_group=True)
        state=deepcopy((p._document(),p.undo_stack,p.redo_stack,scene));files=set((p.root/'Authored'/'Models').iterdir())
        body=dict(asset_id=asset,content_base64=base64.b64encode(content).decode(),donor_face_id=donor,expected_sha256=source['effective_sha256'],source_key='a'*64,new_group=True,replace_group=True,review_key=report['review_key'],proposed_sha256=report['proposed_sha256'],entity_id='one',all_instances=True)
        with http_server(p) as (server,post),patch.dict(p.assets.records,{asset:dict(id=asset)}),patch('sdk.scene_preview.source_key',return_value='a'*64),patch.object(server.scene_previews,'preview',return_value=scene),patch.object(server,'model_preview',side_effect=lambda asset,**kw:kw['prepared']):
            for changes in (dict(review_key='0'*64),dict(proposed_sha256='0'*64),dict(replace_group=False),dict(all_instances=1),dict(entity_id='missing'),dict(extra=True)):
                self.assertEqual(post('/api/model-mesh-append-scene-preview',{**body,**changes})[0],400)
            status,posed=post('/api/model-mesh-append-scene-preview',body);self.assertEqual(status,200,posed)
            self.assertEqual(len(posed['proposal_assets']),2);self.assertEqual(len(posed['proposal_instances']),3)
            self.assertEqual(posed['unavailable_instances'],[dict(entity_id='missing',reason='Unavailable')])
            self.assertEqual(posed['review_key'],report['review_key']);self.assertEqual(len(posed['preview']['triangles']),3)
            self.assertNotIn('current_preview',posed)
            candidate,binding,_=model_mesh_append.prepare(p,*args,new_group=True,replace_group=True)
            expected=preview_shape_instances(scene,asset,candidate,binding)
            self.assertEqual(posed['proposal_assets'],expected['proposal_assets'])
        self.assertEqual((p._document(),p.undo_stack,p.redo_stack,scene),state)
        self.assertEqual(set((p.root/'Authored'/'Models').iterdir()),files)

    def test_scene_composes_all_modes_and_copied_v7_objects(self):
        for cloned in (False,True):
            p,asset,donor,content,scene=self.fixture(cloned)
            source=model_mesh_append.source(p,asset,'a'*64)
            for new_group,replace_group in ((False,False),(True,False),(True,True)):
                candidate,binding,report=model_mesh_append.prepare(p,asset,content,donor,source['effective_sha256'],'a'*64,new_group=new_group,replace_group=replace_group)
                baseline=deepcopy(scene)
                proposed=preview_shape_instances(scene,asset,candidate,binding)
                self.assertEqual(scene,baseline)
                self.assertEqual(len(proposed['proposal_assets']),2)
                raw=proposed['proposal_assets'][0]['preview'];posed=proposed['proposal_assets'][1]['preview']
                self.assertEqual(len(raw['triangles']),len(report['preview']['triangles']))
                self.assertEqual(raw['vertices'],report['preview']['vertices'])
                self.assertEqual(raw['materials'],report['preview']['materials'])
                if cloned:
                    start=raw['objects'][1]['vertex_start']
                    self.assertEqual(posed['vertices'][start:],raw['vertices'][start:])
                else:
                    self.assertEqual(posed['vertices'],pose_vertices(report['preview']['vertices'],report['preview']['objects'],scene['assets'][1]['preview']['pose']['object_transforms']))


if __name__=='__main__':unittest.main()
