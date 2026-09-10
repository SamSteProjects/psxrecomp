"""Transition project history and persistence, independent of retail payloads."""
from copy import deepcopy
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch
from sdk.project import ProjectService, ProjectError
from importer.core import ImportError
from integrations.legaia.tests.test_project_workflow import synthetic_scene

class ProjectTransitions(unittest.TestCase):
    def test_unavailable_transition_report_preserves_clearable_identity(self):
        from sdk.server import _transition_authoring_report
        from types import SimpleNamespace
        key = "script://fixture/scripts/man-p2/0000/transition/0016"
        owner = "scene://fixture/scripts/man-p2/0000"
        project = SimpleNamespace(transition_options=Mock(side_effect=ImportError("aliased record")),
                                  overrides={owner: {"Transitions": {"entries": {key: {"entry_x_encoded": 1}}}}})
        report = _transition_authoring_report(project, owner)
        self.assertFalse(report["supported"])
        self.assertEqual(report["transitions"], [])
        self.assertEqual(report["unresolved_overrides"], [key])
        self.assertEqual(report["reason"], "aliased record")

    def test_history_persistence_and_source_rejection(self):
        with tempfile.TemporaryDirectory() as directory:
            p = ProjectService(Path(directory)); p.import_metadata(synthetic_scene())
            owner = "scene://fixture/scripts/man-p2/0000"
            key = "script://fixture/scripts/man-p2/0000/transition/0016"
            command = dict(type="set_transition_entry", entity_id=owner, transition_id=key,
                           values={"entry_x_encoded": 23})
            context = Mock()
            with patch.object(p, "_transition_context", return_value=context):
                p.command(command)
            context.patch.assert_called_once_with({key: {"entry_x_encoded": 23}})
            authored = deepcopy(p.overrides)
            p.undo(); self.assertEqual(p.overrides, {})
            p.redo(); self.assertEqual(p.overrides, authored)
            self.assertEqual(p.authored_assets()[0]["changes"], ["Transitions: 1 entries"])
            restored = ProjectService.open(p.save())
            self.assertEqual(restored.overrides, authored)
            with patch.object(restored, "_transition_context", side_effect=ImportError("stale source")):
                with self.assertRaises(ImportError): restored.command(command)
            self.assertEqual(restored.overrides, authored)
            for values in ({}, {"direction_encoded": True}, {"entry_x_encoded": 256}, {"name": "town02"}):
                with self.assertRaises(ProjectError): restored.command(dict(command, values=values))
            self.assertEqual(restored.overrides, authored)
            restored.command(dict(type="clear_transition_entry", entity_id=owner, transition_id=key))
            self.assertEqual(restored.overrides, {})
            restored.undo(); self.assertEqual(restored.overrides, authored)

if __name__ == "__main__": unittest.main()
