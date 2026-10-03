"""Source normal lookup/corner ordering without inferred lighting or geometry changes."""
from copy import deepcopy
import struct
import unittest

from importer.assets import decode_tmd
from importer.core import ImportError
from test_model_primitives import synthetic


def header(data):
    return struct.unpack_from('<7I',data,12)


class ModelPreviewNormalTests(unittest.TestCase):
    def test_lit_flat_gouraud_triangle_quad_order_signed_vectors(self):
        normals=[[-32768,1,32767],[3,-5,7],[-11,13,-17],[19,-23,29]]
        for flags in range(0x10,0x18):
            with self.subTest(flags=flags):
                data=bytearray(synthetic(((flags,),),count=1));normal=header(data)[2]+12
                for i,vector in enumerate(normals):struct.pack_into('<3h',data,normal+i*8,*vector)
                before=bytes(data);preview=decode_tmd(before)
                corners=4 if flags&2 else 3;gouraud=(flags-0x10)//4==1
                source=normals[:corners] if gouraud else [normals[0]]*corners
                order=[(0,1,2),(1,3,2)] if corners==4 else [(0,1,2)]
                self.assertEqual(preview['triangle_normals'],[[source[n] for n in triangle] for triangle in order])
                self.assertEqual(preview['normal_preview']['status'],'source_unposed')
                self.assertEqual(preview['normal_preview']['coordinate_system'],'retail_tmd_object_local')
                self.assertEqual(bytes(data),before)

    def test_unlit_never_interprets_color_or_pad_as_normal(self):
        for flags in range(0x18,0x28):
            with self.subTest(flags=flags):
                preview=decode_tmd(synthetic(((flags,),),count=1))
                self.assertEqual(preview['triangle_normals'],[None]*len(preview['triangles']))

    def test_invalid_normal_byte_offsets_withdraw_complete_source_primitive(self):
        for raw_ref in (1,32,65528):
            data=bytearray(synthetic(((0x16,),),count=1));primitive=header(data)[4]+12
            # Gouraud quad corner3 is used only in the second emitted triangle.
            struct.pack_into('<H',data,primitive+8+20+3*2,raw_ref)
            p=decode_tmd(bytes(data));self.assertEqual(p['triangle_normals'],[None,None])
            self.assertEqual(p['normal_preview']['invalid_triangles'],2)
            self.assertEqual(p['triangles'],[[0,1,2],[1,3,2]])

    def test_zero_vectors_retained_padding_ignored_and_aliases_detached(self):
        data=bytearray(synthetic(((0x12,),),count=1));normal=header(data)[2]+12
        struct.pack_into('<3h',data,normal,0,0,0);struct.pack_into('<H',data,normal+6,0xffff)
        before=bytes(data);p=decode_tmd(before)
        self.assertEqual(p['triangle_normals'],[[[0,0,0]]*3,[[0,0,0]]*3])
        p['triangle_normals'][0][0][0]=12
        self.assertEqual(p['triangle_normals'][1],[[0,0,0]]*3)
        self.assertEqual(bytes(data),before)
        self.assertEqual(p['normal_preview']['zero_corners'],6)

    def test_short_packet_normal_operands_preserve_qualified_geometry(self):
        original=synthetic(((0x14,),),count=1);v,nv,n,nn,prim,count,opaque=header(original);at=prim+12
        # GT3 vertex words end at18, but its three normal words require24 bytes.
        data=bytearray(original[:at+8]+original[at+8:at+28]+original[at+32:at+52]+original[at+56:])
        data[at+5]=5
        struct.pack_into('<7I',data,12,v-8,nv,n-8,nn,prim,count,opaque)
        p=decode_tmd(bytes(data));before=decode_tmd(original)
        self.assertEqual(p['triangle_normals'],[None])
        self.assertEqual(p['normal_preview']['invalid_triangles'],1)
        self.assertEqual(p['diagnostics'][0]['reason'],'normal_operands_exceed_stride')
        for key in ('vertices','triangles','triangle_colors','triangle_uvs','materials'):
            self.assertEqual(p[key],before[key])

    def test_normal_xyz_and_reference_changes_preserve_other_preview_fields(self):
        data=synthetic(((0x10,0x16),),count=1);baseline=decode_tmd(data);normal=header(data)[2]+12
        edited=bytearray(data);struct.pack_into('<h',edited,normal,123)
        vector_preview=decode_tmd(bytes(edited))
        self.assertNotEqual(vector_preview['triangle_normals'],baseline['triangle_normals'])
        for key in ('vertices','triangles','triangle_colors','triangle_uvs','triangle_materials','materials','objects','bounds'):
            self.assertEqual(vector_preview[key],baseline[key])
        changed=bytearray(data);primitive=header(data)[4]+12;struct.pack_into('<H',changed,primitive+8+12,8)
        rewired=decode_tmd(bytes(changed));self.assertNotEqual(rewired['triangle_normals'],baseline['triangle_normals'])
        for key in ('vertices','triangles','triangle_colors','triangle_uvs','triangle_materials','materials','objects','bounds'):
            self.assertEqual(rewired[key],baseline[key])

    def test_malformed_normal_table_span_remains_a_source_rejection(self):
        data=bytearray(synthetic(((0x10,),),count=1));struct.pack_into('<I',data,12+8,len(data))
        with self.assertRaises(ImportError):decode_tmd(bytes(data))


if __name__=='__main__':unittest.main()
