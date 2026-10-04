"""GLB colors preserve native modulation/display domains and packet ownership."""
from copy import deepcopy
from pathlib import Path
import json,shutil,subprocess,tomllib,unittest,zipfile
from unittest.mock import patch
from importer.core import ImportError,_pack_ranges,parse_scene_assets,decompress_lzs
from importer.disc_relocation_package import decode_relocation_package
from importer.model_pack_archive import _archive
from importer.model_primitives import inspect_model_primitives
from importer.model_mesh_append import decode_append_mesh
from importer.model_glb import _Accessors
from importer.animation_glb import _read_glb
from sdk import model_mesh_append,model_face_addition
from sdk.project import ProjectError,ProjectService
from sdk.build import build_project
import test_model_mesh_append_normals as fixtures
from test_model_mesh_append_uvs import UVS
from test_model_mesh_append import glb

COLORS=[[1,0,0,1],[0,1,0,1],[0,0,1,1],[.5,.5,.5,1]]
EXPECTED=[[[128,0,0],[0,0,128],[0,128,0]],[[0,128,0],[0,0,128],[64,64,64]]]


class MeshAppendColorTests(unittest.TestCase):
    def fixture(self,flag=0x24):
        helper=fixtures.MeshAppendNormalTests();self.addCleanup(helper.doCleanups)
        return helper.fixture(flag)

    def test_imported_baked_colors_UVs_one_step_history_and_normal_build(self):
        p,asset,donor=self.fixture();source=model_face_addition.source(p,asset,'a'*64)
        before=p.read_model_replacement(asset,p.model_overrides[asset]);content=glb(uvs=UVS,colors=COLORS)
        state=deepcopy((p.model_overrides,p.undo_stack,p.redo_stack))
        report=model_mesh_append.review(p,asset,content,donor,source['effective_sha256'],'a'*64)
        self.assertEqual((p.model_overrides,p.undo_stack,p.redo_stack),state)
        self.assertEqual(report['color_import'],dict(mode='textured_modulation',values=EXPECTED,imported_face_count=2,color_max_error=0))
        p.apply_model_mesh_append(asset,content,donor,source['effective_sha256'],'a'*64,report['review_key'])
        final=p.read_model_replacement(asset,p.model_overrides[asset]);rows=inspect_model_primitives(final,include_normal_references=True)['objects'][0]['primitives']
        self.assertEqual([row['colors'] for row in rows[-2:]],EXPECTED)
        self.assertEqual([row['uvs'] for row in rows[-2:]],report['uv_import']['values'])
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

    def test_flat_untextured_lit_missing_and_alpha_contracts(self):
        p,asset,donor=self.fixture(0x18);source=model_face_addition.source(p,asset,'a'*64)
        gray=[[.5,.5,.5,1]]*4;content=glb(colors=gray)
        report=model_mesh_append.review(p,asset,content,donor,source['effective_sha256'],'a'*64)
        self.assertEqual(report['color_import']['mode'],'untextured_srgb');self.assertEqual(report['color_import']['values'],[[[188,188,188]]]*2)
        state=deepcopy((p.model_overrides,p.undo_stack,p.redo_stack));files=set((p.root/'Authored'/'Models').iterdir())
        for colors,message in ((COLORS,'Flat triangle donor'),([[.5,.5,.5,.5]]*4,'alpha')):
            with self.assertRaisesRegex(ProjectError,message):model_mesh_append.review(p,asset,glb(colors=colors),donor,source['effective_sha256'],'a'*64)
            self.assertEqual((p.model_overrides,p.undo_stack,p.redo_stack),state);self.assertEqual(set((p.root/'Authored'/'Models').iterdir()),files)
        p,asset,donor=self.fixture(0x24);source=model_face_addition.source(p,asset,'a'*64)
        content=glb(lambda d:d['meshes'][0]['primitives'].append(dict(attributes={'POSITION':0},indices=1)),colors=COLORS)
        report=model_mesh_append.review(p,asset,content,donor,source['effective_sha256'],'a'*64)
        self.assertEqual(report['color_import']['values'],EXPECTED+[None,None]);self.assertEqual(report['color_import']['imported_face_count'],2)
        p,asset,donor=self.fixture(0x14);source=model_face_addition.source(p,asset,'a'*64)
        report=model_mesh_append.review(p,asset,glb(colors=COLORS),donor,source['effective_sha256'],'a'*64)
        self.assertEqual(report['color_import']['mode'],'inherited');self.assertEqual(report['color_import']['imported_face_count'],0)
        self.assertEqual(report['geometry']['ignored_attributes'],['COLOR_0'])

    def test_normalized_color_accessors_and_domain_rejection(self):
        for component,maximum in ((5121,255),(5123,65535)):
            content=glb(colors=[[maximum,0,0,maximum]]*4,color_component=component)
            geometry=decode_append_mesh(content)
            self.assertEqual(geometry['triangle_colors'],[[[1,0,0,1]]*3]*2)
            document,binary=_read_glb(content);reader=_Accessors(document,binary)
            self.assertEqual(reader.read(2,4,'color',normalized=True),[(1,0,0,1)]*4)
            with self.assertRaises(ImportError):reader.read(2,4,'legacy color')
            document['bufferViews'][2]['buffer']=False
            with self.assertRaises(ImportError):_Accessors(document,binary).read(2,4,'color',normalized=True)
            with self.assertRaises(ImportError):decode_append_mesh(glb(lambda d:d['accessors'][-1].update(normalized=False),colors=[[maximum,0,0,maximum]]*4,color_component=component))
        for value in (-.1,1.1):
            with self.assertRaises(ImportError):decode_append_mesh(glb(colors=[[value,0,0,1]]*4))

    def test_actual_baked_color_reviews_qualify_browser_with_tamper_rejection(self):
        node=shutil.which('node')
        if not node:self.skipTest('Node unavailable')
        reports=[]
        for flag,colors in ((0x24,COLORS),(0x18,[[.5,.5,.5,1]]*4),(0x14,COLORS)):
            p,asset,donor=self.fixture(flag);source=model_face_addition.source(p,asset,'a'*64)
            report=model_mesh_append.review(p,asset,glb(colors=colors),donor,source['effective_sha256'],'a'*64)
            reports.append(dict(source=source,report=report,donor=donor))
        script="""import {decodeMeshAppendReview} from './integrations/legaia/editor/model-mesh-append.js';
import assert from 'node:assert/strict';let input='';for await(const chunk of process.stdin)input+=chunk;
for(const {source,report,donor} of JSON.parse(input)){
 const hash=report.geometry.glb_sha256;decodeMeshAppendReview(report,source,donor,hash);
 const mutations=[r=>r.color_import.imported_face_count++,r=>r.color_import.color_max_error++,r=>r.color_import.mode='other',r=>r.geometry.triangle_colors[0][0][0]=NaN];
 if(report.color_import.imported_face_count)mutations.push(r=>r.additions[0].fields.colors[0][0]++,r=>r.preview.triangle_colors.at(-1)[0][0]++);
 for(const mutate of mutations){const bad=structuredClone(report);mutate(bad);assert.throws(()=>decodeMeshAppendReview(bad,source,donor,hash));}
}
"""
        result=subprocess.run([node,'--input-type=module','-e',script],input=json.dumps(reports),text=True,capture_output=True,cwd=Path(__file__).resolve().parents[3])
        self.assertEqual(result.returncode,0,result.stderr)


if __name__=='__main__':unittest.main()
