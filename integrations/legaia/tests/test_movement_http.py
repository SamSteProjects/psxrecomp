"""Retail movement edits through the serialized loopback handler; no game."""
import json
import os
from pathlib import Path
import tempfile
import threading
import unittest
from urllib.request import Request, urlopen
from urllib.error import HTTPError
from importer.pipeline import import_scene
from sdk.project import ProjectService
from sdk.server import EditorServer, _movement_authoring_report


class MovementReportTests(unittest.TestCase):
    def test_unavailable_report_retains_clearable_overrides(self):
        from unittest.mock import Mock
        from types import SimpleNamespace
        from importer.core import ImportError
        owner='scene://fixture/actors/man-p1/0001';key='script://fixture/actors/man-p1/0001/movement/0005'
        project=SimpleNamespace(movement_options=Mock(side_effect=ImportError('aliased record')),
                                overrides={owner:{'ScriptMovement':{'entries':{key:{'x':128}}}}})
        report=_movement_authoring_report(project,owner)
        self.assertFalse(report['supported']);self.assertEqual(report['targets'],[])
        self.assertEqual(report['unresolved_overrides'],[key])


@unittest.skipUnless(os.environ.get('LEGAIA_DISC_BIN'),'requires private retail disc')
class MovementHTTP(unittest.TestCase):
    def test_retail_http_edit_history_and_untrusted_fields(self):
        private=Path(__file__).resolve().parents[3]/'local-output/sdk-20260909'
        with tempfile.TemporaryDirectory(prefix='movement-http-',dir=private) as directory:
            project=ProjectService(Path(directory));project.import_metadata(import_scene(os.environ['LEGAIA_DISC_BIN'],'dolk2'),os.environ['LEGAIA_DISC_BIN'])
            server=EditorServer(('127.0.0.1',0),project);thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
            def post(route,body):
                request=Request(f'http://127.0.0.1:{server.server_port}{route}',data=json.dumps(body).encode(),headers={'Content-Type':'application/json'})
                with urlopen(request,timeout=30) as response:return json.load(response)
            try:
                owner='scene://dolk2/actors/man-p1/0002'
                report=post('/api/actor-script',{'entity_id':owner})
                targets=report['movement_authoring']['targets']
                selector=next(item for item in targets if item['mnemonic']=='EXEC_MOVE')
                self.assertEqual(set(selector['values']),{'move_id'})
                target=next(item for item in targets if item['mnemonic']=='MOVE_TO' and item['values']['x']==9280)
                command={'type':'set_movement_target','entity_id':owner,'movement_id':target['semantic_id'],'values':{'x':9344}}
                post('/api/command',command)
                changed=next(item for item in post('/api/actor-script',{'entity_id':owner})['movement_authoring']['targets'] if item['semantic_id']==target['semantic_id'])
                self.assertEqual(changed['values']['x'],9280);self.assertEqual(changed['effective_values']['x'],9344)
                post('/api/undo',{});self.assertFalse(project.overrides)
                post('/api/redo',{});self.assertTrue(project.overrides)
                for body in ({**command,'source_offset':1},{**command,'values':{'x':65}},{**command,'values':{'x':True}},{**command,'movement_id':None}):
                    with self.assertRaises(HTTPError) as error:post('/api/command',body)
                    self.assertEqual(error.exception.code,400);error.exception.close()
                post('/api/command',{'type':'clear_movement_target','entity_id':owner,'movement_id':target['semantic_id']})
                self.assertFalse(project.overrides)
                partial=post('/api/partition-two-script',{'entity_id':'scene://dolk2/scripts/man-p2/0007'})
                self.assertFalse(partial['movement_authoring']['supported'])
                self.assertTrue(partial['inspection']['instructions'])
            finally:
                server.shutdown();server.server_close();thread.join(timeout=5)
            self.assertFalse(thread.is_alive())
