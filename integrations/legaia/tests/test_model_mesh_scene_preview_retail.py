"""Optional actual Retail scene endpoint check; no geometry/server substitutions."""
import base64
from copy import deepcopy
import os
from pathlib import Path
import unittest
from sdk.project import ProjectService
from sdk.scene_preview import source_key
from sdk import model_mesh_append
from test_model_mesh_append import glb
from test_model_primitive_workflow import http_server


@unittest.skipUnless(os.environ.get('LEGAIA_GLB_SCENE_PROJECT'),'requires private Retail V7 scene project')
class RetailMeshScenePreview(unittest.TestCase):
    def test_reviewed_replacement_uses_actual_scene_and_preserves_authored_inputs(self):
        project=ProjectService.open(Path(os.environ['LEGAIA_GLB_SCENE_PROJECT']))
        asset='asset://town01/models/scene-tmd/0036';key=source_key(project)
        source=model_mesh_append.source(project,asset,key)
        owner=len(source['objects'])-1
        donor=next(face for face in source['topology']['faces'] if face['object_index']==owner
            and source['objects'][owner]['primitives'][face['current_primitive_index']]['corner_count']==3
            and source['objects'][owner]['primitives'][face['current_primitive_index']]['normal_indices'] is not None)
        content=glb(normals=[[0,1,0],[1,0,0],[0,0,1],[0,1,0]],uvs=[[0,0],[1,0],[0,1],[1,1]])
        before=deepcopy((project._document(),project.undo_stack,project.redo_stack))
        files={str(p.relative_to(project.root)):p.read_bytes() for folder in ('Authored','Imports')
               for p in (project.root/folder).rglob('*') if p.is_file()}
        with http_server(project) as (_,post):
            status,scene=post('/api/scene-preview',dict(representation='authored'))
            self.assertEqual(status,200,scene)
            instances=[row for row in scene['entities'] if row.get('asset_id')==asset and row.get('renderable')]
            self.assertTrue(instances,'Retail source model must have a real renderable scene instance')
            request=dict(asset_id=asset,content_base64=base64.b64encode(content).decode(),
                donor_face_id=donor['face_id'],expected_sha256=source['effective_sha256'],source_key=key,
                new_group=True,replace_group=True)
            status,review=post('/api/model-mesh-append-preview',request);self.assertEqual(status,200,review)
            status,proposal=post('/api/model-mesh-append-scene-preview',dict(request,
                review_key=review['review_key'],proposed_sha256=review['proposed_sha256'],
                entity_id=instances[0]['entity_id'],all_instances=True))
            self.assertEqual(status,200,proposal)
            self.assertEqual(proposal['review_key'],review['review_key'])
            self.assertTrue(proposal['proposal_assets']);self.assertTrue(proposal['proposal_instances'])
            self.assertEqual({row['entity_id'] for row in proposal['proposal_instances']},
                {row['entity_id'] for row in scene['entities'] if row.get('asset_id')==asset and row.get('renderable')})
            self.assertFalse(proposal['project_changed']);self.assertFalse(proposal['gameplay_verified'])
            self.assertEqual(len(proposal['preview']['triangles']),len(review['preview']['triangles']))
        self.assertEqual((project._document(),project.undo_stack,project.redo_stack),before)
        self.assertEqual({str(p.relative_to(project.root)):p.read_bytes() for folder in ('Authored','Imports')
            for p in (project.root/folder).rglob('*') if p.is_file()},files)


if __name__=='__main__':unittest.main()
