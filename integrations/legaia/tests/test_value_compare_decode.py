"""Retail value-comparison widths, signed thresholds and target-only ownership."""
import hashlib
import os
import struct
import unittest
from importer.pipeline import _disc_context
from importer.script_inspection import inspect_record, _instruction
from importer.branch_authoring import _branch, _graph_candidate
from importer.core import ImportError as RetailImportError

class ValueCompareDecode(unittest.TestCase):
    def record(self, source, comparison, extended=False, low=0x8000, high=0xffff):
        header = bytes((0xce,7)) if extended else b'\x4e'
        size = 8 if source in (10,11) else 6
        data = header + bytes((2,source*16+comparison)) + struct.pack('<HH',low,size-4)
        if size==8: data += struct.pack('<H',high)
        return data+b'\x21\x26\xfe\xff', len(header),size

    def test_all_mode_nibbles_and_headers_have_exact_qualified_edges(self):
        for extended in (False,True):
            for source in range(16):
                for comparison in range(16):
                    with self.subTest(extended=extended,source=source,comparison=comparison):
                        data,header,size=self.record(source,comparison,extended)
                        report=inspect_record(data,0);self.assertFalse(report['stops'],report['stops'])
                        row=report['instructions'][0]
                        self.assertEqual(row['length'],header+size)
                        self.assertEqual(row['target_context'],7 if extended else None)
                        self.assertEqual(row['operands']['source_mode'],source)
                        self.assertEqual(row['operands']['comparison_mode'],comparison)
                        self.assertEqual(row['operands']['runtime_value'],'not_observed')
                        enabled=source<12 and comparison<2
                        self.assertEqual(row['mnemonic'],'VALUE_COMPARE_BRANCH' if enabled else 'VALUE_COMPARE_CONTINUE')
                        if enabled:
                            self.assertEqual(row['successors'],[{'pc':header+size,'condition':'comparison_true'},
                                                               {'pc':header+size,'condition':'comparison_false'}])
                            self.assertEqual(_branch(data,row)['operand_pc'],header+4)
                        else:
                            self.assertIsNone(_branch(data,row))
                            self.assertEqual(row['successors'],[{'pc':header+size,'condition':
                                'source_default_no_branch' if source>=12 else 'comparison_mode_no_branch'}])

    def test_signed_threshold_words_and_split_bank_high_word(self):
        for source in range(12):
            for low in (0,32767,32768,65535):
                for high in (0,32767,32768,65535):
                    data,header,size=self.record(source,0,True,low,high)
                    row=_instruction(data,0)
                    raw=low|(high<<16) if size==8 else low
                    width=32 if size==8 else 16
                    expected=raw-(1<<width) if raw&(1<<(width-1)) else raw
                    self.assertEqual(row['operands']['threshold'],expected)
                    self.assertEqual(row['operands']['threshold_width'],width)
                    self.assertEqual(row['operands']['comparison'],'value_lt_threshold')
                    self.assertEqual(row['operands']['threshold_scaling'],
                        'runtime_factor_mul_i32_div256_toward_zero' if source<2 else 'none')
        self.assertEqual(_instruction(self.record(4,1)[0],0)['operands']['value_source'],'bios_random_low_byte')

    def test_truncation_wrap_and_ignored_destination_never_recover_bytes(self):
        for extended in (False,True):
            for source in range(16):
                data,header,size=self.record(source,0,extended)
                for length in range(1,header+size):
                    report=inspect_record(data[:length],0)
                    self.assertEqual(report['instructions'],[]);self.assertTrue(report['stops'])
                changed=bytearray(data);changed[header+4:header+6]=b'\xfe\xff'
                row=_instruction(bytes(changed),0)
                self.assertEqual(row['operands']['encoded_target'],header+2)
                if source>=12:self.assertFalse(inspect_record(bytes(changed),0)['stops'])
        data=b'\x4e\x00\x00\x1f\x26\xff\x7f\x00\x1fHidden\0'
        report=inspect_record(data,0);self.assertTrue(report['stops']);self.assertEqual(report['dialogues'],[])

    def test_target_rewrite_preserves_selector_mode_and_both_threshold_words(self):
        for source in range(12):
            for comparison in (0,1):
                for extended in (False,True):
                    data,header,size=self.record(source,comparison,extended)
                    graph=inspect_record(data,0);changed=bytearray(data)
                    # Retarget to the existing JMP immediately after the NOP.
                    changed[header+4:header+6]=struct.pack('<H',size-3)
                    candidate=_graph_candidate(data,bytes(changed),0,graph)
                    self.assertFalse(candidate['stops'])
                    immutable=[header,header+1,header+2,header+3]
                    if size==8: immutable += [header+6,header+7]
                    for at in immutable:
                        bad=bytearray(changed);bad[at]^=1
                        with self.assertRaises(RetailImportError):_graph_candidate(data,bytes(bad),0,graph)

