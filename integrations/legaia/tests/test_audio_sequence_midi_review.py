from copy import deepcopy
import base64, json, os, threading, unittest
from urllib.request import Request, urlopen
from urllib.error import HTTPError
from unittest.mock import patch
import test_audio_authoring as base
from test_audio_sequence_midi import export_fixture
from sdk.audio_sequence_midi import review, decode_upload
from sdk.audio_authoring import source_key
from sdk.project import ProjectError
from sdk.server import EditorServer, EditorHandler


class MidiUploadBounds(unittest.TestCase):
    def test_strict_base64_and_byte_bounds(self):
        for value in [None,True,'!', 'A'*800000,base64.b64encode(bytes(25)).decode()]:
            with self.assertRaises(ProjectError):decode_upload(value)


@unittest.skipUnless(os.getenv('LEGAIA_DISC_BIN'),'Retail disc not configured')
class NativeMidiReview(unittest.TestCase):
    setUpClass=classmethod(base.AudioCommands.setUpClass.__func__)
    setUp=base.AudioCommands.setUp
    tearDown=base.AudioCommands.tearDown
    inspect=base.AudioCommands.inspect

    def test_native_review_noop_and_changed_inputs_are_readonly(self):
        options=self.inspect();report=deepcopy(options['current'])
        args=dict(asset_id=self.identifier,expected_entry_sha256=self.entry_hash,expected_authoring_key=source_key(self.project))
        before=deepcopy((self.project._document(),self.project.undo_stack,self.project.redo_stack))
        raw=export_fixture(report);noop=review(self.project,**args,midi_base64=base64.b64encode(raw).decode())
        self.assertEqual(noop['edits'],[]);self.assertIsNone(noop['native_review']);self.assertFalse(noop['input_retained'])
        e=next(e for e in report['events'] if e['kind']=='note_on' and e['values'][1]);e['values'][0]=(e['values'][0]+1)%128
        result=review(self.project,**args,midi_base64=base64.b64encode(export_fixture(report)).decode())
        self.assertEqual(result['edits'],[dict(event_offset=e['offset'],values=e['values'])]);self.assertEqual(result['native_review']['native_audit']['sequence']['edits'][0]['after_values'],e['values'])
        self.assertEqual(before,(self.project._document(),self.project.undo_stack,self.project.redo_stack))
        with self.assertRaises(ProjectError):review(self.project,**{**args,'expected_authoring_key':'f'*64},midi_base64=base64.b64encode(raw).decode())

    def test_http_exact_fields_and_readonly_upload(self):
        raw=export_fixture(self.inspect()['current']);args=dict(asset_id=self.identifier,expected_entry_sha256=self.entry_hash,expected_authoring_key=source_key(self.project),midi_base64=base64.b64encode(raw).decode())
        before=deepcopy(self.project._document())
        server=EditorServer(('127.0.0.1',0),self.project,runtime_port=65533);worker=threading.Thread(target=server.serve_forever,daemon=True)
        def post(value):
            request=Request(f'http://127.0.0.1:{server.server_port}/api/audio-sequence-midi-review',data=json.dumps(value).encode(),headers={'Content-Type':'application/json'})
            with urlopen(request,timeout=30) as response:return json.load(response)
        with patch.object(EditorHandler,'log_message',lambda *args:None):
            worker.start()
            try:
                self.assertEqual(post(args)['edits'],[])
                with self.assertRaises(HTTPError) as error:post({**args,'edits':[]})
                error.exception.close();self.assertEqual(before,self.project._document())
            finally:server.shutdown();server.server_close();worker.join(timeout=10)


if __name__=='__main__':unittest.main()
