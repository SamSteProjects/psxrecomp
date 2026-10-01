"""Font source boundaries, nibble order, crop coordinates and stencil roles."""
import base64
import struct
import unittest
from importer.dialogue_font import decode_dialogue_font
from importer.core import ImportError


def source():
    clut=struct.pack('<I4H',44,0,510,16,1)+bytes(32)
    pixels=bytearray(32768)
    # 'A': low/even fill index1, high/odd shadow14; following byte transparent.
    pixels[32*128+8]=0xe1
    tim=struct.pack('<2I',0x10,8)+clut+struct.pack('<I4H',32780,896,0,64,256)+pixels
    exe=bytearray(0x6471c+256);exe[:8]=b'PS-X EXE';struct.pack_into('<I',exe,0x18,0x80010000)
    exe[0x6471c:]=bytes(range(256))
    return tim,bytes(exe)

class DialogueFontTests(unittest.TestCase):
    def test_source_pixel_stencil_coordinates_and_widths(self):
        tim,exe=source();result=decode_dialogue_font(tim,exe);rgba=base64.b64decode(result['rgba_base64'])
        start=((2*15)*224+14)*4
        self.assertEqual(rgba[start:start+12],bytes([255,255,255,255,32,32,32,255,0,0,0,0]))
        self.assertEqual((result['atlas_width'],result['atlas_height'],len(rgba)),(224,210,188160))
        self.assertEqual(result['widths'],list(range(256)))
        self.assertEqual(result['source']['widths']['file_offset'],0x6471c)
        self.assertEqual(result['source']['tim']['byte_length'],32832)
        self.assertEqual(decode_dialogue_font(tim+b'padding',exe)['rgba_base64'],result['rgba_base64'])

    def test_wrong_page_palette_executable_and_truncated_sources_rejected(self):
        tim,exe=source()
        for position,value in ((12,1),(16,15),(52+4,895),(52+8,63)):
            bad=bytearray(tim);struct.pack_into('<H',bad,position,value)
            with self.assertRaises(ImportError):decode_dialogue_font(bytes(bad),exe)
        for bad in (b'',tim[:50],tim[:-1],bytes(0x8101)):
            with self.assertRaises(ImportError):decode_dialogue_font(bad,exe)
        for bad in (b'',exe[:-1],b'wrongexe'+exe[8:]):
            with self.assertRaises(ImportError):decode_dialogue_font(tim,bad)
        bad=bytearray(exe);struct.pack_into('<I',bad,0x18,0x80074000)
        with self.assertRaises(ImportError):decode_dialogue_font(tim,bytes(bad))
