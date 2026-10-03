"""Independent raw-normal accessor edits preserve source packet ownership."""
from copy import deepcopy
import json
import os
from pathlib import Path
import struct
import unittest

from importer.assets import decode_tmd
from importer.core import ImportError
from importer.model_glb import export_model_glb, import_model_glb
from importer.model_primitives import inspect_model_primitives
from test_model_primitives import synthetic

NORMAL = '_LEGAIA_SOURCE_NORMAL'
SENTINEL = (32768.0,) * 3


def glb_parts(content):
    magic, version, length, size, kind = struct.unpack_from('<5I', content)
    assert (magic, version, length, kind) == (0x46546c67, 2, len(content), 0x4e4f534a)
    document = json.loads(content[20:20 + size])
    binary_size, binary_kind = struct.unpack_from('<2I', content, 20 + size)
    assert binary_kind == 0x004e4942
    return document, bytearray(content[28 + size:28 + size + binary_size])


def accessor_rows(document, binary, primitive, name):
    accessor = document['accessors'][primitive['attributes'][name]]
    assert accessor['componentType'] == 5126 and not accessor.get('sparse')
    width = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3}[accessor['type']]
    view = document['bufferViews'][accessor['bufferView']]
    start = view.get('byteOffset', 0) + accessor.get('byteOffset', 0)
    stride = view.get('byteStride', width * 4)
    return [(start + i * stride, struct.unpack_from(f'<{width}f', binary, start + i * stride))
            for i in range(accessor['count'])]


def rewrite(content, callback):
    document, binary = glb_parts(content)
    callback(document, binary)
    document['buffers'] = [{'byteLength': len(binary)}]
    metadata = json.dumps(document, separators=(',', ':'), allow_nan=False).encode()
    metadata += b' ' * (-len(metadata) % 4)
    binary += bytes(-len(binary) % 4)
    return (struct.pack('<5I', 0x46546c67, 2, 28 + len(metadata) + len(binary), len(metadata), 0x4e4f534a)
            + metadata + struct.pack('<2I', len(binary), 0x004e4942) + binary)


def normal_rows(document, binary):
    for mesh in document['meshes']:
        for primitive in mesh['primitives']:
            yield from accessor_rows(document, binary, primitive, NORMAL)


def lit_source(flags):
    source = bytearray(synthetic(((flags,),), count=2))
    inspection = inspect_model_primitives(bytes(source))
    quad, gouraud = bool(flags & 2), flags >= 0x14
    offset = 20 if quad else 18 if gouraud else 12
    slots = 4 if quad and gouraud else 3 if gouraud else 1
    for row in inspection['objects'][0]['primitives']:
        struct.pack_into(f'<{slots}H', source, row['byte_offset'] + offset, *(slot * 8 for slot in range(slots)))
    return bytes(source)


def legacy_profile(profile, version):
    profile = deepcopy(profile)
    profile['schema_version'] = f'legaia.model-glb-profile.v{version}'
    del profile['attributes']['material']
    profile['imported_fields'].remove('primitive_material_words')
    del profile['attributes']['normal_index']
    profile['imported_fields'].remove('primitive_normal_indices')
    del profile['attributes']['normal']
    profile['imported_fields'].remove('normal_xyz')
    if version < 3:
        profile['imported_fields'].remove('primitive_vertex_indices')
    if version == 1:
        del profile['attributes']['color']
        profile['imported_fields'].remove('primitive_rgb')
    return profile


