"""Read-only NPC output review source/lifecycle guards and actual HTTP routing."""
from hashlib import sha256
from pathlib import Path
import json
import tempfile
import threading
import unittest
from unittest.mock import patch
from urllib.request import Request, urlopen
from urllib.error import HTTPError

from sdk.build import authored_state_key
from sdk.draft_review import review
from sdk.project import ProjectError, ProjectService
from sdk.server import EditorServer


class DraftReviewTests(unittest.TestCase):
    def fixture(self, directory):
        project = ProjectService(Path(directory))
        project.actor_drafts = {'draft': {'scene_id': 'scene://fixture'}}
        key = authored_state_key(project)
        archive = b'qualified archive candidate'
        audit = dict(authored_state_key=key, source_disc_sha256='a'*64,
            source_prot_sha256='b'*64, result_prot_sha256=sha256(archive).hexdigest(),
            container={}, scenes={'scene://fixture':dict(
                final_man_sha256='c'*64, facing_changes=[])})
        return project, key, archive, audit

    def test_review_is_metadata_only_and_preserves_project_files_history(self):
        with tempfile.TemporaryDirectory() as directory:
            project,key,archive,audit=self.fixture(directory)
            before=authored_state_key(project), list(project.undo_stack), list(project.root.iterdir())
            with patch('sdk.draft_build.prepare_draft_archive',return_value=(archive,audit)):
                result=review(project,key)
            self.assertFalse(result['output_written'])
            self.assertFalse(result['normal_build_ready'])
            self.assertFalse(result['gameplay_verified'])
            self.assertEqual(result['draft_count'],1)
            self.assertNotIn('payload',json.dumps(result))
            self.assertEqual(before,(authored_state_key(project),list(project.undo_stack),list(project.root.iterdir())))

    def test_source_mode_empty_and_changed_candidate_reject(self):
        with tempfile.TemporaryDirectory() as directory:
            project,key,archive,audit=self.fixture(directory)
            with patch('sdk.draft_build.prepare_draft_archive',return_value=(archive,audit)) as prepare:
                for bad in (None,'stale','f'*64):
                    with self.assertRaises(ProjectError):review(project,bad)
                project.mode='live'
                with self.assertRaises(ProjectError):review(project,key)
                self.assertEqual(prepare.call_count,0)
                project.mode='edit'
                with patch('sdk.draft_build.prepare_draft_archive',return_value=(b'other',audit)):
                    with self.assertRaisesRegex(ProjectError,'candidate'):review(project,key)
                project.actor_drafts.clear()
                with self.assertRaises(ProjectError):review(project,authored_state_key(project))

    def test_mid_read_changes_withdraw_result(self):
        with tempfile.TemporaryDirectory() as directory:
            project,key,archive,audit=self.fixture(directory)
            def prepare(_project):
                _project.mode='live'
                return archive,audit
            with patch('sdk.draft_build.prepare_draft_archive',side_effect=prepare):
                with self.assertRaisesRegex(ProjectError,'during'):review(project,key)

    def test_single_scene_audit_without_nested_drafts(self):
        with tempfile.TemporaryDirectory() as directory:
            project,key,archive,audit=self.fixture(directory)
            scene=audit.pop('scenes')['scene://fixture']
            audit.update(scene,scene_id='scene://fixture')
            with patch('sdk.draft_build.prepare_draft_archive',return_value=(archive,audit)):
                result=review(project,key)
            self.assertEqual(result['scenes'][0]['draft_count'],1)

    def test_http_exact_request_and_no_export_writer(self):
        with tempfile.TemporaryDirectory() as directory:
            project,key,archive,audit=self.fixture(directory)
            server=EditorServer(('127.0.0.1',0),project)
            thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
            def post(body):
                request=Request(f'http://127.0.0.1:{server.server_port}/api/draft-output-review',data=json.dumps(body).encode(),headers={'Content-Type':'application/json'})
                with urlopen(request,timeout=5) as response:return json.load(response)
            try:
                with patch('sdk.draft_build.prepare_draft_archive',return_value=(archive,audit)), patch('sdk.draft_build.export_draft_disc') as writer:
                    self.assertFalse(post({'source_key':key})['output_written'])
                    for body in ({},{'source_key':key,'output':'outside'},{'source_key':'f'*64}):
                        with self.assertRaises(HTTPError) as error:post(body)
                        self.assertEqual(error.exception.code,400);error.exception.close()
                    writer.assert_not_called()
                    self.assertIsNone(server.last_build)
            finally:
                server.shutdown();server.server_close();thread.join(5)
