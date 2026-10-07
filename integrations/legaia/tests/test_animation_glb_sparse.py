"""Sparse FLOAT animation interoperability and malformed-span checks."""
from copy import deepcopy
import math
import struct
import unittest
from unittest.mock import patch
from importer.animation_glb import _Accessors, import_animation_glb
from importer.core import ImportError
from test_animation_glb import document, encode, record


def sparsify(doc, payload, *, base=False, component=5123):
    """Independent encoder for animation sampler accessors; retain other bytes."""
    doc=deepcopy(doc);payload=bytearray(payload)
    ids={sampler[field] for clip in doc['animations'] for sampler in clip['samplers'] for field in ('input','output')}
    fmt={5121:'B',5123:'H',5125:'I'}[component]
    def view(data):
        payload.extend(bytes(-len(payload)%4));offset=len(payload);payload.extend(data)
        index=len(doc['bufferViews']);doc['bufferViews'].append(dict(buffer=0,byteOffset=offset,byteLength=len(data)));return index
    for index in sorted(ids):
        row=doc['accessors'][index];width={'SCALAR':1,'VEC3':3,'VEC4':4}[row['type']]
        old=doc['bufferViews'][row['bufferView']];start=old.get('byteOffset',0)+row.get('byteOffset',0)
        values=list(struct.iter_unpack(f'<{width}f',payload[start:start+row['count']*width*4]))
        indices=[i for i,value in enumerate(values) if any(v!=0 for v in value)]
        row.pop('bufferView');row.pop('byteOffset',None)
        if base:row['bufferView']=view(bytes(row['count']*width*4))
        if indices:
            row['sparse']=dict(count=len(indices),indices=dict(bufferView=view(struct.pack(f'<{len(indices)}{fmt}',*indices)),componentType=component),values=dict(bufferView=view(b''.join(struct.pack(f'<{width}f',*values[i]) for i in indices))))
    return doc,bytes(payload)


class SparseAnimation(unittest.TestCase):
    def setUp(self):
        self.frames=[[([0,-20,30],[16,32,48])],[([11,0,31],[17,33,49])],[([0,0,0],[0,0,0])]]
        self.source=record(self.frames);self.doc,self.payload=document(self.frames)

    def test_sparse_input_translation_rotation_and_all_index_widths(self):
        for component in (5121,5123,5125):
            for base in (False,True):
                with self.subTest(component=component,base=base):
                    doc,payload=sparsify(self.doc,self.payload,base=base,component=component)
                    candidate,report=import_animation_glb(self.source,encode(doc,payload),fps=15)
                    self.assertEqual(candidate,self.source);self.assertEqual(report['changes'],[])

    def test_sparse_edits_match_independent_native_record(self):
        changed=deepcopy(self.frames);changed[1][0][0][0]=14;changed[1][0][1][2]=52
        doc,payload=document(changed);doc,payload=sparsify(doc,payload)
        candidate,report=import_animation_glb(self.source,encode(doc,payload),fps=15)
        self.assertEqual(candidate,record(changed));self.assertEqual(len(report['changes']),2)

    def test_sparse_cubic_matches_dense_sampling(self):
        from test_animation_glb_cubic import cubic_channel
        rows=[([0,0,0],[i,0,0],[0,0,0]) for i in range(4)]
        doc,payload=cubic_channel(self.doc,self.payload,'translation',rows)
        dense=import_animation_glb(self.source,encode(doc,payload),fps=15)[0]
        doc,payload=sparsify(doc,payload)
        self.assertEqual(import_animation_glb(self.source,encode(doc,payload),fps=15)[0],dense)

    def test_duplicate_unsorted_out_of_range_indices_refuse(self):
        doc,payload=sparsify(self.doc,self.payload,component=5121)
        row=next(row for row in doc['accessors'] if row.get('sparse',{}).get('count',0)>=2)
        offset=doc['bufferViews'][row['sparse']['indices']['bufferView']]['byteOffset']
        for pair in ((1,1),(2,1),(0,row['count'])):
            with self.subTest(pair=pair):
                malformed=bytearray(payload);malformed[offset:offset+2]=bytes(pair)
                with self.assertRaises(ImportError):import_animation_glb(self.source,encode(doc,malformed),fps=15)

    def test_invalid_sparse_metadata_spans_and_nonfinite_values_refuse(self):
        doc,payload=sparsify(self.doc,self.payload)
        accessor=next(i for i,row in enumerate(doc['accessors']) if 'sparse' in row)
        for change in ('count','type','offset','stride','target','buffer','length','no_base_offset'):
            bad=deepcopy(doc);row=bad['accessors'][accessor];s=row['sparse'];iv=bad['bufferViews'][s['indices']['bufferView']];vv=bad['bufferViews'][s['values']['bufferView']]
            if change=='count':s['count']=True
            elif change=='type':s['indices']['componentType']=5122
            elif change=='offset':s['values']['byteOffset']=1
            elif change=='stride':iv['byteStride']=2
            elif change=='target':vv['target']=34962
            elif change=='buffer':iv['buffer']=True
            elif change=='length':vv['byteLength']=1
            else:row['byteOffset']=0
            with self.subTest(change=change),self.assertRaises(ImportError):import_animation_glb(self.source,encode(bad,payload),fps=15)
        bad=bytearray(payload);struct.pack_into('<f',bad,doc['bufferViews'][doc['accessors'][accessor]['sparse']['values']['bufferView']]['byteOffset'],math.inf)
        with self.assertRaises(ImportError):import_animation_glb(self.source,encode(doc,bad),fps=15)

    def test_implicit_zeros_component_bound_and_cache(self):
        doc=dict(accessors=[dict(componentType=5126,type='VEC3',count=2)],bufferViews=[])
        reader=_Accessors(doc,b'');self.assertEqual(reader.read(0,'VEC3'),[[0,0,0],[0,0,0]])
        reader.read(0,'VEC3');self.assertEqual(reader.component_count,6)
        with patch('importer.animation_glb.MAX_ANIMATION_COMPONENTS',5),self.assertRaises(ImportError):_Accessors(doc,b'').read(0,'VEC3')

    def test_sparse_matrix_elements_use_the_same_bounded_float_reader(self):
        identity=[1.0 if i in (0,5,10,15) else 0.0 for i in range(16)]
        payload=bytes([0,1,0,0])+struct.pack('<32f',*(identity*2))
        doc=dict(accessors=[dict(componentType=5126,type='MAT4',count=2,sparse=dict(count=2,
            indices=dict(bufferView=0,componentType=5121),values=dict(bufferView=1)))],
            bufferViews=[dict(buffer=0,byteOffset=0,byteLength=2),dict(buffer=0,byteOffset=4,byteLength=128)])
        self.assertEqual(_Accessors(doc,payload).read(0,'MAT4'),[identity,identity])


if __name__=='__main__':unittest.main()
