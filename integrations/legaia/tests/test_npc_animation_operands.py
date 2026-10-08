"""Literal whole-MAN proof for independently allocated animation arguments."""
from copy import deepcopy
from hashlib import sha256
import os, unittest
from pathlib import Path
from importer.animation_operand_authoring import AnimationOperandAuthoringContext, load_animation_operand_authoring_context
from importer.core import ImportError
from importer.man_actor_structure import append_actor_donor
from importer.man_layout import read_man_layout
from sdk.npc_animation_operands import patch_allocated_animation_operands
from sdk.npc_script_compare import authored_spans
from sdk.project import ProjectError
from test_importer_dialogue_authoring import fixture, ACTOR
from test_effect_color_authoring import END


class NpcAnimationOperands(unittest.TestCase):
    def candidate(self, extended=False):
        model = (b'\xcc\x07' if extended else b'\x4c') + b'\x81\1\2\3\4\5\6\7'
        effect = (b'\xb4\x02' if extended else b'\x34') + b'\x3f\1'
        source, man = fixture(model + effect + END)
        context = AnimationOperandAuthoringContext(source)
        targets = context.options(ACTOR)['targets']
        candidate, allocations = man, {'drafts': []}
        for name in ('npc-a', 'npc-b'):
            candidate, row = append_actor_donor(candidate, sha256(candidate).hexdigest(), 1)
            allocations['drafts'].append(dict(row, draft_id=name))
        return context, candidate, allocations, targets

    def requests(self, targets):
        return [dict(draft_id=name, donor_entity_id=ACTOR, entries={
            targets[0]['semantic_id']: dict(model_id=model, animation_frame=frame, tween_frames=tween),
            targets[1]['semantic_id']: dict(animation_operand=effect)})
            for name, model, frame, tween, effect in [('npc-a', 0xffffff, 65535, 0, 255), ('npc-b', 0, 0, 65535, 0)]]

    def test_independent_clones_multiple_instructions_and_rebased_literal_man(self):
        for extended in (False, True):
            context, base, allocations, targets = self.candidate(extended)
            requests = self.requests(targets)
            result, proof = patch_allocated_animation_operands(context, base, allocations, requests)
            expected = bytearray(base)
            layout = read_man_layout(base)
            source_at, _, _ = context._source.verified_record(ACTOR)
            for row, request in zip(allocations['drafts'], requests):
                final = next(r for r in layout['records'] if r['partition'] == 1 and r['record_index'] == row['record_index'])
                at = final['byte_offset'] + targets[0]['decoded_byte_offset'] - source_at
                values = request['entries'][targets[0]['semantic_id']]
                encoded = values['model_id'].to_bytes(3, 'little') + values['animation_frame'].to_bytes(2, 'little') + values['tween_frames'].to_bytes(2, 'little')
                expected[at:at + 7] = encoded
                at = final['byte_offset'] + targets[1]['decoded_byte_offset'] - source_at
                expected[at] = request['entries'][targets[1]['semantic_id']]['animation_operand']
            self.assertEqual(result, bytes(expected))
            self.assertEqual(read_man_layout(result), layout)
            self.assertEqual(len(proof['changes']), 8)
            self.assertEqual(proof['result_man_sha256'], sha256(result).hexdigest())
            self.assertNotEqual(proof['changes'][0]['decoded_byte_offset'], allocations['drafts'][0]['byte_offset'] + targets[0]['decoded_byte_offset'] - source_at)
            with self.assertRaises(ProjectError):
                patch_allocated_animation_operands(context, result, allocations, requests)
            # Applying only one clone leaves the other clone and donor exact.
            one, _ = patch_allocated_animation_operands(context, base, allocations, requests[:1])
            sibling = next(r for r in layout['records'] if r['partition'] == 1 and r['record_index'] == allocations['drafts'][1]['record_index'])
            at, size = sibling['byte_offset'], sibling['byte_length']
            self.assertEqual(one[at:at + size], base[at:at + size])

    def test_noop_proves_whole_instruction_and_holds_unrelated_bytes(self):
        context, base, allocations, targets = self.candidate(True)
        noop = dict(draft_id='npc-a', donor_entity_id=ACTOR, entries={r['semantic_id']: r['values'] for r in targets})
        result, proof = patch_allocated_animation_operands(context, base, allocations, [noop])
        self.assertEqual(result, base)
        self.assertEqual(proof['changes'], [])
        final = next(r for r in read_man_layout(base)['records'] if r['partition'] == 1 and r['record_index'] == allocations['drafts'][0]['record_index'])
        for target in targets:
            for relative in range(target['pc'], target['pc'] + target['instruction_length']):
                bad = bytearray(base)
                bad[final['byte_offset'] + relative] ^= 1
                with self.assertRaises((ProjectError, ImportError)):
                    patch_allocated_animation_operands(context, bytes(bad), allocations, [noop])
        # A sibling instruction outside the request remains untouched, rather
        # than being overwritten by a complete donor-record copy.
        bad = bytearray(base)
        effect = final['byte_offset'] + targets[1]['pc'] + targets[1]['instruction_length'] - 1
        bad[effect] = 33
        request = self.requests(targets)[0]
        request['entries'].pop(targets[1]['semantic_id'])
        result, _ = patch_allocated_animation_operands(context, bytes(bad), allocations, [request])
        self.assertEqual(result[effect], 33)

    def test_comparison_requalifies_each_field_and_refuses_forged_receipts(self):
        context, base, allocations, targets = self.candidate(True)
        request = self.requests(targets)[0]
        result, proof = patch_allocated_animation_operands(context, base, allocations, [request])
        offset, raw, entry = context._source.verified_record(ACTOR)
        final = next(r for r in read_man_layout(result)['records'] if r['partition'] == 1 and r['record_index'] == allocations['drafts'][0]['record_index'])
        start, size = final['byte_offset'], final['byte_length']
        record = lambda data, at, index: dict(raw_hex=data.hex(), script_offset=entry, byte_length=len(data), byte_offset=at, record_index=index)
        retail, generated = record(raw, offset, 1), record(result[start:start + size], start, final['record_index'])
        draft = dict(donor_entity_id=ACTOR, animation_operands=dict(donor_entity_id=ACTOR, entries=request['entries']))
        metadata = {'npc_animation_operands_changes': proof}
        spans = authored_spans(metadata, 'npc-a', retail, generated, draft)
        self.assertEqual([r['byte_length'] for r in spans], [3, 2, 2, 1])
        self.assertTrue(all(r['category'] == 'own_animation_operand' for r in spans))
        for change in [dict(byte_length=1), dict(target_context=8), dict(after_hex='000000'),
                       dict(pc=0), dict(field='animation_operand'), dict(before_value=True),
                       dict(animation_operand_id=targets[0]['semantic_id'].replace('0001', '0000'))]:
            bad = deepcopy(metadata)
            bad['npc_animation_operands_changes']['changes'][0].update(change)
            with self.assertRaises(ProjectError): authored_spans(bad, 'npc-a', retail, generated, draft)
        bad = deepcopy(generated)
        data = bytearray.fromhex(bad['raw_hex']); data[targets[0]['pc'] + 1] ^= 1
        bad['raw_hex'] = data.hex()
        with self.assertRaises(ProjectError): authored_spans(metadata, 'npc-a', retail, bad, draft)

    def test_owner_allocation_and_native_width_refusals(self):
        context, base, allocations, targets = self.candidate()
        request = self.requests(targets)[0]
        for change in [dict(draft_id='missing'), dict(donor_entity_id=ACTOR.replace('0001', '0000')),
                       dict(entries={targets[0]['semantic_id']: dict(model_id=True, animation_frame=0, tween_frames=0)}),
                       dict(entries={targets[0]['semantic_id']: dict(model_id=16777216, animation_frame=0, tween_frames=0)}),
                       dict(entries={targets[1]['semantic_id']: dict(animation_operand=256)}), dict(extra=True)]:
            with self.assertRaises((ProjectError, ImportError)):
                patch_allocated_animation_operands(context, base, allocations, [dict(request, **change)])
        for change in [dict(record_index=1), dict(byte_length=1), dict(donor={'record_index': 0})]:
            bad = deepcopy(allocations)
            bad['drafts'][0].update(change)
            with self.assertRaises(ProjectError):
                patch_allocated_animation_operands(context, base, bad, [request])
        with self.assertRaises(ProjectError):
            patch_allocated_animation_operands(context, base, allocations, [request, request])


