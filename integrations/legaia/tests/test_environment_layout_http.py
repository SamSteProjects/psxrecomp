"""Scenery layout review and atomic command HTTP boundary."""
from copy import deepcopy
from pathlib import Path
import json, tempfile, threading, unittest
from unittest.mock import patch
from urllib.request import Request, urlopen
from urllib.error import HTTPError
from sdk.project import ProjectService
from sdk.server import EditorServer
from test_project_workflow import synthetic_scene
from test_environment_group import source_map, IDS, SCENE

class EnvironmentLayoutHttp(unittest.TestCase):
    def test_review_command_history_and_strict_fields(self):
        with tempfile.TemporaryDirectory() as root:
            project = ProjectService(Path(root))
            project.import_metadata(synthetic_scene())
            saved = project.save()
            with patch.object(ProjectService, '_environment_source', return_value=source_map()):
                server = EditorServer(('127.0.0.1', 0), project)
                thread = threading.Thread(target=server.serve_forever)
                thread.start()
                try:
                    def post(route, body):
                        request = Request(f'http://127.0.0.1:{server.server_port}{route}', data=json.dumps(body).encode(), headers={'Content-Type':'application/json'})
                        try:
                            with urlopen(request, timeout=10) as response:
                                return response.status, json.load(response)
                        except HTTPError as error:
                            with error:
                                return error.code, json.load(error)
                    body = dict(entity_id=SCENE, entity_ids=IDS, operation=dict(kind='align', axis='z', anchor=IDS[0]))
                    before, saved_bytes = deepcopy(project._document()), saved.read_bytes()
                    for bad in ({}, {**body, 'extra':True}, {**body, 'operation':{'kind':'align','axis':'y','anchor':IDS[0]}}, {**body, 'operation':{'kind':'align','axis':'z','anchor':'foreign'}}):
                        self.assertEqual(post('/api/environment-layout-review', bad)[0], 400)
                    code, report = post('/api/environment-layout-review', body)
                    self.assertEqual(code, 200, report)
                    self.assertEqual(project._document(), before)
                    self.assertEqual(project.undo_stack, [])
                    command = {**body, 'type':'apply_environment_layout', 'review_key':report['review_key']}
                    self.assertEqual(post('/api/command', command)[0], 200)
                    self.assertEqual(len(project.undo_stack), 1)
                    after = deepcopy(project._document())
                    self.assertEqual(post('/api/command', command)[0], 400)
                    self.assertEqual(project._document(), after)
                    self.assertEqual(saved.read_bytes(), saved_bytes)
                    self.assertEqual(post('/api/undo', {})[0], 200)
                    self.assertEqual(project._document(), before)
                    self.assertEqual(post('/api/redo', {})[0], 200)
                    self.assertEqual(project._document(), after)
                finally:
                    server.shutdown()
                    server.server_close()
                    thread.join(timeout=5)
                self.assertFalse(thread.is_alive())
