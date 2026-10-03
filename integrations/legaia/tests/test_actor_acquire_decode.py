"""Native actor acquire continuations, without invented resume PC operands."""
import hashlib,os,struct,unittest
from importer.pipeline import _disc_context
from importer.script_inspection import inspect_record
from importer.branch_authoring import _branch
class ActorAcquireDecode(unittest.TestCase):
    def test_all_forms_headers_signed_parameters_and_conditional_edges(self):
        for extended in (False,True):
            for sub in (0,1,10,11):
                for values in ((-32768,32767),(-1,0)):
                    header=bytes((0xc3,7)) if extended else b'\x43'
                    payload=bytes((sub,0,255))+struct.pack('<2h',*values)
                    if sub>=10:payload+=struct.pack('<h',-32768)
                    data=header+payload+b'\x21\x26\xfe\xff'
                    report=inspect_record(data,0);self.assertFalse(report['stops'])
                    row=report['instructions'][0];args=row['operands']
                    self.assertEqual(row['mnemonic'],'ACTOR_ACQUIRE_REQUEST')
                    self.assertEqual(row['length'],len(header)+len(payload))
                    self.assertEqual(args['encoded_xz'],[0,255])
                    self.assertEqual(args['parameters_i16'],list(values))
                    if sub>=10:self.assertEqual(args['vertical_operand_i16'],-32768)
                    else:self.assertNotIn('vertical_operand_i16',args)
                    self.assertEqual(row['target_context'],7 if extended else None)
                    self.assertEqual(row['successors'],[{'pc':row['length'],'condition':'actor_acquisition_succeeded'},{'pc':0,'condition':'actor_acquisition_pending'}])
                    self.assertIsNone(_branch(data,row));self.assertEqual(report['dialogues'],[])
                    self.assertNotIn('resume_pc',args);self.assertNotIn('target_position',args)
    def test_all_truncation_boundaries_and_unknown_tail_fail_closed(self):
        for extended in (False,True):
            for sub in (0,1,10,11):
                header=bytes((0xc3,7)) if extended else b'\x43'
                full=header+bytes((sub,))+bytes(8 if sub>=10 else 6)
                for length in range(1,len(full)):
                    report=inspect_record(full[:length],0)
                    self.assertEqual(report['instructions'],[]);self.assertTrue(report['stops'])
                report=inspect_record(full+b'\x00\x1fHidden\0',0)
                self.assertEqual(len(report['instructions']),1);self.assertTrue(report['stops']);self.assertEqual(report['dialogues'],[])
    def test_parameters_cannot_be_owned_as_instruction_destinations(self):
        data=b'\x4d\x00\x00\x00\x00'+struct.pack('<H',11-5)+b'\x43\x00\x00\x00\x21\x21\x21\x21\x21\x26\xfe\xff'
        report=inspect_record(data,0)
        self.assertTrue(any('overlap' in s['reason'] or 'interior' in s['reason'] or 'conflict' in s['reason'] for s in report['stops']),report['stops'])
@unittest.skipUnless(os.environ.get('LEGAIA_DISC_BIN'),'requires private retail disc')
class RetailActorAcquireProof(unittest.TestCase):
    def test_shared_tables_acquisition_parameters_wide_extent_and_returns(self):
        with _disc_context(os.environ['LEGAIA_DISC_BIN']) as (_,_,_,archive):data=archive.read_entry(archive.entry(897),extended=True)
        self.assertEqual(hashlib.sha256(data).hexdigest(),'216f846db5ab085a295cef4064747380a06c995caa3e1b2773e78a1d349f126b')
        word=lambda a:struct.unpack_from('<I',data,a-0x801ce818)[0]
        for a in (0x801ceda8,0x801cedac,0x801cedd0,0x801cedd4):self.assertEqual(word(a),0x801df384)
        for a,w in ((0x801df410,0x1040fe8e),(0x801dee4c,0x0280f021),(0x801dee54,0x03c01021),
                    (0x801df518,0x2c42000a),(0x801df528,0x26c40007),(0x801df534,0x27de0002),
                    (0x801df550,0x26c40003),(0x801df554,0x26c40005),(0x801df580,0x26c40003),
                    (0x801df584,0x26c40005),(0x801df5ac,0x0c07497b),(0x801df5b4,0x08078d89),
                    (0x801df5b8,0x27de0008),(0x801e3624,0x03c01021)):
            self.assertEqual(word(a),w,hex(a))
if __name__=='__main__':unittest.main()
