"""Initial clip assignment across project persistence and existing MAN builders."""
from contextlib import ExitStack, nullcontext
from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
import zipfile

ROOT = Path(__file__).resolve().parents[3]
sys.path[:0] = [str(ROOT / 'integrations/legaia'), str(ROOT)]
from importer.core import decompress_lzs, parse_man
from importer.man_assignments import load_man_assignment_context
from importer.pipeline import _disc_context, import_scene
from sdk.actor_animation import review, source_actor
from sdk.build import build_project
from sdk.draft_build import _prepare_draft_scene
from sdk.project import ProjectError, ProjectService
from integrations.legaia.tests.test_actor_animation import fixture

PRIVATE = ROOT / 'local-output/sdk-20260909'


def private_directory():
    PRIVATE.mkdir(parents=True, exist_ok=True)
    return tempfile.TemporaryDirectory(prefix='actor-animation-integration-', dir=PRIVATE)


def assign(project, actor, clip):
    report = review(project, actor, clip)
    project.command({key: report[key] for key in ('entity_id', 'animation_asset_id', 'source_key', 'review_key')} |
                    {'type': 'set_actor_animation'})
    return report


class ActorAnimationCommandIntegration(unittest.TestCase):
    def test_incompatible_appearance_command_rolls_back_assignment_and_history(self):
        document, context, catalog = fixture()
        with private_directory() as directory, ExitStack() as stack:
            project = ProjectService(Path(directory))
            self.assertTrue(project.root.is_relative_to(PRIVATE.resolve()))
            project.import_metadata(document, 'fixture.bin')
            for target, replacement in (
                ('importer.pipeline._disc_context', lambda _: nullcontext()),
                ('importer.pipeline.import_scene', lambda *_: deepcopy(document)),
                ('importer.scene_animation.load_scene_actor_animation_catalog', lambda *_: catalog),
                ('importer.man_assignments.load_man_assignment_context', lambda *_: context),
            ):
                stack.enter_context(patch(target, replacement))
            target = document['actors'][0]['semantic_id']
            assign(project, target, 'animation://fixture/scene-anm/0001')
            qualified = deepcopy(project.overrides[target]['ActorAnimation'])
            # A compatible appearance change retains its already verified witness
            # even when another actor becomes the preferred inherited witness.
            project.command(dict(type='set_actor_appearance', entity_id=target,
                                 donor_entity_id=document['actors'][3]['semantic_id']))
            self.assertEqual(project.overrides[target]['ActorAnimation'], qualified)
            self.assertEqual(source_actor(project, target, verify_disc=True)['semantic_id'], document['actors'][1]['semantic_id'])
            before = deepcopy((project._document(), project.undo_stack, project.redo_stack))
            with self.assertRaisesRegex(ProjectError, 'exact inherited'):
                project.command(dict(type='set_actor_appearance', entity_id=target,
                                     donor_entity_id=document['actors'][2]['semantic_id']))
            self.assertEqual((project._document(), project.undo_stack, project.redo_stack), before)
            self.assertEqual(source_actor(project, target)['semantic_id'], document['actors'][1]['semantic_id'])


