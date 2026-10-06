"""Package integration for initial MAN donor pairs; retail payloads stay private."""
from copy import deepcopy
import json
import os
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch
import zipfile

ROOT = Path(__file__).resolve().parents[3]
sys.path[:0] = [str(ROOT / "integrations/legaia"), str(ROOT)]
from importer.core import ImportError, decompress_lzs
from importer.man_assignments import load_man_assignment_context
from importer.pipeline import import_scene
from importer.serialization import compress_lzs, patch_man_positions, serialize_man_decoded, serialize_man_stream
from sdk.build import BuildError, build_project
from integrations.legaia.tests.test_importer_man_assignments import fixture as assignment_fixture


def actor(scene, record, model=4, animation=1):
    return {"semantic_id": f"scene://{scene}/actors/man-p1/{record:04d}",
            "source_record": {"record_index": record},
            "model_reference": {"model_index": model},
            "placement_fields": {"animation_id": animation}}


class AssignmentBuildGuards(unittest.TestCase):
    def test_malformed_foreign_missing_and_unknown_components_reject_before_output(self):
        first, donor, foreign = actor("fixture", 1), actor("fixture", 2), actor("other", 1)
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            documents = {"scene://fixture": {"scene": {"name": "fixture"}, "actors": [first, donor]},
                         "scene://other": {"scene": {"name": "other"}, "actors": [foreign]}}
            project = SimpleNamespace(texture_additions={}, root=root, name="fixture", disc_path="synthetic", imports=documents, overrides={})
            for components in ({}, {"ModelRenderer": {}}, {"ActorAppearance": {}},
                               {"ActorAppearance": {"donor_entity_id": True}},
                               {"ActorAppearance": {"donor_entity_id": "missing"}},
                               {"ActorAppearance": {"donor_entity_id": foreign["semantic_id"]}},
                               {"ActorAppearance": {"donor_entity_id": donor["semantic_id"], "model_index": 5}},
                               {"ActorAppearance": {"donor_entity_id": donor["semantic_id"]},
                                "Transform": {"position": {"y": 4}}}):
                project.overrides = {first["semantic_id"]: components}
                before = deepcopy(project.overrides)
                with self.subTest(components=components), self.assertRaises(BuildError):
                    build_project(project)
                self.assertEqual(project.overrides, before)
                self.assertEqual(list(root.iterdir()), [])

    def test_stale_donor_metadata_rejects_before_resource_or_output_access(self):
        first, donor = actor("fixture", 1), actor("fixture", 2)
        document = {"scene": {"name": "fixture"}, "actors": [first, donor]}
        fresh = deepcopy(document); fresh["actors"][1]["model_reference"]["model_index"] = 9
        project = SimpleNamespace(texture_additions={}, disc_path="synthetic", imports={"scene://fixture": document},
                                  overrides={first["semantic_id"]: {"ActorAppearance": {"donor_entity_id": donor["semantic_id"]}}})
        with patch("sdk.build.import_scene", return_value=fresh), patch("sdk.build._disc_context") as resources:
            with self.assertRaisesRegex(BuildError, "fresh retail import"):
                build_project(project)
            resources.assert_not_called()

    def test_composed_serializer_noop_and_length_rejection(self):
        original = b"opaque repeated source" * 4
        stream = compress_lzs(original) + b"TAIL"
        encoded, sizes = serialize_man_decoded(stream, len(original), original, "fixture")
        self.assertEqual(encoded, stream[:-4])
        self.assertEqual(sizes["original_encoded_size"], sizes["new_encoded_size"])
        for changed in (original + b"x", bytearray(original)):
            with self.assertRaisesRegex(ImportError, "decoded byte length"):
                serialize_man_decoded(stream, len(original), changed, "fixture")

    def test_composed_capacity_growth_rejects_without_mutation(self):
        context, original = assignment_fixture(compressed=True, opaque_prefix=bytes.fromhex(
            "010500020004040404010004000404050004020105000200000005000401"))
        changed, _ = context.patch({1: {"model_index": 5, "animation_id": 2}})
        stream = compress_lzs(original)
        with self.assertRaisesRegex(ImportError, "original span"):
            serialize_man_decoded(stream, len(original), changed, "fixture")
        self.assertEqual(decompress_lzs(stream, len(original))[0], original)


