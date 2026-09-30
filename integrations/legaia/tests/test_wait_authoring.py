"""Fixed-width wait targets preserve record/control layout and source provenance."""
import unittest
from hashlib import sha256
from importer.core import ImportError
from importer.wait_authoring import WaitAuthoringContext, patch_wait_target
from importer.man_actor_structure import append_actor_donor
from test_importer_dialogue_authoring import fixture,ACTOR

END=b'\x3f\0\0\x06town01\1\2\3opaque'
class WaitAuthoringTests(unittest.TestCase):
    def test_ordinary_extended_and_boundary_targets_preserve_source(self):
        for header in (b'\x4a',b'\xca\x07'):
            record=header+b'\x01\x01'+END
            self.assertEqual(patch_wait_target(record,0,0,{'duration_ticks':257}),(record,[]))
            for value in (0,1,255,256,32767):
                result,audit=patch_wait_target(record,0,0,{'duration_ticks':value},base_offset=100)
                self.assertEqual(result[:len(header)],header)
                self.assertEqual(result[len(header)+2:],END)
                self.assertEqual(int.from_bytes(result[len(header):len(header)+2],'little'),value)
                self.assertEqual(audit[0]['decoded_byte_offset'],100+len(header))
                self.assertEqual(audit[0]['byte_length'],2)
            for values in ({},{'duration_ticks':True},{'duration_ticks':-1},{'duration_ticks':32768},{'duration_ticks':1,'seconds':1}):
                with self.assertRaises(ImportError):patch_wait_target(record,0,0,values)
        for record,pc in ((b'\x4a\0',0),(b'\x4a\0\x80'+END,0),(b'\x4a\1\0\xff',0),(b'\x2a\x4a\1\0'+END,1)):
            with self.assertRaises(ImportError):patch_wait_target(record,0,pc,{'duration_ticks':1})

    def test_verified_source_and_appended_owner_use_exact_span(self):
        source,man=fixture(b'\x4a\1\1'+END)
        context=WaitAuthoringContext(source);target=context.options(ACTOR)['targets'][0]
        edits={target['semantic_id']:{'duration_ticks':512}}
        result,audit=context.patch(edits)
        at=target['decoded_byte_offset']
        self.assertEqual({i for i,(a,b) in enumerate(zip(man,result)) if a!=b},{at,at+1})
        self.assertEqual(context._man,man)
        appended,_=append_actor_donor(man,sha256(man).hexdigest(),1)
        result,rebased=context.patch_appended(appended,edits)
        self.assertEqual(rebased[0]['decoded_byte_offset'],at+3)
        self.assertEqual({i for i,(a,b) in enumerate(zip(appended,result)) if a!=b},{at+3,at+4})
        with self.assertRaises(ImportError):context.patch_appended(result,edits)
        with self.assertRaises(ImportError):context.patch(edits,original=man+b'x')
        with self.assertRaises(ImportError):context.patch({target['semantic_id'].replace('/0001/','/9999/'):{'duration_ticks':1}})
        unsupported,_=fixture(b'\x4a\0\x80'+END)
        self.assertFalse(WaitAuthoringContext(unsupported).options(ACTOR)['supported'])

if __name__=='__main__':unittest.main()
