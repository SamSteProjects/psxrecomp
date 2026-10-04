"""Selected normalized source UV channels reach exact native texture packets."""
from copy import deepcopy
from pathlib import Path
import base64,json,shutil,struct,subprocess,tomllib,unittest,zipfile
from unittest.mock import patch
from importer.animation_glb import _read_glb
from importer.core import ImportError,_pack_ranges,parse_scene_assets,decompress_lzs
from importer.disc_relocation_package import decode_relocation_package
from importer.model_pack_archive import _archive
from importer.model_mesh_append import decode_append_mesh,inspect_append_mesh
from importer.model_primitives import inspect_model_primitives
from sdk import model_mesh_append,model_mesh_batch
from sdk.project import ProjectService,ProjectError
from sdk.build import build_project
import test_model_mesh_append_uvs as fixtures
from test_model_mesh_append import glb
from test_model_primitive_workflow import http_server

EXPECTED=[[[50,240],[50,200],[10,240]],[[10,240],[50,200],[10,200]]]


def uv_sets(*,sections=False,missing=False,same=False,normalized_zero=False):
    doc,binary=_read_glb(glb(uvs=fixtures.UVS));binary=bytearray(binary)
    primitive=doc['meshes'][0]['primitives'][0]
    if same:primitive['attributes']['TEXCOORD_1']=primitive['attributes']['TEXCOORD_0']
    else:
        offset=len(binary);binary.extend(struct.pack('<8H',65535,65535,0,65535,65535,0,0,0))
        view=len(doc['bufferViews']);doc['bufferViews'].append(dict(buffer=0,byteOffset=offset,byteLength=16))
        accessor=len(doc['accessors']);doc['accessors'].append(dict(bufferView=view,componentType=5123,normalized=True,count=4,type='VEC2'))
        primitive['attributes']['TEXCOORD_1']=accessor
    if normalized_zero:
        primitive['attributes']['TEXCOORD_0']=primitive['attributes'].pop('TEXCOORD_1')
    if sections:
        second=deepcopy(primitive)
        if missing:second['attributes'].pop('TEXCOORD_1')
        doc['meshes'][0]['primitives'].append(second)
    doc['buffers'][0]['byteLength']=len(binary)
    encoded=json.dumps(doc,separators=(',',':')).encode();encoded+=b' '*(-len(encoded)%4)
    return struct.pack('<3I',0x46546c67,2,28+len(encoded)+len(binary))+struct.pack('<2I',len(encoded),0x4e4f534a)+encoded+struct.pack('<2I',len(binary),0x004e4942)+binary


