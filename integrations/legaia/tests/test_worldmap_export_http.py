"""HTTP export boundary: server-owned geometry/output and selected identity."""
from pathlib import Path
import json, tempfile, threading, unittest
from unittest.mock import patch
from urllib.request import Request, urlopen
from urllib.error import HTTPError
from sdk.project import ProjectService
from sdk.server import EditorHandler, EditorServer

class WorldmapExportHTTPTests(unittest.TestCase):
    def test_scope_ownership_and_client_payload_rejection(self):
        with tempfile.TemporaryDirectory() as root:
            project=ProjectService(Path(root));server=EditorServer(('127.0.0.1',0),project)
            thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
            def post(body):
                request=Request(f'http://127.0.0.1:{server.server_port}/api/export/worldmap',data=json.dumps(body).encode(),headers={'Content-Type':'application/json'})
                try:
                    with urlopen(request) as response:return response.status,json.load(response)
                except HTTPError as error:
                    with error:return error.code,json.load(error)
            try:
                with patch('sdk.worldmap_export.export',return_value={'fixture':True}) as export:
                    base=dict(scene='map01',source_key='a'*64,scope='source-scene')
                    for body in ({**base,'path':'C:/outside.glb'},{**base,'preview':{}},{**base,'entity_id':'scene://map01/worldmap/ground'},{**base,'scope':'selected'},[],{}):
                        status,result=post(body);self.assertEqual(status,400);self.assertIn('error',result)
                    export.assert_not_called()
                    self.assertEqual(post(base),(200,{'fixture':True}))
                    export.assert_called_once_with(project,'map01','a'*64,'source-scene',None)
                    export.reset_mock();selected={**base,'scope':'selected','entity_id':'scene://map01/worldmap/ground'}
                    self.assertEqual(post(selected),(200,{'fixture':True}))
                    export.assert_called_once_with(project,'map01','a'*64,'selected',selected['entity_id'])
            finally:server.shutdown();server.server_close();thread.join(5)

if __name__=='__main__':unittest.main()
