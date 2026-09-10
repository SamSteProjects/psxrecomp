"""Authored TIM file integrity, history and separation from retail metadata."""
from copy import deepcopy
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch

from integrations.legaia.tests.test_project_workflow import synthetic_scene
from sdk.project import ProjectService, ProjectError


class ProjectTextures(unittest.TestCase):
    def test_content_reference_history_offline_reopen_and_tamper_rejection(self):
        with tempfile.TemporaryDirectory() as raw:
            project = ProjectService(Path(raw))
            source = synthetic_scene()
            project.import_metadata(source)
            actor = source["actors"][0]["semantic_id"]
            project.command({"type": "set_transform", "entity_id": actor, "position": {"x": 128}})
            actor_edits = deepcopy(project.overrides)
            identifier = "texture://fixture/1/raw/0"
            content = b"authored fixture bytes"
            with patch.object(project, "_texture_context", return_value=Mock()):
                project.set_texture_replacement(identifier, content)
            binding = deepcopy(project.texture_overrides[identifier])
            self.assertEqual(project.read_texture_replacement(binding), content)
            project.undo()
            self.assertEqual(project.texture_overrides, {})
            self.assertEqual(project.overrides, actor_edits)
            project.redo()
            reopened = ProjectService.open(project.save())
            self.assertEqual(reopened.texture_overrides, project.texture_overrides)
            self.assertFalse(reopened.dirty)
            reopened.command({"type": "clear_texture_replacement", "asset_id": identifier})
            self.assertEqual(reopened.texture_overrides, {})
            reopened.undo()
            self.assertEqual(reopened.read_texture_replacement(binding), content)
            self.assertEqual(reopened.imports[reopened.active_scene], source)
            path = Path(raw) / "Authored" / "Textures" / (binding["asset_sha256"] + ".tim")
            path.write_bytes(b"x" * len(content))
            with self.assertRaisesRegex(ProjectError, "digest"):
                reopened.save()
            with self.assertRaisesRegex(ProjectError, "digest"):
                ProjectService.open(Path(raw))
            from sdk.scene_preview import ScenePreviewService
            cached = ScenePreviewService()
            cached._key = "previously verified"
            with self.assertRaisesRegex(ProjectError, "digest"):
                cached.preview(reopened, Mock())

    def test_invalid_replacement_does_not_write_or_change_history(self):
        with tempfile.TemporaryDirectory() as raw:
            project = ProjectService(Path(raw))
            project.import_metadata(synthetic_scene())
            before = deepcopy(project.state())
            context = Mock()
            context.validate_replacement.side_effect = ProjectError("source layout mismatch")
            with patch.object(project, "_texture_context", return_value=context):
                with self.assertRaisesRegex(ProjectError, "layout"):
                    project.set_texture_replacement("texture://fixture/1/raw/0", b"fixture")
            self.assertEqual(project.state(), before)
            self.assertFalse((Path(raw) / "Authored").exists())
            project.mode = "live"
            with self.assertRaisesRegex(ProjectError, "Edit"):
                project.set_texture_replacement("texture://fixture/1/raw/0", b"fixture")


if __name__ == "__main__":
    unittest.main()
