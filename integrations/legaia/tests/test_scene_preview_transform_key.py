"""Actor placement refreshes instance identity without decoding geometry again."""
from contextlib import nullcontext
from copy import deepcopy
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from sdk.project import ProjectService
from sdk.scene_preview import ScenePreviewService, preview_project, source_key
from test_project_workflow import synthetic_scene
from test_scene_preview import geometry


class ScenePreviewTransformKeyTests(unittest.TestCase):
    def project(self, root):
        document = synthetic_scene()
        document['actors'][0]['placement_fields']['animation_id'] = 0
        project = ProjectService(Path(root))
        project.import_metadata(document)
        disc = Path(root) / 'fixture.bin'
        disc.write_bytes(b'synthetic source')
        project.disc_path = str(disc)
        return project, document, document['actors'][0]['semantic_id']

    def test_each_axis_clear_undo_redo_refreshes_only_instance_identity(self):
        with tempfile.TemporaryDirectory() as root:
            project, _, actor = self.project(root)
            with patch('sdk.scene_preview.resolve_disc_path', side_effect=lambda path: path), \
                 patch('sdk.scene_preview._disc_stamp', return_value=('synthetic', 1)):
                baseline = source_key(project)
                geometry_key = source_key(project, geometry_only=True)
                for axis, value in (('x', 164), ('z', 264), ('y', -30)):
                    with self.subTest(axis=axis):
                        project.command(dict(type='set_transform', entity_id=actor, position={axis: value}))
                        edited = source_key(project)
                        self.assertNotEqual(edited, baseline)
                        self.assertEqual(source_key(project, geometry_only=True), geometry_key)
                        project.undo()
                        self.assertEqual(source_key(project), baseline)
                        project.redo()
                        self.assertEqual(source_key(project), edited)
                        project.command(dict(type='clear_transform', entity_id=actor, axes=[axis]))
                        self.assertEqual(source_key(project), baseline)
                        self.assertEqual(source_key(project, geometry_only=True), geometry_key)

    def test_only_imported_active_scene_actor_transform_bindings_invalidate(self):
        with tempfile.TemporaryDirectory() as root:
            project, document, actor = self.project(root)
            other = deepcopy(document)
            other['scene'].update(semantic_id='scene://other', name='other')
            other['actors'][0]['semantic_id'] = 'scene://other/actors/man-p1/0001'
            project.import_metadata(other)
            project.set_scene(document['scene']['semantic_id'])
            baseline = source_key(project)
            geometry_key = source_key(project, geometry_only=True)
            project.command(dict(type='set_transform', entity_id=other['actors'][0]['semantic_id'], position={'x': 164}))
            project.overrides['unrelated-unimported-actor'] = {'Transform': {'position': {'x': 999}}}
            self.assertEqual(source_key(project), baseline)
            project.overrides[actor] = {'ScriptWaits': {'sentinel': True}}
            self.assertEqual(source_key(project), baseline)
            project.command(dict(type='set_transform', entity_id=actor, position={'z': 264}))
            self.assertNotEqual(source_key(project), baseline)
            self.assertEqual(source_key(project, geometry_only=True), geometry_key)
            self.assertEqual(project.imports[project.active_scene], document)

    def test_authored_and_retail_preview_keys_bind_refreshed_positions_with_cached_geometry(self):
        with tempfile.TemporaryDirectory() as root:
            project, document, actor = self.project(root)
            service = ScenePreviewService()
            calls = []
            def loader(asset):
                calls.append(asset['id'])
                return geometry()
            with patch('sdk.scene_preview._disc_context', side_effect=lambda _: nullcontext()), \
                 patch('sdk.scene_preview.import_scene', return_value=deepcopy(document)):
                baseline = service.preview(project, loader)
                project.command(dict(type='set_transform', entity_id=actor, position={'x': 164, 'z': 264, 'y': -30}))
                before = deepcopy(project._document()), deepcopy(project.undo_stack)
                authored = service.preview(project, loader)
                retail_view = preview_project(project, 'retail')
                retail = service.preview(retail_view, loader)
                self.assertNotEqual(authored['source_key'], baseline['source_key'])
                self.assertEqual(authored['source_key'], source_key(project))
                self.assertEqual(retail['source_key'], baseline['source_key'])
                self.assertEqual(retail['source_key'], source_key(retail_view))
                self.assertEqual(authored['entities'][0]['preview_position'], {'x': 164, 'y': -30, 'z': 264})
                self.assertEqual(authored['entities'][0]['model_to_scene'][3:12:4], [164, 30, 264])
                self.assertEqual(retail['entities'][0]['preview_position'], {'x': 100, 'y': None, 'z': 200})
                self.assertEqual(len(calls), 1)
                self.assertEqual((project._document(), project.undo_stack), before)
                project.undo()
                restored = service.preview(project, loader)
                self.assertEqual(restored['source_key'], baseline['source_key'])
                self.assertEqual(restored['entities'], baseline['entities'])
                project.redo()
                redone = service.preview(project, loader)
                self.assertEqual(redone['source_key'], authored['source_key'])
                self.assertEqual(redone['entities'], authored['entities'])
                self.assertEqual(len(calls), 1)

    def test_unknown_height_resamples_source_surface_after_x_edit(self):
        with tempfile.TemporaryDirectory() as root:
            project, document, actor = self.project(root)
            ground = dict(vertices=[[0, -10, 128], [128, -10, 128], [0, -10, 256], [128, -10, 256],
                                    [128, -30, 128], [256, -30, 128], [128, -30, 256], [256, -30, 256]],
                          triangles=[[0, 1, 2], [1, 3, 2], [4, 5, 6], [5, 7, 6]],
                          cells=[dict(cell_index=128, vertex_start=0), dict(cell_index=129, vertex_start=4)],
                          textures=[], source_record={'fixture': True}, limitations=['Source preview only'])
            service = ScenePreviewService()
            with patch('sdk.scene_preview._disc_context', side_effect=lambda _: nullcontext()), \
                 patch('sdk.scene_preview.import_scene', return_value=deepcopy(document)):
                baseline = service.preview(project, lambda *_: geometry(), terrain_loader=lambda _: ground)
                project.command(dict(type='set_transform', entity_id=actor, position={'x': 164}))
                moved = service.preview(project, lambda *_: self.fail('actor geometry rebuilt'),
                                        terrain_loader=lambda _: self.fail('terrain rebuilt'))
                self.assertNotEqual(moved['source_key'], baseline['source_key'])
                self.assertIsNone(moved['entities'][0]['position']['y'])
                self.assertEqual(baseline['entities'][0]['preview_position']['y'], -10)
                self.assertEqual(moved['entities'][0]['preview_position']['y'], -30)
                self.assertEqual(moved['entities'][0]['preview_ground_sample']['cell_index'], 129)
                self.assertEqual(moved['entities'][0]['preview_height_status'], 'source_surface')
                self.assertEqual(moved['assets'], baseline['assets'])


if __name__ == '__main__':
    unittest.main()
