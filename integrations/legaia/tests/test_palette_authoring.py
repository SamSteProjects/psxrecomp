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

    def test_pixel_indices_preserve_neighbours_palettes_and_decoded_pixels(self):
        from importer.texture_authoring import inspect_tim_pixel_index, patch_tim_pixel_index
        for bpp in (4,8):
            count=1 << bpp
            source=tim(bpp,image=block(0,0,2,2,b'\x10\x32\x54\x76\x98\xba\xdc\xfe'),palette=block(0,100,count,1,list(range(count))))
            digest=hashlib.sha256(source).hexdigest()
            baseline=decode_tim(source)['rgba']
            for x,y in ((0,0),(1,0),(0,1),( (4 if bpp==4 else 2)*2-1,1)):
                current=inspect_tim_pixel_index(source,x,y)
                self.assertEqual(patch_tim_pixel_index(source,digest,x,y,current['palette_entry']),source)
                for value in range(count):
                    changed=patch_tim_pixel_index(source,digest,x,y,value)
                    self.assertEqual(changed[:current['byte_offset']],source[:current['byte_offset']])
                    self.assertEqual(changed[current['byte_offset']+1:],source[current['byte_offset']+1:])
                    pixels=decode_tim(changed)['rgba'];start=(y*current['width']+x)*4
                    self.assertEqual(pixels[:start],baseline[:start])
                    self.assertEqual(pixels[start+4:],baseline[start+4:])
                    self.assertEqual(inspect_tim_pixel_index(changed,x,y)['palette_entry'],value)
            for x,y,value in ((True,0,1),(-1,0,1),(0,2,1),(0,0,True),(0,0,count)):
                with self.assertRaises(ImportError):patch_tim_pixel_index(source,digest,x,y,value)
            with self.assertRaises(ImportError):patch_tim_pixel_index(source,'0'*64,0,0,1)

    def test_invalid_binding_layout_and_fields_rejected(self):
        source=tim();digest=hashlib.sha256(source).hexdigest()
        for palette,entry,word in ((True,0,1),(1,0,1),(0,16,1),(0,True,1),(0,0,True),(0,0,-1),(0,0,65536),(0,0,1.5)):
            with self.assertRaises(ImportError):patch_tim_palette_word(source,digest,palette,entry,word)
        for content,sha in ((source,'0'*64),(tim(16),hashlib.sha256(tim(16)).hexdigest()),(source+b'x',hashlib.sha256(source+b'x').hexdigest())):
            with self.assertRaises(ImportError):patch_tim_palette_word(content,sha,0,0,1)
