"""File inventory can exceed one append without increasing native write bounds."""
from copy import deepcopy
from pathlib import Path
import base64,json,shutil,subprocess,tomllib,unittest,zipfile
from unittest.mock import patch
from importer.core import ImportError,_pack_ranges,parse_scene_assets,decompress_lzs
from importer.disc_relocation_package import decode_relocation_package
from importer.model_pack_archive import _archive
from importer.model_mesh_append import inspect_append_mesh,decode_append_mesh
from sdk import model_mesh_append,model_mesh_batch
from sdk.project import ProjectService,ProjectError
from sdk.build import build_project
import test_model_mesh_append as fixtures
from test_model_primitive_workflow import http_server


def large():
    return fixtures.glb(lambda doc:doc['meshes'][0]['primitives'].append(deepcopy(doc['meshes'][0]['primitives'][0])),
                        indices=[0,1,2,1,3,2]*144)


class MeshLargeInventoryTests(unittest.TestCase):
    def test_inventory_is_independent_of_transaction_and_parses_once(self):
        content=large()
        from importer.model_mesh_append import _read_glb
        with patch('importer.model_mesh_append._read_glb',wraps=_read_glb) as parser:
            inventory=inspect_append_mesh(content)
        self.assertEqual(parser.call_count,1)
        self.assertEqual(inventory['triangle_count'],576)
        self.assertEqual([row['triangle_count'] for row in inventory['primitives']],[288,288])
        with self.assertRaises(ImportError):decode_append_mesh(content)
        self.assertEqual(len(decode_append_mesh(content,primitive_index=1)['triangles']),288)
        def invalid(doc):
            doc['meshes'][0]['primitives'].append(deepcopy(doc['meshes'][0]['primitives'][0]))
            doc['meshes'][0]['primitives'][1]['mode']=1
        with self.assertRaises(ImportError):inspect_append_mesh(fixtures.glb(invalid))

    def test_subset_http_history_save_open_build_and_browser_inventory(self):
        helper=fixtures.MeshAppendTests();self.addCleanup(helper.doCleanups)
        p,asset,donor=helper.fixture();self.enterContext(patch('sdk.model_mesh_batch.source_key',return_value='a'*64))
        source=model_mesh_append.source(p,asset,'a'*64);content=large()
        mapping=lambda i:dict(primitive_index=i,donor_face_id=donor,replace_group=False)
        before=deepcopy((p._document(),p.undo_stack,p.redo_stack))
        candidate,_,report=model_mesh_batch.prepare(p,asset,content,[mapping(1)],source['effective_sha256'],'a'*64)
        with self.assertRaisesRegex(ProjectError,'512-triangle'):
            model_mesh_batch.prepare(p,asset,content,[mapping(0),mapping(1)],source['effective_sha256'],'a'*64)
        with http_server(p) as (_,post):
            body=dict(asset_id=asset,content_base64=base64.b64encode(content).decode(),mappings=[mapping(1)],
                      expected_sha256=source['effective_sha256'],source_key='a'*64)
            status,inventory=post('/api/model-mesh-file',dict(content_base64=body['content_base64']))
            self.assertEqual(status,200,inventory);self.assertEqual(inventory['triangle_count'],576)
            status,_=post('/api/model-mesh-batch-preview',dict(body,mappings=[mapping(0),mapping(1)]))
            self.assertEqual(status,400);self.assertEqual((p._document(),p.undo_stack,p.redo_stack),before)
            status,review=post('/api/model-mesh-batch-preview',body);self.assertEqual(status,200,review)
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
import {decodeMeshFile} from './integrations/legaia/editor/model-mesh-append.js';
import assert from 'node:assert/strict';let input='';for await(const c of process.stdin)input+=c;
const {source,report}=JSON.parse(input);decodeMeshFile(report.inventory,report.glb_sha256);decodeMeshBatchReview(report,source,report.glb_sha256,report.mappings);
for(const mutate of [r=>r.inventory.triangle_count=65537,r=>r.inventory.triangle_count=128,r=>r.inventory.primitives[0].triangle_count=513]){const bad=structuredClone(report);mutate(bad);assert.throws(()=>decodeMeshBatchReview(bad,source,report.glb_sha256,report.mappings));}"""
        result=subprocess.run([shutil.which('node'),'--input-type=module','-e',script],input=json.dumps(dict(source=source,report=report)),text=True,capture_output=True,cwd=Path(__file__).resolve().parents[3])
        self.assertEqual(result.returncode,0,result.stderr)
