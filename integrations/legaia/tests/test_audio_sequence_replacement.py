from copy import deepcopy
from hashlib import sha256
import unittest
from importer.audio_sequence_replacement import replace_midi
from importer.audio_sequence import inspect_sequence
from importer.audio_catalog import decode_audio_entry
from importer.core import ImportError
from test_audio_sequence_midi import NATIVE,MIDI,ANCHORS,smf,export_fixture
from test_audio_catalog import bank,chunk

class Replacement(unittest.TestCase):
 def test_unchanged_preserves_running_status_and_opaque_tail(self):
  output,report,audit=replace_midi(NATIVE,MIDI,expected_current_sha256=sha256(NATIVE).hexdigest())
  self.assertEqual(output,NATIVE);self.assertTrue(audit['unchanged']);self.assertEqual(report,inspect_sequence(NATIVE))
 def test_changed_timing_insertions_headers_and_carrier_exact_bytes(self):
  anchors=bytes([0,255,81,3,6,26,128,0,255,88,4,3,3,24,8])
  midi=smf(anchors+bytes([0,192,5,0,144,62,110,129,0,128,62,0,0,255,47,0]),960)
  header=NATIVE[:8]+bytes([3,192,6,26,128,3,3])
  expected=header+bytes([0,192,5,0,144,62,110,129,0,128,62,0,0,255,47])+b'opaque'
  output,report,audit=replace_midi(NATIVE,midi,expected_current_sha256=sha256(NATIVE).hexdigest())
  self.assertEqual(output,expected);self.assertEqual(report['decoded_ticks'],128);self.assertEqual(report['header']['ppqn'],960)
  psyq=NATIVE[:4]+b'\0\1'+NATIVE[8:]
  legacy,legacy_report,_=replace_midi(psyq,midi,expected_current_sha256=sha256(psyq).hexdigest())
  self.assertEqual(legacy,expected[:4]+b'\0\1'+expected[8:]);self.assertEqual(legacy_report['header']['header_variant'],'psyq-u16-version')
  packed=chunk(0,bank())+chunk(1,bytes(32))+chunk(2,NATIVE)+b'carrier suffix'
  parsed=decode_audio_entry(packed);seq_chunk=parsed['chunks'][2];prior=packed[seq_chunk['payload_offset']:seq_chunk['payload_offset']+seq_chunk['size_bytes']]
  tail=prior[inspect_sequence(prior)['decoded_byte_end']:]
  # Source-owned tail is not interpreted as removable padding.
  stream=expected[:-6];replacement=stream+bytes((-(len(stream)+len(tail)))%4)+tail
  expected_pack=packed[:seq_chunk['header_offset']]+chunk(2,replacement)+b'carrier suffix'
  output,report,audit=replace_midi(packed,midi,expected_current_sha256=sha256(packed).hexdigest())
  self.assertEqual(output,expected_pack);self.assertEqual(audit['opaque_tail_sha256'],sha256(tail).hexdigest())
  self.assertEqual(output[:seq_chunk['header_offset']],packed[:seq_chunk['header_offset']]);self.assertTrue(output.endswith(b'carrier suffix'))
 def test_unknown_partial_metadata_and_changed_hash_refuse(self):
  for midi in [smf(ANCHORS+bytes([0,255,88,4,4,2,24,8,0,255,47,0])),smf(bytes([0,255,47,0])),MIDI[:-1]]:
   with self.assertRaises(ImportError):replace_midi(NATIVE,midi,expected_current_sha256=sha256(NATIVE).hexdigest())
  partial=NATIVE[:15]+bytes([0,255,1])
  with self.assertRaises(ImportError):replace_midi(partial,MIDI,expected_current_sha256=sha256(partial).hexdigest())
  with self.assertRaises(ImportError):replace_midi(NATIVE,MIDI,expected_current_sha256='f'*64)

class ReplacementFreshness(unittest.TestCase):
 def test_sdk_native_source_drift_refuses_publication(self):
  from types import SimpleNamespace
  from unittest.mock import patch
  import base64
  from sdk.audio_sequence_replacement import review
  from sdk.project import ProjectError
  current=(b'source',NATIVE,None,{'entry_sha256':'a'*64},None)
  with patch('sdk.audio_sequence_replacement.source_key',return_value='b'*64),patch('sdk.audio_sequence_replacement._current',side_effect=[current,(b'source',NATIVE+b'changed',None,current[3],None)]):
   with self.assertRaisesRegex(ProjectError,'native sources changed'):review(SimpleNamespace(mode='edit'),'audio://legaia/prot/0877','a'*64,'b'*64,base64.b64encode(MIDI).decode())
