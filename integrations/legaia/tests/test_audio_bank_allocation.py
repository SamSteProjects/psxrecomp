"""Current fixed bank tables and note links inside allocated sample carriers."""
from copy import deepcopy
import os,unittest
from sdk.audio_bank_authoring import options,review
from sdk.audio_authoring import source_key,options as sequence_options
from sdk.audio_note_links import inspect
from sdk.scene_preview import source_key as resource_key
from sdk.audio_composition import read_entry
from sdk.project import ProjectService
import test_audio_authoring as sequence
import test_audio_native_allocation as allocation

@unittest.skipUnless(os.getenv('LEGAIA_DISC_BIN'),'Retail disc not configured')
class BankAllocation(unittest.TestCase):
    setUpClass=classmethod(sequence.AudioCommands.setUpClass.__func__)
    setUp=sequence.AudioCommands.setUp
    tearDown=sequence.AudioCommands.tearDown
    retain=allocation.NativeAllocation.retain
    apply=allocation.NativeAllocation.apply
    def test_bank_apply_history_clear_and_current_note_rows(self):
        receipt,_=self.retain();self.apply(receipt);samples=deepcopy(self.project.audio_sample_overrides);before=self.project._document();current=read_entry(self.project,self.identifier)
        opt=options(self.project,self.identifier,self.entry_hash,resource_key(self.project));self.assertEqual(opt['schema_version'],'legaia.audio-bank-authoring.v2');self.assertEqual(opt['current_layout']['bank_size_bytes'],opt['current']['header']['declared_size']);self.assertNotEqual(opt['current']['header']['declared_size'],opt['retail']['header']['declared_size'])
        row=next(r for r in opt['current']['parameters'] if r['section']=='header' and r['field']=='master_volume');edits=[dict(section='header',field='master_volume',value=(row['value']+1)%256)];proposal=review(self.project,self.identifier,self.entry_hash,source_key(self.project),edits);self.assertEqual(self.project._document(),before)
        self.project.command(dict(type='set_audio_bank_parameters',asset_id=self.identifier,expected_entry_sha256=self.entry_hash,expected_authoring_key=source_key(self.project),edits=edits,review_key=proposal['review_key']));candidate=read_entry(self.project,self.identifier);changed=[i for i,(a,b) in enumerate(zip(current,candidate)) if a!=b];self.assertEqual(changed,proposal['native_audit']['changed_entry_byte_offsets']);self.assertEqual(samples,self.project.audio_sample_overrides)
        self.project.undo();self.assertEqual(read_entry(self.project,self.identifier),current);self.project.redo();self.assertEqual(read_entry(self.project,self.identifier),candidate);self.project.save();self.assertEqual(ProjectService.open(self.project.root)._document(),self.project._document())
        seq=sequence_options(self.project,self.identifier,self.entry_hash,resource_key(self.project));index=next(e['index'] for e in seq['current']['events'] if e['kind']=='note_on' and e['values'][1]);held=self.project._document();links=inspect(self.project,self.identifier,self.entry_hash,resource_key(self.project),source_key(self.project),index);self.assertEqual(self.project._document(),held);self.assertEqual(links['schema_version'],'legaia.audio-note-links.v2');bank=links['bank'];self.assertEqual(bank['schema_version'],'legaia.audio-current-bank-inspection.v1');self.assertEqual(bank['samples'][0]['size_bytes'],64);self.assertEqual(bank['samples'][0]['source_sha256'],receipt['candidate_sample_sha256']);self.assertEqual(bank['current_layout']['entry_sha256'],seq['current_entry_sha256']);self.assertEqual(bank['source_record']['entry_sha256'],self.entry_hash)
        self.project.command(dict(type='clear_audio_bank_parameters',asset_id=self.identifier,expected_entry_sha256=self.entry_hash,expected_authoring_key=source_key(self.project)));self.assertEqual(read_entry(self.project,self.identifier),current)
