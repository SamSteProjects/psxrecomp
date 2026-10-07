"""Private ADPCM source qualification is bounded, read-only and layer-specific."""
import base64
from copy import deepcopy
from hashlib import sha256
from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import patch
from sdk.audio_sample_adpcm import preview
from sdk.project import ProjectError

def block(header=0,flags=0,nibbles=0):return bytes([header,flags])+bytes([nibbles])*14

class NativeSample(TestCase):
    def setUp(self):
        self.raw=block(0,0,0x11)+block(0x10,4)+block(0x10,3)
        self.current=self.raw[:-1]+b'\x12';self.project=SimpleNamespace(state={'unchanged':True})
        self.key='a'*64;self.record={'entry_sha256':'b'*64}
        self.mock=patch('sdk.audio_sample_adpcm._current',return_value=(self.raw,self.current,b'',self.record,{'size_bytes':len(self.raw)},0,self.raw,None));self.mock.start();self.addCleanup(self.mock.stop)
        self.keys=patch('sdk.audio_sample_adpcm.source_key',return_value=self.key);self.source=self.keys.start();self.addCleanup(self.keys.stop)

    def request(self,layer='retail',raw=None):
        return preview(self.project,'audio://legaia/prot/0877','b'*64,3,self.key,layer,sha256(self.raw if raw is None else raw).hexdigest())

    def test_layers_and_complete_bytes_without_state_changes(self):
        before=deepcopy(self.project.state)
        for layer,raw in [('retail',self.raw),('current',self.current)]:
            report=self.request(layer,raw);self.assertEqual(base64.b64decode(report['adpcm_base64']),raw)
            self.assertEqual(report['sample_sha256'],sha256(raw).hexdigest());self.assertEqual(report['current_entry_sha256'],sha256(self.current).hexdigest())
            self.assertEqual(report['waveform']['decoded_frames'],84);self.assertFalse(report['project_changed']);self.assertEqual(report['runtime_state'],'not_observed')
        self.assertEqual(self.project.state,before)

    def test_invalid_layer_hash_shift_repeat_and_bounds(self):
        for layer in ['proposed','live',None]:
            with self.assertRaises(ProjectError):self.request(layer)
        with self.assertRaises(ProjectError):self.request(raw=b'forged')
        for raw in [block(0x0d,7),block(0,3),block(0,4),block(0,8),block(0x50,7),block(0,7)*4097,b'']:
            with patch('sdk.audio_sample_adpcm._current',return_value=(raw,raw,b'',self.record,{'size_bytes':len(raw)},0,raw,None)):
                with self.assertRaises(ProjectError):self.request(raw=raw)

    def test_source_change_during_qualification_rejects(self):
        self.source.side_effect=[self.key,'c'*64]
        with self.assertRaises(ProjectError):self.request()

    def test_nonrepeat_end_accepts_complete_source_and_retains_opaque_tail(self):
        raw=block(0,0,0x81)+block(0x20,1,0x37)+b'opaque tail'
        with patch('sdk.audio_sample_adpcm._current',return_value=(raw,raw,b'',self.record,{'size_bytes':len(raw)},0,raw,None)):
            report=self.request(raw=raw)
        self.assertEqual(base64.b64decode(report['adpcm_base64']),raw)
        self.assertEqual(report['waveform']['decoded_frames'],56)
        self.assertEqual(report['waveform']['termination']['reason'],'encoded-end')
        self.assertEqual(report['waveform']['remaining_bytes'],11)
