"""Source-corner normal ownership rewiring through independent GLB accessors."""
from copy import deepcopy
from hashlib import sha256
import os
import struct
import unittest

from importer.assets import decode_tmd
from importer.core import ImportError
from importer.model_authoring import replace_model_content
from importer.model_glb import export_model_glb, import_model_glb
from importer.model_primitives import inspect_model_primitives
from test_model_glb_normals import accessor_rows, glb_parts, lit_source, rewrite
from test_model_primitives import synthetic

NORMAL = '_LEGAIA_SOURCE_NORMAL'
INDEX = '_LEGAIA_SOURCE_NORMAL_INDEX'
CORNER = '_LEGAIA_SOURCE_CORNER'


def normal_reference_offset(row, slot):
    return row['byte_offset'] + (20 if row['corner_count'] == 4 else 18 if row['gouraud'] else 12) + slot * 2


def rewire(content, new_id, xyz, *, primitive_index=0, corner=2, gouraud=True,
           object_index=0, first_only=False):
    def edit(document, binary):
        for node in document['nodes']:
            if node.get('name') != f'object-{object_index}':
                continue
            for primitive in document['meshes'][node['mesh']]['primitives']:
                rows = zip(accessor_rows(document, binary, primitive, CORNER),
                           accessor_rows(document, binary, primitive, INDEX),
                           accessor_rows(document, binary, primitive, NORMAL))
                for (_, owner), (at, _), (normal_at, _) in rows:
                    if int(owner[0]) // 4 == primitive_index and (not gouraud or int(owner[0]) % 4 == corner):
                        struct.pack_into('<f', binary, at, new_id)
                        if xyz is not None:
                            struct.pack_into('<3f', binary, normal_at, *xyz)
                        if first_only:
                            return
    return rewrite(content, edit)


def v4_profile(profile):
    legacy = deepcopy(profile)
    legacy['schema_version'] = 'legaia.model-glb-profile.v4'
    del legacy['attributes']['normal_index']
    legacy['imported_fields'].remove('primitive_normal_indices')
    return legacy


class ModelGlbNormalReferenceTests(unittest.TestCase):
    def test_flat_gouraud_triangle_quad_exact_reference_words_and_no_table_mutation(self):
        for flags in (0x10, 0x12, 0x14, 0x16):
            with self.subTest(flags=hex(flags)):
                source = lit_source(flags)
                glb, profile = export_model_glb(source, decode_tmd(source))
                self.assertEqual(profile['schema_version'], 'legaia.model-glb-profile.v5')
                self.assertEqual(profile['attributes']['normal_index'], INDEX)
                self.assertEqual(import_model_glb(source, glb, profile)[0], source)
                row = inspect_model_primitives(source)['objects'][0]['primitives'][0]
                base = struct.unpack_from('<I', source, 20)[0] + 12
                value = struct.unpack_from('<3h', source, base + 3 * 8)
                edited = rewire(glb, 3, value, gouraud=row['gouraud'])
                candidate, report = import_model_glb(source, edited, profile)
                expected = bytearray(source)
                at = normal_reference_offset(row, 2 if row['gouraud'] else 0)
                struct.pack_into('<H', expected, at, 3 * 8)
                self.assertEqual(candidate, bytes(expected))
                self.assertEqual(report['changed_field_count'], 1)
                self.assertEqual(candidate[base:], source[base:])
                with self.assertRaises(ImportError):
                    replace_model_content(source, sha256(source).hexdigest(), candidate)
                replacement, audit = replace_model_content(source, sha256(source).hexdigest(),
                                                           candidate, allow_normal_references=True)
                self.assertEqual(replacement, candidate)
                self.assertEqual([(entry['kind'], entry['field'], entry['byte_offset']) for entry in audit],
                                 [('primitive', 'normal_index', at)])
                # V4 retains the original owner despite a changed optional V5
                # index attribute; an accompanying XYZ edit belongs to that
                # original normal, rather than authorizing a packet rewire.
                index_only = rewire(glb, 3, None, gouraud=row['gouraud'])
                self.assertEqual(import_model_glb(source, index_only, v4_profile(profile))[0], source)

    def test_bounds_missing_alias_conflicts_and_nonfinite_normal_ids_reject(self):
        source = lit_source(0x16)
        glb, profile = export_model_glb(source, decode_tmd(source))
        for value in (-1, 4, 8192, .5, float('nan'), float('inf')):
            with self.subTest(value=value), self.assertRaises(ImportError):
                import_model_glb(source, rewire(glb, value, None), profile)
        base = struct.unpack_from('<I', source, 20)[0] + 12
        xyz = struct.unpack_from('<3h', source, base + 3 * 8)
        with self.assertRaises(ImportError):
            import_model_glb(source, rewire(glb, 3, xyz, first_only=True), profile)
        # Corner3 already selects normal3. Rewiring corner2 to it with the old
        # corner2 XYZ produces incompatible aliases of the same normal owner.
        old_xyz = struct.unpack_from('<3h', source, base + 2 * 8)
        with self.assertRaises(ImportError):
            import_model_glb(source, rewire(glb, 3, old_xyz), profile)
        def remove(document, binary):
            del document['meshes'][0]['primitives'][0]['attributes'][INDEX]
        with self.assertRaises(ImportError):
            import_model_glb(source, rewrite(glb, remove), profile)

    def test_unlit_minus_one_and_unused_unindexed_alias_cannot_hide_reference_change(self):
        source = synthetic(((0x22,),), count=1)
        glb, profile = export_model_glb(source, decode_tmd(source))
        document, binary = glb_parts(glb)
        self.assertTrue(all(value == (-1.0,) for mesh in document['meshes']
                            for primitive in mesh['primitives']
                            for _, value in accessor_rows(document, binary, primitive, INDEX)))
        with self.assertRaises(ImportError):
            import_model_glb(source, rewire(glb, 0, None, gouraud=False), profile)
        source = lit_source(0x16)
        glb, profile = export_model_glb(source, decode_tmd(source))
        def unused_conflict(document, binary):
            primitive = document['meshes'][0]['primitives'][0]
            # Add an unindexed alias of source corner2, with a conflicting
            # normal owner. Keep all required attributes equally sized.
            original_count = None
            for name in list(primitive['attributes']):
                rows = accessor_rows(document, binary, primitive, name)
                values = [list(value) for _, value in rows]
                corners = accessor_rows(document, binary, primitive, CORNER)
                selected = next(i for i, (_, corner) in enumerate(corners) if corner == (2.0,))
                extra = values[selected].copy()
                if name == INDEX:
                    extra[0] = 3
                values.append(extra)
                width = len(extra)
                binary.extend(bytes(-len(binary) % 4))
                at = len(binary)
                flattened = [value for row in values for value in row]
                binary.extend(struct.pack(f'<{len(flattened)}f', *flattened))
                view = len(document['bufferViews'])
                document['bufferViews'].append(dict(buffer=0, byteOffset=at, byteLength=len(flattened) * 4))
                primitive['attributes'][name] = len(document['accessors'])
                document['accessors'].append(dict(bufferView=view, componentType=5126, count=len(values),
                                                  type='SCALAR' if width == 1 else f'VEC{width}'))
                original_count = len(rows)
            binary.extend(bytes(-len(binary) % 4))
            at = len(binary)
            binary.extend(struct.pack(f'<{original_count}H', *range(original_count)))
            view = len(document['bufferViews'])
            document['bufferViews'].append(dict(buffer=0, byteOffset=at, byteLength=original_count * 2))
            primitive['indices'] = len(document['accessors'])
            document['accessors'].append(dict(bufferView=view, componentType=5123, count=original_count, type='SCALAR'))
        with self.assertRaises(ImportError):
            import_model_glb(source, rewrite(glb, unused_conflict), profile)


