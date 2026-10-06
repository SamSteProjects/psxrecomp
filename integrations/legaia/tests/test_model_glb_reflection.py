"""Independent native packet winding and corner ownership for signed GLB scales."""
from copy import deepcopy
import math
import struct
import unittest
from importer.assets import decode_tmd
from importer.core import ImportError
from importer.model_glb import export_model_glb, import_model_glb
from importer.model_glb_transforms import static_model_hierarchy
from importer.model_primitives import inspect_model_primitives
from test_model_primitives import synthetic, TRI_VI, QUAD_VI
from test_model_glb import rewrite
from test_model_glb_hierarchy import group
from test_model_glb_normals import legacy_profile


def mirrored_native(source, scales):
    """Pack expected vectors/corners directly from the native descriptor layouts."""
    result = bytearray(source)
    for obj in inspect_model_primitives(source)['objects']:
        identity = obj['object_index']
        va, _, na, _ = struct.unpack_from('<4I', source, 12 + identity * 28)
        used_vertices, used_normals = set(), set()
        for primitive in obj['primitives']:
            at, flags = primitive['byte_offset'], primitive['flags']
            family, quad = (flags - 0x10) // 4, bool(flags & 2)
            corners = 4 if quad else 3
            gouraud, textured, baked = family in (1, 3, 5), family in (0, 1, 4, 5), family >= 2
            vertex = (QUAD_VI if quad else TRI_VI)[family]
            used_vertices.update(struct.unpack_from(f'<{corners}H', source, at + vertex)[n] // 8 for n in range(corners))
            slots = [(vertex, 2, corners)]
            if textured:
                uv = 0 if family < 2 else (corners * 4 if gouraud else 4)
                # Native fourth UV occupies +10, not +12. Its material words
                # and every fourth RGB byte retain their original locations.
                offsets = (0, 4, 8, 10)[:corners]
                if math.prod(scales) < 0:
                    for dst, src in enumerate((0, 2, 1, 3)[:corners]):
                        result[at+uv+offsets[dst]:at+uv+offsets[dst]+2] = source[at+uv+offsets[src]:at+uv+offsets[src]+2]
            if baked and gouraud:
                for dst, src in enumerate((0, 2, 1, 3)[:corners]):
                    if math.prod(scales) < 0:
                        result[at+dst*4:at+dst*4+3] = source[at+src*4:at+src*4+3]
            if not baked:
                normal = (20 if quad else 18) if gouraud else (20 if quad else 12)
                count = corners if gouraud else 1
                used_normals.update(v // 8 for v in struct.unpack_from(f'<{count}H', source, at + normal))
                if gouraud: slots.append((normal, 2, corners))
            if math.prod(scales) < 0:
                for start, width, count in slots:
                    for dst, src in enumerate((0, 2, 1, 3)[:count]):
                        result[at+start+dst*width:at+start+(dst+1)*width] = source[at+start+src*width:at+start+(src+1)*width]
        for index in used_vertices:
            at = va + 12 + index * 8
            xyz = struct.unpack_from('<3h', source, at)
            struct.pack_into('<3h', result, at, *(round(v*s) for v,s in zip(xyz, scales)))
        for index in used_normals:
            at = na + 12 + index * 8
            xyz = struct.unpack_from('<3h', source, at)
            divided = [v/s for v,s in zip(xyz, scales)]
            factor = math.hypot(*xyz) / math.hypot(*divided) if any(xyz) else 0
            struct.pack_into('<3h', result, at, *(round(v*factor) for v in divided))
    return bytes(result)


class ModelReflection(unittest.TestCase):
    def test_all_24_packet_families_match_independent_native_pack(self):
        for flags in range(0x10, 0x28):
            source = synthetic(((flags,),))
            glb, profile = export_model_glb(source, decode_tmd(source))
            with self.subTest(flags=hex(flags)):
                candidate, report = import_model_glb(source, rewrite(glb, lambda d,b: group(d, dict(scale=[-2,1,.5]))), profile)
                self.assertEqual(candidate, mirrored_native(source, [-2,1,.5]))
                self.assertGreater(report['changed_field_count'], 0)

    def test_matrix_trs_and_nested_reflections_use_composed_orientation(self):
        source = synthetic(((0x16, 0x26),))
        glb, profile = export_model_glb(source, decode_tmd(source))
        for transform in (dict(scale=[-1,1,1]), dict(matrix=[-1,0,0,0,0,1,0,0,0,0,1,0,0,0,0,1])):
            self.assertEqual(import_model_glb(source, rewrite(glb, lambda d,b: group(d,transform)), profile)[0], mirrored_native(source,[-1,1,1]))
        def cancel(doc,binary):
            group(doc, dict(scale=[-1,1,1])); group(doc, dict(scale=[-1,1,1]))
        self.assertEqual(import_model_glb(source, rewrite(glb,cancel), profile)[0], source)
        for scale in ([-1,-1,1],[-1,-1,-1],[1,-1,1],[1,1,-1]):
            self.assertEqual(import_model_glb(source,rewrite(glb,lambda d,b: group(d,dict(scale=scale))),profile)[0],mirrored_native(source,scale))

    def test_mixed_object_reflection_preserves_other_object_and_legacy_rejects(self):
        source = synthetic(((0x26,), (0x16,)))
        glb, profile = export_model_glb(source, decode_tmd(source))
        content = rewrite(glb, lambda d,b: d['nodes'][0].update(scale=[-1,1,1]))
        candidate, _ = import_model_glb(source, content, profile)
        original, changed = inspect_model_primitives(source), inspect_model_primitives(candidate)
        self.assertEqual(original['objects'][1], changed['objects'][1])
        # Entire second object's packets and vector storage are untouched.
        begin = original['objects'][1]['primitives'][0]['byte_offset'] - 8
        self.assertEqual(candidate[begin:], source[begin:])
        for version in range(1,6):
            if version <= 3:
                legacy = legacy_profile(profile, version)
            else:
                legacy = deepcopy(profile); legacy['schema_version'] = f'legaia.model-glb-profile.v{version}'
                del legacy['attributes']['material']; legacy['imported_fields'].remove('primitive_material_words')
                if version == 4:
                    del legacy['attributes']['normal_index']; legacy['imported_fields'].remove('primitive_normal_indices')
            with self.subTest(version=version), self.assertRaisesRegex(ImportError, 'current profile'):
                import_model_glb(source, content, legacy)

    def test_nondegenerate_quad_restores_front_face_orientation(self):
        source = bytearray(synthetic(((0x26,),)))
        va = struct.unpack_from('<I', source, 12)[0] + 12
        for index, xyz in enumerate(((0,0,0),(10,0,0),(0,10,0),(10,10,0))):
            struct.pack_into('<3h', source, va+index*8, *xyz)
        source = bytes(source); glb, profile = export_model_glb(source, decode_tmd(source))
        candidate, _ = import_model_glb(source, rewrite(glb,lambda d,b: group(d,dict(scale=[-1,1,1]))),profile)
        before, after = decode_tmd(source), decode_tmd(candidate)
        def cross_z(preview, triangle):
            a,b,c = [preview['vertices'][index] for index in triangle]
            return (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])
        self.assertTrue(all(cross_z(before,t)>0 for t in before['triangles']))
        self.assertTrue(all(cross_z(after,t)>0 for t in after['triangles']))
        self.assertEqual(candidate, mirrored_native(source,[-1,1,1]))

    def test_signed_inverse_transpose_is_orthogonal_and_preserves_magnitude(self):
        doc=dict(nodes=[dict(name='object-0',scale=[-2,1,.5])],scenes=[dict(nodes=[0])],scene=0)
        before=deepcopy(doc);_, poses=static_model_hierarchy(doc,1);pose=poses[0]
        self.assertTrue(pose.reflected);self.assertEqual(pose.scale_bounds,(.5,2))
        normal=pose.normal([1,1,1]);factor=math.sqrt(3/5.25)
        for actual, expected in zip(normal,[-.5*factor,factor,2*factor]):self.assertAlmostEqual(actual,expected,places=12)
        for tangent in ([1,-1,0],[0,1,-1]):
            self.assertAlmostEqual(sum(a*b for a,b in zip(normal,pose.position(tangent))),0,places=12)
        self.assertAlmostEqual(math.hypot(*normal),math.sqrt(3),places=12)
        self.assertEqual(doc,before)


if __name__ == '__main__': unittest.main()
