"""Retail existing-actor capture retains conditional parent ownership."""
import hashlib, os, struct, unittest
from importer.script_inspection import inspect_record
from importer.branch_authoring import _branch
from importer.pipeline import _disc_context
import test_effect_spawn_decode as spawn_tests

class EffectExistingActorDecode(spawn_tests.EffectSpawnDecode):
    def packet(self, extended):
        return (bytes((0xb4,7)) if extended else b'\x34') + b'\x2f'

    def test_base_packet_and_following_byte_both_headers(self):
        for extended in (False, True):
            packet = self.packet(extended)
            data = packet + b'\x21\x26\xfe\xff'
            report = inspect_record(data, 0)
            self.assertFalse(report['stops'])
            row = report['instructions'][0]
            self.assertEqual(row['mnemonic'], 'EFFECT_EXISTING_ACTOR_CAPTURE_REQUEST')
            self.assertEqual(row['length'], len(packet))
            self.assertEqual(row['operands']['following_byte'], 0x21)
            self.assertEqual(row['target_context'], 7 if extended else None)
            self.assertEqual(row['successors'], [{'pc':len(packet), 'condition':'encoded_continuation'}])
            self.assertIsNone(_branch(data, row))

    def test_capture_descriptor_does_not_claim_parent_dialogue_or_destinations(self):
        for extended in (False, True):
            for payload in (b'', b'\x1fHidden\0\x21', bytes(255)):
                packet = self.packet(extended)
                data = packet + b'\x40' + bytes((len(payload),)) + payload + b'\x21'
                report = inspect_record(data, 0)
                row = report['instructions'][0]
                self.assertTrue(report['stops'])
                self.assertEqual(row['length'], len(packet))
                self.assertEqual(row['successors'], [])
                self.assertEqual(row['operands']['capture_payload'], {'pc':len(packet)+2, 'length':len(payload), 'encoded_hex':payload.hex()})
                self.assertEqual(row['operands']['conditional_continuations'], {'missing_actor':len(packet), 'matched_actor_capture':len(packet)+2+len(payload)})
                self.assertEqual(report['dialogues'], [])
                self.assertIsNone(_branch(data, row))

    def test_exact_end_of_capture_remains_a_separate_parent_boundary(self):
        packet = self.packet(False)
        payload = b'\x1fCaptured\0'
        end = 7 + len(packet) + 2 + len(payload)
        branch = b'\x4d\0\0\0\0' + struct.pack('<H', end-5)
        data = branch+packet+b'\x40'+bytes((len(payload),))+payload+b'\x1fOutside\0'
        report = inspect_record(data, 0)
        self.assertEqual([row['mnemonic'] for row in report['instructions']], ['BBOX_TEST','EFFECT_EXISTING_ACTOR_CAPTURE_REQUEST'])
        self.assertEqual([(row['pc'],row['text']) for row in report['dialogues']], [(end,'Outside')])
        self.assertEqual(report['opaque_regions'][0]['pc'], 7+len(packet))
        self.assertEqual(report['opaque_regions'][0]['length'], 2+len(payload))
        self.assertTrue(report['stops'])

@unittest.skipUnless(os.environ.get('LEGAIA_DISC_BIN'), 'requires private retail disc')
class RetailExistingActorProof(unittest.TestCase):
    def test_native_match_marker_pointer_length_and_advance(self):
        with _disc_context(os.environ['LEGAIA_DISC_BIN']) as (_,_,_,archive):
            data = archive.read_entry(archive.entry(897), extended=True)
        self.assertEqual(hashlib.sha256(data).hexdigest(), '216f846db5ab085a295cef4064747380a06c995caa3e1b2773e78a1d349f126b')
        expected = ((0x801ced0c,0x801dfcac),(0x801dfcb4,0x00021902),
                    (0x801dfefc,0x14620047),(0x801dff00,0x24020002),
                    (0x801e001c,0x1462001f),(0x801e0028,0x8c44c354),
                    (0x801e003c,0x1080fc16),(0x801e0044,0x8c820090),
                    (0x801e004c,0x10550006),(0x801e0068,0x1080fc0b),
                    (0x801e006c,0x26d60001),(0x801e0070,0x92c30000),
                    (0x801e0074,0x24020040),(0x801e0078,0x1462fc07),
                    (0x801e007c,0x26c20002),(0x801e0080,0xac820094),
                    (0x801e0084,0xa480009e),(0x801e0088,0xa480009c),
                    (0x801e008c,0x92c30001),(0x801e0090,0x27c20002),
                    (0x801e0094,0x08077c26),(0x801e0098,0x0043f021),
                    (0x801df098,0x27de0002),(0x801df09c,0x08078d8a))
        for address, value in expected:
            self.assertEqual(struct.unpack_from('<I', data, address-0x801ce818)[0], value, hex(address))

if __name__ == '__main__': unittest.main()
