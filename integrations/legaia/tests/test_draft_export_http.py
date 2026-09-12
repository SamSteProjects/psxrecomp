"""Actual HTTP routing and guards, with the expensive disc writer mocked."""
import json
from pathlib import Path
import tempfile
import threading
import unittest
from urllib.request import Request, urlopen
from urllib.error import HTTPError
from unittest.mock import patch
from sdk.project import ProjectService
from sdk.server import EditorServer


class DraftExportHTTP(unittest.TestCase):
    def test_export_response_and_request_guards(self):
        with tempfile.TemporaryDirectory() as directory:
            project=ProjectService(Path(directory))
            project.active_scene='scene://fixture'
            project.actor_drafts={'draft':{'scene_id':project.active_scene}}
            server=EditorServer(('127.0.0.1',0),project)
            thread=threading.Thread(target=server.serve_forever,daemon=True)
            thread.start()
            def post(body,route='/api/export/actor-drafts'):
                request=Request(f'http://127.0.0.1:{server.server_port}{route}',
                    data=json.dumps(body).encode(),headers={'Content-Type':'application/json'})
                with urlopen(request,timeout=5) as response:
                    return json.load(response)
            try:
                with patch('sdk.draft_build.export_draft_disc',return_value={
                        'disc':{'output_path':'fixture.bin','output_sha256':'hash'}}) as writer:
                    result=post({'entity_id':'draft'})
                    self.assertTrue(result['experimental'])
                    self.assertFalse(result['gameplay_verified'])
                    self.assertEqual(result['output_sha256'],'hash')
                    self.assertTrue(Path(result['report_path']).is_relative_to(project.root))
                    self.assertEqual(Path(result['input_project_path']),Path(result['report_path']).parent/'Inputs'/'project.legaia.json')
                    for body in ({}, {'entity_id':'missing'}, {'entity_id':'draft','output':'outside'}, {'entity_id':1}):
                        with self.assertRaises(HTTPError) as error:
                            post(body)
                        self.assertEqual(error.exception.code,400)
                        error.exception.close()
                    project.mode='live'
                    with self.assertRaises(HTTPError) as error:
                        post({'entity_id':'draft'})
                    self.assertEqual(error.exception.code,400)
                    error.exception.close()
                    self.assertEqual(writer.call_count,1)
                    self.assertIsNone(server.last_build)
                    project.mode='edit'
                    project.actor_drafts.clear()
                    result=post({},'/api/export/project')
                    self.assertTrue(result['experimental'])
                    self.assertIsNone(writer.call_args.args[1])
                    with self.assertRaises(HTTPError) as error:
                        post({'output':'outside'},'/api/export/project')
                    self.assertEqual(error.exception.code,400)
                    error.exception.close()
            finally:
                server.shutdown();server.server_close();thread.join(timeout=5)


if __name__=='__main__':
    unittest.main()
