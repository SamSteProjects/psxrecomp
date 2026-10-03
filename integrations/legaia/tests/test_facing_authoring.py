"""Bounded scalar operand checks and optional fresh retail mechanism evidence."""
from copy import deepcopy
from hashlib import sha256
import os
import struct
import unittest

from importer.core import ImportError, parse_man
from importer.dialogue_authoring import DialogueAuthoringContext
from importer.facing_authoring import (FacingAuthoringContext, load_facing_authoring_context,
                                        patch_facing_sector, validate_facing_values)
from importer.pipeline import _disc_context
from importer.script_inspection import inspect_record
from test_importer_dialogue_authoring import ACTOR, fixture

END = b'\x3f\0\0\x06town01\x01\x02\x03opaque'


def appended_fixture(script, p2_script=None):
    from test_importer_dialogue_authoring import literals
    records = [b'opaque', b'\0\0\0\0\0\x2a', b'\0\1\2\3\4' + script,
               bytes(4) + (p2_script if p2_script is not None else b'\x2a')]
    header = bytearray(0x2b)
    struct.pack_into('<hhh', header, 0x22, 1, 2, 1)
    header[0x28:0x2b] = sum(map(len, records)).to_bytes(3, 'little')
    offsets, cursor = [], 0
    for record in records:
        offsets.append(cursor.to_bytes(3, 'little'))
        cursor += len(record)
    man = bytes(header) + b''.join(offsets) + b''.join(records) + bytes(18) + b'tail'
    return DialogueAuthoringContext('fixture', man, literals(man), {}), man


