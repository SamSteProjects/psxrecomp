"""Observed initial clip assignment with source guards and ordinary Undo history."""
from contextlib import nullcontext
from copy import deepcopy
import os
from pathlib import Path
import struct
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from importer.core import parse_man
from importer.man_assignments import ManAssignmentContext
from importer.scene_animation import SceneActorAnimationCatalog
from sdk.actor_animation import apply, options, review, source_actor, validate
from sdk.asset_references import source_key
from sdk.project import ProjectError, ProjectService
from integrations.legaia.tests.test_project_workflow import synthetic_scene


def fixture():
    counts, offsets = (1, 5, 0), (0, 8, 20, 32, 44, 56)
    start, sections = 0x2b + sum(counts) * 3, 68
    man = bytearray(start + sections + 18)
    struct.pack_into('<hhh', man, 0x22, *counts)
    man[0x28:0x2b] = sections.to_bytes(3, 'little')
    for index, offset in enumerate(offsets):
        man[0x2b + index * 3:0x2e + index * 3] = offset.to_bytes(3, 'little')
    for offset, model, animation in zip(offsets[2:], (4, 4, 5, 4), (1, 2, 3, 2)):
        man[start + offset:start + offset + 6] = bytes((0, model, animation, 5, 6, 0))
    man = bytes(man)
    records = [struct.pack('<4H', 2, frames, 0x080c, 2) + bytes(frames * 2 * 8 + 8)
               for frames in (2, 3, 4)]
    body = struct.pack('<4I', 3, 16, 16 + len(records[0]), 16 + len(records[0]) + len(records[1])) + b''.join(records)
    document = synthetic_scene()
    template = deepcopy(document['actors'][0])
    models = [dict(semantic_id=f'asset://fixture/models/scene-tmd/{index:04d}', asset_kind='tmd_model',
                   source_record=dict(fixture=True, record_index=index, object_count=2))
              for index in (4, 5)]
    document['assets']['models'] = models
    document['actors'] = []
    for actor in parse_man(man, 'fixture').actors:
        row = deepcopy(template)
        row['semantic_id'] = f'scene://fixture/actors/man-p1/{actor.record_index:04d}'
        row['source_record'] = dict(record_index=actor.record_index, byte_offset=actor.byte_offset,
                                    byte_length=actor.byte_length, fixture=True)
        row['placement_fields'] = dict(animation_id=actor.animation_id, local_count=actor.local_count)
        row['model_reference'] = dict(model_index=actor.model_index,
             asset_semantic_id=f'asset://fixture/models/scene-tmd/{actor.model_index:04d}', resolution_status='resolved')
        document['actors'].append(row)
    context = ManAssignmentContext('fixture', man, man, {4: 2, 5: 2}, body, {'fixture': True}, compression='none')
    catalog = SceneActorAnimationCatalog('fixture.bin', 'fixture', document, body, {'fixture': True})
    return document, context, catalog


class ActorAnimationTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.project = ProjectService(Path(directory.name))
        self.document, self.context, self.catalog = fixture()
        self.project.import_metadata(self.document)
        self.project.disc_path = 'fixture.bin'
        self.target, self.witness, self.other, self.duplicate = [a['semantic_id'] for a in self.document['actors']]
        for target, replacement in (
            ('importer.pipeline._disc_context', lambda _: nullcontext()),
            ('importer.pipeline.import_scene', lambda *_: deepcopy(self.document)),
            ('importer.scene_animation.load_scene_actor_animation_catalog', lambda *_: self.catalog),
            ('importer.man_assignments.load_man_assignment_context', lambda *_: self.context),
        ):
            mocked = patch(target, replacement)
            mocked.start()
            self.addCleanup(mocked.stop)

    def command(self, report):
        return {key: report[key] for key in ('entity_id', 'animation_asset_id', 'source_key', 'review_key')} | {'type': 'set_actor_animation'}

    def snapshot(self):
        return deepcopy((self.project._document(), self.project.undo_stack, self.project.redo_stack,
                         self.project.selected, self.project.assets.__dict__))

    def test_choices_are_exact_observed_model_bindings_canonical_and_detached(self):
        before = self.snapshot()
        result = options(self.project, self.target)
        self.assertTrue(result['supported'])
        self.assertEqual(result['source_key'], source_key(self.project))
        self.assertEqual([row['value']['animation_asset_id'] for row in result['choices']],
                         ['animation://fixture/scene-anm/0000', 'animation://fixture/scene-anm/0001'])
        self.assertEqual([row['value']['donor_entity_id'] for row in result['choices']], [self.target, self.witness])
        self.assertEqual(result['base'], result['effective'])
        self.assertIsNone(result['base']['timing']['fps'])
        self.assertEqual(result['choices'][1]['binding']['association']['active_object_indices'], [0, 1])
        result['choices'][1]['binding']['association']['active_object_indices'].clear()
        result['choices'][1]['value']['source_record_sha256'] = '0' * 64
        self.assertEqual(options(self.project, self.target)['choices'][1]['binding']['association']['active_object_indices'], [0, 1])
        self.assertEqual(self.snapshot(), before)

    def test_apply_inherit_undo_redo_preserves_other_components_and_noop_redo(self):
        project = self.project
        project.overrides[self.target] = {'Transform': {'position': {'x': 704}},
            'AnimationChannels': {'animation_id': 'animation://fixture/scene-anm/0000', 'source_record_sha256': 'c' * 64,
                                  'edits': [{'frame_index': 0, 'object_index': 0, 'translation': {'x': 12}}]}}
        baseline = deepcopy(project.overrides)
        snapshot = self.snapshot()
        report = review(project, self.target, 'animation://fixture/scene-anm/0001')
        self.assertEqual(self.snapshot(), snapshot)
        apply(project, self.command(report))
        self.assertEqual(len(project.undo_stack), 1)
        self.assertEqual({key: project.overrides[self.target][key] for key in baseline[self.target]}, baseline[self.target])
        self.assertEqual(source_actor(project, self.target, verify_disc=True)['semantic_id'], self.witness)
        project.undo()
        self.assertEqual(project.overrides, baseline)
        history = deepcopy((project.undo_stack, project.redo_stack))
        # Explicitly selecting the inherited clip is a no-op and preserves Redo.
        apply(project, self.command(review(project, self.target, 'animation://fixture/scene-anm/0000')))
        self.assertEqual((project.undo_stack, project.redo_stack), history)
        project.redo()
        apply(project, self.command(review(project, self.target, None)))
        self.assertEqual(project.overrides, baseline)
        self.assertEqual(len(project.undo_stack), 2)
        self.assertEqual(project.imports[project.active_scene], self.document)

    def test_malformed_foreign_model_and_bad_source_digest_reject_without_mutation(self):
        choice = options(self.project, self.target)['choices'][1]['value']
        for value in (None, {}, {**choice, 'extra': True}, {**choice, 'source_record_sha256': 'A' * 64},
                      {**choice, 'donor_entity_id': self.other}, {**choice, 'donor_entity_id': 'scene://foreign/actor'},
                      {**choice, 'animation_asset_id': 'animation://fixture/scene-anm/0000'}):
            before = self.snapshot()
            with self.subTest(value=value), self.assertRaises(ProjectError):
                validate(self.project, self.target, value)
            self.assertEqual(self.snapshot(), before)
        altered = {**choice, 'source_record_sha256': '0' * 64}
        with self.assertRaisesRegex(ProjectError, 'digest'):
            validate(self.project, self.target, altered, verify_disc=True)

    def test_stale_source_and_changed_review_are_atomic(self):
        report = review(self.project, self.target, 'animation://fixture/scene-anm/0001')
        self.project.overrides[self.target] = {'Transform': {'position': {'x': 704}}}
        before = self.snapshot()
        with self.assertRaisesRegex(ProjectError, 'source changed'):
            apply(self.project, self.command(report))
        self.assertEqual(self.snapshot(), before)
        fresh = review(self.project, self.target, 'animation://fixture/scene-anm/0001')
        command = self.command(fresh)
        command['animation_asset_id'] = None
        with self.assertRaisesRegex(ProjectError, 'since review'):
            apply(self.project, command)
        self.assertEqual(self.snapshot(), before)
        with patch('importer.pipeline.import_scene', return_value={**self.document, 'unexpected': True}):
            with self.assertRaisesRegex(ProjectError, 'freshly verified'):
                options(self.project, self.target)
        self.assertEqual(self.snapshot(), before)

    def test_appearance_base_requires_exact_model_and_prefers_its_clip_witness(self):
        project = self.project
        project.overrides[self.target] = {'ActorAppearance': {'donor_entity_id': self.duplicate}}
        inherited = options(project, self.target)
        self.assertEqual(inherited['base']['actor_semantic_id'], self.duplicate)
        self.assertEqual(inherited['choices'][1]['value']['donor_entity_id'], self.duplicate)
        report = review(project, self.target, 'animation://fixture/scene-anm/0000')
        apply(project, self.command(report))
        self.assertEqual(source_actor(project, self.target)['semantic_id'], self.target)
        retained = deepcopy(project.overrides[self.target]['ActorAnimation'])
        project.overrides[self.target]['ActorAppearance'] = {'donor_entity_id': self.other}
        with self.assertRaisesRegex(ProjectError, 'exact inherited'):
            validate(project, self.target, retained)
        project.overrides[self.target].pop('ActorAnimation')
        other_model = options(project, self.target)
        self.assertEqual([row['binding']['semantic_id'] for row in other_model['choices']], ['animation://fixture/scene-anm/0002'])
        self.assertIsNone(review(project, self.target, 'animation://fixture/scene-anm/0002')['after'])

    def test_saved_witness_survives_same_model_base_change_and_clear_uses_base(self):
        project = self.project
        apply(project, self.command(review(project, self.target, 'animation://fixture/scene-anm/0001')))
        retained = deepcopy(project.overrides[self.target]['ActorAnimation'])
        project.overrides[self.target]['ActorAppearance'] = {'donor_entity_id': self.duplicate}
        self.assertEqual(validate(project, self.target, retained, verify_disc=True)['semantic_id'], self.witness)
        inherited = review(project, self.target, None)
        self.assertIsNone(inherited['after'])
        self.assertEqual(inherited['proposed']['actor_semantic_id'], self.duplicate)
        apply(project, self.command(inherited))
        self.assertNotIn('ActorAnimation', project.overrides[self.target])
        self.assertEqual(source_actor(project, self.target, verify_disc=True)['semantic_id'], self.duplicate)

    def test_assignment_invalidates_cached_candidate_correlation(self):
        from integrations.legaia.observer.correlation import _digest
        project = self.project
        project._live_correlation = {'available': True, 'import_digest': _digest(self.document),
                                     'appearance_donors': {}, 'animation_donors': {}, 'entities': {}}
        apply(project, self.command(review(project, self.target, 'animation://fixture/scene-anm/0001')))
        report = project._current_correlation()
        self.assertFalse(report['available'])
        self.assertIn('initial animation changed', report['reason'])
        self.assertIsNone(project._live_correlation)
        self.assertEqual(project._animation_donors(), {self.target: self.witness})

    def test_unknown_pair_mappings_and_mode_fail_closed(self):
        with self.assertRaisesRegex(ProjectError, 'compatible'):
            review(self.project, self.target, 'animation://fixture/scene-anm/0002')
        self.project.mode = 'live'
        with self.assertRaisesRegex(ProjectError, 'Edit mode'):
            review(self.project, self.target, None)
        self.project.mode = 'edit'
        self.project.active_scene = None
        with self.assertRaisesRegex(ProjectError, 'active scene'):
            review(self.project, self.target, None)
        self.project.active_scene = 'scene://fixture'
        with patch.object(self.context, 'options', return_value={'supported': False, 'reason': 'aliased actor', 'pairs': []}):
            result = options(self.project, self.target)
            self.assertFalse(result['supported'])
            self.assertEqual(result['choices'], [])
        # A known count alone cannot relax an incompatible active-object mapping.
        original = self.catalog.referenced_animation_metadata()
        original['bindings'][1]['association']['active_object_indices'] = [1, 0]
        original['bindings'][3]['association']['active_object_indices'] = [1, 0]
        with patch.object(self.catalog, 'referenced_animation_metadata', return_value=original):
            result = options(self.project, self.target)
            self.assertEqual(len(result['choices']), 1)


