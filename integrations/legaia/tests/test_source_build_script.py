import unittest
from hashlib import sha256
from sdk.project import ProjectError
from sdk.source_build_script import record_at, describe
from test_branch_authoring import p2_fixture
from importer.man_layout import read_man_layout
from types import SimpleNamespace
from sdk.source_build_script import inspect


class SourceBuildScriptTests(unittest.TestCase):
    def test_controller_owner_is_exact_and_active(self):
        project=SimpleNamespace(active_scene='scene://fixture')
        for owner in ['scene://fixture/controllers/man-p1/0001','scene://foreign/controllers/man-p1/0000','scene://fixture/controllers/man-p1/0000/extra','script://fixture/controllers/man-p1/0000']:
            with self.assertRaisesRegex(ProjectError,'active scene'):
                inspect(project,owner,'a'*16)

    def test_partition_identity_and_exact_raw_record(self):
        _, man = p2_fixture(b'\x21\x26\xfe\xff')
        for partition, index, entry in ((1, 1, 5), (2, 0, 4)):
            offset, record, actual_entry = record_at(man, partition, index)
            self.assertEqual(actual_entry, entry)
            report = describe(offset, record, entry, 'scene://fixture/scripts/man-p2/0000')
            self.assertEqual(bytes.fromhex(report['raw_hex']), record)
            self.assertEqual(report['sha256'], sha256(record).hexdigest())
            self.assertEqual(report['inspection']['semantic_id'], 'script://fixture/scripts/man-p2/0000')
        with self.assertRaises(ProjectError):
            record_at(man, 2, 1)

    def test_alias_and_section_overlap_rejected(self):
        _, man = p2_fixture(b'\x21')
        layout = read_man_layout(man)
        actor = next(r for r in layout['records'] if r['partition'] == 1 and r['record_index'] == 1)
        script = next(r for r in layout['records'] if r['partition'] == 2)
        broken = bytearray(man)
        broken[script['table_offset']:script['table_offset']+3] = actor['relative_offset'].to_bytes(3, 'little')
        with self.assertRaises(ProjectError):
            record_at(bytes(broken), 2, 0)
        broken[script['table_offset']:script['table_offset']+3] = (layout['sections'][0]['byte_offset']-layout['data_region_offset']).to_bytes(3, 'little')
        with self.assertRaises(ProjectError):
            record_at(bytes(broken), 2, 0)


if __name__ == '__main__':
    unittest.main()
