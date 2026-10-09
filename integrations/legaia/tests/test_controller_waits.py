import unittest
from hashlib import sha256
from importer.core import ImportError
from importer.controller_waits import ControllerWaitAuthoringContext
from importer.wait_authoring import WaitAuthoringContext
from importer.man_layout import read_man_layout
from test_controller_branches import source,OWNER

ID='script://fixture/controllers/man-p1/0000/wait/0005'


class ControllerWaits(unittest.TestCase):
    def test_literal_full_man_words_and_source_ownership(self):
        for header in [b'\x4a',b'\xca\x07']:
            length=len(header)+2
            src,man=source(header+b'\x01\x01'+b'\x26'+((5-(5+length+1))&65535).to_bytes(2,'little'))
            ctx=ControllerWaitAuthoringContext(src);t=ctx.options(OWNER)['targets'][0];at=t['decoded_byte_offset']
            self.assertEqual(ctx.patch({ID:t['values']}),(man,[]))
            for ticks in [0,1,256,512,32767]:
                result,audit=ctx.patch({ID:{'duration_ticks':ticks}})
                expected=bytearray(man);expected[at:at+2]=ticks.to_bytes(2,'little')
                self.assertEqual(result,bytes(expected));self.assertEqual(read_man_layout(result),read_man_layout(man))
                self.assertEqual(audit[0]['source_decoded_man_sha256'],sha256(man).hexdigest())
                self.assertEqual(audit[0]['source_record_sha256'],sha256(man[57:-18]).hexdigest())
                self.assertEqual(audit[0]['owner_id'],OWNER);self.assertEqual(ctx._man,man)
            with self.assertRaises(ImportError):WaitAuthoringContext(src).options(OWNER)
            with self.assertRaises(ImportError):WaitAuthoringContext(src).patch({ID:{'duration_ticks':1}})

    def test_relocated_preimage_and_extent(self):
        src,man=source(b'\x4a\x01\x01\x26\xfc\xff');ctx=ControllerWaitAuthoringContext(src)
        candidate=bytearray(man[:49]+bytes(4)+man[49:]);candidate[49:53]=bytes(4)
        # Move all relative section and record offsets by four, matching an enlarged index table.
        candidate[40:43]=(int.from_bytes(man[40:43],'little')+4).to_bytes(3,'little')
        candidate[46:49]=(int.from_bytes(man[46:49],'little')+4).to_bytes(3,'little')
        candidate=bytes(candidate);at=ctx.options(OWNER)['targets'][0]['decoded_byte_offset']+4
        result,audit=ctx.patch_appended(candidate,{ID:{'duration_ticks':512}})
        expected=bytearray(candidate);expected[at:at+2]=b'\x00\x02'
        self.assertEqual(result,bytes(expected));self.assertEqual(audit[0]['decoded_byte_offset'],at)
        self.assertEqual(audit[0]['source_decoded_byte_offset'],at-4)
        with self.assertRaises(ImportError):ctx.patch_appended(result,{ID:{'duration_ticks':512}})

    def test_foreign_identity_unknown_paths_and_bad_values(self):
        src,man=source(b'\x4a\x01\x01\x26\xfc\xff');ctx=ControllerWaitAuthoringContext(src)
        for owner in [OWNER.replace('/0000','/0001'),OWNER.replace('/controllers/','/actors/'),OWNER.replace('fixture','other')]:
            with self.assertRaises(ImportError):ctx.options(owner)
            with self.assertRaises(ImportError):ctx.patch({owner.replace('scene://','script://')+'/wait/0005':{'duration_ticks':1}})
        for values in [{'duration_ticks':True},{'duration_ticks':-1},{'duration_ticks':32768},{'duration_ticks':1,'seconds':1}]:
            with self.assertRaises(ImportError):ctx.patch({ID:values})
        with self.assertRaises(ImportError):ctx.patch({ID:{'duration_ticks':1}},original=man+b'x')
        with self.assertRaises(ImportError):ControllerWaitAuthoringContext(object())
        for script in [b'\x4a\x00\x80\x26\xfc\xff',b'\x4a\x01\x01\xff']:
            src,_=source(script);ctx=ControllerWaitAuthoringContext(src)
            self.assertFalse(ctx.options(OWNER)['supported'])
            with self.assertRaises(ImportError):ctx.patch({ID:{'duration_ticks':1}})
