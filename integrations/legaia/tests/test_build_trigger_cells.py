"""Trigger byte audits and retail MAP composition, without gameplay acceptance."""
from copy import deepcopy
from hashlib import sha256
import json
import os
from pathlib import Path
import tempfile
import unittest
import zipfile

from importer.pipeline import import_scene
from importer.trigger_authoring import patch_field_triggers, trigger_authoring_options
from importer.region_authoring import region_authoring_options
from sdk.project import ProjectService
from sdk.trigger_cells import review, apply
from sdk.build import BuildError, _merge_trigger_patch, build_project, package_change_kinds
from test_field_spatial import table


class TriggerMergeTests(unittest.TestCase):
    def test_rejects_payload_changes_false_audits_and_overlapping_edits(self):
        original = bytes(0x10000) + table({0: [(5, 7, 91, 83)]})
        record = trigger_authoring_options(original, 'fixture')['records'][0]
        binding = dict(source_sha256=sha256(original).hexdigest(), edits=[dict(
            trigger_id=record['trigger_id'], tile_x=6, tile_z=7)])
        changed, audit = patch_field_triggers(original, binding['source_sha256'], 'fixture', binding['edits'])
        self.assertEqual(_merge_trigger_patch(original, original, changed, audit, 'fixture', binding), changed)
        for bad_audit in ([], audit + audit, [{**audit[0], 'after_value': 20}],
                          [{**audit[0], 'trigger_id': 'trigger://fixture/field-map/primary/kind-0/0001'}]):
            with self.assertRaises(BuildError):
                _merge_trigger_patch(original, original, changed, bad_audit, 'fixture', binding)
        bad = bytearray(changed)
        bad[record['byte_offset'] + 2] ^= 1
        with self.assertRaises(BuildError):
            _merge_trigger_patch(original, original, bytes(bad), audit, 'fixture', binding)
        with self.assertRaises(BuildError):
            _merge_trigger_patch(original, changed, changed, audit, 'fixture', binding)


@unittest.skipUnless(os.environ.get('LEGAIA_DISC_BIN'), 'requires private retail disc')
class TriggerBuildTests(unittest.TestCase):
    def test_saved_cells_compose_one_exact_map_with_regions_walls_and_scenery(self):
        private = Path(__file__).resolve().parents[3] / 'local-output/sdk-20260909'
        with tempfile.TemporaryDirectory(prefix='trigger-build-', dir=private) as raw:
            project = ProjectService(Path(raw))
            project.import_metadata(import_scene(os.environ['LEGAIA_DISC_BIN'], 'town01'), os.environ['LEGAIA_DISC_BIN'])
            imported = deepcopy(project.imports)
            scene = project.active_scene
            original = project._environment_source(scene)
            record = trigger_authoring_options(original, 'town01')['records'][0]
            values = dict(tile_x=(record['encoded']['tile_x'] + 1) % 256, tile_z=record['encoded']['tile_z'])
            proposed = review(project, record['trigger_id'], values)
            apply(project, dict(type='apply_trigger_cells', trigger_id=record['trigger_id'], values=values,
                                action='set', review_key=proposed['review_key']))
            region = region_authoring_options(original, 'town01')['records'][0]
            project.command(dict(type='set_region_bounds', entity_id=scene, value=dict(
                source_sha256=sha256(original).hexdigest(), edits=[dict(region_id=region['region_id'],
                **{key: region['encoded'][key] + (key == 'x0') for key in ('x0', 'z0', 'x1', 'z1')})])))
            project.command(dict(type='set_collision_walls', entity_id=scene, value=dict(
                source_sha256=sha256(original).hexdigest(), edits=[dict(row=1, column=0, quadrant=0,
                blocked=not bool(original[0x4080] & 16))])))
            project.command(dict(type='set_environment_transforms', entity_id=scene, value=dict(
                source_sha256=sha256(original).hexdigest(), edits=[dict(record_index=194, offset={'x':128})])))
            reopened = ProjectService.open(project.save())
            before = deepcopy(reopened._document())
            result = build_project(reopened)
            self.assertEqual(result['overlay_count'], 1)
            audit = json.loads(Path(result['audit']).read_text(encoding='utf-8'))
            overlay = audit['overlays'][0]
            changed = (Path(result['package_directory']) / overlay['file']).read_bytes()
            expected = sorted([194 * 32, 0x4080, record['byte_offset'], region['byte_offset']])
            self.assertEqual([i for i, (a, b) in enumerate(zip(original, changed)) if a != b], expected)
            self.assertEqual(len(changed), 0x12000)
            self.assertEqual(changed[record['byte_offset'] + 2:record['byte_offset'] + 4],
                             original[record['byte_offset'] + 2:record['byte_offset'] + 4])
            trigger_rows = [row for row in audit['edits'] if row['scope'] == 'source-MAP-trigger-cell-only']
            self.assertEqual(len(trigger_rows), 1)
            self.assertEqual(trigger_rows[0]['semantic_id'], record['trigger_id'])
            self.assertEqual(trigger_rows[0]['field'], 'trigger.tile_x')
            self.assertEqual(len(audit['edits']), 4)
            self.assertEqual(overlay['expected_sha256'], sha256(original).hexdigest())
            self.assertEqual(overlay['sha256'], sha256(changed).hexdigest())
            with zipfile.ZipFile(result['path']) as package:
                self.assertEqual(package.read(overlay['file']), changed)
            self.assertEqual(audit['validation']['live_runtime'], 'not_run')
            self.assertEqual(reopened._document(), before)
            self.assertEqual(reopened.imports, imported)
            self.assertIn('source trigger cells', package_change_kinds(audit['edits']))
