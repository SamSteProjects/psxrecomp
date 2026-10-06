"""Guarded MAN dialogue spans composed with appearance and position packages."""
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
from importer.core import decompress_lzs
from importer.pipeline import import_scene
from importer.serialization import compress_lzs, patch_man_positions
from importer.man_assignments import load_man_assignment_context
from sdk.build import BuildError, _merge_dialogue_patch, build_project


def merge_fixture():
    baseline = b"HEADERhelloTAIL"
    working = b"headerhelloTAIL"
    dialogue = b"HEADERHi   TAIL"
    run = {"record_index": 1, "decoded_byte_offset": 6, "byte_length": 5}
    audit = {**run, "run_id": "run-1", "before_hex": b"hello".hex(), "after_hex": b"Hi   ".hex(),
             "padding_bytes": 3, "source_decoded_man_sha256": hashlib.sha256(baseline).hexdigest()}
    previous = [{"decoded_byte_offset": n} for n in range(6)]
    return baseline, working, dialogue, [audit], {"run-1": run}, previous


class DialogueBuildGuards(unittest.TestCase):
    def test_independent_baseline_span_merge_preserves_other_edits(self):
        args = merge_fixture(); original = deepcopy(args)
        self.assertEqual(_merge_dialogue_patch(*args), b"headerHi   TAIL")
        self.assertEqual(args, original)
        self.assertEqual(_merge_dialogue_patch(args[0], args[1], args[0], [], {}, args[-1]), args[1])

    def test_bad_source_bounds_overlap_and_unaudited_bytes_fail(self):
        for field, value in (("run_id", "unknown"), ("record_index", 2), ("decoded_byte_offset", True),
                             ("decoded_byte_offset", -1), ("byte_length", 0), ("byte_length", 100),
                             ("source_decoded_man_sha256", "0"*64), ("before_hex", "0000000000"),
                             ("after_hex", "GG"), ("after_hex", "00")):
            args = list(merge_fixture()); args[3][0][field] = value
            before = deepcopy(args)
            with self.subTest(field=field), self.assertRaises(BuildError):
                _merge_dialogue_patch(*args)
            self.assertEqual(args, before)
        for mutation in ("overlap", "duplicate", "extra_change", "length"):
            args = list(merge_fixture())
            if mutation == "overlap": args[-1].append({"decoded_byte_offset": 6})
            elif mutation == "duplicate": args[3].append(deepcopy(args[3][0]))
            elif mutation == "extra_change": args[2] = args[2][:-1] + b"x"
            else: args[2] = args[2][:-1]
            with self.subTest(mutation=mutation), self.assertRaises(BuildError):
                _merge_dialogue_patch(*args)

    def test_malformed_dialogue_component_rejects_without_outputs(self):
        identifier = "scene://fixture/actors/man-p1/0001"
        actor = {"semantic_id": identifier, "source_record": {"record_index": 1}}
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            project = SimpleNamespace(texture_additions={}, root=root, name="fixture", disc_path="not-read",
                                      imports={"scene://fixture": {"actors": [actor]}}, overrides={})
            for component in (None, {}, {"runs": {}}, {"runs": []}, {"runs": {"run": 1}},
                              {"runs": {1: "text"}}, {"runs": {"run": "text"}, "source_record": {}},
                              {"runs": {"run": "text"}, "raw_hex": "abcd"}):
                project.overrides = {identifier: {"Dialogue": component}}
                with self.subTest(component=component), self.assertRaises(BuildError):
                    build_project(project)
                self.assertEqual(list(root.iterdir()), [])


