"""Dialogue commands preserve source evidence and unrelated authored components."""
from copy import deepcopy
import json
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
    def test_menu_label_commands_use_verified_spans_history_and_persistence(self):
        from test_importer_dialogue_authoring import fixture, literals
        from importer.dialogue_authoring import DialogueAuthoringContext
        script=b"\x1fQ\0\x27\x0d\0\x0b\0\x1fYes\0\x1fNo\0\x4c\xff"
        for partition in (1,2):
            context,original=fixture(script)
            identifier="scene://fixture/actors/man-p1/0001"
            if partition==2:
                identifier="scene://fixture/scripts/man-p2/0000"
                region=0x2b+12
                section=int.from_bytes(original[0x28:0x2b],'little')
                record=bytes(4)+script
                man=bytearray(original[:region+section]+record+original[region+section:])
                man[0x34:0x37]=section.to_bytes(3,'little')
                man[0x28:0x2b]=(section+len(record)).to_bytes(3,'little')
                original=bytes(man)
                context=DialogueAuthoringContext('fixture',original,literals(original),{})
            run=context.options(identifier)['runs'][0]
            with tempfile.TemporaryDirectory() as directory:
                project=ProjectService(Path(directory));project.import_metadata(synthetic_scene())
                with patch.object(project,'_dialogue_context',return_value=context):
                    project.command(dict(type='set_dialogue_text',entity_id=identifier,run_id=run['semantic_id'],text='OK'))
                    self.assertEqual(project.dialogue_options(identifier)['runs'][0]['effective_text'],'OK ')
                authored=deepcopy(project.overrides)
                project.undo();self.assertEqual(project.overrides,{})
                project.redo();self.assertEqual(project.overrides,authored)
                restored=ProjectService.open(project.save())
                self.assertEqual(restored.overrides,authored)
                restored.command(dict(type='clear_dialogue_text',entity_id=identifier,run_id=run['semantic_id']))
                self.assertEqual(restored.overrides,{})
                restored.undo();self.assertEqual(restored.overrides,authored)

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
            p.import_metadata(json.loads(json.dumps(synthetic_scene()).replace("fixture", "second")))
            catalog = p.authored_assets()
            self.assertEqual(catalog[0]["scene_id"], "scene://fixture")
            self.assertEqual(catalog[0]["kind"], "script")
            self.assertEqual(catalog[0]["id"], script)
            catalog[0]["authored"].clear()
            self.assertEqual(p.overrides, authored)
            restored = ProjectService.open(p.save())
            self.assertEqual(restored.overrides, authored)
            self.assertEqual(restored.authored_assets(), p.authored_assets())
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
