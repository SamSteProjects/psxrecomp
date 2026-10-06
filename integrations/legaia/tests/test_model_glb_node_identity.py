"""Mesh source ownership survives renamed and reordered tagged object nodes."""
import struct
import unittest

from importer.assets import decode_tmd
from importer.core import ImportError
from importer.model_glb import export_model_glb, import_model_glb
from test_model_glb import synthetic, rewrite, rows


def renamed(doc, _binary):
    for i, node in enumerate(doc['nodes']):
        node['name'] = f'External mesh part {i}'
    doc['nodes'].reverse()
    doc['scenes'][0]['nodes'].reverse()


class ModelNodeIdentity(unittest.TestCase):
    def setUp(self):
        self.source = synthetic(((0x22,), (0x26,)))
        self.glb, self.profile = export_model_glb(self.source, decode_tmd(self.source))

    def test_tagged_reordered_and_unnamed_objects_preserve_every_byte(self):
        self.assertEqual(import_model_glb(self.source, rewrite(self.glb, renamed), self.profile)[0], self.source)
        def unnamed(doc, binary):
            renamed(doc, binary)
            for node in doc['nodes']: node.pop('name')
        self.assertEqual(import_model_glb(self.source, rewrite(self.glb, unnamed), self.profile)[0], self.source)

    def test_reordered_mesh_and_node_indices_edit_exact_same_native_fields(self):
        def edit(doc, binary):
            node = doc['nodes'][1]
            for primitive in doc['meshes'][node['mesh']]['primitives']:
                for at, xyz in rows(doc, binary, primitive, 'POSITION'):
                    struct.pack_into('<f', binary, at, xyz[0] + 3)
        canonical = rewrite(self.glb, edit)
        def reorder(doc, binary):
            renamed(doc, binary)
            count = len(doc['meshes'])
            doc['meshes'].reverse()
            for node in doc['nodes']:
                if 'mesh' in node: node['mesh'] = count - 1 - node['mesh']
        expected, before = import_model_glb(self.source, canonical, self.profile)
        actual, after = import_model_glb(self.source, rewrite(canonical, reorder), self.profile)
        self.assertNotEqual(expected, self.source)
        self.assertEqual(actual, expected)
        self.assertEqual(after, before)

    def test_legacy_names_still_work_and_unqualified_renames_reject(self):
        def legacy(doc, binary):
            for node in doc['nodes']: node.pop('extras')
        self.assertEqual(import_model_glb(self.source, rewrite(self.glb, legacy), self.profile)[0], self.source)
        def unqualified(doc, binary):
            legacy(doc, binary)
            renamed(doc, binary)
        with self.assertRaises(ImportError):
            import_model_glb(self.source, rewrite(self.glb, unqualified), self.profile)

    def test_material_face_selection_uses_same_qualified_object_identity(self):
        from sdk.model_glb_material_selection import _face_rows
        for material in range(4):
            self.assertEqual(_face_rows(self.source, self.glb, material),
                             _face_rows(self.source, rewrite(self.glb, renamed), material))

    def test_malformed_duplicate_conflicting_and_unbounded_identities_reject(self):
        invalid = [None, [], {}, {'object_index': True}, {'object_index': '0'},
                   {'object_index': -1}, {'object_index': 2}, {'object_index': 10**400},
                   {'object_index': 0, 'extensions': {}}]
        for value in invalid:
            def change(doc, binary):
                renamed(doc, binary)
                doc['nodes'][0]['extras']['source_object'] = value
            with self.subTest(value=value), self.assertRaises(ImportError):
                import_model_glb(self.source, rewrite(self.glb, change), self.profile)
        for change in [lambda n: n.update(name='object-0'),
                       lambda n: n.update(name=12),
                       lambda n: n.update(name='object-' + '9' * 5000),
                       lambda n: n['extras']['source_object'].update(object_index=0)]:
            def mutate(doc, binary): change(doc['nodes'][1])
            with self.assertRaises(ImportError):
                import_model_glb(self.source, rewrite(self.glb, mutate), self.profile)


if __name__ == '__main__':
    unittest.main()
