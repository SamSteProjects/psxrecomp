"""Opt-in retail P2 dialogue through the actual loopback HTTP handler."""
import json
import os
from pathlib import Path
import sys
import tempfile
import threading
import unittest
from urllib.request import Request, urlopen

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
                post("/api/command", dict(command, type="clear_dialogue_text"))
                cleared = post("/api/trigger-script", trigger)["dialogue_authoring"]["runs"][0]
                self.assertIsNone(cleared["authored_text"])
                self.assertEqual(project.overrides, {})
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
