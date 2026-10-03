"""Retail MENU_CTRL8C/8D widths, relative PCs and immutable search operands."""
import hashlib
import os
import struct
import unittest
from importer.pipeline import _disc_context
from importer.script_inspection import inspect_record
from importer.branch_authoring import _branch, _graph_candidate
from importer.core import ImportError as RetailImportError


class Branch8CDTests(unittest.TestCase):
    def test_relative_targets_conditions_and_widths_both_headers(self):
        for extended in (False, True):
            for sub, size, relative, name, condition in (
                (0x8C, 3, 1, 'FIELD_68_BRANCH', 'field_68_zero'),
                (0x8D, 5, 3, 'ACTOR_SEARCH_BRANCH', 'search_match')):
                header=bytes((0xCC,7)) if extended else b'\x4c'
                body=bytes((sub,))+(b'\x02\x19' if sub==0x8D else b'')
                # delta2 points to the first following NOP, not absolute PC2.
                data=bytes(5)+header+body+b'\x02\0\x21\x26\xff\xff'
                report=inspect_record(data,5)
                self.assertFalse(report['stops'], report['stops'])
                row=report['instructions'][0];operand=5+len(header)
                self.assertEqual(row['mnemonic'],name)
                self.assertEqual(row['length'],len(header)+size)
                self.assertEqual(row['target_context'],7 if extended else None)
                self.assertEqual(row['successors'],[
                    {'pc':operand+relative+2,'condition':condition},
                    {'pc':operand+size,'condition':'field_68_nonzero' if sub==0x8C else 'search_empty_or_no_match'}])
                qualified=_branch(data,row)
                self.assertEqual(qualified['operand_pc'],operand+relative)
                self.assertEqual(qualified['target_pc'],operand+size)
                if sub==0x8D:
                    self.assertEqual(row['operands']['character_selector'],2)
                    self.assertEqual(row['operands']['marker'],25)

    def test_signed_word_wrap_and_unknown_tail_are_not_recovered(self):
        for sub, prefix, relative in [(0x8C,b'',1),(0x8D,b'\xff\xff',3)]:
            data=b'\x4c'+bytes((sub,))+prefix+struct.pack('<h',-32768)+b'\x00\x1fOpaque\0'
            report=inspect_record(data,0);row=report['instructions'][0]
            self.assertEqual(row['successors'][0]['pc'],(1+relative-32768)&65535)
            self.assertEqual(report['dialogues'],[])
            self.assertTrue(report['stops'])
            for length in range(1,row['length']):
                short=inspect_record(data[:length],0)
                self.assertEqual(short['instructions'],[])

    def test_graph_retarget_preserves_search_selector_marker_and_dispatch(self):
        for extended in (False, True):
            header=bytes((0xcc,7)) if extended else b'\x4c'
            body=b'\x8d\x02\x19\x03\0\x21\x26\xff\xff'
            data=header+body;source=inspect_record(data,0)
            self.assertFalse(source['stops'])
            changed=bytearray(data);base=len(header)+3;changed[base:base+2]=struct.pack('<h',2)
            candidate=_graph_candidate(data,bytes(changed),0,source)
            self.assertEqual(candidate['entry_pc'],0)
            self.assertEqual(bytes(changed)[:base],data[:base])
            for at in [len(header)+1,len(header)+2]:
                invalid=bytearray(changed);invalid[at]^=1
                with self.assertRaises(RetailImportError):_graph_candidate(data,bytes(invalid),0,source)


@unittest.skipUnless(os.environ.get('LEGAIA_DISC_BIN'),'requires private unchanged retail disc')
class RetailBranch8CDProof(unittest.TestCase):
    def test_dispatch_table_handlers_and_shared_relative_exit(self):
        with _disc_context(os.environ['LEGAIA_DISC_BIN']) as (_,_,_,archive):
            data=archive.read_entry(archive.entry(897),extended=True)
        self.assertEqual(hashlib.sha256(data).hexdigest(),'216f846db5ab085a295cef4064747380a06c995caa3e1b2773e78a1d349f126b')
        word=lambda address:struct.unpack_from('<I',data,address-0x801ce818)[0]
        self.assertEqual(word(0x801cee80),0x801e1ea0)
        self.assertEqual(word(0x801cef78),0x801e23ec)
        self.assertEqual(word(0x801cef7c),0x801e2404)
        fields=lambda value:(value>>26,(value>>21)&31,(value>>16)&31,value&65535)
        for address,expected in [
            (0x801e23ec,(33,21,2,0x68)),(0x801e23f8,(9,30,30,4)),
            (0x801e2400,(9,22,4,1)),(0x801e2404,(9,30,30,6)),
            (0x801e240c,(36,22,3,1)),(0x801e2444,(36,22,5,2)),
            (0x801e3608,(9,22,4,3)),
            (0x801e3614,(9,2,2,65534))]:self.assertEqual(fields(word(address)),expected,hex(address))
        target=lambda address:address+4+((word(address)&65535)-65536 if word(address)&32768 else word(address)&65535)*4
        self.assertEqual(target(0x801e23f4),0x801e3624)
        self.assertEqual(target(0x801e2434),0x801e3624)
        self.assertEqual(target(0x801e245c),0x801e3608)
        self.assertEqual(word(0x801e2470)&0x3ffffff,0x801e3628>>2&0x3ffffff)
        self.assertEqual(word(0x801e2474),0x03c01021) # v0=s8, already advanced by6.


if __name__=='__main__':unittest.main()