@unittest.skipUnless(os.environ.get("LEGAIA_DISC_BIN"), "requires private retail disc")
class RetailAssignmentBuild(unittest.TestCase):
    def test_combined_package_clear_and_position_only_compatibility(self):
        disc = os.environ["LEGAIA_DISC_BIN"]
        document = import_scene(disc, "town01")
        before_document = deepcopy(document)
        context = load_man_assignment_context(disc, "town01")
        target = next(a for a in document["actors"] if a["source_record"]["record_index"] == 5)
        donor = next(a for a in document["actors"] if a["source_record"]["record_index"] == 40)
        pair = {"model_index": donor["model_reference"]["model_index"], "animation_id": donor["placement_fields"]["animation_id"]}
        x = target["imported_transform"]["position"]["x"] + 64
        private = ROOT / "local-output/sdk-20260909"
        private.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(prefix="assignment-build-", dir=private) as raw:
            project = SimpleNamespace(texture_additions={}, root=Path(raw), name="Assignment build verification", disc_path=disc,
                                      imports={"scene://town01": document}, overrides={})
            baseline = build_project(project)
            self.assertEqual(baseline["overlay_count"], 0)
            for target_record, donor_record in ((1, 40), (52, 40), (5, 36)):
                project.overrides = {f"scene://town01/actors/man-p1/{target_record:04d}": {
                    "ActorAppearance": {"donor_entity_id": f"scene://town01/actors/man-p1/{donor_record:04d}"}}}
                rejected_output = project.root / f"rejected-{target_record}-{donor_record}"
                with self.assertRaisesRegex(BuildError, "unsupported initial donor assignment"):
                    build_project(project, rejected_output)
                self.assertFalse(rejected_output.exists())
            project.overrides = {target["semantic_id"]: {"ActorAppearance": {"donor_entity_id": donor["semantic_id"]},
                                                        "Transform": {"position": {"x": x}}}}
            # Only the final composed encoding invokes the compressor.
            with patch("importer.serialization.compress_lzs", wraps=compress_lzs) as encoder:
                combined = build_project(project)
                self.assertEqual(encoder.call_count, 1)
            self.assertEqual((combined["changed_fields"], combined["overlay_count"]), (3, 1))
            audit = json.loads(Path(combined["audit"]).read_text())
            appearance = [e for e in audit["edits"] if e.get("scope") == "initial-man-header-only"]
            self.assertEqual(len(appearance), 2)
            self.assertTrue(all(e["donor_entity_id"] == donor["semantic_id"] and e["script_compatibility"] == "unverified" for e in appearance))
            changed, _ = context.patch({5: pair})
            expected, _ = patch_man_positions(changed, "town01", {5: {"x": x}})
            with zipfile.ZipFile(combined["path"]) as package:
                payload = package.read("assets/town01-man.lzs")
                self.assertEqual(decompress_lzs(payload, len(expected))[0], expected)
                self.assertIn(b"scripts may override appearance", package.read("manifest.toml"))
            project.overrides = {}
            cleared = build_project(project)
            self.assertEqual((cleared["sha256"], cleared["overlay_count"]), (baseline["sha256"], 0))
            project.overrides = {target["semantic_id"]: {"ActorAppearance": {"donor_entity_id": target["semantic_id"]}}}
            self.assertEqual(build_project(project)["sha256"], baseline["sha256"])
            project.overrides = {target["semantic_id"]: {"Transform": {"position": {"x": x}}}}
            with patch("sdk.build.load_man_assignment_context", side_effect=AssertionError("position-only must not need ANM")):
                position_only = build_project(project)
            original_span, _, original_stats = context.serialize({})
            old_payload, _, _ = serialize_man_stream(original_span, original_stats["decoded_size"], "town01", {5: {"x": x}})
            with zipfile.ZipFile(position_only["path"]) as package:
                self.assertEqual(package.read("assets/town01-man.lzs"), old_payload)
                self.assertIn(b'name = "Authored actor placements"', package.read("manifest.toml"))
            self.assertEqual(document, before_document)


if __name__ == "__main__":
    unittest.main()
