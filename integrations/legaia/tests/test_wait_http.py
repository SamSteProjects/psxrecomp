"""Retail wait edits through the serialized loopback handler; no game."""
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
from sdk.server import EditorServer, _wait_authoring_report


class WaitReportTests(unittest.TestCase):
    def test_unavailable_report_retains_clearable_overrides(self):
        from unittest.mock import Mock
        from types import SimpleNamespace
        from importer.core import ImportError
        owner='scene://fixture/actors/man-p1/0001';key='script://fixture/actors/man-p1/0001/wait/0005'
        project=SimpleNamespace(wait_options=Mock(side_effect=ImportError('aliased record')),
                                overrides={owner:{'ScriptWaits':{'entries':{key:{'duration_ticks':3}}}}})
        report=_wait_authoring_report(project,owner)
        self.assertFalse(report['supported']);self.assertEqual(report['targets'],[])
        self.assertEqual(report['unresolved_overrides'],[key])


@unittest.skipUnless(os.environ.get('LEGAIA_DISC_BIN'),'requires private retail disc')
class WaitHTTP(unittest.TestCase):
    def test_retail_http_edit_history_and_untrusted_fields(self):
        private=Path(__file__).resolve().parents[3]/'local-output/sdk-20260909'
        with tempfile.TemporaryDirectory(prefix='wait-http-',dir=private) as directory:
            project=ProjectService(Path(directory));project.import_metadata(import_scene(os.environ['LEGAIA_DISC_BIN'],'town01'),os.environ['LEGAIA_DISC_BIN'])
            server=EditorServer(('127.0.0.1',0),project);thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
            def post(route,body):
                request=Request(f'http://127.0.0.1:{server.server_port}{route}',data=json.dumps(body).encode(),headers={'Content-Type':'application/json'})
                with urlopen(request,timeout=30) as response:return json.load(response)
            try:
                owner='scene://town01/actors/man-p1/0044'
                report=post('/api/actor-script',{'entity_id':owner})
                target=next(item for item in report['wait_authoring']['targets'] if item['mnemonic']=='WAIT_FRAMES' and item['values']['duration_ticks']==16)
                command={'type':'set_wait_target','entity_id':owner,'wait_id':target['semantic_id'],'values':{'duration_ticks':17}}
                post('/api/command',command)
                changed=next(item for item in post('/api/actor-script',{'entity_id':owner})['wait_authoring']['targets'] if item['semantic_id']==target['semantic_id'])
                self.assertEqual(changed['values']['duration_ticks'],16);self.assertEqual(changed['effective_values']['duration_ticks'],17)
                post('/api/undo',{});self.assertFalse(project.overrides)
                post('/api/redo',{});self.assertTrue(project.overrides)
                for body in ({**command,'source_offset':1},{**command,'values':{'duration_ticks':32768}},{**command,'values':{'duration_ticks':True}},{**command,'values':{'duration_ticks':-1}},{**command,'wait_id':None}):
                    with self.assertRaises(HTTPError) as error:post('/api/command',body)
                    self.assertEqual(error.exception.code,400);error.exception.close()
                post('/api/command',{'type':'clear_wait_target','entity_id':owner,'wait_id':target['semantic_id']})
                self.assertFalse(project.overrides)
                partial=post('/api/partition-two-script',{'entity_id':'scene://town01/scripts/man-p2/0007'})
                self.assertFalse(partial['wait_authoring']['supported'])
                self.assertTrue(partial['inspection']['instructions'])
            finally:
                server.shutdown();server.server_close();thread.join(timeout=5)
            self.assertFalse(thread.is_alive())
