"""External raw material selectors retain qualified packet masks and aliases."""
from copy import deepcopy
import os
import struct
import unittest

from importer.assets import decode_tmd
from importer.core import ImportError
from importer.model_glb import export_model_glb, import_model_glb
from importer.model_materials import inspect_model_materials
from importer.model_primitives import inspect_model_primitives
from test_model_glb_normals import accessor_rows, rewrite
from test_model_primitives import synthetic

MATERIAL = '_LEGAIA_SOURCE_MATERIAL'
CORNER = '_LEGAIA_SOURCE_CORNER'


def edit_material(content, values, *, object_index=0, primitive_index=None, first_only=False):
    def edit(document, binary):
        for node in document['nodes']:
            if node.get('name') != f'object-{object_index}':
                continue
            for primitive in document['meshes'][node['mesh']]['primitives']:
                for (at, old), (_, owner) in zip(accessor_rows(document, binary, primitive, MATERIAL),
                                               accessor_rows(document, binary, primitive, CORNER)):
                    selected = primitive_index is None or int(owner[0]) // 4 in (
                        primitive_index if isinstance(primitive_index, tuple) else (primitive_index,))
                    if selected:
                        target = [old[i] if value is None else value for i, value in enumerate(values)]
                        struct.pack_into('<3f', binary, at, *target)
                        if first_only:
                            return
    return rewrite(content, edit)


def source_with_reserved_words():
    source = bytearray(synthetic(((0x22,),), count=2))
    for row in inspect_model_primitives(bytes(source))['objects'][0]['primitives']:
        struct.pack_into('<H', source, row['byte_offset'] + 6, 0x8123)
        struct.pack_into('<H', source, row['byte_offset'] + 10, 0xe041)
    return bytes(source)


class ModelGlbMaterialTests(unittest.TestCase):
    def test_noop_and_masked_words_exactly_preserve_layout_opaque_bits_and_group_owner(self):
        source = source_with_reserved_words()
        glb, profile = export_model_glb(source, decode_tmd(source))
        self.assertEqual(profile['schema_version'], 'legaia.model-glb-profile.v6')
        self.assertEqual(profile['attributes']['material'], MATERIAL)
        self.assertEqual(import_model_glb(source, glb, profile)[0], source)
        candidate, report = import_model_glb(source, edit_material(glb, (0x8124, 0xe051, 0)), profile)
        expected = bytearray(source)
        catalog = inspect_model_materials(source)
        group = catalog['objects'][0]['groups'][0]
        expected[group['byte_offset'] + 7] ^= 2
        for row in group['primitives']:
            struct.pack_into('<H', expected, row['byte_offset'] + 6, 0x8124)
            struct.pack_into('<H', expected, row['byte_offset'] + 10, 0xe051)
        self.assertEqual(candidate, bytes(expected))
        self.assertEqual(len(candidate), len(source))
        self.assertEqual(report['changed_field_count'], 5)

    def test_shared_abe_and_corner_aliases_reject_conflicting_copies(self):
        source = source_with_reserved_words()
        glb, profile = export_model_glb(source, decode_tmd(source))
        for values, options in [((None, None, 0), dict(primitive_index=0)),
                                ((0x8124, None, None), dict(primitive_index=0, first_only=True))]:
            with self.subTest(values=values), self.assertRaises(ImportError):
                import_model_glb(source, edit_material(glb, values, **options), profile)

    def test_exact_integer_ranges_readonly_bits_and_target_depth_are_qualified(self):
        source = source_with_reserved_words()
        glb, profile = export_model_glb(source, decode_tmd(source))
        for values in [(0x124, None, None), (None, 0xe061, None), (None, 0xc041, None),
                       (None, 0xe1c1, None), (0x8124, 0xe141, None), (-1, None, None),
                       (65536, None, None), (1.5, None, None), (float('nan'), None, None),
                       (None, float('inf'), None), (None, None, 2), (None, None, .5)]:
            with self.subTest(values=values), self.assertRaises(ImportError):
                import_model_glb(source, edit_material(glb, values), profile)

    def test_untextured_sentinel_only_allows_shared_abe_and_malformed_attribute_rejects(self):
        source = synthetic(((0x22,), (0x18,)), count=2)
        glb, profile = export_model_glb(source, decode_tmd(source))
        candidate, _ = import_model_glb(source, edit_material(glb, (-1, -1, 0), object_index=1), profile)
        expected = bytearray(source)
        group = inspect_model_materials(source)['objects'][1]['groups'][0]
        expected[group['byte_offset'] + 7] ^= 2
        self.assertEqual(candidate, bytes(expected))
        with self.assertRaises(ImportError):
            import_model_glb(source, edit_material(glb, (0, -1, 0), object_index=1), profile)
        for mutation in ('missing', 'shape', 'component'):
            def malformed(document, binary):
                attrs = document['meshes'][0]['primitives'][0]['attributes']
                if mutation == 'missing':
                    del attrs[MATERIAL]
                else:
                    accessor = document['accessors'][attrs[MATERIAL]]
                    accessor['type' if mutation == 'shape' else 'componentType'] = 'VEC2' if mutation == 'shape' else 5123
            with self.subTest(mutation=mutation), self.assertRaises(ImportError):
                import_model_glb(source, rewrite(glb, malformed), profile)

    def test_legacy_profiles_retain_materials_and_stale_source_rejects(self):
        source = source_with_reserved_words()
        glb, profile = export_model_glb(source, decode_tmd(source))
        edited = edit_material(glb, (0x8124, 0xe051, 0))
        for version in range(1, 6):
            legacy = deepcopy(profile)
            legacy['schema_version'] = f'legaia.model-glb-profile.v{version}'
            for name, introduced in [('material', 6), ('normal_index', 5), ('normal', 4), ('color', 2)]:
                if version < introduced:
                    del legacy['attributes'][name]
            introduced = {'vertex_xyz': 1, 'primitive_uv': 1, 'primitive_rgb': 2,
                          'primitive_vertex_indices': 3, 'normal_xyz': 4,
                          'primitive_normal_indices': 5, 'primitive_material_words': 6}
            legacy['imported_fields'] = [field for field in legacy['imported_fields'] if introduced[field] <= version]
            with self.subTest(version=version):
                self.assertEqual(import_model_glb(source, glb, legacy)[0], source)
                with self.assertRaises(ImportError):
                    import_model_glb(source, edited, legacy)
        stale = deepcopy(profile)
        stale['effective_sha256'] = '0' * 64
        with self.assertRaises(ImportError):
            import_model_glb(source, edited, stale)


