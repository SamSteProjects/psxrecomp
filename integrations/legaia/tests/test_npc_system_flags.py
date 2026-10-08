"""Independent complete-clone oracles and no-op source/ownership refusals."""
from copy import deepcopy
from hashlib import sha256
import os
import unittest
from unittest import TestCase
from importer.core import ImportError as NativeError
from importer.man_actor_structure import append_actor_donor
from importer.man_layout import read_man_layout
from importer.system_flag_authoring import SystemFlagAuthoringContext
from sdk.npc_system_flags import patch_allocated_system_flags
from sdk.project import ProjectError
from test_importer_dialogue_authoring import fixture, ACTOR
from test_system_flag_authoring import END


class NpcSystemFlagsTests(TestCase):
    def fixture(self, instruction):
        source, candidate = fixture(instruction + END)
        context = SystemFlagAuthoringContext(source)
        allocations = {'drafts': []}
        for identifier in ('npc-a', 'npc-b'):
            candidate, row = append_actor_donor(candidate, sha256(candidate).hexdigest(), 1)
            allocations['drafts'].append(dict(row, draft_id=identifier))
        return context, candidate, allocations

    def request(self, context, identifier='npc-a', value=4095):
        target = context.options(ACTOR)['targets'][0]
        return dict(draft_id=identifier, donor_entity_id=ACTOR,
                    entries={target['semantic_id']: {'index': value}})

    def test_two_clones_have_independent_indices_and_complete_literal_man_equality(self):
        for opcode in (0x51, 0x61, 0x71):
            context, candidate, allocations = self.fixture(bytes((opcode, 0x46)) + (b'\x02\0' if opcode == 0x71 else b''))
            target = context.options(ACTOR)['targets'][0]
            rows = {r['record_index']: r for r in read_man_layout(candidate)['records'] if r['partition'] == 1}
            for value in (0, 255, 256, 4095):
                requests = [self.request(context, 'npc-a', value), self.request(context, 'npc-b', 326)]
                result, audit = patch_allocated_system_flags(context, candidate, allocations, requests)
                expected = bytearray(candidate)
                at = rows[allocations['drafts'][0]['record_index']]['byte_offset'] + target['pc']
                expected[at:at + 2] = bytes(((opcode & 0xf0) | (value >> 8), value & 255))
                self.assertEqual(result, bytes(expected))
                self.assertEqual(len(audit['changes']), 1)
                self.assertEqual(audit['changes'][0]['draft_id'], 'npc-a')
                self.assertEqual(audit['changes'][0]['decoded_byte_offset'], at)
                self.assertEqual(read_man_layout(result), read_man_layout(candidate))
                self.assertEqual(audit['result_man_sha256'], sha256(result).hexdigest())

    def test_noop_still_binds_full_selector_operation_and_test_edges(self):
        context, candidate, allocations = self.fixture(b'\x71\x46\x02\0')
        request = self.request(context, value=326)
        result, audit = patch_allocated_system_flags(context, candidate, allocations, [request])
        self.assertEqual(result, candidate); self.assertEqual(audit['changes'], [])
        target = context.options(ACTOR)['targets'][0]
        row = next(r for r in read_man_layout(candidate)['records'] if r['partition'] == 1 and r['record_index'] == allocations['drafts'][0]['record_index'])
        at = row['byte_offset'] + target['pc']
        for relative, mask in ((0, 1), (0, 0x10), (1, 1), (2, 1), (3, 1)):
            forged = bytearray(candidate); forged[at + relative] ^= mask
            with self.assertRaises((ProjectError, NativeError)):
                patch_allocated_system_flags(context, bytes(forged), allocations, [request])

    def test_foreign_duplicate_retail_and_forged_allocations_refuse(self):
        context, candidate, allocations = self.fixture(b'\x51\x46')
        request = self.request(context)
        for bad in (dict(request, draft_id='missing'), dict(request, donor_entity_id=ACTOR.replace('0001', '0002')),
                    dict(request, entries={next(iter(request['entries'])).replace('0001', '0002'): {'index': 0}})):
            with self.assertRaises((ProjectError, NativeError)):
                patch_allocated_system_flags(context, candidate, allocations, [bad])
        with self.assertRaises(ProjectError):
            patch_allocated_system_flags(context, candidate, allocations, [request, request])
        for field, value in (('record_index', 1), ('byte_length', 1)):
            bad = deepcopy(allocations); bad['drafts'][0][field] = value
            with self.assertRaises(ProjectError):
                patch_allocated_system_flags(context, candidate, bad, [request])

    def test_typed_bounds_and_stopped_or_extended_dispatch_refuse(self):
        context, candidate, allocations = self.fixture(b'\x51\x46')
        for value in (True, -1, 4096, '3', 3.0):
            with self.assertRaises(NativeError):
                patch_allocated_system_flags(context, candidate, allocations, [self.request(context, value=value)])
        for instruction in (b'\xd1\x07\x46', b'\x51\x46\x7f'):
            context, candidate, allocations = self.fixture(instruction)
            entry = context._source.verified_record(ACTOR)[2]
            request = dict(draft_id='npc-a', donor_entity_id=ACTOR,
                entries={f'script://{ACTOR.removeprefix("scene://")}/system-flag/{entry:04x}': {'index': 0}})
            with self.assertRaises((ProjectError, NativeError)):
                patch_allocated_system_flags(context, candidate, allocations, [request])


@unittest.skipUnless(os.environ.get('LEGAIA_DISC_BIN'), 'Private Retail disc required')
class RetailNpcSystemFlagsTests(TestCase):
    def test_town01_allocated_selector_matches_complete_literal_man(self):
        from importer.system_flag_authoring import load_system_flag_authoring_context
        disc = os.environ['LEGAIA_DISC_BIN']
        context = load_system_flag_authoring_context(disc, 'town01')
        owner = 'scene://town01/actors/man-p1/0011'
        target = next(t for t in context.options(owner)['targets'] if t['pc'] == 22)
        original, _ = context.patch({})
        candidate, allocation = append_actor_donor(original, sha256(original).hexdigest(), 11)
        allocation = dict(allocation, draft_id='npc-system-retail')
        requests = [dict(draft_id=allocation['draft_id'], donor_entity_id=owner,
                         entries={target['semantic_id']: {'index': 4095}})]
        result, audit = patch_allocated_system_flags(context, candidate, {'drafts': [allocation]}, requests)
        row = next(r for r in read_man_layout(candidate)['records'] if r['partition'] == 1 and r['record_index'] == allocation['record_index'])
        at = row['byte_offset'] + target['pc']
        expected = bytearray(candidate); expected[at:at + 2] = b'\x7f\xff'
        self.assertEqual(result, bytes(expected))
        self.assertEqual(candidate[at:at + 2], b'\x71\x46')
        self.assertEqual(context._man, original)
        self.assertEqual(audit['changes'][0]['before_index'], 326)
        self.assertEqual(audit['changes'][0]['after_index'], 4095)
