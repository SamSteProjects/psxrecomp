"""Resource transition annotations stay fresh without changing scene geometry."""
from contextlib import ExitStack
from copy import deepcopy
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch

from importer.core import ImportError as RetailImportError
from sdk.project import ProjectService, ProjectError
from sdk.resources import refresh_resource_catalog, scene_transition_graph, scene_transition_state_key
from integrations.legaia.tests.test_importer_script_catalog import catalog
from integrations.legaia.tests.test_project_workflow import synthetic_scene


class TransitionResourceWorkflow(unittest.TestCase):
    def project(self, raw):
        project = ProjectService(Path(raw))
        project.import_metadata(synthetic_scene())
        project.disc_path = 'synthetic'
        project.save()
        return project

    def discovery(self, project, source, transition_context=None):
        stack = ExitStack()
        stack.enter_context(patch('sdk.resources._disc_context'))
        stack.enter_context(patch('sdk.resources.import_scene', return_value=project.imports[project.active_scene]))
        stack.enter_context(patch('sdk.resources.source_key', return_value='a' * 64))
        for name in ('texture_catalog.load_texture_asset_catalog', 'animation_catalog.load_animation_asset_catalog',
                     'animation_catalog.load_global_animation_asset_catalog', 'worldmap_menu.load_worldmap_asset_catalog',
                     'field_map.load_field_map_catalog', 'audio_catalog.load_audio_asset_catalog'):
            stack.enter_context(patch('importer.' + name, return_value={'assets': []}))
        stack.enter_context(patch('importer.script_catalog.load_script_asset_catalog', return_value=source))
        if transition_context is not None:
            stack.enter_context(patch('importer.transition_authoring.load_transition_authoring_context', return_value=transition_context))
        return stack

    def test_refresh_discovery_and_layers_are_detached_metadata_only(self):
        with tempfile.TemporaryDirectory() as raw:
            project = self.project(raw)
            source = catalog(b'\x3f\0\0\x06town02\x01\x82\x03')
            original = deepcopy(project._document())
            with self.discovery(project, source):
                initial = refresh_resource_catalog(project)
            asset = next(row for row in initial['records'] if row['kind'] == 'transition')
            self.assertEqual(asset['source'], project.active_scene)
            self.assertEqual(asset['arrival_layers']['imported']['x'], 192)
            self.assertEqual(asset['arrival_layers']['effective']['z'], 384)
            self.assertIsNone(asset['trigger_position'])
            self.assertFalse(asset['runtime_verified'])
            self.assertEqual(initial['transition_state_key'], scene_transition_state_key(project))
            self.assertEqual(project._document(), original)
            self.assertFalse(project.dirty)
            asset['entry_layers']['effective']['entry_x_encoded'] = 77
            cached = next(row for row in project.assets.resource_catalogs[project.active_scene]['records'] if row['kind'] == 'transition')
            self.assertEqual(cached['entry_layers']['effective']['entry_x_encoded'], 1)

    def test_authored_changes_have_separate_key_and_fresh_serializer_verification(self):
        with tempfile.TemporaryDirectory() as raw:
            project = self.project(raw)
            source = catalog(b'\x3f\0\0\x06town02\x01\x82\x03')
            initial_key = scene_transition_state_key(project)
            owner = 'scene://fixture/actors/man-p1/0001'
            key = 'script://fixture/actors/man-p1/0001/transition/0005'
            context = Mock()
            with patch.object(project, '_transition_context', return_value=context):
                project.command(dict(type='set_transition_entry', entity_id=owner, transition_id=key, values={'entry_x_encoded': 128}))
            authored_key = scene_transition_state_key(project)
            self.assertNotEqual(initial_key, authored_key)
            before = deepcopy(project._document())
            with self.discovery(project, source, context):
                result = refresh_resource_catalog(project)
                graph = scene_transition_graph(project)
            self.assertEqual(context.patch.call_count, 3)
            context.patch.assert_called_with({key: {'entry_x_encoded': 128}})
            asset = next(row for row in result['records'] if row['kind'] == 'transition')
            self.assertEqual(asset['arrival_layers']['effective']['x'], 128)
            self.assertEqual(graph['transition_state_key'], authored_key)
            self.assertEqual(project._document(), before)
            project.undo()
            self.assertEqual(scene_transition_state_key(project), initial_key)
            project.redo()
            self.assertEqual(scene_transition_state_key(project), authored_key)
            restored = ProjectService.open(project.save())
            self.assertEqual(scene_transition_state_key(restored), authored_key)
            context.patch.side_effect = RetailImportError('source preimage differs')
            with self.discovery(restored, source, context):
                with self.assertRaisesRegex(ProjectError, 'source verification'):
                    refresh_resource_catalog(restored)
            self.assertNotIn(restored.active_scene, restored.assets.resource_catalogs)

    def test_late_transition_annotation_change_rejects_refresh(self):
        with tempfile.TemporaryDirectory() as raw:
            project = self.project(raw)
            source = catalog(b'\x3f\0\0\x06town02\x01\x82\x03')
            key = scene_transition_state_key(project)
            with self.discovery(project, source), patch('sdk.resources.scene_transition_state_key', side_effect=[key, 'b' * 64]):
                with self.assertRaisesRegex(ProjectError, 'changed during discovery'):
                    refresh_resource_catalog(project)
            self.assertNotIn(project.active_scene, project.assets.resource_catalogs)


if __name__ == '__main__':
    unittest.main()
