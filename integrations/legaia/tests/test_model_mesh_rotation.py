"""Static native import orientation composes positions, normals and Build ownership."""
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

class MeshRotationTests(unittest.TestCase):
    def fixture(self):
        helper=fixtures.MeshAppendTests();self.addCleanup(helper.doCleanups)
        p,asset,donor=helper.fixture();self.enterContext(patch('sdk.model_mesh_batch.source_key',return_value='a'*64))
        self.enterContext(patch('sdk.model_face_removal.source_key',return_value='a'*64))
        return p,asset,donor

    def test_native_axes_composition_node_scale_offset_normals_and_limits(self):
        content=fixtures.glb(normals=[[0,1,0]]*4,uvs=[[0,0],[1,0],[0,1],[1,1]])
        base=decode_append_mesh(content)
        for rotation,first,second,normal in [([90,0,0],[0,0,-100],[100,0,0],[0,0,-4096]),([0,90,0],[0,-100,0],[0,0,-100],[0,-4096,0]),([0,0,90],[100,0,0],[0,100,0],[4096,0,0]),([90,90,90],[0,-100,0],[0,0,-100],[0,-4096,0])]:
            r=decode_append_mesh(content,source_rotation=rotation)
            self.assertEqual(r['vertices'][1],first);self.assertEqual(r['vertices'][2],second)
            self.assertEqual(r['triangle_normals'],[[normal]*3]*2)
            for field in ('triangles','triangle_uvs'):self.assertEqual(r[field],base[field])
        def hierarchy(doc):
            doc['nodes'][0]['translation']=[100,20,30]
            doc['nodes'].append(dict(children=[0],translation=[20,10,0],scale=[2,1,1]));doc['scenes'][0]['nodes']=[1]
        content=fixtures.glb(hierarchy,positions=[[.25,0,0],[100,0,0],[0,100,0],[100,100,0]],normals=[[0,1,0]]*4)
        r=decode_append_mesh(content,source_scale=.5,source_offset=[10.25,20.5,30],source_rotation=[90,0,0])
        self.assertEqual(r['vertices'][0],[120,6,15]);self.assertEqual(r['vertex_max_error'],.5)
        self.assertEqual(r['triangle_normals'],[[[0,0,-4096]]*3]*2)
        self.assertEqual(inspect_append_mesh(content,source_rotation=[90,0,0])['source_rotation'],[90,0,0])
        for rotation in (None,True,'90',[],[0,0],[0,0,0,0],[True,0,0],[float('nan'),0,0],[float('inf'),0,0],[361,0,0],[-361,0,0],[10**400,0,0]):
            with self.assertRaises(ImportError):decode_append_mesh(content,source_rotation=rotation)
        with self.assertRaises(ImportError):decode_append_mesh(content,source_offset=[10**400,0,0])
        with self.assertRaises(ImportError):decode_append_mesh(content,source_scale=10**400)
        large=fixtures.glb(positions=[[0,0,0],[32767,0,0],[0,-32767,0],[32767,-32767,0]])
        with self.assertRaises(ImportError):decode_append_mesh(large,source_rotation=[0,0,45])
        self.assertEqual(decode_append_mesh(fixtures.glb(),source_rotation=[0,0,0]),decode_append_mesh(fixtures.glb()))

    def test_mapped_replacement_http_editor_guards_history_and_native_build(self):
        p,asset,donor=self.fixture();source=model_mesh_append.source(p,asset,'a'*64)
        content=fixtures.glb(lambda d:d['meshes'][0]['primitives'].append(deepcopy(d['meshes'][0]['primitives'][0])),normals=[[0,1,0]]*4)
        mappings=[dict(primitive_index=i,donor_face_id=donor,replace_group=False) for i in range(2)]
        rotation=[90,0,0];offset=[120,50,-30];args=(asset,content,mappings,source['effective_sha256'],'a'*64)
        candidate,_,report=model_mesh_batch.prepare(p,*args,source_rotation=rotation,source_offset=offset,replace_objects=True)
        self.assertEqual(report['source_rotation'],rotation);self.assertEqual(report['steps'][0]['review']['geometry']['vertices'][1],[120,50,-130])
        before=deepcopy((p._document(),p.undo_stack,p.redo_stack))
        body=dict(asset_id=asset,content_base64=base64.b64encode(content).decode(),mappings=mappings,expected_sha256=source['effective_sha256'],source_key='a'*64,source_rotation=rotation,source_offset=offset,replace_objects=True)
        with http_server(p) as (_,post):
            status,review=post('/api/model-mesh-batch-preview',body);self.assertEqual(status,200,review)
            for value in ([0,0,0],[90,1,0],None,[True,0,0],[0,0],[361,0,0],[10**400,0,0]):
                self.assertEqual(post('/api/model-mesh-batch',{**body,'source_rotation':value,'review_key':review['review_key']})[0],400)
                self.assertEqual((p._document(),p.undo_stack,p.redo_stack),before)
            self.assertEqual(post('/api/model-mesh-batch',{**body,'review_key':review['review_key']})[0],200)
        p.undo();self.assertEqual(p._document(),before[0]);p.redo();p.save()
        self.assertEqual(len(p.undo_stack),len(before[1])+1)
        with patch.object(ProjectService,'_model_source',side_effect=p._model_source):
            reopened=ProjectService.open(p.root);self.assertEqual(reopened.read_model_replacement(asset,reopened.model_overrides[asset]),candidate)
        out=build_project(p)
        with zipfile.ZipFile(out['path']) as z:
            entry=tomllib.loads(z.read('manifest.toml').decode())['disc_relocation'][0];archive=_archive(decode_relocation_package(z.read(entry['file']),entry['sha256'])['replacement'])
        carrier=archive.read_entry(archive.entry(1));d=parse_scene_assets(carrier,1).descriptors[1]
        pack,_=decompress_lzs(carrier[d.data_offset:],d.size);start,_=_pack_ranges(pack)[0];self.assertEqual(pack[start:start+len(candidate)],candidate)
        script="""import {decodeMeshBatchReview} from './integrations/legaia/editor/model-mesh-batch.js';import assert from 'node:assert/strict';let input='';for await(const c of process.stdin)input+=c;
const {source,report,offset,rotation}=JSON.parse(input);const check=r=>decodeMeshBatchReview(r,source,r.glb_sha256,r.mappings,false,null,0,1,true,offset,rotation);check(report);
for(const mutate of [r=>r.source_rotation=[0,0,0],r=>r.inventory.source_rotation=null,r=>r.steps[0].review.source_rotation=[0,0,0],r=>r.steps[1].review.geometry.source_rotation=[-90,0,0]]){const r=structuredClone(report);mutate(r);assert.throws(()=>check(r));}assert.throws(()=>decodeMeshBatchReview(report,source,report.glb_sha256,report.mappings,false,null,0,1,true,offset));"""
        result=subprocess.run([shutil.which('node'),'--input-type=module','-e',script],input=json.dumps(dict(source=source,report=report,offset=offset,rotation=rotation)),text=True,capture_output=True,cwd=Path(__file__).resolve().parents[3]);self.assertEqual(result.returncode,0,result.stderr)

    def test_full_turn_keeps_identical_candidate_but_distinct_review_key(self):
        p,asset,donor=self.fixture();source=model_mesh_append.source(p,asset,'a'*64);content=fixtures.glb(normals=[[0,1,0]]*4);args=(p,asset,content,donor,source['effective_sha256'],'a'*64)
        zero=model_mesh_append.review(*args);full=model_mesh_append.review(*args,source_rotation=[360,0,0])
        self.assertEqual(zero['proposed_sha256'],full['proposed_sha256']);self.assertNotEqual(zero['review_key'],full['review_key'])
        with http_server(p) as (_,post):
            body=dict(asset_id=asset,content_base64=base64.b64encode(content).decode(),donor_face_id=donor,expected_sha256=source['effective_sha256'],source_key='a'*64,source_rotation=[360,0,0])
            self.assertEqual(post('/api/model-mesh-append',{**body,'source_rotation':[0,0,0],'review_key':full['review_key']})[0],400)
            self.assertEqual(post('/api/model-mesh-append',{**body,'review_key':full['review_key']})[0],200)

    def test_scene_review_rotation_and_pose_are_separate_and_read_only(self):
        helper=scene_fixtures.MeshScenePreviewTests();self.addCleanup(helper.doCleanups)
        p,asset,donor,content,scene=helper.fixture();source=model_mesh_append.source(p,asset,'a'*64)
        candidate,binding,report=model_mesh_append.prepare(p,asset,content,donor,source['effective_sha256'],'a'*64,new_group=True,replace_object=True,source_rotation=[0,90,0])
        body=dict(asset_id=asset,content_base64=base64.b64encode(content).decode(),donor_face_id=donor,expected_sha256=source['effective_sha256'],source_key='a'*64,new_group=True,replace_object=True,source_rotation=[0,90,0],review_key=report['review_key'],proposed_sha256=report['proposed_sha256'],entity_id='one',all_instances=True)
        before=deepcopy((p._document(),p.undo_stack,p.redo_stack,scene))
        with http_server(p) as (server,post),patch.dict(p.assets.records,{asset:dict(id=asset)}),patch('sdk.scene_preview.source_key',return_value='a'*64),patch.object(server.scene_previews,'preview',return_value=scene),patch.object(server,'model_preview',side_effect=lambda asset,**kw:kw['prepared']):
            status,posed=post('/api/model-mesh-append-scene-preview',body);self.assertEqual(status,200,posed)
            self.assertEqual(posed['proposal_assets'],preview_shape_instances(scene,asset,candidate,binding)['proposal_assets'])
            self.assertEqual(post('/api/model-mesh-append-scene-preview',{**body,'source_rotation':[0,0,0]})[0],400)
        self.assertEqual((p._document(),p.undo_stack,p.redo_stack,scene),before)

if __name__=='__main__':unittest.main()
