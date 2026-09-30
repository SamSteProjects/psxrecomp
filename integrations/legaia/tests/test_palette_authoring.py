import hashlib
import unittest
from importer.core import ImportError
from importer.texture_authoring import patch_tim_palette_word
from importer.textures import decode_tim
from test_importer_textures import tim, block

class PaletteAuthoringTests(unittest.TestCase):
    def test_exact_word_preserves_headers_image_and_other_palette(self):
        for bpp in (4, 8):
            count = 1 << bpp
            source = tim(bpp, palette=block(0,100,count,2,list(range(count))*2))
            digest = hashlib.sha256(source).hexdigest()
            self.assertEqual(patch_tim_palette_word(source,digest,1,1,1),source)
            changed = patch_tim_palette_word(source,digest,1,1,0xFFFF)
            offset = 20 + (count + 1)*2
            self.assertEqual(changed[:offset],source[:offset])
            self.assertEqual(changed[offset+2:],source[offset+2:])
            self.assertEqual(decode_tim(changed,0),decode_tim(source,0))
            self.assertEqual(patch_tim_palette_word(changed,hashlib.sha256(changed).hexdigest(),1,1,1),source)

    def test_invalid_binding_layout_and_fields_rejected(self):
        source=tim();digest=hashlib.sha256(source).hexdigest()
        for palette,entry,word in ((True,0,1),(1,0,1),(0,16,1),(0,True,1),(0,0,True),(0,0,-1),(0,0,65536),(0,0,1.5)):
            with self.assertRaises(ImportError):patch_tim_palette_word(source,digest,palette,entry,word)
        for content,sha in ((source,'0'*64),(tim(16),hashlib.sha256(tim(16)).hexdigest()),(source+b'x',hashlib.sha256(source+b'x').hexdigest())):
            with self.assertRaises(ImportError):patch_tim_palette_word(content,sha,0,0,1)