@unittest.skipUnless(os.environ.get('LEGAIA_DISC_BIN'), 'requires private retail disc')
class RetailModelGlbNormalReferenceTests(unittest.TestCase):
    def test_retail_flat_gouraud_reference_only_replacements_match_independent_packet_words(self):
        from importer.assets import load_model_source
        from importer.pipeline import _disc_context, import_scene
        with _disc_context(os.environ['LEGAIA_DISC_BIN']):
            document = import_scene(os.environ['LEGAIA_DISC_BIN'], 'town01')
            chosen = {}
            for asset in document['assets']['models']:
                source = load_model_source(os.environ['LEGAIA_DISC_BIN'], asset)
                inspection = inspect_model_primitives(source)
                for obj in inspection['objects']:
                    if struct.unpack_from('<I', source, 24 + obj['object_index'] * 28)[0] < 2:
                        continue
                    for row in obj['primitives']:
                        if 0x10 <= row['flags'] < 0x18:
                            chosen.setdefault('gouraud' if row['gouraud'] else 'flat', (asset, source, obj, row))
                if len(chosen) == 2:
                    break
            self.assertEqual(set(chosen), {'flat', 'gouraud'})
            for family, (asset, source, obj, row) in chosen.items():
                with self.subTest(family=family, asset=asset['semantic_id']):
                    at = normal_reference_offset(row, 0)
                    current = struct.unpack_from('<H', source, at)[0] // 8
                    target = 0 if current != 0 else 1
                    base = struct.unpack_from('<I', source, 20 + obj['object_index'] * 28)[0] + 12
                    xyz = struct.unpack_from('<3h', source, base + target * 8)
                    glb, profile = export_model_glb(source, decode_tmd(source))
                    edited = rewire(glb, target, xyz, object_index=obj['object_index'],
                                    primitive_index=row['primitive_index'], corner=0, gouraud=row['gouraud'])
                    candidate, _ = import_model_glb(source, edited, profile)
                    expected = bytearray(source)
                    struct.pack_into('<H', expected, at, target * 8)
                    self.assertEqual(candidate, bytes(expected))
                    self.assertEqual(candidate[base:base + 8 * struct.unpack_from('<I', source, 24 + obj['object_index'] * 28)[0]],
                                     source[base:base + 8 * struct.unpack_from('<I', source, 24 + obj['object_index'] * 28)[0]])


if __name__ == '__main__':
    unittest.main()
