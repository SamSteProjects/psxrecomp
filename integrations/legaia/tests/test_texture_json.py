import hashlib
import json
import unittest
from copy import deepcopy
from importer.core import ImportError
from importer.texture_json import export_texture_json, import_texture_json
from importer.texture_authoring import inspect_tim_pixel_index
from test_importer_textures import tim, block

class TextureJsonTests(unittest.TestCase):
    def test_roundtrip_and_combined_palette_pixel_preservation(self):
        for bpp in (4,8):
            source=tim(bpp,image=block(0,0,2,2,b"\x10\x32\x54\x76\x98\xba\xdc\xfe"));digest=hashlib.sha256(source).hexdigest()
            encoded=export_texture_json(source)
            self.assertEqual(import_texture_json(source,digest,encoded),source)
            document=json.loads(encoded);document['palette_words'][1]^=1;document['pixel_indices'][0][1]=2
            changed=import_texture_json(source,digest,json.dumps(document).encode())
            offset=inspect_tim_pixel_index(source,1,0)['byte_offset']
            self.assertEqual({i for i,(a,b) in enumerate(zip(source,changed)) if a!=b},{22,offset})
            self.assertEqual(inspect_tim_pixel_index(changed,0,0)['palette_entry'],inspect_tim_pixel_index(source,0,0)['palette_entry'])
            self.assertEqual(inspect_tim_pixel_index(changed,1,0)['palette_entry'],2)

    def test_invalid_source_schema_layout_and_values_rejected(self):
        source=tim();digest=hashlib.sha256(source).hexdigest();encoded=export_texture_json(source);document=json.loads(encoded)
        invalid=[]
        for key,value in [('source_sha256','0'*64),('bpp',8),('height',True),('width',5),('palette_words',[]),('pixel_indices',[])]:
            bad=deepcopy(document);bad[key]=value;invalid.append(json.dumps(bad).encode())
        for field,value in [('palette_words',True),('palette_words',65536),('pixel_indices',True),('pixel_indices',16)]:
            bad=deepcopy(document)
            if field=='pixel_indices':bad[field][0][0]=value
            else:bad[field][0]=value
            invalid.append(json.dumps(bad).encode())
        invalid.extend([encoded.replace(b'"bpp":4',b'"bpp":4,"bpp":4'),b'{',b'\xff'])
        for content in invalid:
            with self.assertRaises(ImportError):import_texture_json(source,digest,content)
        with self.assertRaises(ImportError):export_texture_json(tim(16))
