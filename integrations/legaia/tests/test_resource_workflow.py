"""Derived resource discovery never becomes authored or imported project data."""
from copy import deepcopy
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from sdk.project import ProjectService, ProjectError
from sdk.resources import refresh_resource_catalog, texture_preview, field_map_preview, trigger_script_preview
from importer.core import ImportError as RetailImportError
from integrations.legaia.tests.test_project_workflow import synthetic_scene


class ResourceWorkflow(unittest.TestCase):
    def test_trigger_preview_rejects_changed_source_and_stays_private(self):
        with tempfile.TemporaryDirectory() as raw:
            project = ProjectService(Path(raw))
            document = synthetic_scene()
            project.import_metadata(document)
            project.disc_path = "synthetic"
            project.save()
            before = deepcopy(project._document())
            identifier = "trigger://fixture/field-map/fallback/kind-1/0000"
            report = {"trigger_id": identifier, "read_only": True, "partition": 2}
            with patch("sdk.resources._disc_context"), patch("sdk.resources.import_scene", return_value=document), \
                    patch("importer.trigger_scripts.inspect_trigger_script", return_value=report) as inspect, \
                    patch("sdk.resources.source_key", return_value="verified"):
                result = trigger_script_preview(project, identifier)
                inspect.assert_called_once_with("synthetic", "fixture", identifier)
            self.assertEqual(result["scene_id"], project.active_scene)
            self.assertEqual(result["source_key"], "verified")
            self.assertEqual(project._document(), before)
            self.assertFalse(project.dirty)
            self.assertFalse(project.assets.resource_catalogs)
            with patch("sdk.resources._disc_context"), patch("sdk.resources.import_scene", return_value=document), \
                    patch("importer.trigger_scripts.inspect_trigger_script", return_value=report), \
                    patch("sdk.resources.source_key", side_effect=["before", "after"]):
                with self.assertRaisesRegex(ProjectError, "source changed"):
                    trigger_script_preview(project, identifier)
            with patch("sdk.resources._disc_context"), patch("sdk.resources.import_scene", return_value={}), \
                    patch("sdk.resources.source_key", return_value="verified"), \
                    patch("importer.trigger_scripts.inspect_trigger_script") as inspect:
                with self.assertRaisesRegex(ProjectError, "freshly verified"):
                    trigger_script_preview(project, identifier)
                inspect.assert_not_called()

    def test_field_preview_rejects_changed_source_and_stays_private(self):
        with tempfile.TemporaryDirectory() as raw:
            project = ProjectService(Path(raw))
            document = synthetic_scene()
            project.import_metadata(document)
            project.disc_path = "synthetic"
            project.save()
            before = deepcopy(project._document())
            identifier = "collision://fixture/field-map"
            from importer.field_map import _decode
            from importer.core import ProtEntry
            catalog, _ = _decode("fixture", "a" * 64, ProtEntry(4, 100, 8, 36), bytes(0x12000), None)
            preview = {"asset": catalog["assets"][0], "coordinate_system": "psx_guest_xz",
                       "triggers": [], "regions": [],
                       "rectangles": [{"x_min": 0, "x_max": 64, "z_min": 0, "z_max": 64}]}
            with patch("sdk.resources._disc_context"), patch("sdk.resources.import_scene", return_value=document), \
                    patch("importer.field_map.preview_field_map", return_value=preview), \
                    patch("sdk.resources.source_key", return_value="verified"):
                result = field_map_preview(project, identifier)
            self.assertEqual(result["scene_id"], project.active_scene)
            self.assertEqual(result["source_key"], "verified")
            self.assertEqual(result["spatial"]["scene_id"], project.active_scene)
            self.assertEqual(result["spatial"]["records"], [])
            self.assertEqual(project._document(), before)
            self.assertFalse(project.dirty)
            self.assertFalse(project.assets.resource_catalogs)
            with patch("sdk.resources._disc_context"), patch("sdk.resources.import_scene", return_value=document), \
                    patch("importer.field_map.preview_field_map", return_value=preview), \
                    patch("sdk.resources.source_key", side_effect=["before", "after"]):
                with self.assertRaisesRegex(ProjectError, "source changed"):
                    field_map_preview(project, identifier)

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
                    patch("importer.animation_catalog.load_global_animation_asset_catalog", return_value={"assets": []}), \
                    patch("importer.worldmap_menu.load_worldmap_asset_catalog", return_value={"assets": []}), \
                    patch("importer.animation_catalog.load_animation_asset_catalog", return_value={"assets": []}), \
                    patch("importer.script_catalog.load_script_asset_catalog", side_effect=RetailImportError("unsupported MAN layout")), \
                    patch("importer.field_map.load_field_map_catalog", return_value={"assets": []}):
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
                    patch("importer.animation_catalog.load_global_animation_asset_catalog", return_value={"assets": []}), \
                    patch("importer.worldmap_menu.load_worldmap_asset_catalog", return_value={"assets": []}), \
                    patch("importer.animation_catalog.load_animation_asset_catalog", return_value={"assets": [animation]}), \
                    patch("importer.script_catalog.load_script_asset_catalog", return_value={"assets": [script, dialogue]}), \
                    patch("importer.field_map.load_field_map_catalog", return_value={"assets": []}):
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