@unittest.skipUnless(os.environ.get('LEGAIA_DISC_BIN'), 'requires private retail disc')
class RetailModelGlbMaterialTests(unittest.TestCase):
    def test_retail_selector_and_shared_abe_edits_equal_independent_raw_packet_words(self):
        from importer.assets import load_model_source
        from importer.pipeline import _disc_context, import_scene
        with _disc_context(os.environ['LEGAIA_DISC_BIN']):
            document = import_scene(os.environ['LEGAIA_DISC_BIN'], 'town01')
            selected = None
            for asset in document['assets']['models']:
                source = load_model_source(os.environ['LEGAIA_DISC_BIN'], asset)
                for obj in inspect_model_materials(source)['objects']:
                    for group in obj['groups']:
                        row = next((r for r in group['primitives'] if r['textured'] and r['texture_bpp'] in (4, 8)), None)
                        if row:
                            selected = source, obj, group, row
                            break
                    if selected:
                        break
                if selected:
                    break
            self.assertIsNotNone(selected)
            source, obj, group, row = selected
            glb, profile = export_model_glb(source, decode_tmd(source))
            self.assertEqual(import_model_glb(source, glb, profile)[0], source)
            candidate, _ = import_model_glb(source, edit_material(glb, (row['clut'] ^ 1, row['tpage'] ^ 1, None),
                                      object_index=obj['object_index'], primitive_index=row['primitive_index']), profile)
            expected = bytearray(source)
            primitive = inspect_model_primitives(source)['objects'][obj['object_index']]['primitives'][row['primitive_index']]
            family = (primitive['flags'] - 0x10) // 4
            uv = 0 if family < 2 else primitive['corner_count'] * 4 if primitive['gouraud'] else 4
            struct.pack_into('<H', expected, row['byte_offset'] + uv + 2, row['clut'] ^ 1)
            struct.pack_into('<H', expected, row['byte_offset'] + uv + 6, row['tpage'] ^ 1)
            self.assertEqual(candidate, bytes(expected))
            group_rows = tuple(member['primitive_index'] for member in group['primitives'])
            abe = 0 if group['semi_transparent'] else 1
            composed = edit_material(edit_material(glb, (row['clut'] ^ 1, row['tpage'] ^ 1, None),
                                     object_index=obj['object_index'], primitive_index=row['primitive_index']),
                                     (None, None, abe), object_index=obj['object_index'], primitive_index=group_rows)
            with_abe, _ = import_model_glb(source, composed, profile)
            expected[group['byte_offset'] + 7] ^= 2
            self.assertEqual(with_abe, bytes(expected))


if __name__ == '__main__':
    unittest.main()
