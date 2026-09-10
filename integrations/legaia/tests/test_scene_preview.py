"""Scene geometry ownership, source invalidation and authored transform checks."""
from contextlib import nullcontext
from copy import deepcopy
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from sdk.project import ProjectError, ProjectService
from sdk.scene_preview import ScenePreviewService, source_key
from integrations.legaia.tests.test_project_workflow import synthetic_scene


def geometry():
    return {"vertices": [[0, 0, 0], [10, -20, 0], [10, 0, 5]],
            "triangles": [[0, 1, 2]], "objects": [{"object_index": 0}],
            "textures": [], "materials": []}


class ScenePreviewWorkflow(unittest.TestCase):
    def test_cached_geometry_tracks_edits_undo_and_does_not_mutate_imports(self):
        with tempfile.TemporaryDirectory() as directory:
            project = ProjectService(Path(directory))
            imported = synthetic_scene()
            imported["actors"][0]["placement_fields"]["animation_id"] = 0
            project.import_metadata(imported)
            disc = Path(directory) / "fixture.bin"
            disc.write_bytes(b"synthetic source")
            project.disc_path = str(disc)
            actor = imported["actors"][0]["semantic_id"]
            calls = []
            def loader(asset):
                calls.append(asset["id"])
                return geometry()
            service = ScenePreviewService()
            with patch("sdk.scene_preview._disc_context", side_effect=lambda _: nullcontext()), \
                 patch("sdk.scene_preview.import_scene", return_value=deepcopy(imported)):
                first = service.preview(project, loader)
                self.assertEqual(first["metrics"]["renderable_count"], 1)
                self.assertIsNone(first["entities"][0]["position"]["y"])
                self.assertEqual(first["entities"][0]["display_position"]["y"], 0)
                key = first["source_key"]
                # A caller cannot corrupt the service's cached geometry.
                first["assets"][0]["preview"]["vertices"][0][0] = 123456
                project.command({"type": "set_transform", "entity_id": actor, "position": {"x": 500, "y": -30}})
                moved = service.preview(project, loader)
                self.assertEqual(key, moved["source_key"])
                self.assertEqual(len(calls), 1)
                self.assertEqual(moved["entities"][0]["model_to_scene"][3:12:4], [500, 30, 200])
                self.assertEqual(moved["assets"][0]["preview"]["vertices"][0][0], 0)
                project.undo()
                reverted = service.preview(project, loader)
                self.assertEqual(reverted["entities"][0]["position"], {"x": 100, "y": None, "z": 200})
                self.assertEqual(project.imports[project.active_scene], imported)
                # A new on-disk source requires regeneration even with unchanged metadata.
                disc.write_bytes(b"a changed synthetic source")
                self.assertNotEqual(source_key(project), key)
                service.preview(project, loader)
                self.assertEqual(len(calls), 2)

    def test_wrong_evidence_rejects_and_unknown_multipart_stays_a_marker(self):
        with tempfile.TemporaryDirectory() as directory:
            project = ProjectService(Path(directory))
            imported = synthetic_scene()
            imported["actors"][0]["placement_fields"]["animation_id"] = 0
            project.import_metadata(imported)
            disc = Path(directory) / "fixture.bin"
            disc.write_bytes(b"synthetic")
            project.disc_path = str(disc)
            service = ScenePreviewService()
            multi = geometry()
            multi["objects"].append({"object_index": 1})
            with patch("sdk.scene_preview._disc_context", side_effect=lambda _: nullcontext()), \
                 patch("sdk.scene_preview.import_scene", return_value=deepcopy(imported)) as fresh:
                result = service.preview(project, lambda _: deepcopy(multi))
                self.assertFalse(result["entities"][0]["renderable"])
                self.assertIn("Multipart", result["entities"][0]["reason"])
                self.assertEqual(result["assets"], [])
                disc.write_bytes(b"changed source")
                fresh.return_value = {"wrong": "source"}
                with self.assertRaisesRegex(ProjectError, "evidence differs"):
                    service.preview(project, lambda _: geometry())
                self.assertIsNone(service._key)
                self.assertEqual(service._assets, [])


if __name__ == "__main__":
    unittest.main()
