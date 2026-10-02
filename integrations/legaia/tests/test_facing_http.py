"""Retail facing authoring through the loopback editor, without running a game."""
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
from sdk.server import EditorServer, _facing_authoring_report

class FacingReportTests(unittest.TestCase):
    def test_unavailable_source_keeps_clearable_overrides(self):
        from types import SimpleNamespace
        from unittest.mock import Mock
        from importer.core import ImportError
        owner='scene://fixture/actors/man-p1/0001';key='script://fixture/actors/man-p1/0001/facing/0005'
        project=SimpleNamespace(facing_options=Mock(side_effect=ImportError('aliased record')),overrides={owner:{'ScriptFacing':{'entries':{key:{'sector':2}}}}})
        report=_facing_authoring_report(project,owner)
        self.assertFalse(report['supported']);self.assertEqual(report['targets'],[])
        self.assertEqual(report['unresolved_overrides'],[key])

@unittest.skipUnless(os.environ.get('LEGAIA_DISC_BIN'),'requires private retail disc')
class FacingHTTPTests(unittest.TestCase):
    def test_source_layers_history_persistence_and_command_guards(self):
        private=Path(__file__).resolve().parents[3]/'local-output/sdk-20260909'
        with tempfile.TemporaryDirectory(prefix='facing-http-',dir=private) as raw:
            p=ProjectService(Path(raw));p.import_metadata(import_scene(os.environ['LEGAIA_DISC_BIN'],'town0b'),os.environ['LEGAIA_DISC_BIN'])
            imported=deepcopy(p.imports)
            server=EditorServer(('127.0.0.1',0),p);thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
            def post(route,body):
                request=Request(f'http://127.0.0.1:{server.server_port}{route}',data=json.dumps(body).encode(),headers={'Content-Type':'application/json'})
                with urlopen(request,timeout=30) as response:return json.load(response)
            try:
                owner='scene://town0b/actors/man-p1/0019'
                report=post('/api/actor-script',{'entity_id':owner})
                target=next(row for row in report['facing_authoring']['targets'] if row['pc']==17)
                self.assertEqual(target['before_raw'],0x81);self.assertEqual(target['decoded_byte_offset'],9479)
                self.assertEqual(target['values'],{'sector':1})
                command=dict(type='set_facing_target',entity_id=owner,facing_id=target['semantic_id'],values={'sector':5})
                post('/api/command',command)
                current=next(row for row in post('/api/actor-script',{'entity_id':owner})['facing_authoring']['targets'] if row['pc']==17)
                self.assertEqual(current['values'],{'sector':1});self.assertEqual(current['authored_values'],{'sector':5});self.assertEqual(current['effective_values'],{'sector':5})
                self.assertEqual(len(p.undo_stack),1)
                post('/api/command',command);self.assertEqual(len(p.undo_stack),1)
                post('/api/undo',{});self.assertEqual(p.overrides,{})
                post('/api/redo',{});self.assertIn('ScriptFacing',p.overrides[owner])
                saved=ProjectService.open(p.save());self.assertEqual(saved.overrides,p.overrides)
                for bad in [dict(command,source_offset=9479),dict(command,values={'sector':8}),dict(command,values={'sector':True}),dict(command,facing_id=target['semantic_id'].replace('/0019/','/0018/'))]:
                    before=deepcopy((p.overrides,p.undo_stack,p.redo_stack))
                    with self.assertRaises(HTTPError) as error:post('/api/command',bad)
                    self.assertEqual(error.exception.code,400);error.exception.close()
                    self.assertEqual((p.overrides,p.undo_stack,p.redo_stack),before)
                post('/api/command',dict(type='clear_facing_target',entity_id=owner,facing_id=target['semantic_id']))
                self.assertEqual(p.overrides,{})
                p2='scene://town0b/scripts/man-p2/0008'
                p2report=post('/api/partition-two-script',{'entity_id':p2})
                candidate=next(row for row in p2report['facing_authoring']['targets'] if row['pc']==207)
                self.assertEqual(candidate['mnemonic'],'NPC_RUN');self.assertEqual(candidate['target_context'],49)
                self.assertEqual(candidate['decoded_byte_offset'],31233)
                post('/api/command',dict(type='set_facing_target',entity_id=p2,facing_id=candidate['semantic_id'],values={'sector':3}))
                candidate=next(row for row in post('/api/partition-two-script',{'entity_id':p2})['facing_authoring']['targets'] if row['pc']==207)
                self.assertEqual(candidate['values'],{'sector':0});self.assertEqual(candidate['effective_values'],{'sector':3})
                post('/api/command',dict(type='clear_facing_target',entity_id=p2,facing_id=candidate['semantic_id']))
                self.assertEqual(p.overrides,{})
                self.assertEqual(p.imports,imported)
                with urlopen(f'http://127.0.0.1:{server.server_port}/script-facing.js') as response:
                    self.assertIn(b'mountScriptFacing',response.read())
            finally:
                server.shutdown();server.server_close();thread.join(timeout=5)
            self.assertFalse(thread.is_alive())

if __name__=='__main__':unittest.main()
