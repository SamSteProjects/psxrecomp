"""Bounded source qualification, history and persistence for reviewed MAP cells."""
from copy import deepcopy
from hashlib import sha256
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from importer.trigger_authoring import patch_field_triggers, trigger_authoring_options
from sdk.project import ProjectError, ProjectService
from sdk.trigger_cells import apply, effective_annotations, review
from test_field_spatial import table
from test_project_workflow import synthetic_scene

TRIGGER = 'trigger://fixture/field-map/primary/kind-0/0000'
OTHER = 'trigger://fixture/field-map/primary/kind-1/0000'
REQUESTED = dict(tile_x=1, tile_z=10)


def fixture():
    return bytes(0x10000) + table({0: [(6, 4, 29, 255), (8, 9, 3, 5)],
                                  1: [(2, 1, 17, 7), (10, 20, 3, 1)],
                                  2: [(9, 8, 7, 6)],
                                  3: [(2, 1, 8, 10, 17, 200, 1, 46)]})


def command(report, values=REQUESTED, action='set'):
    return dict(type='apply_trigger_cells', trigger_id=report['trigger_id'],
                values=deepcopy(values), action=action, review_key=report['review_key'])


class TriggerCellsTests(unittest.TestCase):
    def test_readonly_layers_use_unbiased_one_tile_cells_and_exact_source_rows(self):
        with tempfile.TemporaryDirectory() as directory:
            project = ProjectService(Path(directory))
            imported = synthetic_scene()
            project.import_metadata(imported)
            source = fixture()
            with patch.object(project, '_environment_source', return_value=source):
                current = review(project, TRIGGER)
                self.assertEqual(current['schema_version'], 'legaia.trigger-cells-review.v1')
                self.assertTrue(current['read_only'])
                self.assertFalse(current['project_change'])
                self.assertEqual(current['effective_change_count'], 0)
                self.assertEqual(current['values_layers']['authored'], {})
                self.assertEqual(current['tile_bounds_layers']['imported'],
                                 dict(x_min=6, x_max=7, z_min=4, z_max=5))
                self.assertEqual(current['world_bounds_layers']['imported'],
                                 dict(x_min=768, x_max=896, z_min=512, z_max=640))
                proposed = review(project, TRIGGER, REQUESTED)
                self.assertEqual(proposed['effective_change_count'], 2)
                self.assertTrue(proposed['project_change'])
                self.assertEqual(proposed['values_layers']['current'], dict(tile_x=6, tile_z=4))
                self.assertEqual(proposed['world_bounds_layers']['proposed'],
                                 dict(x_min=128, x_max=256, z_min=1280, z_max=1408))
                row = trigger_authoring_options(source, 'fixture')['records'][0]
                self.assertEqual(proposed['source'], dict(map_sha256=sha256(source).hexdigest(),
                    row_sha256=row['sha256'], table_kind=0, record_index=0,
                    byte_offset=row['byte_offset'], byte_length=4))
                self.assertEqual(proposed['trigger_kind'], 0)
                self.assertEqual((proposed['scope'], proposed['height_status'],
                                  proposed['activation'], proposed['gameplay_verified']),
                                 ('source-MAP-trigger-cell-only', 'unknown', 'not_evaluated', False))
                unknown_gate = review(project, OTHER, dict(tile_x=255, tile_z=0))
                self.assertEqual(unknown_gate['trigger_kind'], 1)
                self.assertEqual(unknown_gate['world_bounds_layers']['proposed'],
                                 dict(x_min=32640, x_max=32768, z_min=0, z_max=128))
                proposed['values_layers']['proposed']['tile_x'] = 0
                self.assertEqual(REQUESTED['tile_x'], 1)
                self.assertEqual(project.imports['scene://fixture'], imported)
                self.assertEqual(project.overrides, {})
                self.assertEqual(project.undo_stack, [])

    def test_atomic_apply_history_reopen_noop_and_row_specific_clear(self):
        with tempfile.TemporaryDirectory() as directory:
            project = ProjectService(Path(directory))
            project.import_metadata(synthetic_scene())
            project.save()
            source = fixture()
            with patch.object(ProjectService, '_environment_source', return_value=source):
                report = review(project, TRIGGER, REQUESTED)
                project.command(command(report))
                self.assertEqual(len(project.undo_stack), 1)
                self.assertTrue(project.dirty)
                first = deepcopy(project.overrides)
                project.undo()
                self.assertFalse(project.dirty)
                project.redo()
                self.assertEqual(project.overrides, first)
                reopened = ProjectService.open(project.save())
                self.assertEqual(reopened.overrides, first)
                self.assertFalse(reopened.dirty)
                depth = len(project.undo_stack)
                repeated = review(project, TRIGGER, REQUESTED)
                self.assertFalse(repeated['project_change'])
                self.assertEqual(repeated['effective_change_count'], 0)
                apply(project, command(repeated))
                self.assertEqual(len(project.undo_stack), depth)
                other_values = dict(tile_x=4, tile_z=8)
                other = review(project, OTHER, other_values)
                apply(project, command(other, other_values))
                other_before = deepcopy(project.overrides['scene://fixture']['TriggerCells']['edits'][1])
                cleared = review(project, TRIGGER, action='clear')
                self.assertEqual(cleared['values_layers']['proposed'], cleared['values_layers']['imported'])
                self.assertEqual(cleared['values_layers']['current'], REQUESTED)
                depth = len(project.undo_stack)
                apply(project, command(cleared, None, 'clear'))
                self.assertEqual(len(project.undo_stack), depth + 1)
                self.assertEqual(project.overrides['scene://fixture']['TriggerCells']['edits'], [other_before])
                inherited = review(project, OTHER, other['values_layers']['imported'])
                apply(project, command(inherited, other['values_layers']['imported']))
                self.assertEqual(project.overrides, {})
                depth = len(project.undo_stack)
                apply(project, command(review(project, TRIGGER, action='clear'), None, 'clear'))
                self.assertEqual(len(project.undo_stack), depth)

    def test_annotations_keep_imported_payload_and_qualify_every_retained_edit(self):
        with tempfile.TemporaryDirectory() as directory:
            project = ProjectService(Path(directory))
            project.import_metadata(synthetic_scene())
            source = fixture()
            with patch.object(project, '_environment_source', return_value=source):
                self.assertEqual(effective_annotations(project, project.active_scene), [])
                report = review(project, OTHER, REQUESTED)
                apply(project, command(report))
                before = deepcopy(project.overrides)
                project.mode, project.active_scene = 'live', None
                annotations = effective_annotations(project, 'scene://fixture')
                self.assertEqual(len(annotations), 1)
                annotation = annotations[0]
                self.assertEqual(annotation['trigger_id'], OTHER)
                self.assertEqual(annotation['values_layers']['effective'], REQUESTED)
                self.assertEqual(annotation['values_layers']['imported'], report['values_layers']['imported'])
                self.assertEqual(annotation['row_sha256'], report['source']['row_sha256'])
                self.assertEqual(annotation['world_bounds_layers']['effective'], report['world_bounds_layers']['proposed'])
                annotation['values_layers']['authored']['tile_x'] = 0
                self.assertEqual(project.overrides, before)
                binding = project.overrides['scene://fixture']['TriggerCells']
                changed, _ = patch_field_triggers(source, binding['source_sha256'], 'fixture', binding['edits'])
                row = next(row for row in trigger_authoring_options(source, 'fixture')['records']
                           if row['trigger_id'] == OTHER)
                offset = row['byte_offset']
                self.assertEqual(changed[offset + 2:offset + 4], bytes((17, 7)))
                self.assertEqual(sum(a != b for a, b in zip(changed, source)), 2)
                binding['edits'].append(dict(trigger_id=TRIGGER, tile_x=True, tile_z=1))
                with self.assertRaises(ProjectError):
                    effective_annotations(project, 'scene://fixture')

    def test_direct_commands_canonicalize_inherited_cells_without_spurious_history(self):
        with tempfile.TemporaryDirectory() as directory:
            project = ProjectService(Path(directory))
            project.import_metadata(synthetic_scene())
            source = fixture()
            other_values = dict(tile_x=4, tile_z=8)
            setting = dict(type='set_trigger_cells', entity_id='scene://fixture',
                           value=dict(source_sha256=sha256(source).hexdigest(),
                                      edits=[dict(trigger_id=OTHER, **other_values),
                                             dict(trigger_id=TRIGGER, **REQUESTED)]))
            with patch.object(ProjectService, '_environment_source', return_value=source):
                project.command(setting)
                self.assertEqual([row['trigger_id'] for row in
                                  project.overrides['scene://fixture']['TriggerCells']['edits']], [TRIGGER, OTHER])
                depth = len(project.undo_stack)
                project.command(setting)
                self.assertEqual(len(project.undo_stack), depth)
                setting['value']['edits'][1] = dict(trigger_id=TRIGGER, tile_x=6, tile_z=4)
                project.command(setting)
                self.assertEqual(project.overrides['scene://fixture']['TriggerCells']['edits'],
                                 [dict(trigger_id=OTHER, **other_values)])
                setting['value']['edits'][0] = dict(trigger_id=OTHER, tile_x=2, tile_z=1)
                project.command(setting)
                self.assertEqual(project.overrides, {})
                depth = len(project.undo_stack)
                project.undo()
                self.assertEqual(project.overrides['scene://fixture']['TriggerCells']['edits'],
                                 [dict(trigger_id=OTHER, **other_values)])
                project.redo()
                project.command(dict(type='clear_trigger_cells', entity_id='scene://fixture'))
                self.assertEqual(len(project.undo_stack), depth)
                reopened = ProjectService.open(project.save())
                self.assertEqual(reopened.overrides, {})
                self.assertFalse(reopened.dirty)

    def test_invalid_inputs_and_stale_project_map_or_requested_cells_reject_atomically(self):
        with tempfile.TemporaryDirectory() as directory:
            project = ProjectService(Path(directory))
            project.import_metadata(synthetic_scene())
            source = fixture()
            with patch.object(project, '_environment_source', return_value=source):
                for invalid in ({**REQUESTED, 'tile_x': True}, {**REQUESTED, 'tile_x': -1},
                                {**REQUESTED, 'tile_z': 256}, {**REQUESTED, 'tile_z': 1.0},
                                {**REQUESTED, 'gate': 1}, {'tile_x': 1}, []):
                    with self.assertRaises(ProjectError):
                        review(project, TRIGGER, invalid)
                for identifier in (OTHER + '/raw', TRIGGER.replace('primary', 'fallback'),
                                   TRIGGER.replace('fixture', 'another'), TRIGGER.replace('kind-0', 'kind-2'),
                                   TRIGGER.replace('0000', '9999'), True):
                    with self.assertRaises(ProjectError):
                        review(project, identifier, REQUESTED)
                with self.assertRaises(ProjectError):
                    review(project, TRIGGER, REQUESTED, 'clear')
                report = review(project, TRIGGER, REQUESTED)
                for changed_command in ({**command(report), 'values': {**REQUESTED, 'tile_x': 2}},
                                        {**command(report), 'source': report['source']},
                                        {**command(report), 'review_key': '0' * 64}):
                    with self.assertRaises(ProjectError):
                        apply(project, changed_command)
                project.name = 'Different name'
                with self.assertRaises(ProjectError):
                    apply(project, command(report))
                report = review(project, TRIGGER, REQUESTED)
                project.mode = 'live'
                with self.assertRaises(ProjectError):
                    apply(project, command(report))
                project.mode = 'edit'
                project.active_scene = None
                with self.assertRaises(ProjectError):
                    apply(project, command(report))
                project.active_scene = 'scene://fixture'
                changed = bytearray(source)
                changed[0] = 1
                with patch.object(project, '_environment_source', return_value=bytes(changed)):
                    with self.assertRaises(ProjectError):
                        apply(project, command(report))
                fresh = review(project, TRIGGER, REQUESTED)
                # Re-review succeeds; the command must requalify the source before mutation.
                with patch.object(project, '_environment_source', side_effect=[source, source, bytes(changed)]):
                    with self.assertRaises(ProjectError):
                        apply(project, command(fresh))
                self.assertEqual(project.overrides, {})
                project.overrides = {'scene://fixture': {'TriggerCells': None}}
                with self.assertRaises(ProjectError):
                    review(project, TRIGGER, REQUESTED)
                project.overrides = {'scene://fixture': {'TriggerCells': dict(source_sha256='0' * 64,
                    edits=[dict(trigger_id=TRIGGER, **REQUESTED)])}}
                with self.assertRaises(ProjectError):
                    review(project, TRIGGER, REQUESTED)
                self.assertEqual(project.undo_stack, [])

    def test_source_or_project_drift_during_capture_cannot_deliver_a_review(self):
        with tempfile.TemporaryDirectory() as directory:
            project = ProjectService(Path(directory))
            project.import_metadata(synthetic_scene())
            source = fixture()
            changed = bytearray(source)
            changed[0] = 1
            with patch.object(project, '_environment_source', side_effect=[source, bytes(changed)]):
                with self.assertRaisesRegex(ProjectError, 'source changed'):
                    review(project, TRIGGER, REQUESTED)
            def drift(scene):
                project.name = 'Changed during capture'
                return source
            with patch.object(project, '_environment_source', side_effect=drift):
                with self.assertRaisesRegex(ProjectError, 'Project changed'):
                    review(project, TRIGGER, REQUESTED)
            self.assertEqual(project.overrides, {})
            self.assertEqual(project.undo_stack, [])
