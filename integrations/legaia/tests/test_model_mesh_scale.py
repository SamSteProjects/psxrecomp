"""Explicit source units bind native mesh imports across Review and Build."""
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
import test_model_mesh_append as fixtures
from test_model_primitive_workflow import http_server


class MeshSourceScaleTests(unittest.TestCase):
    def test_scale_bakes_translations_before_rounding_and_preserves_normals_uvs(self):
        def hierarchy(doc):
            doc['nodes'][0]['translation']=[100,20,30]
            doc['nodes'].append(dict(children=[0],translation=[20,10,0],scale=[2,1,1]))
            doc['scenes'][0]['nodes']=[1]
        content=fixtures.glb(hierarchy,positions=[[.25,0,0],[100,0,0],[0,100,0],[100,100,0]],
                             normals=[[0,1,0]]*4,uvs=[[0,0],[1,0],[0,1],[1,1]])
        base=decode_append_mesh(content);scaled=decode_append_mesh(content,source_scale=.5)
        self.assertEqual(scaled['vertices'][0],[110,-15,15])
        self.assertEqual(scaled['triangle_normals'],base['triangle_normals'])
        self.assertEqual(scaled['triangle_uvs'],base['triangle_uvs'])
        self.assertEqual(scaled['node_sources'],base['node_sources'])
        self.assertEqual(scaled['triangles'],base['triangles'])
        self.assertEqual(inspect_append_mesh(content,source_scale=.5)['source_scale'],.5)
        self.assertNotIn('source_scale',base)
        self.assertEqual(decode_append_mesh(content,source_scale=1.0),base)
        large=fixtures.glb(positions=[[0,0,0],[40000,0,0],[0,40000,0],[40000,40000,0]])
        with self.assertRaises(ImportError):inspect_append_mesh(large)
        self.assertEqual(inspect_append_mesh(large,source_scale=.1)['triangle_count'],2)
        for scale in (True,None,'2',0,-1,1e-7,1e7,float('inf'),float('nan')):
            with self.assertRaises(ImportError):decode_append_mesh(content,source_scale=scale)
        with self.assertRaises(ImportError):decode_append_mesh(content,source_scale=1e-6)

    def test_http_scale_is_review_bound_and_atomic_build_reads_exact_native_bytes(self):
        helper=fixtures.MeshAppendTests();self.addCleanup(helper.doCleanups)
        p,asset,donor=helper.fixture();self.enterContext(patch('sdk.model_mesh_batch.source_key',return_value='a'*64))
        source=model_mesh_append.source(p,asset,'a'*64)
        content=fixtures.glb(lambda d:d['meshes'][0]['primitives'].append(deepcopy(d['meshes'][0]['primitives'][0])))
        mappings=[dict(primitive_index=i,donor_face_id=donor,replace_group=False) for i in range(2)]
        args=(asset,content,mappings,source['effective_sha256'],'a'*64)
        before=deepcopy((p._document(),p.undo_stack,p.redo_stack))
        candidate,_,report=model_mesh_batch.prepare(p,*args,source_scale=.5)
        self.assertEqual(report['source_scale'],.5)
        self.assertEqual(report['steps'][0]['review']['geometry']['vertices'][2],[50,0,0])
        with http_server(p) as (_,post):
            body=dict(asset_id=asset,content_base64=base64.b64encode(content).decode(),mappings=mappings,
                      expected_sha256=source['effective_sha256'],source_key='a'*64,source_scale=.5)
            status,review=post('/api/model-mesh-batch-preview',body);self.assertEqual(status,200,review)
            for scale in (1,True,None,0,-1,'0.5',1e7):
                status,_=post('/api/model-mesh-batch',dict(body,source_scale=scale,review_key=review['review_key']))
                self.assertEqual(status,400);self.assertEqual((p._document(),p.undo_stack,p.redo_stack),before)
            status,result=post('/api/model-mesh-batch',dict(body,review_key=review['review_key']))
            self.assertEqual(status,200,result)
        self.assertEqual(len(p.undo_stack),len(before[1])+1)
        p.undo();self.assertEqual(p._document(),before[0]);p.redo();p.save()
        with patch.object(ProjectService,'_model_source',side_effect=p._model_source):
            reopened=ProjectService.open(p.root)
            self.assertEqual(reopened.read_model_replacement(asset,reopened.model_overrides[asset]),candidate)
        out=build_project(p)
        with zipfile.ZipFile(out['path']) as package:
            entry=tomllib.loads(package.read('manifest.toml').decode())['disc_relocation'][0]
            archive=_archive(decode_relocation_package(package.read(entry['file']),entry['sha256'])['replacement'])
        carrier=archive.read_entry(archive.entry(1));descriptor=parse_scene_assets(carrier,1).descriptors[1]
        pack,_=decompress_lzs(carrier[descriptor.data_offset:],descriptor.size);start,_=_pack_ranges(pack)[0]
        self.assertEqual(pack[start:start+len(candidate)],candidate)
        script="""import {decodeMeshBatchReview} from './integrations/legaia/editor/model-mesh-batch.js';
import assert from 'node:assert/strict';let input='';for await(const c of process.stdin)input+=c;
const {source,report}=JSON.parse(input);decodeMeshBatchReview(report,source,report.glb_sha256,report.mappings,false,null,0,.5);
for(const mutate of [r=>r.source_scale=1,r=>r.inventory.source_scale=1,r=>r.steps[0].review.source_scale=true,r=>r.steps[1].review.geometry.source_scale=1]){const bad=structuredClone(report);mutate(bad);assert.throws(()=>decodeMeshBatchReview(bad,source,report.glb_sha256,report.mappings,false,null,0,.5));}"""
        result=subprocess.run([shutil.which('node'),'--input-type=module','-e',script],input=json.dumps(dict(source=source,report=report)),text=True,capture_output=True,cwd=Path(__file__).resolve().parents[3])
        self.assertEqual(result.returncode,0,result.stderr)

    def test_identical_rounded_candidate_keeps_distinct_scale_review_keys(self):
        helper=fixtures.MeshAppendTests();self.addCleanup(helper.doCleanups)
        p,asset,donor=helper.fixture();source=model_mesh_append.source(p,asset,'a'*64)
        args=(p,asset,fixtures.glb(),donor,source['effective_sha256'],'a'*64)
        one=model_mesh_append.review(*args,source_scale=1)
        two=model_mesh_append.review(*args,source_scale=1.001)
        self.assertEqual(one['proposed_sha256'],two['proposed_sha256'])
        self.assertNotEqual(one['review_key'],two['review_key'])
        with http_server(p) as (_,post):
            body=dict(asset_id=asset,donor_face_id=donor,content_base64=base64.b64encode(args[2]).decode(),
                      expected_sha256=source['effective_sha256'],source_key='a'*64,source_scale=1.001)
            status,report=post('/api/model-mesh-append-preview',body);self.assertEqual(status,200,report)
            status,_=post('/api/model-mesh-append',dict(body,source_scale=1,review_key=report['review_key']))
            self.assertEqual(status,400)
            status,result=post('/api/model-mesh-append',dict(body,review_key=report['review_key']))
            self.assertEqual(status,200,result)
