"""Boot underlay ordering, clipping and foreground ambiguity checks."""
import struct
import unittest
from importer.textures import TextureCatalog, Tim, TimBlock, associate_material

class BootUnderlayTests(unittest.TestCase):
    def test_ordered_underlay_and_foreground_precedence(self):
        catalog = TextureCatalog('fixture','digest')
        block = lambda word: TimBlock(0,0,1,1,struct.pack('<H',word))
        catalog.boot_uploads = [(block(0x1f),{'semantic_id':'early'}),(block(0x7c00),{'semantic_id':'late'})]
        material = {'textured':True,'tpage':256,'clut':0}
        result = associate_material(catalog,material,(0,0,0,0))
        self.assertEqual(result['status'],'address_match')
        self.assertEqual(result['source_ids'],['late'])
        catalog.textures.append((Tim(16,block(0x3e0),None,22),{'semantic_id':'field'}))
        foreground = associate_material(catalog,material,(0,0,0,0))
        self.assertEqual(foreground['source_ids'],['field'])
        self.assertNotEqual(result['rgba'],foreground['rgba'])
        catalog.textures.append((Tim(16,block(0x1f),None,22),{'semantic_id':'other-field'}))
        self.assertEqual(associate_material(catalog,material,(0,0,0,0))['status'],'ambiguous')

    def test_row_patch_clips_at_vram_edge_and_metadata_excludes_pixels(self):
        catalog = TextureCatalog('fixture','digest')
        catalog.boot_uploads = [(TimBlock(960,0,256,1,struct.pack('<256H',*range(256))),{'semantic_id':'row'})]
        material = {'textured':True,'tpage':271,'clut':0}
        self.assertEqual(associate_material(catalog,material,(63,0,63,0))['status'],'address_match')
        self.assertEqual(associate_material(catalog,material,(64,0,64,0))['status'],'missing')
        self.assertNotIn('data',catalog.metadata()['boot_underlay'][0])
