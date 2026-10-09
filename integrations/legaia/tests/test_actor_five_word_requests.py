import struct
import unittest
from importer.core import ImportError
from importer.script_inspection import _instruction, inspect_record


class ActorFiveWordRequests(unittest.TestCase):
    def test_signed_operands_both_headers_and_all_truncations(self):
        values = [-32768, 32767, -1, 0, 1]
        for header in (b'\x43', b'\xc3\xff'):
            data = header+b'\x11'+struct.pack('<5h', *values)
            node = _instruction(data, 0)
            self.assertEqual(node['mnemonic'], 'FIVE_WORD_HELPER_REQUEST')
            self.assertEqual(node['length'], len(data))
            self.assertEqual(node['operands']['signed_words'], values)
            self.assertEqual(node['operands']['helper'], '0x801F8D4C')
            self.assertEqual(node['operands']['runtime_binding'], 'helper_owned_state_unresolved')
            self.assertEqual(node['operands']['runtime_effect'], 'not_evaluated')
            self.assertEqual(node['raw_hex'], data.hex())
            self.assertEqual(node['successors'], [{'pc': len(data), 'condition': 'encoded_continuation'}])
            for size in range(len(header)+1, len(data)):
                with self.assertRaises(ImportError): _instruction(data[:size], 0)

    def test_source_loop_preserved_without_helper_execution_or_fallback(self):
        data = b'\x43\x11'+struct.pack('<5h', 0, 16, 320, 204, 0)+b'\x26\xf3\xff'
        original = bytes(data); report = inspect_record(data, 0)
        self.assertEqual(report['status'], 'decoded_supported_paths')
        self.assertEqual([n['pc'] for n in report['instructions']], [0, 12])
        self.assertEqual(data, original)
        with self.assertRaises(ImportError): _instruction(b'\x43\x12'+bytes(20), 0)
