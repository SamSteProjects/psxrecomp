"""Source-object identity survives readable external names and node ordering."""
from copy import deepcopy
import unittest

from importer.animation_glb import import_animation_glb
from importer.core import ImportError
from test_animation_glb import document, encode, record, changed_key


def rename_and_reorder(doc):
    doc = deepcopy(doc)
    count = len(doc['nodes'])
    for i, node in enumerate(doc['nodes']):
        node['name'] = f'External rigid part {i}'
    doc['nodes'].reverse()
    doc['scenes'][0]['nodes'] = [count - 1 - i for i in doc['scenes'][0]['nodes']]
    for clip in doc.get('animations', []):
        for channel in clip['channels']:
            channel['target']['node'] = count - 1 - channel['target']['node']
    return doc


class NodeIdentity(unittest.TestCase):
    def fixture(self):
        frames = [[([i * 12, 3, -2], [i * 8, 0, 0]) for i in range(3)]] * 3
        doc, payload = document(frames)
        return record(frames), doc, payload

    def test_renamed_reordered_nodes_preserve_native_bytes_and_opaque_data(self):
        source, doc, payload = self.fixture()
        candidate, report = import_animation_glb(source, encode(rename_and_reorder(doc), payload), fps=15)
        self.assertEqual(candidate, source)
        self.assertEqual(report['changed_axes'], 0)

    def test_renamed_channels_edit_the_exact_source_object(self):
        source, doc, payload = self.fixture()
        payload = changed_key(doc, payload, 'translation', 1, [31, -3, -2], obj=2)
        expected, original_report = import_animation_glb(source, encode(doc, payload), fps=15)
        actual, report = import_animation_glb(source, encode(rename_and_reorder(doc), payload), fps=15)
        self.assertEqual(actual, expected)
        self.assertEqual(report['changes'], original_report['changes'])
        self.assertEqual(report['changed_axes'], 1)

    def test_missing_display_names_and_name_only_legacy_mapping(self):
        source, doc, payload = self.fixture()
        unnamed = deepcopy(doc)
        for node in unnamed['nodes']: node.pop('name')
        self.assertEqual(import_animation_glb(source, encode(unnamed, payload), fps=15)[0], source)
        for node in doc['nodes']: node.pop('extras')
        self.assertEqual(import_animation_glb(source, encode(doc, payload), fps=15)[0], source)
        doc['nodes'][0]['name'] = 'unqualified part'
        with self.assertRaises(ImportError): import_animation_glb(source, encode(doc, payload), fps=15)

    def test_malformed_duplicate_and_contradictory_source_identities_reject(self):
        source, doc, payload = self.fixture()
        invalid = [None, [], {}, {'object_index': True}, {'object_index': '0'},
                   {'object_index': -1}, {'object_index': 3}, {'object_index': 10**400},
                   {'object_index': 0, 'extensions': {}}]
        for identity in invalid:
            bad = rename_and_reorder(doc)
            bad['nodes'][0]['extras']['source_object'] = identity
            with self.subTest(identity=identity):
                with self.assertRaises(ImportError): import_animation_glb(source, encode(bad, payload), fps=15)
        for mutate in [lambda d: d['nodes'][1]['extras']['source_object'].update(object_index=0),
                       lambda d: d['nodes'][1].update(name='object-0'),
                       lambda d: d['nodes'][1].update(name=12)]:
            bad = deepcopy(doc); mutate(bad)
            with self.assertRaises(ImportError): import_animation_glb(source, encode(bad, payload), fps=15)
