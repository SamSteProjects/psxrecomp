"""MENUE3 native direction/width without runtime actor identity inference."""
import hashlib
import os
import struct
import unittest
from importer.pipeline import _disc_context
from importer.script_inspection import inspect_record
from importer.branch_authoring import _branch

class ActorStateCopyDecode(unittest.TestCase):
    def test_selector_direction_and_continuation_both_headers(self):
        for extended in (False,True):
            for selector in (0,31,128,255):
                header=bytes((0xcc,7)) if extended else b'\x4c'
                data=header+bytes((0xe3,selector))+b'\x21\x26\xfe\xff'
                report=inspect_record(data,0);self.assertFalse(report['stops'])
                row=report['instructions'][0];args=row['operands']
                self.assertEqual(row['mnemonic'],'ACTOR_STATE_COPY')
                self.assertEqual(row['length'],len(header)+2)
                self.assertEqual(row['target_context'],7 if extended else None)
                self.assertEqual(args['actor_selector'],selector)
                self.assertEqual(args['copy_direction'],'resolved_actor_to_dispatch_context')
                self.assertEqual(args['field_offsets'],['0x14','0x16','0x18','0x26'])
                self.assertEqual(args['on_lookup_miss'],'no_field_copy')
                self.assertEqual(args['actor_binding'],'runtime_lookup_unresolved')
                self.assertEqual(row['successors'],[{'pc':len(header)+2,'condition':'encoded_continuation'}])
                self.assertIsNone(_branch(data,row))
                self.assertEqual(report['dialogues'],[])
                self.assertNotIn('target_position',args)

    def test_truncation_and_unknown_tail_stop_without_recovery(self):
        for extended in (False,True):
            header=bytes((0xcc,7)) if extended else b'\x4c'
            full=header+b'\xe3\xff'
            for length in range(1,len(full)):
                report=inspect_record(full[:length],0)
                self.assertEqual(report['instructions'],[]);self.assertTrue(report['stops'])
            report=inspect_record(full+b'\x00\x1fHidden\0',0)
            self.assertEqual(len(report['instructions']),1)
            self.assertTrue(report['stops']);self.assertEqual(report['dialogues'],[])

@unittest.skipUnless(os.environ.get('LEGAIA_DISC_BIN'),'requires private retail disc')
class RetailActorStateCopyProof(unittest.TestCase):
    def test_hash_bound_lookup_load_store_direction_miss_and_continuations(self):
        with _disc_context(os.environ['LEGAIA_DISC_BIN']) as (_,_,_,archive):
            data=archive.read_entry(archive.entry(897),extended=True)
        self.assertEqual(hashlib.sha256(data).hexdigest(),'216f846db5ab085a295cef4064747380a06c995caa3e1b2773e78a1d349f126b')
        word=lambda a:struct.unpack_from('<I',data,a-0x801ce818)[0]
        target=lambda a:a+4+struct.unpack('<h',struct.pack('<H',word(a)&65535))[0]*4
        for a,v in ((0x801cf014,0x801e3108),(0x801e3108,0x92c40001),
                    (0x801e310c,0x0c00f20f),(0x801e3114,0x00402021),
                    (0x801e3120,0x94820014),(0x801e3128,0xa6a20014),
                    (0x801e312c,0x94820016),(0x801e3134,0xa6a20016),
                    (0x801e3138,0x94820018),(0x801e3140,0xa6a20018),
                    (0x801e3144,0x94820026),(0x801e314c,0xa6a20026),
                    (0x801e3170,0xa6a2008e),(0x801e31b4,0x27de0003),
                    (0x801e31bc,0xa2a0008b),(0x801e00b8,0x27de0003)):
            self.assertEqual(word(a),v,hex(a))
        self.assertEqual(target(0x801e3118),0x801e3174) # missing lookup still post-updates
        self.assertEqual(target(0x801e315c),0x801e3178) # mirrored Y depends on current flag
        self.assertEqual((word(0x801e31b8)&0x3ffffff)<<2|0x80000000,0x801e00b8)

if __name__=='__main__':unittest.main()
