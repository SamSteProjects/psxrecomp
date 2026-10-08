"""Two-byte selector authoring, preserved branch words and MAN ownership."""
import hashlib
import os
import unittest
from importer.core import ImportError
from importer.man_actor_structure import append_actor_donor
from importer.man_layout import read_man_layout
from importer.system_flag_authoring import (SystemFlagAuthoringContext,
    load_system_flag_authoring_context, patch_system_flag_selector)
from test_importer_dialogue_authoring import fixture, ACTOR

END = b'\x3f\0\0\x06town01\x01\x02\x03opaque'


class SystemFlagAuthoringTests(unittest.TestCase):
    def test_distinct_forward_and_backward_test_edges_are_preserved(self):
        for delta in (b'\xfe\xff', b'\x03\0'):
            record = b'\x71\x46' + delta + b'\x21\x21\x21' + END
            changed, _ = patch_system_flag_selector(record, 0, 0, {'index': 4095})
            self.assertEqual(changed, b'\x7f\xff' + record[2:])

    def test_every_selector_preserves_operation_and_branch_bytes(self):
        for opcode in (0x50, 0x60, 0x70):
            record = bytes((opcode, 2)) + (b'\x02\0' if opcode == 0x70 else b'') + END
            for index in range(4096):
                changed, audit = patch_system_flag_selector(record, 0, 0, {'index': index}, base_offset=100)
                self.assertEqual(changed, bytes((opcode + index // 256, index % 256)) + record[2:])
                self.assertEqual(len(changed), len(record))
                if index == 2:
                    self.assertEqual(audit, [])
                else:
                    self.assertEqual(audit[0]['decoded_byte_offset'], 100)
                    self.assertEqual(audit[0]['before_index'], 2)
                    self.assertEqual(audit[0]['after_index'], index)
                    self.assertEqual(audit[0]['byte_length'], 2)
                    self.assertEqual(audit[0]['after_hex'], changed[:2].hex())

    def test_invalid_values_unknown_paths_and_extended_addressing_refuse(self):
        for values in ({}, {'index': True}, {'index': -1}, {'index': 4096}, {'bit': 2}, {'index': 2, 'pc': 0}):
            with self.assertRaises(ImportError):
                patch_system_flag_selector(b'\x50\x02' + END, 0, 0, values)
        for record in (b'\xd0\x07\x02' + END, b'\x2e\x02' + END, b'\x50\x02\x2a'):
            with self.assertRaises(ImportError):
                patch_system_flag_selector(record, 0, 0, {'index': 2})
        for pc in (-1, True, 65536, 1):
            with self.assertRaises(ImportError):
                patch_system_flag_selector(b'\x50\x02' + END, 0, pc, {'index': 3})

    def test_man_ownership_noop_overlap_and_detached_audit(self):
        source, man = fixture(b'\x70\x02\x02\0' + END)
        context = SystemFlagAuthoringContext(source)
        target = context.options(ACTOR)['targets'][0]
        changed, audit = context.patch({target['semantic_id']: {'index': 4095}})
        at = target['decoded_byte_offset']
        self.assertEqual(changed, man[:at] + b'\x7f\xff' + man[at + 2:])
        self.assertEqual(read_man_layout(changed), read_man_layout(man))
        self.assertEqual(context.patch({target['semantic_id']: {'index': 2}}), (man, []))
        audit[0]['after_index'] = 1
        self.assertEqual(context.patch({target['semantic_id']: {'index': 4095}})[1][0]['after_index'], 4095)
        self.assertEqual(source._man, man)
        for bad in (target['semantic_id'].replace('/0001/', '/9999/'), target['semantic_id'].replace('system-flag', 'flag-bit')):
            with self.assertRaises(ImportError):
                context.patch({bad: {'index': 3}})
        aliased, _ = fixture(b'\x50\x02' + END, alias=True)
        with self.assertRaises(ImportError):
            SystemFlagAuthoringContext(aliased).options(ACTOR)

    def test_appended_source_rebases_preserves_clone_and_checks_noops(self):
        source, man = fixture(b'\x70\x02\x02\0' + END)
        context = SystemFlagAuthoringContext(source)
        target = context.options(ACTOR)['targets'][0]
        appended, _ = append_actor_donor(man, hashlib.sha256(man).hexdigest(), 1)
        changed, audit = context.patch_appended(appended, {target['semantic_id']: {'index': 4095}})
        at = audit[0]['decoded_byte_offset']
        self.assertEqual(changed, appended[:at] + b'\x7f\xff' + appended[at + 2:])
        self.assertEqual(read_man_layout(changed), read_man_layout(appended))
        self.assertEqual(context.patch_appended(appended, {target['semantic_id']: {'index': 2}}), (appended, []))
        for relative in (0, 1, 2):
            bad = bytearray(appended); bad[at + relative] ^= 1
            with self.assertRaises(ImportError):
                context.patch_appended(bytes(bad), {target['semantic_id']: {'index': 2}})


@unittest.skipUnless(os.environ.get('LEGAIA_DISC_BIN'), 'Private Retail disc required')
class RetailSystemFlagAuthoringTests(unittest.TestCase):
    def test_actual_town01_selector_exact_full_man_readback(self):
        context = load_system_flag_authoring_context(os.environ['LEGAIA_DISC_BIN'], 'town01')
        owner = 'scene://town01/actors/man-p1/0011'
        target = next(t for t in context.options(owner)['targets'] if t['pc'] == 22)
        self.assertEqual(target['values'], {'index': 326})
        original = context._man
        changed, audit = context.patch({target['semantic_id']: {'index': 4095}})
        at = target['decoded_byte_offset']
        self.assertEqual(original[at:at + 2], b'\x71\x46')
        self.assertEqual(changed, original[:at] + b'\x7f\xff' + original[at + 2:])
        self.assertEqual(read_man_layout(changed), read_man_layout(original))
        self.assertEqual(audit[0]['after_index'], 4095)
        self.assertEqual(context._man, original)
        self.assertEqual(len(audit), 1)


if __name__ == '__main__':
    unittest.main()
