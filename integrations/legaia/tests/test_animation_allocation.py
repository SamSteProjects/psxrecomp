"""Native allocation proofs independent of project history/carrier delivery."""
from copy import deepcopy
from hashlib import sha256
import os
import struct
import unittest
from uuid import uuid4

from importer.animation import animation_record_ranges, decode_animation_record
from importer.animation_allocation import allocate_animation_record, append_animation_records, append_animation_record_payloads
from importer.core import ImportError, decompress_lzs
from importer.serialization import compress_lzs
from test_animation_glb import record


def bank(records, padding=b''):
    at = 4 + 4*len(records) + len(padding)
    offsets = []
    for item in records:
        offsets.append(at); at += len(item)
    return struct.pack('<I', len(records)) + struct.pack(f'<{len(records)}I', *offsets) + padding + b''.join(records)


def request(index=0, frames=None, edits=None):
    return dict(record_id=str(uuid4()), donor_record_index=index,
                source_frame_indices=frames if frames is not None else [0],
                edits=edits if edits is not None else [])


class AnimationAllocationTests(unittest.TestCase):
    def test_prepared_payloads_and_empty_identity_composition(self):
        donor = record([[([1,2,3],[4,5,6])]])
        original = bank([donor,b'opaque-neighbor'],b'KEEP')
        unchanged,audit = append_animation_record_payloads(original,sha256(original).hexdigest(),[])
        self.assertEqual(unchanged,original)
        self.assertEqual(audit['table_growth_bytes'],0)
        self.assertEqual(audit['allocated_records'],[])
        identity = str(uuid4())
        changed,audit = append_animation_record_payloads(original,sha256(original).hexdigest(),
            [dict(record_id=identity,record=donor)])
        a,b = animation_record_ranges(changed)[-1]
        self.assertEqual(changed[a:b],donor)
        self.assertEqual(audit['allocated_records'][0]['record_id'],identity)
        for rows in ([dict(record_id=identity,record=bytearray(donor))],
                     [dict(record_id=identity,record=b'bad')],
                     [dict(record_id=identity,record=donor)]*2):
            with self.assertRaises(ImportError): append_animation_record_payloads(original,sha256(original).hexdigest(),rows)

    def test_frame_sequence_and_edits_keep_source_modes_and_opaque_channels(self):
        donor = record([[([i,-i,7], [i,2,255]), ([-2048,2047,0], [8,9,10])]
                        for i in range(3)])
        for mode in (0, 1):
            for flags in (2, 4):
                source = bytearray(donor)
                struct.pack_into('<H', source, 0, mode*256+2)
                struct.pack_into('<H', source, 6, flags)
                source = bytes(source)
                changed, audit = allocate_animation_record(source, sha256(source).hexdigest(), [2,0,2,1],
                    [dict(frame_index=1, object_index=1, translation={'z':-100}, rotation_psx={'x':4080})])
                self.assertEqual(changed[:2], source[:2])
                self.assertEqual(changed[4:8], source[4:8])
                self.assertEqual(changed[-8:], source[-8:])
                self.assertEqual(struct.unpack_from('<H', changed, 2)[0], 4)
                self.assertEqual(changed[8:24], source[40:56])
                self.assertEqual(changed[40:56], source[40:56])
                self.assertEqual(changed[56:72], source[24:40])
                # Frame 1 / object 1 = source frame 0 / object 1, exact signed12 packing.
                self.assertEqual(changed[32:40], bytes([0,255,0x78,156,0x1f,255,9,10]))
                values = decode_animation_record(changed)
                self.assertEqual(values['frames'][1]['object_transforms'][1]['translation'], [-2048,2047,-100])
                self.assertEqual(audit['source_frame_indices'], [2,0,2,1])
                self.assertEqual(len(audit['changed_axes']), 2)
                audit['source_frame_indices'].clear()
                self.assertEqual(allocate_animation_record(source, sha256(source).hexdigest(), [0], [])[1]['source_frame_indices'], [0])

    def test_multiple_append_rebases_absolute_offsets_and_keeps_opaque_neighbors_padding(self):
        donor = record([[([i,0,0], [0,i,0])] for i in range(3)])
        # Non-donor records deliberately are not decodable; preservation must not guess them.
        neighbors = [donor, b'opaque-neighbor', b'last opaque trailer']
        original = bank(neighbors, b'KEEP\x01\x02\x03\x04')
        requests = [request(0, [2,0,1,2]), request(0, [1])]
        before = deepcopy(requests)
        changed, audit = append_animation_records(original, sha256(original).hexdigest(), requests)
        self.assertEqual(requests, before)
        self.assertEqual(struct.unpack_from('<I', changed)[0], 5)
        old = animation_record_ranges(original); new = animation_record_ranges(changed)
        self.assertEqual(changed[24:new[0][0]], b'KEEP\x01\x02\x03\x04')
        for index, ((a,b), (c,d)) in enumerate(zip(old,new)):
            self.assertEqual(c, a+8)
            self.assertEqual(d, b+8)
            self.assertEqual(changed[c:d], neighbors[index])
        for ordinal, frames in enumerate(([2,0,1,2], [1])):
            a,b = new[3+ordinal]
            decoded = decode_animation_record(changed[a:b])
            self.assertEqual([f['object_transforms'][0]['translation'][0] for f in decoded['frames']], frames)
            self.assertEqual(audit['allocated_records'][ordinal]['record_id'], requests[ordinal]['record_id'])
            self.assertEqual(audit['allocated_records'][ordinal]['byte_offset'], a)
        self.assertEqual(audit['candidate_bank_sha256'], sha256(changed).hexdigest())
        self.assertEqual(audit['allocated_channel_count'], 5)

    def test_whole_donor_clone_is_byte_exact_and_can_be_a_later_explicit_donor(self):
        source = bank([record([[([0,0,0], [0,0,0])], [([1,2,3], [4,5,6])]])])
        first, _ = append_animation_records(source, sha256(source).hexdigest(), [request(0,[0,1])])
        a,b = animation_record_ranges(first)[1]
        c,d = animation_record_ranges(source)[0]
        self.assertEqual(first[a:b], source[c:d])
        second, audit = append_animation_records(first, sha256(first).hexdigest(), [request(1,[1,0])])
        self.assertEqual(audit['allocated_records'][0]['donor_record_index'], 1)
        self.assertEqual(audit['source_record_count'], 2)
        self.assertEqual(len(animation_record_ranges(second)), 3)

    def test_invalid_identity_schema_donor_and_stale_source_reject(self):
        original = bank([record([[([0,0,0], [0,0,0])]])])
        for mutate in (lambda r:r.update(record_id='bad'),
                       lambda r:r.update(record_id='00000000-0000-1000-8000-000000000000'),
                       lambda r:r.update(record_id=r['record_id'].upper()),
                       lambda r:r.update(donor_record_index=True),
                       lambda r:r.update(donor_record_index=1),
                       lambda r:r.update(extra=1)):
            r = request(); mutate(r)
            with self.assertRaises(ImportError): append_animation_records(original, sha256(original).hexdigest(), [r])
        r = request()
        for content, expected, rows in ((original,'0'*64,[r]), (bytearray(original),sha256(original).hexdigest(),[r]),
                                       (original,sha256(original).hexdigest(),[]),
                                       (original,sha256(original).hexdigest(),[r,r])):
            with self.assertRaises(ImportError): append_animation_records(content, expected, rows)

    def test_frame_count_exact_indices_axis_validation_and_unsupported_donor_reject(self):
        donor = record([[([0,0,0], [0,0,0])]])
        for frames in ([], [True], [-1], [1], [0]*513, '0'):
            with self.assertRaises(ImportError): allocate_animation_record(donor,sha256(donor).hexdigest(),frames,[])
        for edits in ([dict(frame_index=1,object_index=0,translation={'x':1})],
                      [dict(frame_index=0,object_index=0,translation={'x':2048})],
                      [dict(frame_index=0,object_index=0,rotation_psx={'x':1})]):
            with self.assertRaises(ImportError): allocate_animation_record(donor,sha256(donor).hexdigest(),[0],edits)
        unsupported = bank([b'not a native record'])
        with self.assertRaises(ImportError): append_animation_records(unsupported,sha256(unsupported).hexdigest(),[request()])

    def test_cumulative_channel_record_and_byte_budgets_reject(self):
        donor = record([[([0,0,0], [0,0,0])]*64])
        original = bank([donor])
        # Each individual record fits (64*64=4096); together they exceed the batch budget.
        with self.assertRaisesRegex(ImportError,'cumulative channel'):
            append_animation_records(original,sha256(original).hexdigest(),[request(frames=[0]*64),request()])
        with self.assertRaisesRegex(ImportError,'count exceeds'):
            append_animation_records(original,sha256(original).hexdigest(),[request() for _ in range(65)])
        packed = bank([donor]+[b'X']*4095)
        with self.assertRaisesRegex(ImportError,'count exceeds'):
            append_animation_records(packed,sha256(packed).hexdigest(),[request()])
        packed = bank([donor,bytes(4*1024*1024-12-len(donor))])
        with self.assertRaisesRegex(ImportError,'byte budget'):
            append_animation_records(packed,sha256(packed).hexdigest(),[request()])

    @unittest.skipUnless(os.environ.get('LEGAIA_DISC_BIN'), 'requires private retail disc')
    def test_retail_bank_allocates_new_frame_sequence_and_preserves_all_existing_records(self):
        from importer.scene_animation import load_scene_actor_animation_catalog
        from importer.pipeline import _disc_context
        with _disc_context(os.environ['LEGAIA_DISC_BIN']):
            catalog = load_scene_actor_animation_catalog(os.environ['LEGAIA_DISC_BIN'], 'town01')
            source, _ = catalog.source_bank()
        ranges = animation_record_ranges(source)
        # Use a structurally valid donor with multiple source frames, not a guessed actor association.
        index = next(i for i,(a,b) in enumerate(ranges)
                     if decode_animation_record(source[a:b])['frame_count'] > 1)
        changed, audit = append_animation_records(source,sha256(source).hexdigest(),
            [request(index,[1,0,1], [dict(frame_index=2,object_index=0,translation={'x':123})])])
        self.assertEqual(audit['source_record_count'], 69)
        self.assertEqual(audit['record_count'], 70)
        self.assertEqual(len(audit['preserved_records']), 69)
        new_ranges = animation_record_ranges(changed)
        for (a,b),(c,d) in zip(ranges,new_ranges): self.assertEqual(source[a:b],changed[c:d])
        a,b = new_ranges[-1]
        decoded = decode_animation_record(changed[a:b])
        self.assertEqual(decoded['frame_count'], 3)
        self.assertEqual(decoded['frames'][2]['object_transforms'][0]['translation'][0], 123)
        encoded = compress_lzs(changed)
        self.assertEqual(decompress_lzs(encoded,len(changed)), (changed,len(encoded)))


if __name__ == '__main__':
    unittest.main()
