"""Flag assets adapt decoder evidence without inventing runtime bindings."""
from copy import deepcopy
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from importer.core import validate_metadata_only
from importer.script_catalog import _catalog
from sdk.flag_assets import build_flag_assets, validate_flag_asset
from sdk.project import ProjectError
from integrations.legaia.tests.test_importer_dialogue_authoring import fixture
from integrations.legaia.tests.test_importer_script_catalog import catalog, forbidden_fields


def partition_two_catalog():
    _, original = fixture(b'\x2b\x02')
    region = 0x2B + 12
    section = int.from_bytes(original[0x28:0x2B], 'little')
    record = bytes(4) + b'\x2b\x02\xab\x07\x02'
    man = bytearray(original[:region + section] + record + original[region + section:])
    man[0x34:0x37] = section.to_bytes(3, 'little')
    man[0x28:0x2B] = (section + len(record)).to_bytes(3, 'little')
    return _catalog(bytes(man), 'fixture', {'synthetic': True}, set())


class FlagAssetTests(unittest.TestCase):
    def test_partition_owners_and_extended_contexts_keep_distinct_source_groups(self):
        source = partition_two_catalog()
        before = deepcopy(source)
        records = build_flag_assets(source)
        self.assertEqual(len(records), 3)
        self.assertEqual(len({row['id'] for row in records}), 3)
        self.assertEqual({row['partition'] for row in records}, {1, 2})
        self.assertEqual({row['extended_target'] for row in records}, {None, 7})
        for row in records:
            self.assertEqual(row['id'], row['semantic_id'])
            self.assertEqual(row['owner_id'], row['script_id'].replace('script://', 'scene://', 1))
            script = next(item for item in source['assets'] if item['semantic_id'] == row['script_id'])
            self.assertEqual(row['source_record'], script['source_record'])
            self.assertIsNone(row['runtime_value'])
            self.assertEqual(row['runtime_binding'], 'unresolved')
            self.assertIs(validate_flag_asset(row), row)
            registered = dict(row, kind='flag', layer='derived', scene_id='scene://fixture')
            validate_flag_asset(registered)
        self.assertEqual(source, before)
        reversed_source = deepcopy(source)
        reversed_source['assets'].reverse()
        for script in reversed_source['assets']:
            script.get('flag_references', []).reverse()
        self.assertEqual(records, build_flag_assets(reversed_source))
        records[0]['source_record']['sha256'] = '0' * 64
        records[0]['references'][0]['index'] = 12
        records[0]['limitations'].clear()
        self.assertEqual(source, before)

    def test_all_observed_banks_and_system_extended_selector_are_metadata_only(self):
        source = catalog(b'\x2b\x02\xab\x07\x12\x2e\x03\xb1\x08\x05'
                         b'\x51\x23\xd0\x09\x44\x42\x00\x23\x02\x00')
        records = build_flag_assets(source)
        self.assertEqual({row['bank'] for row in records}, {'local', 'global', 'context', 'system', 'extra'})
        system = next(row for row in records if row['bank'] == 'system' and row['extended_target'] == 9)
        self.assertEqual(system['index'], 0x8044)
        self.assertEqual(system['references'][0]['index_semantics'], 'encoded_selector_not_resolved_runtime_bit')
        unresolved = next(row for row in records if row['bank'] == 'local' and row['index'] == 18)
        self.assertEqual(unresolved['references'][0]['status'], 'bank_width_unresolved')
        self.assertEqual(forbidden_fields(records), set())
        validate_metadata_only(records)
        json.dumps(records)

    def test_authored_layer_changes_reference_without_changing_retail_identity(self):
        source = catalog(b'\x2e\xe2\x2e\x02')
        key = 'script://fixture/actors/man-p1/0001/flag-bit/0005'
        authored = {key: {'bit': 3}}
        before_source, before_authored = deepcopy(source), deepcopy(authored)
        records = build_flag_assets(source, authored)
        self.assertEqual(len(records), 1)
        row = records[0]
        self.assertTrue(row['id'].endswith('/current/global/2'))
        self.assertEqual((row['reference_count'], row['authored_reference_count']), (2, 1))
        ref = row['references'][0]
        self.assertEqual((ref['retail_index'], ref['authored_index'], ref['effective_index']), (2, 3, 3))
        self.assertEqual((source, authored), (before_source, before_authored))
        with self.assertRaises(ProjectError):
            build_flag_assets(source, {key[:-4] + 'ffff': {'bit': 3}})
        unsupported = catalog(b'\x2b\x12')
        with self.assertRaisesRegex(ProjectError, 'unsupported authored'):
            build_flag_assets(unsupported, {key: {'bit': 3}})

    def test_opaque_paths_and_old_minimal_catalogs_supply_no_assets(self):
        self.assertEqual(build_flag_assets({'assets': [{'asset_kind': 'script', 'semantic_id': 'old'}]}), [])
        source = catalog(b'\x2a\x2b\x02')
        self.assertEqual(build_flag_assets(source), [])
        partial = build_flag_assets(catalog(b'\x2b\x02\x2a\x2b\x03'))
        self.assertEqual(len(partial), 1)
        self.assertEqual(partial[0]['script_status'], 'partial')
        self.assertEqual(partial[0]['reference_count'], 1)
        self.assertEqual(partial[0]['coverage']['partial_script_count'], 1)
        malformed = deepcopy(source)
        malformed.pop('script_count')
        with self.assertRaises(ProjectError):
            build_flag_assets(malformed)

    def test_invalid_identity_runtime_and_source_layers_fail_closed(self):
        baseline = build_flag_assets(catalog(b'\x2e\x02'))[0]
        def mutate(field, value):
            return lambda row: row.update({field: value})
        mutations = [
            mutate('runtime_binding', 'global_runtime_flag'), mutate('runtime_value', 1),
            mutate('owner_id', 'scene://fixture/actors/man-p1/0002'),
            mutate('semantic_id', 'flag://universal/2'), mutate('index', True),
            mutate('bank', []),
            mutate('extended_target', False), mutate('scope', 'universal'),
            mutate('reference_count', 2), mutate('authored_reference_count', True),
            lambda row: row['source_record'].update(sha256='not-a-hash'),
            lambda row: row['source_record'].update(partition=2),
            lambda row: row['references'][0].update(byte_offset=0),
            lambda row: row['references'][0].update(pc=4 * 1024 * 1024 + 1),
            lambda row: row['references'][0].update(effective_index=3),
            lambda row: row['references'][0].update(extended_target=7),
            lambda row: row['references'][0].update(runtime_value=False),
            lambda row: row['references'].append(deepcopy(row['references'][0])),
            lambda row: row['source_record'].update(payload=b'private'),
            mutate('story_name', 'Invented story identity'),
        ]
        for mutation in mutations:
            with self.subTest(mutation=mutation):
                row = deepcopy(baseline)
                mutation(row)
                with self.assertRaises(ProjectError):
                    validate_flag_asset(row)
        self.assertEqual(validate_flag_asset(baseline), baseline)
        system = next(row for row in build_flag_assets(catalog(b'\x51\x23')) if row['bank'] == 'system')
        system['index'] = 65536
        with self.assertRaisesRegex(ProjectError, 'selector bounds'):
            validate_flag_asset(system)

    def test_adapter_rejects_limits_instead_of_truncating(self):
        source = catalog(b'\x2e\x02\x2e\x03')
        before = deepcopy(source)
        with patch('sdk.flag_assets.MAX_FLAG_ASSETS', 1):
            with self.assertRaisesRegex(ProjectError, 'discovery bounds'):
                build_flag_assets(source)
        with patch('sdk.flag_assets.MAX_FLAG_REFERENCES', 1):
            with self.assertRaisesRegex(ProjectError, 'discovery bounds'):
                build_flag_assets(source)
        self.assertEqual(source, before)


if __name__ == '__main__':
    unittest.main()
