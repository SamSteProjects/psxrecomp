"""Appended mesh UVs use an explicit Current native texture region."""
from copy import deepcopy
from pathlib import Path
import json,shutil,subprocess,tomllib,unittest,zipfile
from unittest.mock import patch
from importer.core import _pack_ranges,parse_scene_assets,decompress_lzs
from importer.disc_relocation_package import decode_relocation_package
from importer.model_pack_archive import _archive
from importer.model_primitives import inspect_model_primitives
from sdk import model_mesh_append,model_face_addition
from sdk.project import ProjectError,ProjectService
from sdk.build import build_project
import test_model_mesh_append_normals as fixtures
from test_model_mesh_append import glb

UVS=[[0,0],[1,0],[0,1],[1,1]]
EXPECTED=[[[10,200],[10,240],[50,200]],[[50,200],[10,240],[50,240]]]


class MeshAppendUVTests(unittest.TestCase):
    def fixture(self,flag=0x14):
        helper=fixtures.MeshAppendNormalTests();self.addCleanup(helper.doCleanups)
        return helper.fixture(flag)

    def test_normals_and_UVs_share_history_save_open_and_exact_build(self):
        p,asset,donor=self.fixture();source=model_face_addition.source(p,asset,'a'*64)
        before=p.read_model_replacement(asset,p.model_overrides[asset]);content=glb(normals=fixtures.NORMALS,uvs=UVS)
        state=deepcopy((p.model_overrides,p.undo_stack,p.redo_stack))
        report=model_mesh_append.review(p,asset,content,donor,source['effective_sha256'],'a'*64)
        self.assertEqual((p.model_overrides,p.undo_stack,p.redo_stack),state)
        self.assertEqual(report['uv_import'],dict(region=dict(origin=[10,200],width=41,height=41,clut=291,tpage=65),values=EXPECTED,imported_face_count=2,uv_max_error=.5))
        self.assertEqual(report['geometry']['ignored_attributes'],[])
        p.apply_model_mesh_append(asset,content,donor,source['effective_sha256'],'a'*64,report['review_key'])
        final=p.read_model_replacement(asset,p.model_overrides[asset]);rows=inspect_model_primitives(final,include_normal_references=True)['objects'][0]['primitives']
        self.assertEqual([row['uvs'] for row in rows[-2:]],EXPECTED)
        self.assertEqual([row['normal_indices'] for row in rows[-2:]],report['normal_import']['references'])
        self.assertTrue(all(row['material']==rows[0]['material'] for row in rows[-2:]));self.assertEqual(len(p.undo_stack),len(state[1])+1)
        p.undo();self.assertEqual(p.read_model_replacement(asset,p.model_overrides[asset]),before)
        p.redo();self.assertEqual(p.read_model_replacement(asset,p.model_overrides[asset]),final)
        p.save();saved=deepcopy(p.model_overrides[asset])
        with patch.object(ProjectService,'_model_source',side_effect=p._model_source):
            reopened=ProjectService.open(p.root);self.assertEqual(reopened.read_model_replacement(asset,saved),final)
        out=build_project(p)
        with zipfile.ZipFile(out['path']) as package:
            manifest=tomllib.loads(package.read('manifest.toml').decode());entry=manifest['disc_relocation'][0]
            replacement=decode_relocation_package(package.read(entry['file']),entry['sha256'])['replacement']
        archive=_archive(replacement);carrier=archive.read_entry(archive.entry(1))
        d=parse_scene_assets(carrier,1).descriptors[1];pack,_=decompress_lzs(carrier[d.data_offset:],d.size)
        start,_=_pack_ranges(pack)[0];self.assertEqual(pack[start:start+len(final)],final)

    def test_missing_untextured_and_wrapped_UV_ownership(self):
        p,asset,donor=self.fixture();source=model_face_addition.source(p,asset,'a'*64)
        content=glb(lambda d:d['meshes'][0]['primitives'].append(dict(attributes={'POSITION':0},indices=1)),uvs=UVS)
        report=model_mesh_append.review(p,asset,content,donor,source['effective_sha256'],'a'*64)
        self.assertEqual(report['uv_import']['values'],EXPECTED+[None,None])
        self.assertEqual(report['uv_import']['imported_face_count'],2)
        self.assertTrue(all('uvs' not in row['fields'] for row in report['additions'][-2:]))
        state=deepcopy((p.model_overrides,p.undo_stack,p.redo_stack));files=set((p.root/'Authored'/'Models').iterdir())
        for edge in (-.01,1.01):
            with self.assertRaisesRegex(ProjectError,'wrapping'):model_mesh_append.review(p,asset,glb(uvs=[[edge,0]]+UVS[1:]),donor,source['effective_sha256'],'a'*64)
            self.assertEqual((p.model_overrides,p.undo_stack,p.redo_stack),state);self.assertEqual(set((p.root/'Authored'/'Models').iterdir()),files)
        p,asset,donor=self.fixture(0x18);source=model_face_addition.source(p,asset,'a'*64)
        report=model_mesh_append.review(p,asset,glb(uvs=UVS),donor,source['effective_sha256'],'a'*64)
        self.assertEqual(report['uv_import'],dict(region=None,values=[None,None],imported_face_count=0,uv_max_error=0))
        self.assertEqual(report['geometry']['ignored_attributes'],['TEXCOORD_0'])

    def test_actual_UV_reviews_qualify_browser_and_reject_changed_bindings(self):
        node=shutil.which('node')
        if not node:self.skipTest('Node unavailable')
        reports=[]
        for flag in (0x14,0x18):
            p,asset,donor=self.fixture(flag);source=model_face_addition.source(p,asset,'a'*64)
            report=model_mesh_append.review(p,asset,glb(uvs=UVS,normals=fixtures.NORMALS),donor,source['effective_sha256'],'a'*64)
            reports.append(dict(source=source,report=report,donor=donor))
        script="""import {decodeMeshAppendReview} from './integrations/legaia/editor/model-mesh-append.js';
import assert from 'node:assert/strict';let input='';for await(const chunk of process.stdin)input+=chunk;
for(const {source,report,donor} of JSON.parse(input)){
 const hash=report.geometry.glb_sha256;decodeMeshAppendReview(report,source,donor,hash);
 const mutations=[r=>r.uv_import.imported_face_count++,r=>r.uv_import.uv_max_error++,r=>r.geometry.triangle_uvs[0][0][0]=NaN];
 if(report.uv_import.region)mutations.push(r=>r.uv_import.region.clut++,r=>r.uv_import.region.width++,r=>r.additions[0].fields.uvs[0][0]++,r=>r.preview.triangle_uvs.at(-1)[0][0]++);
 for(const mutate of mutations){const bad=structuredClone(report);mutate(bad);assert.throws(()=>decodeMeshAppendReview(bad,source,donor,hash));}
}
"""
        result=subprocess.run([node,'--input-type=module','-e',script],input=json.dumps(reports),text=True,capture_output=True,cwd=Path(__file__).resolve().parents[3])
        self.assertEqual(result.returncode,0,result.stderr)


if __name__=='__main__':unittest.main()
