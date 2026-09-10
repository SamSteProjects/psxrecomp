"""Guarded texture package composition; retail assets remain private."""
from contextlib import nullcontext
from copy import deepcopy
import hashlib
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
from sdk.build import BuildError, build_project


def digest(data):
    return hashlib.sha256(data).hexdigest()


def binding(data, scene="scene://fixture"):
    return {"asset_sha256": digest(data), "byte_length": len(data), "format": "tim", "source_scene_id": scene}


class TextureBuildGuards(unittest.TestCase):
    def fixture(self, root):
        source, changed = b"original TIM fixture", b"modified TIM fixture"
        identifier = "texture://fixture/1/raw/0"
        document = {"scene": {"name": "fixture"}, "actors": [], "source": {"disc_identity": "sha256:" + "a" * 64}}
        project = SimpleNamespace(root=root, name="texture build fixture", disc_path="synthetic",
                                  imports={"scene://fixture": document}, overrides={},
                                  texture_overrides={identifier: binding(changed)},
                                  read_texture_replacement=lambda _: changed)
        image = SimpleNamespace(size=2352 * 2, read_user=lambda *_: source)
        overlay = {"scene": "fixture", "offset": 64, "size": len(source), "payload": changed,
                   "sha256": digest(changed), "expected_sha256": digest(source), "carrier_kind": "raw"}
        audit = {"semantic_id": identifier, "source_record": {}, "before_sha256": digest(source),
                 "after_sha256": digest(changed), "byte_length": len(changed), "scope": "TIM-image-and-palette-payload-only"}
        context = SimpleNamespace(original_tim=lambda _: source, patch=lambda _: ([overlay], [audit]))
        return project, document, image, context, overlay, audit

    def test_invalid_bindings_fail_without_source_access_or_output(self):
        with tempfile.TemporaryDirectory() as raw:
            project, *_ = self.fixture(Path(raw))
            good = deepcopy(project.texture_overrides)
            bad = [None, [], {"texture://fixture/1/raw/0": {}}]
            for key, value in (("source_scene_id", "scene://foreign"), ("format", "png"),
                               ("byte_length", True), ("byte_length", -1), ("byte_length", 1024 * 1024 + 1),
                               ("asset_sha256", "G" * 64),
                               ("path", "../retail.tim"), ("source_record", {})):
                edited = deepcopy(good); edited[next(iter(edited))][key] = value; bad.append(edited)
            with patch("sdk.build.import_scene") as source:
                for overrides in bad:
                    project.texture_overrides = overrides
                    with self.subTest(overrides=overrides), self.assertRaises(BuildError):
                        build_project(project)
                    self.assertEqual(list(Path(raw).iterdir()), [])
                source.assert_not_called()

    def test_stale_source_payload_audit_and_overlap_reject_before_publish(self):
        for fault in ("stale_import", "changed_file", "payload_hash", "source_hash", "offset", "size",
                      "missing_audit", "foreign_audit", "audit_hash", "overlap"):
            with self.subTest(fault=fault), tempfile.TemporaryDirectory() as raw:
                project, document, image, context, overlay, audit = self.fixture(Path(raw))
                fresh = deepcopy(document)
                if fault == "stale_import": fresh["actors"] = [{}]
                elif fault == "changed_file": project.read_texture_replacement = lambda _: b"changed file"
                elif fault == "payload_hash": overlay["sha256"] = "0" * 64
                elif fault == "source_hash": overlay["expected_sha256"] = "0" * 64
                elif fault == "offset": overlay["offset"] = True
                elif fault == "size": overlay["size"] += 1
                elif fault == "missing_audit": context.patch = lambda _: ([overlay], [])
                elif fault == "foreign_audit": audit["semantic_id"] = "texture://foreign/1/raw/0"
                elif fault == "audit_hash": audit["after_sha256"] = "0" * 64
                elif fault == "overlap": context.patch = lambda _: ([overlay, deepcopy(overlay)], [audit])
                with patch("sdk.build.import_scene", return_value=fresh), \
                        patch("sdk.build._disc_context", return_value=nullcontext((image, "a" * 64, None, None))), \
                        patch("importer.texture_authoring.load_texture_authoring_context", return_value=context):
                    with self.assertRaises(BuildError):
                        build_project(project)
                self.assertEqual(list(Path(raw).iterdir()), [])


