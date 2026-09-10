"""Appearance authoring preserves source evidence and independent transforms."""
from copy import deepcopy
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from sdk.project import ProjectError, ProjectService
from integrations.legaia.tests.test_project_workflow import synthetic_scene


def appearance_scene():
    document = synthetic_scene()
    target = document["actors"][0]
    target["model_reference"]["model_index"] = 1
    document["assets"]["models"][0]["source_record"]["object_count"] = 10
    donor = deepcopy(target)
    donor["semantic_id"] = target["semantic_id"].rsplit("/", 1)[0] + "/0002"
    donor["model_reference"].update(model_index=2, asset_semantic_id="asset://fixture/model/1")
    donor["placement_fields"]["animation_id"] = 3
    document["actors"].append(donor)
    document["assets"]["models"].append({"semantic_id": "asset://fixture/model/1",
                                           "source_record": {"fixture": True, "object_count": 10}})
    return document


class ProjectAppearanceTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.project = ProjectService(Path(self.directory.name))
        self.document = appearance_scene()
        self.project.import_metadata(self.document)
        self.target, self.donor = [a["semantic_id"] for a in self.document["actors"]]
        self.options = patch.object(self.project, "appearance_options", return_value={
            "supported": True, "options": [{"donor_entity_id": self.donor}]})
        self.options.start()
        self.addCleanup(self.options.stop)

    def assign(self):
        self.project.command({"type": "set_actor_appearance", "entity_id": self.target,
                              "donor_entity_id": self.donor})

    def test_set_clear_history_and_offline_reopen_preserve_transform_and_import(self):
        project = self.project
        project.command({"type": "set_transform", "entity_id": self.target, "position": {"x": 128}})
        project.save()
        self.assign()
        self.assertTrue(project.dirty)
        authored = deepcopy(project.overrides)
        components = project.state()["scene"]["entities"][0]["components"]
        self.assertEqual(components["ActorAppearance"]["effective"]["donor_entity_id"], self.donor)
        self.assertEqual(components["ActorAppearance"]["effective"]["animation_id"], 3)
        self.assertEqual(components["Transform"]["effective"]["position"]["x"], 128)
        project.undo()
        self.assertFalse(project.dirty)
        self.assertEqual(project.overrides[self.target], {"Transform": {"position": {"x": 128}}})
        project.redo()
        self.assertEqual(project.overrides, authored)
        restored = ProjectService.open(project.save())
        self.assertEqual(restored.overrides, authored)
        self.assertEqual(restored.appearance_source_actor(self.target)["semantic_id"], self.donor)
        self.assertFalse(restored.dirty)
        self.assertEqual(restored.imports, project.imports)
        project.command({"type": "clear_actor_appearance", "entity_id": self.target})
        self.assertEqual(project.overrides[self.target], {"Transform": {"position": {"x": 128}}})
        project.undo()
        self.assertEqual(project.overrides, authored)
        project.redo()
        self.assertNotIn("ActorAppearance", project.overrides[self.target])
        self.assertEqual(project.imports[project.active_scene], self.document)

    def test_invalid_foreign_unverified_and_live_commands_are_transactional(self):
        project = self.project
        original = deepcopy(project.state())
        for donor in (None, True, {}, [], "missing", "scene://other/actors/0002"):
            with self.subTest(donor=donor), self.assertRaises(ProjectError):
                project.command({"type": "set_actor_appearance", "entity_id": self.target,
                                 "donor_entity_id": donor})
            self.assertEqual(project.state(), original)
        with patch.object(project, "appearance_options", return_value={"options": []}):
            with self.assertRaisesRegex(ProjectError, "verified"):
                self.assign()
        self.assertEqual(project.state(), original)
        project.mode = "live"
        for kind in ("set_actor_appearance", "clear_actor_appearance"):
            with self.assertRaisesRegex(ProjectError, "Edit mode"):
                project.command({"type": kind, "entity_id": self.target, "donor_entity_id": self.donor})
        self.assertEqual(project.overrides, {})
        self.assertEqual(project.undo_stack, [])

    def test_noops_preserve_history_and_clear_removes_empty_override(self):
        project = self.project
        project.command({"type": "clear_actor_appearance", "entity_id": self.target})
        self.assertEqual(project.undo_stack, [])
        self.assign()
        history = deepcopy(project.undo_stack)
        self.assign()
        self.assertEqual(project.undo_stack, history)
        project.command({"type": "clear_actor_appearance", "entity_id": self.target})
        self.assertEqual(project.overrides, {})
        project.undo()
        history, redo = deepcopy(project.undo_stack), deepcopy(project.redo_stack)
        self.assign()
        self.assertEqual(project.undo_stack, history)
        self.assertEqual(project.redo_stack, redo)

    def test_malformed_saved_bindings_and_incompatible_donors_are_rejected(self):
        self.assign()
        path = self.project.save()
        saved = json.loads(path.read_text(encoding="utf-8"))
        for value in (None, {}, {"donor_entity_id": self.donor, "model_index": 2},
                      {"donor_entity_id": True}, {"donor_entity_id": "scene://other/actor"}):
            malformed = deepcopy(saved)
            malformed["authored"][self.target]["ActorAppearance"] = value
            path.write_text(json.dumps(malformed), encoding="utf-8")
            with self.subTest(value=value), self.assertRaises(ProjectError):
                ProjectService.open(path)
        donor_asset = self.project.assets.records["asset://fixture/model/1"]
        donor_asset["source_record"]["object_count"] = 9
        with self.assertRaisesRegex(ProjectError, "same object count"):
            self.assign()


@unittest.skipUnless(os.environ.get("LEGAIA_DISC_BIN"), "requires private retail disc")
class RetailProjectAppearanceTests(unittest.TestCase):
    def test_verified_assignment_reopen_clear_and_unchanged_import(self):
        from importer.pipeline import _disc_context, import_scene
        disc = os.environ["LEGAIA_DISC_BIN"]
        # The temporary project contains user-owned metadata and is deleted on exit.
        with tempfile.TemporaryDirectory() as directory, _disc_context(disc):
            document = import_scene(disc, "town01")
            original = deepcopy(document)
            project = ProjectService(Path(directory))
            project.import_metadata(document)
            project.disc_path = disc
            target = next(a["semantic_id"] for a in document["actors"] if a["semantic_id"].endswith("/0049"))
            options = project.appearance_options(target)
            self.assertTrue(options["supported"])
            donor = next(o["donor_entity_id"] for o in options["options"] if not o["unchanged"])
            project.command({"type": "set_actor_appearance", "entity_id": target, "donor_entity_id": donor})
            self.assertEqual(project.appearance_source_actor(target, verify_disc=True)["semantic_id"], donor)
            restored = ProjectService.open(project.save())
            self.assertEqual(restored.appearance_source_actor(target, verify_disc=True)["semantic_id"], donor)
            restored.command({"type": "clear_actor_appearance", "entity_id": target})
            self.assertEqual(restored.appearance_source_actor(target)["semantic_id"], target)
            self.assertEqual(restored.overrides, {})
            self.assertEqual(restored.imports[restored.active_scene], original)
            self.assertEqual(document, original)


if __name__ == "__main__":
    unittest.main()
