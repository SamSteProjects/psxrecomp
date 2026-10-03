"""Retail scene-register write and field callback continuation evidence."""
import hashlib
import os
import struct
import unittest
from importer.pipeline import _disc_context
from importer.script_inspection import inspect_record
from importer.branch_authoring import _branch

class SceneCallbackDecode(unittest.TestCase):
    def test_scene_register_values_are_unsigned_bytes_not_targets(self):
        for extended in (False,True):
            for values in ((0,0,0),(31,76,255),(255,128,1)):
                header=bytes((0xcf,7)) if extended else b'\x4f'
                data=header+bytes(values)+b'\x21\x26\xfe\xff'
                report=inspect_record(data,0);self.assertFalse(report['stops'])
                row=report['instructions'][0]
                self.assertEqual(row['mnemonic'],'SCENE_REGISTER_WRITE')
                self.assertEqual(row['target_context'],7 if extended else None)
                self.assertEqual(row['length'],len(header)+3)
                self.assertEqual(row['operands']['values'],list(values))
                self.assertEqual(row['operands']['field_offsets'],['0x10','0x12','0x14'])
                self.assertEqual(row['operands']['runtime_effect'],'not_evaluated')
                self.assertEqual(row['successors'],[{'pc':len(header)+3,'condition':'encoded_continuation'}])
                self.assertIsNone(_branch(data,row))
                self.assertEqual(report['dialogues'],[])

    def test_callback_advances_and_keeps_its_runtime_effect_unobserved(self):
        for extended in (False,True):
            header=bytes((0xcc,7)) if extended else b'\x4c'
            data=header+b'\xea\x21\x26\xfe\xff'
            report=inspect_record(data,0);self.assertFalse(report['stops'])
            row=report['instructions'][0]
            self.assertEqual(row['mnemonic'],'FIELD_CALLBACK_C7EC')
            self.assertEqual(row['length'],len(header)+1)
            self.assertEqual(row['operands']['callback_address'],'0x8003C7EC')
            self.assertEqual(row['operands']['runtime_effect'],'not_evaluated')
            self.assertEqual(row['successors'],[{'pc':len(header)+1,'condition':'encoded_continuation'}])
            self.assertIsNone(_branch(data,row))
            self.assertEqual([r['pc'] for r in report['instructions']],[0,len(header)+1,len(header)+2])

    def test_truncated_fields_and_unknown_following_bytes_fail_closed(self):
        for extended in (False,True):
            for opcode,body in ((0x4f,b'\x00\x1f\xff'),(0x4c,b'\xea')):
                header=bytes((opcode|128,7)) if extended else bytes((opcode,))
                full=header+body
                for length in range(1,len(full)):
                    report=inspect_record(full[:length],0)
                    self.assertEqual(report['instructions'],[]);self.assertTrue(report['stops'])
                report=inspect_record(full+b'\x00\x1fHidden\0',0)
                self.assertEqual(len(report['instructions']),1)
                self.assertTrue(report['stops']);self.assertEqual(report['dialogues'],[])

@unittest.skipUnless(os.environ.get('LEGAIA_DISC_BIN'),'requires private retail disc')
class RetailSceneCallbackProof(unittest.TestCase):
    def test_hash_bound_byte_reads_word_writes_and_advanced_callback_return(self):
        with _disc_context(os.environ['LEGAIA_DISC_BIN']) as (_,_,_,archive):
            data=archive.read_entry(archive.entry(897),extended=True)
        self.assertEqual(hashlib.sha256(data).hexdigest(),'216f846db5ab085a295cef4064747380a06c995caa3e1b2773e78a1d349f126b')
        word=lambda a:struct.unpack_from('<I',data,a-0x801ce818)[0]
        for a,v in ((0x801ced78,0x801e0c0c),(0x801e0c14,0x92c20000),
                    (0x801e0c1c,0xa4620010),(0x801e0c20,0x92c20001),
                    (0x801e0c28,0xa4620012),(0x801e0c2c,0x92c20002),
                    (0x801e0c30,0x27de0004),(0x801e0c38,0xa4620014),
                    (0x801cf030,0x801e34cc),(0x801e34cc,0x0c00f1fb),
                    (0x801e34d0,0x27de0002),(0x801e34d8,0x03c01021)):
            self.assertEqual(word(a),v,hex(a))

if __name__=='__main__':unittest.main()
