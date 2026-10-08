from copy import deepcopy
from hashlib import sha256
import base64,json,os,unittest
import test_audio_authoring as base
from test_audio_sequence_midi import export_fixture
from sdk.audio_midi_sources import review,library,download,validate_collection,preserve_build_inputs
from sdk.audio_authoring import source_key,_current
from sdk.build import authored_state_key
from sdk.project import ProjectError,ProjectService,digest


@unittest.skipUnless(os.getenv('LEGAIA_DISC_BIN'),'Retail disc not configured')
class MidiSources(unittest.TestCase):
    setUpClass=classmethod(base.AudioCommands.setUpClass.__func__)
    setUp=base.AudioCommands.setUp
    tearDown=base.AudioCommands.tearDown
    inspect=base.AudioCommands.inspect

    def retain(self):
        report=deepcopy(self.inspect()['current']);e=next(e for e in report['events'] if e['kind']=='note_on' and e['values'][1]);e['values'][0]=(e['values'][0]+1)%128
        raw=export_fixture(report)
        args=dict(asset_id=self.identifier,expected_entry_sha256=self.entry_hash,expected_authoring_key=source_key(self.project),midi_base64=base64.b64encode(raw).decode())
        before=deepcopy((self.project._document(),self.project.undo_stack,self.project.redo_stack))
        result=review(self.project,**args)
        self.assertEqual(before,(self.project._document(),self.project.undo_stack,self.project.redo_stack))
        self.project.command(dict(type='retain_audio_midi_source',**args,review_key=result['review_key']))
        return raw,result

    def test_exact_recovery_history_save_open_and_tamper_refusal(self):
        before=deepcopy(self.project._document());native=_current(self.project,self.identifier,self.entry_hash)[1]
        raw,r=self.retain();after=deepcopy(self.project._document());self.assertEqual(_current(self.project,self.identifier,self.entry_hash)[1],native)
        receipt=next(iter(self.project.audio_midi_sources.values()));key=receipt['receipt_key'];path=self.project.root/'Authored/Audio/MidiSources'/(receipt['midi_sha256']+'.mid')
        self.assertEqual(path.read_bytes(),raw);self.assertEqual(base64.b64decode(download(self.project,key,source_key(self.project))['midi_base64']),raw)
        args=dict(asset_id=self.identifier,expected_entry_sha256=self.entry_hash,expected_authoring_key=source_key(self.project),midi_base64=base64.b64encode(raw).decode())
        fresh=review(self.project,**args);history=deepcopy((self.project.undo_stack,self.project.redo_stack))
        self.project.command(dict(type='retain_audio_midi_source',**args,review_key=fresh['review_key']))
        self.assertEqual(self.project._document(),after);self.assertEqual(history,(self.project.undo_stack,self.project.redo_stack))
        self.project.undo();self.assertEqual(self.project._document(),before);self.assertEqual(path.read_bytes(),raw)
        self.project.redo();self.assertEqual(self.project._document(),after);self.project.save();reopened=ProjectService.open(self.project.root)
        self.assertEqual(reopened._document(),after);self.assertEqual(base64.b64decode(download(reopened,key,source_key(reopened))['midi_base64']),raw)
        path.write_bytes(bytes([raw[0]^1])+raw[1:])
        try:
            with self.assertRaises(ProjectError):library(reopened,source_key(reopened))
            with self.assertRaises(ProjectError):ProjectService.open(self.project.root)
        finally:path.write_bytes(raw)

    def test_receipt_bounds_forgery_and_stale_review(self):
        raw,r=self.retain();record=next(iter(self.project.audio_midi_sources.values()))
        for field,value in [('byte_length',True),('source_scene_id','bad'),('midi_sha256','../outside'),('edits',[{'event_offset':True,'values':[1]}])]:
            bad={**deepcopy(record),field:value};bad.pop('receipt_key');bad['receipt_key']=digest(bad)
            with self.assertRaises(ProjectError):validate_collection({bad['receipt_key']:bad})
        rows={}
        for i in range(33):
            row=deepcopy(record);row['review_key']=sha256(str(i).encode()).hexdigest();row.pop('receipt_key');row['receipt_key']=digest(row);rows[row['receipt_key']]=row
            if i==31:validate_collection(rows)
        with self.assertRaises(ProjectError):validate_collection(rows)
        args=dict(asset_id=self.identifier,expected_entry_sha256=self.entry_hash,expected_authoring_key=source_key(self.project),midi_base64=base64.b64encode(raw).decode())
        with self.assertRaises(ProjectError):self.project.command(dict(type='retain_audio_midi_source',**args,review_key=r['review_key']))
        with self.assertRaises(ProjectError):library(self.project,'f'*64)

    def test_build_sidecar_identity_and_exact_bytes(self):
        before_key=authored_state_key(self.project);native=_current(self.project,self.identifier,self.entry_hash)[1]
        raw,_=self.retain();key=authored_state_key(self.project);self.assertNotEqual(key,before_key);self.assertEqual(_current(self.project,self.identifier,self.entry_hash)[1],native)
        destination=self.project.root/'Builds/receipt-check';manifest=preserve_build_inputs(self.project,destination,key,self.project.root)
        directory=destination/'midi-inputs'/key;row=manifest['files'][0]
        self.assertEqual((directory/row['file']).read_bytes(),raw);self.assertEqual(row['sha256'],sha256(raw).hexdigest())
        loaded=json.loads((directory/'manifest.json').read_text(encoding='utf-8'));self.assertEqual(loaded,manifest)
        self.assertEqual(loaded['manifest_key'],digest({k:v for k,v in loaded.items() if k!='manifest_key'}));self.assertFalse(loaded['native_content_changed'])
        with self.assertRaises(ProjectError):preserve_build_inputs(self.project,destination,'f'*64,self.project.root)


if __name__=='__main__':unittest.main()
