"""Sparse saved poses match independent dense meshes through native authoring."""
from copy import deepcopy
import struct,unittest
from importer.animation_glb import _read_glb
from importer.model_glb import _write_glb,_Accessors,MAX_COMPONENTS
from importer.model_mesh_append import decode_append_mesh,inspect_append_mesh
from importer.model_mesh_sparse import morph_delta
from importer.core import ImportError
from sdk import model_mesh_append,model_face_addition
from test_model_mesh_morph import morph_glb
from test_model_mesh_append import glb
import test_model_mesh_append_normals as normal_fixtures


POSE=[[0,-1,0],[104,1,1],[0,99,0],[98,105,0]]
NORMALS=[[1.5,.5,-.5],[.5,1.5,-.5],[1,2,-1.5],[.5,1.5,-.5]]


def sparse_glb(change=None,component=5121,skin=False):
    doc,binary=_read_glb(morph_glb(skin=skin));binary=bytearray(binary)
    def view(data):
        binary.extend(b'\0'*(-len(binary)%4));start=len(binary);binary.extend(data)
        index=len(doc['bufferViews']);doc['bufferViews'].append(dict(buffer=0,byteOffset=start,byteLength=len(data)));return index
    primitive=doc['meshes'][0]['primitives'][0]
    for name,slots,values in [('POSITION',[1,3],[[8,4,2],[-4,12,0]]),('NORMAL',[0,2],[[1,-1,0],[0,2,-2]])]:
        a=doc['accessors'][primitive['targets'][0][name]]
        if name=='POSITION':a.pop('bufferView')
        a['sparse']=dict(count=2,indices=dict(bufferView=view(struct.pack('<2'+{5121:'B',5123:'H',5125:'I'}[component],*slots)),componentType=component),values=dict(bufferView=view(b''.join(struct.pack('<3f',*row) for row in values))))
    if change:change(doc,binary)
    return _write_glb(doc,binary)


