"""Source-byte mesh roundtrip, alias identity and unsupported-layout boundaries."""
from copy import deepcopy
from hashlib import sha256
import struct
import unittest

from importer.animation_glb import _read_glb
from importer.assets import decode_tmd
from importer.core import ImportError
from importer.model_glb import (VERTEX_ID, CORNER_ID, COLOR_ID, export_model_glb,
                                import_model_glb, _write_glb)
from importer.model_primitives import inspect_model_primitives
from test_model_primitives import synthetic


def rewrite(glb, change):
    doc, raw = _read_glb(glb)
    binary = bytearray(raw)
    change(doc, binary)
    return _write_glb(doc, bytes(binary))


def rows(doc, binary, primitive, attribute):
    a = doc['accessors'][primitive['attributes'][attribute]]
    view = doc['bufferViews'][a['bufferView']]
    width = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3}[a['type']]
    start = view.get('byteOffset', 0) + a.get('byteOffset', 0)
    stride = view.get('byteStride', width * 4)
    return [(start + n * stride, struct.unpack_from(f'<{width}f', binary, start + n * stride))
            for n in range(a['count'])]


class ModelGlbTests(unittest.TestCase):
    def test_every_packet_family_noop_preserves_normals_padding_and_opaque_bytes(self):
        for flags in range(0x10, 0x28):
            with self.subTest(flags=hex(flags)):
                source = synthetic(((flags, flags), (flags,)))
                preview = decode_tmd(source)
                before = deepcopy(preview)
                glb, profile = export_model_glb(source, preview)
                candidate, report = import_model_glb(source, glb, profile)
                self.assertEqual(candidate, source)
                self.assertEqual(report['changed_field_count'], 0)
                self.assertEqual(preview, before)
                rgb_profile = deepcopy(profile)
                rgb_profile['schema_version'] = 'legaia.model-glb-profile.v2'
                rgb_profile['imported_fields'].remove('primitive_vertex_indices')
                self.assertEqual(import_model_glb(source, glb, rgb_profile)[0], source)
                legacy = deepcopy(profile)
                legacy['schema_version'] = 'legaia.model-glb-profile.v1'
                del legacy['attributes']['color']
                legacy['imported_fields'].remove('primitive_rgb')
                legacy['imported_fields'].remove('primitive_vertex_indices')
                self.assertEqual(import_model_glb(source, glb, legacy)[0], source)

    def test_vertex_reference_rewire_and_position_edits_have_exact_masks(self):
        for flags in (0x20, 0x22):
            with self.subTest(flags=hex(flags)):
                source = synthetic(((flags,),), count=1)
                geometry = decode_tmd(source)
                glb, profile = export_model_glb(source, geometry)
                row = inspect_model_primitives(source)['objects'][0]['primitives'][0]
                corner = 2
                new_id = 4  # Existing but originally unused source vertex.
                expected = bytearray(source)
                from importer.model_primitives import _primitive_field_locations
                inspection = inspect_model_primitives(source)
                field = next(f for f, _ in _primitive_field_locations(inspection)
                             if f['field'] == 'vertex_index' and f['corner_index'] == corner)
                struct.pack_into('<H', expected, field['byte_offset'], new_id * 8)
                vertex_at = struct.unpack_from('<I', source, 12)[0] + 12 + new_id * 8
                struct.pack_into('<h', expected, vertex_at, geometry['vertices'][new_id][0] + 2)
                def edit(doc, binary):
                    for mesh in doc['meshes']:
                        for primitive in mesh['primitives']:
                            for (at, ids), (position_at, xyz), (_, owner) in zip(
                                    rows(doc, binary, primitive, VERTEX_ID),
                                    rows(doc, binary, primitive, 'POSITION'),
                                    rows(doc, binary, primitive, CORNER_ID)):
                                if owner[0] == corner:
                                    struct.pack_into('<f', binary, at, new_id)
                                    point = geometry['vertices'][new_id]
                                    struct.pack_into('<3f', binary, position_at, point[0] + 2.25, -point[1], point[2])
                changed = rewrite(glb, edit)
                candidate, report = import_model_glb(source, changed, profile)
                self.assertEqual(candidate, bytes(expected))
                self.assertEqual(report['changed_field_count'], 2)
                self.assertEqual(report['quantization']['vertex_max_error'], .25)
                for schema in ('legaia.model-glb-profile.v1', 'legaia.model-glb-profile.v2'):
                    legacy = deepcopy(profile)
                    legacy['schema_version'] = schema
                    legacy['imported_fields'].remove('primitive_vertex_indices')
                    if schema.endswith('v1'):
                        del legacy['attributes']['color']
                        legacy['imported_fields'].remove('primitive_rgb')
                    with self.assertRaises(ImportError):
                        import_model_glb(source, changed, legacy)

    def test_vertex_reference_bounds_and_duplicate_corner_conflicts_reject(self):
        source = synthetic(((0x26,),), count=1)
        glb, profile = export_model_glb(source, decode_tmd(source))
        def change(value, all_copies=False):
            def edit(doc, binary):
                primitive = doc['meshes'][0]['primitives'][0]
                for (at, ids), (_, owner) in zip(rows(doc, binary, primitive, VERTEX_ID),
                                                rows(doc, binary, primitive, CORNER_ID)):
                    if owner[0] == 2:
                        struct.pack_into('<f', binary, at, value)
                        if not all_copies:
                            break
            return edit
        for value, all_copies in ((4, False), (-1, True), (5, True), (8192, True), (2.5, True)):
            with self.subTest(value=value), self.assertRaises(ImportError):
                import_model_glb(source, rewrite(glb, change(value, all_copies)), profile)

    def test_unused_indexed_row_cannot_hide_vertex_reference_conflict(self):
        source = synthetic(((0x26,),), count=1)
        glb, profile = export_model_glb(source, decode_tmd(source))
        def edit(doc, binary):
            primitive = doc['meshes'][0]['primitives'][0]
            # Rebuild the required attributes with an extra unused corner-2 row.
            for attribute in ('POSITION', VERTEX_ID, CORNER_ID, COLOR_ID, 'TEXCOORD_0'):
                original = rows(doc, binary, primitive, attribute)
                data = [list(value) for _, value in original]
                corner_rows = rows(doc, binary, primitive, CORNER_ID)
                alias = next(n for n, (_, value) in enumerate(corner_rows) if value[0] == 2)
                extra = list(data[alias])
                if attribute == VERTEX_ID:
                    extra[0] = 4
                data.append(extra)
                width = len(data[0])
                binary.extend(bytes(-len(binary) % 4))
                at = len(binary)
                flat = [v for value in data for v in value]
                binary.extend(struct.pack(f'<{len(flat)}f', *flat))
                view = len(doc['bufferViews'])
                doc['bufferViews'].append(dict(buffer=0, byteOffset=at, byteLength=len(flat) * 4))
                primitive['attributes'][attribute] = len(doc['accessors'])
                doc['accessors'].append(dict(bufferView=view, componentType=5126, count=len(data),
                                            type='SCALAR' if width == 1 else f'VEC{width}'))
            at = len(binary)
            binary.extend(struct.pack('<6H', *range(6)))
            view = len(doc['bufferViews'])
            doc['bufferViews'].append(dict(buffer=0, byteOffset=at, byteLength=12))
            primitive['indices'] = len(doc['accessors'])
            doc['accessors'].append(dict(bufferView=view, componentType=5123, count=6, type='SCALAR'))
        with self.assertRaisesRegex(ImportError, 'references disagree'):
            import_model_glb(source, rewrite(glb, edit), profile)

    def test_baked_rgb_exact_byte_masks_and_shared_aliases(self):
        for flags in (0x18, 0x1a, 0x1c, 0x1e, 0x20, 0x22, 0x24, 0x26):
            with self.subTest(flags=hex(flags)):
                source = synthetic(((flags,),), count=1)
                glb, profile = export_model_glb(source, decode_tmd(source))
                self.assertEqual(profile['schema_version'], 'legaia.model-glb-profile.v3')
                row = inspect_model_primitives(source)['objects'][0]['primitives'][0]
                expected = bytearray(source)
                for slot in range(len(row['colors'])):
                    expected[row['byte_offset'] + slot * 4] += 3
                def edit(doc, binary):
                    for mesh in doc['meshes']:
                        for primitive in mesh['primitives']:
                            for at, rgb in rows(doc, binary, primitive, COLOR_ID):
                                struct.pack_into('<f', binary, at, rgb[0] + 3.25)
                candidate, report = import_model_glb(source, rewrite(glb, edit), profile)
                self.assertEqual(candidate, bytes(expected))
                self.assertEqual(report['quantization']['color_max_error'], .25)
                self.assertEqual(report['quantization']['quantized_component_count'], len(row['colors']))

    def test_source_rgb_required_finite_bounded_and_aliases_consistent(self):
        for flags in (0x22, 0x26):
            source = synthetic(((flags,),), count=1)
            glb, profile = export_model_glb(source, decode_tmd(source))
            def missing(doc, binary):
                del doc['meshes'][0]['primitives'][0]['attributes'][COLOR_ID]
            def count(doc, binary):
                primitive = doc['meshes'][0]['primitives'][0]
                doc['accessors'][primitive['attributes'][COLOR_ID]]['count'] -= 1
            def change(value):
                def edit(doc, binary):
                    primitive = doc['meshes'][0]['primitives'][0]
                    # Corner 2 appears in both triangles, also aliasing flat RGB.
                    for (at, rgb), (_, corner) in zip(rows(doc, binary, primitive, COLOR_ID),
                                                       rows(doc, binary, primitive, CORNER_ID)):
                        if corner[0] == 2:
                            struct.pack_into('<f', binary, at, value(rgb[0]))
                            break
                return edit
            for edit in (missing, count, change(lambda v: v + 1), change(lambda v: float('nan')),
                         change(lambda v: float('inf')), change(lambda v: -0.25), change(lambda v: 255.25)):
                with self.subTest(flags=hex(flags), edit=edit), self.assertRaises(ImportError):
                    import_model_glb(source, rewrite(glb, edit), profile)

    def test_unbaked_rgb_sentinel_and_legacy_profile_compatibility(self):
        for flags in (0x10, 0x12, 0x14, 0x16, 0x22, 0x26):
            source = synthetic(((flags,),), count=1)
            glb, profile = export_model_glb(source, decode_tmd(source))
            def edit(doc, binary):
                primitive = doc['meshes'][0]['primitives'][0]
                for at, _ in rows(doc, binary, primitive, COLOR_ID):
                    struct.pack_into('<3f', binary, at, 1, 2, 3)
            if flags < 0x18:
                with self.assertRaises(ImportError):
                    import_model_glb(source, rewrite(glb, edit), profile)
            legacy = deepcopy(profile)
            legacy['schema_version'] = 'legaia.model-glb-profile.v1'
            del legacy['attributes']['color']
            legacy['imported_fields'].remove('primitive_rgb')
            legacy['imported_fields'].remove('primitive_vertex_indices')
            def remove(doc, binary):
                for mesh in doc['meshes']:
                    for primitive in mesh['primitives']:
                        del primitive['attributes'][COLOR_ID]
            self.assertEqual(import_model_glb(source, rewrite(glb, remove), legacy)[0], source)
            self.assertEqual(import_model_glb(source, rewrite(glb, edit), legacy)[0], source)

    def test_quad_seam_edits_have_exact_source_byte_mask_and_preserve_unused_vertex(self):
        source = synthetic(((0x22,),))
        glb, profile = export_model_glb(source, decode_tmd(source))
        obj = inspect_model_primitives(source)['objects'][0]
        row = obj['primitives'][0]
        vertex_at = struct.unpack_from('<I', source, 12)[0] + 12 + 8
        uv_at = row['byte_offset'] + 4 + 8  # Flat textured UV2.
        expected = bytearray(source)
        struct.pack_into('<h', expected, vertex_at, struct.unpack_from('<h', source, vertex_at)[0] + 2)
        expected[uv_at] += 1

        def edit(doc, binary):
            for mesh in doc['meshes']:
                for p in mesh['primitives']:
                    for (at, xyz), (_, identity) in zip(rows(doc, binary, p, 'POSITION'), rows(doc, binary, p, VERTEX_ID)):
                        if identity[0] == 1:
                            struct.pack_into('<f', binary, at, xyz[0] + 2.25)
                    for (at, uv), (_, identity) in zip(rows(doc, binary, p, 'TEXCOORD_0'), rows(doc, binary, p, CORNER_ID)):
                        if identity[0] == 2:
                            struct.pack_into('<f', binary, at, uv[0] + 1 / 256)
        candidate, report = import_model_glb(source, rewrite(glb, edit), profile)
        self.assertEqual(candidate, bytes(expected))
        self.assertEqual(report['changed_field_count'], 2)
        self.assertEqual(report['quantization']['vertex_max_error'], .25)
        self.assertEqual(report['quantization']['color_max_error'], 0)
        self.assertEqual(report['quantization']['quantized_component_count'], 1)

    def test_indexed_and_interleaved_storage_does_not_reassign_source_identities(self):
        source = synthetic(((0x22,),))
        glb, profile = export_model_glb(source, decode_tmd(source))

        def interleave(doc, binary):
            for mesh in doc['meshes']:
                for p in mesh['primitives']:
                    values = [rows(doc, binary, p, name) for name in ('POSITION', VERTEX_ID, CORNER_ID, 'TEXCOORD_0')]
                    count = len(values[0])
                    binary.extend(b'\0' * (-len(binary) % 4))
                    at = len(binary)
                    for n in range(count):
                        binary.extend(struct.pack('<7f', *(v for items in values for v in items[n][1])))
                    vi = len(doc['bufferViews'])
                    doc['bufferViews'].append(dict(buffer=0, byteOffset=at, byteLength=count * 28, byteStride=28))
                    for name, width, offset in [('POSITION', 3, 0), (VERTEX_ID, 1, 12), (CORNER_ID, 1, 16), ('TEXCOORD_0', 2, 20)]:
                        ai = len(doc['accessors'])
                        doc['accessors'].append(dict(bufferView=vi, componentType=5126, count=count,
                                                    type='SCALAR' if width == 1 else f'VEC{width}', byteOffset=offset))
                        p['attributes'][name] = ai
                    indices = list(range(count))
                    # Cycle each triangle without changing its orientation.
                    indices = [v for n in range(0, count, 3) for v in (n + 1, n + 2, n)]
                    at = len(binary)
                    binary.extend(struct.pack(f'<{count}H', *indices))
                    vi = len(doc['bufferViews'])
                    doc['bufferViews'].append(dict(buffer=0, byteOffset=at, byteLength=count * 2))
                    p['indices'] = len(doc['accessors'])
                    doc['accessors'].append(dict(bufferView=vi, componentType=5123, count=count, type='SCALAR'))
        self.assertEqual(import_model_glb(source, rewrite(glb, interleave), profile)[0], source)

    def test_conflicting_aliases_lost_ids_topology_and_unapplied_transforms_reject(self):
        source = synthetic(((0x22,),))
        glb, profile = export_model_glb(source, decode_tmd(source))
        def alias(doc, binary):
            p = doc['meshes'][0]['primitives'][0]
            at, xyz = rows(doc, binary, p, 'POSITION')[1]
            struct.pack_into('<f', binary, at, xyz[0] + 1)
        def uv_alias(doc, binary):
            p = doc['meshes'][0]['primitives'][0]
            for (at, uv), (_, identity) in zip(rows(doc, binary, p, 'TEXCOORD_0'), rows(doc, binary, p, CORNER_ID)):
                if identity[0] == 2:
                    struct.pack_into('<f', binary, at, uv[0] + 1 / 256)
                    break
        def lost(doc, binary):
            del doc['meshes'][0]['primitives'][0]['attributes'][CORNER_ID]
        def topology(doc, binary):
            p = doc['meshes'][0]['primitives'][0]
            at, _ = rows(doc, binary, p, CORNER_ID)[0]
            struct.pack_into('<f', binary, at, 3)
        def transform(doc, binary):
            doc['nodes'][0]['translation'] = [1, 0, 0]
        for edit in (alias, uv_alias, lost, topology, transform):
            with self.subTest(edit=edit.__name__), self.assertRaises(ImportError):
                import_model_glb(source, rewrite(glb, edit), profile)

    def test_source_domains_accessor_bounds_profile_and_external_dependencies_reject(self):
        source = synthetic(((0x22,),))
        glb, profile = export_model_glb(source, decode_tmd(source))
        def overflow(doc, binary):
            p = doc['meshes'][0]['primitives'][0]
            at, _ = rows(doc, binary, p, 'POSITION')[0]
            struct.pack_into('<f', binary, at, 32767.25)
        def uv_overflow(doc, binary):
            p = doc['meshes'][0]['primitives'][0]
            at, _ = rows(doc, binary, p, 'TEXCOORD_0')[0]
            struct.pack_into('<f', binary, at, 2)
        def bounds(doc, binary):
            doc['accessors'][0]['byteOffset'] = len(binary)
        def sparse(doc, binary):
            doc['accessors'][0]['sparse'] = {}
        def external(doc, binary):
            doc['images'] = [{'uri': 'https://example.invalid/texture.png'}]
        for edit in (overflow, uv_overflow, bounds, sparse, external):
            with self.subTest(edit=edit.__name__), self.assertRaises(ImportError):
                import_model_glb(source, rewrite(glb, edit), profile)
        stale = deepcopy(profile); stale['effective_sha256'] = sha256(b'wrong').hexdigest()
        with self.assertRaises(ImportError):
            import_model_glb(source, glb, stale)

    def test_display_color_and_normal_edits_cannot_change_source_fields(self):
        source = synthetic(((0x22,),))
        glb, profile = export_model_glb(source, decode_tmd(source))
        def color(doc, binary):
            p = doc['meshes'][0]['primitives'][0]
            for at, _ in rows(doc, binary, p, 'COLOR_0'):
                struct.pack_into('<3f', binary, at, 1, 0, 0)
            p['material'] = 99  # Not a source-owned UV crop or material identity.
        candidate, report = import_model_glb(source, rewrite(glb, color), profile)
        self.assertEqual(candidate, source)
        self.assertEqual(report['changed_field_count'], 0)


if __name__ == '__main__':
    unittest.main()
