"""Independent packet expectations and reviewed native delivery from source PNG."""
from copy import deepcopy
from hashlib import sha256
import base64
import struct
import unittest

from importer.core import ImportError
from importer.texture_image_conversion import convert_png
from importer.texture_png import _encode_png
from importer.textures import decode_tim, _pack_members
from importer.model_pack_archive import _archive
from importer.model_pack_composition import compose_model_pack_archive
from sdk import texture_slots
from sdk.texture_allocation_build import prepare
from sdk.scene_preview import source_key
import test_texture_slots_workflow as slots_workflow
from test_model_primitive_workflow import http_server


def options(bpp=4, **changes):
    return dict(dict(bpp=bpp,image_x=640,image_y=32,clut_x=0,clut_y=500 if bpp<=8 else 0,stp_mode='opaque'),**changes)


class TextureImageConversion(unittest.TestCase):
    def test_exact_indexed_and_direct_packets_alpha_and_separate_stp(self):
        rgba=bytes([255,0,0,0, 255,0,0,255, 0,0,0,255, 255,0,0,255])
        png=_encode_png(4,1,rgba)
        plane=_encode_png(4,1,bytes([0,0,0,255]*2+[255,255,255,255]*2))
        for bpp in (4,8,16):
            candidate,report=convert_png(png,options(bpp),plane)
            capacity=1<<bpp if bpp<=8 else 0
            expected=struct.pack('<II',0x10,(4,8,16).index(bpp)|(8 if capacity else 0))
            if capacity:
                expected+=struct.pack('<I4H',12+capacity*2,0,500,capacity,1)
                expected+=struct.pack(f'<{capacity}H',*[0,31,0x8000,0x801f]+[0]*(capacity-4))
            image=bytes([0x10,0x32]) if bpp==4 else bytes(range(4)) if bpp==8 else struct.pack('<4H',0,31,0x8000,0x801f)
            expected+=struct.pack('<I4H',12+len(image),640,32,len(image)//2,1)+image
            self.assertEqual(candidate,expected)
            decoded=decode_tim(candidate)
            self.assertEqual(decoded['stp'],bytes([0,0,1,1]))
            self.assertEqual(decoded['rgba'][3::4],bytes([0,255,255,255]))
            self.assertEqual(report['quantization']['color_max_error'],0)
            self.assertTrue(report['alpha_stp_classes_verified'])
        opaque=bytes([1,2,3,255, 16,32,64,255, 0,0,0,255, 255,255,255,255])
        candidate,report=convert_png(_encode_png(4,1,opaque),options(24))
        expected=struct.pack('<II',0x10,3)+struct.pack('<I4H',24,640,32,6,1)+bytes(c for at in range(0,16,4) for c in opaque[at:at+3])
        self.assertEqual(candidate,expected);self.assertEqual(decode_tim(candidate)['rgba'],opaque)
        self.assertEqual(report['quantization']['color_rms_error'],0)

    def test_quantization_determinism_alignment_bounds_and_explicit_conflicts(self):
        rgba=bytes(c for i in range(128) for c in (i*2,255-i*2,i,255))
        png=_encode_png(64,2,rgba)
        candidate,report=convert_png(png,options())
        self.assertEqual(convert_png(png,options()),(candidate,report))
        self.assertLessEqual(report['quantization']['palette_representative_count'],16)
        self.assertGreater(report['quantization']['quantized_pixel_count'],0)
        for choice in (options(bpp=True),options(extra=1),options(image_x=1020),options(image_y=511),options(clut_x=1),options(clut_y=512),options(16,clut_x=16),options(24,stp_mode='semi')):
            with self.assertRaises(ImportError):convert_png(png,choice)
        for bpp,width in ((4,3),(8,3),(24,3)):
            with self.assertRaises(ImportError):convert_png(_encode_png(width,1,bytes([255]*width*4)),options(bpp))
        with self.assertRaises(ImportError):convert_png(_encode_png(4,1,bytes([255,0,0,128]*4)),options())
        black=_encode_png(4,1,bytes([0,0,0,255]*4));zero=_encode_png(4,1,bytes([0,0,0,255]*4))
        with self.assertRaises(ImportError):convert_png(black,options(),zero)
        transparent=_encode_png(4,1,bytes([0]*16));white=_encode_png(4,1,bytes([255]*16))
        with self.assertRaises(ImportError):convert_png(transparent,options(),white)
        with self.assertRaises(ImportError):convert_png(transparent,options(24))
        with self.assertRaises(ImportError):convert_png(black,options(),_encode_png(2,1,bytes([255]*8)))
        _,forced=convert_png(black,options());self.assertEqual(forced['quantization']['forced_black_stp_pixels'],4)
        _,forced=convert_png(transparent,options(stp_mode='semi'));self.assertEqual(forced['quantization']['forced_transparent_stp_pixels'],4)

    def test_http_readonly_conversion_stale_context_and_existing_slot_build(self):
        helper=slots_workflow.TextureSlotsWorkflow();self.addCleanup(helper.doCleanups)
        p,context,archive,blob,ids=helper.setup_project()
        png=_encode_png(8,2,bytes([255,0,0,255]*16))
        body=dict(asset_id=ids[0],source_key=source_key(p),png_base64=base64.b64encode(png).decode('ascii'),stp_png_base64=None,options=options(8))
        before=deepcopy((p._document(),p.undo_stack,p.redo_stack))
        with http_server(p) as (_,post):
            for bad in (dict(body,source_key='stale'),dict(body,asset_id=None),dict(body,asset_id=[]),dict(body,extra=1),dict(body,png_base64='?'),dict(body,options=options(bpp=True))):
                status,_=post('/api/texture-image-convert',bad);self.assertEqual(status,400)
            status,result=post('/api/texture-image-convert',body);self.assertEqual(status,200,result)
            candidate=base64.b64decode(result['content_base64'])
            self.assertEqual(result['report']['proposed_sha256'],sha256(candidate).hexdigest())
            self.assertEqual((p._document(),p.undo_stack,p.redo_stack),before)
            args=(p,ids[0],candidate,source_key(p),'PNG authored',True)
            review=texture_slots.review(*args);applied=texture_slots.apply(*args,review['review_key'])
            identifier=applied['asset_id'];body.update(asset_id=identifier,source_key=source_key(p))
            status,result=post('/api/texture-image-convert',body);self.assertEqual(status,200,result)
            self.assertEqual(base64.b64decode(result['content_base64']),candidate)
        _,_,requests=prepare(p,{}, {},context,archive)
        rebuilt,_=compose_model_pack_archive(blob,sha256(blob).hexdigest(),requests)
        ar=_archive(rebuilt);raw=ar.read_entry(ar.entry(1));start,_=_pack_members(raw,True)[2]
        self.assertEqual(raw[start:start+len(candidate)],candidate)


if __name__=='__main__':unittest.main()
