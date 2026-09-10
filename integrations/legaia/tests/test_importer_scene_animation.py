"""Actual MAN-to-ANM association tests; tracked payloads are synthetic only."""
from copy import deepcopy
import os
from pathlib import Path
import struct
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from importer.core import ImportError
from importer.scene_animation import (SceneActorAnimationCatalog, actor_animation_capabilities,
                                     load_scene_actor_animation_catalog)


def fixture(bones=1):
    record = struct.pack("<4H", bones, 2, 0x080C, 2)
    record += b"".join(bytes([frame * 10 + bone, 0, 0, 0, 0, 0, 0, 0])
                        for frame in range(2) for bone in range(bones)) + bytes(8)
    body = struct.pack("<II", 1, 8) + record
    asset = {"semantic_id": "asset://synthetic/models/scene-tmd/0001", "asset_kind": "tmd_model",
             "source_record": {"object_count": 1, "disc": {"sha256": "f" * 64}}}
    actor = {"semantic_id": "scene://synthetic/actors/man-p1/0001",
             "source_record": {"record_index": 1, "disc": {"sha256": "f" * 64}},
             "placement_fields": {"animation_id": 1, "local_count": 0},
             "model_reference": {"asset_semantic_id": asset["semantic_id"], "model_index": 1}}
    model = {"vertices": [[1, 2, 3]], "triangles": [[0, 0, 0]], "posed": False,
             "coordinate_system": "retail_tmd_object_local",
             "objects": [{"object_index": 0, "vertex_start": 0, "vertex_count": 1}]}
    document = {"actors": [deepcopy(actor)], "assets": {"models": [deepcopy(asset)]}}
    catalog = SceneActorAnimationCatalog("synthetic.bin", "synthetic", document, body,
                                         {"descriptor_type": 5, "disc": {"sha256": "f" * 64}})
    return catalog, actor, asset, model


class SceneAnimationTests(unittest.TestCase):
    def test_frame_mapping_stable_ids_and_no_world_pose_invention(self):
        catalog, actor, asset, model = fixture()
        original = deepcopy(model)
        with patch("importer.scene_animation.load_model_preview", return_value=model) as load:
            pose = catalog.pose_preview(actor, asset, 1)
            animation = catalog.animation_preview(actor, asset)
            self.assertEqual(load.call_count, 1)
        self.assertEqual(pose["vertices"], [[11, 2, 3]])
        self.assertTrue(pose["posed"])
        self.assertEqual(pose["coordinate_system"], "retail_psx_actor_local_y_down")
        self.assertEqual(pose["pose"]["semantic_id"], "animation://synthetic/scene-anm/0000")
        self.assertEqual(pose["pose"]["source_record"]["record_index"], 0)
        self.assertIsNone(pose["pose"]["timing"]["fps"])
        self.assertIsNone(pose["pose"]["skeleton"]["hierarchy"])
        self.assertEqual(animation["frames"][1]["vertices"], pose["vertices"])
        self.assertEqual(animation["geometry"]["vertices"], original["vertices"])
        self.assertEqual(model, original)
        # Caller changes to returned geometry cannot poison the request cache.
        pose["vertices"][0][0] = 999
        pose["pose"]["source_record"]["disc"]["sha256"] = "changed"
        with patch("importer.scene_animation.load_model_preview") as load:
            restored = catalog.pose_preview(actor, asset, 1)
            self.assertEqual(restored["vertices"], [[11, 2, 3]])
            self.assertEqual(restored["pose"]["source_record"]["disc"]["sha256"], "f" * 64)
            load.assert_not_called()

    def test_zero_global_wrong_asset_and_tampered_source_are_rejected(self):
        catalog, actor, asset, _ = fixture()
        for fields in ({"animation_id": 0}, {"animation_id": 2}, {"animation_id": True}):
            bad = deepcopy(actor)
            bad["placement_fields"].update(fields)
            with self.assertRaises(ImportError):
                catalog.pose_preview(bad, asset)
        for mutate in (lambda a: a["model_reference"].update(model_index=0xF1),
                       lambda a: a["source_record"].update(record_index=9),
                       lambda a: a["model_reference"].update(asset_semantic_id="asset://other")):
            bad = deepcopy(actor)
            mutate(bad)
            with self.assertRaises(ImportError):
                catalog.pose_preview(bad, asset)
        bad = deepcopy(asset)
        bad["source_record"]["disc"]["sha256"] = "0" * 64
        with self.assertRaisesRegex(ImportError, "provenance"):
            catalog.pose_preview(actor, bad)

    def test_wrong_channel_count_and_frame_bounds_are_rejected(self):
        catalog, actor, asset, _ = fixture(bones=2)
        with self.assertRaisesRegex(ImportError, "channel count"):
            catalog.pose_preview(actor, asset)
        self.assertFalse(catalog.capabilities(actor, asset)["supported"])
        catalog, actor, asset, model = fixture()
        with patch("importer.scene_animation.load_model_preview", return_value=model):
            for frame in (-1, 2, True):
                with self.assertRaisesRegex(ImportError, "frame index"):
                    catalog.pose_preview(actor, asset, frame)

    def test_header_eligibility_does_not_fabricate_idle_or_rate(self):
        _, actor, asset, _ = fixture()
        support = actor_animation_capabilities(actor, asset)
        self.assertEqual(support["clips"], [{"id": "placement", "label": "Imported animation 1", "record_index": 0}])
        actor["placement_fields"]["animation_id"] = 0
        self.assertFalse(actor_animation_capabilities(actor, asset)["supported"])