class ModelGlbNormalTests(unittest.TestCase):
    def test_flat_gouraud_tri_quad_roundtrip_and_exact_shared_normal_word_edits(self):
        for flags in (0x10, 0x12, 0x14, 0x16):
            with self.subTest(flags=hex(flags)):
                source = lit_source(flags)
                geometry = decode_tmd(source)
                untouched = deepcopy(geometry)
                glb, profile = export_model_glb(source, geometry)
                self.assertEqual(profile['schema_version'], 'legaia.model-glb-profile.v6')
                self.assertEqual(profile['attributes']['normal'], NORMAL)
                self.assertIn('normal_xyz', profile['imported_fields'])
                self.assertEqual(import_model_glb(source, glb, profile)[0], source)
                normal_base = struct.unpack_from('<I', source, 20)[0] + 12
                slot = 1 if flags >= 0x14 else 0
                value = struct.unpack_from('<3h', source, normal_base + slot * 8)
                document, binary = glb_parts(glb)
                aliases = [v for _, v in normal_rows(document, binary) if v == value]
                self.assertGreater(len(aliases), 1)
                def edit(document, binary):
                    for at, normal in normal_rows(document, binary):
                        if normal == value:
                            struct.pack_into('<f', binary, at + 4, normal[1] + 1.25)
                candidate, report = import_model_glb(source, rewrite(glb, edit), profile)
                expected = bytearray(source)
                struct.pack_into('<h', expected, normal_base + slot * 8 + 2, value[1] + 1)
                self.assertEqual(candidate, bytes(expected))
                self.assertEqual(report['changed_field_count'], 1)
                self.assertEqual(report['quantization']['normal_max_error'], .25)
                self.assertEqual(report['quantization']['quantized_component_count'], 1)
                self.assertEqual(geometry, untouched)

    def test_alias_conflicts_missing_nonfinite_bounds_and_no_reference_changes_reject(self):
        source = lit_source(0x16)
        glb, profile = export_model_glb(source, decode_tmd(source))
        for value in (1.0, float('nan'), float('inf'), -32769.0, 32768.0):
            def edit(document, binary):
                at, _ = next(normal_rows(document, binary))
                struct.pack_into('<f', binary, at, value)
            with self.subTest(value=value), self.assertRaises(ImportError):
                import_model_glb(source, rewrite(glb, edit), profile)
        def remove(document, binary):
            del document['meshes'][0]['primitives'][0]['attributes'][NORMAL]
        with self.assertRaises(ImportError):
            import_model_glb(source, rewrite(glb, remove), profile)
        # A profile never licenses packet normal-reference rewrites.
        row = inspect_model_primitives(source)['objects'][0]['primitives'][0]
        for raw_reference in (4, 32):
            malformed = bytearray(source)
            struct.pack_into('<H', malformed, row['byte_offset'] + 20, raw_reference)
            with self.subTest(reference=raw_reference), self.assertRaises(ImportError):
                export_model_glb(bytes(malformed), decode_tmd(bytes(malformed)))
            with self.assertRaises(ImportError):
                import_model_glb(bytes(malformed), glb, profile)
        missing_table = bytearray(source)
        struct.pack_into('<I', missing_table, 24, 0)
        with self.assertRaises(ImportError):
            export_model_glb(bytes(missing_table), decode_tmd(bytes(missing_table)))

    def test_signed_boundary_normals_preserve_padding_and_unreferenced_vectors(self):
        source = lit_source(0x12)
        glb, profile = export_model_glb(source, decode_tmd(source))
        normal_base = struct.unpack_from('<I', source, 20)[0] + 12
        for value in (-32768, 32767):
            def edit(document, binary):
                for at, _ in normal_rows(document, binary):
                    struct.pack_into('<f', binary, at + 8, value)
            candidate, report = import_model_glb(source, rewrite(glb, edit), profile)
            expected = bytearray(source)
            struct.pack_into('<h', expected, normal_base + 4, value)
            self.assertEqual(candidate, bytes(expected))
            self.assertEqual(report['quantization']['normal_max_error'], 0)
            self.assertEqual(candidate[normal_base + 6:], source[normal_base + 6:])

    def test_unlit_sentinel_and_legacy_imports_ignore_raw_normal_changes(self):
        source = synthetic(((0x22,),), count=1)
        glb, profile = export_model_glb(source, decode_tmd(source))
        document, binary = glb_parts(glb)
        self.assertTrue(all(value == SENTINEL for _, value in normal_rows(document, binary)))
        def edit(document, binary):
            at, _ = next(normal_rows(document, binary))
            struct.pack_into('<f', binary, at, 32767)
        changed = rewrite(glb, edit)
        with self.assertRaises(ImportError):
            import_model_glb(source, changed, profile)
        for version in (1, 2, 3):
            with self.subTest(version=version):
                candidate, report = import_model_glb(source, changed, legacy_profile(profile, version))
                self.assertEqual(candidate, source)
                self.assertNotIn('normal_max_error', report['quantization'])


