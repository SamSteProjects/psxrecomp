"""Native sample history and disjoint bank/SEQ/sample composition."""
from copy import deepcopy
from pathlib import Path
from hashlib import sha256
import base64,json,os,threading,unittest
from urllib.request import Request,urlopen
from urllib.error import HTTPError
from unittest.mock import patch
import test_audio_authoring as seq_tests
from test_audio_sample_authoring import independent_decode,wav
from importer.audio_bank import inspect_bank
from importer.pipeline import _disc_context
from sdk.project import ProjectService,ProjectError
from sdk.audio_bank_authoring import _source,options as bank_options,review as bank_review
from sdk.audio_authoring import source_key,options as seq_options,review as seq_review
from sdk.audio_sample_sources import review as source_review,read_source,source_path,review_removal
from sdk.audio_sample_authoring import options,review,read,prepare_overlays,preview
from sdk.audio_composition import read_entry,prepare_overlays as composed_overlays
from sdk.scene_preview import source_key as resource_key
from sdk.project_copy import review as copy_review,create_copy
from sdk.build import authored_state_key,build_report,package_change_kinds
from sdk.server import EditorServer,EditorHandler

@unittest.skipUnless(os.getenv('LEGAIA_DISC_BIN'),'Retail disc not configured')
class SampleWorkflow(unittest.TestCase):
    setUpClass=classmethod(seq_tests.AudioCommands.setUpClass.__func__)
    setUp=seq_tests.AudioCommands.setUp
    tearDown=seq_tests.AudioCommands.tearDown
    inspect=seq_tests.AudioCommands.inspect
    first_edit=seq_tests.AudioCommands.first_edit
    change=seq_tests.AudioCommands.change

    def retain(self,index=0):
        body,bank,record=_source(self.project,self.identifier,self.entry_hash,self.project.active_scene)
        profile=inspect_bank(bank);row=profile['samples'][index];raw=bank[row['offset']:row['offset']+row['size_bytes']]
        input=wav([int(v*.5) for v in independent_decode(raw)],32000)
        args=dict(asset_id=self.identifier,expected_entry_sha256=self.entry_hash,expected_bank_sha256=profile['bank_sha256'],sample_index=index,
            expected_sample_sha256=row['source_sha256'],expected_authoring_key=source_key(self.project),wav_base64=base64.b64encode(input).decode('ascii'))
        proposal=source_review(self.project,**args);self.project.command(dict(type='retain_audio_sample_source',review_key=proposal['review_key'],**args))
        record=next(r for r in self.project.audio_sample_sources.values() if r['sample_index']==index)
        return record,input
    def args(self,index=0,operation='apply',receipt=None):
        value=dict(asset_id=self.identifier,expected_entry_sha256=self.entry_hash,sample_index=index,expected_authoring_key=source_key(self.project),operation=operation)
        if operation=='apply':value['receipt_key']=receipt['receipt_key']
        return value
    def apply(self,index=0,operation='apply',receipt=None):
        args=self.args(index,operation,receipt);report=review(self.project,**args)
        command={k:v for k,v in args.items() if k!='operation'}
        self.project.command(dict(type='set_audio_sample_wav' if operation=='apply' else 'clear_audio_sample_wav',review_key=report['review_key'],**command))
        return report

    def test_three_families_compose_clear_independently_and_source_removal_blocks(self):
        receipt,_=self.retain();body,_,_=_source(self.project,self.identifier,self.entry_hash,self.project.active_scene)
        _,seqedit=self.first_edit();self.change([seqedit])
        value=bank_options(self.project,self.identifier,self.entry_hash,resource_key(self.project));parameter=value['retail']['parameters'][0]
        args=dict(asset_id=self.identifier,expected_entry_sha256=self.entry_hash,expected_authoring_key=source_key(self.project),edits=[dict(section='header',field='master_volume',value=(parameter['value']+1)%256)])
        proposal=bank_review(self.project,**args);self.project.command(dict(type='set_audio_bank_parameters',review_key=proposal['review_key'],**args))
        before=read_entry(self.project,self.identifier);document=deepcopy(self.project._document());arguments=self.args(receipt=receipt)
        proposed=review(self.project,**arguments);self.assertEqual(self.project._document(),document)
        self.assertEqual(proposed['native_audit']['before_entry_sha256'],sha256(before).hexdigest())
        self.apply(receipt=receipt);all_three=read_entry(self.project,self.identifier)
        self.assertNotEqual(all_three,before);self.assertIn('Native audio samples',self.project.unsaved_sections)
        self.assertTrue(bank_options(self.project,self.identifier,self.entry_hash,resource_key(self.project))['samples_authored'])
        self.assertTrue(seq_options(self.project,self.identifier,self.entry_hash,resource_key(self.project))['samples_authored'])
        state=options(self.project,self.identifier,self.entry_hash,0,source_key(self.project));self.assertEqual(state['current_sample_sha256'],receipt['candidate_sample_sha256'])
        self.assertEqual(state['current']['decoded_frames'],state['retail']['decoded_frames'])
        rows=[r for r in self.project.authored_assets() if r['id']==self.identifier];self.assertEqual(len(rows),1);self.assertEqual(len(rows[0]['changes']),3)
        with self.assertRaises(ProjectError):review_removal(self.project,receipt['receipt_key'],source_key(self.project))
        with _disc_context(self.disc) as (image,_,_,archive):overlays,changes=composed_overlays(self.project,image,archive)
        self.assertEqual(len(overlays),1);self.assertEqual(overlays[0]['payload'],all_three)
        self.assertEqual(overlays[0]['source_kind'],'raw_PROT_audio_operands')
        self.assertEqual(package_change_kinds(changes),['native audio bank parameters','native audio samples','native audio sequence operands'])
        report=build_report(dict(edits=changes,overlays=overlays,validation={}));self.assertTrue(any('sample_index' in r for r in report['changes']))
        self.project.command(dict(type='clear_audio_bank_parameters',asset_id=self.identifier,expected_entry_sha256=self.entry_hash,expected_authoring_key=source_key(self.project)))
        sample_with_sequence=read_entry(self.project,self.identifier)
        self.project.command(dict(type='clear_audio_sequence_operands',asset_id=self.identifier,expected_entry_sha256=self.entry_hash,expected_authoring_key=source_key(self.project)))
        sample_only=read_entry(self.project,self.identifier);self.assertNotEqual(sample_only,body)
        self.apply(operation='clear');self.assertEqual(self.project.audio_sample_overrides,{})
        self.assertEqual(read_entry(self.project,self.identifier,body),body)
        self.project.undo();self.assertEqual(read_entry(self.project,self.identifier),sample_only)
        self.project.undo();self.assertEqual(read_entry(self.project,self.identifier),sample_with_sequence)

    def test_multi_sample_noop_history_save_open_copy_and_corrupt_redo(self):
        receipt,input=self.retain();base_key=authored_state_key(self.project)
        self.apply(receipt=receipt);original=deepcopy(self.project._document());key=authored_state_key(self.project)
        self.assertNotEqual(key,base_key);length=len(self.project.undo_stack)
        self.assertTrue(self.apply(receipt=receipt)['no_change']);self.assertEqual(len(self.project.undo_stack),length)
        self.project.save();opened=ProjectService.open(self.project.root);self.assertEqual(read_entry(opened,self.identifier),read_entry(self.project,self.identifier))
        clone=create_copy(self.project,'Native sample copy',copy_review(self.project)['review_key']);copied=ProjectService.open(Path(clone['copied_project']))
        self.assertEqual(read_entry(copied,self.identifier),read_entry(self.project,self.identifier))
        second,_=self.retain(1);first_current=read_entry(self.project,self.identifier);self.apply(1,receipt=second)
        self.assertEqual(len(self.project.audio_sample_overrides[self.identifier]['samples']),2)
        self.apply(1,operation='clear');self.assertEqual(read_entry(self.project,self.identifier),first_current)
        self.project.undo();self.project.undo();self.project.undo();self.project.undo()
        self.assertEqual(self.project.audio_sample_overrides,{})
        source_path(self.project,receipt).write_bytes(input[:-1]+bytes([input[-1]^1]))
        with self.assertRaises(ProjectError):self.project.redo()
        self.assertEqual(self.project.audio_sample_overrides,{})

    def test_stale_review_exact_shapes_and_modified_saved_binding(self):
        receipt,_=self.retain();args=self.args(receipt=receipt);proposal=review(self.project,**args)
        _,edit=self.first_edit();self.change([edit]);before=deepcopy(self.project._document())
        value={k:v for k,v in args.items() if k!='operation'}
        with self.assertRaises(ProjectError):self.project.command(dict(type='set_audio_sample_wav',review_key=proposal['review_key'],**value))
        self.assertEqual(self.project._document(),before)
        with self.assertRaises(ProjectError):review(self.project,**{**self.args(receipt=receipt),'sample_index':True})
        self.apply(receipt=receipt);path=self.project.save();document=json.loads(path.read_text(encoding='utf-8'))
        document['audio_sample_overrides'][self.identifier]['samples'][0]['receipt_key']='f'*64
        path.write_text(json.dumps(document),encoding='utf-8')
        with self.assertRaises(ProjectError):ProjectService.open(path)

    def test_http_current_review_apply_clear_and_exact_fields(self):
        receipt,_=self.retain();server=EditorServer(('127.0.0.1',0),self.project);thread=threading.Thread(target=server.serve_forever,daemon=True)
        def post(route,value):
            request=Request(f'http://127.0.0.1:{server.server_port}'+route,data=json.dumps(value).encode(),headers={'Content-Type':'application/json'})
            try:
                with urlopen(request,timeout=30) as response:return json.load(response)
            except HTTPError as error:error.msg=error.read().decode('utf-8');error.close();raise
        with patch.object(EditorHandler,'log_message',lambda *args:None):
            thread.start()
            try:
                args=self.args(receipt=receipt);proposal=post('/api/audio-sample-review',args)
                document=deepcopy(self.project._document())
                base={k:v for k,v in args.items() if k not in ('operation','receipt_key')}
                retail_query=dict(**base,layer='retail',expected_sample_sha256=receipt['source_sample_sha256'])
                retail=post('/api/audio-sample-preview',retail_query)
                proposed_query=dict(**args,layer='proposed',review_key=proposal['review_key'],expected_sample_sha256=proposal['proposed_sample_sha256'])
                proposed=post('/api/audio-sample-preview',proposed_query)
                self.assertEqual(self.project._document(),document)
                self.assertEqual(retail['waveform']['sample_rate'],None)
                self.assertEqual(proposed['waveform']['decoded_frames'],retail['waveform']['decoded_frames'])
                self.assertEqual(sha256(base64.b64decode(proposed['pcm_base64'])).hexdigest(),proposed['pcm_sha256'])
                self.assertEqual(proposed['pcm_sha256'],proposal['native_audit']['sample']['decoded_pcm_sha256'])
                self.assertNotEqual(retail['pcm_sha256'],proposed['pcm_sha256'])
                with self.assertRaises(HTTPError):post('/api/audio-sample-preview',{**retail_query,'receipt_key':receipt['receipt_key']})
                with self.assertRaises(HTTPError):post('/api/audio-sample-preview',{**proposed_query,'review_key':'f'*64})
                with self.assertRaises(HTTPError):post('/api/audio-sample-preview',{**proposed_query,'expected_sample_sha256':'f'*64})
                with self.assertRaises(HTTPError):post('/api/audio-sample-review',{**args,'extra':1})
                command={k:v for k,v in args.items() if k!='operation'}
                post('/api/command',dict(type='set_audio_sample_wav',review_key=proposal['review_key'],**command))
                query={k:v for k,v in self.args(receipt=receipt).items() if k not in ('operation','receipt_key')}
                self.assertIsNotNone(post('/api/audio-sample-authoring',query)['authored_sample'])
                current_query=dict(**query,layer='current',expected_sample_sha256=proposal['proposed_sample_sha256'])
                current=post('/api/audio-sample-preview',current_query)
                self.assertEqual(current['pcm_sha256'],proposed['pcm_sha256'])
                with self.assertRaises(HTTPError):post('/api/audio-sample-preview',proposed_query)
                clear=self.args(operation='clear');report=post('/api/audio-sample-review',clear)
                clear_preview=post('/api/audio-sample-preview',dict(**clear,layer='proposed',review_key=report['review_key'],expected_sample_sha256=report['proposed_sample_sha256']))
                self.assertEqual(clear_preview['pcm_sha256'],retail['pcm_sha256'])
                post('/api/command',dict(type='clear_audio_sample_wav',review_key=report['review_key'],**{k:v for k,v in clear.items() if k!='operation'}))
                self.assertEqual(self.project.audio_sample_overrides,{})
            finally:server.shutdown();server.server_close();thread.join(timeout=10)

if __name__=='__main__':unittest.main()