@unittest.skipUnless(os.environ.get("LEGAIA_DISC_BIN"), "requires private retail disc")
class RetailTextureBuild(unittest.TestCase):
    def test_texture_and_man_composition_noop_clear_and_private_file_tamper(self):
        from importer.dialogue_authoring import load_dialogue_authoring_context
        from importer.pipeline import import_scene
        from importer.texture_authoring import load_texture_authoring_context
        from sdk.project import ProjectService, ProjectError
        disc = os.environ["LEGAIA_DISC_BIN"]
        document = import_scene(disc, "town01")
        context = load_texture_authoring_context(disc, "town01")
        ids = ["texture://town01/5/raw/0", "texture://town01/5/raw/1"]
        originals = {identifier: context.original_tim(identifier) for identifier in ids}
        replacements = {identifier: data[:-1] + bytes([data[-1] ^ 1]) for identifier, data in originals.items()}
        private = ROOT / "local-output/sdk-20260909"; private.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(prefix="texture-build-", dir=private) as raw:
            project = ProjectService(Path(raw))
            project.import_metadata(document, disc)
            project.save()
            baseline = build_project(project)
            imported = deepcopy(project.imports)
            def bind(payloads):
                project.texture_overrides = {}
                for identifier, data in payloads.items():
                    value = binding(data, "scene://town01")
                    path = project.root / "Authored/Textures" / (value["asset_sha256"] + ".tim")
                    path.parent.mkdir(parents=True, exist_ok=True); path.write_bytes(data)
                    project.texture_overrides[identifier] = value
            bind(originals)
            self.assertEqual(build_project(project)["sha256"], baseline["sha256"])
            bind(replacements)
            texture_only = build_project(project)
            self.assertEqual((texture_only["changed_fields"], texture_only["overlay_count"]), (2, 2))
            expected_overlays, _ = context.patch(replacements)
            target, donor, speaker = (f"scene://town01/actors/man-p1/{n:04d}" for n in (5, 40, 49))
            actor = next(a for a in document["actors"] if a["semantic_id"] == target)
            run = next(r for r in load_dialogue_authoring_context(disc, "town01").options(speaker)["runs"]
                       if r["semantic_id"].endswith("/dialogue/0060/run/0061"))
            project.overrides = {target: {"Transform": {"position": {"x": actor["imported_transform"]["position"]["x"] + 64}},
                                         "ActorAppearance": {"donor_entity_id": donor}},
                                 speaker: {"Dialogue": {"runs": {run["semantic_id"]: run["text"][:-1] + "?"}}}}
            combined = build_project(project)
            self.assertEqual((combined["changed_fields"], combined["overlay_count"]), (6, 3))
            self.assertEqual(combined["changed_fields_unit"], "authored fields/runs/textures")
            audit = json.loads(Path(combined["audit"]).read_text())
            with zipfile.ZipFile(combined["path"]) as archive:
                for expected in expected_overlays:
                    observed = next(o for o in audit["overlays"] if o["offset"] == expected["offset"])
                    self.assertEqual(archive.read(observed["file"]), expected["payload"])
                    self.assertEqual(observed["expected_sha256"], expected["expected_sha256"])
                self.assertIn(b"no resource relocation", archive.read("manifest.toml"))
            self.assertEqual(project.imports, imported)
            authored_file = project.root / "Authored/Textures" / (project.texture_overrides[ids[0]]["asset_sha256"] + ".tim")
            authored_file.write_bytes(b"tampered")
            rejected = project.root / "rejected"
            with self.assertRaises(ProjectError):
                build_project(project, rejected)
            self.assertFalse(rejected.exists())
            project.overrides = {}; project.texture_overrides = {}
            self.assertEqual(build_project(project)["sha256"], baseline["sha256"])


if __name__ == "__main__":
    unittest.main()
