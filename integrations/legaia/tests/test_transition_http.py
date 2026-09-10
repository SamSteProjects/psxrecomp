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
class TransitionHTTP(unittest.TestCase):
    def test_transition_apply_history_clear_and_client_source_rejection(self):
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
                owner = "scene://town01/scripts/man-p2/0000"
                report = post("/api/partition-two-script", {"entity_id": owner})
                entry = report["transition_authoring"]["transitions"][0]
                command = dict(entity_id=owner, transition_id=entry["semantic_id"])
                post("/api/command", dict(command, type="set_transition_entry", values={"entry_x_encoded": 99}))
                edited = post("/api/partition-two-script", {"entity_id": owner})["transition_authoring"]["transitions"][0]
                self.assertEqual(edited["effective_values"]["entry_x_encoded"], 99)
                post("/api/undo", {})
                self.assertFalse(project.overrides)
                post("/api/redo", {})
                self.assertTrue(project.overrides)
                post("/api/command", dict(command, type="clear_transition_entry"))
                self.assertFalse(project.overrides)
                with self.assertRaises(HTTPError) as error:
                    post("/api/command", dict(command, type="set_transition_entry", values={"entry_x_encoded":99}, source_offset=3))
                self.assertEqual(error.exception.code, 400)
                error.exception.close()
            finally:
                server.shutdown()
                server.server_close()
                thread.join(timeout=5)
            self.assertFalse(thread.is_alive())


if __name__ == "__main__":
    unittest.main()
