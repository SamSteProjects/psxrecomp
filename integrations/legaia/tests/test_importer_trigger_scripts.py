"""P2 boundaries, fresh trigger resolution and opt-in retail source evidence."""
from contextlib import nullcontext
from copy import deepcopy
import os
from pathlib import Path
import struct
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from importer.core import ImportError
from importer.trigger_scripts import _inspect, _p2_entry, _p2_record, inspect_trigger_script


def fixture():
    code = b'\x1fHello\0\x21\x26\xfe\xff'
    first = bytes([1, 65, 0, 2, 9, 8, 1, 1, 0, 1, 2, 0]) + code
    second = b'\0\0\0\0\x4c\x80\x1fUnvisited\0'
    region = 0x2B + 4 * 3
    body = bytes(8) + first + second
    man = bytearray(region)
    struct.pack_into('<hhh', man, 0x22, 1, 1, 2)
    man[0x28:0x2B] = len(body).to_bytes(3, 'little')
    for i, offset in enumerate((0, 4, 8, 8 + len(first))):
        man[0x2B + 3*i:0x2E + 3*i] = offset.to_bytes(3, 'little')
    return bytes(man) + body + bytes(18), region, first


class TriggerScriptTests(unittest.TestCase):
    def test_p2_header_and_existing_inspector_preserve_boundaries(self):
        man, region, first = fixture()
        record, report = _inspect(man, 'fixture', 0)
        self.assertEqual(record['byte_offset'], region + 8)
        self.assertEqual(record['byte_length'], len(first))
        self.assertEqual(record['script_offset'], 12)
        self.assertEqual(record['header'], {'prefix_word_count': 1, 'c0_count': 2, 'c1_count': 1, 'c2_count': 1})
        self.assertEqual([d['text'] for d in report['dialogues']], ['Hello'])
        self.assertEqual(report['dialogues'][0]['semantic_id'], 'script://fixture/scripts/man-p2/0000/dialogue/000c')
        self.assertEqual(report['status'], 'decoded_supported_paths')
        _, unknown = _inspect(man, 'fixture', 1)
        self.assertEqual(unknown['status'], 'partial')
        self.assertEqual(unknown['dialogues'], [])
        self.assertEqual(unknown['stops'][0]['pc'], 4)
        self.assertEqual(unknown['opaque_regions'][0]['pc'], 4)

    def test_headers_aliases_all_partition_bounds_and_sections_reject(self):
        man, region, _ = fixture()
        for data in (b'', b'\1', b'\0', b'\0\1', b'\0\0\1', b'\0\0\0\1'):
            with self.subTest(data=data), self.assertRaises(ImportError):
                _p2_entry(data)
        for index in (-1, True, 2):
            with self.assertRaises(ImportError):
                _p2_record(man, index)
        # A P0 alias must reject the P2 target, even though P2 itself is unique.
        bad = bytearray(man)
        bad[0x2B:0x2E] = (8).to_bytes(3, 'little')
        with self.assertRaisesRegex(ImportError, 'aliased'):
            _p2_record(bytes(bad), 0)
        # A different partition begins inside the variable P2 header.
        bad = bytearray(man)
        bad[0x2B:0x2E] = (10).to_bytes(3, 'little')
        with self.assertRaisesRegex(ImportError, 'bounded record'):
            _inspect(bytes(bad), 'fixture', 0)
        # A valid record pointer into section payload must not expose it as code.
        bad = bytearray(man)
        sections = int.from_bytes(man[0x28:0x2B], 'little')
        bad[0x31:0x34] = (sections + 1).to_bytes(3, 'little')
        with self.assertRaisesRegex(ImportError, 'overlaps a section'):
            _p2_record(bytes(bad), 0)
        for offset, value in ((0x22, b'\xff\xff'), (0x28, b'\xff'*3), (0x2B, b'\xff'*3)):
            bad = bytearray(man)
            bad[offset:offset + len(value)] = value
            with self.assertRaises(ImportError):
                _p2_record(bytes(bad), 0)

    def test_fresh_trigger_lookup_rejects_gate_and_provenance_injection(self):
        man, _, _ = fixture()
        trigger_id = 'trigger://fixture/field-map/fallback/kind-1/0000'
        trigger = {'semantic_id': trigger_id, 'asset_kind': 'trigger', 'table_kind': 1,
                   'encoded': {'gate': 1, 'record_index': 0}, 'source_record': {'sha256': '1' * 64}}
        descriptor = SimpleNamespace(type_byte=3, size=len(man), data_offset=4)
        bundle = SimpleNamespace(entry_index=3, table_offset=0, descriptors=[descriptor])
        with patch('importer.trigger_scripts._disc_context', side_effect=lambda _: nullcontext((None, '0'*64, {}, None))), \
             patch('importer.trigger_scripts.load_field_map_catalog', side_effect=lambda *_: {'assets': [deepcopy(trigger)]}) as catalog, \
             patch('importer.trigger_scripts._bounded_scene_range', return_value=(1, 10)), \
             patch('importer.trigger_scripts.find_scene_bundle', return_value=(bundle, bytes(100))), \
             patch('importer.trigger_scripts.decompress_lzs', return_value=(man, 50)):
            result = inspect_trigger_script('disc', 'fixture', trigger_id)
            self.assertEqual(result['partition'], 2)
            self.assertEqual(result['script_id'], 'script://fixture/scripts/man-p2/0000')
            self.assertEqual(result['trigger_source_record']['sha256'], '1' * 64)
            trigger['source_record']['sha256'] = '2' * 64
            self.assertEqual(inspect_trigger_script('disc', 'fixture', trigger_id)['trigger_source_record']['sha256'], '2' * 64)
            self.assertEqual(catalog.call_count, 2)
            for gate in (0, 7):
                trigger['encoded']['gate'] = gate
                with self.assertRaisesRegex(ImportError, 'gate-1'):
                    inspect_trigger_script('disc', 'fixture', trigger_id)
            trigger['encoded']['gate'] = 1
            with self.assertRaisesRegex(ImportError, 'absent'):
                inspect_trigger_script('disc', 'fixture', trigger_id + '0')
            bundle.descriptors.append(SimpleNamespace(type_byte=4, size=10, data_offset=4))
            with self.assertRaisesRegex(ImportError, 'aliased'):
                inspect_trigger_script('disc', 'fixture', trigger_id)
        for bad in (None, {}, 'scene://fixture', 'trigger://' + 'x' * 512):
            with self.assertRaises(ImportError):
                inspect_trigger_script('disc', 'fixture', bad)


@unittest.skipUnless(os.environ.get('LEGAIA_DISC_BIN'), 'requires private retail disc')
class RetailTriggerScriptTests(unittest.TestCase):
    def test_town01_first_gate1_record_has_exact_source_and_bounded_decode(self):
        from importer.pipeline import _disc_context
        disc = os.environ['LEGAIA_DISC_BIN']
        with _disc_context(disc):
            report = inspect_trigger_script(disc, 'town01', 'trigger://town01/field-map/fallback/kind-1/0000')
            self.assertEqual(report['record_index'], 38)
            self.assertEqual(report['source_record']['byte_offset'], 44621)
            self.assertEqual(report['record']['byte_length'], 24)
            self.assertEqual(report['record']['script_offset'], 20)
            self.assertEqual(report['inspection']['status'], 'decoded_supported_paths')
            self.assertEqual([i['mnemonic'] for i in report['inspection']['instructions']], ['NOP', 'JMP_REL'])
            self.assertEqual(report['inspection']['dialogues'], [])
            with self.assertRaisesRegex(ImportError, 'gate-1'):
                inspect_trigger_script(disc, 'town01', 'trigger://town01/field-map/primary/kind-1/0000')


if __name__ == '__main__':
    unittest.main()