@unittest.skipUnless(os.environ.get('LEGAIA_DISC_BIN'), 'Private Retail disc required')
class RetailNpcAnimationOperands(unittest.TestCase):
    def test_map02_clone_effect_arguments_literal_complete_man(self):
        context = load_animation_operand_authoring_context(Path(os.environ['LEGAIA_DISC_BIN']), 'map02')
        owner = 'scene://map02/actors/man-p1/0003'
        target = next(r for r in context.options(owner)['targets'] if r['mnemonic'] == 'EFFECT_ANIMATION_TRIGGER')
        source_at, _, _ = context._source.verified_record(owner)
        base, allocations = context._man, {'drafts': []}
        for name in ('npc-a', 'npc-b'):
            base, row = append_actor_donor(base, sha256(base).hexdigest(), 3)
            allocations['drafts'].append(dict(row, draft_id=name))
        requests = [dict(draft_id=name, donor_entity_id=owner, entries={target['semantic_id']: dict(animation_operand=value)})
                    for name, value in [('npc-a', 1), ('npc-b', 255)]]
        result, proof = patch_allocated_animation_operands(context, base, allocations, requests)
        expected = bytearray(base)
        for row, value in zip(allocations['drafts'], (1, 255)):
            final = next(r for r in read_man_layout(base)['records'] if r['partition'] == 1 and r['record_index'] == row['record_index'])
            expected[final['byte_offset'] + target['decoded_byte_offset'] - source_at] = value
        self.assertEqual(result, bytes(expected))
        self.assertEqual(len(proof['changes']), 2)
        self.assertEqual(read_man_layout(result), read_man_layout(base))
        self.assertEqual(context.patch({})[0], context._man)


if __name__ == '__main__': unittest.main()
