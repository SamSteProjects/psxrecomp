"""One HTTP regression for the template dialog's actual command payloads."""
from copy import deepcopy
import http.client
import json
from pathlib import Path
import sys
import tempfile
import threading
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from sdk.project import ProjectService
from sdk.server import EditorServer
from integrations.legaia.tests.test_project_workflow import synthetic_scene


class TemplateHTTPWorkflow(unittest.TestCase):
    def test_create_apply_delete_and_normal_command_validation(self):
        with tempfile.TemporaryDirectory() as directory:
            project = ProjectService(Path(directory))
            metadata = synthetic_scene()
            second = deepcopy(metadata["actors"][0])
            second["semantic_id"] = "scene://fixture/actors/man-p1/0002"
            metadata["actors"].append(second)
            project.import_metadata(metadata)
            first_id, second_id = [actor["semantic_id"] for actor in metadata["actors"]]
            with EditorServer(("127.0.0.1", 0), project) as server:
                thread = threading.Thread(target=server.serve_forever, daemon=True)
                thread.start()

                def command(body, expected_status=200, route="/api/command"):
                    connection = http.client.HTTPConnection("127.0.0.1", server.server_port, timeout=3)
                    try:
                        connection.request("POST", route, json.dumps(body), {"Content-Type": "application/json"})
                        response = connection.getresponse()
                        result = json.loads(response.read())
                        self.assertEqual(response.status, expected_status, result)
                        return result
                    finally:
                        connection.close()

                try:
                    command({"type": "set_transform", "entity_id": first_id, "position": {"x": 128}})
                    created = command({"type": "create_actor_template", "entity_id": first_id, "name": "Courtyard"})
                    template_id = created["actor_templates"][0]["id"]
                    applied = command({"type": "apply_actor_template", "entity_id": second_id, "template_id": template_id})
                    transform = applied["scene"]["entities"][1]["components"]["Transform"]
                    self.assertEqual(transform["authored"], {"position": {"x": 128}})
                    self.assertIsNone(transform["effective"]["position"]["y"])
                    # Exact Delete button payload: it has no actor dependency.
                    deleted = command({"type": "delete_actor_template", "template_id": template_id})
                    self.assertEqual(deleted["actor_templates"], [])
                    self.assertEqual(deleted["scene"]["entities"][1]["components"]["Transform"], transform)
                    before = deepcopy(project.state())
                    for kind in ("set_transform", "clear_transform", "create_actor_template", "apply_actor_template"):
                        for invalid in (None, "", 7):
                            body = {"type": kind, "position": {"x": 10}, "axes": ["x"], "name": "Invalid", "template_id": template_id}
                            if invalid is not None:
                                body["entity_id"] = invalid
                            rejected = command(body, 400)
                            self.assertIn("entity_id", rejected["error"])
                    command({"type": "delete_actor_template", "template_id": "missing"}, 400)
                    self.assertEqual(project.state(), before)
                    # Unsupported decoder errors must return JSON, not drop the socket.
                    # Capability rejection occurs before this nonexistent disc is opened.
                    project.disc_path = str(Path(directory) / "not-read.bin")
                    before = deepcopy(project.state())
                    rejected = command({"asset_id": "asset://fixture/model/0", "clip_id": "idle"},
                                       400, "/api/animation-preview")
                    self.assertIn("support animation preview", rejected["error"])
                    self.assertEqual(project.state(), before)
                finally:
                    server.shutdown()
                    thread.join(timeout=3)
                    self.assertFalse(thread.is_alive())


if __name__ == "__main__":
    unittest.main()
