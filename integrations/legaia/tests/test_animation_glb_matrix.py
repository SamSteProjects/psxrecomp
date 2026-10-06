"""Rigid matrix equivalence against independently constructed TRS fixtures."""
from copy import deepcopy
import math
import struct
import unittest

from importer.animation_glb import import_animation_glb
from importer.core import ImportError
from test_animation_glb import document, encode, record
from test_animation_glb_hierarchy import translated_hierarchy


def matrix(translation, quaternion, float32=False):
    x,y,z,w=quaternion
    rows=[[1-2*(y*y+z*z),2*(x*y-z*w),2*(x*z+y*w)],
          [2*(x*y+z*w),1-2*(x*x+z*z),2*(y*z-x*w)],
          [2*(x*z-y*w),2*(y*z+x*w),1-2*(x*x+y*y)]]
    result=[rows[row][column] for column in range(3) for row in range(3)]
    result=result[:3]+[0]+result[3:6]+[0]+result[6:]+[0]+list(translation)+[1]
    return [struct.unpack('<f',struct.pack('<f',v))[0] for v in result] if float32 else result


def matrix_parent(doc):
    doc=deepcopy(doc);node=doc['nodes'][-1]
    node['matrix']=matrix(node.pop('translation',[0,0,0]),node.pop('rotation',[0,0,0,1]))
    node.pop('scale',None)
    return doc


class RigidMatrices(unittest.TestCase):
    def test_static_source_matrices_preserve_native_angles_and_opaque_bytes(self):
        for ticks in [[0,0,0],[128,0,0],[0,128,0],[0,0,128],[12,30,70],[64,64,64]]:
            frames=[[([14,-7,23],ticks)]];doc,payload=document(frames);doc.pop('animations')
            node=doc['nodes'][0];node['matrix']=matrix(node.pop('translation'),node.pop('rotation'),True)
            candidate,_=import_animation_glb(record(frames),encode(doc,payload),fps=15)
            self.assertEqual(candidate,record(frames))

    def test_static_matrix_parent_is_equivalent_to_hierarchical_trs(self):
        frames=[[([10,3,-2],[12,8,30]),([-4,12,0],[0,0,0])]]*3
        doc,payload=document(frames);doc,payload=translated_hierarchy(doc,payload)
        self.assertEqual(import_animation_glb(record(frames),encode(matrix_parent(doc),payload),fps=15)[0],record(frames))
        doc['nodes'][-1]['rotation']=[0,0,math.sqrt(.5),math.sqrt(.5)]
        expected=import_animation_glb(record(frames),encode(doc,payload),fps=15)[0]
        self.assertEqual(import_animation_glb(record(frames),encode(matrix_parent(doc),payload),fps=15)[0],expected)

    def test_scale_shear_reflection_perspective_and_huge_basis_reject(self):
        frames=[[([0,0,0],[0,0,0])]];doc,payload=document(frames);doc.pop('animations')
        node=doc['nodes'][0];node.pop('translation');node.pop('rotation')
        base=matrix([0,0,0],[0,0,0,1])
        for index,value in [(0,2),(0,-1),(4,.1),(3,.01),(15,0),(0,10**400),(0,1e200)]:
            bad=deepcopy(doc);m=base.copy();m[index]=value;bad['nodes'][0]['matrix']=m
            with self.subTest(index=index,value=value):
                with self.assertRaises(ImportError):import_animation_glb(record(frames),encode(bad,payload),fps=15)

    def test_matrix_trs_mixture_and_any_animated_matrix_target_reject(self):
        frames=[[([0,0,0],[0,0,0])]]*2;doc,payload=document(frames)
        doc['nodes'][0]['matrix']=matrix([0,0,0],[0,0,0,1])
        with self.assertRaisesRegex(ImportError,'combined'):import_animation_glb(record(frames),encode(doc,payload),fps=15)
        doc['nodes'][0].pop('translation');doc['nodes'][0].pop('rotation')
        with self.assertRaisesRegex(ImportError,'matrices'):import_animation_glb(record(frames),encode(doc,payload),fps=15)
