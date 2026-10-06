"""Analytic normal directions and independently packed nonuniform native edits."""
import math
import struct
import unittest

from importer.assets import decode_tmd
from importer.core import ImportError
from importer.model_glb import export_model_glb, import_model_glb
from importer.model_glb_transforms import static_model_hierarchy
from importer.model_primitives import inspect_model_primitives
from importer.model_normal_references import _normal_field_locations
from test_model_glb import rewrite
from test_model_glb_hierarchy import group
from test_model_glb_normals import lit_source, legacy_profile


def expected(source, scales):
    result = bytearray(source)
    inspection = inspect_model_primitives(source)
    used_normals = {}
    for field,_ in _normal_field_locations(source, inspection):
        used_normals.setdefault(field['object_index'],set()).add(struct.unpack_from('<H',source,field['byte_offset'])[0]//8)
    for obj in inspection['objects']:
        identity = obj['object_index']
        va,_,na,_ = struct.unpack_from('<4I',source,12+identity*28)
        used_vertices = {v for row in obj['primitives'] for v in row['vertices']}
        for index in used_vertices:
            at = va + 12 + index*8
            point = struct.unpack_from('<3h',source,at)
            struct.pack_into('<3h',result,at,*(round(v*s) for v,s in zip(point,scales)))
        for index in used_normals.get(identity,set()):
            at = na + 12 + index*8
            normal = struct.unpack_from('<3h',source,at)
            divided = [v/s for v,s in zip(normal,scales)]
            before,after = math.hypot(*normal), math.hypot(*divided)
            quantized = [round(v*before/after) for v in divided] if before else [0]*3
            struct.pack_into('<3h',result,at,*quantized)
    return bytes(result)


class NonuniformModelScale(unittest.TestCase):
    def test_native_positions_and_normals_match_independent_axis_division(self):
        source = lit_source(0x16)
        glb, profile = export_model_glb(source,decode_tmd(source))
        scales = [2,1,.5]
        for kind in ('trs','matrix'):
            def edit(doc,binary):
                transform = dict(scale=scales) if kind=='trs' else dict(matrix=[2,0,0,0,0,1,0,0,0,0,.5,0,0,0,0,1])
                group(doc,transform)
            content = rewrite(glb,edit)
            candidate, report = import_model_glb(source,content,profile)
            self.assertEqual(candidate, expected(source,scales))
            self.assertGreater(report['changed_field_count'],0)
            with self.assertRaises(ImportError):
                import_model_glb(source,content,legacy_profile(profile,3))

    def test_inverse_transpose_preserves_magnitude_and_surface_orthogonality(self):
        doc=dict(nodes=[dict(name='object-0',scale=[2,1,.5])],scenes=[dict(nodes=[0])],scene=0)
        _,poses=static_model_hierarchy(doc,1)
        pose=poses[0];normal=pose.normal([1,1,1]);length=math.sqrt(3/5.25)
        for actual,wanted in zip(normal,[.5*length,length,2*length]):self.assertAlmostEqual(actual,wanted,places=12)
        self.assertAlmostEqual(math.hypot(*normal),math.sqrt(3),places=12)
        for tangent in ([1,-1,0],[0,1,-1]):
            self.assertAlmostEqual(sum(a*b for a,b in zip(normal,pose.position(tangent))),0,places=12)
        self.assertEqual(pose.normal([0,0,0]),[0,0,0])

    def test_rotated_child_under_anisotropic_parent_composes_full_linear_matrix(self):
        c=math.sqrt(.5)
        doc=dict(nodes=[dict(name='object-0',rotation=[0,0,math.sin(math.pi/8),math.cos(math.pi/8)],scale=[1,3,1]),
                        dict(name='Parent',scale=[2,1,1],children=[0])],scenes=[dict(nodes=[1])],scene=0)
        _,poses=static_model_hierarchy(doc,1);pose=poses[0]
        point=pose.position([2,3,4])
        for actual,wanted in zip(point,[-14*c,11*c,4]):self.assertAlmostEqual(actual,wanted,places=12)
        raw=[c/3,4*c/3,0];factor=math.sqrt(2)/math.hypot(*raw)
        normal=pose.normal([1,1,0])
        for actual,wanted in zip(normal,[v*factor for v in raw]):self.assertAlmostEqual(actual,wanted,places=12)
        self.assertAlmostEqual(sum(a*b for a,b in zip(normal,pose.position([1,-1,0]))),0,places=12)

    def test_legacy_unlit_positions_and_native_normal_overflow_guard(self):
        from test_model_glb import synthetic
        source=synthetic(((0x22,),));glb,profile=export_model_glb(source,decode_tmd(source))
        content=rewrite(glb,lambda d,b:group(d,dict(scale=[2,1,.5])))
        self.assertEqual(import_model_glb(source,content,legacy_profile(profile,3))[0],expected(source,[2,1,.5]))
        source=bytearray(lit_source(0x16));na=struct.unpack_from('<I',source,20)[0]+12
        for i in range(struct.unpack_from('<I',source,24)[0]):struct.pack_into('<3h',source,na+i*8,30000,30000,30000)
        source=bytes(source);glb,profile=export_model_glb(source,decode_tmd(source));content=rewrite(glb,lambda d,b:group(d,dict(scale=[.01,1,1])))
        with self.assertRaises(ImportError):import_model_glb(source,content,profile)


if __name__=='__main__':unittest.main()
