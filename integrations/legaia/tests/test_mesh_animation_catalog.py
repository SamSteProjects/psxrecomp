"""Source clip labels never qualify unselected sampler payloads or mutate projects."""
from copy import deepcopy
from unittest.mock import patch
import base64, unittest
from importer.animation_glb import _read_glb
from importer.model_glb import _write_glb
from importer.model_mesh_animation_catalog import inspect_mesh_animations
from importer.model_mesh_append import inspect_append_mesh
from importer.core import ImportError
from test_model_mesh_animation_pose import animated, pose
import test_model_mesh_append as mesh
from test_model_primitive_workflow import http_server
from sdk import model_mesh_append
from sdk.model_mesh_sources import read_source
from sdk.project import ProjectService


def clips():
    content=animated(mesh.glb(),[(0,'translation','LINEAR',[[0,0,0],[10,0,0]])])
    doc,binary=_read_glb(content)
    doc['animations'][0]['name']='Walk <source>'
    doc['animations'].append(deepcopy(doc['animations'][0]))
    doc['animations'][1]['samplers'][0]['input']=999
    return _write_glb(doc,binary)


class MeshAnimationCatalog(unittest.TestCase):
    def test_duplicate_labels_and_unqualified_payloads_keep_indices(self):
        content=clips();held=bytes(content);catalog=inspect_mesh_animations(content)
        self.assertEqual([r['name'] for r in catalog['clips']],['Walk <source>']*2)
        self.assertEqual([r['animation_index'] for r in catalog['clips']],[0,1])
        self.assertEqual(catalog['clips'][0]['target_nodes'],[0])
        self.assertEqual(catalog['clips'][0]['target_paths'],['translation'])
        self.assertFalse(catalog['sampling_qualified']);self.assertFalse(catalog['payloads_decoded'])
        inspect_append_mesh(content,animation_pose=pose())
        with self.assertRaises(ImportError):inspect_append_mesh(content,animation_pose=pose(index=1))
        self.assertEqual(content,held)

    def test_empty_and_malformed_ownership(self):
        self.assertEqual(inspect_mesh_animations(mesh.glb())['clips'],[])
        doc,binary=_read_glb(clips())
        for change in [lambda d:d['animations'][0].update(name=123),lambda d:d['animations'][0].update(name='x'*513),lambda d:d['animations'][0]['channels'][0]['target'].update(node=True),lambda d:d['nodes'].__setitem__(0,None)]:
            bad=deepcopy(doc);change(bad)
            with self.assertRaises(ImportError):inspect_mesh_animations(_write_glb(bad,binary))

    def test_http_read_only_and_exact_inputs(self):
        helper=mesh.MeshAppendTests();self.addCleanup(helper.doCleanups)
        project,_,_=helper.fixture();before=deepcopy((project._document(),project.undo_stack,project.redo_stack))
        files={p.relative_to(project.root):p.read_bytes() for p in project.root.rglob('*') if p.is_file()}
        body={'content_base64':base64.b64encode(clips()).decode()}
        with http_server(project) as (_,post):
            status,catalog=post('/api/model-mesh-animations',body);self.assertEqual(status,200,catalog)
            self.assertEqual(catalog,inspect_mesh_animations(clips()))
            for bad in [dict(body,animation_pose=pose()),dict(body,scene_index=0),{'content_base64':'bad!'}]:
                status,_=post('/api/model-mesh-animations',bad);self.assertEqual(status,400)
        self.assertEqual((project._document(),project.undo_stack,project.redo_stack),before)
        self.assertEqual({p.relative_to(project.root):p.read_bytes() for p in project.root.rglob('*') if p.is_file()},files)

    def test_named_clip_native_apply_retains_index_not_label(self):
        helper=mesh.MeshAppendTests();self.addCleanup(helper.doCleanups)
        project,asset,donor=helper.fixture();before=deepcopy(project._document());depth=len(project.undo_stack)
        content=clips();source=model_mesh_append.source(project,asset,'a'*64)
        expected,_,_=model_mesh_append.prepare(project,asset,mesh.glb(positions=[[5,0,0],[105,0,0],[5,100,0],[105,100,0]]),donor,source['effective_sha256'],'a'*64)
        body=dict(content_base64=base64.b64encode(content).decode(),asset_id=asset,donor_face_id=donor,expected_sha256=source['effective_sha256'],source_key='a'*64,animation_pose=pose())
        with http_server(project) as (_,post):
            status,review=post('/api/model-mesh-append-preview',body);self.assertEqual(status,200,review)
            status,_=post('/api/model-mesh-append',dict(body,review_key=review['review_key']));self.assertEqual(status,200)
        self.assertEqual(len(project.undo_stack),depth+1)
        record=project.model_overrides[asset]['mesh_imports'][-1]
        self.assertEqual(record['recipe']['animation_pose'],pose());self.assertEqual(read_source(project,record),content)
        self.assertEqual(project.read_model_replacement(asset,project.model_overrides[asset]),expected)
        after=deepcopy(project._document());project.undo();self.assertEqual(project._document(),before)
        project.redo();self.assertEqual(project._document(),after);project.save()
        with patch.object(ProjectService,'_model_source',side_effect=project._model_source):
            opened=ProjectService.open(project.root);self.assertEqual(opened._document(),after)
            self.assertEqual(opened.read_model_replacement(asset,opened.model_overrides[asset]),expected)