class SparseMorphTests(unittest.TestCase):
    def test_zero_and_dense_initialization_unsigned_index_widths(self):
        expected=decode_append_mesh(glb(positions=POSE,normals=NORMALS))
        for component in (5121,5123,5125):
            content=sparse_glb(component=component);held=bytes(content);actual=decode_append_mesh(content)
            self.assertEqual(content,held)
            for key in ('vertices','triangles','triangle_normals'):self.assertEqual(actual[key],expected[key])
            self.assertEqual(inspect_append_mesh(content)['node_sources'],actual['node_sources'])
        self.assertEqual(expected['vertices'],[[0,1,0],[0,-99,0],[104,-1,1],[98,-105,0]])

    def test_offsets_and_interleaved_dense_initialization(self):
        def offset(d,b):
            p=d['meshes'][0]['primitives'][0]
            for name in ('POSITION','NORMAL'):
                a=d['accessors'][p['targets'][0][name]]
                for label,unit in [('indices',1),('values',4)]:
                    spec=a['sparse'][label];v=d['bufferViews'][spec['bufferView']];payload=bytes(b[v['byteOffset']:v['byteOffset']+v['byteLength']]);b.extend(b'\0'*(-len(b)%4));start=len(b);b.extend(b'\0'*unit+payload);v.update(byteOffset=start,byteLength=unit+len(payload));spec['byteOffset']=unit
            a=d['accessors'][p['targets'][0]['NORMAL']];v=d['bufferViews'][a['bufferView']];start=len(b);base=bytes(b[v['byteOffset']:v['byteOffset']+v['byteLength']])
            for i in range(4):b.extend(base[i*12:i*12+12]+b'\0'*4)
            v.update(byteOffset=start,byteLength=64,byteStride=16)
        a=decode_append_mesh(sparse_glb(offset));e=decode_append_mesh(sparse_glb())
        for key in ('vertices','triangles','triangle_normals'):self.assertEqual(a[key],e[key])

    def test_cache_isolated_from_dense_reader_and_component_budget(self):
        doc,binary=_read_glb(sparse_glb());reader=_Accessors(doc,binary);index=doc['meshes'][0]['primitives'][0]['targets'][0]['POSITION']
        with self.assertRaises(ImportError):reader.read(index,3,'fixed layout')
        result=morph_delta(reader,index,4);cost=reader.components;self.assertEqual(morph_delta(reader,index,4),result);self.assertEqual(reader.components,cost)
        self.assertEqual(result,[(0.,0.,0.),(8.,4.,2.),(0.,0.,0.),(-4.,12.,0.)])
        with self.assertRaises(ImportError):morph_delta(reader,index,3)
        exhausted=_Accessors(doc,binary);exhausted.components=MAX_COMPONENTS-1
        with self.assertRaisesRegex(ImportError,'component budget'):morph_delta(exhausted,index,4)
        self.assertIn('sparse',doc['accessors'][index]);self.assertNotIn('bufferView',doc['accessors'][index])

    def test_sparse_tangent_qualified_without_native_allocation(self):
        def tangent(d,b):
            p=d['meshes'][0]['primitives'][0];b.extend(b'\0'*(-len(b)%4));start=len(b)
            b.extend(b''.join(struct.pack('<4f',1,0,0,1) for _ in range(4)))
            view=len(d['bufferViews']);d['bufferViews'].append(dict(buffer=0,byteOffset=start,byteLength=64))
            index=len(d['accessors']);d['accessors'].append(dict(bufferView=view,componentType=5126,count=4,type='VEC4'))
            p['attributes']['TANGENT']=index;p['targets'][0]['TANGENT']=p['targets'][0]['NORMAL']
        actual=decode_append_mesh(sparse_glb(tangent));expected=decode_append_mesh(sparse_glb())
        self.assertEqual(actual['vertices'],expected['vertices']);self.assertEqual(actual['triangle_normals'],expected['triangle_normals']);self.assertEqual(actual['ignored_attributes'],['TANGENT'])

    def test_sparse_before_skin_literal_positions_and_normals(self):
        # Independent two-joint affine blend applied after the sparse shape.
        positions=[[3,3.75,0],[217,16.75,1],[6,158.5,0],[208,230,0]]
        normals=[[.75,.4,-.5],[.25,6/7,-.5],[.5,4/3,-1.5],[.25,.75,-.5]]
        a=decode_append_mesh(sparse_glb(skin=True));e=decode_append_mesh(glb(positions=positions,normals=normals))
        for key in ('vertices','triangles','triangle_normals'):self.assertEqual(a[key],e[key])

    def test_malformed_ownership_range_order_alignment_and_nonfinite_refusals(self):
        def change(kind):
            def mutate(d,b):
                p=d['meshes'][0]['primitives'][0];a=d['accessors'][p['targets'][0]['POSITION']];s=a['sparse'];iv=d['bufferViews'][s['indices']['bufferView']];vv=d['bufferViews'][s['values']['bufferView']]
                if kind=='duplicate':b[iv['byteOffset']+1]=1
                elif kind=='descending':b[iv['byteOffset']]=3;b[iv['byteOffset']+1]=1
                elif kind=='range':b[iv['byteOffset']+1]=4
                elif kind=='nan':struct.pack_into('<f',b,vv['byteOffset'],float('nan'))
                elif kind=='zero':s['count']=0
                elif kind=='count':s['count']=5
                elif kind=='boolean':s['count']=True
                elif kind=='stride':vv['byteStride']=12
                elif kind=='target':iv['target']=34963
                elif kind=='external':vv['buffer']=1
                elif kind=='truncated':vv['byteLength']=12
                elif kind=='offset':s['values']['byteOffset']=1
                elif kind=='view':s['indices']['bufferView']=True
                elif kind=='signed':s['indices']['componentType']=5122
                elif kind=='base_offset':a['byteOffset']=4
                elif kind=='base_count':a['count']=3
                elif kind=='normalized':a['normalized']=True
                elif kind=='missing':s.pop('values')
                elif kind=='extra':s['indices']['extensions']={}
            return mutate
        for kind in ('duplicate','descending','range','nan','zero','count','boolean','stride','target','external','truncated','offset','view','signed','base_offset','base_count','normalized','missing','extra'):
            with self.subTest(kind=kind),self.assertRaises(ImportError):decode_append_mesh(sparse_glb(change(kind)))

    def test_native_lit_bytes_and_history(self):
        helper=normal_fixtures.MeshAppendNormalTests();self.addCleanup(helper.doCleanups);p,asset,donor=helper.fixture(0x14);source=model_face_addition.source(p,asset,'a'*64)
        content=sparse_glb();before=deepcopy(p._document());depth=len(p.undo_stack)
        actual,_,report=model_mesh_append.prepare(p,asset,content,donor,source['effective_sha256'],'a'*64)
        expected,_,oracle=model_mesh_append.prepare(p,asset,glb(positions=POSE,normals=NORMALS),donor,source['effective_sha256'],'a'*64)
        self.assertEqual(actual,expected);self.assertEqual(report['normal_import'],oracle['normal_import']);self.assertEqual(report['normal_import']['mode'],'gouraud')
        p.apply_model_mesh_append(asset,content,donor,source['effective_sha256'],'a'*64,report['review_key']);self.assertEqual(len(p.undo_stack),depth+1);p.undo();self.assertEqual(p._document(),before);p.redo()


if __name__=='__main__':unittest.main()
