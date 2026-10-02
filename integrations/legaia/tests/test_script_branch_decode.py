"""Executing-retail branch arithmetic and corrected nonbranch continuations.

Synthetic records test offsets, loops and atomic ownership without proprietary
fixtures. Opt-in retail checks read the user's unchanged disc, verify independent
handler/consumer instruction fields and hashes, and never write source bytes.
"""
import hashlib
import os
import struct
import unittest

from importer.pipeline import _disc_context
from importer.script_inspection import inspect_record


class ScriptBranchDecodeTests(unittest.TestCase):
    def decode(self, body, extended=False, opcode=0x26, entry=3):
        header = bytes((opcode | 128, 7)) if extended else bytes((opcode,))
        record = bytes(entry) + header + body
        report = inspect_record(record, entry)
        self.assertFalse(report['stops'], report['stops'])
        row = report['instructions'][0]
        self.assertEqual(row['pc'], entry)
        self.assertEqual(row['target_context'], 7 if extended else None)
        self.assertEqual(row['raw_hex'], record[entry:entry + row['length']].hex())
        return row, report

    def test_jump_word_base_and_backward_self_loop_both_headers(self):
        for extended in (False, True):
            header = 2 if extended else 1
            row, report = self.decode(struct.pack('<h', -header), extended)
            self.assertEqual(row['mnemonic'], 'JMP_REL')
            self.assertEqual(row['successors'], [{'pc': 3, 'condition': 'unconditional'}])
            self.assertEqual(len(report['instructions']), 1)
            self.assertEqual(row['length'], header + 2)

    def test_system_test_entire_ordinary_high_nibble_has_both_encoded_paths(self):
        for opcode in range(0x70, 0x80):
            row, report = self.decode(b'\x46\x03\0\x21\x21\x26\xff\xff', opcode=opcode)
            self.assertEqual(row['mnemonic'], 'SYSFLAG_TEST')
            self.assertEqual(row['operands']['index'], ((opcode & 15) << 8) | 0x46)
            self.assertEqual(row['successors'], [{'pc': 8, 'condition': 'flag_set'},
                                               {'pc': 7, 'condition': 'flag_clear'}])
            self.assertEqual([node['pc'] for node in report['instructions']], [3, 7, 8, 9])

    def test_extended_system_operands_stop_without_false_edges_or_text_scan(self):
        for opcode in (0x50, 0x5f, 0x60, 0x6f, 0x70, 0x77, 0x7f):
            report = inspect_record(bytes((opcode | 128, 7, 0x46, 3, 0)) + b'\x1fOpaque\0', 0)
            self.assertEqual(report['instructions'], [])
            self.assertEqual(report['dialogues'], [])
            self.assertEqual(report['opaque_regions'][0]['pc'], 0)
            self.assertIn('extended SYSFLAG raw operand addressing', report['stops'][0]['reason'])

    def test_conditional_relative_word_base_preserves_modes_and_conditions(self):
        for extended in (False, True):
            for mode in (0, 1):
                row, _ = self.decode(bytes((mode, 0xe3)) + b'\x03\0\x21\x21\x26\xff\xff',
                                     extended, opcode=0x42)
                operand = 3 + (2 if extended else 1)
                self.assertEqual(row['operands']['mode'], mode)
                self.assertEqual(row['operands']['test'], 0xe3)
                self.assertEqual(row['successors'],
                                 [{'pc': operand + 5, 'condition': 'test_passed'},
                                  {'pc': operand + 4, 'condition': 'test_failed'}])
        report = inspect_record(b'\x42\x02\0\x02\0', 0)
        self.assertEqual(report['instructions'], [])
        self.assertIn('unsupported conditional jump mode', report['stops'][0]['reason'])

    def test_bbox_outside_branch_uses_skip_word_base_both_headers(self):
        for extended in (False, True):
            row, _ = self.decode(bytes((1, 2, 3, 4)) + b'\x03\0\x21\x21\x26\xff\xff',
                                 extended, opcode=0x4d)
            operand = 3 + (2 if extended else 1)
            self.assertEqual(row['operands']['tile_bounds'], [1, 2, 3, 4])
            self.assertEqual(row['successors'], [{'pc': operand + 6, 'condition': 'inside_box'},
                                               {'pc': operand + 7, 'condition': 'outside_box'}])

    def test_all_flag_word_banks_are_relative_not_absolute_both_headers(self):
        for extended in (False, True):
            for sub, bank in ((0xa0, 'actor_flags'), (0xa1, 'actor_local_flags'),
                              (0xa2, 'global_story_word')):
                row, _ = self.decode(bytes((sub, 0xf3)) + b'\x03\0\x21\x21\x26\xff\xff',
                                     extended, opcode=0x4c)
                operand = 3 + (2 if extended else 1)
                self.assertEqual(row['mnemonic'], 'FLAG_WORD_BRANCH')
                self.assertEqual(row['operands']['delta'], 3)
                self.assertEqual(row['operands']['target'], operand + 5)
                self.assertEqual(row['operands']['flag_word'], bank)
                self.assertEqual(row['operands']['bit_encoded'], 0xf3)
                self.assertEqual(row['successors'], [{'pc': operand + 5, 'condition': 'flag_bit_set'},
                                                   {'pc': operand + 4, 'condition': 'flag_bit_clear'}])

    def test_flag_word_signed_delta_can_return_to_its_own_source_instruction(self):
        for extended in (False, True):
            header = 2 if extended else 1
            row, _ = self.decode(b'\xa0\x03' + struct.pack('<h', -header - 2) + b'\x26\xff\xff',
                                 extended, opcode=0x4c)
            self.assertEqual(row['operands']['target'], 3)
            self.assertEqual(row['successors'][0], {'pc': 3, 'condition': 'flag_bit_set'})
        report = inspect_record(b'\x4c\xa0\x01\xfc\xff\x26\xff\xff', 0)
        self.assertEqual(report['instructions'][0]['operands']['target'], 65535)
        self.assertTrue(any(stop['pc'] == 65535 for stop in report['stops']))

    def test_camera_apply_parameter_does_not_select_a_script_target(self):
        for extended in (False, True):
            row, report = self.decode(b'\xc7\xff\xff\x1fOne\0\x1fTwo\0', extended, opcode=0x45)
            self.assertEqual(row['mnemonic'], 'CAMERA_APPLY')
            self.assertEqual(row['operands']['apply_trigger'], -1)
            self.assertEqual(row['operands']['mode'], 1)
            self.assertNotIn('target', row['operands'])
            self.assertEqual(row['successors'],
                             [{'pc': 3 + row['length'], 'condition': 'encoded_continuation'}])
            self.assertEqual([message['text'] for message in report['dialogues']], ['One', 'Two'])

    def test_field_43_44_write_or_ramp_and_never_jump_for_any_tick_gate(self):
        for extended in (False, True):
            for sub in (0x43, 0x44):
                for ticks in (0, 1, 32767, 32768, 65535):
                    row, report = self.decode(bytes((sub,)) + struct.pack('<hH', -1, ticks) + b'\x1fNext\0',
                                             extended, opcode=0x4c)
                    self.assertEqual(row['mnemonic'], 'FIELD_RAMP')
                    self.assertEqual(row['operands']['value'], -1)
                    self.assertEqual(row['operands']['ticks'], ticks)
                    self.assertEqual(row['successors'],
                                     [{'pc': 3 + row['length'], 'condition': 'encoded_continuation'}])
                    self.assertEqual([message['text'] for message in report['dialogues']], ['Next'])

    def test_flag_tests_have_bit_operands_and_no_authored_destination_word(self):
        for opcode in (0x2d, 0x30, 0x33):
            row, _ = self.decode(b'\x03\x26\xff\xff', opcode=opcode)
            self.assertEqual(row['length'], 2)
            self.assertTrue(row['operands']['can_wait_for_flag'])
            self.assertNotIn('target', row['operands'])
            self.assertNotIn('delta', row['operands'])


