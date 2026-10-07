"""Shared request qualification must retain byte freshness and graph provenance."""
from copy import deepcopy
from hashlib import sha256
import unittest
import os
from unittest.mock import patch

import test_project_asset_references as fixtures
import test_audio_input_assets as wav_fixtures
from sdk.asset_references import assemble_project
from sdk.audio_reference_snapshot import AudioReferenceSnapshot
from sdk.project import ProjectError, digest


class AudioReferenceSnapshots(unittest.TestCase):
 def setUp(self):
  fixtures.ProjectAssetReferences.setUp(self)
  self.native='audio://fixture/native';self.wav='audio-input://legaia/wav/'+'a'*64
  self.body=b'original carrier';self.bank=b'original bank'
  self.record=dict(entry_sha256=sha256(self.body).hexdigest(),pieces=[],carrier='fixture')
  self.binding=dict(source_scene_id='scene://fixture',source_record=self.record,bank_sha256=sha256(self.bank).hexdigest(),samples=[dict(sample_index=0,receipt_key='b'*64)])
  self.p.audio_sample_overrides[self.native]=deepcopy(self.binding)
  self.inputs=dict(assets={self.wav:dict(name='Retained WAV')},receipts={},records_by_scene={})
  self.proof=dict(native_asset_id=self.native,wav_asset_id=self.wav,binding_scene_id='scene://fixture',capture_scene_id='scene://fixture',sample_index=0,receipt_key='b'*64,binding_sha256=digest(self.binding),retail_entry_sha256=self.record['entry_sha256'],current_entry_sha256='c'*64,current_sample_sha256='d'*64,sample_entry_byte_offset=128,sample_size_bytes=32)
  self.catalogs['scene://fixture']['records'].append(dict(id=self.native,kind='audio',source_record=dict(sha256=self.record['entry_sha256'])))
 def mocks(self):
  return (patch('sdk.audio_input_assets.inventory',side_effect=lambda p:deepcopy(self.inputs)),
   patch('sdk.audio_input_bindings.current',return_value=[deepcopy(self.proof)]),
   patch('sdk.audio_bank_authoring._source',return_value=(self.body,self.bank,deepcopy(self.record))))
 def test_64_scene_project_composes_once_and_rechecks_native_once(self):
  for index in range(62):
   scene='scene://extra'+str(index);doc=deepcopy(self.p.imports['scene://other']);doc['scene']['semantic_id']=scene;doc['scene']['name']='extra'+str(index)
   self.p.imports[scene]=doc;self.catalogs[scene]=dict(scene_id=scene,source_key='3'*64,records=[],limitations=[])
  before=deepcopy(self.p._document());m=self.mocks()
  with m[0] as inventory,m[1] as qualify,m[2] as native:
   report=assemble_project(self.p,self.catalogs,self.wav)
  self.assertEqual(inventory.call_count,2);self.assertEqual(qualify.call_count,1);self.assertEqual(native.call_count,1)
  self.assertEqual(len(report['coverage']['scenes']),64)
  self.assertEqual(report['incoming'][0]['current_wav_binding_evidence'],self.proof)
  self.assertEqual(report['incoming'][0]['id'],digest({k:v for k,v in report['incoming'][0].items() if k!='id'}))
  self.assertEqual(self.p._document(),before)
 def test_detached_proofs_navigation_reuse_and_project_ownership(self):
  m=self.mocks()
  with m[0],m[1],m[2]:
   snapshot=AudioReferenceSnapshot(self.p)
   snapshot.inputs()['assets'].clear();snapshot.bindings()[0]['receipt_key']='bad'
   self.assertEqual(snapshot.bindings()[0],self.proof);self.assertIn(self.wav,snapshot.inputs()['assets'])
   self.p.active_scene='scene://other';snapshot.verify(self.p)
   self.p.audio_sample_overrides[self.native]['samples'][0]['sample_index']=1
   with self.assertRaisesRegex(ProjectError,'project changed'):snapshot.verify(self.p)
 def test_retained_file_drift_rejects_publication(self):
  m=self.mocks()
  with m[0] as inventory,m[1],m[2] as native:
   inventory.side_effect=[deepcopy(self.inputs),dict(assets={},receipts={},records_by_scene={})]
   with self.assertRaisesRegex(ProjectError,'inputs changed'):assemble_project(self.p,self.catalogs,self.wav)
   native.assert_not_called()
 def test_native_body_bank_and_ownership_drift_reject_publication(self):
  for body,bank,record in [(b'changed',self.bank,self.record),(self.body,b'changed',self.record),(self.body,self.bank,{**self.record,'carrier':'changed'})]:
   with self.subTest(body=body,bank=bank,record=record):
    m=self.mocks()
    with m[0],m[1],m[2] as native:
     native.return_value=(body,bank,deepcopy(record))
     with self.assertRaisesRegex(ProjectError,'native ownership changed'):assemble_project(self.p,self.catalogs,self.wav)
 def test_mutation_during_native_recheck_rejects(self):
  m=self.mocks()
  def mutate(*args):
   self.p.audio_sample_overrides.clear()
   return self.body,self.bank,self.record
  with m[0],m[1],m[2] as native:
   native.side_effect=mutate
   with self.assertRaisesRegex(ProjectError,'project changed'):assemble_project(self.p,self.catalogs,self.wav)
 def test_retained_bytes_rechecked_even_when_size_and_mtime_held(self):
  fixture=wav_fixtures.AudioInputAssets();fixture.setUp();self.addCleanup(fixture.doCleanups)
  from sdk.audio_sample_sources import source_path
  receipt=next(iter(fixture.project.audio_sample_sources.values()))
  path=source_path(fixture.project,receipt);original=path.read_bytes();stamp=path.stat()
  snapshot=AudioReferenceSnapshot(fixture.project)
  changed=bytearray(original);changed[44]^=1
  try:
   path.write_bytes(changed);os.utime(path,ns=(stamp.st_atime_ns,stamp.st_mtime_ns))
   self.assertEqual(path.stat().st_size,stamp.st_size);self.assertEqual(path.stat().st_mtime_ns,stamp.st_mtime_ns)
   with self.assertRaises(ProjectError):snapshot.verify(fixture.project)
  finally:path.write_bytes(original)
  snapshot.verify(fixture.project)


if __name__=='__main__':unittest.main()
