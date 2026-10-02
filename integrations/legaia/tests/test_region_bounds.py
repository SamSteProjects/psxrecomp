"""Small source qualification and command checks for reviewed MAP regions."""
from copy import deepcopy
from hashlib import sha256
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from importer.region_authoring import patch_field_regions, region_authoring_options
from sdk.project import ProjectError, ProjectService
from sdk.region_bounds import apply, effective_annotations, review
from test_field_spatial import table
from test_project_workflow import synthetic_scene

REGION = 'region://fixture/field-map/primary/0000'
OTHER = 'region://fixture/field-map/primary/0001'
REQUESTED = dict(x0=1, z0=10, x1=9, z1=2)


def fixture():
    return bytes(0x10000) + table({3: [(6, 4, 6, 4, 3, 29, 90, 255),
                                      (2, 1, 8, 10, 17, 200, 1, 46)]})


def command(report, values=REQUESTED, action='set'):
    return dict(type='apply_region_bounds', region_id=report['region_id'],
                values=deepcopy(values), action=action, review_key=report['review_key'])


class RegionBoundsTests(unittest.TestCase):
    def test_readonly_layers_use_retail_normalization_and_distinct_world_bias(self):
        with tempfile.TemporaryDirectory() as directory:
            project = ProjectService(Path(directory))
            imported = synthetic_scene()
            project.import_metadata(imported)
            source = fixture()
            with patch.object(project, '_environment_source', return_value=source):
                current = review(project, REGION)
                self.assertTrue(current['read_only'])
                self.assertFalse(current['project_change'])
                self.assertEqual(current['effective_change_count'], 0)
                self.assertEqual(current['values_layers']['authored'], {})
                self.assertEqual(current['tile_bounds_layers']['imported'],
                                 dict(x_min=6, x_max=8, z_min=2, z_max=4))
                self.assertEqual(current['world_bounds_layers']['imported'],
                                 dict(x_min=832, x_max=1088, z_min=320, z_max=576))
                proposed = review(project, REGION, REQUESTED)
                self.assertEqual(proposed['effective_change_count'], 4)
                self.assertTrue(proposed['project_change'])
                self.assertEqual(proposed['values_layers']['current'], dict(x0=6, z0=4, x1=6, z1=4))
                self.assertEqual(proposed['world_bounds_layers']['proposed'],
                                 dict(x_min=192, x_max=1216, z_min=320, z_max=1344))
                row = region_authoring_options(source, 'fixture')['records'][0]
                self.assertEqual(proposed['source'], dict(map_sha256=sha256(source).hexdigest(),
                    row_sha256=row['sha256'], record_index=0, byte_offset=row['byte_offset'], byte_length=8))
                self.assertEqual(proposed['region_type'], 3)
                self.assertEqual((proposed['height_status'], proposed['activation'], proposed['gameplay_verified']),
                                 ('unknown', 'not_evaluated', False))
                proposed['values_layers']['proposed']['x0'] = 0
                self.assertEqual(REQUESTED['x0'], 1)
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
                report = review(project, REGION, REQUESTED)
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
                repeated = review(project, REGION, REQUESTED)
                self.assertFalse(repeated['project_change'])
                self.assertEqual(repeated['effective_change_count'], 0)
                apply(project, command(repeated))
                self.assertEqual(len(project.undo_stack), depth)
                other_values = dict(x0=4, z0=8, x1=1, z1=7)
                other = review(project, OTHER, other_values)
                apply(project, command(other, other_values))
                other_before = deepcopy(project.overrides['scene://fixture']['RegionBounds']['edits'][1])
                cleared = review(project, REGION, action='clear')
                self.assertEqual(cleared['values_layers']['proposed'], cleared['values_layers']['imported'])
                self.assertEqual(cleared['values_layers']['current'], REQUESTED)
                depth = len(project.undo_stack)
                apply(project, command(cleared, None, 'clear'))
                self.assertEqual(len(project.undo_stack), depth + 1)
                self.assertEqual(project.overrides['scene://fixture']['RegionBounds']['edits'], [other_before])
                restored = review(project, OTHER, other['values_layers']['imported'])
                apply(project, command(restored, other['values_layers']['imported']))
                self.assertEqual(project.overrides, {})
                depth = len(project.undo_stack)
                empty = review(project, REGION, action='clear')
                apply(project, command(empty, None, 'clear'))
                self.assertEqual(len(project.undo_stack), depth)

    def test_annotations_qualify_whole_binding_keep_source_and_allow_readonly_live_mode(self):
        with tempfile.TemporaryDirectory() as directory:
            project = ProjectService(Path(directory))
            project.import_metadata(synthetic_scene())
            source = fixture()
            with patch.object(project, '_environment_source', return_value=source):
                self.assertEqual(effective_annotations(project, project.active_scene), [])
                report = review(project, REGION, REQUESTED)
                apply(project, command(report))
                before = deepcopy(project.overrides)
                project.mode = 'live'
                project.active_scene = None
                annotations = effective_annotations(project, 'scene://fixture')
                self.assertEqual(len(annotations), 1)
                annotation = annotations[0]
                self.assertEqual(annotation['region_id'], REGION)
                self.assertEqual(annotation['values_layers']['effective'], REQUESTED)
                self.assertEqual(annotation['values_layers']['imported'], report['values_layers']['imported'])
                self.assertEqual(annotation['row_sha256'], report['source']['row_sha256'])
                self.assertEqual(annotation['world_bounds_layers']['effective'], report['world_bounds_layers']['proposed'])
                annotation['values_layers']['authored']['x0'] = 0
                self.assertEqual(project.overrides, before)
                binding = project.overrides['scene://fixture']['RegionBounds']
                changed, _ = patch_field_regions(source, binding['source_sha256'], 'fixture', binding['edits'])
                record = region_authoring_options(source, 'fixture')['records'][0]
                offset = record['byte_offset']
                self.assertEqual(changed[offset + 4:offset + 8], source[offset + 4:offset + 8])
                binding['edits'].append(dict(region_id=OTHER, x0=True, z0=1, x1=8, z1=10))
                with self.assertRaises(ProjectError):
                    effective_annotations(project, 'scene://fixture')

    def test_direct_commands_canonicalize_order_and_inherited_rows_without_spurious_history(self):
        with tempfile.TemporaryDirectory() as directory:
            project = ProjectService(Path(directory))
            project.import_metadata(synthetic_scene())
            source = fixture()
            rows = region_authoring_options(source, 'fixture')['records']
            retail = [{key: row['encoded'][key] for key in ('x0', 'z0', 'x1', 'z1')}
                      for row in rows]
            other_values = dict(x0=4, z0=8, x1=1, z1=7)
            setting = dict(type='set_region_bounds', entity_id='scene://fixture',
                           value=dict(source_sha256=sha256(source).hexdigest(),
                                      edits=[dict(region_id=OTHER, **other_values),
                                             dict(region_id=REGION, **REQUESTED)]))
            with patch.object(ProjectService, '_environment_source', return_value=source):
                project.command(setting)
                canonical = project.overrides['scene://fixture']['RegionBounds']
                self.assertEqual([row['region_id'] for row in canonical['edits']], [REGION, OTHER])
                depth = len(project.undo_stack)
                project.command(setting)
                self.assertEqual(len(project.undo_stack), depth)
                inherited_one = deepcopy(setting)
                inherited_one['value']['edits'][1] = dict(region_id=REGION, **retail[0])
                project.command(inherited_one)
                self.assertEqual(project.overrides['scene://fixture']['RegionBounds']['edits'],
                                 [dict(region_id=OTHER, **other_values)])
                inherited_all = deepcopy(inherited_one)
                inherited_all['value']['edits'][0] = dict(region_id=OTHER, **retail[1])
                project.command(inherited_all)
                self.assertEqual(project.overrides, {})
                depth = len(project.undo_stack)
                project.undo()
                self.assertEqual(project.overrides['scene://fixture']['RegionBounds']['edits'],
                                 [dict(region_id=OTHER, **other_values)])
                project.redo()
                self.assertEqual(project.overrides, {})
                project.command(dict(type='clear_region_bounds', entity_id='scene://fixture'))
                self.assertEqual(len(project.undo_stack), depth)
                reopened = ProjectService.open(project.save())
                self.assertEqual(reopened.overrides, {})
                self.assertFalse(reopened.dirty)

    def test_invalid_inputs_and_stale_project_map_or_requested_values_reject_atomically(self):
        with tempfile.TemporaryDirectory() as directory:
            project = ProjectService(Path(directory))
            project.import_metadata(synthetic_scene())
            source = fixture()
            with patch.object(project, '_environment_source', return_value=source):
                for invalid in ({**REQUESTED, 'x0': True}, {**REQUESTED, 'x1': -1},
                                {**REQUESTED, 'z0': 256}, {**REQUESTED, 'z1': 1.0},
                                {**REQUESTED, 'height': 1}, {'x0': 1}, []):
                    with self.assertRaises(ProjectError):
                        review(project, REGION, invalid)
                for identifier in (OTHER + '/raw', REGION.replace('primary', 'fallback'),
                                   REGION.replace('fixture', 'another'),
                                   'region://fixture/field-map/primary/9999', True):
                    with self.assertRaises(ProjectError):
                        review(project, identifier, REQUESTED)
                with self.assertRaises(ProjectError):
                    review(project, REGION, REQUESTED, 'clear')
                report = review(project, REGION, REQUESTED)
                with self.assertRaises(ProjectError):
                    apply(project, {**command(report), 'values': {**REQUESTED, 'x0': 2}})
                with self.assertRaises(ProjectError):
                    apply(project, {**command(report), 'source': report['source']})
                project.name = 'Different name'
                with self.assertRaises(ProjectError):
                    apply(project, command(report))
                report = review(project, REGION, REQUESTED)
                project.mode = 'live'
                with self.assertRaises(ProjectError):
                    apply(project, command(report))
                project.mode = 'edit'
                changed = bytearray(source)
                changed[0] = 1
                with patch.object(project, '_environment_source', return_value=bytes(changed)):
                    with self.assertRaises(ProjectError):
                        apply(project, command(report))
                project.overrides = {'scene://fixture': {'RegionBounds': None}}
                with self.assertRaises(ProjectError):
                    review(project, REGION, REQUESTED)
                project.overrides = {'scene://fixture': {'RegionBounds': dict(source_sha256='0' * 64,
                    edits=[dict(region_id=REGION, **REQUESTED)])}}
                with self.assertRaises(ProjectError):
                    review(project, REGION, REQUESTED)
                self.assertEqual(project.undo_stack, [])

    def test_capture_drift_rejects_without_applying_authored_state(self):
        with tempfile.TemporaryDirectory() as directory:
            project = ProjectService(Path(directory))
            project.import_metadata(synthetic_scene())
            source = fixture()
            changed = bytearray(source)
            changed[0] = 1
            with patch.object(project, '_environment_source', side_effect=[source, bytes(changed)]):
                with self.assertRaisesRegex(ProjectError, 'source changed'):
                    review(project, REGION, REQUESTED)
            def drift(scene):
                project.name = 'Changed during capture'
                return source
            with patch.object(project, '_environment_source', side_effect=drift):
                with self.assertRaisesRegex(ProjectError, 'Project changed'):
                    review(project, REGION, REQUESTED)
            self.assertEqual(project.overrides, {})
            self.assertEqual(project.undo_stack, [])
