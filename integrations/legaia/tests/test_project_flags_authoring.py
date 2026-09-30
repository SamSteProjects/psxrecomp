"""Source-qualified flag edits retain retail evidence and ordinary project history."""
from copy import deepcopy
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from sdk.project import ProjectService, ProjectError
from sdk.build import build_project, BuildError
from importer.core import ImportError
from test_importer_dialogue_authoring import fixture, ACTOR
from integrations.legaia.tests.test_project_workflow import synthetic_scene

class ProjectFlagsAuthoring(unittest.TestCase):
    def test_source_layers_history_persistence_and_atomic_rejection(self):
        source, _ = fixture(b'\x2e\xe2\x3f\0\0\x06town01\1\2\3opaque')
        with tempfile.TemporaryDirectory() as directory:
            project = ProjectService(Path(directory))
            project.import_metadata(synthetic_scene())
            imported = deepcopy(project.imports)
            with patch.object(project, '_dialogue_context', return_value=source):
                key = project.flag_options(ACTOR)['targets'][0]['semantic_id']
                command = dict(type='set_flag_bit', entity_id=ACTOR, flag_id=key, values={'bit':3})
                project.command(command)
                target = project.flag_options(ACTOR)['targets'][0]
                self.assertEqual(target['values'], {'bit':2})
                self.assertEqual(target['authored_values'], {'bit':3})
                self.assertEqual(target['effective_values'], {'bit':3})
                self.assertEqual(project.imports, imported)
                authored = deepcopy(project.overrides)
                count = len(project.undo_stack)
                project.command(command)
                self.assertEqual(len(project.undo_stack), count)
                for values in ({}, {'bit':True}, {'bit':32}, {'bit':3, 'extra':1}):
                    with self.assertRaises(ProjectError):project.command(dict(command, values=values))
                with self.assertRaises(ImportError):project.command(dict(command, flag_id=key[:-4]+'0001'))
                self.assertEqual(project.overrides, authored)
                self.assertEqual(len(project.undo_stack), count)
            self.assertEqual(project.authored_assets()[0]['changes'], ['Flags: 1 operands'])
            project.undo();self.assertEqual(project.overrides,{})
            project.redo();self.assertEqual(project.overrides,authored)
            restored = ProjectService.open(project.save())
            self.assertEqual(restored.overrides,authored)
            with patch.object(restored, '_dialogue_context', side_effect=ImportError('stale source')):
                with self.assertRaises(ImportError):restored.command(command)
            self.assertEqual(restored.overrides,authored)
            with self.assertRaisesRegex(BuildError,'verified user-owned retail disc'):build_project(restored)
            self.assertFalse((Path(directory)/'Builds').exists())
            restored.command(dict(type='clear_flag_bit', entity_id=ACTOR, flag_id=key))
            self.assertEqual(restored.overrides,{})
            restored.undo();self.assertEqual(restored.overrides,authored)

if __name__ == '__main__':unittest.main()