@unittest.skipUnless(os.environ.get("LEGAIA_DISC_BIN"), "requires private retail disc")
class RetailSceneAnimationTests(unittest.TestCase):
    def test_town01_all_39_header_associations_pose_and_preserve_unknowns(self):
        from importer.pipeline import _disc_context, import_scene
        disc = os.environ["LEGAIA_DISC_BIN"]
        with _disc_context(disc):
            imported = import_scene(disc, "town01")
            catalog = load_scene_actor_animation_catalog(disc, "town01")
            assets = {a["semantic_id"]: a for a in imported["assets"]["models"]}
            counts = {"supported": 0, "zero": 0, "global": 0}
            for actor in imported["actors"]:
                asset = assets[actor["model_reference"]["asset_semantic_id"]]
                if actor["model_reference"]["model_index"] >= 0xF0:
                    counts["global"] += 1
                    self.assertFalse(catalog.capabilities(actor, asset)["supported"])
                    continue
                if actor["placement_fields"]["animation_id"] == 0:
                    counts["zero"] += 1
                    self.assertFalse(catalog.capabilities(actor, asset)["supported"])
                    continue
                pose = catalog.pose_preview(actor, asset)
                self.assertEqual(len(pose["objects"]), pose["pose"]["bone_count"])
                self.assertEqual(pose["pose"]["association"]["animation_id"], actor["placement_fields"]["animation_id"])
                self.assertEqual(pose["pose"]["source_record"]["descriptor_type"], 5)
                self.assertEqual(pose["pose"]["source_record"]["containing_size"], 96448)
                self.assertIsNone(actor["imported_transform"]["rotation"])
                self.assertIsNone(actor["imported_transform"]["position"]["y"])
                counts["supported"] += 1
            self.assertEqual(counts, {"supported": 39, "zero": 10, "global": 3})
            actor = next(a for a in imported["actors"] if a["semantic_id"].endswith("/0049"))
            asset = assets[actor["model_reference"]["asset_semantic_id"]]
            animation = catalog.animation_preview(actor, asset)
            self.assertEqual((animation["bone_count"], animation["frame_count"]), (10, 15))
            self.assertEqual(animation["frames"][0]["vertices"], catalog.pose_preview(actor, asset)["vertices"])


if __name__ == "__main__":
    unittest.main()
