"""Native mesh origin is post-conversion, reviewed and replayable through Build."""
from copy import deepcopy
from pathlib import Path
import base64,json,shutil,subprocess,tomllib,unittest,zipfile
from unittest.mock import patch
from importer.core import ImportError,_pack_ranges,parse_scene_assets,decompress_lzs
from importer.disc_relocation_package import decode_relocation_package
from importer.model_pack_archive import _archive
from importer.model_mesh_append import decode_append_mesh,inspect_append_mesh
from sdk import model_mesh_append,model_mesh_batch
from sdk.project import ProjectService
from sdk.build import build_project
from sdk.scene_preview import preview_shape_instances
import test_model_mesh_append as fixtures
import test_model_mesh_scene_preview as scene_fixtures
from test_model_primitive_workflow import http_server

OFFSET=[120.25,50.5,-30]

class MeshOriginTests(unittest.TestCase):
    def fixture(self):
        helper=fixtures.MeshAppendTests();self.addCleanup(helper.doCleanups)
        p,asset,donor=helper.fixture();self.enterContext(patch('sdk.model_mesh_batch.source_key',return_value='a'*64))
        return p,asset,donor

    def test_post_transform_reflection_scale_rounding_and_invalid_origins(self):
        def hierarchy(doc):
            doc['nodes'][0]['translation']=[100,20,30]
            doc['nodes'].append(dict(children=[0],translation=[20,10,0],scale=[2,1,1]));doc['scenes'][0]['nodes']=[1]
        content=fixtures.glb(hierarchy,positions=[[.25,0,0],[100,0,0],[0,100,0],[100,100,0]],normals=[[0,1,0]]*4,uvs=[[0,0],[1,0],[0,1],[1,1]])
        base=decode_append_mesh(content,source_scale=.5)
        moved=decode_append_mesh(content,source_scale=.5,source_offset=[10.25,20.5,-30])
        self.assertEqual(moved['vertices'][0],[120,6,-15]);self.assertEqual(moved['vertex_max_error'],.5)
        for field in ('triangles','triangle_normals','triangle_uvs','node_sources'):self.assertEqual(moved[field],base[field])
        self.assertEqual(decode_append_mesh(content,source_scale=.5,source_offset=[0,0,0]),base)
        self.assertEqual(inspect_append_mesh(content,source_scale=.5,source_offset=OFFSET)['source_offset'],OFFSET)
        wide=fixtures.glb(positions=[[0,0,0],[40000,0,0],[0,40000,0],[40000,40000,0]])
        with self.assertRaises(ImportError):decode_append_mesh(wide)
        self.assertEqual(decode_append_mesh(wide,source_offset=[-10000,10000,0])['vertices'][2],[30000,10000,0])
        for offset in (None,True,'xyz',[],[0,0],[0,0,0,0],[True,0,0],[float('nan'),0,0],[float('inf'),0,0],[32768,0,0],[-32769,0,0]):
            with self.assertRaises(ImportError):decode_append_mesh(content,source_offset=offset)

    def test_atomic_mapped_http_native_build_and_editor_choice_guards(self):
        p,asset,donor=self.fixture();source=model_mesh_append.source(p,asset,'a'*64)
        content=fixtures.glb(lambda d:d['meshes'][0]['primitives'].append(deepcopy(d['meshes'][0]['primitives'][0])))
        mappings=[dict(primitive_index=i,donor_face_id=donor,replace_group=False) for i in range(2)]
        args=(asset,content,mappings,source['effective_sha256'],'a'*64)
        candidate,_,report=model_mesh_batch.prepare(p,*args,source_scale=.5,source_offset=OFFSET)
        self.assertEqual(report['source_offset'],OFFSET)
        self.assertEqual(report['steps'][0]['review']['geometry']['vertices'][2],[170,50,-30])
        before=deepcopy((p._document(),p.undo_stack,p.redo_stack))
        body=dict(asset_id=asset,content_base64=base64.b64encode(content).decode(),mappings=mappings,expected_sha256=source['effective_sha256'],source_key='a'*64,source_scale=.5,source_offset=OFFSET)
        with http_server(p) as (_,post):
            status,review=post('/api/model-mesh-batch-preview',body);self.assertEqual(status,200,review)
            for offset in ([0,0,0],[120.25,50.5,-31],None,[True,0,0],[0,0],[-32769,0,0]):
                self.assertEqual(post('/api/model-mesh-batch',{**body,'source_offset':offset,'review_key':review['review_key']})[0],400)
                self.assertEqual((p._document(),p.undo_stack,p.redo_stack),before)
            self.assertEqual(post('/api/model-mesh-batch',{**body,'review_key':review['review_key']})[0],200)
        self.assertEqual(len(p.undo_stack),len(before[1])+1);p.undo();self.assertEqual(p._document(),before[0]);p.redo();p.save()
        with patch.object(ProjectService,'_model_source',side_effect=p._model_source):
            reopened=ProjectService.open(p.root);self.assertEqual(reopened.read_model_replacement(asset,reopened.model_overrides[asset]),candidate)
        out=build_project(p)
        with zipfile.ZipFile(out['path']) as z:
            entry=tomllib.loads(z.read('manifest.toml').decode())['disc_relocation'][0];archive=_archive(decode_relocation_package(z.read(entry['file']),entry['sha256'])['replacement'])
        carrier=archive.read_entry(archive.entry(1));d=parse_scene_assets(carrier,1).descriptors[1]
        pack,_=decompress_lzs(carrier[d.data_offset:],d.size);start,_=_pack_ranges(pack)[0]
        self.assertEqual(pack[start:start+len(candidate)],candidate)
        script="""import {decodeMeshBatchReview} from './integrations/legaia/editor/model-mesh-batch.js';import assert from 'node:assert/strict';let input='';for await(const c of process.stdin)input+=c;
const {source,report,offset}=JSON.parse(input);const check=r=>decodeMeshBatchReview(r,source,r.glb_sha256,r.mappings,false,null,0,.5,false,offset);check(report);
for(const mutate of [r=>r.source_offset=[0,0,0],r=>r.inventory.source_offset=null,r=>r.steps[0].review.source_offset=[0,0,0],r=>r.steps[1].review.geometry.source_offset=[120.25,-50.5,-30]]){const r=structuredClone(report);mutate(r);assert.throws(()=>check(r));}assert.throws(()=>decodeMeshBatchReview(report,source,report.glb_sha256,report.mappings,false,null,0,.5));"""
        r=subprocess.run([shutil.which('node'),'--input-type=module','-e',script],input=json.dumps(dict(source=source,report=report,offset=OFFSET)),text=True,capture_output=True,cwd=Path(__file__).resolve().parents[3]);self.assertEqual(r.returncode,0,r.stderr)

    def test_identical_native_candidates_still_bind_requested_origin(self):
        p,asset,donor=self.fixture();source=model_mesh_append.source(p,asset,'a'*64);content=fixtures.glb();args=(p,asset,content,donor,source['effective_sha256'],'a'*64)
        zero=model_mesh_append.review(*args);small=model_mesh_append.review(*args,source_offset=[.001,0,0])
        self.assertEqual(zero['proposed_sha256'],small['proposed_sha256']);self.assertNotEqual(zero['review_key'],small['review_key'])
        with http_server(p) as (_,post):
            body=dict(asset_id=asset,content_base64=base64.b64encode(content).decode(),donor_face_id=donor,expected_sha256=source['effective_sha256'],source_key='a'*64,source_offset=[.001,0,0])
            status,report=post('/api/model-mesh-append-preview',body);self.assertEqual(status,200,report)
            self.assertEqual(post('/api/model-mesh-append',{**body,'source_offset':[0,0,0],'review_key':report['review_key']})[0],400)
            self.assertEqual(post('/api/model-mesh-append',{**body,'review_key':report['review_key']})[0],200)

    def test_scene_review_composes_pose_and_binds_origin(self):
        helper=scene_fixtures.MeshScenePreviewTests();self.addCleanup(helper.doCleanups)
        p,asset,donor,content,scene=helper.fixture();source=model_mesh_append.source(p,asset,'a'*64)
        candidate,binding,report=model_mesh_append.prepare(p,asset,content,donor,source['effective_sha256'],'a'*64,new_group=True,replace_object=True,source_offset=OFFSET)
        body=dict(asset_id=asset,content_base64=base64.b64encode(content).decode(),donor_face_id=donor,expected_sha256=source['effective_sha256'],source_key='a'*64,new_group=True,replace_object=True,source_offset=OFFSET,review_key=report['review_key'],proposed_sha256=report['proposed_sha256'],entity_id='one',all_instances=True)
        before=deepcopy((p._document(),p.undo_stack,p.redo_stack,scene))
        with http_server(p) as (server,post),patch.dict(p.assets.records,{asset:dict(id=asset)}),patch('sdk.scene_preview.source_key',return_value='a'*64),patch.object(server.scene_previews,'preview',return_value=scene),patch.object(server,'model_preview',side_effect=lambda asset,**kw:kw['prepared']):
            status,posed=post('/api/model-mesh-append-scene-preview',body);self.assertEqual(status,200,posed)
            self.assertEqual(posed['proposal_assets'],preview_shape_instances(scene,asset,candidate,binding)['proposal_assets'])
            self.assertEqual(post('/api/model-mesh-append-scene-preview',{**body,'source_offset':[0,0,0]})[0],400)
        self.assertEqual((p._document(),p.undo_stack,p.redo_stack,scene),before)

if __name__=='__main__':unittest.main()
