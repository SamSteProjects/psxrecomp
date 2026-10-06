"""Rigid node hierarchy bakes exact native positions and raw normal vectors."""
import struct
import unittest

from importer.assets import decode_tmd
from importer.core import ImportError
from importer.model_glb import export_model_glb, import_model_glb
from importer.model_primitives import inspect_model_primitives
from test_model_glb import synthetic, rewrite
from test_model_glb_normals import lit_source, legacy_profile


def group(doc, transform):
    doc['nodes'].append(dict(name='External parent', children=list(doc['scenes'][0]['nodes']), **transform))
    doc['scenes'][0]['nodes'] = [len(doc['nodes']) - 1]


def translated(source, delta):
    result = bytearray(source)
    count = struct.unpack_from('<I', source, 8)[0]
    for obj in range(count):
        used = {v for row in inspect_model_primitives(source)['objects'][obj]['primitives'] for v in row['vertices']}
        at, length = struct.unpack_from('<2I', source, 12 + obj * 28)
        for i in used:
            start = 12 + at + 8 * i
            xyz = struct.unpack_from('<3h', source, start)
            struct.pack_into('<3h', result, start, *(a+b for a,b in zip(xyz, delta)))
    return bytes(result)


class ModelHierarchy(unittest.TestCase):
    def test_nested_group_and_object_translation_preserve_all_other_bytes(self):
        source = synthetic(((0x22,), (0x26,)))
        glb, profile = export_model_glb(source, decode_tmd(source))
        def edit(doc, binary):
            for node in doc['nodes']: node['translation'] = [1, -2, 3]
            group(doc, dict(translation=[4, -5, 6]))
            group(doc, dict(translation=[7, -8, 9]))
        candidate, _ = import_model_glb(source, rewrite(glb, edit), profile)
        self.assertEqual(candidate, translated(source, [12, 15, 18]))

    def test_rigid_matrix_rotates_positions_and_stored_normals_without_normalizing(self):
        source = lit_source(0x16)
        glb, profile = export_model_glb(source, decode_tmd(source))
        expected = bytearray(source)
        va, vc, na, nc = struct.unpack_from('<4I', source, 12)
        # glTF +90 Z: [x,-y,z] -> [y,x,z], native -> [y,-x,z].
        used = {v for row in inspect_model_primitives(source)['objects'][0]['primitives'] for v in row['vertices']}
        for at, slots in ((va, used), (na, range(nc))):
            for i in slots:
                start = at + 12 + i * 8
                x,y,z = struct.unpack_from('<3h', source, start)
                struct.pack_into('<3h', expected, start, y,-x,z)
        def edit(doc, binary):
            group(doc, dict(matrix=[0,1,0,0,-1,0,0,0,0,0,1,0,0,0,0,1]))
        candidate, report = import_model_glb(source, rewrite(glb, edit), profile)
        self.assertEqual(candidate, bytes(expected))
        self.assertLess(report['quantization']['normal_max_error'], 1e-9)
        rotation_only = rewrite(glb, edit)
        with self.assertRaises(ImportError):
            import_model_glb(source, rotation_only, legacy_profile(profile, 3))

    def test_parent_rotation_then_child_translation_has_correct_order(self):
        source = synthetic(((0x22,),))
        glb, profile = export_model_glb(source, decode_tmd(source))
        def edit(doc, binary):
            doc['nodes'][0]['translation'] = [2, 3, 4]
            group(doc, dict(rotation=[0,0,0,1]))
            group(doc, dict(rotation=[0,0,1,0], translation=[10,20,30]))
        # 180 Z rotation plus parent T: glTF [-x+8,-y+17,z+34].
        expected = bytearray(source)
        va, vc = struct.unpack_from('<2I', source, 12)
        used = {v for row in inspect_model_primitives(source)['objects'][0]['primitives'] for v in row['vertices']}
        for i in used:
            at = va + 12 + i * 8
            x,y,z = struct.unpack_from('<3h', source, at)
            struct.pack_into('<3h', expected, at, -x+8,-y-17,z+34)
        self.assertEqual(import_model_glb(source, rewrite(glb, edit), profile)[0], bytes(expected))
        # Unlit packets have no stored normal operands to lose in legacy profiles.
        self.assertEqual(import_model_glb(source, rewrite(glb, edit), legacy_profile(profile, 3))[0], bytes(expected))

    def test_malformed_hierarchy_nonrigid_or_overflow_transforms_reject(self):
        source = synthetic(((0x22,),))
        glb, profile = export_model_glb(source, decode_tmd(source))
        for transform in [dict(scale=[0,1,1]), dict(rotation=[0,0,0,0]),
                          dict(translation=[True,0,0]), dict(translation=[1e300,0,0]),
                          dict(matrix=[1,0,0,0,1,1,0,0,0,0,1,0,0,0,0,1]),
                          dict(matrix=[1,0,0,0,0,1,0,0,0,0,1,0,0,0,0,1],translation=[0,0,0])]:
            with self.subTest(transform=transform), self.assertRaises(ImportError):
                import_model_glb(source, rewrite(glb, lambda d,b: group(d, transform)), profile)
        def detached(d,b): d['nodes'].append(dict(name='Detached'))
        def cycle(d,b): d['nodes'][0]['children']=[0]
        def duplicate(d,b): group(d, dict()); d['nodes'][-1]['children']=[0,0]
        def hidden_mesh(d,b): group(d, dict()); d['nodes'][-1]['mesh']=0
        for edit in (detached,cycle,duplicate,hidden_mesh):
            with self.subTest(edit=edit.__name__), self.assertRaises(ImportError):
                import_model_glb(source, rewrite(glb, edit), profile)


if __name__ == '__main__':
    unittest.main()
