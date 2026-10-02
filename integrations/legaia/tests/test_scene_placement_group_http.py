"""Mixed placement review and atomic history through the loopback HTTP API."""
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
from test_environment_group import SCENE, IDS, source_map
from test_project_workflow import synthetic_scene

ACTOR = 'scene://fixture/actors/man-p1/0001'
MIXED = [ACTOR, IDS[0]]


class ScenePlacementGroupHttpTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.project = ProjectService(Path(self.directory.name))
        document = synthetic_scene()
        document['actors'][0]['imported_transform']['position'].update(x=128, z=256)
        self.project.import_metadata(document)
        self.project.save()
        self.source = source_map()
        source_patch = patch.object(ProjectService, '_environment_source',
                                    side_effect=lambda _scene: self.source)
        source_patch.start()
        self.addCleanup(source_patch.stop)
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
                         self.project.redo_stack, self.project.saved_digest)), {
            str(path.relative_to(self.project.root)): path.read_bytes()
            for path in self.project.root.rglob('*') if path.is_file()
        }

    def body(self, delta=None):
        return dict(entity_id=SCENE, entity_ids=MIXED,
                    delta=dict(x=64, z=64) if delta is None else delta)

    def review(self, delta=None):
        status, report = self.post('/api/scene-placement-group-review', self.body(delta))
        self.assertEqual(status, 200, report)
        return report

    def command(self, report):
        return dict(type='apply_scene_placement_group', entity_id=report['scene_id'],
                    entity_ids=report['entity_ids'], delta=report['delta'],
                    review_key=report['review_key'])

    def assert_rejected_unchanged(self, route, body):
        before = self.snapshot()
        status, result = self.post(route, body)
        self.assertEqual(status, 400, result)
        self.assertEqual(self.snapshot(), before)

    def test_review_strict_fields_selection_and_edit_mode_are_read_only(self):
        valid = self.body()
        for body in ({}, {**valid, 'extra': True}, {**valid, 'entity_id': 'scene://missing'},
                     {**valid, 'entity_ids': [ACTOR]}, {**valid, 'entity_ids': IDS},
                     {**valid, 'delta': dict(x=1, z=0)},
                     {**valid, 'delta': dict(x=True, z=0)}):
            with self.subTest(body=body):
                self.assert_rejected_unchanged('/api/scene-placement-group-review', body)
        before = self.snapshot()
        report = self.review()
        self.assertEqual(report['schema_version'], 'legaia.scene-placement-group-review.v1')
        self.assertEqual(report['affected_count'], 2)
        self.assertEqual({target['kind'] for target in report['targets']}, {'actor', 'decoration'})
        self.assertFalse(report['gameplay_verified'])
        self.assertEqual(self.snapshot(), before)
        self.project.mode = 'live'
        self.assert_rejected_unchanged('/api/scene-placement-group-review', valid)
        self.assert_rejected_unchanged('/api/command', self.command(report))

    def test_apply_and_undo_redo_update_both_owners_in_one_step_without_file_writes(self):
        before = self.snapshot()
        report = self.review()
        code, result = self.post('/api/command', self.command(report))
        self.assertEqual(code, 200, result)
        self.assertEqual(len(self.project.undo_stack), 1)
        self.assertEqual(set(self.project.undo_stack[0]['entity_ids']), {ACTOR, SCENE})
        self.assertEqual(self.project.overrides[ACTOR]['Transform']['position'], dict(x=192, z=320))
        self.assertEqual(self.project.overrides[SCENE]['Environment']['instances'][0]['cell_index'], 129)
        applied = deepcopy(self.project.overrides)
        self.assertTrue(self.project.dirty)
        self.assertEqual(self.snapshot()[1], before[1])
        self.assertEqual(self.post('/api/undo', {})[0], 200)
        undone = self.snapshot()
        self.assertEqual(undone[0][0], before[0][0])
        self.assertEqual(undone[0][1], before[0][1])
        self.assertEqual(undone[0][3], before[0][3])
        self.assertEqual(undone[1], before[1])
        self.assertEqual(len(self.project.redo_stack), 1)
        self.assertFalse(self.project.dirty)
        self.assertEqual(self.post('/api/redo', {})[0], 200)
        self.assertEqual(self.project.overrides, applied)
        self.assertEqual(len(self.project.undo_stack), 1)
        self.assertEqual(self.snapshot()[1], before[1])

    def test_stale_project_source_or_proposal_and_extra_apply_fields_reject_atomically(self):
        report = self.review()
        self.project.name = 'Unsaved name change'
        self.assert_rejected_unchanged('/api/command', self.command(report))
        report = self.review()
        command = self.command(report)
        self.assert_rejected_unchanged('/api/command', {**command, 'delta': dict(x=128, z=64)})
        self.assert_rejected_unchanged('/api/command', {**command, 'changes': report['changes']})
        changed = bytearray(self.source)
        changed[0x4000] ^= 1
        self.source = bytes(changed)
        self.assert_rejected_unchanged('/api/command', command)

    def test_noop_apply_preserves_existing_redo_and_saved_state(self):
        report = self.review()
        self.assertEqual(self.post('/api/command', self.command(report))[0], 200)
        self.assertEqual(self.post('/api/undo', {})[0], 200)
        report = self.review(dict(x=0, z=0))
        self.assertFalse(report['project_change'])
        before = self.snapshot()
        self.assertEqual(self.post('/api/command', self.command(report))[0], 200)
        self.assertEqual(self.snapshot(), before)


if __name__ == '__main__':
    unittest.main()
