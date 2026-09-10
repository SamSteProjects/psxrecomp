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

    def test_transform_build_issues_use_serializer_constraints(self):
        with tempfile.TemporaryDirectory() as directory:
            project = ProjectService(Path(directory))
            project.import_metadata(synthetic_scene())
            actor = "scene://fixture/actors/man-p1/0001"
            def issues():
                return project.state()["scene"]["entities"][0]["components"]["Transform"]["build_issues"]
            self.assertEqual(issues(), [])
            project.command({"type": "set_transform", "entity_id": actor,
                             "position": {"x": 125, "y": 0}})
            self.assertEqual(len(issues()), 2)
            self.assertTrue(any("exact multiple of 64" in issue for issue in issues()))
            self.assertTrue(any("project-only" in issue for issue in issues()))
            project.undo()
            self.assertEqual(issues(), [])
            project.command({"type": "set_transform", "entity_id": actor,
                             "position": {"x": 64, "z": 16384}})
            self.assertEqual(issues(), [])

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

    def test_authored_templates_capture_apply_history_and_persist(self):
        with tempfile.TemporaryDirectory() as directory:
            project = ProjectService(Path(directory))
            metadata = synthetic_scene()
            second = deepcopy(metadata["actors"][0])
            second["semantic_id"] = "scene://fixture/actors/man-p1/0002"
            second["imported_transform"]["position"]["x"] = 500
            metadata["actors"].append(second)
            project.import_metadata(metadata)
            first_id, second_id = [actor["semantic_id"] for actor in metadata["actors"]]
            project.command({"type": "set_transform", "entity_id": first_id, "position": {"x": 128}})
            project.command({"type": "set_transform", "entity_id": second_id, "position": {"z": 256}})
            project.save()
            project.command({"type": "create_actor_template", "entity_id": first_id, "name": "Courtyard"})
            template_id = next(iter(project.actor_templates))
            template = deepcopy(project.actor_templates[template_id])
            self.assertEqual(template["components"], {"Transform": {"position": {"x": 128}}})
            self.assertEqual(template["source"]["entity_id"], first_id)
            self.assertTrue(project.dirty)
            project.undo()
            self.assertFalse(project.dirty)
            self.assertEqual(project.actor_templates, {})
            project.redo()
            project.command({"type": "set_transform", "entity_id": first_id, "position": {"x": 320}})
            self.assertEqual(project.actor_templates[template_id], template)
            project.command({"type": "apply_actor_template", "entity_id": second_id, "template_id": template_id})
            self.assertEqual(project.overrides[second_id]["Transform"]["position"], {"x": 128, "z": 256})
            target = project.state()["scene"]["entities"][1]["components"]["Transform"]
            self.assertEqual(target["imported"]["position"], {"x": 500, "y": None, "z": 200})
            self.assertEqual(target["effective"]["position"], {"x": 128, "y": None, "z": 256})
            project.undo()
            self.assertEqual(project.overrides[second_id]["Transform"]["position"], {"z": 256})
            project.redo()
            project.command({"type": "delete_actor_template", "template_id": template_id})
            self.assertEqual(project.actor_templates, {})
            project.undo()
            restored = ProjectService.open(project.save())
            self.assertEqual(restored.actor_templates, project.actor_templates)
            self.assertEqual(restored.overrides, project.overrides)
            self.assertEqual(restored.imports["scene://fixture"], metadata)
            self.assertFalse(restored.dirty)

    def test_template_failures_are_transactional_and_scope_checked_on_open(self):
        with tempfile.TemporaryDirectory() as directory:
            project = ProjectService(Path(directory))
            metadata = synthetic_scene()
            project.import_metadata(metadata)
            actor_id = metadata["actors"][0]["semantic_id"]
            with self.assertRaisesRegex(ProjectError, "Author one"):
                project.command({"type": "create_actor_template", "entity_id": actor_id, "name": "Empty"})
            self.assertEqual(project.actor_templates, {})
            project.command({"type": "set_transform", "entity_id": actor_id, "position": {"y": 8, "z": 128}})
            project.command({"type": "create_actor_template", "entity_id": actor_id, "name": "Project height"})
            identifier = next(iter(project.actor_templates))
            before = deepcopy(project.state())
            for command in ({"type": "create_actor_template", "entity_id": actor_id, "name": "project HEIGHT"},
                            {"type": "apply_actor_template", "entity_id": "missing", "template_id": identifier},
                            {"type": "delete_actor_template", "template_id": "missing"}):
                with self.assertRaises(ProjectError):
                    project.command(command)
                self.assertEqual(project.state(), before)
            project.mode = "live"
            with self.assertRaisesRegex(ProjectError, "Edit mode"):
                project.command({"type": "apply_actor_template", "entity_id": actor_id, "template_id": identifier})
            project.mode = "edit"
            path = project.save()
            original = json.loads(path.read_text())
            for mutation in ("other_disc", "model_component", "bad_position"):
                raw = deepcopy(original)
                template = raw["actor_templates"][identifier]
                if mutation == "other_disc":
                    template["source"]["disc_identity"] = "synthetic:other-disc"
                elif mutation == "model_component":
                    template["components"]["ModelRenderer"] = {"asset_id": "invented"}
                else:
                    template["components"]["Transform"]["position"]["x"] = True
                path.write_text(json.dumps(raw), encoding="utf-8")
                with self.assertRaises(ProjectError):
                    ProjectService.open(path)
            # Provenance remains useful even after the source instance is absent.
            raw = deepcopy(original)
            raw["actor_templates"][identifier]["source"]["entity_id"] = "scene://previous/actor"
            path.write_text(json.dumps(raw), encoding="utf-8")
            self.assertIn(identifier, ProjectService.open(path).actor_templates)


if __name__ == "__main__":
    unittest.main()