class FacingAuthoringTests(unittest.TestCase):
    def test_both_opcode_families_preserve_flags_context_and_exact_instruction_shape(self):
        for extended in (False, True):
            for family in ('CAM_CFG', 'NPC_RUN'):
                opcode = 0x38 if family == 'CAM_CFG' else 0x4C
                header = bytes((opcode | 0x80, 0xF8)) if extended else bytes((opcode,))
                args = b'\xa3\x80' if family == 'CAM_CFG' else b'\x51\x00\x80\xb3\x09'
                record = header + args + END
                offset = len(header) + (0 if family == 'CAM_CFG' else 3)
                original = inspect_record(record, 0)
                for sector in range(8):
                    changed, audit = patch_facing_sector(record, 0, 0, {'sector': sector}, base_offset=100)
                    expected = bytearray(record)
                    expected[offset] = (record[offset] & 0xF0) | sector
                    self.assertEqual(changed, bytes(expected))
                    self.assertEqual(changed[offset] & 0xF0, record[offset] & 0xF0)
                    self.assertEqual(len(audit), int(sector != 3))
                    decoded = inspect_record(changed, 0)
                    self.assertEqual([(n['pc'], n['length'], n['mnemonic'], n['target_context'], n['successors'])
                                      for n in decoded['instructions']],
                                     [(n['pc'], n['length'], n['mnemonic'], n['target_context'], n['successors'])
                                      for n in original['instructions']])
                    if audit:
                        row = audit[0]
                        self.assertEqual(row['field'], 'sector')
                        self.assertEqual(row['decoded_byte_offset'], 100 + offset)
                        self.assertEqual(row['record_relative_byte_offset'], offset)
                        self.assertEqual(row['target_context'], 0xF8 if extended else None)
                        self.assertEqual((row['before_sector'], row['after_sector']), (3, sector))
                        self.assertEqual(row['source_record_sha256'], sha256(record).hexdigest())

    def test_context_composes_detached_options_and_audits_without_mutating_baseline(self):
        source, original = fixture(b'\x38\x81\0\x4c\x51\x01\x80\xa2\x09' + END)
        context = FacingAuthoringContext(source)
        options = context.options(ACTOR)
        self.assertTrue(options['supported'])
        self.assertIsNone(options['reason'])
        self.assertEqual([row['values']['sector'] for row in options['targets']], [1, 2])
        self.assertEqual([row['before_raw'] for row in options['targets']], [0x81, 0xA2])
        self.assertTrue(all(row['preservation_mask'] == 240 for row in options['targets']))
        targets = deepcopy(options['targets'])
        options['targets'][0]['values']['sector'] = 7
        options['source']['limitations'].clear()
        self.assertEqual(context.options(ACTOR)['targets'], targets)
        self.assertTrue(context.provenance()['limitations'])
        edits = {row['semantic_id']: {'sector': 3} for row in targets}
        changed, audit = context.patch(edits, original=original)
        self.assertEqual(len(changed), len(original))
        self.assertEqual({i for i, (a, b) in enumerate(zip(original, changed)) if a != b},
                         {row['decoded_byte_offset'] for row in audit})
        self.assertEqual(parse_man(changed), parse_man(original))
        self.assertEqual([row['after_byte'] for row in audit], [0x83, 0xA3])
        self.assertEqual(context._man, original)
        for row in audit:
            self.assertEqual(row['source_decoded_man_sha256'], sha256(original).hexdigest())
            self.assertEqual(row['owner_id'], ACTOR)
            self.assertIn(row['facing_id'], edits)
        audit[0]['after_byte'] = 0
        self.assertEqual(context.patch(edits)[1][0]['after_byte'], 0x83)
        self.assertEqual(context.patch({}), (original, []))
        with self.assertRaisesRegex(ImportError, 'verified source'):
            context.patch(edits, original=changed)
        for invalid in ({**edits, 'foreign': {'sector': 4}},
                        {targets[0]['semantic_id'].replace('fixture', 'another'): {'sector': 4}},
                        {targets[0]['semantic_id'].replace('/0001/', '/9999/'): {'sector': 4}}):
            with self.assertRaises(ImportError):
                context.patch(invalid)
        self.assertEqual(context.patch({}), (original, []))

    def test_appended_original_p1_p2_owners_rebase_and_donor_copies_remain_retail(self):
        from importer.man_actor_structure import append_actor_candidates
        from importer.man_layout import read_man_layout
        from test_importer_dialogue_authoring import literals
        source, man = appended_fixture(b'\x38\xa3\0\xcc\xf8\x51\0\x80\xb3\x09' + END,
                                       b'\xb8\xf8\xa3\0' + END)
        context = FacingAuthoringContext(source)
        appended, _ = append_actor_candidates(man, sha256(man).hexdigest(),
            [dict(id='draft/a', donor_record_index=1, position=None),
             dict(id='draft/b', donor_record_index=1, position=None)])
        targets = context.options(ACTOR)['targets'] + context.options('scene://fixture/scripts/man-p2/0000')['targets']
        edits = {target['semantic_id']: {'sector': 6} for target in targets}
        result, audit = context.patch_appended(appended, edits)
        self.assertEqual(len(audit), 3)
        self.assertEqual(read_man_layout(appended), read_man_layout(result))
        self.assertEqual({n for n, (a, b) in enumerate(zip(appended, result)) if a != b},
                         {row['decoded_byte_offset'] for row in audit})
        for row in audit:
            self.assertEqual(row['decoded_byte_offset'], row['source_decoded_byte_offset'] + 6)
            self.assertEqual(row['appended_man_sha256'], sha256(appended).hexdigest())
            self.assertEqual(row['appended_target_context'], row['target_context'])
            self.assertEqual(result[row['decoded_byte_offset']] & 0xF0, row['before_byte'] & 0xF0)
        layout = read_man_layout(appended)
        for clone in (row for row in layout['records'] if row['partition'] == 1 and row['record_index'] >= 2):
            start, end = clone['byte_offset'], clone['byte_offset'] + clone['byte_length']
            self.assertEqual(result[start:end], appended[start:end])
        self.assertEqual(context.patch_appended(appended, {}), (appended, []))
        noops = {target['semantic_id']: target['values'] for target in targets}
        self.assertEqual(context.patch_appended(appended, noops), (appended, []))
        self.assertEqual(context._man, man)
        placed = bytearray(appended)
        p1_placement = next(row for row in layout['records'] if row['partition'] == 1 and row['record_index'] == 1)
        placed[p1_placement['byte_offset'] + 3:p1_placement['byte_offset'] + 5] = b'\x88\x89'
        placed = bytes(placed)
        composed, placed_audit = context.patch_appended(placed, edits)
        self.assertEqual({n for n, (a, b) in enumerate(zip(placed, composed)) if a != b},
                         {row['decoded_byte_offset'] for row in placed_audit})
        self.assertEqual(composed[p1_placement['byte_offset'] + 3:p1_placement['byte_offset'] + 5], b'\x88\x89')
        for target in targets:
            at = target['decoded_byte_offset'] + 6
            for relative, value in ((0, appended[at] ^ 0x10),):
                invalid = bytearray(appended)
                invalid[at + relative] = value
                with self.assertRaisesRegex(ImportError, 'preimage'):
                    context.patch_appended(bytes(invalid), {target['semantic_id']: {'sector': 6}})
        # Entry prefix, dispatch context and opcode cannot be substituted.
        p1 = next(row for row in layout['records'] if row['partition'] == 1 and row['record_index'] == 1)
        for at in (p1['byte_offset'], p1['byte_offset'] + 5, p1['byte_offset'] + 9):
            invalid = bytearray(appended)
            invalid[at] ^= 1
            with self.assertRaises(ImportError):
                context.patch_appended(bytes(invalid), edits)
        with self.assertRaisesRegex(ImportError, 'preimage'):
            context.patch_appended(result, edits)
        for invalid in (bytearray(appended), b'', bytes(4 * 1024 * 1024 + 1)):
            with self.assertRaises(ImportError):
                context.patch_appended(invalid, edits)

    def test_appended_missing_aliased_or_changed_extent_record_rejects(self):
        from importer.man_actor_structure import append_actor_candidates
        source, man = appended_fixture(b'\x38\xa3\0' + END)
        context = FacingAuthoringContext(source)
        target = context.options(ACTOR)['targets'][0]
        appended, _ = append_actor_candidates(man, sha256(man).hexdigest(),
            [dict(id='draft/a', donor_record_index=1, position=None)])
        edits = {target['semantic_id']: {'sector': 6}}
        # Original P1 record table entry is at 0x31; alias, truncate and move it.
        for replacement in (appended[0x2B:0x2E],
                            (int.from_bytes(appended[0x31:0x34], 'little') + 1).to_bytes(3, 'little')):
            invalid = bytearray(appended)
            invalid[0x31:0x34] = replacement
            with self.assertRaises(ImportError):
                context.patch_appended(bytes(invalid), edits)
        invalid = bytearray(appended)
        struct.pack_into('<h', invalid, 0x24, 1)
        with self.assertRaises(ImportError):
            context.patch_appended(bytes(invalid), edits)

    def test_nonscalar_modes_parked_nondirection_unknown_conflicts_and_invalid_values_reject(self):
        for record in (b'\x38\x03\x01' + END, b'\x38\x08\0' + END,
                       b'\x4c\x51\x7f\xff\x03\x09' + END,
                       b'\x4c\x51\x00\x80\x08\x09' + END,
                       b'\x38\x03\0\x2a', b'\x38\x03',
                       b'\x38\x03\0\x26\xfb\xff'):
            with self.assertRaises(ImportError):
                patch_facing_sector(record, 0, 0, {'sector': 2})
        record = b'\x38\x03\0' + END
        for values in ({}, {'sector': True}, {'sector': -1}, {'sector': 8}, {'sector': 1.0},
                       {'sector': 2, 'heading': 1024}, {'sector': 2, 'offset': 1}, []):
            with self.assertRaises(ImportError):
                validate_facing_values(values)
        for pc in (True, -1, 1, 100):
            with self.assertRaises(ImportError):
                patch_facing_sector(record, 0, pc, {'sector': 2})
        for offset in (True, -1, 1.0):
            with self.assertRaises(ImportError):
                patch_facing_sector(record, 0, 0, {'sector': 2}, base_offset=offset)

    def test_unavailable_reasons_aliases_and_raw_source_keep_evidenced_ownership(self):
        source, original = fixture(b'\x38\x01\x01\x4c\x51\x7f\xff\x01\x09' + END)
        context = FacingAuthoringContext(source)
        options = context.options(ACTOR)
        self.assertFalse(options['supported'])
        self.assertEqual(options['targets'], [])
        self.assertEqual(len(options['unavailable']), 2)
        self.assertIn('halt-acquire', options['unavailable'][0]['reason'])
        self.assertIn('parked', options['unavailable'][1]['reason'])
        aliased, _ = fixture(b'\x38\x01\0' + END, alias=True)
        with self.assertRaisesRegex(ImportError, 'aliased'):
            FacingAuthoringContext(aliased).options(ACTOR)
        supported, original = fixture(b'\x38\x81\0' + END)
        raw = DialogueAuthoringContext('fixture', original, original, {'compression': 'none'}, compression='none')
        target = FacingAuthoringContext(supported).options(ACTOR)['targets'][0]['semantic_id']
        self.assertEqual(FacingAuthoringContext(raw).patch({target: {'sector': 3}}),
                         FacingAuthoringContext(supported).patch({target: {'sector': 3}}))
        self.assertTrue(hasattr(FacingAuthoringContext(raw), 'patch_appended'))


