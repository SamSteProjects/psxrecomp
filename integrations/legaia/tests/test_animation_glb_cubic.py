"""Cubic interchange: independent curves, native quantization and invalid input."""
from copy import deepcopy
import math
import struct
import unittest

from importer.animation import decode_animation_record
from importer.animation_glb import import_animation_glb
from importer.core import ImportError
from test_animation_glb import document, encode, quaternion, record


def cubic_channel(doc, payload, path, triples, obj=0):
    """Replace one track with tightly packed in/value/out rows."""
    doc = deepcopy(doc)
    channel = next(c for c in doc['animations'][0]['channels']
                   if c['target'] == {'node': obj, 'path': path})
    sampler = doc['animations'][0]['samplers'][channel['sampler']]
    width = 3 if path == 'translation' else 4
    raw = b''.join(struct.pack(f'<{width}f', *v) for triple in triples for v in triple)
    vi = len(doc['bufferViews'])
    doc['bufferViews'].append({'buffer': 0, 'byteOffset': len(payload), 'byteLength': len(raw)})
    ai = len(doc['accessors'])
    doc['accessors'].append({'bufferView': vi, 'componentType': 5126,
                            'count': len(triples)*3, 'type': f'VEC{width}'})
    sampler.update(output=ai, interpolation='CUBICSPLINE')
    return doc, payload + raw


