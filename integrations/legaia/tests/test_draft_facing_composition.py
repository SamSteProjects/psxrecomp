"""Facing operands compose with placements and donor appends; no game is run."""
from copy import deepcopy
from hashlib import sha256
import os
from pathlib import Path
import tempfile
import unittest

from importer.core import IsoNode, ProtArchive, parse_man
from importer.facing_authoring import FacingAuthoringContext, load_facing_authoring_context
from importer.man_actor_structure import append_actor_donor
from importer.man_layout import read_man_layout
from importer.man_source import read_man_source
from importer.pipeline import _bounded_scene_range, _disc_context, import_scene
from importer.serialization import patch_man_positions
from sdk.draft_build import prepare_draft_archive
from sdk.project import ProjectService
from test_importer_dialogue_authoring import ACTOR, fixture


def span(payload, partition, index):
    return next(row for row in read_man_layout(payload)['records']
                if (row['partition'], row['record_index']) == (partition, index))


def record(payload, partition, index):
    row = span(payload, partition, index)
    return payload[row['byte_offset']:row['byte_offset'] + row['byte_length']]


class DraftFacingCompositionTests(unittest.TestCase):
    def test_same_actor_position_and_facing_preserve_retail_donor_clone(self):
        source, original = fixture(b'\x38\xa1\0\x3f\0\0\x06town01\1\2\3opaque')
        context = FacingAuthoringContext(source)
        target = context.options(ACTOR)['targets'][0]
        actor = next(row for row in parse_man(original).actors if row.record_index == 1)
        candidate, _ = append_actor_donor(original, sha256(original).hexdigest(), 1)
        clone_before = record(candidate, 1, 2)
        self.assertEqual(clone_before, record(original, 1, 1))
        positioned, placement = patch_man_positions(candidate, 'fixture', {
            1: {'x': actor.world_x + 64, 'z': actor.world_z}})
        edits = {target['semantic_id']: {'sector': 3}}
        context.patch(edits, original=original)
        result, audit = context.patch_appended(positioned, edits)
        owner = span(result, 1, 1)
        at = owner['byte_offset'] + target['pc'] + 1
        self.assertEqual(result[at], 0xa3)
        self.assertEqual(audit[0]['decoded_byte_offset'], at)
        self.assertEqual(audit[0]['source_decoded_byte_offset'], target['decoded_byte_offset'])
        self.assertEqual({i for i, (a, b) in enumerate(zip(positioned, result)) if a != b}, {at})
        self.assertTrue(placement)
        self.assertEqual(next(a for a in parse_man(result).actors if a.record_index == 1).world_x,
                         actor.world_x + 64)
        self.assertEqual(record(result, 1, 2), clone_before)
        self.assertEqual(context._man, original)


