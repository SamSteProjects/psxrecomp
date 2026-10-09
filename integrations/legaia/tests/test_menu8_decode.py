"""MENU80 native child walker ownership and MENU82/84 fixed writes."""
import hashlib
import os
import struct
import unittest
from importer.pipeline import _disc_context
from importer.script_inspection import inspect_record,_instruction,MAX_MESSAGE_TOKENS
from importer.branch_authoring import _branch

class Menu8Decode(unittest.TestCase):
    def test_fixed_byte_writes_preserve_selector_and_context(self):
        for extended in (False,True):
            for sub in (0x82,0x84):
                for value in (0,31,128,255):
                    header=bytes((0xcc,7)) if extended else b'\x4c'
                    data=header+bytes((sub,value))+b'\x21\x26\xfe\xff'
                    report=inspect_record(data,0);self.assertFalse(report['stops'])
                    row=report['instructions'][0];self.assertEqual(row['length'],len(header)+2)
                    self.assertEqual(row['target_context'],7 if extended else None)
                    self.assertEqual(row['operands']['character_selector' if sub==0x82 else 'value'],value)
                    self.assertIsNone(_branch(data,row))
                    self.assertEqual(row['successors'],[{'pc':len(header)+2,'condition':'encoded_continuation'}])
                    for length in range(1,row['length']):
                        self.assertEqual(inspect_record(data[:length],0)['instructions'],[])

    def test_allocator_exact_native_token_rules_and_opaque_children(self):
        for extended in (False,True):
            header=bytes((0xcc,7)) if extended else b'\x4c'
            # 5E consumes no argument; C0 consumes even a low-valued argument;
            # FF is one byte. No child is exposed as parent dialogue/instruction.
            payload=b'\x1f\x5e\x00\xc0\x00\xff\x1e'
            data=header+b'\x80\x02'+payload+b'\x21\x26\xfe\xff'
            report=inspect_record(data,0);self.assertFalse(report['stops'],report['stops'])
            row=report['instructions'][0];start=len(header)+2
            self.assertEqual(row['mnemonic'],'ALLOCATE_CHILD_PAYLOADS')
            self.assertEqual(row['length'],start+7)
            self.assertEqual(row['operands']['children'],[
                {'index':0,'pc':start,'length':3,'terminator':0,'token_count':2},
                {'index':1,'pc':start+3,'length':4,'terminator':30,'token_count':2}])
            self.assertEqual(row['successors'],[{'pc':start+7,'condition':'halt_acquire_succeeded'},
                                               {'pc':0,'condition':'halt_acquire_pending'}])
            self.assertEqual(report['dialogues'],[])
            self.assertIsNone(_branch(data,row))
            self.assertEqual([r['pc'] for r in report['instructions']],[0,start+7,start+8])

    def test_allocator_zero_max_count_and_every_truncation_boundary(self):
        for extended in (False,True):
            header=bytes((0xcc,7)) if extended else b'\x4c'
            for count in (0,1,255):
                full=header+bytes((0x80,count))+bytes(count)
                row=_instruction(full,0);self.assertEqual(row['length'],len(full))
                self.assertEqual(len(row['operands']['children']),count)
                for length in range(1,len(full)):
                    report=inspect_record(full[:length],0)
                    self.assertEqual(report['instructions'],[]);self.assertTrue(report['stops'])
            data=header+b'\x80\x01\xc0\x00\x21\x00'
            for length in range(len(header)+2,len(data)):
                self.assertEqual(inspect_record(data[:length],0)['instructions'],[])
        long=b'\x4c\x80\x01'+b'A'*MAX_MESSAGE_TOKENS+b'\0\x1fHidden\0'
        report=inspect_record(long,0);self.assertTrue(report['stops']);self.assertEqual(report['dialogues'],[])

    def test_parent_branch_into_child_payload_is_a_conflicting_boundary(self):
        # A branch visits the child before the allocator. The decoder must
        # reject ownership overlap, not retain a child as a parent instruction.
        data=b'\x4d\x00\x00\x00\x00'+struct.pack('<H',10-5)+b'\x4c\x80\x01\x21\x00\x21\x26\xfe\xff'
        report=inspect_record(data,0)
        self.assertTrue(report['stops'])
        self.assertTrue(any('overlap' in s['reason'] or 'interior' in s['reason'] or 'conflict' in s['reason'] for s in report['stops']),report['stops'])

    def test_global_signed_word_write_has_no_jump_operand(self):
        for extended in (False,True):
            for value in (-32768,-1,0,32767):
                header=bytes((0xcc,7)) if extended else bytes((0x4c,))
                data=header+bytes((0x89,))+struct.pack('<h',value)+bytes((0x21,0x26,0xfe,0xff))
                report=inspect_record(data,0);self.assertFalse(report['stops'])
                row=report['instructions'][0]
                self.assertEqual(row['mnemonic'],'SET_GLOBAL_73F00')
                self.assertEqual(row['operands']['value'],value)
                self.assertEqual(row['length'],len(header)+3)
                self.assertIsNone(_branch(data,row))
                for length in range(1,row['length']):
                    self.assertEqual(inspect_record(data[:length],0)['instructions'],[])

