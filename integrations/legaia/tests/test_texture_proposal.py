import hashlib
import json
import unittest
from importer.texture_authoring import texture_payload_changes
from importer.texture_json import export_texture_json, import_texture_json
from test_importer_textures import tim, block

class TextureProposalTests(unittest.TestCase):
    def test_exact_counts_and_pixel_locations(self):
        for bpp in (4,8):
            source=tim(bpp,image=block(0,0,2,2,b'\x10\x32\x54\x76\x98\xba\xdc\xfe'))
            data=json.loads(export_texture_json(source))
            data['palette_words'][1]^=1
            data['pixel_indices'][1][1]=(data['pixel_indices'][1][1]+1)%(1<<bpp)
            candidate=import_texture_json(source,hashlib.sha256(source).hexdigest(),json.dumps(data).encode())
            result=texture_payload_changes(source,candidate)
            self.assertEqual((result['palette_words_changed'],result['pixel_indices_changed'],result['image_bytes_changed']),(1,1,1))
            self.assertEqual(result['changes'][1]['x'],1)
            self.assertEqual(result['changes'][1]['y'],1)
            self.assertFalse(result['changes_truncated'])
            self.assertEqual(texture_payload_changes(candidate,candidate)['total_change_count'],0)

    def test_bounded_details_complete_counts_and_direct_color(self):
        source=tim(image=block(0,0,80,2,bytes(320)))
        candidate=source[:-320]+bytes([255])*320
        result=texture_payload_changes(source,candidate)
        self.assertEqual(result['pixel_indices_changed'],640)
        self.assertEqual(len(result['changes']),256)
        self.assertTrue(result['changes_truncated'])
        source=tim(16)
        result=texture_payload_changes(source,source[:-1]+b'\xff')
        self.assertIsNone(result['pixel_indices_changed'])
        self.assertEqual(result['image_bytes_changed'],1)
