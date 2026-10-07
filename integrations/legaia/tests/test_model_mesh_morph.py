"""Saved morph shapes: independent native geometry, ownership and refusals."""
from copy import deepcopy
import json,struct,subprocess,unittest
from importer.animation_glb import _read_glb
from importer.model_glb import _write_glb
from importer.model_mesh_append import decode_append_mesh,inspect_append_mesh
from importer.core import ImportError
from sdk import model_mesh_append,model_face_addition
from test_model_mesh_append import glb
import test_model_mesh_append as mesh_fixtures
import test_model_mesh_append_normals as normal_fixtures
from test_model_mesh_skin import skin_glb


def morph_glb(change=None,skin=False):
    doc,binary=_read_glb(skin_glb(normals=[[1,1,0]]*4) if skin else glb(normals=[[1,1,0]]*4));binary=bytearray(binary)
    def add(rows,width=3):
        binary.extend(b'\0'*(-len(binary)%4));start=len(binary)
        for row in rows:binary.extend(struct.pack('<'+str(width)+'f',*row))
        view=len(doc['bufferViews']);doc['bufferViews'].append(dict(buffer=0,byteOffset=start,byteLength=len(binary)-start))
        index=len(doc['accessors']);doc['accessors'].append(dict(bufferView=view,componentType=5126,count=len(rows),type='VEC'+str(width)))
        return index
    primitive=doc['meshes'][0]['primitives'][0]
    primitive['targets']=[dict(POSITION=add([[4,8,0]]*4),NORMAL=add([[-1,1,0]]*4)),dict(POSITION=add([[0,4,0]]*4),NORMAL=add([[0,0,2]]*4))]
    doc['meshes'][0]['weights']=[.5,-.25]
    if change:change(doc,binary,add)
    return _write_glb(doc,binary)