@unittest.skipUnless(os.environ.get("LEGAIA_DISC_BIN"), "requires private retail disc")
class RetailDialogueBuild(unittest.TestCase):
    def test_all_three_edit_kinds_roundtrip_and_clear_baseline(self):
        from importer.dialogue_authoring import load_dialogue_authoring_context
        disc = os.environ["LEGAIA_DISC_BIN"]
        document = import_scene(disc, "town01"); original_document = deepcopy(document)
        target = "scene://town01/actors/man-p1/0005"
        speaker = "scene://town01/actors/man-p1/0049"
        donor = "scene://town01/actors/man-p1/0040"
        context = load_dialogue_authoring_context(disc, "town01")
        run = next(r for r in context.options(speaker)["runs"] if r["semantic_id"].endswith("/dialogue/0060/run/0061"))
        replacement_text = run["text"][:-1] + ("?" if run["text"][-1] != "?" else "!")
        actors = {a["semantic_id"]: a for a in document["actors"]}
        x = actors[target]["imported_transform"]["position"]["x"] + 64
        donor_pair = {"model_index": actors[donor]["model_reference"]["model_index"],
                      "animation_id": actors[donor]["placement_fields"]["animation_id"]}
        private = ROOT / "local-output/sdk-20260909"; private.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(prefix="dialogue-build-", dir=private) as directory:
            project = SimpleNamespace(texture_additions={}, root=Path(directory), name="Dialogue build verification", disc_path=disc,
                                      imports={"scene://town01": document}, overrides={})
            baseline_build = build_project(project)
            # A valid run under the wrong authored actor must fail before writing.
            project.overrides = {target: {"Dialogue": {"runs": {run["semantic_id"]: replacement_text}}}}
            rejected = project.root / "rejected-owner"
            with self.assertRaisesRegex(BuildError, "owned by this actor"):
                build_project(project, rejected)
            self.assertFalse(rejected.exists())
            project.overrides = {target: {"ActorAppearance": {"donor_entity_id": donor}, "Transform": {"position": {"x": x}}},
                                 speaker: {"Dialogue": {"runs": {run["semantic_id"]: replacement_text}}}}
            with patch("importer.serialization.compress_lzs", wraps=compress_lzs) as encoder:
                built = build_project(project)
                self.assertEqual(encoder.call_count, 1)
            self.assertEqual((built["overlay_count"], built["changed_fields"]), (1, 4))
            self.assertEqual(built["changed_fields_unit"], "authored fields/runs")
            appearances = load_man_assignment_context(disc, "town01")
            original, _ = appearances.patch({})
            header_changed, _ = appearances.patch({5: donor_pair})
            expected, _ = patch_man_positions(header_changed, "town01", {5: {"x": x}})
            dialogue, dialogue_audit = context.patch({run["semantic_id"]: replacement_text}, original=original)
            combined = bytearray(expected)
            for change in dialogue_audit:
                start, end = change["decoded_byte_offset"], change["decoded_byte_offset"] + change["byte_length"]
                combined[start:end] = dialogue[start:end]
            with zipfile.ZipFile(built["path"]) as package:
                payload = package.read("assets/town01-man.lzs")
                self.assertEqual(decompress_lzs(payload, len(original))[0], bytes(combined))
                self.assertIn(b"Dialogue: glyph edits preserve the source record layout.", package.read("manifest.toml"))
            audit = json.loads(Path(built["audit"]).read_text())
            dialogue_fields = [c for c in audit["edits"] if c.get("scope") == "inline-mes-glyph-run-only"]
            self.assertEqual(len(dialogue_fields), 1)
            self.assertEqual(dialogue_fields[0]["semantic_id"], speaker)
            self.assertEqual(dialogue_fields[0]["byte_length"], run["byte_length"])
            project.overrides = {speaker: {"Dialogue": {"runs": {run["semantic_id"]: run["text"]}}}}
            self.assertEqual(build_project(project)["sha256"], baseline_build["sha256"])
            project.overrides = {}
            self.assertEqual(build_project(project)["sha256"], baseline_build["sha256"])
            self.assertEqual(document, original_document)


@unittest.skipUnless(os.environ.get("LEGAIA_DISC_BIN"), "requires private retail disc")
class RetailP2DialogueBuild(unittest.TestCase):
    def test_p2_package_exact_span_and_clear_baseline(self):
        from importer.pipeline import import_scene
        from importer.dialogue_authoring import load_dialogue_authoring_context
        from importer.core import decompress_lzs
        disc = os.environ["LEGAIA_DISC_BIN"]
        document = import_scene(disc, "town01")
        context = load_dialogue_authoring_context(disc, "town01")
        identifier = "scene://town01/scripts/man-p2/0036"
        run = context.options(identifier)["runs"][0]
        replacement = run["text"][:-1] + ("?" if run["text"][-1] != "?" else "!")
        private = ROOT / "local-output/sdk-20260909"
        with tempfile.TemporaryDirectory(prefix="p2-dialogue-build-", dir=private) as directory:
            project = SimpleNamespace(texture_additions={}, root=Path(directory), name="P2 verification", disc_path=disc,
                                      imports={"scene://town01": document}, overrides={})
            baseline = build_project(project)
            project.overrides = {identifier: {"Dialogue": {"runs": {run["semantic_id"]: replacement}}}}
            built = build_project(project)
            self.assertEqual((built["overlay_count"], built["changed_fields"]), (1, 1))
            expected, changes = context.patch({run["semantic_id"]: replacement})
            original, _ = context.patch({})
            self.assertEqual(len(changes), 1)
            self.assertEqual(sum(a != b for a, b in zip(original, expected)), 1)
            with zipfile.ZipFile(built["path"]) as package:
                self.assertEqual(decompress_lzs(package.read("assets/town01-man.lzs"), len(expected))[0], expected)
            audit = json.loads(Path(built["audit"]).read_text())
            self.assertEqual(audit["edits"][0]["semantic_id"], identifier)
            project.overrides = {}
            self.assertEqual(build_project(project)["sha256"], baseline["sha256"])


if __name__ == "__main__":
    unittest.main()
