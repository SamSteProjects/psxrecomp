"""HTTP export representation gates and private GLB writes."""
import json
from pathlib import Path
import tempfile
import threading
import unittest
from unittest.mock import Mock
from urllib.request import Request, urlopen
from urllib.error import HTTPError
from sdk.server import EditorServer
from sdk.project import ProjectService
from test_animation_clip_export import clip
from test_importer_export import parse_glb

class AnimationClipHttpTests(unittest.TestCase):
    def test_actor_clip_export_and_early_rejection(self):
        with tempfile.TemporaryDirectory() as temp:
            server=EditorServer(('127.0.0.1',0),ProjectService(Path(temp)))
            server.actor_animation_preview=Mock(return_value=clip())
            thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
            def post(body):
                request=Request(f'http://127.0.0.1:{server.server_port}/api/export/actor-animation',data=json.dumps(body).encode(),headers={'Content-Type':'application/json'})
                try:
                    with urlopen(request) as response:return response.status,json.load(response)
                except HTTPError as error:
                    with error:return error.code,json.load(error)
            try:
                for args in ({'clip_fps':True},{'clip_fps':0},{'clip_fps':121},{'clip_fps':15,'frame_index':0},{'clip_fps':15,'output_path':'other'},{}):
                    status,_=post({'entity_id':'scene://fixture/actor',**args});self.assertEqual(status,400)
                server.actor_animation_preview.assert_not_called()
                status,result=post({'entity_id':'scene://fixture/actor','clip_fps':15})
                self.assertEqual(status,200);self.assertTrue(result['audit']['full_clip'])
                path=Path(result['path']);self.assertEqual(path.parent,Path(temp)/'Exports')
                doc,_=parse_glb(path.read_bytes());self.assertEqual(len(doc['animations'][0]['channels']),2)
                status,frame=post({'entity_id':'scene://fixture/actor','frame_index':1})
                self.assertEqual(status,200);self.assertTrue(frame['audit']['posed'])
                self.assertNotIn('full_clip',frame['audit'])
            finally:server.shutdown();server.server_close();thread.join()

if __name__=='__main__':unittest.main()
