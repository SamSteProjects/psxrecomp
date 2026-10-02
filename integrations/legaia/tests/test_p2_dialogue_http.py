"""Opt-in retail P2 dialogue through the actual loopback HTTP handler."""
import json
import os
from pathlib import Path
import sys
import tempfile
import threading
import unittest
from urllib.request import Request, urlopen
from urllib.error import HTTPError

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from importer.pipeline import import_scene
from sdk.project import ProjectService
from sdk.server import EditorServer


@unittest.skipUnless(os.environ.get("LEGAIA_DISC_BIN"), "requires private retail disc")
class P2DialogueHTTP(unittest.TestCase):
    def test_verified_trigger_edit_refresh_clear_and_unknown_rejection(self):
        private = Path(__file__).resolve().parents[3] / "local-output/sdk-20260909"
        with tempfile.TemporaryDirectory(prefix="p2-http-", dir=private) as directory:
            project = ProjectService(Path(directory))
            project.disc_path = os.environ["LEGAIA_DISC_BIN"]
            project.import_metadata(import_scene(project.disc_path, "town01"))
            project.save()
            server = EditorServer(("127.0.0.1", 0), project)
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            def post(route, body):
                request = Request(f"http://127.0.0.1:{server.server_port}{route}",
                                  data=json.dumps(body).encode(), headers={"Content-Type": "application/json"})
                with urlopen(request, timeout=30) as response:
                    return json.load(response)
            try:
                flags = post("/api/scene-flags", {})
                self.assertEqual(flags["reference_count"], 1339)
                self.assertEqual(flags["coverage"]["script_count"], 91)
                self.assertEqual(flags["scene_id"], "scene://town01")
                self.assertTrue(all(group["runtime_binding"] == "unresolved" for group in flags["groups"]))
                self.assertTrue(any(group["partition"] == 2 for group in flags["groups"]))
                with self.assertRaises(HTTPError) as error:
                    post("/api/scene-flags", {"scene_id": "scene://town0c"})
                self.assertEqual(error.exception.code, 400)
                error.exception.close()
                graph = post("/api/scene-transitions", {})
                self.assertEqual(len(graph["edges"]), 1)
                edge = graph["edges"][0]
                self.assertEqual((edge["source"], edge["target"]), ("scene://town01", "scene://map01"))
                self.assertEqual(edge["script_id"], "script://town01/scripts/man-p2/0000")
                self.assertEqual(edge["reachability"], "not_evaluated")
                self.assertEqual(edge["script_status"], "partial")
                self.assertEqual(graph["coverage"]["script_count"], 91)
                trigger = {"asset_id": "trigger://town01/field-map/fallback/kind-1/0008"}
                report = post("/api/trigger-script", trigger)
                authoring = report["dialogue_authoring"]
                self.assertTrue(authoring["supported"])
                run = authoring["runs"][0]
                owner = "scene://" + report["script_id"].removeprefix("script://")
                self.assertIn("/scripts/man-p2/", owner)
                command = {"entity_id": owner, "run_id": run["semantic_id"]}
                post("/api/command", dict(command, type="set_dialogue_text", text="SDK"))
                edited = post("/api/trigger-script", trigger)["dialogue_authoring"]["runs"][0]
                self.assertEqual(edited["authored_text"], "SDK")
                self.assertEqual(edited["effective_text"], "SDK".ljust(run["max_length"]))
                restored = ProjectService.open(project.save())
                self.assertFalse(restored.assets.resource_catalogs)
                saved = restored.authored_assets()
                self.assertEqual(len(saved), 1)
                self.assertEqual(saved[0]["kind"], "script")
                self.assertEqual(saved[0]["id"], owner)
                self.assertEqual(saved[0]["script_id"], report["script_id"])
                reopened = post("/api/partition-two-script", {"entity_id": saved[0]["id"]})
                self.assertEqual(reopened["inspection"], report["inspection"])
                self.assertEqual(reopened["source_record"], report["source_record"])
                self.assertEqual(reopened["dialogue_authoring"]["runs"][0]["authored_text"], "SDK")
                for invalid in (owner.replace("town01", "town0c"), owner.rsplit("/", 1)[0] + "/9999",
                                owner.replace("scripts/man-p2", "actors/man-p1")):
                    with self.assertRaises(HTTPError) as error:
                        post("/api/partition-two-script", {"entity_id": invalid})
                    self.assertEqual(error.exception.code, 400)
                    error.exception.close()
                self.assertEqual(project.overrides, restored.overrides)
                post("/api/command", dict(command, type="clear_dialogue_text"))
                cleared = post("/api/trigger-script", trigger)["dialogue_authoring"]["runs"][0]
                self.assertIsNone(cleared["authored_text"])
                self.assertEqual(project.overrides, {})
                self.assertEqual(project.authored_assets(), [])
                opening = post("/api/trigger-script", {"asset_id": "trigger://town01/field-map/fallback/kind-1/0045"})
                self.assertFalse(opening["dialogue_authoring"]["supported"])
                self.assertEqual(opening["dialogue_authoring"]["runs"], [])
            finally:
                server.shutdown()
                server.server_close()
                thread.join(timeout=5)
            self.assertFalse(thread.is_alive())


if __name__ == "__main__":
    unittest.main()
