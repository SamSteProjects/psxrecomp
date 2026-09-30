import unittest
from importer.core import ImportError
from importer.flag_authoring import patch_flag_bit,FlagAuthoringContext
from test_importer_dialogue_authoring import fixture,ACTOR
END=b'\x3f\0\0\x06town01\x01\x02\x03opaque'
class FlagAuthoringTests(unittest.TestCase):
    def test_appended_owner_rebases_without_editing_donor_clone(self):
        from hashlib import sha256
        from importer.man_actor_structure import append_actor_donor
        source,man=fixture(b'\x2e\xe2'+END);context=FlagAuthoringContext(source)
        target=context.options(ACTOR)['targets'][0]
        appended,_=append_actor_donor(man,sha256(man).hexdigest(),1)
        changed,audit=context.patch_appended(appended,{target['semantic_id']:{'bit':3}})
        self.assertEqual({i for i,(a,b) in enumerate(zip(appended,changed)) if a!=b},{audit[0]['decoded_byte_offset']})
        self.assertEqual(appended[audit[0]['decoded_byte_offset']],0xe2)
        self.assertEqual(changed[audit[0]['decoded_byte_offset']],0xe3)

    def test_banks_extended_dispatch_and_high_bits_preserved(self):
        for opcode in range(0x2b,0x34):
            for extended in (False,True):
                header=bytes((opcode|128,7)) if extended else bytes((opcode,))
                source=header+b'\xe2'+END
                self.assertEqual(patch_flag_bit(source,0,0,{'bit':2}),(source,[]))
                changed,audit=patch_flag_bit(source,0,0,{'bit':3},base_offset=100)
                self.assertEqual(changed[:len(header)],header);self.assertEqual(changed[len(header):],b'\xe3'+END)
                self.assertEqual(audit[0]['before_bit'],2);self.assertEqual(audit[0]['after_bit'],3)
                self.assertEqual(audit[0]['decoded_byte_offset'],100+len(header))
                self.assertEqual(audit[0]['target_context'],7 if extended else None)
    def test_unknown_width_side_effect_selector_and_invalid_inputs_reject(self):
        for source,bit in [(b'\x2b\x10'+END,2),(b'\x2b\x02'+END,16),(b'\x31\x08'+END,2),(b'\x31\x02'+END,8),(b'\xb2\x07\x0a'+END,2),(b'\x32\x02'+END,10),(b'\x50\x02'+END,3),(b'\x2b\x02\x2a',3)]:
            with self.assertRaises(ImportError):patch_flag_bit(source,0,0,{'bit':bit})
        for values in ({'bit':True},{'bit':32},{'bit':-1},{'bit':2,'offset':1},{}):
            with self.assertRaises(ImportError):patch_flag_bit(b'\x2b\x02'+END,0,0,values)
    def test_verified_context_patch_is_detached_and_single_byte(self):
        source,man=fixture(b'\x2e\xe2'+END);context=FlagAuthoringContext(source)
        options=context.options(ACTOR);target=options['targets'][0]
        changed,audit=context.patch({target['semantic_id']:{'bit':3}})
        self.assertEqual({i for i,(a,b) in enumerate(zip(man,changed)) if a!=b},{audit[0]['decoded_byte_offset']})
        self.assertEqual(audit[0]['before_byte'],0xe2);self.assertEqual(audit[0]['after_byte'],0xe3)
        self.assertEqual(context._man,man)
        with self.assertRaises(ImportError):context.patch({target['semantic_id'].replace('/0001/','/9999/'):{'bit':3}})
