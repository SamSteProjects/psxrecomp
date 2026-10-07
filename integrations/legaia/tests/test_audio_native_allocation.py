"""Native allocated sample commands, dynamic Current and source-bound preview."""
from copy import deepcopy
import base64,json,os,threading,unittest
from urllib.request import Request,urlopen
from urllib.error import HTTPError
from unittest.mock import patch
from sdk.project import ProjectService,ProjectError
from sdk.audio_authoring import source_key
from sdk.audio_sample_sources import review as input_review
from sdk.audio_sample_allocation import options,review,preview,selected,FORMAT
from sdk.audio_sample_authoring import options as fixed_options
from sdk.audio_composition import read_entry
from sdk.audio_bank_authoring import _source
from sdk.audio_input_assets import inventory
from sdk.audio_input_bindings import current as current_bindings
from sdk.server import EditorServer,EditorHandler
from importer.audio_bank import inspect_bank
from importer.core import ImportError
import test_audio_authoring as sequence
import test_audio_sample_authoring as codec

@unittest.skipUnless(os.getenv('LEGAIA_DISC_BIN'),'Retail disc not configured')
class NativeAllocation(unittest.TestCase):
    setUpClass=classmethod(sequence.AudioCommands.setUpClass.__func__)
    setUp=sequence.AudioCommands.setUp
    tearDown=sequence.AudioCommands.tearDown
    def retain(self,index=0):
        body,bank,record=_source(self.project,self.identifier,self.entry_hash,self.project.active_scene)
        source=inspect_bank(bank)['samples'][index];wav=codec.wav([int((i%20-10)*711) for i in range(84)],32000)
        args=dict(asset_id=self.identifier,expected_entry_sha256=self.entry_hash,expected_bank_sha256=codec.digest(bank),sample_index=index,
            expected_sample_sha256=source['source_sha256'],expected_authoring_key=source_key(self.project),wav_base64=base64.b64encode(wav).decode())
        proposal=input_review(self.project,**args,allocation=True);self.project.command(dict(type='retain_audio_sample_allocation_source',review_key=proposal['review_key'],**args))
        return next(r for r in self.project.audio_sample_sources.values() if r['sample_index']==index),body
    def apply(self,receipt):
        args=dict(asset_id=self.identifier,expected_entry_sha256=self.entry_hash,sample_index=receipt['sample_index'],expected_authoring_key=source_key(self.project))
        proposal=review(self.project,**args,operation='apply',receipt_key=receipt['receipt_key'])
        self.project.command(dict(type='set_audio_sample_allocation',receipt_key=receipt['receipt_key'],review_key=proposal['review_key'],**args));return proposal
    def test_apply_history_save_open_dynamic_bindings_preview_and_clear(self):
        receipt,body=self.retain();before=self.project._document();proposal=self.apply(receipt)
        self.assertEqual(self.project.audio_sample_overrides[self.identifier]['format'],FORMAT)
        current=read_entry(self.project,self.identifier);row,offset,raw=selected(current,0)
        self.assertEqual(row['size_bytes'],64);self.assertEqual(codec.digest(raw),receipt['candidate_sample_sha256'])
        opt=options(self.project,self.identifier,self.entry_hash,0,source_key(self.project));self.assertEqual(opt['current_sample_entry_byte_offset'],offset)
        self.assertEqual(opt['current_input'],receipt);self.assertEqual(opt['current']['decoded_frames'],84)
        refs=current_bindings(self.project,inventory(self.project));self.assertEqual(refs[0]['sample_size_bytes'],64)
        pcm=preview(self.project,self.identifier,self.entry_hash,0,source_key(self.project),'current',codec.digest(raw))
        self.assertEqual(len(base64.b64decode(pcm['pcm_base64'])),168);self.assertEqual(pcm['selected_sample'],row)
        self.project.save();self.assertEqual(ProjectService.open(self.project.root)._document(),self.project._document())
        self.project.undo();self.assertEqual(self.project._document(),before);self.project.redo();self.assertEqual(read_entry(self.project,self.identifier),current)
        key=source_key(self.project);clear=review(self.project,self.identifier,self.entry_hash,0,key,'clear')
        self.assertIsNone(clear['proposed_binding']);self.project.command(dict(type='clear_audio_sample_allocation',asset_id=self.identifier,expected_entry_sha256=self.entry_hash,sample_index=0,expected_authoring_key=key,review_key=clear['review_key']))
        self.assertEqual(read_entry(self.project,self.identifier,body),body);self.project.undo();self.assertEqual(read_entry(self.project,self.identifier),current)
    def test_multiple_ordinal_moves_restore_one_and_guard_legacy_fixed_offsets(self):
        first,body=self.retain(0);self.apply(first);second,_=self.retain(1);self.apply(second)
        current=read_entry(self.project,self.identifier);source_row,source_at,_=selected(body,2);current_row,current_at,raw=selected(current,2)
        self.assertEqual(source_row['source_sha256'],codec.digest(raw));self.assertNotEqual(source_at,current_at)
        self.assertEqual(options(self.project,self.identifier,self.entry_hash,2,source_key(self.project))['current_sample'],current_row)
        with self.assertRaisesRegex(ProjectError,'allocation authoring'):fixed_options(self.project,self.identifier,self.entry_hash,2,source_key(self.project))
        key=source_key(self.project);clear=review(self.project,self.identifier,self.entry_hash,0,key,'clear')
        self.project.command(dict(type='clear_audio_sample_allocation',asset_id=self.identifier,expected_entry_sha256=self.entry_hash,sample_index=0,expected_authoring_key=key,review_key=clear['review_key']))
        row,_,raw=selected(read_entry(self.project,self.identifier),0);self.assertEqual(row['source_sha256'],selected(body,0)[0]['source_sha256'])
        self.assertEqual(selected(read_entry(self.project,self.identifier),1)[0]['source_sha256'],second['candidate_sample_sha256'])
    def test_forged_stale_noop_and_proposed_preview_are_atomic(self):
        receipt,body=self.retain();key=source_key(self.project);before=self.project._document()
        proposal=review(self.project,self.identifier,self.entry_hash,0,key,'apply',receipt['receipt_key'])
        pcm=preview(self.project,self.identifier,self.entry_hash,0,key,'proposed',proposal['proposed_sample_sha256'],'apply',receipt['receipt_key'],proposal['review_key'])
        self.assertEqual(pcm['waveform']['decoded_frames'],84);self.assertEqual(self.project._document(),before)
        args=dict(type='set_audio_sample_allocation',asset_id=self.identifier,expected_entry_sha256=self.entry_hash,sample_index=0,expected_authoring_key=key,receipt_key=receipt['receipt_key'],review_key=proposal['review_key'])
        for field in ('review_key','expected_authoring_key','expected_entry_sha256','receipt_key'):
            with self.assertRaises((ProjectError,ImportError)):self.project.command(dict(args,**{field:'f'*64}))
            self.assertEqual(self.project._document(),before)
        self.project.command(args);history=len(self.project.undo_stack);again=review(self.project,self.identifier,self.entry_hash,0,source_key(self.project),'apply',receipt['receipt_key'])
        self.assertTrue(again['no_change']);self.project.command(dict(args,expected_authoring_key=source_key(self.project),review_key=again['review_key']));self.assertEqual(len(self.project.undo_stack),history)
    def test_http_options_review_proposed_apply_current_and_wrong_layer_refusal(self):
        receipt,_=self.retain();server=EditorServer(('127.0.0.1',0),self.project,runtime_port=65533);worker=threading.Thread(target=server.serve_forever,daemon=True)
        def post(route,body):
            try:
                with urlopen(Request(f'http://127.0.0.1:{server.server_port}'+route,data=json.dumps(body).encode(),headers={'Content-Type':'application/json'}),timeout=30) as response:return json.load(response)
            except HTTPError as error:error.read();error.close();raise
        with patch.object(EditorHandler,'log_message',lambda *args:None):
            worker.start()
            try:
                args=dict(asset_id=self.identifier,expected_entry_sha256=self.entry_hash,sample_index=0,expected_authoring_key=source_key(self.project))
                opt=post('/api/audio-allocation-authoring',args);proposal=post('/api/audio-allocation-review',dict(args,operation='apply',receipt_key=receipt['receipt_key']))
                pcm=post('/api/audio-allocation-preview',dict(args,layer='proposed',expected_sample_sha256=proposal['proposed_sample_sha256'],operation='apply',receipt_key=receipt['receipt_key'],review_key=proposal['review_key']))
                self.assertEqual(pcm['waveform']['decoded_frames'],84)
                with self.assertRaises(HTTPError):post('/api/audio-allocation-preview',dict(args,layer='current',expected_sample_sha256=opt['current_sample_sha256'],review_key=proposal['review_key']))
                post('/api/command',dict(args,type='set_audio_sample_allocation',receipt_key=receipt['receipt_key'],review_key=proposal['review_key']))
                args['expected_authoring_key']=source_key(self.project);self.assertEqual(post('/api/audio-allocation-authoring',args)['current_sample']['size_bytes'],64)
            finally:server.shutdown();worker.join(5);server.server_close()

if __name__=='__main__':unittest.main()
