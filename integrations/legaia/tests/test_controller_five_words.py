import unittest
from hashlib import sha256
from importer.core import ImportError,decompress_lzs
from importer.controller_five_words import ControllerFiveWordAuthoringContext,validate_five_word_values
from importer.controller_system_flags import ControllerRecordSource
from importer.serialization import compress_lzs
from importer.man_layout import read_man_layout
from test_controller_branches import source,OWNER

ID='script://fixture/controllers/man-p1/0000/five-word/0005'
VALUES=dict(signed_words=[-32768,32767,-1,0,1])


class ControllerFiveWords(unittest.TestCase):
    def test_literal_complete_man_dispatch_raw_lzs_limits_and_detached_values(self):
        for header in (b'\x43',b'\xc3\x07'):
            script=header+b'\x11'+bytes(10);script+=b'\x26'+((-len(script)-1)&65535).to_bytes(2,'little')
            src,man=source(script)
            for compression in ('none','lzs'):
                ctx=ControllerFiveWordAuthoringContext(src if compression=='none' else ControllerRecordSource('fixture',man,compress_lzs(man),{},compression='lzs'))
                target=ctx.options(OWNER)['targets'][0];self.assertEqual(target['values'],dict(signed_words=[0]*5));self.assertEqual(ctx.patch({ID:target['values']}),(man,[]))
                for values in (VALUES,dict(signed_words=[32767,-32768,0,-1,1])):
                    result,audit=ctx.patch({ID:values});at=57+5+len(header)+1;expected=bytearray(man);expected[at:at+10]=b''.join(w.to_bytes(2,'little',signed=True) for w in values['signed_words'])
                    self.assertEqual(result,bytes(expected));self.assertEqual(ctx._man,man);self.assertEqual(read_man_layout(result),read_man_layout(man));self.assertEqual(decompress_lzs(compress_lzs(result),len(result))[0],result)
                    self.assertEqual(audit[0]['byte_length'],10);self.assertEqual(audit[0]['before_values'],target['values']);self.assertEqual(audit[0]['after_values'],values);self.assertEqual(audit[0]['source_record_sha256'],sha256(man[57:-18]).hexdigest())
                target['values']['signed_words'][0]=99;self.assertEqual(ctx.options(OWNER)['targets'][0]['values']['signed_words'][0],0)

    def test_domains_ownership_and_partial_sources_refuse(self):
        src,man=source(b'\x43\x11'+bytes(10)+b'\x26\xf3\xff');ctx=ControllerFiveWordAuthoringContext(src)
        for word in (True,-32769,32768,1.0,'1',None):
            with self.assertRaises(ImportError):validate_five_word_values(dict(signed_words=[word,0,0,0,0]))
        for value in ({},dict(VALUES,selector=0),dict(VALUES,extra=0),dict(signed_words=[]),dict(signed_words=[0,0]),dict(signed_words=[0]*6),dict(signed_words=(0,0,0,0,0)),None):
            with self.assertRaises(ImportError):ctx.patch({ID:value})
        for owner in (OWNER.replace('fixture','foreign'),OWNER.replace('/controllers/','/actors/'),OWNER.replace('/0000','/0001')):
            with self.assertRaises(ImportError):ctx.options(owner)
        for identity in (ID[:-4]+'0006',ID[:-4]+'ffff',ID.replace('/five-word/','/word-triplet/'),ID.replace('/controllers/','/actors/')):
            with self.assertRaises(ImportError):ctx.patch({identity:VALUES})
        with self.assertRaises(ImportError):ctx.patch({ID:VALUES},original=man+b'x')
        src,_=source(b'\x43\x11'+bytes(10)+b'\x43\x12');ctx=ControllerFiveWordAuthoringContext(src);self.assertFalse(ctx.options(OWNER)['supported'])
        with self.assertRaises(ImportError):ctx.patch({ID:VALUES})

    def test_unvisited_opaque_tail_is_preserved_without_inferring_a_path(self):
        from importer.script_inspection import inspect_record
        src,man=source(b'\x43\x11'+bytes(10)+b'\x26\xf3\xff\x43\x12\xff\x00')
        ctx=ControllerFiveWordAuthoringContext(src);options=ctx.options(OWNER)
        self.assertEqual(options['inspection']['status'],'partial');self.assertFalse(options['inspection']['stops']);self.assertTrue(options['inspection']['opaque_regions']);self.assertTrue(options['supported'])
        result,_=ctx.patch({ID:VALUES});expected=bytearray(man);expected[64:74]=b''.join(w.to_bytes(2,'little',signed=True) for w in VALUES['signed_words']);self.assertEqual(result,bytes(expected))
        self.assertEqual(inspect_record(result[57:-18],5)['opaque_regions'],options['inspection']['opaque_regions'])

    def test_other_word_families_keep_separate_dispatch_and_value_shapes(self):
        from importer.controller_three_words import ControllerThreeWordAuthoringContext
        from importer.controller_word_triplets import ControllerWordTripletAuthoringContext
        from importer.controller_fades import ControllerFadeAuthoringContext
        src,man=source(b'\x43\x11'+bytes(10)+b'\x4c\xd8\x00'+bytes(6)+b'\x4c\x90\x00'+bytes(6)+b'\x4c\xe6'+bytes(6)+b'\x26\xd9\xff')
        families=[
            (ControllerFiveWordAuthoringContext,ID,64,VALUES),
            (ControllerWordTripletAuthoringContext,ID.replace('/five-word/0005','/word-triplet/0011'),76,dict(selector=255,signed_words=[-32768,32767,-1])),
            (ControllerFadeAuthoringContext,ID.replace('/five-word/0005','/fade/001a'),85,dict(selector=255,signed_words=[-32768,32767,-1])),
            (ControllerThreeWordAuthoringContext,ID.replace('/five-word/0005','/three-word/0023'),94,dict(signed_words=[-32768,32767,-1])),
        ]
        for kind,identity,at,value in families:
            ctx=kind(src);result,audit=ctx.patch({identity:value});expected=bytearray(man)
            raw=(bytes([255]) if 'selector' in value else b'')+b''.join(w.to_bytes(2,'little',signed=True) for w in value['signed_words'])
            expected[at:at+len(raw)]=raw;self.assertEqual(result,bytes(expected));self.assertEqual(audit[0]['byte_length'],len(raw))
            for _,other,_,_ in families:
                if other!=identity:
                    with self.assertRaises(ImportError):ctx.patch({other:value})