@unittest.skipUnless(os.environ.get('LEGAIA_DISC_BIN'), 'requires private retail disc')
class RetailActorAnimationTests(unittest.TestCase):
    def test_town0b_observed_same_model_swap_is_one_byte_and_inherits_without_retargeting(self):
        from importer.pipeline import _disc_context, import_scene
        from importer.man_assignments import load_man_assignment_context
        disc = os.environ['LEGAIA_DISC_BIN']
        with tempfile.TemporaryDirectory() as directory, _disc_context(disc):
            document = import_scene(disc, 'town0b')
            project = ProjectService(Path(directory))
            project.import_metadata(document, disc)
            actor = 'scene://town0b/actors/man-p1/0019'
            result = options(project, actor)
            self.assertEqual([row['binding']['semantic_id'] for row in result['choices']],
                             ['animation://town0b/scene-anm/0012', 'animation://town0b/scene-anm/0013'])
            report = review(project, actor, 'animation://town0b/scene-anm/0012', result['source_key'])
            self.assertEqual(report['after']['donor_entity_id'], 'scene://town0b/actors/man-p1/0049')
            apply(project, {key: report[key] for key in ('entity_id', 'animation_asset_id', 'source_key', 'review_key')} |
                  {'type': 'set_actor_animation'})
            witness = source_actor(project, actor, verify_disc=True)
            context = load_man_assignment_context(disc, 'town0b')
            changed, audit = context.patch({19: {'animation_id': witness['placement_fields']['animation_id']}})
            self.assertEqual([(row['decoded_byte_offset'], row['before_byte'], row['after_byte']) for row in audit], [(9471, 14, 13)])
            self.assertEqual(sum(a != b for a, b in zip(changed, context._man)), 1)
            encoded, _, metadata = context.serialize({19: {'animation_id': 13}})
            self.assertEqual(len(encoded), 28024)
            self.assertLessEqual(metadata['new_encoded_size'], metadata['original_encoded_size'])
            self.assertEqual(project.imports['scene://town0b'], document)
            self.assertEqual(len(project.undo_stack), 1)
            project.undo()
            self.assertEqual(source_actor(project, actor)['semantic_id'], actor)


if __name__ == '__main__':
    unittest.main()
