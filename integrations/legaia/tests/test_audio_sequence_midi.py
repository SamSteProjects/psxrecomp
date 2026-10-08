"""Independent SMF bytes, native operands and strict interchange boundaries."""
from copy import deepcopy
import unittest
from importer.audio_sequence_midi import decode_midi, midi_operand_edits, MAX_MIDI_BYTES
from importer.audio_sequence import inspect_sequence
from importer.audio_sequence_authoring import replace_sequence_operands
from importer.core import ImportError
from hashlib import sha256
from test_audio_catalog import seq


def smf(track, ppqn=480):
    return b'MThd\0\0\0\6\0\0\0\1'+ppqn.to_bytes(2, 'big')+b'MTrk'+len(track).to_bytes(4, 'big')+bytes(track)


ANCHORS = bytes([0,255,81,3,7,161,32,0,255,88,4,4,2,24,8])
NATIVE = seq()[:15]+bytes([0,144,60,100,131,96,60,0,0,255,47])+b'opaque'
MIDI = smf(ANCHORS+bytes([0,144,60,100,131,96,60,0,0,255,47,0]))


def export_fixture(report):
    """Test-only encoder independent of the production browser exporter."""
    def vlq(value):
        values=[value & 127]
        while value >> 7:
            value >>= 7
            values.insert(0, (value & 127)|128)
        return bytes(values)
    h=report['header']
    track=bytearray(b'\0\xff\x51\x03'+h['initial_tempo_us_per_quarter'].to_bytes(3,'big')
        +bytes([0,255,88,4,h['time_signature_numerator'],h['time_signature_denominator_power'],24,8]))
    for e in report['events']:
        track.extend(vlq(e['delta_ticks']))
        if e['kind']=='set_tempo':track.extend(b'\xff\x51\x03'+e['values'][0].to_bytes(3,'big'))
        elif e['kind']=='end_of_track':track.extend(b'\xff\x2f\0')
        else:track.extend(bytes([e['status'],*e['values']]))
    return smf(track,h['ppqn'])


class MidiCodec(unittest.TestCase):
    def test_literal_running_status_and_native_readback(self):
        self.assertEqual(midi_operand_edits(MIDI,NATIVE),[])
        edited=bytearray(MIDI);edited[39:41]=bytes([62,110]);edited[43]=62
        edits=midi_operand_edits(bytes(edited),NATIVE)
        self.assertEqual(edits,[{'event_offset':15,'values':[62,110]},{'event_offset':19,'values':[62,0]}])
        candidate,audit=replace_sequence_operands(NATIVE,NATIVE,expected_source_sha256=sha256(NATIVE).hexdigest(),expected_current_sha256=sha256(NATIVE).hexdigest(),edits=edits)
        expected=bytearray(NATIVE);expected[17:19]=bytes([62,110]);expected[21]=62
        self.assertEqual(candidate,bytes(expected));self.assertEqual(candidate[-6:],b'opaque')
        self.assertEqual(audit['changed_byte_offsets'],[17,18,21])

    def test_all_channel_families_tempo_and_explicit_status_after_meta(self):
        native=seq()[:15]+bytes([0,128,1,2,0,144,3,4,0,160,5,6,0,176,7,8,0,192,9,0,208,10,0,224,11,12,0,255,81,7,161,32,0,144,60,1,0,255,47])
        source=inspect_sequence(native);proposed=deepcopy(source)
        for e in proposed['events'][:-1]:e['values']=[v+1 for v in e['values']]
        edits=midi_operand_edits(export_fixture(proposed),native)
        self.assertEqual(len(edits),9)
        raw=export_fixture(source);self.assertEqual(midi_operand_edits(raw,native),[])
        # Removing a required channel status immediately after tempo is invalid.
        index=raw.rfind(bytes([0,144,60,1]));track=raw[22:index+1]+raw[index+2:]
        with self.assertRaises(ImportError):decode_midi(smf(track))

    def test_truncation_header_metadata_layout_and_extent_refuse(self):
        for end in range(len(MIDI)):
            with self.assertRaises(ImportError):decode_midi(MIDI[:end])
        for offset,value in [(0,0),(4,1),(8,1),(11,2),(12,128),(13,225),(18,1),(22,128),(28,0),(38,145),(39,128),(42,97),(47,1)]:
            raw=bytearray(MIDI);raw[offset]=value
            with self.assertRaises(ImportError):midi_operand_edits(bytes(raw),NATIVE)
        for raw in [smf(ANCHORS+b'\0\xf0\0\0\xff\x2f\0'),smf(ANCHORS+b'\0\xff\x01\0\0\xff\x2f\0'),smf(ANCHORS+b'\0\xff\x2f\0\0'),bytes(MAX_MIDI_BYTES+1)]:
            with self.assertRaises(ImportError):decode_midi(raw)
        with self.assertRaises(ImportError):midi_operand_edits(MIDI,NATIVE[:19]+b'\0\xff\x7f')
        for n in (256,257):
            native=seq()[:15]+bytes([0,192,1])*n+b'\0\xff\x2f';report=inspect_sequence(native)
            for e in report['events'][:-1]:e['values']=[2]
            if n==256:self.assertEqual(len(midi_operand_edits(export_fixture(report),native)),256)
            else:
                with self.assertRaises(ImportError):midi_operand_edits(export_fixture(report),native)


if __name__=='__main__':unittest.main()
