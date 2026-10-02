"""Opt-in retail branch review and history through the loopback HTTP handler.

Each test imports the unchanged private disc into its own temporary project.
There is no runtime connection, game launch, or write to a user project.
"""
from copy import deepcopy
import json
import os
from pathlib import Path
import tempfile
import threading
import unittest
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from importer.pipeline import import_scene
from sdk.project import ProjectService
from sdk.server import EditorServer


@unittest.skipUnless(os.environ.get('LEGAIA_DISC_BIN'), 'requires unchanged private retail disc')
class ScriptBranchHTTP(unittest.TestCase):
    OWNER = 'scene://town01/actors/man-p1/0002'
    BRANCH = 'script://town01/actors/man-p1/0002/branch/001f'
    VALUE = {'target_pc': 11}

    def setUp(self):
        private = Path(__file__).resolve().parents[3] / 'local-output/sdk-20260909'
        temporary = tempfile.TemporaryDirectory(prefix='script-branch-http-', dir=private)
        self.addCleanup(temporary.cleanup)
        self.project = ProjectService(Path(temporary.name))
        self.project.import_metadata(import_scene(os.environ['LEGAIA_DISC_BIN'], 'town01'),
                                     os.environ['LEGAIA_DISC_BIN'])
        self.project.save()
        self.server = EditorServer(('127.0.0.1', 0), self.project)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.addCleanup(self.stop_server)
        self.base = f'http://127.0.0.1:{self.server.server_port}'

    def stop_server(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=5)
        self.assertFalse(self.thread.is_alive())

    def post(self, route, body):
        request = Request(self.base + route, data=json.dumps(body).encode('utf-8'),
                          headers={'Content-Type': 'application/json'})
        try:
            with urlopen(request, timeout=30) as response:
                return response.status, json.load(response)
        except HTTPError as error:
            with error:
                return error.code, json.load(error)

    def ok(self, route, body):
        status, result = self.post(route, body)
        self.assertEqual(status, 200, result)
        return result

    def saved_files(self):
        # This newly created test project contains only bounded metadata files.
        return {str(path.relative_to(self.project.root)): path.read_bytes()
                for path in self.project.root.rglob('*') if path.is_file()}

    def integrity(self):
        project = self.project
        return deepcopy((project.imports, project.overrides, project.undo_stack,
                         project.redo_stack, project.saved_digest, project.saved_sections,
                         project.name, project.active_scene, project.mode,
                         project.dirty, self.saved_files()))

    def review_body(self, value=None):
        return {'entity': self.OWNER, 'branch_id': self.BRANCH,
                'value': deepcopy(self.VALUE if value is None else value)}

    def command(self, report, value=None):
        return {'type': 'set_branch', **self.review_body(value),
                'review_key': report['review']['review_key']}

    def selected(self, snapshot):
        return next(row for row in snapshot['targets'] if row['semantic_id'] == self.BRANCH)

    def test_review_is_read_only_and_serves_the_browser_module(self):
        baseline = self.integrity()
        with urlopen(self.base + '/script-branches.js', timeout=30) as response:
            self.assertEqual(response.status, 200)
            self.assertEqual(response.headers.get_content_type(), 'text/javascript')
            self.assertIn(b'export function mountScriptBranches', response.read())
        snapshot = self.ok('/api/script-branches', {'entity': self.OWNER})
        self.assertEqual(snapshot['schema_version'], 'legaia.script-branches.v1')
        self.assertEqual(snapshot['owner_id'], self.OWNER)
        self.assertTrue(snapshot['supported'])
        self.assertFalse(snapshot['gameplay_verified'])
        target = self.selected(snapshot)
        self.assertEqual((target['target_pc'], target['current_target_pc'], target['authored_value']),
                         (15, 15, None))
        self.assertEqual(target['source_record_sha256'], snapshot['source_record_sha256'])
        proposal = self.ok('/api/script-branch-review', self.review_body())
        self.assertEqual(proposal['state_key'], snapshot['state_key'])
        self.assertEqual(proposal['source_record_sha256'], snapshot['source_record_sha256'])
        self.assertEqual(proposal['source_report'], snapshot['source_report'])
        self.assertEqual(proposal['current_report'], snapshot['current_report'])
        self.assertFalse(proposal['review']['no_op'])
        self.assertFalse(proposal['gameplay_verified'])
        audit, = proposal['review']['audit']
        self.assertEqual((audit['before'], audit['after'], audit['byte_length']), (15, 11, 2))
        self.assertEqual(audit['changed_byte_offsets'], [4791])
        self.assertEqual(audit['scope'], 'script-branch-target-only')
        proposed_branch = next(row for row in proposal['review']['proposed_report']['instructions']
                               if row['pc'] == 0x1f)
        self.assertEqual(proposed_branch['successors'], [{'pc': 11, 'condition': 'unconditional'}])
        self.assertEqual(self.selected(proposal)['current_target_pc'], 15)
        no_op = self.ok('/api/script-branch-review', self.review_body({'target_pc': 15}))
        self.assertTrue(no_op['review']['no_op'])
        self.assertEqual(no_op['review']['audit'], [])
        self.assertEqual(self.integrity(), baseline)

    def test_malformed_foreign_interior_and_stale_apply_leave_evidence_and_history_unchanged(self):
        proposal = self.ok('/api/script-branch-review', self.review_body())
        command = self.command(proposal)
        baseline = self.integrity()
        invalid_reviews = [
            {}, {'entity': self.OWNER, 'branch_id': self.BRANCH},
            {**self.review_body(), 'source_key': proposal['state_key']},
            {**self.review_body(), 'entity': None},
            {**self.review_body(), 'branch_id': self.BRANCH.replace('/0002/', '/0003/')},
            {**self.review_body(), 'entity': self.OWNER.replace('town01', 'dolk2')},
            {**self.review_body(), 'value': {'target_pc': 16}},  # inside a retail MES payload
            {**self.review_body(), 'value': {'target_pc': True}},
            {**self.review_body(), 'value': {'target_pc': 32768}},
            {**self.review_body(), 'value': {'target_pc': 11, 'byte_offset': 0}},
        ]
        invalid_commands = [
            {key: value for key, value in command.items() if key != 'review_key'},
            {**command, 'source_key': proposal['state_key']},
            {**command, 'review_key': None},
            {**command, 'review_key': '0' * 64},
            {**command, 'branch_id': self.BRANCH.replace('/0002/', '/0003/')},
            {**command, 'value': {'target_pc': 16}},
            {**command, 'value': {'target_pc': 15}},  # value differs from the reviewed proposal
        ]
        for route, bodies in (('/api/script-branches', ({'entity': self.OWNER, 'value': None},)),
                              ('/api/script-branch-review', invalid_reviews),
                              ('/api/command', invalid_commands)):
            for body in bodies:
                with self.subTest(route=route, body=body):
                    status, error = self.post(route, body)
                    self.assertEqual(status, 400, error)
                    self.assertIsInstance(error['error'], str)
                    self.assertEqual(self.integrity(), baseline)
        # A valid ordinary operand command changes the same owner's current
        # script/source key; the old branch review must then become unusable.
        inspected = self.ok('/api/actor-script', {'entity_id': self.OWNER})
        flag = next(row for row in inspected['flag_authoring']['targets'] if row['mnemonic'] == 'CFLAG_SET')
        self.ok('/api/command', {'type': 'set_flag_bit', 'entity_id': self.OWNER,
                                'flag_id': flag['semantic_id'], 'values': {'bit': 3}})
        changed = self.ok('/api/script-branches', {'entity': self.OWNER})
        self.assertNotEqual(changed['state_key'], proposal['state_key'])
        self.assertEqual(self.saved_files(), baseline[-1])
        after_flag = self.integrity()
        status, error = self.post('/api/command', command)
        self.assertEqual(status, 400, error)
        self.assertIn('changed', error['error'])
        self.assertEqual(self.integrity(), after_flag)
        self.assertNotIn('ScriptBranches', self.project.overrides.get(self.OWNER, {}))

    def test_reviewed_apply_reset_save_and_ordinary_history_preserve_imports(self):
        imported = deepcopy(self.project.imports)
        files = self.saved_files()
        original = self.ok('/api/script-branches', {'entity': self.OWNER})
        proposal = self.ok('/api/script-branch-review', self.review_body())
        applied = self.ok('/api/command', self.command(proposal))
        authored = {self.OWNER: {'ScriptBranches': {'entries': {self.BRANCH: self.VALUE}}}}
        self.assertEqual(self.project.overrides, authored)
        self.assertEqual((len(self.project.undo_stack), len(self.project.redo_stack)), (1, 0))
        self.assertNotEqual(applied['script_authoring_state_key'], original['state_key'])
        self.assertTrue(self.project.dirty)
        self.assertEqual(self.saved_files(), files)
        current = self.ok('/api/script-branches', {'entity': self.OWNER})
        self.assertEqual(current['source_report'], original['source_report'])
        self.assertEqual((self.selected(current)['target_pc'], self.selected(current)['current_target_pc']), (15, 11))
        self.ok('/api/undo', {})
        self.assertFalse(self.project.overrides)
        self.assertFalse(self.project.dirty)
        self.assertEqual((len(self.project.undo_stack), len(self.project.redo_stack)), (0, 1))
        self.ok('/api/redo', {})
        self.assertEqual(self.project.overrides, authored)
        self.ok('/api/project/save', {})
        reopened = ProjectService.open(self.project.root)
        self.assertEqual(reopened.overrides, authored)
        self.assertEqual(reopened.imports, imported)
        self.assertFalse(self.project.dirty)
        clear_body = {'entity': self.OWNER, 'branch_id': self.BRANCH, 'value': None}
        reset = self.ok('/api/script-branch-review', clear_body)
        reset_audit, = reset['review']['audit']
        self.assertEqual((reset_audit['before'], reset_audit['after']), (11, 15))
        self.assertEqual(reset_audit['changed_byte_offsets'], [4791])
        self.ok('/api/command', {'type': 'set_branch', **clear_body,
                                'review_key': reset['review']['review_key']})
        self.assertFalse(self.project.overrides)
        self.assertEqual((len(self.project.undo_stack), len(self.project.redo_stack)), (2, 0))
        self.ok('/api/undo', {})
        self.assertEqual(self.project.overrides, authored)
        self.ok('/api/redo', {})
        self.assertFalse(self.project.overrides)
        restored = self.ok('/api/script-branches', {'entity': self.OWNER})
        self.assertEqual(self.selected(restored)['current_target_pc'], 15)
        self.assertEqual(restored['source_record_sha256'], original['source_record_sha256'])
        self.assertEqual(self.project.imports, imported)
        self.ok('/api/project/save', {})
        reopened = ProjectService.open(self.project.root)
        self.assertFalse(reopened.overrides)
        self.assertEqual(reopened.imports, imported)


if __name__ == '__main__':
    unittest.main()
