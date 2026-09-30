"""Retail flag edits through the serialized loopback handler; no game."""
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
from sdk.server import EditorServer, _flag_authoring_report


class FlagReportTests(unittest.TestCase):
    def test_unavailable_report_retains_clearable_overrides(self):
        from unittest.mock import Mock
        from types import SimpleNamespace
        from importer.core import ImportError
        owner='scene://fixture/actors/man-p1/0001';key='script://fixture/actors/man-p1/0001/flag-bit/0005'
        project=SimpleNamespace(flag_options=Mock(side_effect=ImportError('aliased record')),
                                overrides={owner:{'ScriptFlags':{'entries':{key:{'bit':3}}}}})
        report=_flag_authoring_report(project,owner)
        self.assertFalse(report['supported']);self.assertEqual(report['targets'],[])
        self.assertEqual(report['unresolved_overrides'],[key])


@unittest.skipUnless(os.environ.get('LEGAIA_DISC_BIN'),'requires private retail disc')
class FlagHTTP(unittest.TestCase):
    def test_retail_http_edit_history_and_untrusted_fields(self):
        private=Path(__file__).resolve().parents[3]/'local-output/sdk-20260909'
        with tempfile.TemporaryDirectory(prefix='flag-http-',dir=private) as directory:
            project=ProjectService(Path(directory));project.import_metadata(import_scene(os.environ['LEGAIA_DISC_BIN'],'dolk2'),os.environ['LEGAIA_DISC_BIN'])
            server=EditorServer(('127.0.0.1',0),project);thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
            def post(route,body):
                request=Request(f'http://127.0.0.1:{server.server_port}{route}',data=json.dumps(body).encode(),headers={'Content-Type':'application/json'})
                with urlopen(request,timeout=30) as response:return json.load(response)
            try:
                owner='scene://dolk2/actors/man-p1/0002'
                report=post('/api/actor-script',{'entity_id':owner})
                target=next(item for item in report['flag_authoring']['targets'] if item['mnemonic']=='CFLAG_SET' and item['values']['bit']==24)
                command={'type':'set_flag_bit','entity_id':owner,'flag_id':target['semantic_id'],'values':{'bit':25}}
                post('/api/command',command)
                changed=next(item for item in post('/api/actor-script',{'entity_id':owner})['flag_authoring']['targets'] if item['semantic_id']==target['semantic_id'])
                self.assertEqual(changed['values']['bit'],24);self.assertEqual(changed['effective_values']['bit'],25)
                post('/api/undo',{});self.assertFalse(project.overrides)
                post('/api/redo',{});self.assertTrue(project.overrides)
                for body in ({**command,'source_offset':1},{**command,'values':{'bit':32}},{**command,'values':{'bit':True}},{**command,'values':{'bit':8}},{**command,'flag_id':None}):
                    with self.assertRaises(HTTPError) as error:post('/api/command',body)
                    self.assertEqual(error.exception.code,400);error.exception.close()
                post('/api/command',{'type':'clear_flag_bit','entity_id':owner,'flag_id':target['semantic_id']})
                self.assertFalse(project.overrides)
                partial=post('/api/partition-two-script',{'entity_id':'scene://dolk2/scripts/man-p2/0007'})
                self.assertFalse(partial['flag_authoring']['supported'])
                self.assertTrue(partial['inspection']['instructions'])
            finally:
                server.shutdown();server.server_close();thread.join(timeout=5)
            self.assertFalse(thread.is_alive())
