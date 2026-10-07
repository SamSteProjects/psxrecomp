"""Current-sized writes qualify actual spans and preserve all other native bytes."""
from copy import deepcopy
import base64,json,os,threading,unittest
from urllib.request import Request,urlopen
from unittest.mock import patch
from sdk.project import ProjectService,ProjectError
from sdk.audio_authoring import source_key
from sdk.audio_bank_authoring import _source
from sdk.audio_sample_allocation import review,selected,preview
from sdk.audio_sample_sources import review as input_review
from sdk.audio_composition import read_entry
from sdk.server import EditorServer,EditorHandler
from importer.audio_bank import inspect_bank
import test_audio_authoring as sequence
import test_audio_sample_authoring as codec
import test_audio_native_allocation as allocation

@unittest.skipUnless(os.getenv('LEGAIA_DISC_BIN'),'Retail disc not configured')
class CurrentSize(unittest.TestCase):
    setUpClass=classmethod(sequence.AudioCommands.setUpClass.__func__)
    setUp=sequence.AudioCommands.setUp
    tearDown=sequence.AudioCommands.tearDown
    retain=allocation.NativeAllocation.retain
    apply=allocation.NativeAllocation.apply
    def retain_variant(self,frames=84):
        _,bank,record=_source(self.project,self.identifier,self.entry_hash,self.project.active_scene)
        row=inspect_bank(bank)['samples'][0];wav=codec.wav([int((i%17-8)*1231) for i in range(frames)],44100)
        args=dict(asset_id=self.identifier,expected_entry_sha256=self.entry_hash,expected_bank_sha256=codec.digest(bank),sample_index=0,expected_sample_sha256=row['source_sha256'],expected_authoring_key=source_key(self.project),wav_base64=base64.b64encode(wav).decode())
        proposal=input_review(self.project,**args,allocation=True)
        self.project.command(dict(type='retain_audio_sample_allocation_source',review_key=proposal['review_key'],**args))
        return next(r for r in self.project.audio_sample_sources.values() if r['wav_sha256']==proposal['binding']['wav_sha256'])
    def args(self):return dict(asset_id=self.identifier,expected_entry_sha256=self.entry_hash,sample_index=0,expected_authoring_key=source_key(self.project))
    def test_preserves_current_layout_outside_bytes_history_save_and_rejects_resize(self):
        receipt,_=self.retain();self.apply(receipt);other,_=self.retain(1);self.apply(other)
        replacement=self.retain_variant();wrong=self.retain_variant(112);before=deepcopy(self.project._document());current=read_entry(self.project,self.identifier)
        args=self.args();proposal=review(self.project,**args,operation='apply-current-size',receipt_key=replacement['receipt_key'])
        self.assertEqual(proposal['schema_version'],'legaia.audio-allocation-review.v2');self.assertEqual(proposal['before_entry_size_bytes'],proposal['after_entry_size_bytes'])
        pcm=preview(self.project,**args,layer='proposed',expected_sample_sha256=proposal['proposed_sample_sha256'],operation='apply-current-size',receipt_key=replacement['receipt_key'],review_key=proposal['review_key']);self.assertEqual(pcm['waveform']['decoded_frames'],84)
        with self.assertRaisesRegex(ProjectError,'exact Current'):review(self.project,**args,operation='apply-current-size',receipt_key=wrong['receipt_key'])
        command=dict(type='set_audio_sample_current_size',receipt_key=replacement['receipt_key'],review_key=proposal['review_key'],**args)
        with self.assertRaises(ProjectError):self.project.command(dict(command,review_key='0'*64))
        self.assertEqual(self.project._document(),before);self.project.command(command);candidate=read_entry(self.project,self.identifier)
        row,at,raw=selected(current,0);new,pos,encoded=selected(candidate,0)
        self.assertEqual((at,len(raw)),(pos,len(encoded)));self.assertNotEqual(raw,encoded)
        outside=current[:at]+current[at+len(raw):];self.assertEqual(outside,candidate[:pos]+candidate[pos+len(encoded):]);self.assertEqual(codec.digest(outside),proposal['held_outside_sample_sha256'])
        self.assertEqual(selected(candidate,1)[2],selected(current,1)[2]);after=deepcopy(self.project._document())
        self.project.undo();self.assertEqual(self.project._document(),before);self.project.redo();self.assertEqual(self.project._document(),after)
        self.project.save();self.assertEqual(ProjectService.open(self.project.root)._document(),after)
        history=len(self.project.undo_stack);noop=review(self.project,**self.args(),operation='apply-current-size',receipt_key=replacement['receipt_key']);self.assertTrue(noop['no_change'])
        self.project.command(dict(command,expected_authoring_key=source_key(self.project),review_key=noop['review_key']));self.assertEqual(len(self.project.undo_stack),history)
    def test_http_review_proposed_and_current_size_command(self):
        r,_=self.retain();self.apply(r);r=self.retain_variant();server=EditorServer(('127.0.0.1',0),self.project,runtime_port=65533);worker=threading.Thread(target=server.serve_forever,daemon=True)
        def post(route,body):
            with urlopen(Request(f'http://127.0.0.1:{server.server_port}'+route,data=json.dumps(body).encode(),headers={'Content-Type':'application/json'}),timeout=30) as response:return json.load(response)
        with patch.object(EditorHandler,'log_message',lambda *args:None):
            worker.start()
            try:
                args=self.args();p=post('/api/audio-allocation-review',dict(args,operation='apply-current-size',receipt_key=r['receipt_key']))
                v=post('/api/audio-allocation-preview',dict(args,layer='proposed',expected_sample_sha256=p['proposed_sample_sha256'],operation='apply-current-size',receipt_key=r['receipt_key'],review_key=p['review_key']));self.assertEqual(v['waveform']['decoded_frames'],84)
                post('/api/command',dict(args,type='set_audio_sample_current_size',receipt_key=r['receipt_key'],review_key=p['review_key']))
                self.assertEqual(selected(read_entry(self.project,self.identifier),0)[0]['source_sha256'],r['candidate_sample_sha256'])
            finally:server.shutdown();worker.join(5);server.server_close()
