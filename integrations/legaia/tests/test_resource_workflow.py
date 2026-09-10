"""Derived resource discovery never becomes authored or imported project data."""
from copy import deepcopy
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from sdk.project import ProjectService, ProjectError
from sdk.resources import refresh_resource_catalog, texture_preview
from importer.core import ImportError as RetailImportError
from integrations.legaia.tests.test_project_workflow import synthetic_scene


class ResourceWorkflow(unittest.TestCase):
    def test_unsupported_script_catalog_retains_other_verified_resources(self):
        with tempfile.TemporaryDirectory() as raw:
            project = ProjectService(Path(raw))
            document = synthetic_scene()
            project.import_metadata(document)
            project.disc_path = "synthetic"
            project.save()
            texture = {"semantic_id": "texture://fixture/1/raw/0", "asset_kind": "texture"}
            with patch("sdk.resources.source_key", return_value="verified-key"), patch("sdk.resources._disc_context"), \
                    patch("sdk.resources.import_scene", return_value=document), \
                    patch("importer.texture_catalog.load_texture_asset_catalog", return_value={"assets": [texture]}), \
                    patch("importer.animation_catalog.load_animation_asset_catalog", return_value={"assets": []}), \
                    patch("importer.script_catalog.load_script_asset_catalog", side_effect=RetailImportError("unsupported MAN layout")):
                result = refresh_resource_catalog(project)
            self.assertEqual([row["id"] for row in result["records"]], [texture["semantic_id"]])
            self.assertIn("Scripts and dialogue unavailable: unsupported MAN layout", result["limitations"])
            self.assertFalse(project.dirty)

    def test_verified_registration_is_metadata_only_and_does_not_dirty_project(self):
        with tempfile.TemporaryDirectory() as raw:
            project = ProjectService(Path(raw))
            document = synthetic_scene()
            project.import_metadata(document)
            project.disc_path = "synthetic"
            project.save()
            before = deepcopy(project.state())
            texture = {"semantic_id": "texture://fixture/1/raw/0", "asset_kind": "texture", "source_record": {"fixture": True}}
            animation = {"semantic_id": "animation://fixture/scene-anm/0000", "asset_kind": "animation", "source_record": {"fixture": True}}
            script = {"semantic_id": "script://fixture/actors/man-p1/0001", "asset_kind": "script", "source_record": {"fixture": True}}
            dialogue = {"semantic_id": script["semantic_id"] + "/dialogue/0010", "asset_kind": "dialogue", "script_id": script["semantic_id"], "source_record": {"fixture": True}}
            with patch("sdk.resources.source_key", return_value="verified-key"), patch("sdk.resources._disc_context"), \
                    patch("sdk.resources.import_scene", return_value=document), \
                    patch("importer.texture_catalog.load_texture_asset_catalog", return_value={"assets": [texture]}), \
                    patch("importer.animation_catalog.load_animation_asset_catalog", return_value={"assets": [animation]}), \
                    patch("importer.script_catalog.load_script_asset_catalog", return_value={"assets": [script, dialogue]}):
                result = refresh_resource_catalog(project)
            self.assertEqual(len(result["records"]), 4)
            self.assertTrue(all(record["layer"] == "derived" for record in result["records"]))
            self.assertEqual(project.state(), before)
            self.assertEqual(project.imports[project.active_scene], document)
            self.assertFalse(project.dirty)
            result["records"].clear()
            self.assertEqual(len(project.assets.resource_catalogs[project.active_scene]["records"]), 4)

    def test_changed_source_rejects_before_texture_read_and_clears_previous_catalog(self):
        with tempfile.TemporaryDirectory() as raw:
            project = ProjectService(Path(raw))
            project.import_metadata(synthetic_scene())
            project.disc_path = "synthetic"
            project.assets.resource_catalogs[project.active_scene] = {"source_key": "old"}
            with patch("sdk.resources.source_key", return_value="key"), patch("sdk.resources._disc_context"), \
                    patch("sdk.resources.import_scene", return_value={}), \
                    patch("importer.texture_catalog.preview_texture_asset") as decode:
                with self.assertRaisesRegex(ProjectError, "freshly verified"):
                    refresh_resource_catalog(project)
                with self.assertRaisesRegex(ProjectError, "freshly verified"):
                    texture_preview(project, "texture://fixture/1/raw/0", 0)
            decode.assert_not_called()
            self.assertNotIn(project.active_scene, project.assets.resource_catalogs)


if __name__ == "__main__":
    unittest.main()
