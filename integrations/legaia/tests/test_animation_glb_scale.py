"""Identity scale is proved across the curve, including unsampled intervals."""
from copy import deepcopy
import struct
import unittest

from importer.animation_glb import import_animation_glb
from importer.core import ImportError
from test_animation_glb import document, encode, record


def add_scale(doc, payload, *, node=0, mode='LINEAR', rows=None):
    doc = deepcopy(doc)
    animation = doc['animations'][0]
    input_index = animation['samplers'][0]['input']
    count = doc['accessors'][input_index]['count']
    rows = rows if rows is not None else (
        [[0,0,0], [1,1,1], [0,0,0]]*count if mode == 'CUBICSPLINE' else [[1,1,1]]*count)
    raw = b''.join(struct.pack('<3f', *row) for row in rows)
    vi, ai = len(doc['bufferViews']), len(doc['accessors'])
    doc['bufferViews'].append(dict(buffer=0, byteOffset=len(payload), byteLength=len(raw)))
    doc['accessors'].append(dict(bufferView=vi, componentType=5126, count=len(rows), type='VEC3'))
    si = len(animation['samplers'])
    animation['samplers'].append(dict(input=input_index, output=ai, interpolation=mode))
    animation['channels'].append(dict(sampler=si, target=dict(node=node, path='scale')))
    return doc, payload+raw


class IdentityScale(unittest.TestCase):
    def fixture(self, objects=1):
        frames = [[([1,2,3], [4,5,6])]*objects]*3
        doc, payload = document(frames, terminal=False)
        return record(frames), doc, payload

    def test_unit_scale_preserves_exact_native_record_for_all_modes(self):
        source, doc, payload = self.fixture()
        baseline, report = import_animation_glb(source, encode(doc, payload), fps=15)
        for mode in ['STEP', 'LINEAR', 'CUBICSPLINE']:
            d, p = add_scale(doc, payload, mode=mode)
            candidate, result = import_animation_glb(source, encode(d, p), fps=15)
            self.assertEqual(candidate, source)
            self.assertEqual(candidate, baseline)
            self.assertEqual(result['changed_axes'], 0)
            self.assertEqual(result['quantization'], report['quantization'])

    def test_cubic_unused_endpoint_tangents_do_not_change_curve(self):
        source, doc, payload = self.fixture()
        rows = [[0,0,0], [1,1,1], [0,0,0]]*3
        rows[0] = [100,-100,7]
        rows[-1] = [-100,100,7]
        d, p = add_scale(doc, payload, mode='CUBICSPLINE', rows=rows)
        self.assertEqual(import_animation_glb(source, encode(d, p), fps=15)[0], source)
        for index in [2,3,5,6]:
            changed = deepcopy(rows); changed[index] = [0.0001,0,0]
            d, p = add_scale(doc, payload, mode='CUBICSPLINE', rows=changed)
            with self.assertRaisesRegex(ImportError, 'identity scale'):
                import_animation_glb(source, encode(d, p), fps=15)

    def test_nonunit_duplicate_bad_shape_and_nonfinite_scale_reject(self):
        source, doc, payload = self.fixture()
        for value in [0, -1, 1.000001, 2, float('nan'), float('inf')]:
            d, p = add_scale(doc, payload, rows=[[1,1,1],[1,value,1],[1,1,1]])
            with self.assertRaises(ImportError): import_animation_glb(source, encode(d, p), fps=15)
        d, p = add_scale(doc, payload)
        for mutate in [lambda d:d['animations'][0]['channels'].append(deepcopy(d['animations'][0]['channels'][-1])),
                       lambda d:d['accessors'][-1].update(type='VEC4'),
                       lambda d:d['accessors'][-1].update(count=2),
                       lambda d:d['animations'][0]['channels'][-1]['target'].update(node=True),
                       lambda d:d['animations'][0]['samplers'][-1].update(interpolation='UNKNOWN')]:
            bad = deepcopy(d); mutate(bad)
            with self.assertRaises(ImportError): import_animation_glb(source, encode(bad, p), fps=15)

    def test_identity_ancestor_scale_and_all_64_rigid_objects(self):
        source, doc, payload = self.fixture()
        root = len(doc['nodes']); doc['nodes'].append(dict(name='Root', children=[0]))
        doc['scenes'][0]['nodes'] = [root]
        d, p = add_scale(doc, payload, node=root)
        self.assertEqual(import_animation_glb(source, encode(d, p), fps=15)[0], source)
        d['nodes'][root]['matrix'] = [1,0,0,0,0,1,0,0,0,0,1,0,0,0,0,1]
        with self.assertRaisesRegex(ImportError, 'matrices'):
            import_animation_glb(source, encode(d, p), fps=15)
        source, doc, payload = self.fixture(objects=64)
        for node in range(64): doc, payload = add_scale(doc, payload, node=node)
        self.assertEqual(len(doc['animations'][0]['channels']), 192)
        root=len(doc['nodes']);doc['nodes'].append(dict(name='Root',children=list(range(64))));doc['scenes'][0]['nodes']=[root]
        doc,payload=add_scale(doc,payload,node=root)
        self.assertEqual(import_animation_glb(source, encode(doc, payload), fps=15)[0], source)