class StaticMorphTests(unittest.TestCase):
    def test_literal_pose_node_mesh_zero_weights_and_transform_order(self):
        r=decode_append_mesh(morph_glb());self.assertEqual(r['vertices'],[[2,-3,0],[2,-103,0],[102,-3,0],[102,-103,0]])
        self.assertEqual(r['node_sources'][0]['morph_bake'],dict(target_count=2,weight_source='mesh',weights=[.5,-.25]))
        override=morph_glb(lambda d,b,a:d['nodes'][0].update(weights=[1,0]))
        self.assertEqual(decode_append_mesh(override)['vertices'][0],[4,-8,0]);self.assertEqual(inspect_append_mesh(override)['node_sources'][0]['morph_bake']['weight_source'],'node')
        zero=morph_glb(lambda d,b,a:d['meshes'][0].pop('weights'))
        self.assertEqual(decode_append_mesh(zero)['vertices'][0],[0,0,0]);self.assertEqual(inspect_append_mesh(zero)['node_sources'][0]['morph_bake']['weight_source'],'zero')
        scaled=morph_glb(lambda d,b,a:d['nodes'][0].update(scale=[2,3,1],translation=[5,7,0]))
        literal=glb(positions=[[9,16,0],[209,16,0],[9,316,0],[209,316,0]],normals=[[.25,.5,-.5]]*4)
        actual=decode_append_mesh(scaled);expected=decode_append_mesh(literal)
        for key in ('vertices','triangles','triangle_normals'):self.assertEqual(actual[key],expected[key])

    def test_morph_before_skin_and_shared_base_distinct_targets(self):
        r=decode_append_mesh(morph_glb(skin=True));self.assertEqual(r['vertices'],[[7,-9,0],[10,-164,0],[213,-20,0],[216,-226,0]])
        literal=glb(positions=[[7,8.75,0],[213,20.25,0],[10,164.5,0],[216,226,0]],normals=[[.25,1.2,-.5],[.25,6/7,-.5],[.25,1,-.5],[.25,.75,-.5]])
        self.assertEqual(r['triangle_normals'],decode_append_mesh(literal)['triangle_normals'])
        def second(d,b,add):
            primitive=deepcopy(d['meshes'][0]['primitives'][0]);primitive['targets'][0]['POSITION']=add([[40,8,0]]*4);d['meshes'][0]['primitives'].append(primitive)
        r=decode_append_mesh(morph_glb(second));self.assertEqual(r['vertices'][4:],[[20,-3,0],[20,-103,0],[120,-3,0],[120,-103,0]])
        self.assertEqual(r['triangles'],[[0,1,2],[2,1,3],[4,5,6],[6,5,7]])

    def test_tangent_qualification_and_missing_target_components(self):
        def tangent(d,b,add):
            p=d['meshes'][0]['primitives'][0];p['attributes']['TANGENT']=add([[1,0,0,1]]*4,4);p['targets'][0]['TANGENT']=add([[0,1,0]]*4);p['targets'][1].pop('NORMAL')
        r=decode_append_mesh(morph_glb(tangent));self.assertIn('TANGENT',r['ignored_attributes'])
        self.assertEqual(r['triangle_normals'],decode_append_mesh(glb(normals=[[.5,1.5,0]]*4))['triangle_normals'])

    def test_bounded_malformed_and_animated_refusals(self):
        changes=[lambda d,b,a:d['nodes'][0].update(weights=[1]),lambda d,b,a:d['meshes'][0].update(weights=None),lambda d,b,a:d['nodes'][0].update(weights=[True,0]),lambda d,b,a:d['nodes'][0].update(weights=[1000001,0]),lambda d,b,a:d['meshes'][0]['primitives'][0].update(targets=[]),lambda d,b,a:d['meshes'][0]['primitives'][0]['targets'].append({}),lambda d,b,a:d['meshes'][0]['primitives'][0]['targets'][0].update(COLOR_0=0),lambda d,b,a:d['meshes'][0]['primitives'][0]['attributes'].pop('NORMAL'),lambda d,b,a:d['accessors'][-1].update(count=3),lambda d,b,a:d['accessors'][-1].update(sparse={}),lambda d,b,a:d['accessors'][-1].update(normalized=True),lambda d,b,a:d['accessors'][-1].update(type='VEC4'),lambda d,b,a:d['meshes'][0]['primitives'][0]['targets'][0].update(POSITION=True),lambda d,b,a:d['nodes'][0].update(weights=[10000,0]),lambda d,b,a:d.update(animations=[dict(channels=[dict(sampler=0,target=dict(node=0,path='weights'))],samplers=[{}])])]
        for change in changes:
            with self.subTest(change=change),self.assertRaises(ImportError):decode_append_mesh(morph_glb(change))
        def mismatch(d,b,a):
            other=deepcopy(d['meshes'][0]['primitives'][0]);other.pop('targets');d['meshes'][0]['primitives'].append(other)
        with self.assertRaisesRegex(ImportError,'same morph target count'):decode_append_mesh(morph_glb(mismatch))
        with self.assertRaisesRegex(ImportError,'1 through 8'):decode_append_mesh(morph_glb(lambda d,b,a:d['meshes'][0]['primitives'][0].update(targets=[{'POSITION':0}]*9)))

    def test_native_review_apply_and_client_metadata(self):
        helper=mesh_fixtures.MeshAppendTests();self.addCleanup(helper.doCleanups);p,asset,donor=helper.fixture();source=model_face_addition.source(p,asset,'a'*64)
        content=morph_glb();before=deepcopy(p._document());depth=len(p.undo_stack)
        literal=glb(positions=[[2,3,0],[102,3,0],[2,103,0],[102,103,0]],normals=[[.5,1.5,-.5]]*4)
        actual,_,report=model_mesh_append.prepare(p,asset,content,donor,source['effective_sha256'],'a'*64)
        expected,_,_=model_mesh_append.prepare(p,asset,literal,donor,source['effective_sha256'],'a'*64);self.assertEqual(actual,expected);self.assertEqual(p._document(),before)
        script="""import {decodeMeshAppendReview,decodeMeshFile} from './integrations/legaia/editor/model-mesh-append.js';import assert from 'node:assert/strict';let text='';for await(const c of process.stdin)text+=c;const {report,source,inventory,donor}=JSON.parse(text);decodeMeshFile(inventory,report.geometry.glb_sha256);decodeMeshAppendReview(report,source,donor,report.geometry.glb_sha256);for(const change of [r=>r.geometry.node_sources[0].morph_bake.weights=[1],r=>r.geometry.node_sources[0].morph_bake.weights=[null,0],r=>r.geometry.node_sources[0].morph_bake.weight_source='zero',r=>r.geometry.node_sources[0].morph_bake.target_count=9,r=>r.geometry.node_sources[0].morph_bake.extra=1]){const bad=structuredClone(report);change(bad);assert.throws(()=>decodeMeshAppendReview(bad,source,donor,report.geometry.glb_sha256));}"""
        run=subprocess.run(['C:/Program Files/nodejs/node.exe','--input-type=module','-e',script],input=json.dumps(dict(report=report,source=source,inventory=inspect_append_mesh(content),donor=donor)),text=True,capture_output=True,encoding='utf-8');self.assertEqual(run.returncode,0,run.stderr)
        p.apply_model_mesh_append(asset,content,donor,source['effective_sha256'],'a'*64,report['review_key']);self.assertEqual(len(p.undo_stack),depth+1);p.undo();self.assertEqual(p._document(),before);p.redo()

    def test_native_gouraud_normal_allocation_literal_bytes(self):
        helper=normal_fixtures.MeshAppendNormalTests();self.addCleanup(helper.doCleanups);p,asset,donor=helper.fixture(0x14);source=model_face_addition.source(p,asset,'a'*64)
        literal=glb(positions=[[2,3,0],[102,3,0],[2,103,0],[102,103,0]],normals=[[.5,1.5,-.5]]*4)
        actual,_,report=model_mesh_append.prepare(p,asset,morph_glb(),donor,source['effective_sha256'],'a'*64)
        expected,_,oracle=model_mesh_append.prepare(p,asset,literal,donor,source['effective_sha256'],'a'*64)
        self.assertEqual(actual,expected);self.assertEqual(report['normal_import'],oracle['normal_import']);self.assertEqual(report['normal_import']['mode'],'gouraud')


if __name__=='__main__':unittest.main()
