"""Source-relative SEQ operands through moved native sample carriers."""
from copy import deepcopy
import os,unittest
from sdk.audio_authoring import options,review,proposed_inspection,source_key
from sdk.scene_preview import source_key as resource_key
from sdk.audio_composition import read_entry
from sdk.project import ProjectService,ProjectError
from importer.audio_catalog import decode_audio_entry
import test_audio_native_allocation as allocation
import test_audio_authoring as sequence

@unittest.skipUnless(os.getenv('LEGAIA_DISC_BIN'),'Retail disc not configured')
class SequenceAllocation(unittest.TestCase):
    setUpClass=classmethod(sequence.AudioCommands.setUpClass.__func__)
    setUp=sequence.AudioCommands.setUp
    tearDown=sequence.AudioCommands.tearDown
    retain=allocation.NativeAllocation.retain
    apply=allocation.NativeAllocation.apply
    def test_current_review_proposed_apply_clear_history_and_save(self):
        receipt,_=self.retain();self.apply(receipt);sample_binding=deepcopy(self.project.audio_sample_overrides)
        opt=options(self.project,self.identifier,self.entry_hash,resource_key(self.project));self.assertEqual(opt['schema_version'],'legaia.audio-sequence-authoring.v2')
        current=read_entry(self.project,self.identifier);at=decode_audio_entry(current)['chunks'][2]['payload_offset'];self.assertEqual(opt['current_sequence_offset'],at);self.assertNotEqual(at,opt['source_record']['sequence_offset'])
        event=next(e for e in opt['current']['events'] if e['channel'] is not None);edit=dict(event_offset=event['offset'],values=[(event['values'][0]+1)%128,*event['values'][1:]])
        before=self.project._document();key=source_key(self.project);v=review(self.project,self.identifier,self.entry_hash,key,[edit]);self.assertEqual(self.project._document(),before)
        self.assertEqual(v['native_audit']['sequence_offset'],at);self.assertTrue(all(at<=i<at+opt['source_record']['sequence_size_bytes'] for i in v['native_audit']['changed_entry_byte_offsets']))
        report=proposed_inspection(self.project,self.identifier,self.entry_hash,key,[edit],v['review_key']);self.assertEqual(report['current_sequence_offset'],at)
        self.project.command(dict(type='set_audio_sequence_operands',asset_id=self.identifier,expected_entry_sha256=self.entry_hash,expected_authoring_key=key,edits=[edit],review_key=v['review_key']))
        candidate=read_entry(self.project,self.identifier);self.assertEqual(candidate[:at],current[:at]);end=at+opt['source_record']['sequence_size_bytes'];self.assertEqual(candidate[end:],current[end:]);self.assertEqual(self.project.audio_sample_overrides,sample_binding)
        self.project.undo();self.assertEqual(read_entry(self.project,self.identifier),current);self.project.redo();self.assertEqual(read_entry(self.project,self.identifier),candidate)
        self.project.save();fresh=ProjectService.open(self.project.root);self.assertEqual(fresh._document(),self.project._document())
        with self.assertRaises(ProjectError):review(self.project,self.identifier,self.entry_hash,key,[edit])
        self.project.command(dict(type='clear_audio_sequence_operands',asset_id=self.identifier,expected_entry_sha256=self.entry_hash,expected_authoring_key=source_key(self.project)));self.assertEqual(read_entry(self.project,self.identifier),current)
