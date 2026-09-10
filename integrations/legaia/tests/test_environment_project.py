from hashlib import sha256
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from sdk.project import ProjectService
from sdk.scene_preview import environment_effective_transforms
from importer.core import ImportError
from integrations.legaia.tests.test_project_workflow import synthetic_scene


class EnvironmentProjectTests(unittest.TestCase):
    def test_shared_preview_offsets_keep_source_and_reverse_z(self):
        with tempfile.TemporaryDirectory() as directory:
            project = ProjectService(Path(directory))
            project.import_metadata(synthetic_scene())
            data = bytes(0x12000)
            value = {'source_sha256':sha256(data).hexdigest(),
                     'edits':[{'record_index':0, 'offset':{'x':10,'z':20}, 'rotation_psx':{'y':1024}}]}
            project.overrides['scene://fixture'] = {'Environment':value}
            metadata = {'source_record':{'map_sha256':value['source_sha256']}, 'placements':[
                {'semantic_id':str(i), 'object_record_index':0,
                 'imported_transform':{'position':dict(x=i*128,y=-64,z=500), 'rotation_psx':dict(x=0,y=0,z=0)}}
                for i in range(2)]}
            with patch.object(project, '_environment_source', return_value=data):
                effective = environment_effective_transforms(project, metadata)
            self.assertEqual(effective['1']['position'], dict(x=138,y=-64,z=480))
            self.assertEqual(effective['0']['rotation_psx']['y'], 1024)
            self.assertEqual(metadata['placements'][1]['imported_transform']['position']['x'],128)

    def test_save_reopen_undo_clear_and_stale_rejection(self):
        with tempfile.TemporaryDirectory() as directory:
            project = ProjectService(Path(directory))
            project.import_metadata(synthetic_scene())
            project.save()
            data = bytes(0x12000)
            value = {'source_sha256':sha256(data).hexdigest(),
                     'edits':[{'record_index':0, 'offset':{'x':123}}]}
            with patch.object(project, '_environment_source', return_value=data):
                project.command({'type':'set_environment_transforms', 'entity_id':'scene://fixture', 'value':value})
                self.assertTrue(project.dirty)
                project.undo()
                self.assertFalse(project.dirty)
                project.redo()
                saved = project.save()
                reopened = ProjectService.open(saved)
                self.assertEqual(reopened.overrides, project.overrides)
                self.assertFalse(reopened.dirty)
                authored = reopened.authored_assets()
                self.assertEqual(len(authored), 1)
                self.assertEqual(authored[0]['kind'], 'scene')
                self.assertEqual(authored[0]['authored']['Environment'], value)
                with self.assertRaises(ImportError):
                    project.command({'type':'set_environment_transforms', 'entity_id':'scene://fixture',
                                     'value':dict(value, source_sha256='0'*64)})
                self.assertEqual(reopened.overrides, project.overrides)
                reopened.command({'type':'clear_environment_transforms', 'entity_id':'scene://fixture'})
                self.assertEqual(reopened.overrides, {})
                reopened.undo()
                self.assertEqual(reopened.overrides, project.overrides)


if __name__ == '__main__':
    unittest.main()
