"""Frozen initial-animation presets across transfer, review and atomic history."""
from contextlib import nullcontext
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
from importer.core import decompress_lzs
from importer.man_assignments import load_man_assignment_context
from importer.pipeline import _disc_context, import_scene
from sdk.actor_animation import options, review as animation_review, source_actor
from sdk.actor_presets import preview, proposal_view
from sdk.build import build_project
from sdk.preset_batch import review as batch_review
from sdk.project import ProjectError, ProjectService
from sdk import resources  # Bind production aliases before synthetic fixture patches.
from sdk.template_files import export_file, parse, review as file_review
from integrations.legaia.tests.test_actor_animation import fixture

PRIVATE = ROOT / 'local-output/sdk-20260909'


def private_directory():
    PRIVATE.mkdir(parents=True, exist_ok=True)
    return tempfile.TemporaryDirectory(prefix='animated-presets-', dir=PRIVATE)


def assign(project, actor, clip):
    report = animation_review(project, actor, clip)
    project.command({key: report[key] for key in ('entity_id', 'animation_asset_id', 'source_key', 'review_key')} |
                    {'type': 'set_actor_animation'})
    return report


def apply_preset(project, template, actor, report=None):
    report = report or preview(project, template, actor)
    project.command(dict(type='apply_actor_template', template_id=template, entity_id=actor,
                         review_key=report['review_key']))
    return report


def import_preset(project, value, name):
    content = json.dumps(value)
    report = file_review(project, content, name)
    project.command(dict(type='import_actor_template', content=content, name=name,
                         review_key=report['review_key']))
    return report['template']['id']


