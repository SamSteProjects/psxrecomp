"""Sparse section selection retains source IDs and one native publication."""
from copy import deepcopy
from pathlib import Path
import base64,json,shutil,subprocess,tomllib,unittest,zipfile
from unittest.mock import patch
from importer.core import _pack_ranges,parse_scene_assets,decompress_lzs
from importer.disc_relocation_package import decode_relocation_package
from importer.model_pack_archive import _archive
from sdk import model_mesh_append,model_mesh_batch
from sdk.project import ProjectService,ProjectError
from sdk.build import build_project
import test_model_mesh_append as fixtures
from test_model_primitive_workflow import http_server


def sections(count):
    def mutate(doc):
        primitive=doc['meshes'][0]['primitives'][0]
        doc['meshes'][0]['primitives']=[deepcopy(primitive) for _ in range(count)]
    return fixtures.glb(mutate)


class MeshBatchSelectionTests(unittest.TestCase):
    def fixture(self):
        helper=fixtures.MeshAppendTests();self.addCleanup(helper.doCleanups)
        p,asset,donor=helper.fixture()
        self.enterContext(patch('sdk.model_mesh_batch.source_key',return_value='a'*64))
        return p,asset,donor

    def test_sparse_mapping_http_history_persistence_and_exact_build(self):
        p,asset,donor=self.fixture();source=model_mesh_append.source(p,asset,'a'*64);content=sections(4)
        mappings=[dict(primitive_index=i,donor_face_id=donor,replace_group=False) for i in (0,2)]
        before=deepcopy((p._document(),p.undo_stack,p.redo_stack))
        files=set((p.root/'Authored'/'Models').iterdir())
        candidate,_,report=model_mesh_batch.prepare(p,asset,content,mappings,source['effective_sha256'],'a'*64)
        self.assertEqual(report['selected_primitive_indices'],[0,2])
        self.assertEqual(report['skipped_primitive_indices'],[1,3])
        self.assertEqual([step['review']['selected_primitive_index'] for step in report['steps']],[0,2])
        self.assertEqual(sum(len(step['review']['additions']) for step in report['steps']),4)
        self.assertEqual((p._document(),p.undo_stack,p.redo_stack),before)
        self.assertEqual(set((p.root/'Authored'/'Models').iterdir()),files)
        with http_server(p) as (_,post):
            body=dict(asset_id=asset,content_base64=base64.b64encode(content).decode(),mappings=mappings,
                      expected_sha256=source['effective_sha256'],source_key='a'*64)
            status,review=post('/api/model-mesh-batch-preview',body);self.assertEqual(status,200,review)
            changed=deepcopy(mappings);changed[1]['primitive_index']=1
            other_candidate,_,other=model_mesh_batch.prepare(p,asset,content,changed,source['effective_sha256'],'a'*64)
            self.assertEqual(other_candidate,candidate)
            self.assertNotEqual(other['review_key'],review['review_key'])
            status,_=post('/api/model-mesh-batch',dict(body,mappings=changed,review_key=review['review_key']))
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
const {source,report}=JSON.parse(input);decodeMeshBatchReview(report,source,report.glb_sha256,report.mappings);
for(const mutate of [r=>r.selected_primitive_indices=[0,1],r=>r.skipped_primitive_indices=[1],r=>r.steps[1].review.selected_primitive_index=1,r=>r.mappings.reverse(),r=>r.mappings[1].primitive_index=0]){const bad=structuredClone(report);mutate(bad);assert.throws(()=>decodeMeshBatchReview(bad,source,report.glb_sha256,report.mappings));}"""
        result=subprocess.run([shutil.which('node'),'--input-type=module','-e',script],input=json.dumps(dict(source=source,report=report)),text=True,capture_output=True,cwd=Path(__file__).resolve().parents[3])
        self.assertEqual(result.returncode,0,result.stderr)

    def test_larger_inventory_can_select_one_section_and_invalid_subsets_are_read_only(self):
        p,asset,donor=self.fixture();source=model_mesh_append.source(p,asset,'a'*64);content=sections(17)
        mapping=lambda i:dict(primitive_index=i,donor_face_id=donor,replace_group=False)
        args=(source['effective_sha256'],'a'*64)
        before=deepcopy((p._document(),p.undo_stack,p.redo_stack))
        candidate,_,report=model_mesh_batch.prepare(p,asset,content,[mapping(16)],*args)
        single=model_mesh_append.prepare(p,asset,content,donor,*args,new_group=True,primitive_index=16)[0]
        self.assertEqual(candidate,single)
        self.assertEqual(report['selected_primitive_indices'],[16])
        self.assertEqual(report['skipped_primitive_indices'],list(range(16)))
        for mappings in ([],[mapping(True)],[mapping(-1)],[mapping(17)],
                         [mapping(1),mapping(1)],[mapping(2),mapping(0)],
                         [mapping(i) for i in range(17)]):
            with self.assertRaises(ProjectError):model_mesh_batch.prepare(p,asset,content,mappings,*args)
            self.assertEqual((p._document(),p.undo_stack,p.redo_stack),before)
