"""Selected GLB scene ownership survives the complete native model workflow."""
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


def scenes(doc):
    doc['nodes'].append(dict(mesh=0,translation=[300,40,10]))
    doc['scenes']=[dict(name='Original',nodes=[0]),dict(name='Offset',nodes=[1]),dict(name='Together',nodes=[1,0]),dict(name='Empty',nodes=[])]
    doc['scene']=1


class MeshSceneSelectionTests(unittest.TestCase):
    def fixture(self):
        helper=fixtures.MeshAppendTests();self.addCleanup(helper.doCleanups)
        return helper.fixture()

    def test_default_selected_shared_and_empty_scene_inventory(self):
        content=fixtures.glb(scenes)
        first=decode_append_mesh(content,scene_index=0);default=decode_append_mesh(content)
        self.assertEqual(default['scene_source']['scene_index'],1)
        self.assertEqual(default['vertices'][0],[300,-40,10]);self.assertEqual(first['vertices'][0],[0,0,0])
        together=decode_append_mesh(content,scene_index=2)
        self.assertEqual(len(together['triangles']),4)
        self.assertEqual([r['node_index'] for r in together['node_sources']],[1,0])
        self.assertEqual(together['glb_sha256'],default['glb_sha256'])
        empty=inspect_append_mesh(content,scene_index=3)
        self.assertEqual(empty['primitives'],[]);self.assertEqual(empty['triangle_count'],0)
        with self.assertRaises(ImportError):decode_append_mesh(content,scene_index=3)
        for selected in (True,-1,4,'1'):
            with self.assertRaises(ImportError):decode_append_mesh(content,scene_index=selected)
        for change in (lambda d:d.update(scene=True),lambda d:d['scenes'][0].update(nodes=[[0]]),lambda d:d['scenes'][0].update(name='bad\nname')):
            def mutate(doc):scenes(doc);change(doc)
            with self.assertRaises(ImportError):inspect_append_mesh(fixtures.glb(mutate))

    def test_batch_http_source_choice_history_persistence_and_exact_build(self):
        p,asset,donor=self.fixture();self.enterContext(patch('sdk.model_mesh_batch.source_key',return_value='a'*64))
        source=model_mesh_append.source(p,asset,'a'*64);content=fixtures.glb(scenes)
        mappings=[dict(primitive_index=i,donor_face_id=donor,replace_group=False) for i in range(2)]
        args=(asset,content,mappings,source['effective_sha256'],'a'*64)
        before=deepcopy((p._document(),p.undo_stack,p.redo_stack))
        candidate,_,report=model_mesh_batch.prepare(p,*args,scene_index=2)
        self.assertEqual([step['review']['selected_scene_index'] for step in report['steps']],[2,2])
        with http_server(p) as (_,post):
            body=dict(asset_id=asset,content_base64=base64.b64encode(content).decode(),mappings=mappings,expected_sha256=source['effective_sha256'],source_key='a'*64,scene_index=2)
            status,review=post('/api/model-mesh-batch-preview',body);self.assertEqual(status,200,review)
            for index in (0,True):
                status,_=post('/api/model-mesh-batch',dict(body,scene_index=index,review_key=report['review_key']));self.assertEqual(status,400)
                self.assertEqual((p._document(),p.undo_stack,p.redo_stack),before)
            status,empty=post('/api/model-mesh-file',dict(content_base64=body['content_base64'],scene_index=3));self.assertEqual(status,200,empty)
            self.assertEqual(empty['primitives'],[])
            status,result=post('/api/model-mesh-batch',dict(body,review_key=report['review_key']));self.assertEqual(status,200,result)
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
const {source,report}=JSON.parse(input);decodeMeshBatchReview(report,source,report.glb_sha256,report.mappings,false,2);
for(const mutate of [r=>r.selected_scene_index=1,r=>r.steps[0].review.selected_scene_index=1,r=>r.steps[1].review.geometry.scene_source.scene_index=1,r=>r.inventory.scene_source.scenes[0].roots=[true]]){const bad=structuredClone(report);mutate(bad);assert.throws(()=>decodeMeshBatchReview(bad,source,report.glb_sha256,report.mappings,false,2));}"""
        result=subprocess.run([shutil.which('node'),'--input-type=module','-e',script],input=json.dumps(dict(source=source,report=report)),text=True,capture_output=True,cwd=Path(__file__).resolve().parents[3])
        self.assertEqual(result.returncode,0,result.stderr)

    def test_identical_scene_candidates_still_have_distinct_review_keys(self):
        def identical(doc):doc['scenes']=[dict(nodes=[0]),dict(nodes=[0])]
        p,asset,donor=self.fixture();source=model_mesh_append.source(p,asset,'a'*64)
        args=(p,asset,fixtures.glb(identical),donor,source['effective_sha256'],'a'*64)
        one=model_mesh_append.review(*args,scene_index=0);two=model_mesh_append.review(*args,scene_index=1)
        self.assertEqual(one['proposed_sha256'],two['proposed_sha256']);self.assertNotEqual(one['review_key'],two['review_key'])
        with http_server(p) as (_,post):
            body=dict(asset_id=asset,content_base64=base64.b64encode(args[2]).decode(),donor_face_id=donor,expected_sha256=source['effective_sha256'],source_key='a'*64,scene_index=0)
            status,report=post('/api/model-mesh-append-preview',body);self.assertEqual(status,200,report)
            status,_=post('/api/model-mesh-append',dict(body,scene_index=1,review_key=report['review_key']));self.assertEqual(status,400)
