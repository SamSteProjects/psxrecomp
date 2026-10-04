"""Opt-in opaque material RGB reaches native packets without material allocation."""
from copy import deepcopy
from pathlib import Path
import base64,json,shutil,subprocess,tomllib,unittest,zipfile
from unittest.mock import patch
from importer.core import ImportError,_pack_ranges,parse_scene_assets,decompress_lzs
from importer.disc_relocation_package import decode_relocation_package
from importer.model_pack_archive import _archive
from importer.model_primitives import inspect_model_primitives
from importer.model_mesh_append import decode_append_mesh
from sdk import model_mesh_append,model_mesh_batch
from sdk.project import ProjectError,ProjectService
from sdk.build import build_project
import test_model_mesh_append_colors as fixtures
from test_model_mesh_append import glb
from test_model_primitive_workflow import http_server


def material(doc,factor=(.5,.25,1,1)):
    doc['materials']=[dict(pbrMetallicRoughness=dict(baseColorFactor=list(factor)))]
    doc['meshes'][0]['primitives'][0]['material']=0


class MeshMaterialColorTests(unittest.TestCase):
    def fixture(self,flag=0x24):
        helper=fixtures.MeshAppendColorTests();self.addCleanup(helper.doCleanups)
        return helper.fixture(flag)

    def test_linear_multiply_defaults_and_unsupported_alpha(self):
        content=glb(material,colors=fixtures.COLORS)
        raw=decode_append_mesh(content);baked=decode_append_mesh(content,material_colors=True)
        self.assertNotIn('material_colors',raw)
        self.assertEqual(baked['triangle_colors'][0],[[.5,0,0,1],[0,0,1,1],[0,.25,0,1]])
        missing=decode_append_mesh(glb(material),material_colors=True)
        self.assertEqual(missing['triangle_colors'][0],[[.5,.25,1,1]]*3)
        for change in (lambda d:material(d,(.5,.25,1,.5)),
                lambda d:(material(d),d['materials'][0].update(alphaMode='BLEND')),
                lambda d:material(d,(True,1,1,1)),
                lambda d:(material(d),d['materials'][0].update(extensions={'KHR_materials_unlit':{}}))):
            with self.assertRaises(ImportError):decode_append_mesh(glb(change),material_colors=True)
        with self.assertRaises(ImportError):decode_append_mesh(glb(material,colors=[[1,1,1,.5]]*4),material_colors=True)
        p,asset,donor=self.fixture(0x18);source=model_mesh_append.source(p,asset,'a'*64)
        report=model_mesh_append.review(p,asset,glb(lambda d:material(d,(.25,.25,.25,1))),donor,source['effective_sha256'],'a'*64,material_colors=True)
        self.assertEqual(report['color_import']['values'],[[[137,137,137]]]*2)

    def test_atomic_batch_http_history_persistence_and_exact_build(self):
        p,asset,donor=self.fixture();self.enterContext(patch('sdk.model_mesh_batch.source_key',return_value='a'*64))
        source=model_mesh_append.source(p,asset,'a'*64)
        def sections(doc):
            material(doc);second=deepcopy(doc['meshes'][0]['primitives'][0]);second.pop('material')
            doc['meshes'][0]['primitives'].append(second)
        content=glb(sections,colors=fixtures.COLORS)
        mappings=[dict(primitive_index=i,donor_face_id=donor,replace_group=False) for i in range(2)]
        args=(asset,content,mappings,source['effective_sha256'],'a'*64)
        before=deepcopy((p._document(),p.undo_stack,p.redo_stack))
        candidate,_,report=model_mesh_batch.prepare(p,*args,material_colors=True)
        expected=[[[64,0,0],[0,0,128],[0,32,0]],[[0,32,0],[0,0,128],[32,16,64]]]+fixtures.EXPECTED
        self.assertEqual([r['colors'] for r in inspect_model_primitives(candidate)['objects'][0]['primitives'][-4:]],expected)
        with http_server(p) as (_,post):
            body=dict(asset_id=asset,content_base64=base64.b64encode(content).decode(),mappings=mappings,expected_sha256=source['effective_sha256'],source_key='a'*64,material_colors=True)
            status,review=post('/api/model-mesh-batch-preview',body);self.assertEqual(status,200,review)
            self.assertEqual(review['review_key'],report['review_key'])
            for value in (False,1):
                status,_=post('/api/model-mesh-batch',dict(body,material_colors=value,review_key=report['review_key']));self.assertEqual(status,400)
                self.assertEqual((p._document(),p.undo_stack,p.redo_stack),before)
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
const {source,report}=JSON.parse(input);decodeMeshBatchReview(report,source,report.glb_sha256,report.mappings,true);
assert.throws(()=>decodeMeshBatchReview(report,source,report.glb_sha256,report.mappings,false));
for(const mutate of [r=>r.steps[0].review.material_colors=false,r=>r.steps[0].review.geometry.material_factors[0].base_color_factor[0]=.7,r=>r.steps[0].review.geometry.material_factors[0].base_color_factor[3]=.5,r=>r.steps[1].review.geometry.material_factors[0].primitive_index=0]){const bad=structuredClone(report);mutate(bad);assert.throws(()=>decodeMeshBatchReview(bad,source,report.glb_sha256,report.mappings,true));}"""
        result=subprocess.run([shutil.which('node'),'--input-type=module','-e',script],input=json.dumps(dict(source=source,report=report)),text=True,capture_output=True,cwd=Path(__file__).resolve().parents[3])
        self.assertEqual(result.returncode,0,result.stderr)

    def test_lit_review_binds_choice_even_when_native_bytes_match(self):
        p,asset,donor=self.fixture(0x14);source=model_mesh_append.source(p,asset,'a'*64)
        args=(p,asset,glb(material),donor,source['effective_sha256'],'a'*64)
        plain=model_mesh_append.review(*args);baked=model_mesh_append.review(*args,material_colors=True)
        self.assertEqual(plain['proposed_sha256'],baked['proposed_sha256'])
        self.assertNotEqual(plain['review_key'],baked['review_key'])
        self.assertEqual(baked['color_import']['imported_face_count'],0)
        with self.assertRaises(ProjectError):p.apply_model_mesh_append(*args[1:],baked['review_key'])
        with http_server(p) as (_,post):
            body=dict(asset_id=asset,content_base64=base64.b64encode(args[2]).decode(),donor_face_id=donor,expected_sha256=source['effective_sha256'],source_key='a'*64,material_colors=True)
            status,report=post('/api/model-mesh-append-preview',body);self.assertEqual(status,200,report)
            self.assertEqual(report['review_key'],baked['review_key'])
            status,_=post('/api/model-mesh-append',dict(body,material_colors=False,review_key=report['review_key']));self.assertEqual(status,400)
            status,_=post('/api/model-mesh-append-preview',dict(body,material_colors=1));self.assertEqual(status,400)
