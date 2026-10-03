"""Retail STATE_RESUME0 variable completion owns its arguments and native payload."""
import hashlib
import os
import struct
import unittest
from importer.pipeline import _disc_context
from importer.script_inspection import inspect_record,MAX_MESSAGE_TOKENS
from importer.branch_authoring import _branch

class EmbeddedResumeDecode(unittest.TestCase):
    def data(self, extended=False, length=3, payload=b'\x1f\x5e\xc0\x00\xff\x1e'):
        header=bytes((0xc9,7)) if extended else b'\x49'
        arguments=(b'\x1f\x26\x00'*86)[:length]
        return header+bytes((0,255,length))+arguments+payload+b'\x21\x26\xfe\xff',header,arguments

    def test_argument_count_is_at_plus_two_and_native_payload_is_opaque(self):
        for extended in (False,True):
            for length in (0,3,255):
                data,header,arguments=self.data(extended,length)
                report=inspect_record(data,0);self.assertFalse(report['stops'],report['stops'])
                row=report['instructions'][0];start=len(header)+3+length
                self.assertEqual(row['mnemonic'],'STATE_RESUME')
                self.assertEqual(row['target_context'],7 if extended else None)
                self.assertEqual(row['length'],start+6)
                args=row['operands'];self.assertEqual(args['prefix_byte'],255)
                self.assertEqual(args['argument_length'],length)
                self.assertEqual(args['arguments'],list(arguments))
                self.assertEqual(args['embedded_payload'],{'pc':start,'length':6,'terminator':30,'token_count':4})
                self.assertEqual(row['successors'],[{'pc':start+6,'condition':'external_state_completed'}])
                self.assertEqual(report['dialogues'],[])
                self.assertIsNone(_branch(data,row))

    def test_all_truncation_boundaries_and_limits_stop_without_recovery(self):
        for extended in (False,True):
            data,header,_=self.data(extended)
            instruction_length=len(data)-4
            for length in range(1,instruction_length):
                report=inspect_record(data[:length],0)
                self.assertEqual(report['instructions'],[]);self.assertTrue(report['stops'])
            for payload in (b'\xc0',b'A'*MAX_MESSAGE_TOKENS+b'\0'):
                data=header+bytes((0,255,0))+payload
                report=inspect_record(data,0)
                self.assertEqual(report['instructions'],[]);self.assertTrue(report['stops'])

    def test_empty_payload_and_unknown_following_bytes_have_exact_ownership(self):
        for extended in (False,True):
            data,header,_=self.data(extended,0,b'\0')
            report=inspect_record(data,0);self.assertFalse(report['stops'])
            self.assertEqual(report['instructions'][0]['length'],len(header)+4)
            data=data[:-4]+b'\x00\x1fHidden\0'
            report=inspect_record(data,0);self.assertEqual(len(report['instructions']),1)
            self.assertTrue(report['stops']);self.assertEqual(report['dialogues'],[])
        data=b'\x4d\x00\x00\x00\x00'+struct.pack('<H',14-5)+b'\x49\x00\xff\x03\x1f\x26\x00\x1f\x5e\x00\x21\x26\xfe\xff'
        report=inspect_record(data,0);self.assertTrue(report['stops'])
        self.assertTrue(any('overlap' in s['reason'] or 'interior' in s['reason'] or 'conflict' in s['reason'] for s in report['stops']))

@unittest.skipUnless(os.environ.get('LEGAIA_DISC_BIN'),'requires private retail disc')
class RetailEmbeddedResumeProof(unittest.TestCase):
    def test_completion_argument_pointer_and_native_walker_are_hash_bound(self):
        with _disc_context(os.environ['LEGAIA_DISC_BIN']) as (image,_,_,archive):
            data=archive.read_entry(archive.entry(897),extended=True)
            exe=image.read_file(image.find('SCUS_942.54'))
        self.assertEqual(hashlib.sha256(data).hexdigest(),'216f846db5ab085a295cef4064747380a06c995caa3e1b2773e78a1d349f126b')
        self.assertEqual(hashlib.sha256(exe).hexdigest(),'292256e2e66db42727f613406785e444254d3f699569e611f65fcf1c6d2f3482')
        word=lambda a:struct.unpack_from('<I',data,a-0x801ce818)[0]
        for a,v in ((0x801ced60,0x801e08c4),(0x801e08ec,0x92c40002),
                    (0x801e08f4,0x24970004),(0x801e08f8,0x03d7f021),
                    (0x801e08fc,0x24840003),(0x801e0900,0x0c00f28e),
                    (0x801e0904,0x02c42021),(0x801e0908,0x03d11821),
                    (0x801e0910,0x0062f021)):
            self.assertEqual(word(a),v,hex(a))
        load=struct.unpack_from('<I',exe,0x18)[0]
        ew=lambda a:struct.unpack_from('<I',exe,a-load+0x800)[0]
        self.assertEqual(ew(0x8003ca48),0x2c62001f)
        self.assertEqual(ew(0x8003ca50),0x306200f0)
        self.assertEqual(ew(0x8003ca3c),0x240600c0)

if __name__=='__main__':unittest.main()
