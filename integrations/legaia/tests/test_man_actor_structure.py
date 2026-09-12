"""Small synthetic MAN exercises actual table growth and record identity."""
from hashlib import sha256
from pathlib import Path
import struct
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from importer.core import ImportError, parse_man
from importer.man_actor_structure import append_actor_donor, append_actor_candidates
from importer.man_layout import read_man_layout, resolve_spawn_record
from importer.script_reindex import spawn_index_map


def fixture():
    records = [b'opaque', b'\0\0\0\0\0\x2a',
               b'\0\x01\x02\x03\x04\x2a', b'\0\0\0\0\x2a']
    header = bytearray(0x2b)
    struct.pack_into('<hhh', header, 0x22, 1, 2, 1)
    header[0x28:0x2b] = sum(map(len, records)).to_bytes(3, 'little')
    offsets, cursor = [], 0
    for record in records:
        offsets.append(cursor.to_bytes(3, 'little'))
        cursor += len(record)
    return bytes(header)+b''.join(offsets)+b''.join(records)+b'\0'*18+b'tail'


class ManActorStructureTests(unittest.TestCase):
    def test_batch_identity_order_and_original_donor_scope(self):
        source=fixture()
        source_hash=sha256(source).hexdigest()
        drafts=[dict(id='b',donor_record_index=1,position=dict(x=704,z=768)),
                dict(id='a',donor_record_index=1,position=dict(x=832,z=896))]
        result,audit=append_actor_candidates(source,source_hash,drafts)
        reverse,other=append_actor_candidates(source,source_hash,list(reversed(drafts)))
        self.assertEqual(result,reverse)
        self.assertEqual(audit,other)
        self.assertEqual([(d['draft_id'],d['record_index']) for d in audit['drafts']], [('a',2),('b',3)])
        actors={a.record_index:a for a in parse_man(result).actors}
        self.assertEqual((actors[2].world_x,actors[2].world_z),(832,896))
        self.assertEqual((actors[3].world_x,actors[3].world_z),(704,768))
        self.assertFalse(audit['build_ready'])
        with self.assertRaisesRegex(ImportError,'unique'):
            append_actor_candidates(source,source_hash,[drafts[0],drafts[0]])
        with self.assertRaisesRegex(ImportError,'original MAN'):
            append_actor_candidates(source,source_hash,[drafts[0],dict(drafts[1],donor_record_index=2)])

    def test_append_preserves_records_sections_coordinates_and_target_identity(self):
        source = fixture()
        result, audit = append_actor_donor(source, sha256(source).hexdigest(), 1)
        old, new = read_man_layout(source), read_man_layout(result)
        self.assertEqual(new['partition_counts'], [1, 3, 1])
        self.assertEqual(len(parse_man(result).actors), 2)
        self.assertEqual(audit['donor']['world_x'], parse_man(source).actors[0].world_x)
        self.assertEqual(source[old['sections'][0]['byte_offset']:],
                         result[new['sections'][0]['byte_offset']:])
        for before in old['records']:
            after = next(r for r in new['records'] if
                         (r['partition'], r['record_index']) ==
                         (before['partition'], before['record_index']))
            self.assertEqual(source[before['byte_offset']:before['byte_offset']+before['byte_length']],
                             result[after['byte_offset']:after['byte_offset']+after['byte_length']])
        self.assertEqual(spawn_index_map(source, result), {3: 4})
        self.assertEqual(resolve_spawn_record(new, 3)['status'], 'outside_partition2')
        self.assertFalse(audit['script_relocation_verified'])

    def test_bad_source_alias_and_changed_target_rejected(self):
        source = fixture()
        with self.assertRaises(ImportError):
            append_actor_donor(source, '0'*64, 1)
        alias = bytearray(source)
        alias[0x2b:0x2e] = alias[0x31:0x34]
        with self.assertRaises(ImportError):
            append_actor_donor(bytes(alias), sha256(alias).hexdigest(), 1)
        result, _ = append_actor_donor(source, sha256(source).hexdigest(), 1)
        changed = bytearray(result)
        target = resolve_spawn_record(read_man_layout(result), 4)
        changed[target['byte_offset']] ^= 1
        with self.assertRaises(ImportError):
            spawn_index_map(source, bytes(changed))


if __name__ == '__main__':
    unittest.main()
