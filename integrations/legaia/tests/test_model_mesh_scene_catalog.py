"""Geometry-independent scene selection recovers unsupported default scenes."""
from copy import deepcopy
from pathlib import Path
import base64,json,shutil,subprocess,unittest
from importer.core import ImportError
from importer.model_mesh_scene import inspect_source_scenes
from importer.model_mesh_append import inspect_append_mesh
from sdk import model_mesh_append
import test_model_mesh_append as fixtures
from test_model_primitive_workflow import http_server


def unsupported_default(doc):
    doc['nodes'][0]['scale']=[0,1,1]
    doc['nodes'].append(dict(mesh=0,translation=[100,20,30]))
    doc['scenes']=[dict(name='Zero scale',nodes=[0]),dict(name='Usable',nodes=[1])]


class MeshSceneCatalogTests(unittest.TestCase):
    def test_catalog_lists_source_scenes_without_geometry_claims(self):
        content=fixtures.glb(unsupported_default);catalog=inspect_source_scenes(content)
        self.assertFalse(catalog['geometry_qualified']);self.assertTrue(catalog['read_only'])
        self.assertEqual([row['name'] for row in catalog['scene_source']['scenes']],['Zero scale','Usable'])
        with self.assertRaises(ImportError):inspect_append_mesh(content)
        usable=inspect_append_mesh(content,scene_index=1)
        self.assertEqual(usable['glb_sha256'],catalog['glb_sha256'])
        script="""import {decodeMeshSceneCatalog} from './integrations/legaia/editor/model-mesh-append.js';
import assert from 'node:assert/strict';let input='';for await(const c of process.stdin)input+=c;
const catalog=JSON.parse(input);decodeMeshSceneCatalog(catalog,catalog.glb_sha256);
for(const mutate of [v=>v.geometry_qualified=true,v=>v.read_only=false,v=>v.glb_sha256='0'.repeat(64),v=>v.scene_source.scenes[0].roots=[true],v=>v.scene_source.scene_index=3]){const bad=structuredClone(catalog);mutate(bad);assert.throws(()=>decodeMeshSceneCatalog(bad,catalog.glb_sha256));}"""
        result=subprocess.run([shutil.which('node'),'--input-type=module','-e',script],input=json.dumps(catalog),text=True,capture_output=True,cwd=Path(__file__).resolve().parents[3])
        self.assertEqual(result.returncode,0,result.stderr)

    def test_http_catalog_is_read_only_and_usable_scene_still_qualifies_apply(self):
        helper=fixtures.MeshAppendTests();self.addCleanup(helper.doCleanups)
        p,asset,donor=helper.fixture();source=model_mesh_append.source(p,asset,'a'*64)
        content=fixtures.glb(unsupported_default);body=dict(content_base64=base64.b64encode(content).decode())
        before=deepcopy((p._document(),p.undo_stack,p.redo_stack));files=set((p.root/'Authored'/'Models').iterdir())
        with http_server(p) as (_,post):
            status,catalog=post('/api/model-mesh-scenes',body);self.assertEqual(status,200,catalog)
            self.assertFalse(catalog['geometry_qualified'])
            status,_=post('/api/model-mesh-scenes',dict(body,scene_index=1));self.assertEqual(status,400)
            status,_=post('/api/model-mesh-file',body);self.assertEqual(status,400)
            status,inventory=post('/api/model-mesh-file',dict(body,scene_index=1));self.assertEqual(status,200,inventory)
            self.assertEqual((p._document(),p.undo_stack,p.redo_stack),before)
            self.assertEqual(set((p.root/'Authored'/'Models').iterdir()),files)
            request=dict(body,asset_id=asset,donor_face_id=donor,expected_sha256=source['effective_sha256'],source_key='a'*64,scene_index=1)
            status,review=post('/api/model-mesh-append-preview',request);self.assertEqual(status,200,review)
            self.assertEqual(review['geometry']['vertices'][0],[100,-20,30])
            status,result=post('/api/model-mesh-append',dict(request,review_key=review['review_key']));self.assertEqual(status,200,result)
        self.assertEqual(len(p.undo_stack),len(before[1])+1)
        p.undo();self.assertEqual(p._document(),before[0])
