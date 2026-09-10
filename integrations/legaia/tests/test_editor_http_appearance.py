"""HTTP appearance boundary tests; resource decoding has separate retail tests."""
from contextlib import nullcontext
from copy import deepcopy
import http.client
import json
from pathlib import Path
import sys
import tempfile
import threading
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[3]
sys.path[:0] = [str(ROOT / "integrations/legaia"), str(ROOT)]
from importer.core import ImportError
from sdk.project import ProjectService
from sdk.server import EditorServer
from integrations.legaia.tests.test_project_appearance import appearance_scene


class AppearanceHTTPTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.project = ProjectService(Path(self.directory.name))
        self.document = appearance_scene()
        self.project.import_metadata(self.document)
        self.target, self.donor = [a["semantic_id"] for a in self.document["actors"]]
        self.options_patch = patch.object(self.project, "appearance_options", return_value={
            "supported": True, "reason": None, "options": [{"donor_entity_id": self.donor}],
            "limitations": ["synthetic HTTP fixture; no runtime claim"]})
        self.options = self.options_patch.start()
        self.server = EditorServer(("127.0.0.1", 0), self.project)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

    def tearDown(self):
        self.server.shutdown(); self.thread.join(timeout=3); self.server.server_close()
        self.options_patch.stop(); self.directory.cleanup()
        self.assertFalse(self.thread.is_alive())

    def post(self, route, body, status=200, headers=None):
        connection = http.client.HTTPConnection("127.0.0.1", self.server.server_port, timeout=3)
        try:
            connection.request("POST", route, json.dumps(body), {"Content-Type": "application/json", **(headers or {})})
            response = connection.getresponse(); result = json.loads(response.read())
            self.assertEqual(response.status, status, result)
            return result
        finally:
            connection.close()

    def command(self, kind, **fields):
        return self.post("/api/command", {"type": kind, "entity_id": self.target, **fields})

    def snapshot(self):
        return deepcopy((self.project.state(), self.project.undo_stack, self.project.redo_stack, self.server.last_build))

    def test_invalid_route_and_source_payloads_fail_before_decoding_or_mutation(self):
        before = self.snapshot()
        with patch.object(self.server, "actor_appearance_preview") as preview, patch.object(self.server, "export_preview") as export:
            for route in ("/api/actor-appearance-options", "/api/actor-appearance-preview", "/api/export/actor-appearance"):
                base = {"entity_id": self.target}
                if route.endswith("/actor-appearance") and route.startswith("/api/export/"):
                    base["frame_index"] = 0
                for body in ({}, [], {**base, "entity_id": None}, {**base, "entity_id": ""},
                             {**base, "entity_id": "scene://foreign/actors/man-p1/0001"},
                             *({**base, key: value} for key, value in (
                                 ("donor_entity_id", self.donor), ("asset_id", "asset://other"),
                                 ("disc_path", "elsewhere.bin"), ("output_path", "../outside.glb"),
                                 ("model_index", 9), ("animation_id", 4), ("raw_hex", "abcd"),
                                 ("source_record", {}), ("vertices", [[0, 0, 0]])))):
                    with self.subTest(route=route, body=body):
                        self.post(route, body, 400)
                        self.assertEqual(self.snapshot(), before)
            for frame in (None, True, -1, 0.5, "0"):
                self.post("/api/export/actor-appearance", {"entity_id": self.target, "frame_index": frame}, 400)
            preview.assert_not_called(); export.assert_not_called(); self.options.assert_not_called()
        self.assertFalse((self.project.root / "Exports").exists())

    def test_commands_history_save_reopen_and_rejections_preserve_layers(self):
        self.command("set_transform", position={"x": 128})
        imported = deepcopy(self.project.imports)
        self.post("/api/actor-appearance-options", {"entity_id": self.target})
        self.command("set_actor_appearance", donor_entity_id=self.donor)
        combined = deepcopy(self.project.overrides)
        self.command("clear_actor_appearance")
        self.assertEqual(self.project.overrides[self.target], {"Transform": {"position": {"x": 128}}})
        self.post("/api/undo", {}); self.assertEqual(self.project.overrides, combined)
        self.post("/api/redo", {}); self.assertNotIn("ActorAppearance", self.project.overrides[self.target])
        self.post("/api/undo", {}); self.post("/api/project/save", {})
        restored = ProjectService.open(self.project.root)
        self.assertEqual(restored.overrides, combined)
        self.assertEqual(restored.imports, imported)
        before = self.snapshot()
        for body in ({"type": "set_actor_appearance", "entity_id": self.target},
                     {"type": "set_actor_appearance", "entity_id": self.target, "donor_entity_id": self.donor, "source_record": {}},
                     {"type": "clear_actor_appearance", "entity_id": self.target, "donor_entity_id": self.donor},
                     *({"type": "set_actor_appearance", "entity_id": self.target, "donor_entity_id": value}
                       for value in (None, True, [], {}, "missing", "scene://foreign/actor"))):
            self.post("/api/command", body, 400); self.assertEqual(self.snapshot(), before)
        with patch.object(self.project, "appearance_options", side_effect=ImportError("verified source changed")):
            self.post("/api/command", {"type": "set_actor_appearance", "entity_id": self.target, "donor_entity_id": self.donor}, 400)
            self.assertEqual(self.snapshot(), before)
        self.project.mode = "live"
        live_before = self.snapshot()
        self.post("/api/command", {"type": "clear_actor_appearance", "entity_id": self.target}, 400)
        self.assertEqual(self.snapshot(), live_before)

    def test_preview_uses_project_donor_and_blocks_cross_origin(self):
        self.command("set_actor_appearance", donor_entity_id=self.donor)
        animation_preview = {"animation": {"actor_semantic_id": self.donor, "source_record": {"fixture": True}},
                             "animation_support": {"supported": True, "clips": []}, "frames": []}
        before = self.snapshot()
        with patch("importer.pipeline._disc_context", return_value=nullcontext()), patch.object(
                self.server, "actor_animation_preview", return_value=deepcopy(animation_preview)) as animation:
            result = self.post("/api/actor-appearance-preview", {"entity_id": self.target})
            animation.assert_called_once_with(self.donor)
            self.assertEqual(result["animation"]["entity_id"], self.target)
            self.assertEqual(result["animation"]["donor_entity_id"], self.donor)
            self.assertEqual(result["animation"]["actor_semantic_id"], self.donor)
            self.assertEqual(result["animation"]["layer"], "authored")
            self.assertEqual(self.snapshot(), before)
        calls = self.options.call_count
        self.post("/api/actor-appearance-options", {"entity_id": self.target}, 403,
                  headers={"Origin": "https://foreign.invalid"})
        self.assertEqual(self.options.call_count, calls)
        self.assertEqual(self.snapshot(), before)


if __name__ == "__main__":
    unittest.main()
