"""Explicit GLB clip selection preserves binding and fixed native sampling."""
from copy import deepcopy
import struct
import unittest

from importer.animation import decode_animation_record
from importer.animation_glb import import_animation_glb
from importer.core import ImportError
from test_animation_glb import document, encode, record


def two_clips(doc, payload, amount=4):
    doc=deepcopy(doc)
    doc['animations'][0]['name']='Original pose'
    second=deepcopy(doc['animations'][0]);second['name']='Edited pose'
    channel=next(c for c in second['channels'] if c['target']==dict(node=0,path='translation'))
    sampler=second['samplers'][channel['sampler']]
    original=doc['accessors'][sampler['output']];view=doc['bufferViews'][original['bufferView']]
    start=view.get('byteOffset',0)+original.get('byteOffset',0)
    raw=bytearray(payload[start:start+original['count']*12])
    struct.pack_into('<f',raw,0,struct.unpack_from('<f',raw,0)[0]+amount)
    vi=len(doc['bufferViews']);ai=len(doc['accessors'])
    doc['bufferViews'].append(dict(buffer=0,byteOffset=len(payload),byteLength=len(raw)))
    doc['accessors'].append(dict(bufferView=vi,componentType=5126,count=original['count'],type='VEC3'))
    sampler['output']=ai;doc['animations'].append(second)
    return doc,payload+raw


class ClipSelection(unittest.TestCase):
    def fixture(self):
        frames=[[([0,0,0],[0,0,0])]]*3
        doc,payload=document(frames,terminal=False)
        doc,payload=two_clips(doc,payload)
        return record(frames),doc,payload

    def test_selected_clip_exact_native_changes_and_explicit_report_identity(self):
        source,doc,payload=self.fixture();raw=encode(doc,payload)
        for index in [0,1]:
            candidate,report=import_animation_glb(source,raw,fps=15,animation_index=index)
            self.assertEqual(report['file_animation_index'],index)
            self.assertEqual(report['changed_axes'],index)
            transforms=decode_animation_record(candidate)['frames'][0]['object_transforms'][0]
            self.assertEqual(transforms['translation'],[index*4,0,0])
            if index==0:self.assertEqual(candidate,source)

    def test_multi_clip_requires_valid_explicit_choice_and_bounded_catalog(self):
        source,doc,payload=self.fixture();raw=encode(doc,payload)
        for index in [None,False,True,-1,2,10**400,1.0,'1']:
            with self.subTest(index_type=type(index).__name__):
                with self.assertRaises(ImportError):import_animation_glb(source,raw,fps=15,animation_index=index)
        doc['animations']=doc['animations']*33
        with self.assertRaises(ImportError):import_animation_glb(source,encode(doc,payload),fps=15,animation_index=0)

    def test_single_clip_and_static_defaults_preserve_legacy_report(self):
        source,doc,payload=self.fixture();doc['animations']=doc['animations'][:1]
        candidate,report=import_animation_glb(source,encode(doc,payload),fps=15)
        self.assertEqual(candidate,source);self.assertNotIn('file_animation_index',report)
        doc.pop('animations')
        _,report=import_animation_glb(source,encode(doc,payload),fps=15)
        self.assertNotIn('file_animation_index',report)
        with self.assertRaises(ImportError):import_animation_glb(source,encode(doc,payload),fps=15,animation_index=0)

    def test_unselected_channels_are_not_sampled_or_merged(self):
        source,doc,payload=self.fixture()
        doc['animations'][1]['channels'][0]['target']['path']='weights'
        self.assertEqual(import_animation_glb(source,encode(doc,payload),fps=15,animation_index=0)[0],source)
        with self.assertRaises(ImportError):import_animation_glb(source,encode(doc,payload),fps=15,animation_index=1)
