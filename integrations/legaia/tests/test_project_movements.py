"""Movement project history and persistence, independent of retail payloads."""
from copy import deepcopy
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch
from sdk.project import ProjectService, ProjectError
from importer.core import ImportError
from integrations.legaia.tests.test_project_workflow import synthetic_scene

class ProjectMovements(unittest.TestCase):
    def test_real_serializer_layers_and_missing_disc_boundary(self):
        from test_importer_dialogue_authoring import fixture, ACTOR
        from sdk.build import build_project, BuildError
        source,_=fixture(b'\x23\x00\x80\x3f\0\0\x06town01\1\2\3')
        with tempfile.TemporaryDirectory() as directory:
            p=ProjectService(Path(directory));p.import_metadata(synthetic_scene())
            before=deepcopy(p.imports)
            with patch.object(p,'_dialogue_context',return_value=source):
                target=p.movement_options(ACTOR)['targets'][0]
                p.command({'type':'set_movement_target','entity_id':ACTOR,'movement_id':target['semantic_id'],'values':{'x':128}})
                result=p.movement_options(ACTOR)['targets'][0]
            self.assertEqual(result['values'],{'x':64,'z':128})
            self.assertEqual(result['effective_values'],{'x':128,'z':128})
            self.assertEqual(result['authored_values'],{'x':128})
            self.assertEqual(p.imports,before)
            with self.assertRaisesRegex(BuildError,'verified user-owned retail disc'):
                build_project(p)
            self.assertFalse((Path(directory)/'Builds').exists())

    def test_history_persistence_and_source_rejection(self):
        with tempfile.TemporaryDirectory() as directory:
            p = ProjectService(Path(directory)); p.import_metadata(synthetic_scene())
            owner = "scene://fixture/scripts/man-p2/0000"
            key = "script://fixture/scripts/man-p2/0000/movement/0016"
            command = dict(type="set_movement_target", entity_id=owner, movement_id=key,
                           values={"x": 128})
            context = Mock()
            with patch.object(p, "_movement_context", return_value=context):
                p.command(command)
            context.patch.assert_called_once_with({key: {"x": 128}})
            authored = deepcopy(p.overrides)
            p.undo(); self.assertEqual(p.overrides, {})
            p.redo(); self.assertEqual(p.overrides, authored)
            self.assertEqual(p.authored_assets()[0]["changes"], ["Movement: 1 targets"])
            restored = ProjectService.open(p.save())
            self.assertEqual(restored.overrides, authored)
            with patch.object(restored, "_movement_context", side_effect=ImportError("stale source")):
                with self.assertRaises(ImportError): restored.command(command)
            self.assertEqual(restored.overrides, authored)
            for values in ({}, {"x": True}, {"x": 65}, {"name": "town02"}):
                with self.assertRaises(ProjectError): restored.command(dict(command, values=values))
            self.assertEqual(restored.overrides, authored)
            restored.command(dict(type="clear_movement_target", entity_id=owner, movement_id=key))
            self.assertEqual(restored.overrides, {})
            restored.undo(); self.assertEqual(restored.overrides, authored)

if __name__ == "__main__": unittest.main()