@unittest.skipUnless(os.environ.get('LEGAIA_DISC_BIN'), 'requires private retail disc')
class RetailModelGlbNormalTests(unittest.TestCase):
    def test_retail_lit_flat_and_gouraud_exact_normal_word_changes(self):
        from importer.assets import load_model_source
        from importer.pipeline import _disc_context, import_scene
        with _disc_context(os.environ['LEGAIA_DISC_BIN']):
            document = import_scene(os.environ['LEGAIA_DISC_BIN'], 'town01')
            chosen = {}
            for asset in document['assets']['models']:
                source = load_model_source(os.environ['LEGAIA_DISC_BIN'], asset)
                inspection = inspect_model_primitives(source)
                for obj in inspection['objects']:
                    for row in obj['primitives']:
                        if 0x10 <= row['flags'] < 0x18:
                            family = 'gouraud' if row['gouraud'] else 'flat'
                            chosen.setdefault(family, (asset, source, obj, row))
                if len(chosen) == 2:
                    break
            self.assertEqual(set(chosen), {'flat', 'gouraud'})
            for family, (asset, source, obj, row) in chosen.items():
                with self.subTest(family=family, asset=asset['semantic_id']):
                    normal_ref_at = row['byte_offset'] + (20 if row['corner_count'] == 4 else
                                                         18 if row['gouraud'] else 12)
                    slot = struct.unpack_from('<H', source, normal_ref_at)[0] // 8
                    normal_base = struct.unpack_from('<I', source, 20 + obj['object_index'] * 28)[0] + 12
                    at = normal_base + slot * 8
                    before = struct.unpack_from('<3h', source, at)
                    delta = 1 if before[0] < 32767 else -1
                    glb, profile = export_model_glb(source, decode_tmd(source))
                    self.assertEqual(import_model_glb(source, glb, profile)[0], source)
                    def edit(document, binary):
                        for node in document['nodes']:
                            if node.get('name') == f"object-{obj['object_index']}":
                                for primitive in document['meshes'][node['mesh']]['primitives']:
                                    for target, value in accessor_rows(document, binary, primitive, NORMAL):
                                        if value == before:
                                            struct.pack_into('<f', binary, target, value[0] + delta)
                    candidate, _ = import_model_glb(source, rewrite(glb, edit), profile)
                    # Equal XYZ vectors can appear at multiple source slots;
                    # independently update exactly those referenced slots.
                    expected = bytearray(source)
                    referenced = set()
                    for primitive in obj['primitives']:
                        if not 0x10 <= primitive['flags'] < 0x18:
                            continue
                        offset = 20 if primitive['corner_count'] == 4 else 18 if primitive['gouraud'] else 12
                        count = primitive['corner_count'] if primitive['gouraud'] else 1
                        refs = struct.unpack_from(f'<{count}H', source, primitive['byte_offset'] + offset)
                        referenced.update(ref // 8 for ref in refs)
                    for normal_id in referenced:
                        target = normal_base + normal_id * 8
                        if struct.unpack_from('<3h', source, target) == before:
                            struct.pack_into('<h', expected, target, before[0] + delta)
                    self.assertNotEqual(candidate, source)
                    self.assertEqual(candidate, bytes(expected))


if __name__ == '__main__':
    unittest.main()
