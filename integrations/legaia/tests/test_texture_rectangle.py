import hashlib
import unittest
from importer.core import ImportError
from importer.texture_authoring import patch_tim_index_rectangle,inspect_tim_pixel_index,copy_tim_index_rectangle
from test_importer_textures import tim,block

class TextureRectangleTests(unittest.TestCase):
    def test_copy_overlaps_use_original_indices_and_preserve_outside_pixels(self):
        for bpp in (4,8):
            source=tim(bpp,image=block(0,0,3,3,bytes(range(18))))
            digest=hashlib.sha256(source).hexdigest()
            width=12 if bpp==4 else 6
            for sx,sy,x,y,w,h in [(0,0,1,0,4,2),(1,0,0,0,4,2),(0,0,0,1,width,2),(0,1,0,0,width,2),(1,0,3,2,2,1)]:
                candidate=copy_tim_index_rectangle(source,digest,sx,sy,x,y,w,h)
                self.assertEqual(candidate[:32+(1<<bpp)*2],source[:32+(1<<bpp)*2])
                for row in range(3):
                    for col in range(width):
                        before_x,before_y=(sx+col-x,sy+row-y) if x<=col<x+w and y<=row<y+h else (col,row)
                        self.assertEqual(inspect_tim_pixel_index(candidate,col,row)['palette_entry'],inspect_tim_pixel_index(source,before_x,before_y)['palette_entry'])
            self.assertEqual(copy_tim_index_rectangle(source,digest,0,0,0,0,width,3),source)

    def test_copy_rejects_stale_source_and_invalid_rectangles(self):
        source=tim();digest=hashlib.sha256(source).hexdigest()
        for args in [(True,0,0,0,1,1),(-1,0,0,0,1,1),(0,0,True,0,1,1),(0,0,0,0,0,1),(3,0,0,0,2,1),(0,0,3,0,2,1),(0,1,0,0,1,1),(0,0,0,0,1,True)]:
            with self.assertRaises(ImportError):copy_tim_index_rectangle(source,digest,*args)
        with self.assertRaises(ImportError):copy_tim_index_rectangle(source,'0'*64,0,0,0,0,1,1)
        source=tim(16)
        with self.assertRaises(ImportError):copy_tim_index_rectangle(source,hashlib.sha256(source).hexdigest(),0,0,0,0,1,1)

    def test_regions_preserve_every_outside_pixel_and_palette(self):
        for bpp in (4,8):
            source=tim(bpp,image=block(0,0,3,3,bytes(range(18))));digest=hashlib.sha256(source).hexdigest()
            width=12 if bpp==4 else 6
            for x,y,w,h in [(0,0,width,3),(1,0,3,2),(width-1,2,1,1),(0,1,1,1)]:
                candidate=patch_tim_index_rectangle(source,digest,x,y,w,h,(1<<bpp)-1)
                self.assertEqual(candidate[:32+(1<<bpp)*2],source[:32+(1<<bpp)*2])
                for row in range(3):
                    for col in range(width):
                        expected=(1<<bpp)-1 if x<=col<x+w and y<=row<y+h else inspect_tim_pixel_index(source,col,row)['palette_entry']
                        self.assertEqual(inspect_tim_pixel_index(candidate,col,row)['palette_entry'],expected)
            self.assertEqual(patch_tim_index_rectangle(source,digest,0,0,1,1,0),source)

    def test_stale_bounds_types_and_formats_reject(self):
        source=tim();digest=hashlib.sha256(source).hexdigest()
        for args in [(True,0,1,1,0),(0,0,True,1,0),(0,0,1,0,0),(3,0,2,1,0),(0,0,1,2,0),(0,0,1,1,16),(0,0,1,1,True),(-1,0,1,1,0)]:
            with self.assertRaises(ImportError):patch_tim_index_rectangle(source,digest,*args)
        with self.assertRaises(ImportError):patch_tim_index_rectangle(source,'0'*64,0,0,1,1,0)
        source=tim(16)
        with self.assertRaises(ImportError):patch_tim_index_rectangle(source,hashlib.sha256(source).hexdigest(),0,0,1,1,0)
