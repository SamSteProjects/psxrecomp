"""Per-section UV choices remain one atomic native donor mapping."""
from copy import deepcopy
from pathlib import Path
import base64,json,shutil,subprocess,tomllib,unittest,zipfile
from unittest.mock import patch
from importer.core import _pack_ranges,parse_scene_assets,decompress_lzs
from importer.disc_relocation_package import decode_relocation_package
from importer.model_pack_archive import _archive
from importer.model_primitives import inspect_model_primitives
from sdk import model_mesh_append,model_mesh_batch
from sdk.project import ProjectService,ProjectError
from sdk.build import build_project
import test_model_mesh_uv_sets as fixtures
import test_model_mesh_append_uvs as uv0
from test_model_primitive_workflow import http_server


class MeshBatchUVSetTests(unittest.TestCase):
    def fixture(self):
        helper=fixtures.MeshUVSetTests();self.addCleanup(helper.doCleanups)
        p,asset,donor=helper.fixture();self.enterContext(patch('sdk.model_mesh_batch.source_key',return_value='a'*64))
        return p,asset,donor

    def test_mixed_channels_http_atomic_history_save_and_exact_build(self):
        p,asset,donor=self.fixture();source=model_mesh_append.source(p,asset,'a'*64)
        content=fixtures.uv_sets(sections=True)
        mappings=[dict(primitive_index=i,donor_face_id=donor,replace_group=False,uv_set=channel) for i,channel in enumerate((1,0))]
        args=(asset,content,mappings,source['effective_sha256'],'a'*64)
        candidate,_,report=model_mesh_batch.prepare(p,*args)
        self.assertEqual([step['review'].get('uv_set',0) for step in report['steps']],[1,0])
        self.assertEqual([row['uvs'] for row in inspect_model_primitives(candidate)['objects'][0]['primitives'][-4:]],fixtures.EXPECTED+uv0.EXPECTED)
        before=deepcopy((p._document(),p.undo_stack,p.redo_stack))
        with http_server(p) as (_,post):
            body=dict(asset_id=asset,content_base64=base64.b64encode(content).decode(),mappings=mappings,expected_sha256=source['effective_sha256'],source_key='a'*64)
            status,value=post('/api/model-mesh-batch-preview',body);self.assertEqual(status,200,value)
            changed=deepcopy(mappings);changed[1]['uv_set']=1
            status,_=post('/api/model-mesh-batch',dict(body,mappings=changed,review_key=report['review_key']));self.assertEqual(status,400)
            self.assertEqual((p._document(),p.undo_stack,p.redo_stack),before)
            status,value=post('/api/model-mesh-batch',dict(body,review_key=report['review_key']));self.assertEqual(status,200,value)
        self.assertEqual(len(p.undo_stack),len(before[1])+1)
        p.undo();self.assertEqual(p._document(),before[0]);p.redo();p.save()
        with patch.object(ProjectService,'_model_source',side_effect=p._model_source):
            reopened=ProjectService.open(p.root);self.assertEqual(reopened.read_model_replacement(asset,reopened.model_overrides[asset]),candidate)
        out=build_project(p)
        with zipfile.ZipFile(out['path']) as package:
            entry=tomllib.loads(package.read('manifest.toml').decode())['disc_relocation'][0]
            archive=_archive(decode_relocation_package(package.read(entry['file']),entry['sha256'])['replacement'])
        carrier=archive.read_entry(archive.entry(1));descriptor=parse_scene_assets(carrier,1).descriptors[1]
        pack,_=decompress_lzs(carrier[descriptor.data_offset:],descriptor.size);start,_=_pack_ranges(pack)[0]
        self.assertEqual(pack[start:start+len(candidate)],candidate)
        script="""import {decodeMeshBatchReview} from './integrations/legaia/editor/model-mesh-batch.js';
import assert from 'node:assert/strict';let input='';for await(const c of process.stdin)input+=c;
const {source,report}=JSON.parse(input);decodeMeshBatchReview(report,source,report.glb_sha256,report.mappings);
for(const mutate of [r=>r.steps[0].review.uv_set=0,r=>r.steps[1].review.uv_set=1,r=>r.mappings[0].uv_set=true]){const bad=structuredClone(report);mutate(bad);assert.throws(()=>decodeMeshBatchReview(bad,source,report.glb_sha256,report.mappings));}
const bad=structuredClone(report);bad.mappings[0].uv_set=null;assert.throws(()=>decodeMeshBatchReview(bad,source,report.glb_sha256,bad.mappings));"""
        result=subprocess.run([shutil.which('node'),'--input-type=module','-e',script],input=json.dumps(dict(source=source,report=report)),text=True,capture_output=True,cwd=Path(__file__).resolve().parents[3])
        self.assertEqual(result.returncode,0,result.stderr)

    def test_invalid_choices_read_only_and_identical_native_bytes_bind_mapping(self):
        p,asset,donor=self.fixture();source=model_mesh_append.source(p,asset,'a'*64)
        content=fixtures.uv_sets(sections=True,same=True)
        mappings=[dict(primitive_index=i,donor_face_id=donor,replace_group=False,uv_set=channel) for i,channel in enumerate((1,0))]
        args=(asset,content,mappings,source['effective_sha256'],'a'*64)
        report=model_mesh_batch.review(p,*args);changed=deepcopy(mappings);changed[1]['uv_set']=1
        other=model_mesh_batch.review(p,asset,content,changed,source['effective_sha256'],'a'*64)
        self.assertEqual(report['proposed_sha256'],other['proposed_sha256']);self.assertNotEqual(report['review_key'],other['review_key'])
        before=deepcopy((p._document(),p.undo_stack,p.redo_stack));files=set((p.root/'Authored'/'Models').iterdir())
        for choice in (True,None,-1,8,'1'):
            bad=deepcopy(mappings);bad[1]['uv_set']=choice
            with self.assertRaises(ProjectError):model_mesh_batch.review(p,asset,content,bad,source['effective_sha256'],'a'*64)
        with self.assertRaises(ProjectError):model_mesh_batch.review(p,*args,uv_set=True)
        with self.assertRaises(ProjectError):model_mesh_batch.apply(p,asset,content,changed,source['effective_sha256'],'a'*64,review_key=report['review_key'])
        self.assertEqual((p._document(),p.undo_stack,p.redo_stack),before)
        self.assertEqual(set((p.root/'Authored'/'Models').iterdir()),files)