class AnimationGlbCubicTests(unittest.TestCase):
    def values(self, source, doc, payload, fps=4):
        candidate, report = import_animation_glb(source, encode(doc, payload), fps=fps)
        return [f['object_transforms'][0] for f in decode_animation_record(candidate)['frames']], report

    def test_derivatives_scale_by_seconds_and_reflect_y_with_endpoint_hold(self):
        source = record([[([0,0,0], [0,0,0])]]*5)
        doc, payload = document([[([0,0,0], [0,0,0])]]*2, fps=2, terminal=False)
        doc, payload = cubic_channel(doc, payload, 'translation', [
            ([999,999,999], [0,0,0], [16,32,-16]),
            ([0,0,0], [8,0,0], [999,999,999])])
        values, report = self.values(source, doc, payload)
        # At .25 seconds, Hermite gives .5*8 + .125*.5*[16,32,-16].
        self.assertEqual([v['translation'] for v in values],
                         [[0,0,0], [5,-2,-1], [8,0,0], [8,0,0], [8,0,0]])
        self.assertEqual(report['frame_count'], 5)

    def test_nonuniform_segments_and_before_first_key_hold(self):
        source = record([[([0,0,0], [0,0,0])]]*7)
        doc, payload = document([[([0,0,0], [0,0,0])]]*3, terminal=False)
        # A translation-only curve with .25, .75, 1.5 second keys.
        doc['animations'][0]['channels'] = [doc['animations'][0]['channels'][0]]
        sampler = doc['animations'][0]['samplers'][0]
        view = doc['bufferViews'][doc['accessors'][sampler['input']]['bufferView']]
        payload = bytearray(payload)
        struct.pack_into('<3f', payload, view['byteOffset'], .25, .75, 1.5)
        doc, payload = cubic_channel(doc, bytes(payload), 'translation', [
            ([0,0,0], [2,0,0], [0,0,0]),
            ([0,0,0], [10,0,0], [0,0,0]),
            ([0,0,0], [37,0,0], [0,0,0])])
        values, _ = self.values(source, doc, payload)
        # Zero-tangent smoothstep: at 1/3 and 2/3 of the final segment, 7/27 and 20/27.
        self.assertEqual([v['translation'][0] for v in values], [2,2,6,10,17,30,37])

    def test_rotation_derivatives_are_not_normalized_and_entire_sign_flip_is_equivalent(self):
        source = record([[([0,0,0], [0,0,0])]]*3)
        doc, payload = document([[([0,0,0], [0,0,0])]]*2, fps=2, terminal=False)
        q = [0,0,0,1]
        triples = [([0,0,0,0], q, [0,0,-8,0]), ([0,0,0,0], q, [0,0,0,0])]
        # Midpoint before normalization is [0,0,-.5,1]; expected retail Z is +atan(.5)*2.
        expected_ticks = round(math.atan(.5)*256/math.pi)
        for sign in (1, -1):
            d, p = cubic_channel(doc, payload, 'rotation',
                [[[sign*x for x in row] for row in triple] for triple in triples])
            values, report = self.values(source, d, p)
            self.assertEqual([v['rotation_psx'] for v in values],
                             [[0,0,0], [0,0,expected_ticks*16], [0,0,0]])
            self.assertLessEqual(report['maximum_angular_error_degrees'], 360/512)

    def test_exact_unit_keys_keep_source_euler_branches_and_opaque_bytes(self):
        frames = [[([i,-i,i], r)] for i, r in enumerate(([170,115,190], [51,64,13], [255,255,255]))]
        source = record(frames)
        doc, payload = document(frames, terminal=False)
        for path, width in (('translation', 3), ('rotation', 4)):
            rows = [[t[0],-t[1],t[2]] if path == 'translation' else quaternion(r)
                    for frame in frames for t, r in frame]
            doc, payload = cubic_channel(doc, payload, path,
                                         [([0]*width, row, [0]*width) for row in rows])
        candidate, report = import_animation_glb(source, encode(doc,payload), fps=15)
        self.assertEqual(candidate, source)
        self.assertEqual(report['changed_axes'], 0)

    def test_negative_dot_rotation_keeps_cubic_curve_instead_of_shortest_arc(self):
        source = record([[([0,0,0], [0,0,0])]]*3)
        doc, payload = document([[([0,0,0], [0,0,0])]]*2, fps=2, terminal=False)
        doc, payload = cubic_channel(doc, payload, 'rotation', [
            ([0]*4, quaternion([0,0,0]), [0]*4),
            ([0]*4, quaternion([0,0,192]), [0]*4)])
        values, _ = self.values(source, doc, payload)
        self.assertEqual([v['rotation_psx'][2] for v in values], [0,1536,3072])

    def test_degenerate_rotation_and_sampled_translation_overshoot_reject(self):
        source = record([[([0,0,0], [0,0,0])]]*3)
        doc, payload = document([[([0,0,0], [0,0,0])]]*2, fps=2, terminal=False)
        d, p = cubic_channel(doc, payload, 'rotation', [
            ([0]*4, [0,0,0,1], [0]*4), ([0]*4, [0,0,0,-1], [0]*4)])
        with self.assertRaisesRegex(ImportError, 'zero quaternion'):
            self.values(source, d, p)
        d, p = cubic_channel(doc, payload, 'translation', [
            ([0]*3, [0]*3, [40000,0,0]), ([0]*3, [0]*3, [0]*3)])
        with self.assertRaisesRegex(ImportError, 'before quantization'):
            self.values(source, d, p)

    def test_minimum_keys_triple_counts_unit_keys_and_finite_tangents_reject(self):
        source = record([[([0,0,0], [0,0,0])]]*2)
        doc, payload = document([[([0,0,0], [0,0,0])]]*2, terminal=False)
        d, p = cubic_channel(doc, payload, 'rotation', [
            ([0]*4, [0,0,0,1], [0]*4), ([0]*4, [0,0,0,1], [0]*4)])
        sampler = d['animations'][0]['samplers'][1]
        for kind in ('count', 'one-key', 'unit', 'finite'):
            bad, binary = deepcopy(d), bytearray(p)
            output = bad['accessors'][sampler['output']]
            view = bad['bufferViews'][output['bufferView']]
            if kind == 'count': output['count'] -= 1
            elif kind == 'one-key':
                bad['animations'][0]['channels'] = [bad['animations'][0]['channels'][1]]
                bad['accessors'][sampler['input']]['count'] = 1
                output['count'] = 3
            elif kind == 'unit': struct.pack_into('<4f', binary, view['byteOffset']+16, 0,0,0,2)
            else: struct.pack_into('<f', binary, view['byteOffset'], float('nan'))
            with self.subTest(kind=kind), self.assertRaises(ImportError):
                import_animation_glb(source, encode(bad,bytes(binary)), fps=15)


if __name__ == '__main__':
    unittest.main()