class AnimatedPresetTests(unittest.TestCase):
    def setUp(self):
        directory = private_directory()
        self.addCleanup(directory.cleanup)
        self.project = ProjectService(Path(directory.name) / 'source')
        self.document, self.context, self.catalog = fixture()
        self.project.import_metadata(self.document, 'fixture.bin')
        self.target, self.witness, self.other, self.duplicate = [row['semantic_id'] for row in self.document['actors']]
        self.clip = 'animation://fixture/scene-anm/0001'
        for name, replacement in (
            ('importer.pipeline._disc_context', lambda _: nullcontext()),
            ('importer.pipeline.import_scene', lambda *_: deepcopy(self.document)),
            ('importer.scene_animation.load_scene_actor_animation_catalog', lambda *_: self.catalog),
            ('importer.man_assignments.load_man_assignment_context', lambda *_: self.context),
            ('sdk.resources._disc_context', lambda _: nullcontext()),
            ('sdk.resources.import_scene', lambda *_: deepcopy(self.document)),
        ):
            mocked = patch(name, replacement)
            mocked.start()
            self.addCleanup(mocked.stop)

    def snapshot(self, project=None):
        project = project or self.project
        return deepcopy((project._document(), project.undo_stack, project.redo_stack,
                         project.selected, project.assets.__dict__))

    def capture(self, capture='animation', name='Animation preset'):
        self.project.command(dict(type='create_actor_template', capture=capture,
                                  entity_id=self.target, name=name))
        return next(key for key, row in self.project.actor_templates.items() if row['name'] == name)

    def channels(self, actor):
        project = self.project
        binding = project.animation_authoring_options(actor)['binding']
        channel = project.animation_channel_values(actor, 0, 0)
        value = dict(animation_id=binding['semantic_id'],
                     source_record_sha256=binding['source_record']['record_sha256'],
                     edits=[dict(frame_index=0, object_index=0,
                                 translation={'x': channel['retail']['translation']['x'] ^ 1})])
        project.command(dict(type='set_animation_channels', entity_id=actor, value=value))
        return value, deepcopy(project.animation_authoring_options(actor))

    def test_capture_requires_authored_clip_and_keeps_legacy_scopes(self):
        project = self.project
        for capture in ('animation', 'animated'):
            before = self.snapshot()
            with self.assertRaises(ProjectError):
                self.capture(capture)
            self.assertEqual(self.snapshot(), before)
        assign(project, self.target, self.clip)
        captured = deepcopy(project.overrides[self.target]['ActorAnimation'])
        for capture in ('animation', 'animated'):
            key = self.capture(capture, capture)
            template = project.actor_templates[key]
            self.assertEqual(template['scope'], 'authored-actor-preset-v2')
            self.assertEqual(template['components'], {'ActorAnimation': captured})
            self.assertEqual(template['source']['entity_id'], self.target)
        project.command(dict(type='set_transform', entity_id=self.target, position={'x':704}))
        project.command(dict(type='set_actor_appearance', entity_id=self.target, donor_entity_id=self.target))
        full = self.capture('animated', 'Full preset')
        self.assertEqual(set(project.actor_templates[full]['components']), {'Transform', 'ActorAppearance', 'ActorAnimation'})
        self.assertEqual(project.actor_templates[full]['components']['Transform'], {'position': {'x':704}})
        clip_only = self.capture('animation', 'Only clip despite other edits')
        self.assertEqual(project.actor_templates[clip_only]['components'], {'ActorAnimation': captured})
        legacy = self.capture('combined', 'Legacy combined')
        self.assertEqual(project.actor_templates[legacy]['scope'], 'authored-actor-preset-v1')
        self.assertNotIn('ActorAnimation', project.actor_templates[legacy]['components'])
        self.assertEqual(export_file(project, legacy)['schema_version'], 'legaia.actor-preset-file.v1')
        self.assertEqual(export_file(project, full)['schema_version'], 'legaia.actor-preset-file.v2')

    def test_single_final_composition_preserves_channels_and_history(self):
        project = self.project
        assign(project, self.target, self.clip)
        project.command(dict(type='set_transform', entity_id=self.target, position={'x':704}))
        project.command(dict(type='set_actor_appearance', entity_id=self.target, donor_entity_id=self.target))
        key = self.capture('animated')
        component = deepcopy(project.actor_templates[key]['components']['ActorAnimation'])
        project.command(dict(type='set_actor_appearance', entity_id=self.duplicate, donor_entity_id=self.other))
        project.command(dict(type='set_transform', entity_id=self.duplicate, position={'z':960}))
        channels, channel_binding = self.channels(self.duplicate)
        before, depth = self.snapshot(), len(project.undo_stack)
        report = preview(project, key, self.duplicate)
        self.assertEqual(self.snapshot(), before)
        self.assertEqual(report['scope'], 'authored-actor-preset-v2')
        self.assertEqual(report['animation']['after'], component)
        self.assertEqual(report['animation']['base']['semantic_id'], 'animation://fixture/scene-anm/0000')
        self.assertEqual(report['animation']['effective']['semantic_id'], 'animation://fixture/scene-anm/0002')
        self.assertEqual(report['animation']['proposed']['actor_semantic_id'], self.witness)
        self.assertEqual(report['animation']['witness']['entity_id'], self.witness)
        self.assertEqual(report['after']['Transform']['position'], {'x':704, 'z':960})
        view = proposal_view(project, report)
        self.assertEqual(source_actor(view, self.duplicate, verify_disc=True)['semantic_id'], self.witness)
        self.assertEqual(self.snapshot(), before)
        apply_preset(project, key, self.duplicate, report)
        self.assertEqual(len(project.undo_stack), depth + 1)
        self.assertEqual(project.overrides[self.duplicate]['AnimationChannels'], channels)
        self.assertEqual(project.animation_authoring_options(self.duplicate), channel_binding)
        applied = deepcopy(project.overrides)
        project.undo()
        self.assertEqual(project.overrides, before[0]['authored'])
        project.redo()
        self.assertEqual(project.overrides, applied)
        # A matching preset must leave an unrelated pending Redo entry intact.
        project.command(dict(type='set_transform', entity_id=self.duplicate, position={'z':1024}))
        project.undo()
        history = deepcopy((project.undo_stack, project.redo_stack))
        matching = preview(project, key, self.duplicate)
        self.assertFalse(matching['changed'])
        apply_preset(project, key, self.duplicate, matching)
        self.assertEqual((project.undo_stack, project.redo_stack), history)
        project.redo()
        restored = ProjectService.open(project.save())
        self.assertEqual(restored.overrides, project.overrides)
        self.assertEqual(restored.actor_templates, project.actor_templates)
        self.assertEqual(restored.imports[project.active_scene], self.document)

    def test_animation_only_group_normalizes_inheritance_atomically(self):
        project = self.project
        assign(project, self.target, self.clip)
        key = self.capture()
        project.command(dict(type='set_transform', entity_id=self.duplicate, position={'z':960}))
        channels, binding = self.channels(self.duplicate)
        assign(project, self.duplicate, 'animation://fixture/scene-anm/0000')
        before, depth = self.snapshot(), len(project.undo_stack)
        report = batch_review(project, key, [self.duplicate, self.target])
        self.assertEqual(self.snapshot(), before)
        self.assertEqual(report['changed_count'], 1)
        row = next(row for row in report['targets'] if row['entity_id'] == self.duplicate)
        self.assertIsNone(row['appearance'])
        self.assertIsNone(row['animation']['after'])
        self.assertNotIn('ActorAnimation', row['after'])
        project.command(dict(type='apply_actor_preset_batch', template_id=key,
                             actor_ids=[self.duplicate, self.target], review_key=report['review_key']))
        self.assertEqual(len(project.undo_stack), depth + 1)
        self.assertEqual(project.overrides[self.duplicate], {'Transform': {'position': {'z':960}}, 'AnimationChannels':channels})
        self.assertEqual(project.animation_authoring_options(self.duplicate), binding)
        after = deepcopy(project.overrides)
        project.undo()
        self.assertEqual(project.overrides, before[0]['authored'])
        project.redo()
        self.assertEqual(project.overrides, after)
        restored = ProjectService.open(project.save())
        self.assertEqual(restored.overrides, after)

    def test_inherited_animation_only_preset_is_a_true_noop_on_untouched_actor(self):
        project = self.project
        assign(project,self.target,self.clip)
        key=self.capture('animation','Initial clip only')
        self.assertNotIn(self.witness,project.overrides)
        project.command(dict(type='set_transform',entity_id=self.other,position={'x':512}))
        project.undo()
        before=self.snapshot()
        report=preview(project,key,self.witness)
        self.assertFalse(report['changed'])
        self.assertIsNone(report['after'])
        view=proposal_view(project,report)
        self.assertNotIn(self.witness,view.overrides)
        apply_preset(project,key,self.witness,report)
        self.assertEqual(self.snapshot(),before)
        self.assertNotIn(self.witness,project.overrides)
        project.save()
        self.assertEqual(ProjectService.open(project.root).overrides,project.overrides)

    def test_legacy_group_presets_prove_and_preserve_retained_clip(self):
        project = self.project
        assign(project, self.target, self.clip)
        retained = deepcopy(project.overrides[self.target]['ActorAnimation'])
        project.command(dict(type='set_transform', entity_id=self.target, position={'x':512}))
        key = self.capture('position', 'Legacy position')
        before = deepcopy(project.overrides)
        report = batch_review(project, key, [self.target, self.duplicate])
        row = next(row for row in report['targets'] if row['entity_id']==self.target)
        self.assertEqual(row['animation']['after'], retained)
        project.command(dict(type='apply_actor_preset_batch', template_id=key,
                             actor_ids=[self.target,self.duplicate], review_key=report['review_key']))
        self.assertEqual(project.overrides[self.target]['ActorAnimation'], retained)
        project.undo()
        self.assertEqual(project.overrides, before)
        project.command(dict(type='set_actor_appearance', entity_id=self.target, donor_entity_id=self.witness))
        key = self.capture('appearance', 'Legacy appearance')
        before = deepcopy(project.overrides)
        report = batch_review(project, key, [self.target,self.duplicate])
        row = next(row for row in report['targets'] if row['entity_id']==self.target)
        self.assertEqual(row['animation']['after'], retained)
        project.command(dict(type='apply_actor_preset_batch', template_id=key,
                             actor_ids=[self.target,self.duplicate], review_key=report['review_key']))
        self.assertEqual(project.overrides[self.target]['ActorAnimation'], retained)
        project.undo()
        self.assertEqual(project.overrides, before)

    def test_transfer_and_source_edits_do_not_reinterpret_frozen_witness(self):
        project = self.project
        assign(project, self.target, self.clip)
        key = self.capture()
        frozen = deepcopy(project.actor_templates[key])
        project.command(dict(type='set_actor_appearance', entity_id=self.target, donor_entity_id=self.target))
        with_appearance = self.capture('animated', 'Frozen model and clip')
        frozen_appearance = deepcopy(project.actor_templates[with_appearance])
        assign(project, self.target, None)
        project.command(dict(type='set_actor_appearance', entity_id=self.target, donor_entity_id=self.other))
        project._validate_template(key, frozen)
        project._validate_template(with_appearance, frozen_appearance)
        self.assertEqual(export_file(project, with_appearance)['template'], frozen_appearance)
        value = export_file(project, key)
        self.assertEqual(value['template'], frozen)
        self.assertEqual(value['schema_version'], 'legaia.actor-preset-file.v2')
        target = ProjectService(project.root.parent / 'destination')
        target.import_metadata(self.document, 'fixture.bin')
        before, depth = self.snapshot(target), len(target.undo_stack)
        imported_evidence = deepcopy(target.imports)
        imported = import_preset(target, value, 'Transferred animation')
        self.assertNotEqual(imported, key)
        self.assertEqual(target.overrides, {})
        self.assertEqual(len(target.undo_stack), depth + 1)
        self.assertEqual(target.actor_templates[imported]['components'], frozen['components'])
        target.undo()
        self.assertNotIn(imported, target.actor_templates)
        target.redo()
        apply_preset(target, imported, self.target)
        self.assertEqual(target.overrides[self.target]['ActorAnimation'], frozen['components']['ActorAnimation'])
        self.assertEqual(source_actor(target, self.target, verify_disc=True)['semantic_id'], self.witness)
        restored = ProjectService.open(target.save())
        self.assertEqual(restored.actor_templates, target.actor_templates)
        self.assertEqual(restored.overrides, target.overrides)
        self.assertEqual(project.actor_templates[key], frozen)
        self.assertEqual(target.imports, imported_evidence)

    def test_forged_stale_model_and_last_target_failure_leave_no_partial_changes(self):
        project = self.project
        assign(project, self.target, self.clip)
        key = self.capture()
        value = export_file(project, key)
        for mutation in (
            lambda item: item['template']['components']['ActorAnimation'].update(source_record_sha256='0' * 64),
            lambda item: item['template']['components']['ActorAnimation'].update(donor_entity_id='scene://foreign/actors/man-p1/0001'),
            lambda item: item['template']['source'].update(scene_id='scene://foreign'),
            lambda item: item.update(source_import_sha256='0' * 64),
        ):
            forged = deepcopy(value)
            mutation(forged)
            before = self.snapshot()
            with self.assertRaises(ProjectError):
                file_review(project, json.dumps(forged), 'Forged preset')
            self.assertEqual(self.snapshot(), before)
        for ids in ([self.target, self.other], [self.other, self.target]):
            before = self.snapshot()
            with self.assertRaises(ProjectError):
                batch_review(project, key, ids)
            self.assertEqual(self.snapshot(), before)
        before = self.snapshot()
        with self.assertRaises(ProjectError):
            preview(project, key, self.other)
        self.assertEqual(self.snapshot(), before)
        report = preview(project, key, self.target)
        project.command(dict(type='set_transform', entity_id=self.target, position={'z':960}))
        before = self.snapshot()
        with self.assertRaises(ProjectError):
            apply_preset(project, key, self.target, report)
        self.assertEqual(self.snapshot(), before)
        stale = file_review(project, json.dumps(value), 'Library copy')
        project.command(dict(type='rename_actor_template', template_id=key, name='Renamed source'))
        before = self.snapshot()
        with self.assertRaises(ProjectError):
            project.command(dict(type='import_actor_template', content=json.dumps(value), name='Library copy', review_key=stale['review_key']))
        self.assertEqual(self.snapshot(), before)
        project.mode = 'live'
        with self.assertRaises(ProjectError):
            apply_preset(project, key, self.target)

    def test_v1_files_remain_strict_and_omitted_clip_rejects_incompatible_appearance(self):
        project = self.project
        assign(project, self.target, self.clip)
        animated = self.capture()
        new_file = export_file(project, animated)
        with self.assertRaises(ProjectError):
            parse(json.dumps(dict(new_file, schema_version='legaia.actor-preset-file.v1')))
        project.command(dict(type='set_transform', entity_id=self.other, position={'x':704}))
        project.command(dict(type='set_actor_appearance', entity_id=self.other, donor_entity_id=self.other))
        project.command(dict(type='create_actor_template', capture='combined', entity_id=self.other, name='Legacy other model'))
        legacy = next(key for key, item in project.actor_templates.items() if item['name'] == 'Legacy other model')
        old_file = export_file(project, legacy)
        self.assertEqual(old_file['schema_version'], 'legaia.actor-preset-file.v1')
        self.assertEqual(parse(json.dumps(old_file)), old_file)
        with self.assertRaises(ProjectError):
            parse(json.dumps(dict(old_file, schema_version='legaia.actor-preset-file.v2')))
        before = self.snapshot()
        with self.assertRaises(ProjectError):
            preview(project, legacy, self.target)
        self.assertEqual(self.snapshot(), before)
        forged = deepcopy(old_file['template'])
        forged['components']['ActorAnimation'] = deepcopy(new_file['template']['components']['ActorAnimation'])
        with self.assertRaises(ProjectError):
            project._validate_template(legacy, forged)
        reopened = ProjectService.open(project.save())
        self.assertEqual(reopened.actor_templates, project.actor_templates)


