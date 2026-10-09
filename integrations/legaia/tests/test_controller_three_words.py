import unittest
from hashlib import sha256
from importer.core import ImportError,decompress_lzs
from importer.controller_three_words import ControllerThreeWordAuthoringContext,validate_three_word_values
from importer.controller_system_flags import ControllerRecordSource
from importer.serialization import compress_lzs
from importer.man_layout import read_man_layout
from test_controller_branches import source,OWNER

ID='script://fixture/controllers/man-p1/0000/three-word/0005'
VALUES=dict(signed_words=[-32768,32767,-1])


class ControllerThreeWords(unittest.TestCase):
    def test_literal_complete_man_dispatch_raw_lzs_limits_and_detached_values(self):
        for header in (b'\x4c',b'\xcc\x07'):
            script=header+b'\xe6'+bytes(6);script+=b'\x26'+((-len(script)-1)&65535).to_bytes(2,'little')
            src,man=source(script)
            for compression in ('none','lzs'):
                ctx=ControllerThreeWordAuthoringContext(src if compression=='none' else ControllerRecordSource('fixture',man,compress_lzs(man),{},compression='lzs'))
                target=ctx.options(OWNER)['targets'][0];self.assertEqual(target['values'],dict(signed_words=[0]*3));self.assertEqual(ctx.patch({ID:target['values']}),(man,[]))
                for values in (VALUES,dict(signed_words=[32767,-32768,0])):
                    result,audit=ctx.patch({ID:values});at=57+5+len(header)+1;expected=bytearray(man);expected[at:at+6]=b''.join(w.to_bytes(2,'little',signed=True) for w in values['signed_words'])
                    self.assertEqual(result,bytes(expected));self.assertEqual(ctx._man,man);self.assertEqual(read_man_layout(result),read_man_layout(man));self.assertEqual(decompress_lzs(compress_lzs(result),len(result))[0],result)
                    self.assertEqual(audit[0]['byte_length'],6);self.assertEqual(audit[0]['before_values'],target['values']);self.assertEqual(audit[0]['after_values'],values);self.assertEqual(audit[0]['source_record_sha256'],sha256(man[57:-18]).hexdigest())
                target['values']['signed_words'][0]=99;self.assertEqual(ctx.options(OWNER)['targets'][0]['values']['signed_words'][0],0)

    def test_domains_ownership_and_partial_sources_refuse(self):
        src,man=source(b'\x4c\xe6'+bytes(6)+b'\x26\xf7\xff');ctx=ControllerThreeWordAuthoringContext(src)
        for word in (True,-32769,32768,1.0,'1',None):
            with self.assertRaises(ImportError):validate_three_word_values(dict(signed_words=[word,0,0]))
        for value in ({},dict(VALUES,selector=0),dict(VALUES,extra=0),dict(signed_words=[]),dict(signed_words=[0,0]),dict(signed_words=[0]*4),dict(signed_words=(0,0,0)),None):
            with self.assertRaises(ImportError):ctx.patch({ID:value})
        for owner in (OWNER.replace('fixture','foreign'),OWNER.replace('/controllers/','/actors/'),OWNER.replace('/0000','/0001')):
            with self.assertRaises(ImportError):ctx.options(owner)
        for identity in (ID[:-4]+'0006',ID[:-4]+'ffff',ID.replace('/three-word/','/word-triplet/'),ID.replace('/controllers/','/actors/')):
            with self.assertRaises(ImportError):ctx.patch({identity:VALUES})
        with self.assertRaises(ImportError):ctx.patch({ID:VALUES},original=man+b'x')
        src,_=source(b'\x4c\xe6'+bytes(6)+b'\x4c\xe7');ctx=ControllerThreeWordAuthoringContext(src);self.assertFalse(ctx.options(OWNER)['supported'])
        with self.assertRaises(ImportError):ctx.patch({ID:VALUES})

    def test_three_word_fade_and_d8_keep_distinct_family_payloads(self):
        from importer.controller_fades import ControllerFadeAuthoringContext
        from importer.controller_word_triplets import ControllerWordTripletAuthoringContext
        src,man=source(b'\x4c\xe6'+bytes(6)+b'\x4c\xd8\x00'+bytes(6)+b'\x4c\x90\x00'+bytes(6)+b'\x26\xe5\xff')
        e6=ControllerThreeWordAuthoringContext(src);d8=ControllerWordTripletAuthoringContext(src);fade=ControllerFadeAuthoringContext(src)
        d8id=ID.replace('/three-word/0005','/word-triplet/000d');fadeid=ID.replace('/three-word/0005','/fade/0016')
        for ctx,identity,other,at,value in [(e6,ID,d8id,64,VALUES),(d8,d8id,ID,72,dict(VALUES,selector=255)),(fade,fadeid,ID,81,dict(VALUES,selector=255))]:
            result,audit=ctx.patch({identity:value});expected=bytearray(man);raw=(bytes([255]) if 'selector' in value else b'')+b''.join(w.to_bytes(2,'little',signed=True) for w in value['signed_words']);expected[at:at+len(raw)]=raw
            self.assertEqual(result,bytes(expected));self.assertEqual(audit[0]['byte_length'],len(raw))
            with self.assertRaises(ImportError):ctx.patch({other:value})

    def test_unvisited_opaque_tail_is_preserved_without_inferring_a_path(self):
        from importer.script_inspection import inspect_record
        src,man=source(b'\x4c\xe6'+bytes(6)+b'\x26\xf7\xff\x4c\xe7\xff\x00')
        ctx=ControllerThreeWordAuthoringContext(src);options=ctx.options(OWNER)
        self.assertEqual(options['inspection']['status'],'partial');self.assertFalse(options['inspection']['stops']);self.assertTrue(options['inspection']['opaque_regions']);self.assertTrue(options['supported'])
        result,_=ctx.patch({ID:VALUES});expected=bytearray(man);expected[64:70]=b''.join(w.to_bytes(2,'little',signed=True) for w in VALUES['signed_words']);self.assertEqual(result,bytes(expected))
        self.assertEqual(inspect_record(result[57:-18],5)['opaque_regions'],options['inspection']['opaque_regions'])
