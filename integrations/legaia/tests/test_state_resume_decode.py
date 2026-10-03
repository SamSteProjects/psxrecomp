"""STATE_RESUME completion boundaries; no menu execution or payload authoring."""
import hashlib
import os
import struct
import unittest
from importer.pipeline import _disc_context
from importer.script_inspection import inspect_record
from importer.branch_authoring import _branch

SIZES = {1: 2, 3: 2, 7: 2, 2: 6, 4: 6, 5: 13,
         6: 4, 8: 4, 9: 4, 12: 4, 13: 4}

class StateResumeDecode(unittest.TestCase):
    def test_fixed_completion_boundaries_preserve_opaque_payload(self):
        for extended in (False, True):
            for sub, size in SIZES.items():
                with self.subTest(extended=extended, sub=sub):
                    header = bytes((0xc9, 7)) if extended else b'\x49'
                    # Payload intentionally resembles MES/jump bytes; never scan it.
                    payload = (b'\x1f\x26\xff\x00' * 4)[:size - 1]
                    data = header + bytes((sub,)) + payload + b'\x21\x26\xfe\xff'
                    report = inspect_record(data, 0)
                    self.assertFalse(report['stops'], report['stops'])
                    row = report['instructions'][0]
                    self.assertEqual(row['length'], len(header) + size)
                    self.assertEqual(row['target_context'], 7 if extended else None)
                    self.assertEqual(row['operands']['payload'], list(payload))
                    self.assertEqual(row['operands']['runtime_state'], 'not_observed')
                    self.assertEqual(row['successors'], [{'pc':len(header)+size,
                                                          'condition':'external_state_completed'}])
                    self.assertEqual(report['dialogues'], [])
                    self.assertIsNone(_branch(data, row))

    def test_every_truncated_form_stops_without_recovery(self):
        for extended in (False, True):
            for sub, size in SIZES.items():
                header = bytes((0xc9, 7)) if extended else b'\x49'
                full = header + bytes((sub,)) + bytes(size-1)
                for length in range(1, len(full)):
                    report = inspect_record(full[:length], 0)
                    self.assertEqual(report['instructions'], [])
                    self.assertTrue(report['stops'])

    def test_malformed_embedded_and_nonadvancing_forms_stop(self):
        for sub in (0, 10, 11, 14, 255):
            report = inspect_record(bytes((0x49,sub,0x1f,65,0,0x21)), 0)
            self.assertTrue(report['stops'])
            self.assertEqual(report['instructions'], [])
            self.assertEqual(report['dialogues'], [])

@unittest.skipUnless(os.environ.get('LEGAIA_DISC_BIN'), 'requires private retail disc')
class RetailStateResumeProof(unittest.TestCase):
    def test_dispatch_completion_and_fixed_exits_from_hashed_source(self):
        with _disc_context(os.environ['LEGAIA_DISC_BIN']) as (_,_,_,archive):
            data = archive.read_entry(archive.entry(897), extended=True)
        self.assertEqual(hashlib.sha256(data).hexdigest(),
                         '216f846db5ab085a295cef4064747380a06c995caa3e1b2773e78a1d349f126b')
        word = lambda a: struct.unpack_from('<I',data,a-0x801ce818)[0]
        target = lambda a: a+4+struct.unpack('<h',struct.pack('<H',word(a)&65535))[0]*4
        self.assertEqual(word(0x801ced60), 0x801e08c4)
        self.assertEqual(word(0x801e08c8), 0x8e02b450) # read external state
        self.assertEqual(word(0x801e08cc), 0x24110001) # completed sentinel1
        self.assertEqual(target(0x801e08d0), 0x801e097c)
        for a in (0x801e0914,0x801e091c,0x801e0924): self.assertEqual(target(a),0x801e00b8)
        for a in (0x801e092c,0x801e0934): self.assertEqual(target(a),0x801e212c)
        for a in (0x801e094c,0x801e0954,0x801e095c,0x801e0964): self.assertEqual(target(a),0x801df898)
        for a,delta in ((0x801e00b8,3),(0x801e2130,7),(0x801e0948,14),
                        (0x801df898,5),(0x801e0978,5)):
            self.assertEqual(word(a),0x27de0000|delta)
        self.assertEqual(target(0x801e096c),0x801e3628) # A/B don't advance
        self.assertEqual(word(0x801e097c)>>26,5) # pending state returns without advancing
        self.assertEqual(word(0x801e098c),0x2c42000e) # only sub0..D arm

if __name__=='__main__': unittest.main()