class MeshUVSetTests(unittest.TestCase):
    def fixture(self,flag=0x14):
        helper=fixtures.MeshAppendUVTests();self.addCleanup(helper.doCleanups)
        return helper.fixture(flag)

    def test_normalized_channel_inventory_and_selected_native_build(self):
        content=uv_sets();inventory=inspect_append_mesh(content)
        self.assertEqual(inventory['uv_sets'],[[0,1]])
        geometry=decode_append_mesh(content,uv_set=1)
        self.assertEqual(geometry['triangle_uvs'][0],[[1,1],[1,0],[0,1]])
        self.assertEqual(decode_append_mesh(uv_sets(normalized_zero=True))['triangle_uvs'],geometry['triangle_uvs'])
        self.assertEqual(geometry['ignored_attributes'],['TEXCOORD_0'])
        for value in (True,-1,8,'1'):
            with self.assertRaises(ImportError):decode_append_mesh(content,uv_set=value)
        p,asset,donor=self.fixture();source=model_mesh_append.source(p,asset,'a'*64)
        args=(asset,content,donor,source['effective_sha256'],'a'*64)
        report=model_mesh_append.review(p,*args,uv_set=1)
        self.assertEqual(report['uv_import']['values'],EXPECTED)
        p.apply_model_mesh_append(*args,report['review_key'],uv_set=1)
        candidate=p.read_model_replacement(asset,p.model_overrides[asset])
        self.assertEqual([row['uvs'] for row in inspect_model_primitives(candidate)['objects'][0]['primitives'][-2:]],EXPECTED)
        p.save()
        with patch.object(ProjectService,'_model_source',side_effect=p._model_source):
            reopened=ProjectService.open(p.root);self.assertEqual(reopened.read_model_replacement(asset,reopened.model_overrides[asset]),candidate)
        out=build_project(p)
        with zipfile.ZipFile(out['path']) as package:
            entry=tomllib.loads(package.read('manifest.toml').decode())['disc_relocation'][0]
            archive=_archive(decode_relocation_package(package.read(entry['file']),entry['sha256'])['replacement'])
        carrier=archive.read_entry(archive.entry(1));descriptor=parse_scene_assets(carrier,1).descriptors[1]
        pack,_=decompress_lzs(carrier[descriptor.data_offset:],descriptor.size);start,_=_pack_ranges(pack)[0]
        self.assertEqual(pack[start:start+len(candidate)],candidate)

    def test_atomic_batch_http_missing_channel_history_and_browser_dto(self):
        p,asset,donor=self.fixture();self.enterContext(patch('sdk.model_mesh_batch.source_key',return_value='a'*64))
        source=model_mesh_append.source(p,asset,'a'*64);content=uv_sets(sections=True,missing=True)
        mappings=[dict(primitive_index=i,donor_face_id=donor,replace_group=False) for i in range(2)]
        args=(asset,content,mappings,source['effective_sha256'],'a'*64)
        candidate,_,report=model_mesh_batch.prepare(p,*args,uv_set=1)
        zero=model_mesh_batch.review(p,*args)
        self.assertEqual(report['steps'][0]['review']['uv_import']['values'],EXPECTED)
        self.assertEqual(report['steps'][1]['review']['uv_import']['imported_face_count'],0)
        before=deepcopy((p._document(),p.undo_stack,p.redo_stack))
        with http_server(p) as (_,post):
            body=dict(asset_id=asset,content_base64=base64.b64encode(content).decode(),mappings=mappings,expected_sha256=source['effective_sha256'],source_key='a'*64,uv_set=1)
            status,value=post('/api/model-mesh-batch-preview',body);self.assertEqual(status,200,value)
            for choice in (0,True):
                status,_=post('/api/model-mesh-batch',dict(body,uv_set=choice,review_key=report['review_key']));self.assertEqual(status,400)
                self.assertEqual((p._document(),p.undo_stack,p.redo_stack),before)
            status,value=post('/api/model-mesh-batch',dict(body,review_key=report['review_key']));self.assertEqual(status,200,value)
        self.assertEqual(len(p.undo_stack),len(before[1])+1);self.assertEqual(p.read_model_replacement(asset,p.model_overrides[asset]),candidate)
        p.undo();self.assertEqual(p._document(),before[0]);p.redo()
        script="""import {decodeMeshBatchReview} from './integrations/legaia/editor/model-mesh-batch.js';
import assert from 'node:assert/strict';let input='';for await(const c of process.stdin)input+=c;
const {source,report,zero}=JSON.parse(input);decodeMeshBatchReview(zero,source,zero.glb_sha256,zero.mappings);decodeMeshBatchReview(report,source,report.glb_sha256,report.mappings,false,null,1);
for(const mutate of [r=>r.uv_set=0,r=>r.steps[0].review.geometry.uv_set=0,r=>r.steps[1].review.geometry.uv_sources[0].sets=[0,1],r=>r.steps[0].review.geometry.ignored_attributes=[],r=>r.inventory.uv_sets[0]=[1],r=>r.inventory.uv_sets[1]=[0,1]]){const bad=structuredClone(report);mutate(bad);assert.throws(()=>decodeMeshBatchReview(bad,source,report.glb_sha256,report.mappings,false,null,1));}"""
        result=subprocess.run([shutil.which('node'),'--input-type=module','-e',script],input=json.dumps(dict(source=source,report=report,zero=zero)),text=True,capture_output=True,cwd=Path(__file__).resolve().parents[3])
        self.assertEqual(result.returncode,0,result.stderr)

    def test_identical_and_untextured_choices_bind_review(self):
        for flag in (0x14,0x18):
            p,asset,donor=self.fixture(flag);source=model_mesh_append.source(p,asset,'a'*64)
            args=(p,asset,uv_sets(same=True),donor,source['effective_sha256'],'a'*64)
            zero=model_mesh_append.review(*args);one=model_mesh_append.review(*args,uv_set=1)
            self.assertEqual(zero['proposed_sha256'],one['proposed_sha256']);self.assertNotEqual(zero['review_key'],one['review_key'])
            with self.assertRaises(ProjectError):p.apply_model_mesh_append(*args[1:],one['review_key'])
