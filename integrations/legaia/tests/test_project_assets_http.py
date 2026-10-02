"""Project inventory dispatch is read-only; empty editor state remains usable."""
from copy import deepcopy
import json
from pathlib import Path
import tempfile
import threading
import unittest
from unittest.mock import patch
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from sdk.project import ProjectError, ProjectService
from sdk.server import EditorServer
from test_project_workflow import synthetic_scene


class ProjectAssetsHttpTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.project = ProjectService(Path(self.directory.name))
        self.server = EditorServer(('127.0.0.1', 0), self.project)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.addCleanup(self.stop)

    def stop(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(5)
        self.assertFalse(self.thread.is_alive())

    def request(self, route, body=None):
        request = Request(f'http://127.0.0.1:{self.server.server_port}{route}',
                          data=None if body is None else json.dumps(body).encode(),
                          headers={'Content-Type': 'application/json'})
        try:
            with urlopen(request, timeout=10) as response:
                return response.status, json.load(response)
        except HTTPError as error:
            with error:
                return error.code, json.load(error)

    def test_empty_project_state_and_strict_read_only_dispatch(self):
        status, state = self.request('/api/state')
        self.assertEqual(status, 200)
        self.assertIsNone(state['project_assets_source_key'])
        self.assertFalse(state['capabilities']['project_assets'])
        before = deepcopy((self.project._document(), self.project.selected,
                           self.project.undo_stack, self.project.redo_stack))
        with patch('sdk.project_assets.inspect', return_value={'qualified': True}) as discover:
            self.assertEqual(self.request('/api/project-assets', {}), (200, {'qualified': True}))
            discover.assert_called_once_with(self.project)
            discover.reset_mock()
            for body in [{'scene_id': 'scene://fixture'}, {'write': True}, [], 1, True]:
                self.assertEqual(self.request('/api/project-assets', body)[0], 400)
            discover.assert_not_called()
        self.assertEqual(before, (self.project._document(), self.project.selected,
                                 self.project.undo_stack, self.project.redo_stack))

    def test_index_budget_failure_does_not_break_existing_editor_state(self):
        self.project.import_metadata(synthetic_scene(), 'C:/private/not-a-disc.bin')
        with patch('sdk.project_assets.source_key', side_effect=ProjectError('Project index exceeds its metadata budget')):
            status, state = self.request('/api/state')
        self.assertEqual(status, 200)
        self.assertFalse(state['capabilities']['project_assets'])
        self.assertIsNone(state['project_assets_source_key'])
        self.assertEqual(state['project_assets_unavailable_reason'], 'Project index exceeds its metadata budget')
        self.assertEqual(state['scene']['id'], 'scene://fixture')


if __name__ == '__main__':
    unittest.main()
