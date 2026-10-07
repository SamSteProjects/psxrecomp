"""Static weighted skin baking, native review and bounded source refusals."""
from copy import deepcopy
from decimal import Decimal,localcontext
from hashlib import sha256
import json,struct,subprocess,unittest
from importer.animation_glb import _read_glb
from importer.model_glb import _write_glb
from importer.model_mesh_append import decode_append_mesh,inspect_append_mesh
from importer.core import ImportError
from sdk import model_mesh_append,model_face_addition
from test_model_mesh_append import glb
import test_model_mesh_append as mesh_fixtures
import test_model_mesh_append_normals as normal_fixtures


def skin_glb(change=None,weight_component=5126,normals=None):
    doc,binary=_read_glb(glb(normals=normals));binary=bytearray(binary)
    def add(rows,width,component,kind,normalized=False):
        binary.extend(b'\0'*(-len(binary)%4));start=len(binary);fmt={5126:'f',5121:'B',5123:'H'}[component]
        for row in rows:binary.extend(struct.pack('<'+str(width)+fmt,*row))
        view=len(doc['bufferViews']);doc['bufferViews'].append(dict(buffer=0,byteOffset=start,byteLength=len(binary)-start))
        index=len(doc['accessors']);doc['accessors'].append(dict(bufferView=view,componentType=component,count=len(rows),type=kind))
        if normalized:doc['accessors'][-1]['normalized']=True
        return index
    attrs=doc['meshes'][0]['primitives'][0]['attributes']
    attrs['JOINTS_0']=add([[0,1,0,0]]*4,4,5121,'VEC4')
    divisor={5126:1,5121:255,5123:65535}[weight_component]
    weights=[[.75,.25,0,0],[.25,.75,0,0],[.5,.5,0,0],[0,1,0,0]]
    if divisor!=1:weights=[[round(row[0]*divisor),divisor-round(row[0]*divisor),0,0] for row in weights]
    attrs['WEIGHTS_0']=add(weights,4,weight_component,'VEC4',weight_component!=5126)
    matrices=[[1,0,0,0,0,1,0,0,0,0,1,0,-10,0,0,1],[1,0,0,0,0,1,0,0,0,0,1,0,-4,-10,0,1]]
    accessor=add(matrices,16,5126,'MAT4')
    doc.update(nodes=[{'mesh':0,'skin':0,'translation':[1000,1000,1000]},
                      {'translation':[20,0,0],'scale':[2,1,1],'children':[2]},
                      {'translation':[0,40,0],'scale':[1,2,1]}],scenes=[{'nodes':[1,0]}],skins=[dict(joints=[1,2],skeleton=1,inverseBindMatrices=accessor)])
    doc['buffers'][0]['byteLength']=len(binary)
    if change:change(doc,binary)
    return _write_glb(doc,binary)


