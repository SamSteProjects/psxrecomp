from copy import deepcopy
from hashlib import sha256
import base64,os,unittest
import test_audio_authoring as base
from test_audio_sequence_midi import export_fixture
from sdk.sequence_replacement_authoring import review,read
from sdk.audio_authoring import source_key,_current
from sdk.project import ProjectError,ProjectService

@unittest.skipUnless(os.getenv('LEGAIA_DISC_BIN'),'Retail disc not configured')
class ReplacementAuthoring(unittest.TestCase):
 setUpClass=classmethod(base.AudioCommands.setUpClass.__func__)
 setUp=base.AudioCommands.setUp
 tearDown=base.AudioCommands.tearDown
 inspect=base.AudioCommands.inspect
 def test_review_apply_supersedes_operands_history_save_open_clear_and_tamper(self):
  from sdk.audio_authoring import review as operand_review
  opt=self.inspect();e=next(e for e in opt['current']['events'] if e['kind']=='note_on' and e['values'][1]);edit=dict(event_offset=e['offset'],values=[(e['values'][0]+1)%128,e['values'][1]])
  args=dict(asset_id=self.identifier,expected_entry_sha256=self.entry_hash,expected_authoring_key=source_key(self.project),edits=[edit]);r=operand_review(self.project,**args);self.project.command(dict(type='set_audio_sequence_operands',review_key=r['review_key'],**args))
  track=deepcopy(self.inspect()['current']);track['events'][1]['delta_ticks']+=1;raw=export_fixture(track)
  before=deepcopy(self.project._document());native=_current(self.project,self.identifier,self.entry_hash)[1]
  args=dict(asset_id=self.identifier,expected_entry_sha256=self.entry_hash,expected_authoring_key=source_key(self.project),midi_base64=base64.b64encode(raw).decode())
  r=review(self.project,**args);self.assertTrue(r['supersedes_sequence_operands']);self.assertEqual(self.project._document(),before)
  with self.assertRaises(ProjectError):self.project.command(dict(type='set_audio_sequence_replacement',review_key='f'*64,**args))
  self.project.command(dict(type='set_audio_sequence_replacement',review_key=r['review_key'],**args));after=deepcopy(self.project._document())
  self.assertNotIn(self.identifier,self.project.audio_overrides);b=self.project.audio_sequence_replacements[self.identifier]
  candidate=_current(self.project,self.identifier,self.entry_hash)[1];self.assertEqual(sha256(candidate).hexdigest(),r['after_entry_sha256']);self.assertEqual(read(self.project,self.identifier,b)[2],raw)
  self.project.undo();self.assertEqual(self.project._document(),before);self.assertEqual(_current(self.project,self.identifier,self.entry_hash)[1],native)
  self.project.redo();self.assertEqual(self.project._document(),after)
  self.project.save();p=ProjectService.open(self.project.root);self.assertEqual(p._document(),after);self.assertEqual(_current(p,self.identifier,self.entry_hash)[1],candidate)
  args=dict(asset_id=self.identifier,expected_entry_sha256=self.entry_hash,expected_authoring_key=source_key(p),midi_base64=base64.b64encode(raw).decode())
  again=review(p,**args);history=deepcopy((p.undo_stack,p.redo_stack));p.command(dict(type='set_audio_sequence_replacement',review_key=again['review_key'],**args));self.assertEqual((p.undo_stack,p.redo_stack),history);self.assertEqual(p._document(),after)
  from test_audio_native_allocation import NativeAllocation
  sample,_=NativeAllocation.retain(self);NativeAllocation.apply(self,sample)
  moved=_current(self.project,self.identifier,self.entry_hash)[1]
  from importer.audio_sequence_replacement import sequence_span
  at,size=sequence_span(candidate);new_at,new_size=sequence_span(moved)
  self.assertNotEqual(at,new_at);self.assertEqual(size,new_size);self.assertEqual(candidate[at:at+size],moved[new_at:new_at+new_size])
  self.project.save();self.assertEqual(ProjectService.open(self.project.root)._document(),self.project._document())
  self.project.command(dict(type='clear_audio_sequence_replacement',asset_id=self.identifier,expected_entry_sha256=self.entry_hash,expected_authoring_key=source_key(self.project)));self.assertEqual(self.project.audio_sequence_replacements,{})
  self.project.undo();self.assertEqual(_current(self.project,self.identifier,self.entry_hash)[1],moved)
  path=self.project.root/'Authored/Audio/SequenceReplacements'/(b['midi_sha256']+'.mid');path.write_bytes(bytes([raw[0]^1])+raw[1:])
  try:
   with self.assertRaises(ProjectError):ProjectService.open(self.project.root)
   with self.assertRaises(ProjectError):self.project.save()
  finally:path.write_bytes(raw)
