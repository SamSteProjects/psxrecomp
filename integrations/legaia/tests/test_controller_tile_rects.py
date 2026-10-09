import unittest
from hashlib import sha256
from importer.core import ImportError, decompress_lzs
from importer.controller_tile_rects import ControllerTileRectAuthoringContext, FIELDS
from importer.controller_system_flags import ControllerRecordSource
from importer.man_layout import read_man_layout
from importer.serialization import compress_lzs, serialize_man_decoded
from test_controller_branches import source, OWNER

ID='script://fixture/controllers/man-p1/0000/tile-rect/0005'


class ControllerTileRects(unittest.TestCase):
    def test_literal_five_byte_writes_full_man_and_compressed_roundtrip(self):
        for header in (b'\x4c',b'\xcc\x07'):
            for compression in ('none','lzs'):
                script=header+b'\x83\x01\x02\x03\x04\x05';length=len(script)
                src,man=source(script+b'\x26'+((-length-1)&65535).to_bytes(2,'little'))
                if compression=='lzs':src=ControllerRecordSource('fixture',man,compress_lzs(man),{},compression='lzs')
                ctx=ControllerTileRectAuthoringContext(src);target=ctx.options(OWNER)['targets'][0];at=target['decoded_byte_offset']
                self.assertEqual(ctx.patch({ID:target['values']}),(man,[]))
                for values in ((0,0,0,0,0),(255,255,255,255,255),(255,254,0,1,128)):
                    fields=dict(zip(FIELDS,values));result,audit=ctx.patch({ID:fields})
                    expected=bytearray(man);expected[at:at+5]=bytes(values);self.assertEqual(result,bytes(expected))
                    self.assertEqual(read_man_layout(result),read_man_layout(man));self.assertEqual(ctx._man,man)
                    self.assertEqual(audit[0]['source_record_sha256'],sha256(man[57:-18]).hexdigest())
                    self.assertEqual(audit[0]['source_decoded_man_sha256'],sha256(man).hexdigest())
                    self.assertEqual(audit[0]['after_values'],fields);self.assertEqual(audit[0]['owner_id'],OWNER)
                    encoded,_=serialize_man_decoded(compress_lzs(man),len(man),result,'fixture')
                    self.assertEqual(decompress_lzs(encoded,len(man))[0],result)
                target['values']['value']=99;self.assertEqual(ctx.options(OWNER)['targets'][0]['values']['value'],5)

    def test_relocated_record_and_noop_preimage_refusal(self):
        src,man=source(b'\x4c\x83\x01\x02\x03\x04\x05\x26\xf8\xff');ctx=ControllerTileRectAuthoringContext(src)
        candidate=bytearray(man[:49]+bytes(4)+man[49:]);candidate[40:43]=(int.from_bytes(man[40:43],'little')+4).to_bytes(3,'little');candidate[46:49]=(int.from_bytes(man[46:49],'little')+4).to_bytes(3,'little');candidate=bytes(candidate)
        target=ctx.options(OWNER)['targets'][0];at=target['decoded_byte_offset']+4;fields=dict(zip(FIELDS,(1,2,3,4,255)))
        result,audit=ctx.patch_appended(candidate,{ID:fields});expected=bytearray(candidate);expected[at+4]=255
        self.assertEqual(result,bytes(expected));self.assertEqual(audit[0]['decoded_byte_offset'],at);self.assertEqual(audit[0]['source_decoded_byte_offset'],at-4)
        self.assertEqual(ctx.patch_appended(candidate,{ID:target['values']}),(candidate,[]))
        for edits in ({ID:fields},{ID:target['values']},{}):
            with self.assertRaises(ImportError):ctx.patch_appended(result,edits)

    def test_unknown_paths_wrong_owners_and_invalid_fields_refuse(self):
        src,man=source(b'\x4c\x83\x01\x02\x03\x04\x05\x26\xf8\xff');ctx=ControllerTileRectAuthoringContext(src);values=dict(zip(FIELDS,range(5)))
        for owner in (OWNER.replace('fixture','foreign'),OWNER.replace('/controllers/','/actors/'),OWNER.replace('/0000','/0001')):
            with self.assertRaises(ImportError):ctx.options(owner)
            with self.assertRaises(ImportError):ctx.patch({owner.replace('scene://','script://')+'/tile-rect/0005':values})
        for invalid in (True,-1,256,1.0,'1',None):
            with self.assertRaises(ImportError):ctx.patch({ID:dict(values,value=invalid)})
        for fields in ({},dict(values,meaning='walkable'),{k:v for k,v in values.items() if k!='value'}):
            with self.assertRaises(ImportError):ctx.patch({ID:fields})
        for pc in ('0006','000c','ffff'):
            with self.assertRaises(ImportError):ctx.patch({ID[:-4]+pc:values})
        with self.assertRaises(ImportError):ctx.patch({ID:values},original=man+b'x')
        with self.assertRaises(ImportError):ControllerTileRectAuthoringContext(object())
        src,_=source(b'\x4c\x83\x01\x02\x03\x04\x05\x4c\xee');ctx=ControllerTileRectAuthoringContext(src)
        self.assertFalse(ctx.options(OWNER)['supported'])
        with self.assertRaises(ImportError):ctx.patch({ID:values})
