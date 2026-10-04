"""Standard mesh normals allocate native rows with exact packet ownership."""
from copy import deepcopy
from hashlib import sha256
from pathlib import Path
import json,shutil,subprocess,struct,unittest,tomllib,zipfile
from unittest.mock import patch
from importer.model_primitives import inspect_model_primitives
from sdk import model_mesh_append,model_face_addition
from sdk.project import ProjectError,ProjectService
from sdk.build import build_project
from importer.core import _pack_ranges,parse_scene_assets,decompress_lzs
from importer.disc_relocation_package import decode_relocation_package
from importer.model_pack_archive import _archive
from test_model_primitives import synthetic
import test_model_mesh_append as fixtures

NORMALS=[[0,1,0],[1,0,0],[0,0,1],[0,1,0]]


class MeshAppendNormalTests(unittest.TestCase):
    def fixture(self,flag):
        helper=fixtures.MeshAppendTests();self.addCleanup(helper.doCleanups)
        def native(groups,count=2):return synthetic(((flag,),) if groups==((0x20,),) else groups,count=count)
        with patch('test_model_pack_growth.synthetic',side_effect=native):return helper.fixture()

    def test_gouraud_normals_use_new_rows_and_survive_one_step_history(self):
        p,asset,donor=self.fixture(0x14);source=model_face_addition.source(p,asset,'a'*64)
        original=inspect_model_primitives(p._model_source(asset),include_normal_references=True)['objects'][0]
        content=fixtures.glb(normals=NORMALS)
        report=model_mesh_append.review(p,asset,content,donor,source['effective_sha256'],'a'*64)
        n=original['normal_count'];metadata=report['normal_import']
        self.assertEqual(metadata,dict(mode='gouraud',first_normal_index=n,vectors=[[0,-4096,0],[0,0,4096],[4096,0,0]],references=[[n,n+1,n+2],[n+2,n+1,n]],imported_face_count=2))
        self.assertEqual(report['topology']['allocated_vector_count'],7)
        before=p.read_model_replacement(asset,p.model_overrides[asset]);history=len(p.undo_stack)
        p.apply_model_mesh_append(asset,content,donor,source['effective_sha256'],'a'*64,report['review_key'])
        final=p.read_model_replacement(asset,p.model_overrides[asset]);rows=inspect_model_primitives(final,include_normal_references=True)['objects'][0]
        self.assertEqual(rows['normal_count'],n+3)
        self.assertEqual([row['normal_indices'] for row in rows['primitives'][-2:]],metadata['references'])
        pointer=12+struct.unpack_from('<I',final,20)[0]
        actual=[list(struct.unpack_from('<3h',final,pointer+(n+i)*8)) for i in range(3)]
        self.assertEqual(actual,metadata['vectors']);self.assertEqual(len(p.undo_stack),history+1)
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


    def test_flat_mixed_and_unlit_ownership(self):
        p,asset,donor=self.fixture(0x10);source=model_face_addition.source(p,asset,'a'*64)
        state=deepcopy((p.model_overrides,p.undo_stack,p.redo_stack));files=set((p.root/'Authored'/'Models').iterdir())
        with self.assertRaisesRegex(ProjectError,'Flat triangle donor'):model_mesh_append.review(p,asset,fixtures.glb(normals=NORMALS),donor,source['effective_sha256'],'a'*64)
        self.assertEqual((p.model_overrides,p.undo_stack,p.redo_stack),state);self.assertEqual(set((p.root/'Authored'/'Models').iterdir()),files)
        report=model_mesh_append.review(p,asset,fixtures.glb(normals=[[0,2,0]]*4),donor,source['effective_sha256'],'a'*64)
        self.assertEqual(report['normal_import']['mode'],'flat');self.assertEqual(report['normal_import']['vectors'],[[0,-4096,0]])
        n=source['objects'][0]['normal_count'];self.assertEqual(report['normal_import']['references'],[[n],[n]])
        p,asset,donor=self.fixture(0x14);source=model_face_addition.source(p,asset,'a'*64)
        content=fixtures.glb(lambda d:d['meshes'][0]['primitives'].append(dict(attributes={'POSITION':0},indices=1)),normals=NORMALS)
        report=model_mesh_append.review(p,asset,content,donor,source['effective_sha256'],'a'*64)
        self.assertEqual(report['normal_import']['references'][-2:],[None,None]);self.assertEqual(report['normal_import']['imported_face_count'],2)
        self.assertTrue(all('normal_indices' not in row['fields'] for row in report['additions'][-2:]))
        p,asset,donor=self.fixture(0x20);source=model_face_addition.source(p,asset,'a'*64)
        report=model_mesh_append.review(p,asset,fixtures.glb(normals=NORMALS),donor,source['effective_sha256'],'a'*64)
        self.assertEqual(report['normal_import']['mode'],'inherited');self.assertEqual(report['normal_import']['vectors'],[])
        self.assertEqual(report['geometry']['ignored_attributes'],['NORMAL']);self.assertEqual(len(report['allocations']),1)

    def test_actual_normal_reviews_qualify_browser_with_tamper_rejection(self):
        node=shutil.which('node')
        if not node:self.skipTest('Node unavailable')
        fixtures_json=[]
        for flag,normals in ((0x14,NORMALS),(0x10,[[0,1,0]]*4),(0x20,NORMALS)):
            p,asset,donor=self.fixture(flag);source=model_face_addition.source(p,asset,'a'*64)
            report=model_mesh_append.review(p,asset,fixtures.glb(normals=normals),donor,source['effective_sha256'],'a'*64)
            fixtures_json.append(dict(source=source,report=report,donor=donor))
        script="""import {decodeMeshAppendReview} from './integrations/legaia/editor/model-mesh-append.js';
import assert from 'node:assert/strict';let input='';for await(const chunk of process.stdin)input+=chunk;
for(const {source,report,donor} of JSON.parse(input)){
 const hash=report.geometry.glb_sha256;decodeMeshAppendReview(report,source,donor,hash);
 const mutations=[r=>r.geometry.triangle_normals[0][0]=[0,0,0],r=>r.normal_import.first_normal_index++,r=>r.normal_import.imported_face_count++,r=>r.normal_import.mode='other'];
 if(report.normal_import.vectors.length)mutations.push(r=>r.normal_import.vectors[0][0]++,r=>r.additions[0].fields.normal_indices[0]++);
 for(const mutate of mutations){const bad=structuredClone(report);mutate(bad);assert.throws(()=>decodeMeshAppendReview(bad,source,donor,hash));}
}
"""
        result=subprocess.run([node,'--input-type=module','-e',script],input=json.dumps(fixtures_json),text=True,capture_output=True,cwd=Path(__file__).resolve().parents[3])
        self.assertEqual(result.returncode,0,result.stderr)


if __name__=='__main__':unittest.main()
