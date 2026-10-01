"""Component review/removal uses existing history without requiring retail or runtime."""
from copy import deepcopy
import json
from pathlib import Path
import tempfile
import threading
import unittest
from urllib.error import HTTPError
from urllib.request import Request, urlopen
from sdk.project import ProjectError, ProjectService
from sdk.server import EditorServer
from test_project_workflow import synthetic_scene

OWNER = 'scene://fixture/actors/man-p1/0001'


class ComponentReviewTests(unittest.TestCase):
    def project(self, directory):
        p = ProjectService(Path(directory))
        p.import_metadata(synthetic_scene())
        p.overrides[OWNER] = {
            'Transform': {'position': {'x': 125}},
            'ScriptModelSelectors': {'entries': {
                'script://fixture/actors/man-p1/0001/model-selector/0000': {'model_selector_signed': 240}}}}
        return p

    def command(self, p, component='Transform', owner=OWNER):
        review = next(r for r in p.component_reviews(owner) if r['component'] == component)
        return dict(type='revert_authored_component', entity_id=owner,
                    component=component, review_key=review['review_key'])

    def test_review_revert_undo_redo_save_preserves_other_component_and_source(self):
        with tempfile.TemporaryDirectory() as directory:
            p = self.project(directory)
            source, before = deepcopy(p.imports), deepcopy(p.overrides)
            p.save()
            review = next(r for r in p.authored_assets() if r['id'] == OWNER)['component_reviews']
            review[0]['authored'].clear()
            self.assertEqual(p.overrides, before)
            p.command(self.command(p))
            self.assertNotIn('Transform', p.overrides[OWNER])
            self.assertEqual(p.overrides[OWNER]['ScriptModelSelectors'], before[OWNER]['ScriptModelSelectors'])
            self.assertEqual(p.state()['scene']['entities'][0]['components']['Transform']['effective']['position']['x'], 100)
            self.assertTrue(p.dirty)
            p.undo(); self.assertEqual(p.overrides, before); self.assertFalse(p.dirty)
            p.redo()
            self.assertEqual(ProjectService.open(p.save()).overrides, p.overrides)
            p.command(self.command(p, 'ScriptModelSelectors'))
            self.assertNotIn(OWNER, p.overrides)
            p.undo(); self.assertIn('ScriptModelSelectors', p.overrides[OWNER])
            self.assertEqual(p.imports, source)

    def test_stale_component_source_project_and_malformed_commands_are_atomic(self):
        with tempfile.TemporaryDirectory() as directory:
            for mutation in ('component', 'source', 'project', 'extra', 'unknown', 'live'):
                p = self.project(Path(directory)/mutation)
                cmd = self.command(p)
                if mutation == 'component': p.overrides[OWNER]['Transform']['position']['x'] = 150
                if mutation == 'source': p.imports['scene://fixture']['actors'][0]['imported_transform']['position']['x'] = 101
                if mutation == 'project': p.root = Path(directory)/'other'
                if mutation == 'extra': cmd['position'] = {'x': 0}
                if mutation == 'unknown': cmd['component'] = 'RetailMetadata'
                if mutation == 'live': p.mode = 'live'
                before = deepcopy(p.overrides)
                with self.assertRaises(ProjectError): p.command(cmd)
                self.assertEqual(p.overrides, before); self.assertFalse(p.undo_stack)

    def test_unrelated_changes_do_not_invalidate_review_but_replay_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            p = self.project(directory); cmd = self.command(p)
            p.overrides[OWNER]['ScriptModelSelectors']['entries']['script://fixture/actors/man-p1/0001/model-selector/0000']['model_selector_signed'] = 239
            p.command(cmd)
            before = deepcopy(p.overrides); depth = len(p.undo_stack)
            with self.assertRaises(ProjectError): p.command(cmd)
            self.assertEqual(p.overrides, before); self.assertEqual(len(p.undo_stack), depth)

    def test_script_and_scene_components_are_reviewable_without_changing_active_scene(self):
        with tempfile.TemporaryDirectory() as directory:
            p = self.project(directory)
            owner = 'scene://fixture/scripts/man-p2/0000'
            p.overrides[owner] = {'ScriptWaits': {'entries': {'script://fixture/scripts/man-p2/0000/wait/0000': {'duration_ticks': 3}}}}
            p.overrides['scene://fixture'] = {'Environment': {'edits': [], 'instances': []}}
            active = p.active_scene
            p.command(self.command(p, 'ScriptWaits', owner))
            p.command(self.command(p, 'Environment', 'scene://fixture'))
            self.assertEqual(p.active_scene, active)
            p.undo(); p.undo()
            self.assertIn(owner, p.overrides); self.assertIn('Environment', p.overrides['scene://fixture'])

    def test_http_review_command_and_unknown_fields(self):
        with tempfile.TemporaryDirectory() as directory:
            p = self.project(directory)
            server = EditorServer(('127.0.0.1', 0), p)
            thread = threading.Thread(target=server.serve_forever, daemon=True); thread.start()
            def post(route, body):
                request = Request(f'http://127.0.0.1:{server.server_port}{route}',
                                  data=json.dumps(body).encode(), headers={'Content-Type': 'application/json'})
                with urlopen(request, timeout=30) as response: return json.load(response)
            try:
                cmd = self.command(p)
                for body in ({**cmd, 'bytes': '00'}, {**cmd, 'review_key': None}, {**cmd, 'component': []}):
                    with self.assertRaises(HTTPError) as error: post('/api/command', body)
                    self.assertEqual(error.exception.code, 400); error.exception.close()
                result = post('/api/command', cmd)
                self.assertTrue(result['history']['can_undo'])
                self.assertEqual(next(r for r in result['authored_assets'] if r['id'] == OWNER)['component_reviews'][0]['component'], 'ScriptModelSelectors')
                post('/api/undo', {}); self.assertIn('Transform', p.overrides[OWNER])
            finally:
                server.shutdown(); server.server_close(); thread.join(timeout=5)
            self.assertFalse(thread.is_alive())


if __name__ == '__main__': unittest.main()
