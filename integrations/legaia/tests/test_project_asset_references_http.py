"""Asset reference scope dispatch must remain read-only and strictly shaped."""
from copy import deepcopy
import json
from pathlib import Path
import tempfile
import threading
import unittest
from unittest.mock import patch
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from sdk.project import ProjectService
from sdk.server import EditorServer
from test_project_workflow import synthetic_scene


class ProjectAssetReferenceHttpTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.project = ProjectService(Path(self.directory.name))
        self.project.import_metadata(synthetic_scene())
        self.project.save()
        self.server = EditorServer(('127.0.0.1', 0), self.project)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.addCleanup(self.stop)

    def stop(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=5)
        self.assertFalse(self.thread.is_alive())

    def post(self, body):
        request = Request(f'http://127.0.0.1:{self.server.server_port}/api/asset-references',
                          data=json.dumps(body).encode('utf-8'),
                          headers={'Content-Type': 'application/json'})
        try:
            with urlopen(request, timeout=10) as response:
                return response.status, json.load(response)
        except HTTPError as error:
            with error:
                return error.code, json.load(error)

    def snapshot(self):
        return deepcopy((self.project._document(), self.project.undo_stack,
                         self.project.redo_stack, self.project.saved_digest,
                         self.project.active_scene, self.project.selected)), {
            str(path.relative_to(self.project.root)): path.read_bytes()
            for path in self.project.root.rglob('*') if path.is_file()
        }

    def test_default_active_and_explicit_project_dispatch_preserve_state(self):
        before = self.snapshot()
        with patch('sdk.asset_references.inspect', return_value={'scope': 'active'}) as active, \
             patch('sdk.asset_references.inspect_project', return_value={'scope': 'project'}) as project:
            self.assertEqual(self.post({'asset_id': 'scene://fixture'}), (200, {'scope': 'active'}))
            self.assertEqual(self.post({'asset_id': 'scene://fixture', 'scope': 'active'}), (200, {'scope': 'active'}))
            self.assertEqual(self.post({'asset_id': 'scene://fixture', 'scope': 'project'}), (200, {'scope': 'project'}))
            self.assertEqual(active.call_count, 2)
            project.assert_called_once_with(self.project, 'scene://fixture')
        self.assertEqual(before, self.snapshot())

    def test_malformed_scope_and_extra_fields_reject_before_discovery(self):
        before = self.snapshot()
        with patch('sdk.asset_references.inspect') as active, patch('sdk.asset_references.inspect_project') as project:
            for body in [{}, {'scope': 'project'}, {'asset_id': 'scene://fixture', 'write': True},
                         *[{'asset_id': 'scene://fixture', 'scope': scope} for scope in [None, True, 1, [], {}, '', 'all', 'PROJECT']]]:
                with self.subTest(body=body):
                    self.assertEqual(self.post(body)[0], 400)
            active.assert_not_called()
            project.assert_not_called()
        self.assertEqual(before, self.snapshot())
