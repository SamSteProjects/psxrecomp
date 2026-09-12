"""Build reports describe emitted changes and track authored snapshot identity."""
from copy import deepcopy
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from sdk.build import authored_state_key, build_report, package_change_kinds
from sdk.project import ProjectService
from integrations.legaia.tests.test_project_workflow import synthetic_scene


class BuildReportTests(unittest.TestCase):
    def test_package_content_summary_keeps_all_emitted_families(self):
        edits=[{'scope':'shared-scene-animation-record'}, {'scope':'source-MAP-wall-bit-only'},
               {'scope':'TMD-vertex-normal-XYZ-only'}, {'scope':'script-movement-target-only'},
               {'scope':'shared-scene-animation-record'}]
        expected=['animation channels','model shapes','script movement targets','source collision walls']
        self.assertEqual(package_change_kinds(edits),expected)
        self.assertEqual(package_change_kinds(list(reversed(edits))),expected)
        self.assertEqual(package_change_kinds([]),[])
        self.assertEqual(package_change_kinds([{'scope':'unknown'}]),['other audited scene data'])
        self.assertEqual(package_change_kinds([{}]),['actor positions'])

    def test_snapshot_tracks_build_inputs_but_not_selection_or_templates(self):
        with tempfile.TemporaryDirectory() as raw:
            project = ProjectService(Path(raw))
            project.import_metadata(synthetic_scene())
            baseline = authored_state_key(project)
            project.select(None)
            self.assertIsNone(project.selected)
            self.assertEqual(authored_state_key(project), baseline)
            project.select("scene://fixture/actors/man-p1/0001")
            self.assertEqual(project.selected, "scene://fixture/actors/man-p1/0001")
            project.actor_templates = {"template": {"name": "Unused template"}}
            self.assertEqual(authored_state_key(project), baseline)
            for attribute, replacement in (("name", "different"), ("disc_path", "different"),
                    ("overrides", {"actor": {"Transform": {"position": {"x": 64}}}}),
                    ("texture_overrides", {"texture": {"asset_sha256": "a" * 64}}),
                    ("imports", {})):
                before = deepcopy(getattr(project, attribute))
                setattr(project, attribute, replacement)
                self.assertNotEqual(authored_state_key(project), baseline, attribute)
                setattr(project, attribute, before)
                self.assertEqual(authored_state_key(project), baseline, attribute)

    def test_real_edit_history_and_reopen_restore_snapshot_identity(self):
        with tempfile.TemporaryDirectory() as raw:
            project = ProjectService(Path(raw))
            project.import_metadata(synthetic_scene())
            actor = "scene://fixture/actors/man-p1/0001"
            baseline = authored_state_key(project)
            project.command({"type": "set_transform", "entity_id": actor,
                             "position": {"x": 192}})
            edited = authored_state_key(project)
            self.assertNotEqual(edited, baseline)
            project.undo()
            self.assertEqual(authored_state_key(project), baseline)
            project.redo()
            self.assertEqual(authored_state_key(project), edited)
            project.command({"type": "create_actor_template", "entity_id": actor,
                             "name": "Saved position"})
            self.assertEqual(authored_state_key(project), edited)
            reopened = ProjectService.open(project.save())
            self.assertEqual(authored_state_key(reopened), edited)
            self.assertEqual(reopened.actor_templates, project.actor_templates)

    def test_transition_report_retains_navigable_resource_and_owner(self):
        owner = "scene://fixture/scripts/man-p2/0000"
        resource = "script://fixture/scripts/man-p2/0000/transition/0016"
        report = build_report({"edits": [{"scene": "fixture", "semantic_id": owner,
            "transition_id": resource, "field": "entry_x_encoded", "before_byte": 96,
            "after_byte": 97, "scope": "encoded-transition-entry-only"}],
            "overlays": [{"size": 10}], "validation": {"live_runtime": "not_run"}})
        change = report["changes"][0]
        self.assertEqual((change["asset_id"], change["owner_id"]), (resource, owner))
        self.assertEqual((change["before"], change["after"]), (96, 97))
        self.assertEqual(change["scope"], "encoded-transition-entry-only")

    def test_report_uses_audited_values_and_excludes_binary_spans(self):
        audit = {"edits": [
            {"scene": "fixture", "semantic_id": "actor", "field": "position.x",
             "before_value": 128, "after_value": 192, "before_byte": 1, "after_byte": 2},
            {"scene": "fixture", "semantic_id": "actor", "run_id": "run", "field": "dialogue.text",
             "before_hex": b"Before".hex(), "after_hex": b"After ".hex()},
            {"scene": "other", "semantic_id": "texture", "field": "texture.tim",
             "before_sha256": "a" * 64, "after_sha256": "b" * 64}],
            "overlays": [{"size": 20}, {"size": 30}], "validation": {"live_runtime": "not_run"}}
        report = build_report(audit)
        self.assertEqual((report["change_count"], report["scene_count"], report["overlay_bytes"]), (3, 2, 50))
        self.assertEqual(report["changes"][0]["before"], 128)
        self.assertEqual(report["changes"][1]["asset_id"], "run")
        self.assertEqual(report["changes"][1]["owner_id"], "actor")
        self.assertEqual(report["changes"][1]["after"], "After ")
        self.assertEqual(report["changes"][2]["after"], "b" * 64)
        self.assertNotIn("before_hex", str(report))
        report["validation"]["live_runtime"] = "changed"
        self.assertEqual(audit["validation"]["live_runtime"], "not_run")
        audit["edits"] = []; audit["overlays"] = []
        self.assertEqual(build_report(audit)["change_count"], 0)


if __name__ == "__main__":
    unittest.main()
