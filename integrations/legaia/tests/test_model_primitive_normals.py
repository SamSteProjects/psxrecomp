from hashlib import sha256
import struct
import unittest
from importer.core import ImportError
from importer.model_primitives import inspect_model_primitives, patch_model_primitives
from test_model_primitives import synthetic

class PrimitiveNormalTests(unittest.TestCase):
    def test_flat_gouraud_all_layouts_exact_word_ownership(self):
        for flags in [0x10,0x11,0x12,0x13,0x14,0x15,0x16,0x17]:
            with self.subTest(flags=flags):
                source=synthetic(((flags,),(0x20,)),count=1)
                info=inspect_model_primitives(source,include_normal_references=True)
                row=info['objects'][0]['primitives'][0]
                indices=[3]*len(row['normal_indices'])
                candidate,audit=patch_model_primitives(source,sha256(source).hexdigest(),[dict(object_index=0,primitive_index=0,normal_indices=indices)])
                expected=bytearray(source)
                relative=(18 if row['corner_count']==3 else 20) if row['gouraud'] else (12 if row['corner_count']==3 else 20)
                struct.pack_into(f'<{len(indices)}H',expected,row['byte_offset']+relative,*[24]*len(indices))
                self.assertEqual(candidate,bytes(expected))
                self.assertTrue(all(r['field']=='normal_index' for r in audit))
                self.assertEqual(inspect_model_primitives(candidate,include_normal_references=True)['objects'][0]['primitives'][0]['normal_indices'],indices)
    def test_invalid_layout_domain_and_stale_hash(self):
        source=synthetic(((0x12,),),count=1)
        digest=sha256(source).hexdigest()
        for values in [[True],[-1],[4],[8192],[0,1],[],None]:
            with self.subTest(values=values),self.assertRaises(ImportError):
                patch_model_primitives(source,digest,[dict(object_index=0,primitive_index=0,normal_indices=values)])
        with self.assertRaises(ImportError):patch_model_primitives(source,'0'*64,[dict(object_index=0,primitive_index=0,normal_indices=[1])])
        unlit=synthetic(((0x20,),),count=1)
        self.assertIsNone(inspect_model_primitives(unlit,include_normal_references=True)['objects'][0]['primitives'][0]['normal_indices'])
        with self.assertRaises(ImportError):patch_model_primitives(unlit,sha256(unlit).hexdigest(),[dict(object_index=0,primitive_index=0,normal_indices=[0])])
