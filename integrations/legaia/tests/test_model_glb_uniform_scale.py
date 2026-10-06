"""Uniform scale affects represented positions and parent translations, not normals."""
from copy import deepcopy
import struct
import unittest

from importer.assets import decode_tmd
from importer.core import ImportError
from importer.model_glb import export_model_glb, import_model_glb
from importer.model_primitives import inspect_model_primitives
from test_model_glb import synthetic, rewrite
from test_model_glb_hierarchy import group
from test_model_glb_normals import lit_source, legacy_profile


def expected_positions(source, factor, delta):
    result = bytearray(source)
    for obj in inspect_model_primitives(source)['objects']:
        at = struct.unpack_from('<I', source, 12 + obj['object_index'] * 28)[0] + 12
        used = {v for row in obj['primitives'] for v in row['vertices']}
        for index in used:
            start = at + index * 8
            xyz = struct.unpack_from('<3h', source, start)
            struct.pack_into('<3h', result, start, *(round(v*factor+d) for v,d in zip(xyz, delta)))
    return bytes(result)


class UniformModelScale(unittest.TestCase):
    def test_nested_trs_scale_and_translation_keep_raw_normals_padding_and_packets(self):
        source = lit_source(0x16)
        glb, profile = export_model_glb(source, decode_tmd(source))
        def edit(doc, binary):
            doc['nodes'][0].update(scale=[3,3,3], translation=[1,-2,3])
            group(doc, dict(scale=[2,2,2], translation=[4,-5,6]))
        self.assertEqual(import_model_glb(source, rewrite(glb, edit), profile)[0],
                         expected_positions(source, 6, [6,9,12]))
        self.assertEqual(import_model_glb(source, rewrite(glb, edit), legacy_profile(profile, 3))[0],
                         expected_positions(source, 6, [6,9,12]))

    def test_matrix_scale_and_trs_scale_compose_with_rotation(self):
        source = synthetic(((0x22,),))
        glb, profile = export_model_glb(source, decode_tmd(source))
        def edit(doc, binary):
            doc['nodes'][0].update(scale=[.5,.5,.5], translation=[2,-3,4])
            group(doc, dict(matrix=[-2,0,0,0,0,-2,0,0,0,0,2,0,10,-20,30,1]))
        expected = bytearray(source)
        at = struct.unpack_from('<I', source, 12)[0] + 12
        used = {v for row in inspect_model_primitives(source)['objects'][0]['primitives'] for v in row['vertices']}
        for i in used:
            x,y,z = struct.unpack_from('<3h', source, at+i*8)
            struct.pack_into('<3h', expected, at+i*8, -x+6,-y+14,z+38)
        self.assertEqual(import_model_glb(source, rewrite(glb, edit), profile)[0], bytes(expected))

    def test_fractional_scale_reports_rounding_and_zero_unused_slots_remain(self):
        source = synthetic(((0x22,),))
        glb, profile = export_model_glb(source, decode_tmd(source))
        content = rewrite(glb, lambda d,b: group(d, dict(scale=[.25,.25,.25])))
        candidate, report = import_model_glb(source, content, profile)
        self.assertEqual(candidate, expected_positions(source, .25, [0,0,0]))
        self.assertEqual(report['quantization']['vertex_max_error'], .5)
        self.assertGreater(report['quantization']['quantized_component_count'], 0)

    def test_bad_local_and_composed_scales_shear_and_matrix_trs_reject(self):
        source = synthetic(((0x22,),))
        glb, profile = export_model_glb(source, decode_tmd(source))
        invalid = [[0]*3, [True]*3, [1e300]*3, [1e-10]*3, [1025]*3, [-1025]*3]
        for scale in invalid:
            with self.subTest(scale=scale), self.assertRaises(ImportError):
                import_model_glb(source, rewrite(glb, lambda d,b: group(d, dict(scale=scale))), profile)
        for matrix in [[2,0,0,0,1,2,0,0,0,0,2,0,0,0,0,1]]:
            with self.subTest(matrix=matrix), self.assertRaises(ImportError):
                import_model_glb(source, rewrite(glb, lambda d,b: group(d, dict(matrix=matrix))), profile)
        for scale in (64, 1/64):
            def excessive(doc, binary):
                doc['nodes'][0]['scale']=[scale]*3
                group(doc, dict(scale=[scale]*3))
            with self.assertRaises(ImportError): import_model_glb(source, rewrite(glb, excessive), profile)

    def test_input_metadata_is_not_mutated(self):
        from importer.model_glb_transforms import static_model_hierarchy
        doc=dict(nodes=[dict(name='object-0', scale=[2,2,2])], scenes=[dict(nodes=[0])], scene=0)
        before=deepcopy(doc)
        _,poses=static_model_hierarchy(doc, 1)
        self.assertEqual(poses[0].position([1,2,3]), [2,4,6])
        self.assertEqual(doc, before)


if __name__ == '__main__':
    unittest.main()