@unittest.skipUnless(os.environ.get('LEGAIA_DISC_BIN'), 'requires private retail disc')
class RetailDraftFacingCompositionTests(unittest.TestCase):
    def test_descriptor_and_streaming_archive_readback_preserves_clone_and_source(self):
        disc = os.environ['LEGAIA_DISC_BIN']
        private = Path(__file__).resolve().parents[3] / 'local-output/sdk-20260909'
        private.mkdir(parents=True, exist_ok=True)
        for scene in ('town01', 'dolk2'):
            with self.subTest(scene=scene), _disc_context(disc) as (_, _, mapping, source_archive), \
                    tempfile.TemporaryDirectory(prefix='facing-compose-', dir=private) as directory:
                document = import_scene(disc, scene)
                context = load_facing_authoring_context(disc, scene)
                from importer.script_inspection import inspect_record
                def unchanged_clone_donor(actor):
                    original = record(context._man, 1, actor['source_record']['record_index'])
                    entry = 1 + original[0] * 2 + 4
                    return not any(row['mnemonic'] == 'SPAWN_RECORD'
                                   for row in inspect_record(original, entry)['instructions'])
                target = next(target for actor in document['actors'] if unchanged_clone_donor(actor)
                              for target in context.options(actor['semantic_id'])['targets'])
                donor = next(actor for actor in document['actors'] if actor['semantic_id'] == target['owner_id'])
                index = donor['source_record']['record_index']
                source_actor = next(actor for actor in parse_man(context._man).actors
                                    if actor.record_index == index)
                project = ProjectService(Path(directory))
                project.import_metadata(document, disc)
                project.command(dict(type='create_actor_draft', donor_entity_id=target['owner_id'],
                                     position={'x': source_actor.world_x, 'z': source_actor.world_z},
                                     name='Facing composition probe'))
                project.command(dict(type='set_transform', entity_id=target['owner_id'],
                                     position={'x': source_actor.world_x + 64, 'z': source_actor.world_z}))
                sector = (target['values']['sector'] + 1) % 8
                project.command(dict(type='set_facing_target', entity_id=target['owner_id'],
                                     facing_id=target['semantic_id'], values={'sector': sector}))
                before = deepcopy((project._document(), project.imports, project.undo_stack,
                                   project.redo_stack, project.selected))
                files = {str(p.relative_to(project.root)): p.read_bytes()
                         for p in project.root.rglob('*') if p.is_file()}
                draft = next(iter(project.actor_drafts))
                archive_bytes, audit = prepare_draft_archive(project, draft)
                scene_audit = audit['scenes'][f'scene://{scene}'] if 'scenes' in audit else audit
                pool = scene_audit['actor_pool_evidence']
                self.assertEqual(pool['source']['node_capacity'], 143)
                self.assertEqual(len(pool['source']['setup_allocation_sites']), 6)
                self.assertEqual(pool['initial_placement_minimum_nodes'],
                                 read_man_layout(context._man)['partition_counts'][1] + 1)
                self.assertFalse(pool['runtime_allocation_verified'])

                class MemoryImage:
                    def read_user(self, lba, offset, length, file_size):
                        return archive_bytes[lba * 2048 + offset:lba * 2048 + offset + length]

                archive = ProtArchive(MemoryImage(), IsoNode(0, len(archive_bytes), False, 'PROT.DAT'))
                start, end = _bounded_scene_range(source_archive, mapping, scene)
                carrier = read_man_source(archive, start, end, scene)
                candidate = carrier.payload
                owner = span(candidate, 1, index)
                original_record = record(context._man, 1, index)
                original_entry = 1 + original_record[0] * 2 + 4
                node = next(row for row in inspect_record(original_record, original_entry)['instructions']
                            if row['pc'] == target['pc'])
                relative = target['pc'] + (2 if node['target_context'] is not None else 1)
                relative += 3 if node['mnemonic'] == 'NPC_RUN' else 0
                at = owner['byte_offset'] + relative
                self.assertEqual(candidate[at], (original_record[relative] & 0xf0) | sector)
                self.assertEqual(scene_audit['facing_changes'][0]['decoded_byte_offset'], at)
                self.assertEqual(scene_audit['facing_changes'][0]['source_decoded_byte_offset'],
                                 target['decoded_byte_offset'])
                cloned_index = read_man_layout(context._man)['partition_counts'][1]
                self.assertEqual(record(candidate, 1, cloned_index), original_record)
                candidate_actor = next(actor for actor in parse_man(candidate).actors if actor.record_index == index)
                self.assertEqual((candidate_actor.world_x, candidate_actor.world_z),
                                 (source_actor.world_x + 64, source_actor.world_z))
                self.assertEqual(context._man, read_man_source(source_archive, start, end, scene).payload)
                self.assertEqual((project._document(), project.imports, project.undo_stack,
                                  project.redo_stack, project.selected), before)
                self.assertEqual({str(p.relative_to(project.root)): p.read_bytes()
                                  for p in project.root.rglob('*') if p.is_file()}, files)
                self.assertFalse(audit['gameplay_verified'])


if __name__ == '__main__':
    unittest.main()
