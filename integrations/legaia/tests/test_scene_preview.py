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
from sdk.scene_preview import ScenePreviewService, source_key, environment_matrix
from integrations.legaia.tests.test_project_workflow import synthetic_scene


def geometry():
    return {"vertices": [[0, 0, 0], [10, -20, 0], [10, 0, 5]],
            "triangles": [[0, 1, 2]], "objects": [{"object_index": 0}],
            "textures": [], "materials": []}


class ScenePreviewWorkflow(unittest.TestCase):
    def test_environment_matrix_rotates_before_single_y_reflection(self):
        matrix = environment_matrix({"position": {"x": 10, "y": -20, "z": 30},
                                     "rotation_psx": {"x": 0, "y": 1024, "z": 0}})
        # Source +Z becomes world +X for a quarter yaw; translation is last.
        self.assertAlmostEqual(matrix[2] + matrix[3], 11)
        self.assertAlmostEqual(matrix[6] + matrix[7], 20)
        self.assertAlmostEqual(matrix[10] + matrix[11], 30)
        self.assertEqual(matrix[5], -1)

    def test_donor_pose_keeps_target_placement_and_invalidates_only_appearance(self):
        with tempfile.TemporaryDirectory() as directory:
            project = ProjectService(Path(directory))
            imported = synthetic_scene()
            target = imported["actors"][0]
            target["placement_fields"]["animation_id"] = 0
            donor = deepcopy(target)
            donor["semantic_id"] = target["semantic_id"].rsplit("/", 1)[0] + "/0002"
            donor["source_record"] = {"fixture": "donor"}
            donor["placement_fields"]["animation_id"] = 7
            donor["model_reference"]["asset_semantic_id"] = "asset://fixture/model/1"
            donor["imported_transform"]["position"]["x"] = 900
            imported["actors"].append(donor)
            imported["assets"]["models"].append({"semantic_id": "asset://fixture/model/1",
                                                    "source_record": {"fixture": "donor"}})
            project.import_metadata(imported)
            disc = Path(directory) / "fixture.bin"
            disc.write_bytes(b"synthetic")
            project.disc_path = str(disc)
            verified, posed = [], []
            def resolve(identifier, *, verify_disc=False):
                verified.append((identifier, verify_disc))
                source = project.overrides.get(identifier, {}).get("ActorAppearance", {}).get("donor_entity_id", identifier)
                return deepcopy(next(a for a in imported["actors"] if a["semantic_id"] == source))
            project.appearance_source_actor = resolve
            class Catalog:
                def pose_preview(self, actor, asset, frame):
                    posed.append((deepcopy(actor), asset["id"], frame))
                    result = geometry()
                    result["vertices"][0][0] = 7
                    return result
            service = ScenePreviewService()
            def loader(asset, *, prepared=None):
                return prepared if prepared is not None else geometry()
            with patch("sdk.scene_preview._disc_context", side_effect=lambda _: nullcontext()), \
                 patch("sdk.scene_preview.import_scene", return_value=deepcopy(imported)):
                first = service.preview(project, loader, lambda *_: Catalog())
                initial_key = first["source_key"]
                project.overrides[target["semantic_id"]] = {"ActorAppearance": {"donor_entity_id": donor["semantic_id"]}}
                replaced = service.preview(project, loader, lambda *_: Catalog())
                binding = replaced["entities"][0]
                self.assertNotEqual(initial_key, replaced["source_key"])
                self.assertEqual(binding["entity_id"], target["semantic_id"])
                self.assertEqual(binding["source_actor_id"], donor["semantic_id"])
                self.assertEqual(binding["source_record"], donor["source_record"])
                self.assertEqual(binding["model_reference"], donor["model_reference"])
                self.assertTrue(binding["appearance_authored"])
                self.assertEqual(binding["position"]["x"], 100)
                self.assertEqual(binding["geometry_key"], replaced["entities"][1]["geometry_key"])
                self.assertEqual(posed[-1][0], donor)
                # State projection resolves metadata without disc I/O; each geometry
                # rebuild must separately request verified sources for both actors.
                self.assertEqual([identifier for identifier, flag in verified if flag],
                                 [target["semantic_id"], donor["semantic_id"]] * 2)
                # Neither transform edits nor another scene's appearance invalidates geometry.
                project.overrides[target["semantic_id"]]["Transform"] = {"position": {"x": 333}}
                project.overrides["scene://other/actors/0001"] = {"ActorAppearance": {"donor_entity_id": "elsewhere"}}
                self.assertEqual(source_key(project), replaced["source_key"])
                cached = service.preview(project, loader, lambda *_: Catalog())
                self.assertEqual(cached["entities"][0]["position"]["x"], 333)
                self.assertEqual(len(posed), 2)
                del project.overrides[target["semantic_id"]]["ActorAppearance"]
                self.assertEqual(source_key(project), initial_key)
                reverted = service.preview(project, loader, lambda *_: Catalog())
                self.assertEqual(reverted["entities"][0]["source_actor_id"], target["semantic_id"])
                self.assertFalse(reverted["entities"][0]["appearance_authored"])
                self.assertEqual(project.imports[project.active_scene], imported)
                # A fabricated resolver result cannot attach foreign provenance to geometry.
                project.overrides[target["semantic_id"]]["ActorAppearance"] = {"donor_entity_id": donor["semantic_id"]}
                project.appearance_source_actor = lambda *args, **kwargs: {**donor, "source_record": {"forged": True}}
                with self.assertRaisesRegex(ProjectError, "verified scene evidence"):
                    service.preview(project, loader, lambda *_: Catalog())
                self.assertIsNone(service._key)

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