@unittest.skipUnless(os.environ.get('LEGAIA_DISC_BIN'), 'requires unchanged private SCUS disc')
class RetailScriptBranchProofTests(unittest.TestCase):
    def test_executing_handlers_and_signed_pc_consumers_are_hash_bound(self):
        with _disc_context(os.environ['LEGAIA_DISC_BIN']) as (image, _, _, archive):
            source = archive.read_entry(archive.entry(897), extended=True)
            self.assertEqual(hashlib.sha256(source).hexdigest(),
                             '216f846db5ab085a295cef4064747380a06c995caa3e1b2773e78a1d349f126b')
            base = 0x801ce818
            word = lambda address: struct.unpack_from('<I', source, address - base)[0]
            fields = lambda value: (value >> 26, (value >> 21) & 31, (value >> 16) & 31, value & 65535)
            # Independent executing fields: extended operand+PC adjustments;
            # JMP+1, COND+5, BBOX+7; shared signed-word delta-2+PC.
            for address, expected in (
                (0x801de948, (9, 22, 22, 1)), (0x801de94c, (9, 30, 30, 1)),
                (0x801dece8, (9, 30, 30, 1)), (0x801decec, (36, 22, 2, 1)),
                (0x801decf0, (36, 22, 3, 0)),
                (0x801e35d4, (36, 16, 2, 1)), (0x801e35f0, (36, 16, 3, 3)),
                (0x801e35f4, (36, 16, 4, 2)), (0x801e35ec, (9, 30, 2, 2)),
                (0x801dfbc8, (9, 30, 30, 5)), (0x801dfbd8, (9, 30, 2, 65534)),
                (0x801dfb38, (9, 30, 30, 7)), (0x801dfb78, (36, 22, 3, 5)),
                (0x801dfb7c, (36, 22, 2, 4)),
                (0x801e256c, (9, 30, 30, 5)), (0x801e2588, (9, 22, 4, 2)),
                (0x801e25dc, (9, 22, 4, 2)), (0x801e3614, (9, 2, 2, 65534)),
                (0x801e1138, (9, 30, 30, 6)), (0x801e1248, (41, 21, 2, 36)),
                (0x801e1280, (41, 21, 2, 40)),
                (0x801df25c, (9, 22, 4, 1)), (0x801df288, (9, 30, 30, 4))):
                self.assertEqual(fields(word(address)), expected, hex(address))
            self.assertEqual(word(0x801e361c) & 63, 33)  # ADDU PC,PC,signed delta-2
            self.assertEqual((word(0x801e361c) >> 11) & 31, 30)
            self.assertEqual(word(0x801e1234) >> 26, 5)  # nonzero ticks take ramp, not jump
            self.assertEqual(word(0x801e126c) >> 26, 5)
            self.assertEqual(word(0x801df27c), 0x0c077821)  # JAL camera801DE084; return unused
            executable = image.read_file(image.find('SCUS_942.54'))
            self.assertEqual(hashlib.sha256(executable).hexdigest(),
                             '292256e2e66db42727f613406785e444254d3f699569e611f65fcf1c6d2f3482')
            load = struct.unpack_from('<I', executable, 0x18)[0]
            exe_word = lambda address: struct.unpack_from('<I', executable, address - load + 0x800)[0]
            # All five dispatch consumers narrow/sign-extend before adding PC
            # to source bytecode base. High-bit destinations are not positive PCs.
            for call, store, sll, sra in (
                (0x80039e14, 0x80039e24, 0x80039e28, 0x80039e2c),
                (0x8003a4b8, 0x8003a4c8, 0x8003a4cc, 0x8003a4d0),
                (0x8003a920, 0x8003a930, 0x8003a934, 0x8003a938),
                (0x8003ad4c, 0x8003ad5c, 0x8003ad60, 0x8003ad64),
                (0x8003cfd4, 0x8003cfe4, 0x8003cfe8, 0x8003cfec)):
                self.assertEqual(exe_word(call), 0x0c077a10)  # JAL801DE840
                self.assertEqual(exe_word(store) >> 26, 41)
                self.assertEqual(exe_word(store) & 65535, 0x9e)
                self.assertEqual((exe_word(sll) & 63, (exe_word(sll) >> 6) & 31), (0, 16))
                self.assertEqual((exe_word(sra) & 63, (exe_word(sra) >> 6) & 31), (3, 16))
            self.assertEqual((exe_word(0x8003ceb4) & 63, (exe_word(0x8003ceb4) >> 6) & 31), (3, 16))


if __name__ == '__main__':
    unittest.main()
