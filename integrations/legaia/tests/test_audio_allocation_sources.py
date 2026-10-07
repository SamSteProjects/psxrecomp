"""Allocation inputs stay historical while sharing project persistence/recovery."""
from copy import deepcopy
from pathlib import Path
import base64,os,unittest,json,threading
from urllib.request import Request,urlopen
from urllib.error import HTTPError
from unittest.mock import patch
from sdk.project import ProjectService,ProjectError
from sdk.audio_sample_sources import review,read_source,library,download,source_path,preserve_build_inputs,read_build_inputs,review_removal,ALLOCATION_SCHEMA
from sdk.audio_sample_authoring import options,review as native_review
from sdk.audio_authoring import source_key
from sdk.audio_composition import read_entry
from sdk.audio_bank_authoring import _source
from sdk.audio_input_assets import inventory
from sdk.export_snapshot import capture_export_inputs
from sdk.project_copy import review as copy_review,create_copy
from sdk.build import authored_state_key
from importer.audio_bank import inspect_bank
from importer.core import ImportError
from sdk.server import EditorServer,EditorHandler
import test_audio_sample_authoring as codec
import test_audio_authoring as sequence

@unittest.skipUnless(os.getenv('LEGAIA_DISC_BIN'),'Retail disc not configured')
class AllocationSources(unittest.TestCase):
    setUpClass=classmethod(sequence.AudioCommands.setUpClass.__func__)
    setUp=sequence.AudioCommands.setUp
    tearDown=sequence.AudioCommands.tearDown
    def args(self,index=0,frames=84):
        body,bank,record=_source(self.project,self.identifier,self.entry_hash,self.project.active_scene)
        sample=inspect_bank(bank)['samples'][index];wav=codec.wav([int((i%20-10)*711) for i in range(frames)],32000)
        return dict(asset_id=self.identifier,expected_entry_sha256=self.entry_hash,expected_bank_sha256=codec.digest(bank),sample_index=index,
            expected_sample_sha256=sample['source_sha256'],expected_authoring_key=source_key(self.project),wav_base64=base64.b64encode(wav).decode()),wav,body
    def retain(self):
        args,wav,body=self.args();proposal=review(self.project,**args,allocation=True)
        self.project.command(dict(type='retain_audio_sample_allocation_source',review_key=proposal['review_key'],**args))
        record=next(iter(self.project.audio_sample_sources.values()));return record,wav,body
    def test_review_retain_history_save_open_copy_assets_and_snapshot_keep_native_bytes(self):
        args,wav,body=self.args();document=self.project._document();proposal=review(self.project,**args,allocation=True)
        self.assertEqual(self.project._document(),document);self.assertEqual(proposal['binding']['decoded_frames'],84)
        self.assertEqual(proposal['binding']['schema_version'],ALLOCATION_SCHEMA)
        self.project.command(dict(type='retain_audio_sample_allocation_source',review_key=proposal['review_key'],**args))
        record=next(iter(self.project.audio_sample_sources.values()));self.assertEqual(read_source(self.project,record),wav)
        self.assertEqual(len(self.project.undo_stack),1);self.assertEqual(read_entry(self.project,self.identifier,body),body)
        self.project.undo();self.assertEqual(self.project._document(),document);self.project.redo();self.project.save()
        opened=ProjectService.open(self.project.root);self.assertEqual(opened._document(),self.project._document())
        self.assertEqual(len(inventory(opened)['assets']),1)
        _,files=capture_export_inputs(opened);self.assertEqual(files['Authored/Audio/Sources/'+record['wav_sha256']+'.wav'],wav)
        clone=ProjectService.open(Path(create_copy(opened,'Allocation input copy',copy_review(opened)['review_key'])['copied_project']))
        self.assertEqual(clone.audio_sample_sources,opened.audio_sample_sources);self.assertEqual(read_source(clone,record),wav)
        fixed=options(opened,self.identifier,self.entry_hash,0,source_key(opened));self.assertEqual(fixed['retained_inputs'],[])
        with self.assertRaisesRegex(ProjectError,'allocation authoring'):native_review(opened,self.identifier,self.entry_hash,0,source_key(opened),'apply',record['receipt_key'])
    def test_recovery_removal_and_frozen_build_inputs_preserve_original_bytes(self):
        record,wav,body=self.retain();key=authored_state_key(self.project);destination=self.project.root/'Builds'/('0'*16)
        preserve_build_inputs(self.project,destination,key,self.project.root)
        self.assertEqual(read_build_inputs(self.project,'0'*16,key)[1][record['wav_sha256']],wav)
        result=download(self.project,record['receipt_key'],source_key(self.project));self.assertEqual(base64.b64decode(result['wav_base64']),wav)
        removal=review_removal(self.project,record['receipt_key'],source_key(self.project))
        self.project.command(dict(type='remove_audio_sample_source',receipt_key=record['receipt_key'],expected_authoring_key=source_key(self.project),review_key=removal['review_key']))
        self.assertEqual(self.project.audio_sample_sources,{});self.assertTrue(source_path(self.project,record).exists())
        self.assertEqual(read_build_inputs(self.project,'0'*16,key)[1][record['wav_sha256']],wav)
        self.assertEqual(read_entry(self.project,self.identifier,body),body);self.project.undo();self.assertEqual(read_source(self.project,record),wav)
    def test_stale_legacy_loop_marker_cut_and_malformed_input_refuse_atomically(self):
        args,wav,_=self.args();proposal=review(self.project,**args,allocation=True);document=self.project._document()
        for change in ({'review_key':'f'*64},{'expected_authoring_key':'f'*64},{'expected_sample_sha256':'f'*64}):
            with self.assertRaises((ProjectError,ImportError)):self.project.command(dict(type='retain_audio_sample_allocation_source',**args,review_key=proposal['review_key'])|change)
            self.assertEqual(self.project._document(),document)
        with self.assertRaises((ProjectError,ImportError)):self.project.command(dict(type='retain_audio_sample_source',review_key=proposal['review_key'],**args))
        for index,frames in ((0,28),(0,56),(3,84)):
            bad,_,_=self.args(index,frames)
            with self.assertRaises((ProjectError,ImportError)):review(self.project,**bad,allocation=True)
            self.assertEqual(self.project._document(),document)
        bad=deepcopy(args);bad['wav_base64']=base64.b64encode(codec.wav([0]*85)).decode()
        with self.assertRaises((ProjectError,ImportError)):review(self.project,**bad,allocation=True)

    def test_http_large_allocation_review_retain_exact_fields_and_stale_refusal(self):
        args,_,body=self.args();_,bank,_=_source(self.project,self.identifier,self.entry_hash,self.project.active_scene)
        sample=inspect_bank(bank)['samples'][0];raw=bank[sample['offset']:sample['offset']+sample['size_bytes']]
        frames=[v//2 for v in codec.independent_decode(raw)]+[0]*28;wav=codec.wav(frames,32000)
        args['wav_base64']=base64.b64encode(wav).decode();self.assertGreater(len(json.dumps(args)),32768)
        server=EditorServer(('127.0.0.1',0),self.project,runtime_port=65533);worker=threading.Thread(target=server.serve_forever,daemon=True)
        def post(route,value):
            req=Request(f'http://127.0.0.1:{server.server_port}'+route,data=json.dumps(value).encode(),headers={'Content-Type':'application/json'})
            try:
                with urlopen(req,timeout=30) as response:return json.load(response)
            except HTTPError as error:
                error.read();error.close();raise
        with patch.object(EditorHandler,'log_message',lambda *args:None):
            worker.start()
            try:
                document=self.project._document();proposal=post('/api/audio-sample-allocation-source-review',args)
                self.assertEqual(self.project._document(),document);self.assertEqual(proposal['binding']['decoded_frames'],len(frames))
                with self.assertRaises(HTTPError):post('/api/audio-sample-allocation-source-review',{**args,'extra':1})
                with self.assertRaises(HTTPError):post('/api/audio-sample-source-retain',dict(args,review_key=proposal['review_key']))
                post('/api/audio-sample-allocation-source-retain',dict(args,review_key=proposal['review_key']))
                self.assertEqual(read_entry(self.project,self.identifier,body),body)
                self.assertEqual(read_source(self.project,next(iter(self.project.audio_sample_sources.values()))),wav)
                document=self.project._document()
                with self.assertRaises(HTTPError):post('/api/audio-sample-allocation-source-retain',dict(args,review_key=proposal['review_key']))
                self.assertEqual(self.project._document(),document)
            finally:server.shutdown();worker.join(5);server.server_close()

if __name__=='__main__':unittest.main()
