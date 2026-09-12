"""Scene geometry ownership, source invalidation and authored transform checks."""
from contextlib import nullcontext
from copy import deepcopy
from pathlib import Path
import sys
import tempfile
import unittest
from types import SimpleNamespace
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
    def test_environment_transforms_reuse_geometry_and_undo_restores_baseline(self):
        with tempfile.TemporaryDirectory() as directory:
            project = ProjectService(Path(directory))
            imported = synthetic_scene()
            imported['actors'][0]['placement_fields']['animation_id'] = 0
            project.import_metadata(imported)
            disc = Path(directory) / 'fixture.bin'
            disc.write_bytes(b'synthetic source')
            project.disc_path = str(disc)
            asset = imported['actors'][0]['model_reference']['asset_semantic_id']
            transform = {'position':dict(x=100,y=0,z=200), 'rotation_psx':dict(x=0,y=0,z=0)}
            placement = {'semantic_id':'decoration', 'name':'Decoration', 'model_asset_id':asset,
                         'imported_transform':transform, 'animation_id':0}
            catalog = SimpleNamespace(metadata={'placements':[placement], 'mesh_pool':{}},
                                      pose_preview=lambda _: {'pose':{'kind':'static'}})
            calls = []
            def loader(asset, **kwargs):
                calls.append(asset['id'])
                return {**geometry(), 'bounds':{'min':[0,-20,0],'max':[10,0,5]}}
            def effective(*_):
                return {'decoration':{'position':dict(x=228,y=0,z=200),
                                      'rotation_psx':dict(x=0,y=1024,z=0)}} if project.overrides else {}
            service = ScenePreviewService()
            with patch('sdk.scene_preview._disc_context', side_effect=lambda _:nullcontext()), \
                 patch('sdk.scene_preview.import_scene', return_value=deepcopy(imported)), \
                 patch('sdk.scene_preview.environment_effective_transforms', side_effect=effective):
                first = service.preview(project,loader,environment_loader_factory=lambda *_:catalog)
                count = len(calls)
                project.overrides[project.active_scene] = {'Environment':{'instances':[{'cell_index':1}]}}
                moved = service.preview(project,loader,environment_loader_factory=lambda *_:self.fail('geometry rebuilt'))
                self.assertEqual(len(calls),count)
                self.assertNotEqual(first['source_key'],moved['source_key'])
                self.assertEqual(moved['entities'][-1]['position']['x'],228)
                self.assertTrue(moved['entities'][-1]['authored_transform'])
                project.overrides.clear()
                restored = service.preview(project,loader)
                self.assertEqual(restored['entities'][-1]['position']['x'],100)
                self.assertFalse(restored['entities'][-1]['authored_transform'])
                self.assertEqual(first['assets'],restored['assets'])
                self.assertEqual(len(calls),count)

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
                draft_id = 'authored-actor://cffa550b-224d-4698-bb90-6a76fa491fee'
                project.actor_drafts[draft_id] = dict(scene_id=project.active_scene,
                    donor_entity_id=target['semantic_id'], position=dict(x=704,z=704), name='Retail donor draft')
                draft_preview = service.preview(project, loader, lambda *_: self.fail('draft rebuilt geometry'))
                draft_binding = next(e for e in draft_preview['entities'] if e['entity_id']==draft_id)
                self.assertEqual(draft_binding['source_actor_id'], target['semantic_id'])
                self.assertEqual(draft_binding['geometry_key'], first['entities'][0]['geometry_key'])
                self.assertFalse(draft_binding['appearance_authored'])
                self.assertEqual(draft_binding['position']['x'],704)
                self.assertEqual(draft_preview['metrics']['draft_count'],1)
                self.assertEqual(draft_preview['metrics']['total_entity_count'],len(draft_preview['entities']))
                self.assertEqual(draft_preview['metrics']['entity_count'],len(project.imports[project.active_scene]['actors'])+1)
                self.assertEqual(draft_preview['metrics']['total_renderable_count'],sum(bool(e['renderable']) for e in draft_preview['entities']))
                project.actor_drafts.clear()
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
