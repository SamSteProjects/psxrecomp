from copy import deepcopy
import os,threading,json,unittest
from unittest.mock import patch
from urllib.request import Request,urlopen
from urllib.error import HTTPError
import test_audio_authoring as base
from sdk.audio_authoring import proposed_inspection,review,source_key
from sdk.project import ProjectError
from sdk.server import EditorServer,EditorHandler

@unittest.skipUnless(os.getenv('LEGAIA_DISC_BIN'),'Retail disc not configured')
class ProposedSequence(unittest.TestCase):
    setUpClass=classmethod(base.AudioCommands.setUpClass.__func__)
    setUp=base.AudioCommands.setUp
    tearDown=base.AudioCommands.tearDown
    inspect=base.AudioCommands.inspect
    first_edit=base.AudioCommands.first_edit
    change=base.AudioCommands.change

    def args(self,edit):return dict(asset_id=self.identifier,expected_entry_sha256=self.entry_hash,expected_authoring_key=source_key(self.project),edits=[edit])

    def test_proposed_native_report_preserves_structure_and_does_not_apply(self):
        options=self.inspect();event=next(e for e in options['current']['events'] if e['kind']=='note_on' and e['values'][1]>0)
        edit=dict(event_offset=event['offset'],values=[(event['values'][0]+1)%128,event['values'][1]])
        args=self.args(edit);proposal=review(self.project,**args);before=deepcopy(self.project._document());history=len(self.project.undo_stack)
        result=proposed_inspection(self.project,**args,review_key=proposal['review_key']);sequence=result['sequence'];changed=sequence['events'][event['index']]
        self.assertEqual(changed['values'],edit['values']);self.assertEqual(sequence['event_count'],options['current']['event_count'])
        for old,new in zip(options['current']['events'],sequence['events']):
            for field in ('index','offset','end_offset','delta_ticks','ticks','status','channel','kind','running_status'):self.assertEqual(old[field],new[field])
        self.assertEqual(result['before_entry_sha256'],options['current_entry_sha256']);self.assertEqual(result['after_entry_sha256'],proposal['native_audit']['after_entry_sha256'])
        self.assertEqual(self.project._document(),before);self.assertEqual(len(self.project.undo_stack),history)

    def test_tempo_report_and_stale_or_unreviewed_inspection_reject(self):
        self.identifier='audio://legaia/prot/0268'
        self.entry_hash=self.rows[self.identifier]['source_record']['sha256']
        options=self.inspect();event=next(e for e in options['current']['events'] if e['kind']=='set_tempo');value=event['values'][0]+1 if event['values'][0]<16777215 else event['values'][0]-1
        args=self.args(dict(event_offset=event['offset'],values=[value]));proposal=review(self.project,**args)
        result=proposed_inspection(self.project,**args,review_key=proposal['review_key'])
        self.assertEqual(result['sequence']['decoded_time_seconds'],proposal['native_audit']['sequence']['decoded_time_seconds'])
        self.assertEqual(result['sequence']['decoded_ticks'],options['current']['decoded_ticks'])
        self.assertNotEqual(result['sequence']['decoded_time_seconds'],options['current']['decoded_time_seconds'])
        with self.assertRaises(ProjectError):proposed_inspection(self.project,**args,review_key='f'*64)
        _,edit=self.first_edit();self.change([edit])
        with self.assertRaises(ProjectError):proposed_inspection(self.project,**args,review_key=proposal['review_key'])

    def test_http_requires_exact_review_fields(self):
        _,edit=self.first_edit();args=self.args(edit);proposal=review(self.project,**args);value={**args,'review_key':proposal['review_key']};before=deepcopy(self.project._document())
        server=EditorServer(('127.0.0.1',0),self.project);worker=threading.Thread(target=server.serve_forever,daemon=True)
        def post(value):
            request=Request(f'http://127.0.0.1:{server.server_port}/api/audio-sequence-proposed',data=json.dumps(value).encode(),headers={'Content-Type':'application/json'})
            with urlopen(request,timeout=30) as response:return json.load(response)
        with patch.object(EditorHandler,'log_message',lambda *args:None):
            worker.start()
            try:
                self.assertEqual(post(value)['review_key'],proposal['review_key'])
                with self.assertRaises(HTTPError) as error:post({**value,'extra':True})
                error.exception.close();self.assertEqual(self.project._document(),before)
            finally:server.shutdown();server.server_close();worker.join(timeout=10)

if __name__=='__main__':unittest.main()
