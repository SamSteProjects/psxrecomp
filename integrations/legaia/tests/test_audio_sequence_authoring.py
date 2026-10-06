"""Independent byte preservation/readback checks; no runtime or SDK writes."""
import os
import unittest
from hashlib import sha256
from importer.core import ImportError
from importer.audio_sequence import inspect_sequence
from importer.audio_catalog import decode_audio_entry, load_audio_asset_catalog
from importer.audio_sequence_authoring import replace_sequence_operands, replace_audio_entry_sequence
from importer.pipeline import _disc_context
from test_audio_catalog import seq, bank, chunk


def digest(body):
    return sha256(body).hexdigest()


def raw(events):
    return seq()[:15] + bytes(events)


def replace(original, edits, current=None):
    current = original if current is None else current
    return replace_sequence_operands(original, current, expected_source_sha256=digest(original),
                                     expected_current_sha256=digest(current), edits=edits)


class SequenceAuthoring(unittest.TestCase):
    def test_channel_shapes_running_status_and_composed_current(self):
        body = raw([0,0x90,60,100,0x81,0,61,99,0,0xc1,7,0,0xd2,8,
                    0,0x80,1,2,0,0xa3,3,4,0,0xb4,5,6,0,0xe5,9,10,0,0xff,0x2f]) + b'opaque'
        source = inspect_sequence(body)
        events = source['events'][:-1]
        edits = [dict(event_offset=e['offset'], values=[(v+1)%128 for v in e['values']]) for e in events]
        output, audit = replace(body, edits)
        expected = bytearray(body)
        for e in events:
            for i,v in enumerate(e['values']):
                expected[e['end_offset']-len(e['values'])+i]=(v+1)%128
        self.assertEqual(output, bytes(expected))
        self.assertEqual(len(audit['edits']),8)
        self.assertTrue(inspect_sequence(output)['events'][1]['running_status'])
        restored, _ = replace(body, [dict(event_offset=e['offset'],values=e['values']) for e in events], output)
        self.assertEqual(restored,body)
        noop,_=replace(body,edits,output)
        self.assertEqual(noop,output)

    def test_tempo_recomputes_time_and_preserves_vlq_and_header(self):
        body=raw([0,0xff,0x51,0x07,0xa1,0x20,0x83,0x60,0x90,60,100,0,0xff,0x2f])
        output,audit=replace(body,[dict(event_offset=15,values=[1000000])])
        expected=bytearray(body);expected[18:21]=(1000000).to_bytes(3,'big')
        self.assertEqual(output,bytes(expected))
        self.assertEqual(inspect_sequence(output)['events'][1]['time_seconds'],1)
        self.assertEqual(audit['decoded_time_seconds'],1)
        for value in (0,0x1000000,True,-1):
            with self.assertRaises(ImportError):replace(body,[dict(event_offset=15,values=[value])])

    def test_partial_reached_operand_preserves_entire_unknown_tail(self):
        body=raw([0,0xc0,2,0,0xff,0x7f,0,0x90,60,100])
        output,audit=replace(body,[dict(event_offset=15,values=[127])])
        self.assertEqual(output,body[:17]+bytes([127])+body[18:])
        self.assertFalse(audit['complete'])
        self.assertEqual(inspect_sequence(output)['stop_offset'],18)
        for offset in (18,21,16,0):
            with self.assertRaises(ImportError):replace(body,[dict(event_offset=offset,values=[1])])

    def test_source_current_hash_structure_and_edit_bounds_fail_closed(self):
        body=raw([0,0x90,60,100,0,0xff,0x2f])+b'padding'
        edit=dict(event_offset=15,values=[1,2])
        for edits in ([],[edit]*2,[dict(event_offset=True,values=[1,2])],
                      [dict(event_offset=15,values=[True,2])],
                      [dict(event_offset=15,values=[128,2])],
                      [dict(event_offset=15,values=[1])],[dict(**edit,other=3)], [edit]*257):
            with self.assertRaises(ImportError):replace(body,edits)
        for position,value in ((15,1),(16,0x91),(4,2),(22,1)):
            changed=bytearray(body);changed[position]=value
            with self.assertRaises(ImportError):replace(body,[edit],bytes(changed))
        for source_hash,current_hash in (('f'*64,digest(body)),(digest(body),'f'*64)):
            with self.assertRaises(ImportError):replace_sequence_operands(body,body,
                expected_source_sha256=source_hash,expected_current_sha256=current_hash,edits=[edit])
        self.assertEqual(body,raw([0,0x90,60,100,0,0xff,0x2f])+b'padding')

    def test_native_carrier_preserves_bank_samples_padding_and_declarations(self):
        sequence=raw([0,0xc0,2,0,0xff,0x2f])
        body=chunk(0,bank())+chunk(1,bytes(range(32)))+chunk(2,sequence)+b'physical pad'
        output,audit=replace_audio_entry_sequence(body,body,expected_source_sha256=digest(body),
            expected_current_sha256=digest(body),edits=[dict(event_offset=15,values=[3])])
        position=decode_audio_entry(body)['chunks'][2]['payload_offset']+17
        self.assertEqual(output,body[:position]+bytes([3])+body[position+1:])
        self.assertEqual(audit['changed_entry_byte_offsets'],[position])
        changed=bytearray(body);changed[40]=255
        with self.assertRaises(ImportError):replace_audio_entry_sequence(body,bytes(changed),
            expected_source_sha256=digest(body),expected_current_sha256=digest(changed),
            edits=[dict(event_offset=15,values=[3])])
        standalone,_=replace_audio_entry_sequence(sequence,sequence,
            expected_source_sha256=digest(sequence),expected_current_sha256=digest(sequence),
            edits=[dict(event_offset=15,values=[3])])
        self.assertEqual(standalone,sequence[:17]+bytes([3])+sequence[18:])

    @unittest.skipUnless(os.getenv('LEGAIA_DISC_BIN'),'Retail disc not configured')
    def test_all_retail_sequence_carriers_exact_operand_roundtrip(self):
        disc=os.environ['LEGAIA_DISC_BIN']
        catalog=load_audio_asset_catalog(disc,'town01')
        count=partial=0
        with _disc_context(disc) as (image,_,_,archive):
            for row in catalog['assets']:
                if row.get('sequence') is None:continue
                index=row['source_record']['prot_entry_index']
                start,end=archive.toc[index+2:index+4]
                body=image.read_user(archive.node.extent_lba,start*2048,(end-start)*2048,archive.node.size)
                decoded=decode_audio_entry(body)
                offset=0 if decoded['format']=='SEQ' else decoded['chunks'][2]['payload_offset']
                size=len(body) if offset==0 else decoded['chunks'][2]['size_bytes']
                report=inspect_sequence(body[offset:offset+size])
                event=next(e for e in report['events'] if e['channel'] is not None)
                values=[(v+1)%128 for v in event['values']]
                output,audit=replace_audio_entry_sequence(body,body,
                    expected_source_sha256=digest(body),expected_current_sha256=digest(body),
                    edits=[dict(event_offset=event['offset'],values=values)])
                expected=bytearray(body)
                first=offset+event['end_offset']-len(values)
                expected[first:first+len(values)]=bytes(values)
                self.assertEqual(output,bytes(expected),row['semantic_id'])
                restored,_=replace_audio_entry_sequence(body,output,
                    expected_source_sha256=digest(body),expected_current_sha256=digest(output),
                    edits=[dict(event_offset=event['offset'],values=event['values'])])
                self.assertEqual(restored,body,row['semantic_id'])
                self.assertEqual(audit['sequence']['complete'],report['complete'])
                count+=1;partial+=not report['complete']
        self.assertEqual((count,partial),(83,1))


if __name__=='__main__':unittest.main()