class StaticSkinTests(unittest.TestCase):
    def test_joint_world_inverse_bind_weights_and_ignored_mesh_transform(self):
        content=skin_glb(normals=[[0,1,0]]*4);before=bytes(content);r=decode_append_mesh(content)
        self.assertEqual(content,before);self.assertEqual(r['vertices'],[[3,-5,0],[6,-160,0],[209,-15,0],[212,-220,0]])
        self.assertEqual(r['triangles'],[[0,1,2],[2,1,3]]);self.assertEqual(r['triangle_normals'],[[[0,-4096,0]]*3]*2)
        binding=dict(skin_index=0,joint_nodes=[1,2],inverse_bind_accessor=5)
        self.assertEqual(r['node_sources'][0]['skin_bake'],binding)
        self.assertEqual(r['static_scope']['baked_skin_indices'],[0])
        self.assertNotIn('_skin_world',r['node_sources'][0]);self.assertEqual(inspect_append_mesh(content)['node_sources'],r['node_sources'])
        # Independent diagonal inverse-transpose directions, not a skin helper oracle.
        r=decode_append_mesh(skin_glb(normals=[[1,1,0]]*4))
        expected=[]
        with localcontext() as ctx:
            ctx.prec=60
            for y_scale in [Decimal('1.25'),Decimal('1.5'),Decimal('1.75'),Decimal(2)]:
                x=Decimal('.5');y=-1/y_scale;length=(x*x+y*y).sqrt();expected.append([int((x/length*4096).to_integral_value()),int((y/length*4096).to_integral_value()),0])
        self.assertEqual(r['triangle_normals'],[[expected[0],expected[1],expected[2]],[expected[2],expected[1],expected[3]]])

    def test_normalized_weights_multiple_sets_and_optional_inverse_bind(self):
        for component,divisor in [(5121,255),(5123,65535)]:
            r=decode_append_mesh(skin_glb(weight_component=component));weights=[round(.25*divisor)/divisor,round(.5*divisor)/divisor,1-round(.25*divisor)/divisor,1]
            # Encoded first weight is rounded; second is exact remaining integer.
            weights=[(divisor-round(.75*divisor))/divisor,(divisor-round(.5*divisor))/divisor,(divisor-round(.25*divisor))/divisor,1]
            source=[[0,0],[0,100],[100,0],[100,100]]
            self.assertEqual(r['vertices'],[[round(2*x+12*w),round(-(1+w)*y-20*w),0] for (x,y),w in zip(source,weights)])
        def omitted(d,b):d['skins'][0].pop('inverseBindMatrices')
        r=decode_append_mesh(skin_glb(omitted));self.assertEqual(r['vertices'][0],[20,-10,0]);self.assertIsNone(r['node_sources'][0]['skin_bake']['inverse_bind_accessor'])
        def additional(d,b):
            attrs=d['meshes'][0]['primitives'][0]['attributes'];a=d['accessors'][attrs['WEIGHTS_0']];view=d['bufferViews'][a['bufferView']];b[view['byteOffset']:view['byteOffset']+view['byteLength']]=b'\0'*view['byteLength'];attrs['JOINTS_1']=attrs['JOINTS_0'];attrs['WEIGHTS_1']=len(d['accessors']);d['accessors'].append(deepcopy(a));start=len(b);b.extend(b''.join(struct.pack('<4f',1,0,0,0) for _ in range(4)));d['accessors'][-1]['bufferView']=len(d['bufferViews']);d['bufferViews'].append(dict(buffer=0,byteOffset=start,byteLength=64));d['buffers'][0]['byteLength']=len(b)
        self.assertEqual(decode_append_mesh(skin_glb(additional))['vertices'],[[0,0,0],[0,-100,0],[200,0,0],[200,-100,0]])

    def test_malformed_activity_weights_bindings_and_singular_refusals(self):
        def weight(d,b,words):
            attrs=d['meshes'][0]['primitives'][0]['attributes'];view=d['bufferViews'][d['accessors'][attrs['WEIGHTS_0']]['bufferView']];struct.pack_into('<4f',b,view['byteOffset'],*words)
        changes=[lambda d,b:d['skins'][0].update(joints=[1,1]),lambda d,b:d['skins'][0].update(joints=[0,2]),lambda d,b:d['skins'][0].update(skeleton=0),lambda d,b:d['skins'][0].update(inverseBindMatrices=True),lambda d,b:d['skins'][0].update(inverseBindMatrices=None),lambda d,b:d['skins'][0].update(skeleton=None),lambda d,b:d['accessors'][-3].update(byteOffset=1),lambda d,b:d['accessors'][-1].update(type='VEC4'),lambda d,b:d['accessors'][-1].update(count=1),lambda d,b:weight(d,b,[0,0,0,0]),lambda d,b:weight(d,b,[.5,.25,0,0]),lambda d,b:weight(d,b,[-.5,1.5,0,0]),lambda d,b:d['meshes'][0]['primitives'][0]['attributes'].pop('WEIGHTS_0'),lambda d,b:d['accessors'][-3].update(componentType=5125),lambda d,b:d['nodes'][2].update(scale=[-1,-1,-1]),lambda d,b:d.update(animations=[dict(channels=[dict(sampler=0,target=dict(node=2,path='translation'))],samplers=[{}])])]
        for change in changes:
            with self.subTest(change=change),self.assertRaises(ImportError):decode_append_mesh(skin_glb(change))
        def duplicate(d,b):
            attrs=d['meshes'][0]['primitives'][0]['attributes'];view=d['bufferViews'][d['accessors'][attrs['JOINTS_0']]['bufferView']];b[view['byteOffset']+1]=0
        with self.assertRaisesRegex(ImportError,'unique nonzero'):decode_append_mesh(skin_glb(duplicate))
        def reflected(d,b):d['nodes'][1]['scale'][0]=-2
        r=decode_append_mesh(skin_glb(reflected));self.assertEqual(r['triangles'],[[0,1,2],[1,3,2]])

    def test_native_review_matches_independent_static_mesh_and_client_ownership(self):
        helper=mesh_fixtures.MeshAppendTests();self.addCleanup(helper.doCleanups);p,asset,donor=helper.fixture();source=model_face_addition.source(p,asset,'a'*64)
        content=skin_glb();before=deepcopy((p._document(),p.undo_stack,p.redo_stack))
        report=model_mesh_append.review(p,asset,content,donor,source['effective_sha256'],'a'*64)
        static=glb(positions=[[3,5,0],[209,15,0],[6,160,0],[212,220,0]])
        oracle=model_mesh_append.review(p,asset,static,donor,source['effective_sha256'],'a'*64)
        self.assertEqual(report['proposed_sha256'],oracle['proposed_sha256']);self.assertEqual(report['preview'],oracle['preview']);self.assertEqual((p._document(),p.undo_stack,p.redo_stack),before)
        script="""import {decodeMeshAppendReview,decodeMeshFile} from './integrations/legaia/editor/model-mesh-append.js';import assert from 'node:assert/strict';let text='';for await(const c of process.stdin)text+=c;const {report,source,inventory,donor}=JSON.parse(text);decodeMeshFile(inventory,report.geometry.glb_sha256);decodeMeshAppendReview(report,source,donor,report.geometry.glb_sha256);for(const change of [r=>r.geometry.node_sources[0].skin_bake.joint_nodes=[99],r=>r.geometry.node_sources[0].skin_bake.inverse_bind_accessor=true,r=>r.geometry.static_scope.baked_skin_indices=[],r=>r.geometry.static_scope.selected_nodes=[0,1],r=>delete r.geometry.static_scope]){const bad=structuredClone(report);change(bad);assert.throws(()=>decodeMeshAppendReview(bad,source,donor,report.geometry.glb_sha256));}"""
        run=subprocess.run(['C:/Program Files/nodejs/node.exe','--input-type=module','-e',script],input=json.dumps(dict(report=report,source=source,inventory=inspect_append_mesh(content),donor=donor)),text=True,capture_output=True,encoding='utf-8');self.assertEqual(run.returncode,0,run.stderr)
        depth=len(p.undo_stack);p.apply_model_mesh_append(asset,content,donor,source['effective_sha256'],'a'*64,report['review_key']);self.assertEqual(len(p.undo_stack),depth+1);p.undo();self.assertEqual(p._document(),before[0]);p.redo()

    def test_interleaved_joint_weights_and_distinct_primitive_influences(self):
        def interleave(d,b):
            attrs=d['meshes'][0]['primitives'][0]['attributes'];j=d['accessors'][attrs['JOINTS_0']];w=d['accessors'][attrs['WEIGHTS_0']]
            jv=d['bufferViews'][j['bufferView']];wv=d['bufferViews'][w['bufferView']];start=len(b)
            for i in range(4):b.extend(b[jv['byteOffset']+i*4:jv['byteOffset']+i*4+4]);b.extend(b[wv['byteOffset']+i*16:wv['byteOffset']+i*16+16])
            view=len(d['bufferViews']);d['bufferViews'].append(dict(buffer=0,byteOffset=start,byteLength=80,byteStride=20));j.update(bufferView=view,byteOffset=0);w.update(bufferView=view,byteOffset=4);d['buffers'][0]['byteLength']=len(b)
        self.assertEqual(decode_append_mesh(skin_glb(interleave)),decode_append_mesh(skin_glb())|{'glb_sha256':sha256(skin_glb(interleave)).hexdigest()})
        def second(d,b):
            primitive=deepcopy(d['meshes'][0]['primitives'][0]);start=len(b);b.extend(b''.join(struct.pack('<4f',1,0,0,0) for _ in range(4)));view=len(d['bufferViews']);d['bufferViews'].append(dict(buffer=0,byteOffset=start,byteLength=64));a=len(d['accessors']);d['accessors'].append(dict(bufferView=view,componentType=5126,count=4,type='VEC4'));primitive['attributes']['WEIGHTS_0']=a;d['meshes'][0]['primitives'].append(primitive);d['buffers'][0]['byteLength']=len(b)
        r=decode_append_mesh(skin_glb(second));self.assertEqual(r['vertices'],[[3,-5,0],[6,-160,0],[209,-15,0],[212,-220,0],[0,0,0],[0,-100,0],[200,0,0],[200,-100,0]])
        self.assertEqual(r['triangles'],[[0,1,2],[2,1,3],[4,5,6],[6,5,7]])
        def mixed(d,b):
            d['nodes'][2]['scale'][0]=-1;attrs=d['meshes'][0]['primitives'][0]['attributes'];view=d['bufferViews'][d['accessors'][attrs['WEIGHTS_0']]['bufferView']]
            for i in range(4):struct.pack_into('<4f',b,view['byteOffset']+i*16,1 if i%2==0 else 0,0 if i%2==0 else 1,0,0)
        with self.assertRaisesRegex(ImportError,'mixes reflected'):decode_append_mesh(skin_glb(mixed))

    def test_native_gouraud_normal_allocation_matches_literal_static_pose(self):
        helper=normal_fixtures.MeshAppendNormalTests();self.addCleanup(helper.doCleanups);p,asset,donor=helper.fixture(0x14);source=model_face_addition.source(p,asset,'a'*64)
        content=skin_glb(normals=[[1,1,0]]*4)
        static=glb(positions=[[3,5,0],[209,15,0],[6,160,0],[212,220,0]],normals=[[.5,.8,0],[.5,4/7,0],[.5,2/3,0],[.5,.5,0]])
        actual,_,report=model_mesh_append.prepare(p,asset,content,donor,source['effective_sha256'],'a'*64)
        expected,_,oracle=model_mesh_append.prepare(p,asset,static,donor,source['effective_sha256'],'a'*64)
        self.assertEqual(actual,expected);self.assertEqual(report['normal_import'],oracle['normal_import']);self.assertEqual(report['normal_import']['mode'],'gouraud');self.assertEqual(len(report['normal_import']['vectors']),4)


if __name__=='__main__':unittest.main()
