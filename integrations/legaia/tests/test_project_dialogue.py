"""Dialogue commands preserve source evidence and unrelated authored components."""
from copy import deepcopy
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from importer.core import ImportError
from sdk.project import ProjectService, ProjectError
from integrations.legaia.tests.test_project_workflow import synthetic_scene


class ProjectDialogue(unittest.TestCase):
    def test_partition_two_command_history_and_offline_persistence(self):
        with tempfile.TemporaryDirectory() as raw:
            p = ProjectService(Path(raw)); p.import_metadata(synthetic_scene())
            script = "scene://fixture/scripts/man-p2/0003"
            run = "script://fixture/scripts/man-p2/0003/dialogue/0010/run/0011"
            context = SimpleNamespace(options=lambda _: {"runs": [{"semantic_id": run}]}, patch=Mock())
            with patch.object(p, "_dialogue_context", return_value=context):
                p.command({"type": "set_dialogue_text", "entity_id": script, "run_id": run, "text": "Ready"})
            context.patch.assert_called_once_with({run: "Ready"})
            authored = deepcopy(p.overrides)
            p.undo(); self.assertEqual(p.overrides, {})
            p.redo(); self.assertEqual(p.overrides, authored)
            restored = ProjectService.open(p.save())
            self.assertEqual(restored.overrides, authored)
            restored.command({"type": "clear_dialogue_text", "entity_id": script, "run_id": run})
            self.assertEqual(restored.overrides, {})
            restored.undo(); self.assertEqual(restored.overrides, authored)
            with self.assertRaises(ProjectError):
                restored._dialogue_document("scene://missing/scripts/man-p2/0003")
            before = deepcopy(restored.overrides)
            with patch.object(restored, "_dialogue_context", side_effect=ImportError("record is aliased")):
                with self.assertRaisesRegex(ImportError, "aliased"):
                    restored.command({"type": "set_dialogue_text", "entity_id": script, "run_id": run, "text": "No"})
            self.assertEqual(restored.overrides, before)

    def test_text_command_history_clear_and_offline_reopen(self):
        with tempfile.TemporaryDirectory() as raw:
            p = ProjectService(Path(raw))
            original = synthetic_scene()
            p.import_metadata(original)
            actor = original["actors"][0]["semantic_id"]
            run = "script://fixture/actors/man-p1/0001/dialogue/0010/run/0011"
            context = SimpleNamespace(options=lambda _: {"supported": True, "runs": [
                {"semantic_id": run, "text": "Fixture text", "max_length": 12}]}, patch=Mock())
            p.command({"type": "set_transform", "entity_id": actor, "position": {"x": 128}})
            with patch.object(p, "_dialogue_context", return_value=context):
                p.command({"type": "set_dialogue_text", "entity_id": actor, "run_id": run, "text": "SDK text"})
                self.assertEqual(p.dialogue_options(actor)["runs"][0]["effective_text"], "SDK text    ")
            context.patch.assert_called_once_with({run: "SDK text"})
            authored = deepcopy(p.overrides)
            p.undo()
            self.assertNotIn("Dialogue", p.overrides[actor])
            self.assertEqual(p.overrides[actor]["Transform"]["position"], {"x": 128})
            p.redo()
            self.assertEqual(p.overrides, authored)
            restored = ProjectService.open(p.save())
            self.assertEqual(restored.overrides, authored)
            self.assertFalse(restored.dirty)
            restored.command({"type": "clear_dialogue_text", "entity_id": actor, "run_id": run})
            self.assertNotIn("Dialogue", restored.overrides[actor])
            self.assertEqual(restored.imports[restored.active_scene], original)
            restored.undo()
            self.assertEqual(restored.overrides, authored)

    def test_rejected_source_or_text_does_not_mutate_history_or_project(self):
        with tempfile.TemporaryDirectory() as raw:
            p = ProjectService(Path(raw)); p.import_metadata(synthetic_scene())
            actor = "scene://fixture/actors/man-p1/0001"
            run = "script://fixture/actors/man-p1/0001/dialogue/0010/run/0011"
            context = SimpleNamespace(options=lambda _: {"runs": [{"semantic_id": run}]},
                                      patch=Mock(side_effect=ImportError("source capacity exceeded")))
            before = deepcopy(p.state())
            with patch.object(p, "_dialogue_context", return_value=context):
                with self.assertRaisesRegex(ImportError, "capacity"):
                    p.command({"type": "set_dialogue_text", "entity_id": actor, "run_id": run, "text": "Too long"})
                for text in (None, 3, "New\nline", "Caret^", "\u2603"):
                    with self.assertRaises((ImportError, ProjectError)):
                        p.command({"type": "set_dialogue_text", "entity_id": actor, "run_id": run, "text": text})
            self.assertEqual(p.state(), before)
            self.assertEqual(p.undo_stack, [])
            self.assertEqual(p.redo_stack, [])
            p.mode = "live"
            with self.assertRaisesRegex(ProjectError, "Edit mode"):
                p.command({"type": "clear_dialogue_text", "entity_id": actor, "run_id": run})


if __name__ == "__main__":
    unittest.main()
