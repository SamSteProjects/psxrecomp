"""Loopback collision review/apply contracts without a retail disc or runtime."""
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


RECTANGLE = dict(row_start=1, row_end=2, column_start=0, column_end=1,
                 quadrant='all', blocked=True)


class CollisionRectangleHttpTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.project = ProjectService(Path(self.directory.name))
        self.project.import_metadata(synthetic_scene())
        self.project.save()
        self.source = bytes([0x0a]) * 0x12000
        self.source_patch = patch.object(ProjectService, '_environment_source',
                                        side_effect=lambda _scene: self.source)
        self.source_patch.start()
        self.addCleanup(self.source_patch.stop)
        self.server = EditorServer(('127.0.0.1', 0), self.project)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.addCleanup(self.stop_server)

    def stop_server(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=5)
        self.assertFalse(self.thread.is_alive())

    def post(self, route, body):
        request = Request(f'http://127.0.0.1:{self.server.server_port}{route}',
                          data=json.dumps(body).encode(),
                          headers={'Content-Type': 'application/json'})
        try:
            with urlopen(request, timeout=10) as response:
                return response.status, json.load(response)
        except HTTPError as error:
            with error:
                return error.code, json.load(error)

    def snapshot(self):
        return deepcopy((self.project._document(), self.project.undo_stack,
                         self.project.redo_stack, self.project.saved_digest)), {
            str(path.relative_to(self.project.root)): path.read_bytes()
            for path in self.project.root.rglob('*') if path.is_file()
        }

    def review(self, rectangle=None):
        status, report = self.post('/api/collision-rectangle-review', {
            'entity_id': self.project.active_scene,
            'rectangle': RECTANGLE if rectangle is None else rectangle,
        })
        self.assertEqual(status, 200, report)
        return report

    def command(self, report, **changes):
        return dict(type='apply_collision_rectangle', entity_id=report['scene_id'],
                    rectangle=report['rectangle'], review_key=report['review_key'],
                    **changes)

    def assert_rejected_unchanged(self, route, body):
        before = self.snapshot()
        status, result = self.post(route, body)
        self.assertEqual(status, 400, result)
        self.assertEqual(self.snapshot(), before)

    def test_review_whitelist_bounds_and_edit_mode_are_read_only(self):
        valid = dict(entity_id=self.project.active_scene, rectangle=RECTANGLE)
        for body in ({}, {'rectangle': RECTANGLE}, {**valid, 'output_path': 'other'},
                     {**valid, 'entity_id': 'scene://missing'}):
            with self.subTest(body=body):
                self.assert_rejected_unchanged('/api/collision-rectangle-review', body)
        for rectangle in ({**RECTANGLE, 'row_start': 0},
                          {**RECTANGLE, 'column_start': 2},
                          {**RECTANGLE, 'quadrant': True},
                          {**RECTANGLE, 'blocked': 1},
                          {**RECTANGLE, 'extra': True},
                          {**RECTANGLE, 'row_end': 127, 'column_end': 127}):
            with self.subTest(rectangle=rectangle):
                self.assert_rejected_unchanged('/api/collision-rectangle-review',
                                               {**valid, 'rectangle': rectangle})
        before = self.snapshot()
        report = self.review()
        self.assertEqual(report['wall_bit_count'], 16)
        self.assertEqual(report['effective_change_count'], 16)
        self.assertFalse(report['gameplay_verified'])
        self.assertEqual(self.snapshot(), before)
        self.project.mode = 'live'
        self.assert_rejected_unchanged('/api/collision-rectangle-review', valid)
        self.assert_rejected_unchanged('/api/command', self.command(report))

    def test_apply_is_one_history_entry_and_undo_redo_do_not_write_files(self):
        before = self.snapshot()
        report = self.review()
        status, result = self.post('/api/command', self.command(report))
        self.assertEqual(status, 200, result)
        self.assertEqual(len(self.project.undo_stack), 1)
        self.assertEqual(len(self.project.overrides[self.project.active_scene]['Collision']['edits']), 16)
        self.assertTrue(self.project.dirty)
        applied = deepcopy(self.project.overrides)
        self.assertEqual(self.snapshot()[1], before[1])
        self.assertEqual(self.post('/api/undo', {})[0], 200)
        self.assertEqual(self.project.overrides, {})
        self.assertFalse(self.project.dirty)
        self.assertEqual(self.post('/api/redo', {})[0], 200)
        self.assertEqual(self.project.overrides, applied)
        self.assertEqual(len(self.project.undo_stack), 1)
        self.assertEqual(self.snapshot()[1], before[1])

    def test_stale_document_source_and_changed_proposal_cannot_apply(self):
        report = self.review()
        self.project.name = 'Unsaved name change'
        self.assert_rejected_unchanged('/api/command', self.command(report))
        report = self.review()
        changed = self.command(report)
        changed['rectangle'] = {**RECTANGLE, 'blocked': False}
        self.assert_rejected_unchanged('/api/command', changed)
        self.assert_rejected_unchanged('/api/command', {**self.command(report), 'value': report['value']})
        self.source = bytes([0x0b]) * 0x12000
        self.assert_rejected_unchanged('/api/command', self.command(report))

    def test_unavailable_or_changed_bound_source_rejects_without_mutation(self):
        with patch.object(ProjectService, '_environment_source',
                          side_effect=ProjectError('Source unavailable')):
            self.assert_rejected_unchanged('/api/collision-rectangle-review',
                                          dict(entity_id=self.project.active_scene, rectangle=RECTANGLE))
        report = self.review()
        self.assertEqual(self.post('/api/command', self.command(report))[0], 200)
        self.source = bytes([0x0b]) * 0x12000
        self.assert_rejected_unchanged('/api/collision-rectangle-review',
                                      dict(entity_id=self.project.active_scene, rectangle=RECTANGLE))
        self.assert_rejected_unchanged('/api/command', self.command(report))

    def test_noop_apply_preserves_history_and_redo(self):
        report = self.review({**RECTANGLE, 'blocked': False})
        self.assertFalse(report['project_change'])
        before = self.snapshot()
        self.assertEqual(self.post('/api/command', self.command(report))[0], 200)
        self.assertEqual(self.snapshot(), before)
        report = self.review()
        self.assertEqual(self.post('/api/command', self.command(report))[0], 200)
        self.assertEqual(self.post('/api/undo', {})[0], 200)
        report = self.review({**RECTANGLE, 'blocked': False})
        before = self.snapshot()
        self.assertEqual(self.post('/api/command', self.command(report))[0], 200)
        self.assertEqual(self.snapshot(), before)


if __name__ == '__main__':
    unittest.main()
