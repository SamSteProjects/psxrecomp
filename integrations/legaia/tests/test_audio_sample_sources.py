"""Retained WAV receipts, Current recovery and native-input preservation."""
from copy import deepcopy
from pathlib import Path
import base64,json,os,threading,unittest
from urllib.request import Request,urlopen
from urllib.error import HTTPError
from unittest.mock import patch
import test_audio_authoring as sequence_tests
from test_audio_sample_authoring import wav,independent_decode
from sdk.project import ProjectService,ProjectError
from sdk.audio_sample_sources import review,library,download,review_removal,read_source,source_path,validate_record,preserve_build_inputs,read_build_inputs
from sdk.audio_authoring import source_key
from sdk.audio_bank_authoring import _source
from sdk.project_copy import review as copy_review,create_copy
from sdk.export_snapshot import capture_export_inputs
from sdk.build import authored_state_key
from sdk.server import EditorServer,EditorHandler
from importer.audio_bank import inspect_bank

@unittest.skipUnless(os.getenv('LEGAIA_DISC_BIN'),'Retail disc not configured')
class WavInputs(unittest.TestCase):
    setUpClass=classmethod(sequence_tests.AudioCommands.setUpClass.__func__)
    setUp=sequence_tests.AudioCommands.setUp
    tearDown=sequence_tests.AudioCommands.tearDown

    def args(self):
        body,bank,record=_source(self.project,self.identifier,self.entry_hash,self.project.active_scene)
        report=inspect_bank(bank);sample=report['samples'][0];raw=bank[sample['offset']:sample['offset']+sample['size_bytes']]
        frames=independent_decode(raw);input=wav([int(v*.5) for v in frames],32000)
        return dict(asset_id=self.identifier,expected_entry_sha256=self.entry_hash,expected_bank_sha256=report['bank_sha256'],
                    sample_index=0,expected_sample_sha256=sample['source_sha256'],expected_authoring_key=source_key(self.project),
                    wav_base64=base64.b64encode(input).decode('ascii')),input
    def retain(self):
        args,input=self.args();report=review(self.project,**args)
        self.project.command(dict(type='retain_audio_sample_source',review_key=report['review_key'],**args))
        return next(iter(self.project.audio_sample_sources.values())),input

    def test_review_retain_recovery_history_save_open_snapshot_copy_remove(self):
        document=deepcopy(self.project._document());native=(deepcopy(self.project.imports),deepcopy(self.project.overrides),deepcopy(self.project.audio_overrides),deepcopy(self.project.audio_bank_overrides));key=authored_state_key(self.project)
        args,input=self.args();report=review(self.project,**args);self.assertEqual(self.project._document(),document)
        self.project.command(dict(type='retain_audio_sample_source',review_key=report['review_key'],**args));record=next(iter(self.project.audio_sample_sources.values()))
        self.assertIn('Retained WAV inputs',self.project.unsaved_sections);self.assertEqual(len(self.project.undo_stack),1)
        self.assertNotEqual(authored_state_key(self.project),key);self.assertEqual(read_source(self.project,record),input)
        recovered=download(self.project,record['receipt_key'],source_key(self.project));self.assertEqual(base64.b64decode(recovered['wav_base64']),input)
        self.assertTrue(recovered['historical_inputs']);self.project.undo();self.assertEqual(self.project._document(),document)
        self.project.redo();self.project.save();self.assertFalse(self.project.dirty)
        opened=ProjectService.open(self.project.root);self.assertEqual(opened.audio_sample_sources,self.project.audio_sample_sources)
        _,files=capture_export_inputs(self.project);relative=f"Authored/Audio/Sources/{record['wav_sha256']}.wav"
        self.assertEqual(files[relative],input)
        copied=create_copy(self.project,'WAV input copy',copy_review(self.project)['review_key']);clone=ProjectService.open(Path(copied['copied_project']))
        self.assertEqual(read_source(clone,record),input);self.assertEqual(clone.audio_sample_sources,self.project.audio_sample_sources)
        removal=review_removal(self.project,record['receipt_key'],source_key(self.project));self.assertFalse(removal['source_file_deleted'])
        self.project.command(dict(type='remove_audio_sample_source',receipt_key=record['receipt_key'],expected_authoring_key=source_key(self.project),review_key=removal['review_key']))
        self.assertEqual(self.project.audio_sample_sources,{});self.assertEqual(authored_state_key(self.project),key);self.assertTrue(source_path(self.project,record).exists())
        self.project.undo();self.assertEqual(read_source(self.project,record),input)
        self.assertEqual((self.project.imports,self.project.overrides,self.project.audio_overrides,self.project.audio_bank_overrides),native)

    def test_stale_reviews_malformed_upload_and_atomic_history_rejection(self):
        args,_=self.args();report=review(self.project,**args)
        with self.assertRaises(ProjectError):self.project.command(dict(type='retain_audio_sample_source',review_key='f'*64,**args))
        with self.assertRaises(ProjectError):review(self.project,**{**args,'wav_base64':'not base64!'})
        self.assertEqual(self.project.audio_sample_sources,{});self.assertEqual(self.project.undo_stack,[])
        self.retain();snapshot=deepcopy(self.project._document())
        with self.assertRaises(ProjectError):self.project.command(dict(type='retain_audio_sample_source',review_key=report['review_key'],**args))
        self.assertEqual(self.project._document(),snapshot);self.assertEqual(len(self.project.undo_stack),1)
        record=next(iter(self.project.audio_sample_sources.values()));broken=deepcopy(record);broken['sample_index']=True
        with self.assertRaises(ProjectError):validate_record(broken)
        with self.assertRaises(ProjectError):library(self.project,'f'*64)

    def test_changed_blob_fails_save_open_copy_recovery_and_redo(self):
        record,input=self.retain();self.project.save();path=source_path(self.project,record);path.write_bytes(input[:-1]+bytes([input[-1]^1]))
        for action in (self.project.save,lambda:ProjectService.open(self.project.root),lambda:copy_review(self.project),lambda:download(self.project,record['receipt_key'],source_key(self.project))):
            with self.assertRaises(ProjectError):action()
        self.project.undo();self.assertEqual(self.project.audio_sample_sources,{})
        with self.assertRaises(ProjectError):self.project.redo()
        self.assertEqual(self.project.audio_sample_sources,{});self.assertEqual(len(self.project.redo_stack),1)

    def test_frozen_build_wav_inputs_survive_current_removal_and_reject_tampering(self):
        record,input=self.retain();key=authored_state_key(self.project);identifier='0'*16;destination=self.project.root/'Builds'/identifier
        preserve_build_inputs(self.project,destination,key,self.project.root)
        manifest,files=read_build_inputs(self.project,identifier,key);self.assertEqual(files[record['wav_sha256']],input)
        self.project.undo();self.assertEqual(self.project.audio_sample_sources,{})
        source_path(self.project,record).write_bytes(b'changed current source')
        self.assertEqual(read_build_inputs(self.project,identifier,key)[1][record['wav_sha256']],input)
        path=destination/'wav-inputs'/key/(record['wav_sha256']+'.wav');path.write_bytes(input[:-1]+bytes([input[-1]^1]))
        with self.assertRaises(ProjectError):read_build_inputs(self.project,identifier,key)

    def test_http_exact_review_retain_library_download_and_removal(self):
        server=EditorServer(('127.0.0.1',0),self.project);worker=threading.Thread(target=server.serve_forever,daemon=True)
        def post(route,value):
            req=Request(f'http://127.0.0.1:{server.server_port}'+route,data=json.dumps(value).encode(),headers={'Content-Type':'application/json'})
            try:
                with urlopen(req,timeout=30) as response:return json.load(response)
            except HTTPError as error:
                error.msg=error.read().decode('utf-8');error.close();raise
        with patch.object(EditorHandler,'log_message',lambda *args:None):
            worker.start()
            try:
                args,input=self.args();proposal=post('/api/audio-sample-source-review',args)
                with self.assertRaises(HTTPError) as rejected:post('/api/audio-sample-source-review',{**args,'extra':1})
                rejected.exception.close();self.assertFalse(self.project.dirty)
                post('/api/audio-sample-source-retain',dict(review_key=proposal['review_key'],**args))
                key=source_key(self.project);value=post('/api/audio-sample-sources',dict(expected_authoring_key=key));self.assertEqual(len(value['imports']),1)
                receipt=value['imports'][0]['receipt_key'];params=dict(receipt_key=receipt,expected_authoring_key=key)
                recovery=post('/api/audio-sample-source-download',params);self.assertEqual(base64.b64decode(recovery['wav_base64']),input)
                remove=post('/api/audio-sample-source-removal-review',params);post('/api/command',dict(type='remove_audio_sample_source',review_key=remove['review_key'],**params))
                self.assertEqual(self.project.audio_sample_sources,{})
            finally:server.shutdown();server.server_close();worker.join(timeout=10)

if __name__=='__main__':unittest.main()
