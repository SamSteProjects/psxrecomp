"""Project-wide authored discovery stays independent of the active scene/cache."""
from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch

from integrations.legaia.tests.test_project_workflow import synthetic_scene
from sdk.project import ProjectService


class AuthoredAssetCatalog(unittest.TestCase):
    def test_cross_scene_history_persistence_and_snapshot_isolation(self):
        with tempfile.TemporaryDirectory() as directory:
            project = ProjectService(Path(directory))
            first = synthetic_scene()
            second = json.loads(json.dumps(first).replace('fixture', 'second'))
            project.import_metadata(first)
            actor = first['actors'][0]['semantic_id']
            project.command({'type': 'set_transform', 'entity_id': actor, 'position': {'x': 128}})
            project.command({'type': 'create_actor_template', 'entity_id': actor, 'name': 'Courtyard'})
            with patch.object(project, '_texture_context', return_value=Mock()):
                project.set_texture_replacement('texture://fixture/1/raw/0', b'private fixture')
            project.import_metadata(second)
            before = deepcopy(project._document())
            records = project.state()['authored_assets']
            self.assertEqual({row['kind'] for row in records}, {'actor', 'texture', 'template'})
            self.assertTrue(all(row['scene_id'] == 'scene://fixture' for row in records))
            self.assertEqual(len({row['id'] for row in records}), 3)
            self.assertFalse(project.assets.resource_catalogs)
            records[0]['authored'].clear()
            self.assertEqual(project._document(), before)
            restored = ProjectService.open(project.save())
            self.assertEqual(restored.authored_assets(), project.authored_assets())
            restored.command({'type': 'clear_texture_replacement', 'asset_id': 'texture://fixture/1/raw/0'})
            self.assertEqual(len(restored.authored_assets()), 2)
            restored.undo()
            self.assertEqual(restored.authored_assets(), project.authored_assets())


if __name__ == '__main__':
    unittest.main()
