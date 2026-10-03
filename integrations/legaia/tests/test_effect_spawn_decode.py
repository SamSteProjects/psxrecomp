"""Spawn packet inspection keeps conditional captures out of parent flow."""
import hashlib,os,struct,unittest
from importer.script_inspection import inspect_record
from importer.branch_authoring import _branch
from importer.pipeline import _disc_context
class EffectSpawnDecode(unittest.TestCase):
    def packet(self,extended):return (bytes((0xb4,7)) if extended else b'\x34')+b'\x1f'+bytes(range(11))
    def test_base_packet_and_following_byte_both_headers(self):
        for extended in (False,True):
            packet=self.packet(extended);report=inspect_record(packet+b'\x21\x26\xfe\xff',0)
            self.assertFalse(report['stops']);row=report['instructions'][0]
            self.assertEqual(row['mnemonic'],'EFFECT_SPAWN_PACKET');self.assertEqual(row['length'],len(packet))
            self.assertEqual(row['operands']['packet_bytes'],list(range(11)))
            self.assertEqual(row['operands']['following_byte'],0x21)
            self.assertEqual(row['target_context'],7 if extended else None)
            self.assertEqual(row['successors'],[{'pc':len(packet),'condition':'encoded_continuation'}])
            self.assertIsNone(_branch(packet+b'\x21',row))
    def test_capture_descriptor_does_not_claim_parent_dialogue_or_destinations(self):
        for extended in (False,True):
            for payload in (b'',b'\x1fHidden\0\x21',bytes(255)):
                packet=self.packet(extended);data=packet+b'\x40'+bytes((len(payload),))+payload+b'\x21'
                report=inspect_record(data,0);self.assertTrue(report['stops']);self.assertEqual(len(report['instructions']),1)
                row=report['instructions'][0];self.assertEqual(row['length'],len(packet));self.assertEqual(row['successors'],[])
                self.assertEqual(row['operands']['capture_payload'],{'pc':len(packet)+2,'length':len(payload),'encoded_hex':payload.hex()})
                self.assertEqual(row['operands']['conditional_continuations'],{'existing_actor':len(packet),'new_actor_capture':len(packet)+2+len(payload)})
                self.assertEqual(report['dialogues'],[]);self.assertIsNone(_branch(data,row))
    def test_base_peek_and_every_capture_truncation_fail_closed(self):
        for extended in (False,True):
            packet=self.packet(extended);full=packet+b'\x40\x03\x1f\x21\0'
            for length in range(1,len(full)):
                report=inspect_record(full[:length],0);self.assertEqual(report['instructions'],[]);self.assertTrue(report['stops'])
@unittest.skipUnless(os.environ.get('LEGAIA_DISC_BIN'),'requires private retail disc')
class RetailEffectSpawnProof(unittest.TestCase):
    def test_native_existing_match_capture_extent_and_shared_advance(self):
        with _disc_context(os.environ['LEGAIA_DISC_BIN']) as (_,_,_,archive):data=archive.read_entry(archive.entry(897),extended=True)
        self.assertEqual(hashlib.sha256(data).hexdigest(),'216f846db5ab085a295cef4064747380a06c995caa3e1b2773e78a1d349f126b')
        word=lambda a:struct.unpack_from('<I',data,a-0x801ce818)[0]
        for a,w in ((0x801ced0c,0x801dfcac),(0x801dff48,0x14800bd5),(0x801dffe0,0x0c07959a),
                    (0x801dffec,0x26d6000c),(0x801dfff0,0x92c30000),(0x801dfff4,0x24020040),
                    (0x801dfff8,0x14620ba9),(0x801e0000,0xaea20094),(0x801e000c,0x92c30001),
                    (0x801e0010,0x27c20002),(0x801e0018,0x0043f021),(0x801e2ea4,0x27de000d)):
            self.assertEqual(word(a),w,hex(a))
if __name__=='__main__':unittest.main()
