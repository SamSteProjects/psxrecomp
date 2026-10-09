import unittest
from importer.core import ImportError
from importer.script_inspection import _instruction,inspect_record

class ActorGlobalByteRequests(unittest.TestCase):
 def test_four_native_destinations_and_signed_words_in_both_headers(self):
  destinations={3:'0x8007B618',4:'0x8007B614',5:'0x8007B60C',6:'0x8007B610'}
  for sub,destination in destinations.items():
   for header in [b'\x43',b'\xc3\xf8']:
    data=header+bytes([sub,0,127,128,255])+b'\x00\x80\xff\x7f'
    n=_instruction(data,0);self.assertEqual(n['mnemonic'],'GLOBAL_FOUR_BYTE_REQUEST');self.assertEqual(n['length'],len(data))
    self.assertEqual(n['operands']['byte_values'],[0,127,128,255]);self.assertEqual(n['operands']['parameters_i16'],[-32768,32767]);self.assertEqual(n['operands']['native_destination'],destination)
    self.assertEqual(n['operands']['runtime_effect'],'not_evaluated');self.assertEqual(n['successors'],[dict(pc=len(data),condition='encoded_continuation')]);self.assertEqual(data.hex(),n['raw_hex'])
    for length in range(len(header)+1,len(data)):
     with self.assertRaises(ImportError):_instruction(data[:length],0)
 def test_continuation_reaches_loop_without_executing_or_changing_source(self):
  data=b'\x43\x03\x01\x02\x03\x04\xff\xff\x00\x00\x26\xf5\xff';before=bytes(data)
  r=inspect_record(data,0);self.assertEqual(r['status'],'decoded_supported_paths');self.assertEqual([n['pc'] for n in r['instructions']],[0,10]);self.assertEqual(r['instructions'][0]['operands']['parameters_i16'],[-1,0]);self.assertEqual(data,before)
  with self.assertRaises(ImportError):_instruction(b'\x43\x11'+bytes(12),0)
