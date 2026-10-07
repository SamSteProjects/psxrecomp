"""Readonly dynamic native ADPCM layers preserve fixed writer guards."""
from copy import deepcopy
import base64,os,unittest
from sdk.audio_sample_adpcm import preview
from sdk.audio_sample_allocation import options
from sdk.audio_sample_authoring import options as fixed_options
from sdk.audio_authoring import source_key
from sdk.project import ProjectError
import test_audio_authoring as sequence
import test_audio_native_allocation as allocation

@unittest.skipUnless(os.getenv('LEGAIA_DISC_BIN'),'Retail disc not configured')
class AllocatedAdpcm(unittest.TestCase):
    setUpClass=classmethod(sequence.AudioCommands.setUpClass.__func__)
    setUp=sequence.AudioCommands.setUp
    tearDown=sequence.AudioCommands.tearDown
    retain=allocation.NativeAllocation.retain
    apply=allocation.NativeAllocation.apply
    def test_current_and_retail_native_bytes_dynamic_extents_readonly_and_writer_guard(self):
        receipt,_=self.retain();self.apply(receipt);key=source_key(self.project);o=options(self.project,self.identifier,self.entry_hash,0,key);held=deepcopy(self.project._document())
        for layer,sha,expected_size in [('retail',o['source_sample']['source_sha256'],21504),('current',o['current_sample_sha256'],64)]:
            v=preview(self.project,self.identifier,self.entry_hash,0,key,layer,sha);self.assertEqual(v['schema_version'],'legaia.audio-sample-adpcm.v2');self.assertEqual(v['selected_sample']['size_bytes'],expected_size);self.assertEqual(len(base64.b64decode(v['adpcm_base64'])),expected_size);self.assertEqual(v['current_entry_sha256'],o['current_entry_sha256']);self.assertEqual(v['sample_entry_byte_offset'],o['current_sample_entry_byte_offset']);self.assertEqual(self.project._document(),held)
        with self.assertRaises(ProjectError):preview(self.project,self.identifier,self.entry_hash,0,key,'current',o['source_sample']['source_sha256'])
        with self.assertRaises(ProjectError):preview(self.project,self.identifier,self.entry_hash,0,'0'*64,'current',o['current_sample_sha256'])
        with self.assertRaises(ProjectError):fixed_options(self.project,self.identifier,self.entry_hash,0,key)