@unittest.skipUnless(os.environ.get('LEGAIA_DISC_BIN'), 'requires private retail disc')
class RetailFacingAuthoringTests(unittest.TestCase):
    def test_retail_dispatch_tables_operand_masks_and_context_writes_are_source_verified(self):
        with _disc_context(os.environ['LEGAIA_DISC_BIN']) as (image, _, _, archive):
            source = archive.read_entry(archive.entry(897), extended=True)
            self.assertEqual(sha256(source).hexdigest(),
                             '216f846db5ab085a295cef4064747380a06c995caa3e1b2773e78a1d349f126b')
            base = 0x801CE818
            word = lambda address: struct.unpack_from('<I', source, address - base)[0]
            for address, target in ((0x801CED1C, 0x801DEE58), (0x801CED6C, 0x801E0C3C),
                                    (0x801CEE74, 0x801E1780), (0x801CEF34, 0x801E1828)):
                self.assertEqual(word(address), target)
            fields = lambda value: (value >> 26, (value >> 21) & 31, (value >> 16) & 31, value & 0xFFFF)
            # Actual MIPS fields: lbu op1/op0; scalar gate; ANDI sector; LHU LUT; SH actor+0x26.
            for address, expected in ((0x801DEE58, (36, 22, 2, 1)),
                                      (0x801DEE60, (12, 2, 2, 127)),
                                      (0x801DEE6C, (36, 22, 3, 0)),
                                      (0x801DEE74, (12, 3, 3, 15)),
                                      (0x801DEE80, (37, 3, 2, 0)),
                                      (0x801DEE8C, (41, 21, 2, 38)),
                                      (0x801E1828, (36, 22, 2, 3)),
                                      (0x801E1830, (12, 2, 2, 128)),
                                      (0x801E18E4, (36, 22, 2, 3)),
                                      (0x801E18EC, (12, 2, 2, 15)),
                                      (0x801E18F8, (37, 2, 2, 0)),
                                      (0x801E1900, (41, 21, 2, 38))):
                self.assertEqual(fields(word(address)), expected)
            executable = image.read_file(image.find('SCUS_942.54'))
            load_address = struct.unpack_from('<I', executable, 0x18)[0]
            lut_offset = 0x80073F04 - load_address + 0x800
            self.assertEqual(struct.unpack_from('<8H', executable, lut_offset), tuple(i * 512 for i in range(8)))

    def test_town0b_unconditional_fixture_preserves_upper_bit_and_all_other_bytes(self):
        with _disc_context(os.environ['LEGAIA_DISC_BIN']):
            context = load_facing_authoring_context(os.environ['LEGAIA_DISC_BIN'], 'town0b')
            options = context.options('scene://town0b/actors/man-p1/0019')
            target = next(row for row in options['targets'] if row['pc'] == 17)
            self.assertEqual(target['mnemonic'], 'CAM_CFG')
            self.assertEqual(target['decoded_byte_offset'], 9479)
            self.assertEqual(target['before_raw'], 0x81)
            self.assertEqual(target['values'], {'sector': 1})
            self.assertEqual(target['source_record_sha256'],
                             '04659e35af297acefa6b11fc9d1222d7ea9e5f12790297184d296655603ac6d2')
            changed, audit = context.patch({target['semantic_id']: {'sector': 3}})
            self.assertEqual({i for i, (a, b) in enumerate(zip(context._man, changed)) if a != b}, {9479})
            self.assertEqual(changed[9479], 0x83)
            self.assertEqual(audit[0]['after_sector'], 3)
            self.assertEqual(parse_man(changed), parse_man(context._man))

    def test_town01_source_npc_facing_is_authorable_without_initial_runtime_claim(self):
        with _disc_context(os.environ['LEGAIA_DISC_BIN']):
            context = load_facing_authoring_context(os.environ['LEGAIA_DISC_BIN'], 'town01')
            options = context.options('scene://town01/actors/man-p1/0014')
            self.assertTrue(options['supported'])
            target = next(row for row in options['targets'] if row['pc'] == 33)
            self.assertEqual(target['mnemonic'], 'NPC_RUN')
            self.assertEqual(target['values'], {'sector': 2})
            changed, audit = context.patch({target['semantic_id']: {'sector': 6}})
            self.assertEqual({i for i, (a, b) in enumerate(zip(context._man, changed)) if a != b},
                             {target['decoded_byte_offset']})
            self.assertEqual(changed[target['decoded_byte_offset']] & 0xF0, target['before_raw'] & 0xF0)
            self.assertEqual(audit[0]['after_sector'], 6)
            self.assertEqual(parse_man(changed), parse_man(context._man))
            self.assertNotIn('initial_heading', target)
            self.assertNotIn('runtime_heading', target)