@unittest.skipUnless(os.environ.get('LEGAIA_DISC_BIN'), 'requires private retail disc')
class RetailActorAnimationIntegration(unittest.TestCase):
    def test_town0b_save_history_build_and_inherit_preserve_imported_channel_ownership(self):
        disc = os.environ['LEGAIA_DISC_BIN']
        with private_directory() as directory, _disc_context(disc):
            project = ProjectService(Path(directory))
            self.assertTrue(project.root.is_relative_to(PRIVATE.resolve()))
            document = import_scene(disc, 'town0b')
            original = deepcopy(document)
            project.import_metadata(document, disc)
            target = 'scene://town0b/actors/man-p1/0019'
            imported_clip = 'animation://town0b/scene-anm/0013'
            selected_clip = 'animation://town0b/scene-anm/0012'
            channel_options = project.animation_authoring_options(target)
            self.assertEqual(channel_options['binding']['semantic_id'], imported_clip)
            channel = project.animation_channel_values(target, 0, 0)
            authored_channels = dict(animation_id=imported_clip,
                source_record_sha256=channel_options['binding']['source_record']['record_sha256'],
                edits=[dict(frame_index=0, object_index=0,
                            translation={'x': channel['retail']['translation']['x'] ^ 1})])
            project.command(dict(type='set_animation_channels', entity_id=target, value=authored_channels))
            baseline_components = deepcopy(project.overrides)
            baseline = build_project(project)
            report = assign(project, target, selected_clip)
            self.assertEqual(report['after']['donor_entity_id'], 'scene://town0b/actors/man-p1/0049')
            self.assertEqual(project.overrides[target]['AnimationChannels'], authored_channels)
            after_options = project.animation_authoring_options(target)
            self.assertEqual(after_options['binding'], channel_options['binding'])
            self.assertEqual(after_options['shared_actor_ids'], channel_options['shared_actor_ids'])
            assignment_components = deepcopy(project.overrides)
            self.assertEqual(len(project.undo_stack), 2)
            project.undo()
            self.assertEqual(project.overrides, baseline_components)
            project.redo()
            self.assertEqual(project.overrides, assignment_components)
            path = project.save()
            saved_bytes = path.read_bytes()
            restored = ProjectService.open(path)
            self.assertEqual(restored.overrides, assignment_components)
            self.assertEqual(restored.imports['scene://town0b'], original)
            self.assertEqual(source_actor(restored, target, verify_disc=True)['semantic_id'], 'scene://town0b/actors/man-p1/0049')
            combined = build_project(restored)
            audit = json.loads(Path(combined['audit']).read_text(encoding='utf-8'))
            assignments = [row for row in audit['edits'] if row.get('scope') == 'initial-man-header-only']
            self.assertEqual(len(assignments), 1)
            change = assignments[0]
            self.assertEqual((change['field'], change['decoded_byte_offset'], change['before_byte'], change['after_byte']),
                             ('animation_id', 9471, 14, 13))
            self.assertEqual(change['assignment_kind'], 'ActorAnimation')
            self.assertEqual(change['animation_asset_id'], selected_clip)
            self.assertEqual(change['assignment_source_record_sha256'], report['after']['source_record_sha256'])
            self.assertTrue(all(row['animation_id'] == imported_clip for row in audit['edits']
                                if row.get('scope') == 'shared-scene-animation-record'))
            context = load_man_assignment_context(disc, 'town0b')
            start, end = context._ranges[12]
            self.assertEqual(change['assignment_source_record_sha256'], hashlib.sha256(context._anm[start:end]).hexdigest())
            expected, _ = context.patch({19: {'animation_id': 13}})
            with zipfile.ZipFile(combined['path']) as package:
                decoded = decompress_lzs(package.read('assets/town0b-man.lzs'), len(context._man))[0]
                self.assertEqual(decoded, expected)
                self.assertEqual([index for index, (a, b) in enumerate(zip(decoded, context._man)) if a != b], [9471])
            self.assertEqual(path.read_bytes(), saved_bytes)
            assign(restored, target, None)
            self.assertEqual(restored.overrides, baseline_components)
            cleared = build_project(restored)
            self.assertEqual(cleared['sha256'], baseline['sha256'])
            self.assertEqual(restored.overrides[target]['AnimationChannels'], authored_channels)
            self.assertEqual(project.imports['scene://town0b'], original)
            self.assertEqual(document, original)
            self.assertEqual(path.read_bytes(), saved_bytes)

    def test_town0b_deferred_draft_composes_existing_assignment_and_retail_clone_once(self):
        disc = os.environ['LEGAIA_DISC_BIN']
        with private_directory() as directory, _disc_context(disc):
            project = ProjectService(Path(directory))
            self.assertTrue(project.root.is_relative_to(PRIVATE.resolve()))
            document = import_scene(disc, 'town0b')
            project.import_metadata(document, disc)
            target = 'scene://town0b/actors/man-p1/0019'
            report = assign(project, target, 'animation://town0b/scene-anm/0012')
            donor = project._actor(target)
            position = {axis: donor['imported_transform']['position'][axis] for axis in ('x', 'z')}
            project.command(dict(type='create_actor_draft', donor_entity_id=target, position=position, name='Retail donor proof'))
            draft = next(iter(project.actor_drafts))
            before = deepcopy((project._document(), project.undo_stack, project.redo_stack))
            prot, audit = _prepare_draft_scene(project, draft, defer_rebuild=True)
            candidate = audit['_rebuild_request']['candidate']
            actors = {row.record_index: row for row in parse_man(candidate, 'town0b').actors}
            context = load_man_assignment_context(disc, 'town0b')
            original = parse_man(context._man, 'town0b')
            appended_record = original.partition_counts[1]
            self.assertEqual(parse_man(candidate, 'town0b').partition_counts[1], original.partition_counts[1] + 1)
            self.assertEqual((actors[19].model_index, actors[19].animation_id), (102, 13))
            self.assertEqual((actors[appended_record].model_index, actors[appended_record].animation_id), (102, 14))
            changes = audit['existing_actor_appearance_changes']
            self.assertEqual(len(changes), 1)
            self.assertEqual((changes[0]['source_decoded_byte_offset'], changes[0]['decoded_byte_offset']), (9471, 9474))
            self.assertEqual(changes[0]['assignment_source_record_sha256'], report['after']['source_record_sha256'])
            self.assertFalse(audit['gameplay_verified'])
            self.assertEqual(hashlib.sha256(prot).hexdigest(), audit['source_prot_sha256'])
            self.assertEqual((project._document(), project.undo_stack, project.redo_stack), before)
            self.assertEqual(project.imports['scene://town0b'], document)


if __name__ == '__main__':
    unittest.main()
