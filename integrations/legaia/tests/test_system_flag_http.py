"""Private Retail system selector Review/Apply through the real HTTP handler."""
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


@unittest.skipUnless(os.environ.get('LEGAIA_DISC_BIN'), 'Private Retail disc required')
class SystemFlagHTTP(unittest.TestCase):
    owner = 'scene://town01/actors/man-p1/0011'
    operand = 'script://town01/actors/man-p1/0011/system-flag/0016'

    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.project = ProjectService(Path(temporary.name))
        self.project.import_metadata(import_scene(os.environ['LEGAIA_DISC_BIN'], 'town01'), os.environ['LEGAIA_DISC_BIN'])
        self.project.save()
        self.server = EditorServer(('127.0.0.1', 0), self.project)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.addCleanup(self.stop)
        self.base = f'http://127.0.0.1:{self.server.server_port}'

    def stop(self):
        self.server.shutdown(); self.server.server_close(); self.thread.join(timeout=5)
        self.assertFalse(self.thread.is_alive())

    def post(self, route, body, expected=200):
        request = Request(self.base + route, data=json.dumps(body).encode(), headers={'Content-Type':'application/json'})
        try:
            with urlopen(request, timeout=30) as response:
                status, result = response.status, json.load(response)
        except HTTPError as error:
            with error: status, result = error.code, json.load(error)
        self.assertEqual(status, expected, result)
        return result

    def integrity(self):
        p = self.project
        files = {str(f.relative_to(p.root)): f.read_bytes() for f in p.root.rglob('*') if f.is_file()}
        return deepcopy((p._document(), p.imports, p.undo_stack, p.redo_stack, p.dirty, files))

    def review(self, value):
        return self.post('/api/system-flag-selector-review', {'entity':self.owner, 'operand_id':self.operand, 'value':value})

    def command(self, proposal):
        return dict(type='set_system_flag_selector', entity_id=self.owner, operand_id=self.operand,
                    value=proposal['value'], review_key=proposal['review_key'])

    def test_readonly_review_apply_clear_history_and_save_open(self):
        before = self.integrity()
        snapshot = self.post('/api/system-flag-selectors', {'entity':self.owner})
        self.assertEqual(snapshot['schema_version'], 'legaia.system-flag-authoring.v1')
        self.assertEqual(next(t for t in snapshot['targets'] if t['semantic_id']==self.operand)['current_index'],326)
        proposal = self.review({'index':4095})
        self.assertEqual(proposal['state_key'], snapshot['state_key'])
        self.assertFalse(proposal['gameplay_verified'])
        self.assertEqual(self.integrity(), before)
        self.post('/api/command', self.command(proposal))
        self.assertEqual(len(self.project.undo_stack),1)
        current = self.post('/api/system-flag-selectors', {'entity':self.owner})
        self.assertEqual(next(t for t in current['targets'] if t['semantic_id']==self.operand)['current_index'],4095)
        self.post('/api/undo', {}); self.assertEqual(self.project.overrides,{})
        self.post('/api/redo', {})
        self.project.save()
        self.assertEqual(ProjectService.open(self.project.root).overrides,self.project.overrides)
        self.post('/api/command', self.command(self.review(None)))
        self.assertEqual(self.project.overrides,{})
        self.assertEqual(self.project.imports,before[1])

    def test_invalid_stale_and_live_apply_preserve_state(self):
        proposal = self.review({'index':4095}); before = self.integrity()
        for body in ({}, {'entity':None}, {'entity':self.owner,'extra':True}):
            self.post('/api/system-flag-selectors',body,400)
        for value in ({'index':True},{'index':4096},{'index':-1},{'index':1,'offset':0}):
            self.post('/api/system-flag-selector-review',{'entity':self.owner,'operand_id':self.operand,'value':value},400)
        self.post('/api/system-flag-selector-review',{'entity':self.owner,'operand_id':None,'value':None},400)
        self.post('/api/system-flag-selector-review',{'entity':self.owner,'operand_id':self.operand.replace('/0011/','/0012/'),'value':None},400)
        self.post('/api/command',dict(self.command(proposal),review_key=None),400)
        self.post('/api/command',dict(self.command(proposal),extra=1),400)
        self.assertEqual(self.integrity(),before)
        self.post('/api/command',self.command(self.review({'index':0})))
        before = self.integrity()
        self.post('/api/command',self.command(proposal),400)
        self.assertEqual(self.integrity(),before)
        self.project.mode='live'; before=self.integrity()
        self.post('/api/command',self.command(proposal),400)
        self.assertEqual(self.integrity(),before)


if __name__=='__main__':unittest.main()
