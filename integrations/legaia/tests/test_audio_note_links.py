from copy import deepcopy
import os,json,threading,unittest
from unittest.mock import patch
from urllib.request import Request,urlopen
from urllib.error import HTTPError
import test_audio_authoring as base
from sdk.audio_note_links import inspect
from sdk.audio_authoring import source_key
from sdk.scene_preview import source_key as resource_key
from sdk.project import ProjectError
from sdk.server import EditorServer,EditorHandler

@unittest.skipUnless(os.getenv('LEGAIA_DISC_BIN'),'Retail disc not configured')
class NoteLinks(unittest.TestCase):
    setUpClass=classmethod(base.AudioCommands.setUpClass.__func__)
    setUp=base.AudioCommands.setUp
    tearDown=base.AudioCommands.tearDown
    inspect=base.AudioCommands.inspect
    change=base.AudioCommands.change
    def args(self,index):return dict(asset_id=self.identifier,expected_entry_sha256=self.entry_hash,expected_source_key=resource_key(self.project),expected_authoring_key=source_key(self.project),note_index=index)
    def test_current_links_and_latest_explicit_program_are_nonmutating(self):
        options=self.inspect();event=next(e for e in options['current']['events'] if e['kind']=='note_on' and e['values'][1]>0)
        before=deepcopy(self.project._document());result=inspect(self.project,**self.args(event['index']))
        self.assertEqual(result['note'],event);self.assertIsNotNone(result['bank'])
        prior=next((e for e in reversed(options['current']['events'][:event['index']]) if e['channel']==event['channel'] and e['kind']=='program_change'),None)
        self.assertEqual(result['program_event'],prior);self.assertEqual(self.project._document(),before);self.assertFalse(self.project.undo_stack)
        self.change([dict(event_offset=event['offset'],values=[(event['values'][0]+1)%128,event['values'][1]])])
        changed=inspect(self.project,**self.args(event['index']));self.assertNotEqual(changed['note']['values'],event['values']);self.assertNotEqual(changed['current_sequence_sha256'],result['current_sequence_sha256'])
        changed['bank']['programs'][0]['volume']=999
        self.assertNotEqual(inspect(self.project,**self.args(event['index']))['bank']['programs'][0]['volume'],999)
    def test_exact_note_source_and_http_fields(self):
        report=self.inspect();event=next(e for e in report['current']['events'] if e['kind']=='note_on' and e['values'][1]>0);args=self.args(event['index']);before=deepcopy(self.project._document())
        for bad in [True,-1,32768,next(e['index'] for e in report['current']['events'] if e['kind']!='note_on')]:
            with self.assertRaises(ProjectError):inspect(self.project,**{**args,'note_index':bad})
        with self.assertRaises(ProjectError):inspect(self.project,**{**args,'expected_authoring_key':'f'*64})
        server=EditorServer(('127.0.0.1',0),self.project);worker=threading.Thread(target=server.serve_forever,daemon=True)
        def post(value):
            req=Request(f'http://127.0.0.1:{server.server_port}/api/audio-note-links',data=json.dumps(value).encode(),headers={'Content-Type':'application/json'})
            with urlopen(req,timeout=30) as response:return json.load(response)
        with patch.object(EditorHandler,'log_message',lambda *args:None):
            worker.start()
            try:
                self.assertEqual(post(args)['note'],event)
                with self.assertRaises(HTTPError) as error:post({**args,'extra':True})
                self.assertEqual(error.exception.code,400);error.exception.close()
            finally:server.shutdown();server.server_close();worker.join(timeout=10)
        self.assertEqual(self.project._document(),before)

if __name__=='__main__':unittest.main()