@unittest.skipUnless(os.environ.get('LEGAIA_DISC_BIN'), 'requires private retail disc')
class RetailAnimatedPresetTests(unittest.TestCase):
    def test_town0b_transfer_apply_history_and_build_change_only_expected_man_header(self):
        disc = os.environ['LEGAIA_DISC_BIN']
        with private_directory() as directory, _disc_context(disc):
            source = ProjectService(Path(directory) / 'source')
            document = import_scene(disc, 'town0b')
            source.import_metadata(document, disc)
            actor = 'scene://town0b/actors/man-p1/0019'
            witness = 'scene://town0b/actors/man-p1/0049'
            clip = 'animation://town0b/scene-anm/0012'
            assign(source, actor, clip)
            source.command(dict(type='create_actor_template', capture='animation', entity_id=actor, name='Observed alternative'))
            template = next(iter(source.actor_templates))
            value = export_file(source, template)
            target = ProjectService(Path(directory) / 'destination')
            target.import_metadata(document, disc)
            transferred = import_preset(target, value, 'Transferred alternative')
            binding = target.animation_authoring_options(actor)['binding']
            channel = target.animation_channel_values(actor, 0, 0)
            channels = dict(animation_id=binding['semantic_id'], source_record_sha256=binding['source_record']['record_sha256'],
                edits=[dict(frame_index=0, object_index=0, translation={'x':channel['retail']['translation']['x'] ^ 1})])
            target.command(dict(type='set_animation_channels', entity_id=actor, value=channels))
            baseline_components = deepcopy(target.overrides)
            baseline = build_project(target)
            before_depth = len(target.undo_stack)
            report = preview(target, transferred, actor)
            self.assertEqual(report['animation']['proposed']['actor_semantic_id'], witness)
            apply_preset(target, transferred, actor, report)
            self.assertEqual(len(target.undo_stack), before_depth + 1)
            self.assertEqual(target.overrides[actor]['AnimationChannels'], channels)
            self.assertEqual(target.animation_authoring_options(actor)['binding'], binding)
            applied = deepcopy(target.overrides)
            target.undo()
            self.assertEqual(target.overrides, baseline_components)
            target.redo()
            self.assertEqual(target.overrides, applied)
            saved = target.save()
            saved_bytes = saved.read_bytes()
            opened = ProjectService.open(saved)
            self.assertEqual(opened.actor_templates, target.actor_templates)
            self.assertEqual(opened.overrides, applied)
            result = build_project(opened)
            context = load_man_assignment_context(disc, 'town0b')
            with zipfile.ZipFile(result['path']) as package:
                decoded = decompress_lzs(package.read('assets/town0b-man.lzs'), len(context._man))[0]
            self.assertEqual(len(decoded), len(context._man))
            self.assertEqual([index for index, pair in enumerate(zip(context._man, decoded)) if pair[0] != pair[1]], [9471])
            self.assertEqual((context._man[9471], decoded[9471]), (14, 13))
            audit = json.loads(Path(result['audit']).read_text(encoding='utf-8'))
            assignments = [row for row in audit['edits'] if row.get('scope') == 'initial-man-header-only']
            self.assertEqual(len(assignments), 1)
            change = assignments[0]
            start, end = context._ranges[12]
            self.assertEqual(change['assignment_source_record_sha256'], hashlib.sha256(context._anm[start:end]).hexdigest())
            self.assertEqual((change['assignment_kind'], change['animation_asset_id']), ('ActorAnimation', clip))
            self.assertEqual(saved.read_bytes(), saved_bytes)
            assign(opened, actor, None)
            self.assertEqual(opened.overrides, baseline_components)
            self.assertEqual(build_project(opened)['sha256'], baseline['sha256'])
            group = batch_review(opened, transferred, [witness, actor])
            depth = len(opened.undo_stack)
            opened.command(dict(type='apply_actor_preset_batch', template_id=transferred, actor_ids=[actor, witness], review_key=group['review_key']))
            self.assertEqual(len(opened.undo_stack), depth + 1)
            self.assertEqual(opened.overrides[actor]['ActorAnimation']['animation_asset_id'], clip)
            self.assertNotIn('ActorAnimation', opened.overrides.get(witness, {}))
            opened.undo()
            self.assertEqual(opened.overrides, baseline_components)
            self.assertEqual(opened.imports['scene://town0b'], document)
            self.assertEqual(source.imports['scene://town0b'], document)
            self.assertEqual(saved.read_bytes(), saved_bytes)


if __name__ == '__main__':
    unittest.main()
