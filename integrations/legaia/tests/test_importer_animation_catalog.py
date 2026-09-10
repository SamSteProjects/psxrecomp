"""Animation asset metadata uses real bindings and never preview payloads."""
from copy import deepcopy
import os
from pathlib import Path
import struct
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[3]
sys.path[:0] = [str(ROOT / "integrations/legaia"), str(ROOT)]
from importer.animation_catalog import load_animation_asset_catalog
from importer.core import ImportError, canonical_json, validate_metadata_only
from importer.scene_animation import SceneActorAnimationCatalog


def fixture(reverse=False, marker=0x080C):
    assets = [{"semantic_id": f"asset://fixture/models/scene-tmd/{i:04d}", "asset_kind": "tmd_model",
               "source_record": {"object_count": count}}
              for i, count in ((1, 1), (2, 1), (3, 2), (4, 1))]
    actors = []
    for index, model, animation in ((1, 1, 1), (2, 2, 1), (3, 1, 0), (4, 0xF0, 1), (5, 3, 1)):
        actors.append({"semantic_id": f"scene://fixture/actors/man-p1/{index:04d}",
                       "source_record": {"record_index": index}, "placement_fields": {"animation_id": animation, "local_count": 0},
                       "model_reference": {"model_index": model, "asset_semantic_id": assets[max(0, min(model-1, 3))]["semantic_id"]}})
    record = struct.pack("<4H", 1, 2, marker, 2) + bytes(24)
    body = struct.pack("<III", 2, 12, 12+len(record)) + record + record
    document = {"actors": list(reversed(actors)) if reverse else actors, "assets": {"models": assets}}
    return SceneActorAnimationCatalog("synthetic", "fixture", document, body,
                                      {"descriptor_type": 5, "disc": {"sha256": "f" * 64}})


class AnimationCatalogTests(unittest.TestCase):
    def read(self, catalog):
        with patch("importer.animation_catalog.load_scene_actor_animation_catalog", return_value=catalog), patch(
                "importer.scene_animation.load_model_preview", side_effect=AssertionError("metadata must not load geometry")):
            return load_animation_asset_catalog("synthetic", "fixture")

    def test_deduplicated_stable_ids_exact_bindings_unknown_timing(self):
        result = self.read(fixture())
        self.assertEqual((result["asset_count"], result["binding_count"], result["actor_count"]), (1, 2, 5))
        self.assertEqual(result["scene_anm_record_count"], 2)
        asset = result["assets"][0]
        self.assertEqual(asset["semantic_id"], "animation://fixture/scene-anm/0000")
        self.assertEqual(asset["name"], "Scene animation 0000")
        self.assertEqual((asset["asset_kind"], asset["kind"]), ("animation", "animation"))
        self.assertEqual((asset["frame_count"], asset["channel_count"], asset["bone_count"]), (2, 1, 1))
        self.assertIsNone(asset["timing"]["fps"]); self.assertIsNone(asset["timing"]["wire_rate"])
        self.assertIsNone(asset["looping"])
        self.assertEqual(asset["actor_semantic_ids"], [f"scene://fixture/actors/man-p1/{i:04d}" for i in (1, 2)])
        self.assertEqual(asset["asset_semantic_ids"], [f"asset://fixture/models/scene-tmd/{i:04d}" for i in (1, 2)])
        self.assertNotIn("preview_actor_semantic_id", asset)
        self.assertEqual(len(result["unavailable_bindings"]), 3)
        self.assertEqual(result["unavailable_binding_count"], 3)
        self.assertIn("Referenced initial MAN animations only", result["limitations"][0])
        self.assertEqual(canonical_json(result), canonical_json(self.read(fixture(reverse=True))))
        validate_metadata_only(result)
        text = canonical_json(result)
        for payload_key in ('"frames":', '"vertices":', '"geometry":', '"object_transforms":', '"raw_bytes":'):
            self.assertNotIn(payload_key, text)

    def test_returned_metadata_cannot_change_future_results(self):
        catalog = fixture(); first = self.read(catalog); expected = deepcopy(first)
        first["assets"][0]["source_record"]["disc"]["sha256"] = "changed"
        first["assets"][0]["bindings"][0]["actor_source_record"]["record_index"] = 999
        first["unavailable_bindings"].clear()
        self.assertEqual(self.read(catalog), expected)

    def test_unsupported_wire_and_excessive_bindings_are_explicit(self):
        bad = self.read(fixture(marker=0))
        self.assertEqual(bad["assets"], [])
        self.assertEqual(len(bad["unavailable_bindings"]), 5)
        self.assertIn("0 animation assets", bad["limitations"][1])
        self.assertIn("unsupported animation record mode", bad["unavailable_bindings"][0]["reason"])
        catalog = fixture(); original = next(iter(catalog._actors.values()))
        catalog._actors = {f"actor-{n}": original for n in range(513)}
        with self.assertRaisesRegex(ImportError, "512 actor"):
            self.read(catalog)
        with patch("importer.animation_catalog.load_scene_actor_animation_catalog", side_effect=ImportError("disc changed")):
            with self.assertRaisesRegex(ImportError, "disc changed"):
                load_animation_asset_catalog("synthetic", "fixture")


@unittest.skipUnless(os.environ.get("LEGAIA_DISC_BIN"), "requires private retail disc")
class RetailAnimationCatalogTests(unittest.TestCase):
    def test_town01_referenced_records_metadata_only_and_repeatable(self):
        disc = os.environ["LEGAIA_DISC_BIN"]
        with patch("importer.scene_animation.load_model_preview", side_effect=AssertionError("metadata must not load geometry")):
            result = load_animation_asset_catalog(disc, "town01")
            repeated = load_animation_asset_catalog(disc, "town01")
        self.assertEqual(canonical_json(result), canonical_json(repeated))
        self.assertEqual((result["actor_count"], result["binding_count"], len(result["unavailable_bindings"])), (52, 39, 13))
        self.assertGreater(result["asset_count"], 0)
        self.assertLess(result["asset_count"], result["binding_count"])
        self.assertLess(len(canonical_json(result).encode()), 256 * 1024)
        for asset in result["assets"]:
            self.assertEqual(asset["source_record"]["descriptor_type"], 5)
            self.assertEqual(asset["source_record"]["containing_size"], 96448)
            self.assertEqual(len(asset["source_record"]["record_sha256"]), 64)
            self.assertIsNone(asset["timing"]["fps"])
            self.assertEqual(asset["bone_count"], asset["channel_count"])
            self.assertTrue(all(b["initial_animation_id"] == asset["record_index"] + 1 for b in asset["bindings"]))
        validate_metadata_only(result)


if __name__ == "__main__":
    unittest.main()