@unittest.skipUnless(os.environ.get('LEGAIA_DISC_BIN'),'requires private retail disc')
class RetailMenu8Proof(unittest.TestCase):
    def test_native_tables_walker_loop_acquire_and_fixed_writes(self):
        with _disc_context(os.environ['LEGAIA_DISC_BIN']) as (image,_,_,archive):
            data=archive.read_entry(archive.entry(897),extended=True)
            exe=image.read_file(image.find('SCUS_942.54'))
        self.assertEqual(hashlib.sha256(data).hexdigest(),'216f846db5ab085a295cef4064747380a06c995caa3e1b2773e78a1d349f126b')
        self.assertEqual(hashlib.sha256(exe).hexdigest(),'292256e2e66db42727f613406785e444254d3f699569e611f65fcf1c6d2f3482')
        word=lambda a:struct.unpack_from('<I',data,a-0x801ce818)[0]
        target=lambda a:a+4+struct.unpack('<h',struct.pack('<H',word(a)&65535))[0]*4
        for a,v in ((0x801cef48,0x801e1ecc),(0x801cef50,0x801e206c),(0x801cef54,0x801e20a8),(0x801cef58,0x801e2134),
                    (0x801e20dc,0x0c07558c),(0x801e20f4,0xa0600003),(0x801e20f8,0xa0620002),
                    (0x801e212c,0x08078d89),(0x801e2130,0x27de0007),
                    (0x801e1f78,0x27de0003),(0x801e1f88,0x92d70000),
                    (0x801e1f98,0x0c00f28e),(0x801e1fa0,0x24420001),
                    (0x801e1fa4,0x03c2f021),(0x801e1fa8,0x02c2b021),
                    (0x801dee4c,0x0280f021),(0x801e2070,0x92d20001),
                    (0x801e2098,0x27de0003),(0x801e2134,0x27de0003),
                    (0x801e2138,0x92c30001),(0x801e2144,0xac43b630),
                    (0x801cef6c,0x801e22c8),(0x801e22cc,0x26c40001),
                    (0x801e22d8,0xa4623f00),(0x801e3620,0x27de0004)):
            self.assertEqual(word(a),v,hex(a))
        self.assertEqual(target(0x801e1f58),0x801dee4c)
        self.assertEqual(target(0x801e1fb4),0x801e1f98)
        load=struct.unpack_from('<I',exe,0x18)[0]
        ew=lambda a:struct.unpack_from('<I',exe,a-load+0x800)[0]
        for a,v in ((0x8003ca3c,0x240600c0),(0x8003ca48,0x2c62001f),
                    (0x8003ca50,0x306200f0),(0x8003ca5c,0x24840001),
                    (0x8003ca60,0x24a50001),(0x8003ca64,0x24840001),
                    (0x8003ca6c,0x24a50001),(0x8003ca74,0x00a01021)):
            self.assertEqual(ew(a),v,hex(a))

if __name__=='__main__':unittest.main()
