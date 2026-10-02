"""Flag assets share verified catalogs while operand edits retain ordinary history."""
from contextlib import ExitStack, nullcontext
from copy import deepcopy
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from importer.flag_authoring import FlagAuthoringContext
from importer.script_catalog import _catalog
from sdk.asset_references import assemble, assemble_project
from sdk.project import ProjectError, ProjectService
from sdk.resources import (refresh_resource_catalog, scene_flag_index,
                           scene_flag_state_key, project_flag_index, project_flag_state_key)
from test_importer_dialogue_authoring import ACTOR, fixture
from test_project_workflow import synthetic_scene


class FlagAssetIntegration(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.project = ProjectService(Path(self.tmp.name))
        self.document = synthetic_scene()
        self.project.import_metadata(self.document)
        self.project.disc_path = 'synthetic'
        self.source, man = fixture(b'\x2e\xe2\x2f\xe2')
        self.catalog = _catalog(man, 'fixture', {'synthetic': True}, set())
        self.flags = FlagAuthoringContext(self.source)
        self.key = self.flags.options(ACTOR)['targets'][0]['semantic_id']
        self.stack = ExitStack()
        self.addCleanup(self.stack.close)
        for target, value in (
            ('sdk.resources._disc_context', nullcontext()),
            ('sdk.resources.import_scene', self.document),
            ('sdk.resources.source_key', 'a' * 64),
            ('importer.texture_catalog.load_texture_asset_catalog', {'assets': []}),
            ('importer.animation_catalog.load_animation_asset_catalog', {'assets': []}),
            ('importer.animation_catalog.load_global_animation_asset_catalog', {'assets': []}),
            ('importer.worldmap_menu.load_worldmap_asset_catalog', {'assets': []}),
            ('importer.field_map.load_field_map_catalog', {'assets': []}),
            ('importer.script_catalog.load_script_asset_catalog', self.catalog),
            ('importer.flag_authoring.load_flag_authoring_context', self.flags),
        ):
            self.stack.enter_context(patch(target, return_value=value))
        self.stack.enter_context(patch.object(self.project, '_dialogue_context', return_value=self.source))
        self.project.save()

    def edit(self):
        self.project.command(dict(type='set_flag_bit', entity_id=ACTOR, flag_id=self.key, values={'bit': 3}))

    def test_catalog_and_annotations_follow_history_without_changing_imported_identity(self):
        before = deepcopy((self.project._document(), self.project.undo_stack, self.project.redo_stack))
        retail = refresh_resource_catalog(self.project)
        self.assertEqual(before, (self.project._document(), self.project.undo_stack, self.project.redo_stack))
        self.assertFalse(self.project.dirty)
        group = next(row for row in retail['records'] if row['kind'] == 'flag')
        self.assertEqual([row['pc'] for row in group['references']], [5, 7])
        self.edit()
        authored = refresh_resource_catalog(self.project)
        effective = next(row for row in authored['records'] if row['kind'] == 'flag')
        self.assertEqual(effective['id'], group['id'])
        self.assertEqual([(r['retail_index'], r['authored_index'], r['effective_index'])
                          for r in effective['references']], [(2, 3, 3), (2, None, 2)])
        self.assertNotEqual(authored['flag_state_key'], retail['flag_state_key'])
        self.assertEqual(authored['source_key'], retail['source_key'])
        self.assertEqual(self.project.imports[self.project.active_scene], self.document)
        self.project.undo()
        self.assertEqual(refresh_resource_catalog(self.project), retail)
        self.project.redo()
        self.assertEqual(refresh_resource_catalog(self.project), authored)
        restored = ProjectService.open(self.project.save())
        self.assertEqual(scene_flag_state_key(restored), authored['flag_state_key'])
        self.assertEqual(restored.overrides, self.project.overrides)

    def test_scene_and_project_flags_reject_changed_annotations_and_catalog_is_cleared(self):
        catalog = refresh_resource_catalog(self.project)
        self.assertEqual(scene_flag_index(self.project)['flag_state_key'], catalog['flag_state_key'])
        self.edit()
        self.assertNotEqual(project_flag_state_key(self.project), project_flag_state_key(ProjectService(self.project.root)))
        with patch('sdk.resources._verify'):
            report = project_flag_index(self.project)
        self.assertEqual(report['source_key'], project_flag_state_key(self.project))
        self.assertEqual(report['authored_reference_count'], 1)
        with patch('sdk.resources.scene_flag_state_key', side_effect=['before', 'after']):
            with self.assertRaisesRegex(ProjectError, 'source changed'):
                refresh_resource_catalog(self.project)
        self.assertNotIn(self.project.active_scene, self.project.assets.resource_catalogs)
        with patch('sdk.resources.scene_flag_state_key', side_effect=['before', 'after']):
            with self.assertRaisesRegex(ProjectError, 'source changed'):
                scene_flag_index(self.project)

    def test_graph_keeps_individual_source_sites_and_separate_scene_membership(self):
        catalog = refresh_resource_catalog(self.project)
        group = next(row for row in catalog['records'] if row['kind'] == 'flag')
        report = assemble(self.project, catalog, group['id'])
        self.assertEqual(len(report['incoming']), 2)
        self.assertEqual([e['pc'] for e in report['incoming']], [5, 7])
        self.assertEqual({e['kind'] for e in report['incoming']}, {'script_flag_reference'})
        self.assertTrue(all(e['runtime_binding'] == 'not_asserted' and e['flag_reference_evidence']['index'] == 2
                            for e in report['incoming']))
        other = deepcopy(self.document)
        other['scene'] = {'semantic_id': 'scene://other', 'name': 'other'}
        for actor in other['actors']:
            actor['semantic_id'] = actor['semantic_id'].replace('fixture', 'other')
        self.project.import_metadata(other)
        self.project.active_scene = 'scene://fixture'
        other_catalog = deepcopy(catalog)
        other_catalog['scene_id'] = 'scene://other'
        for row in other_catalog['records']:
            for field in ('id', 'semantic_id', 'scene_id', 'owner_id', 'script_id', 'actor_semantic_id', 'owner_semantic_id'):
                if isinstance(row.get(field), str):
                    row[field] = row[field].replace('fixture', 'other')
            for ref in row.get('references', []):
                if isinstance(ref.get('flag_operand_id'), str):
                    ref['flag_operand_id'] = ref['flag_operand_id'].replace('fixture', 'other')
        result = assemble_project(self.project, {'scene://fixture': catalog, 'scene://other': other_catalog}, group['id'])
        root = next(node for node in result['nodes'] if node['id'] == group['id'])
        self.assertEqual(root['scene_ids'], ['scene://fixture'])
        self.assertEqual(root['navigable_scene_ids'], ['scene://fixture'])
        self.assertEqual(len(result['incoming']), 2)
        broken = deepcopy(catalog)
        broken['records'] = [row for row in broken['records'] if row['kind'] != 'script']
        with self.assertRaisesRegex(ProjectError, 'source script'):
            assemble(self.project, broken, group['id'])


if __name__ == '__main__':
    unittest.main()
