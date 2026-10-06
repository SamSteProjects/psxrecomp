"""Independent scene-space pose expectations for rigid hierarchy baking."""
from copy import deepcopy
import math
import struct
import unittest

from importer.animation import decode_animation_record
from importer.animation_glb import import_animation_glb
from importer.core import ImportError
from test_animation_glb import document, encode, record


def translated_hierarchy(doc, payload, offset=5):
    """Reparent exported independent nodes without changing their world poses."""
    doc = deepcopy(doc); payload = bytearray(payload)
    count = len(doc['nodes'])
    doc['nodes'].append(dict(name='External rig root', translation=[offset,0,0], children=list(range(count))))
    doc['scenes'][0]['nodes'] = [count]
    for node in doc['nodes'][:count]: node['translation'][0] -= offset
    written = set()
    for clip in doc.get('animations', []):
        for channel in clip['channels']:
            if channel['target']['path'] != 'translation': continue
            sampler = clip['samplers'][channel['sampler']]
            accessor = doc['accessors'][sampler['output']]
            view = doc['bufferViews'][accessor['bufferView']]
            start = view.get('byteOffset',0)+accessor.get('byteOffset',0)
            for i in range(accessor['count']):
                at = start+i*12
                if at in written: continue
                written.add(at)
                struct.pack_into('<f',payload,at,struct.unpack_from('<f',payload,at)[0]-offset)
    return doc, bytes(payload)


class HierarchyBaking(unittest.TestCase):
    def test_reparented_export_preserves_exact_native_and_opaque_bytes(self):
        frames = [[([10,3,-2],[12,8,30]), ([-4,12,0],[0,0,0])]]*3
        doc,payload=document(frames);doc,payload=translated_hierarchy(doc,payload)
        source=record(frames)
        self.assertEqual(import_animation_glb(source,encode(doc,payload),fps=15)[0],source)

    def test_static_rotating_parent_rotates_translation_and_native_orientation(self):
        source=record([[([0,0,0],[0,0,0])]])
        doc,payload=document([[([10,0,0],[0,0,0])]])
        doc.pop('animations')
        h=math.sqrt(.5)
        doc['nodes'].append(dict(name='Parent',translation=[3,4,5],rotation=[0,0,h,h],children=[0]))
        doc['scenes'][0]['nodes']=[1]
        candidate,_=import_animation_glb(source,encode(doc,payload),fps=15)
        self.assertEqual(candidate,record([[([3,-14,5],[0,0,192])]]))

    def test_noncommuting_parent_and_child_rotation_order(self):
        expected=record([[([0,0,0],[192,0,192])]])
        doc,payload=document([[([0,0,0],[0,0,0])]])
        doc.pop('animations');h=math.sqrt(.5)
        doc['nodes'][0]['rotation']=[0,h,0,h]
        doc['nodes'].append(dict(name='Parent',rotation=[h,0,0,h],children=[0]))
        doc['scenes'][0]['nodes']=[1]
        self.assertEqual(import_animation_glb(expected,encode(doc,payload),fps=15)[0],expected)

    def test_animated_parent_is_sampled_and_mapped_parent_is_not_double_counted(self):
        frames=[[([i*3,0,0],[0,0,0]),([2,0,0],[0,0,0])] for i in range(3)]
        doc,payload=document(frames);doc['nodes'][0]['children']=[1];doc['scenes'][0]['nodes']=[0]
        candidate,_=import_animation_glb(record(frames),encode(doc,payload),fps=15)
        expected=[[([i*3,0,0],[0,0,0]),([i*3+2,0,0],[0,0,0])] for i in range(3)]
        self.assertEqual(candidate,record(expected))
        # The same keyed translation on an unmapped ancestor participates too.
        doc['nodes'][0].pop('children');doc['nodes'].append(dict(name='Root',children=[0,1]))
        doc['scenes'][0]['nodes']=[2]
        doc['animations'][0]['channels'][0]['target']['node']=2
        candidate,_=import_animation_glb(record(frames),encode(doc,payload),fps=15)
        self.assertEqual(candidate,record(expected))

    def test_composed_overflow_nonunit_scale_and_unrelated_tracks_reject(self):
        source=record([[([1,0,0],[0,0,0])]])
        doc,payload=document([[([1,0,0],[0,0,0])]])
        doc['nodes'].append(dict(name='Root',children=[0],translation=[2047,0,0]))
        doc['scenes'][0]['nodes']=[1]
        with self.assertRaisesRegex(ImportError,'twelve-bit'):import_animation_glb(source,encode(doc,payload),fps=15)
        doc['nodes'][1]['translation']=[0,0,0];doc['nodes'][1]['scale']=[2,1,1]
        with self.assertRaisesRegex(ImportError,'scale'):import_animation_glb(source,encode(doc,payload),fps=15)
        doc['nodes'][1].pop('scale');doc['nodes'].append(dict(name='Unrelated'))
        doc['animations'][0]['channels'][0]['target']['node']=2
        with self.assertRaisesRegex(ImportError,'targets'):import_animation_glb(source,encode(doc,payload),fps=15)

    def test_deep_hierarchy_is_iterative_and_sample_work_is_bounded(self):
        frames=[[([0,0,0],[0,0,0])]]*17;doc,payload=document(frames)
        for i in range(1,4096):doc['nodes'].append(dict(name='Ancestor',children=[i-1]))
        doc['scenes'][0]['nodes']=[4095]
        with self.assertRaisesRegex(ImportError,'sampled-node'):import_animation_glb(record(frames),encode(doc,payload),fps=15)
        frames=frames[:1];doc,payload=document(frames)
        for i in range(1,1100):doc['nodes'].append(dict(name='Ancestor',children=[i-1]))
        doc['scenes'][0]['nodes']=[1099]
        self.assertEqual(import_animation_glb(record(frames),encode(doc,payload),fps=15)[0],record(frames))
