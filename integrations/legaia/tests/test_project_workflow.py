"""Small synthetic acceptance checks for the connected authoring workflow."""
from copy import deepcopy
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from sdk.project import ProjectError, ProjectService


def synthetic_scene():
    return {"source": {"disc_identity": "synthetic:test-disc"},
            "scene": {"semantic_id": "scene://fixture", "name": "fixture"},
            "actors": [{"semantic_id": "scene://fixture/actors/man-p1/0001",
                        "imported_transform": {"position": {"x": 100, "y": None, "z": 200}, "rotation": None},
                        "model_reference": {"asset_semantic_id": "asset://fixture/model/0", "resolution_status": "resolved"},
                        "placement_fields": {"animation_id": 2}, "source_record": {"fixture": True},
                        "claims": [], "unresolved": ["position.y", "rotation"]}],
            "assets": {"models": [{"semantic_id": "asset://fixture/model/0", "source_record": {"fixture": True}}]}}


class ProjectWorkflow(unittest.TestCase):
    def test_edit_undo_save_reopen_preserves_imported_evidence(self):
        with tempfile.TemporaryDirectory() as directory:
            project = ProjectService(Path(directory))
            original = synthetic_scene()
            project.import_metadata(original)
            actor_id = original["actors"][0]["semantic_id"]
            project.save()
            project.command({"type": "set_transform", "entity_id": actor_id, "position": {"x": 125}})
            self.assertTrue(project.dirty)
            transform = project.state()["scene"]["entities"][0]["components"]["Transform"]
            self.assertEqual(transform["imported"]["position"], {"x": 100, "y": None, "z": 200})
            self.assertEqual(transform["effective"]["position"], {"x": 125, "y": None, "z": 200})
            project.undo()
            self.assertFalse(project.dirty)
            project.redo()
            path = project.save()
            restored = ProjectService.open(path)
            self.assertEqual(restored.overrides, project.overrides)
            self.assertEqual(restored.imports["scene://fixture"], original)
            self.assertFalse(restored.dirty)

    def test_corrupt_evidence_and_escaping_import_are_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            project = ProjectService(Path(directory))
            project.import_metadata(synthetic_scene())
            path = project.save()
            imported = next((Path(directory) / "Imported").glob("*.json"))
            imported.write_text("{}", encoding="utf-8")
            with self.assertRaisesRegex(ProjectError, "digest"):
                ProjectService.open(path)
            with self.assertRaisesRegex(ProjectError, "modified"):
                project.save()
            raw = json.loads(path.read_text())
            raw["imports"][0]["file"] = "../outside.json"
            path.write_text(json.dumps(raw))
            with self.assertRaisesRegex(ProjectError, "reference"):
                ProjectService.open(path)

    def test_failed_authoring_and_reimport_do_not_change_project(self):
        with tempfile.TemporaryDirectory() as directory:
            project = ProjectService(Path(directory))
            metadata = synthetic_scene()
            project.import_metadata(metadata)
            actor_id = metadata["actors"][0]["semantic_id"]
            for invalid in (True, float("nan"), "42", 1e9):
                with self.assertRaises(ProjectError):
                    project.command({"type": "set_transform", "entity_id": actor_id, "position": {"x": invalid}})
            self.assertEqual(project.overrides, {})
            project.command({"type": "set_transform", "entity_id": actor_id, "position": {"x": 125}})
            before = deepcopy(project.state())
            changed = deepcopy(metadata)
            changed["actors"][0]["imported_transform"]["position"]["x"] = 400
            with self.assertRaisesRegex(ProjectError, "evidence changed"):
                project.import_metadata(changed)
            self.assertEqual(project.state(), before)


if __name__ == "__main__":
    unittest.main()