class Menu49Continuation(unittest.TestCase):
    def test_field_write_and_ramp_always_keep_the_encoded_continuation(self):
        for extended in (False,True):
            for ticks in (0,1,32767,-32768,-1):
                header=bytes((0xcc,7)) if extended else bytes((0x4c,))
                data=header+bytes((0x49,))+struct.pack('<hh',-123,ticks)+bytes((0x21,0x26,0xfe,0xff))
                report=inspect_record(data,0);self.assertFalse(report['stops'])
                row=report['instructions'][0]
                self.assertEqual(row['mnemonic'],'FIELD_4A_STATE_WRITE')
                self.assertEqual(row['length'],len(header)+5)
                self.assertEqual(row['operands']['ticks_signed'],ticks)
                self.assertEqual(row['operands']['value'],-123)
                self.assertFalse(row['operands']['can_yield'])
                self.assertNotIn('target',row['operands'])
                self.assertIsNone(_branch(data,row))
                self.assertEqual(row['successors'],[{'pc':len(header)+5,'condition':'encoded_continuation'}])
                for length in range(1,len(header)+5):
                    short=inspect_record(data[:length],0)
                    self.assertEqual(short['instructions'],[]);self.assertTrue(short['stops'])

@unittest.skipUnless(os.environ.get('LEGAIA_DISC_BIN'),'requires private retail disc')
class RetailValueCompareProof(unittest.TestCase):
    def test_hash_bound_dispatch_signed_loaders_comparisons_and_relative_exits(self):
        with _disc_context(os.environ['LEGAIA_DISC_BIN']) as (image,_,_,archive):
            data=archive.read_entry(archive.entry(897),extended=True)
            exe=image.read_file(image.find('SCUS_942.54'))
        self.assertEqual(hashlib.sha256(data).hexdigest(),'216f846db5ab085a295cef4064747380a06c995caa3e1b2773e78a1d349f126b')
        self.assertEqual(hashlib.sha256(exe).hexdigest(),'292256e2e66db42727f613406785e444254d3f699569e611f65fcf1c6d2f3482')
        word=lambda a:struct.unpack_from('<I',data,a-0x801ce818)[0]
        target=lambda a:a+4+struct.unpack('<h',struct.pack('<H',word(a)&65535))[0]*4
        self.assertEqual(word(0x801cee70),0x801e1138)
        self.assertEqual(word(0x801cef1c),0x801e1480)
        self.assertEqual(word(0x801e1138),0x27de0006)
        self.assertEqual(word(0x801e1140),0x26c40003)
        self.assertEqual(word(0x801e1488),0x3c020200)
        self.assertEqual(word(0x801e1494),0x3c020100)
        # Both nonzero-duration ramps return the already-advanced PC.
        self.assertEqual(word(0x801e175c),0x0c00f17c)
        self.assertEqual(word(0x801e205c),0x0c00f17c)
        for a in (0x801e1768,0x801e2068): self.assertEqual(word(a),0x03c01021)
        # Zero-duration writes exit through the same advanced-PC return.
        for a in (0x801e14d0,0x801e15ac,0x801e1600):
            self.assertEqual((word(a)&0x3ffffff)<<2|0x80000000,0x801e3624)
        self.assertEqual(word(0x801ced74),0x801e0a04)
        expected=[0x801e0a40,0x801e0a70,0x801e0ac0,0x801e0aec,0x801e0afc,
                  0x801e0b0c,0x801e0b0c,0x801e0b0c,0x801e0b0c,0x801e0b34,0x801e0b50,0x801e0b60]
        self.assertEqual([word(0x801cee30+i*4) for i in range(12)],expected)
        self.assertEqual(word(0x801e0a14),0x2c62000c) # C..F select initialized zero values
        self.assertEqual(target(0x801e0a18),0x801e0b88)
        self.assertEqual(word(0x801e0ae0),0x905106f8) # level byte
        self.assertEqual(word(0x801e0b28),0x84510000) # signed slot word
        self.assertEqual(word(0x801e0b08),0x305100ff) # random &255
        self.assertEqual(word(0x801e0b7c),0x3210ffff) # low bank word unsigned pack
        self.assertEqual(word(0x801e0b80),0x00021400) # high bank word <<16
        self.assertEqual(word(0x801e0bb0),0x0230102a) # signed state<threshold
        self.assertEqual(word(0x801e0ba4),0x0211102a) # signed threshold<state
        self.assertEqual(target(0x801e0bdc),0x801e212c)
        self.assertEqual(target(0x801e0bf4),0x801e24f0)
        for a in (0x801e0be0,0x801e0bf8):self.assertEqual(word(a),0x27c20005)
        self.assertEqual(word(0x801e2130),0x27de0007)
        self.assertEqual(word(0x801e24f4),0x27de0009)
        self.assertEqual(word(0x801e3604),0x0044f021) # PC+5 + unsigned branch word
        load=struct.unpack_from('<I',exe,0x18)[0]
        exe_word=lambda a:struct.unpack_from('<I',exe,a-load+0x800)[0]
        self.assertEqual(exe_word(0x8003ceac),0x00021400)
        self.assertEqual(exe_word(0x8003ceb4),0x00021403) # threshold helper signextends16

if __name__=='__main__':unittest.main()
