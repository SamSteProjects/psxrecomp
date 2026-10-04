from copy import deepcopy
from hashlib import sha256
import random
import struct
import unittest

from importer.core import ImportError, _pack_ranges, parse_scene_assets, decompress_lzs
from importer.model_face_ledger import create_face_ledger, append_face_ledger
from importer.model_pack_growth import grow_model_pack, grow_scene_model_pack, MAX_PACK_BYTES
from importer.serialization import compress_lzs
from test_model_primitives import synthetic


def pack_source():
    models = [synthetic(((flags,),), count=2) for flags in (0x20, 0x22, 0x24)]
    source = bytearray(16)
    struct.pack_into('<I', source, 0, 3)
    for slot, model in enumerate(models):
        struct.pack_into('<I', source, 4+slot*4, len(source)//4)
        source.extend(model);source.extend(b'PAD!')
    return bytes(source), models


def ledger_for(model, count=1, varied=False):
    corners = 4 if struct.unpack_from('<H', model, 42)[0] & 2 else 3
    donor = f'face://source/{sha256(model).hexdigest()}/0/0'
    rng = random.Random(9103)
    requests = []
    for index in range(count):
        fields = dict(vertices=list(reversed(range(corners))))
        if varied:
            fields.update(colors=[[rng.randrange(256) for _ in range(3)] for _ in range(corners)],
                          uvs=[[rng.randrange(256) for _ in range(2)] for _ in range(corners)])
        requests.append(dict(face_id=f'face://authored/00000000-0000-4000-8000-{index+1:012x}',
                             donor_face_id=donor, fields=fields))
    candidate, ledger, _ = append_face_ledger(model, create_face_ledger(model), requests)
    return candidate, ledger


def container_for(pack, capacity_extra=0):
    stream = compress_lzs(pack)
    payloads = [b'LEAD', stream+bytes(capacity_extra), b'NEIGHBOR', b'TAIL']
    source = bytearray(40)
    struct.pack_into('<II', source, 0, 4, 0xAABBCCDD)
    for index, payload in enumerate(payloads):
        struct.pack_into('<II', source, 8+index*8,
                         ((2 if index == 1 else 1)<<24)|(len(pack) if index == 1 else len(payload)), len(source))
        source.extend(payload)
    return bytes(source)


class ModelPackGrowthTests(unittest.TestCase):
    def test_multiple_slot_growth_preserves_every_neighbor_and_tail(self):
        source, models = pack_source()
        first, ledger0 = ledger_for(models[0]);second, ledger1 = ledger_for(models[1])
        records = [dict(slot_index=1, ledger=ledger1), dict(slot_index=0, ledger=ledger0)]
        snapshot = deepcopy(records)
        candidate, audit = grow_model_pack(source, sha256(source).hexdigest(), records)
        expected = bytearray(16);struct.pack_into('<I', expected, 0, 3)
        for slot, payload in enumerate((first, second, models[2])):
            struct.pack_into('<I', expected, 4+slot*4, len(expected)//4)
            expected.extend(payload+b'PAD!')
        self.assertEqual(candidate, bytes(expected))
        self.assertEqual(records, snapshot)
        self.assertEqual(audit['growth_bytes'], len(candidate)-len(source))
        old, new = _pack_ranges(source), _pack_ranges(candidate)
        self.assertEqual(source[slice(*old[2])], candidate[slice(*new[2])])
        self.assertEqual(audit['members'][2]['source_sha256'], audit['members'][2]['proposed_sha256'])
        self.assertTrue(all(row['trailing_bytes_preserved'] for row in audit['members']))
        self.assertFalse(audit['build_ready'])

    def test_noop_keeps_entire_pack_and_original_compressed_bytes(self):
        source, models = pack_source()
        records = [dict(slot_index=0, ledger=create_face_ledger(models[0]))]
        candidate, audit = grow_model_pack(source, sha256(source).hexdigest(), records)
        self.assertEqual(candidate, source);self.assertEqual(audit['growth_bytes'], 0)
        carrier = container_for(source, 37)
        unchanged, carrier_audit = grow_scene_model_pack(carrier, sha256(carrier).hexdigest(), 1, sha256(source).hexdigest(), records)
        self.assertEqual(unchanged, carrier)
        self.assertEqual(carrier_audit['growth_bytes'], 0)

    def test_compressed_capacity_and_relocation_preserve_descriptors_and_payloads(self):
        pack, models = pack_source();_, ledger = ledger_for(models[2], 32, varied=True)
        records = [dict(slot_index=2, ledger=ledger)];carrier = container_for(pack)
        args = (carrier, sha256(carrier).hexdigest(), 1, sha256(pack).hexdigest(), records)
        with self.assertRaises(ImportError): grow_scene_model_pack(*args)
        candidate, audit = grow_scene_model_pack(*args, allow_growth=True)
        self.assertGreater(audit['growth_bytes'], 0);self.assertEqual(audit['growth_bytes'] % 4, 0)
        before, after = (parse_scene_assets(body, 0) for body in (carrier, candidate))
        self.assertEqual(candidate[:8], carrier[:8])
        for index in (0, 2, 3):
            a, b = before.descriptors[index], after.descriptors[index]
            end = before.descriptors[index+1].data_offset if index+1 < 4 else len(carrier)
            self.assertEqual(candidate[b.data_offset:b.data_offset+end-a.data_offset], carrier[a.data_offset:end])
            self.assertEqual((a.type_byte, a.size), (b.type_byte, b.size))
        decoded, _ = decompress_lzs(candidate[after.descriptors[1].data_offset:], after.descriptors[1].size)
        self.assertEqual(decoded, grow_model_pack(pack, sha256(pack).hexdigest(), records)[0])
        self.assertEqual(len(candidate)-len(carrier), audit['growth_bytes'])
        self.assertFalse(audit['build_ready'])
        room = container_for(pack, audit['compressed_size']+16)
        same_length, roomy = grow_scene_model_pack(room, sha256(room).hexdigest(), 1, sha256(pack).hexdigest(), records)
        self.assertEqual(len(same_length), len(room));self.assertEqual(roomy['moved_descriptors'], [])

    def test_pack_slot_source_schema_and_directory_reject(self):
        source, models = pack_source();_, ledger = ledger_for(models[0]);valid = dict(slot_index=0, ledger=ledger)
        rows = [[], [valid, valid], [dict(valid, slot_index=True)], [dict(valid, slot_index=3)],
                [dict(valid, extra=True)], [dict(slot_index=1, ledger=ledger)]]
        for replacements in rows:
            with self.assertRaises(ImportError): grow_model_pack(source, sha256(source).hexdigest(), replacements)
        with self.assertRaises(ImportError): grow_model_pack(source, 'stale', [valid])
        mutations = [(4, 0), (8, 4), (12, len(source)//4+1), (0, 241)]
        for at, value in mutations:
            bad = bytearray(source);struct.pack_into('<I', bad, at, value);bad = bytes(bad)
            with self.assertRaises(ImportError): grow_model_pack(bad, sha256(bad).hexdigest(), [valid])
        with self.assertRaises(ImportError): grow_model_pack(source+bytes(MAX_PACK_BYTES), '', [valid])

    def test_last_physical_resource_grows_without_moving_earlier_resources(self):
        pack, models = pack_source();_, ledger = ledger_for(models[2], 32, varied=True)
        source = bytearray(40);struct.pack_into('<I', source, 0, 4)
        for index, payload in enumerate((b'HEAD', b'MIDDLE', b'TAIL', compress_lzs(pack))):
            size = len(pack) if index == 3 else len(payload)
            struct.pack_into('<II', source, 8+index*8, ((2 if index == 3 else 1)<<24)|size, len(source))
            source.extend(payload)
        source = bytes(source);records = [dict(slot_index=2, ledger=ledger)]
        result, audit = grow_scene_model_pack(source, sha256(source).hexdigest(), 3,
                                             sha256(pack).hexdigest(), records, allow_growth=True)
        self.assertGreater(audit['growth_bytes'], 0)
        self.assertEqual(audit['moved_descriptors'], [])
        self.assertEqual(result[:32], source[:32])
        table = parse_scene_assets(result, 0);start = table.descriptors[3].data_offset
        self.assertEqual(result[40:start], source[40:start])
        decoded, _ = decompress_lzs(result[start:], table.descriptors[3].size)
        self.assertEqual(decoded, grow_model_pack(pack, sha256(pack).hexdigest(), records)[0])

    def test_carrier_source_type_alias_bounds_and_policy_reject(self):
        pack, models = pack_source();_, ledger = ledger_for(models[0]);records = [dict(slot_index=0, ledger=ledger)]
        source = container_for(pack)
        for index in (True, -1, 0, 4):
            with self.assertRaises(ImportError): grow_scene_model_pack(source, sha256(source).hexdigest(), index, sha256(pack).hexdigest(), records)
        with self.assertRaises(ImportError): grow_scene_model_pack(source, 'stale', 1, sha256(pack).hexdigest(), records)
        with self.assertRaises(ImportError): grow_scene_model_pack(source, sha256(source).hexdigest(), 1, 'stale', records)
        with self.assertRaises(ImportError): grow_scene_model_pack(source, sha256(source).hexdigest(), 1, sha256(pack).hexdigest(), records, allow_growth=1)
        for at, value in ((20, 39), (28, 44), (28, len(source)), (28, len(source)+1)):
            bad = bytearray(source);struct.pack_into('<I', bad, at, value);bad = bytes(bad)
            with self.assertRaises(ImportError): grow_scene_model_pack(bad, sha256(bad).hexdigest(), 1, sha256(pack).hexdigest(), records, allow_growth=True)


if __name__ == '__main__':
    unittest.main()
