"""Existing-layout face rewrites, byte ownership and composed rigid previews."""
from copy import deepcopy
from hashlib import sha256
import os
from pathlib import Path
import struct
import sys
from types import SimpleNamespace
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from importer.assets import decode_tmd
from importer.core import ImportError
from importer.model_authoring import replace_model_content, replace_model_shape, preview_model_shape, model_shape_overlays
from importer.model_json import rotate_shape_object, translate_shape_object, scale_shape_object
from importer.model_primitives import inspect_model_primitives, patch_model_primitives, MAX_PRIMITIVE_EDITS


TRI_VI = (14, 12, 4, 12, 14, 22)
QUAD_VI = (12, 12, 4, 16, 16, 28)
TRI_STRIDE = (20, 24, 12, 20, 20, 28)
QUAD_STRIDE = (24, 28, 12, 24, 24, 36)


def synthetic(object_groups=((0x22,),), count=2):
    """Build independent known packet layouts with opaque footers/vector pads."""
    data = bytearray(12 + len(object_groups) * 28)
    struct.pack_into('<III', data, 0, 0x80000002, 0, len(object_groups))
    for object_index, groups in enumerate(object_groups):
        primitive_start = len(data)
        for flags in groups:
            row, quad = (flags - 0x10) // 4, bool(flags & 2)
            corners = 4 if quad else 3
            stride = (QUAD_STRIDE if quad else TRI_STRIDE)[row]
            vi = (QUAD_VI if quad else TRI_VI)[row]
            textured, gouraud, baked = row in (0, 1, 4, 5), row in (1, 3, 5), row >= 2
            data.extend(struct.pack('<HH4B', count, flags, 9, stride // 4, 1, 0x27))
            for primitive in range(count):
                packet = bytearray((n * 13 + 0x51) & 255 for n in range(stride))
                if baked:
                    for corner in range(corners if gouraud else 1):
                        packet[corner * 4:corner * 4 + 4] = bytes((80 + corner, 120 + corner, 160 + corner, 0xA0 + corner))
                if textured:
                    uv = 0 if row < 2 else (corners * 4 if gouraud else 4)
                    for corner, delta in enumerate((0, 4, 8, 10)[:corners]):
                        packet[uv + delta:uv + delta + 2] = bytes((10 + corner * 20, 240 - corner * 20))
                    struct.pack_into('<H', packet, uv + 2, 0x123)
                    struct.pack_into('<H', packet, uv + 6, 0x41)
                struct.pack_into(f'<{corners}H', packet, vi, *(corner * 8 for corner in range(corners)))
                if not baked:
                    normal_at = (18 if corners == 3 else 20) if gouraud else (12 if corners == 3 else 20)
                    normal_slots = corners if gouraud else 1
                    struct.pack_into(f'<{normal_slots}H', packet, normal_at, *(n * 8 for n in range(normal_slots)))
                data.extend(packet)
            data.extend(bytes([0xCC]) * stride)
        data.extend(bytes(4) + b'KEEP')
        vertex_start = len(data)
        data.extend(b''.join(struct.pack('<4h', n * 10, n * 5, -n * 3, 0x2345) for n in range(5)))
        normal_start = len(data)
        data.extend(b''.join(struct.pack('<4h', 4096, n, -n, 0x3456) for n in range(4)))
        struct.pack_into('<7I', data, 12 + object_index * 28, vertex_start - 12, 5,
                         normal_start - 12, 4, primitive_start - 12, len(groups) * count, 0x00808080)
    return bytes(data)


def identity(row, object_index=0, **fields):
    return {'object_index': object_index, 'primitive_index': row['primitive_index'], **fields}


def audit_diffs(audit):
    result = {}
    for change in audit:
        if change['kind'] == 'primitive' and change['field'] == 'vertex_index':
            before, after = (struct.pack('<H', change[key] * 8) for key in ('before_value', 'after_value'))
        elif change['kind'] == 'primitive':
            before, after = (bytes([change[key]]) for key in ('before_value', 'after_value'))
        else:
            before, after = (struct.pack('<h', change[key]) for key in ('before_value', 'after_value'))
        for delta, (a, b) in enumerate(zip(before, after)):
            if a != b:
                result[change['byte_offset'] + delta] = (a, b)
    return result


class ModelPrimitiveTests(unittest.TestCase):
    def test_all_24_flags_inspection_writes_and_exact_independent_byte_mask(self):
        for flags in range(0x10, 0x28):
            with self.subTest(flags=hex(flags)):
                source = synthetic(((flags, flags),))
                report = inspect_model_primitives(source)
                self.assertEqual(set(report), {'schema_version', 'source_sha256', 'objects'})
                self.assertEqual(report['schema_version'], 'legaia.model-primitives.v1')
                self.assertEqual(report['source_sha256'], sha256(source).hexdigest())
                obj = report['objects'][0]
                self.assertEqual(set(obj), {'object_index', 'vertex_count', 'primitives'})
                self.assertEqual([(p['primitive_index'], p['group_index']) for p in obj['primitives']],
                                 [(0, 0), (1, 0), (2, 1), (3, 1)])
                row, quad = (flags - 0x10) // 4, bool(flags & 2)
                corners = 4 if quad else 3
                packet = obj['primitives'][2]
                self.assertEqual(set(packet), {'primitive_index', 'group_index', 'flags', 'byte_offset',
                    'vertices', 'uvs', 'colors', 'material', 'corner_count', 'gouraud', 'baked_colors'})
                self.assertEqual(packet['vertices'], list(range(corners)))
                self.assertEqual(packet['corner_count'], corners)
                self.assertEqual(packet['gouraud'], row in (1, 3, 5))
                self.assertEqual(packet['baked_colors'], row >= 2)
                self.assertEqual(packet['material']['clut'], 0x123 if row in (0, 1, 4, 5) else None)
                fields = {'vertices': [4, 3, 2, 1][:corners]}
                expected = bytearray(source)
                base = packet['byte_offset']
                vi = (QUAD_VI if quad else TRI_VI)[row]
                struct.pack_into(f'<{corners}H', expected, base + vi, *(v * 8 for v in fields['vertices']))
                if row in (0, 1, 4, 5):
                    uv = 0 if row < 2 else (corners * 4 if row == 5 else 4)
                    fields['uvs'] = [[1 + n * 2, 2 + n * 2] for n in range(corners)]
                    for n, delta in enumerate((0, 4, 8, 10)[:corners]):
                        expected[base + uv + delta:base + uv + delta + 2] = bytes(fields['uvs'][n])
                else:
                    self.assertIsNone(packet['uvs'])
                if row >= 2:
                    words = corners if row in (3, 5) else 1
                    self.assertEqual(len(packet['colors']), words)
                    fields['colors'] = [[200 + n, 201 + n, 202 + n] for n in range(words)]
                    for n, values in enumerate(fields['colors']):
                        expected[base + n * 4:base + n * 4 + 3] = bytes(values)
                else:
                    self.assertIsNone(packet['colors'])
                changed, audit = patch_model_primitives(source, report['source_sha256'], [identity(packet, **fields)])
                self.assertEqual(changed, bytes(expected))
                diffs = {i: (a, b) for i, (a, b) in enumerate(zip(source, changed)) if a != b}
                self.assertEqual(audit_diffs(audit), diffs)
                self.assertTrue(all(c['kind'] == 'primitive' and c['primitive_index'] == 2 and c['group_index'] == 1 for c in audit))
                self.assertEqual(decode_tmd(source)['materials'], decode_tmd(changed)['materials'])
                with self.assertRaises(ImportError):
                    replace_model_shape(source, sha256(source).hexdigest(), changed)
                self.assertEqual(patch_model_primitives(changed, sha256(changed).hexdigest(), [identity(packet, **fields)]), (changed, []))

    def test_noop_detached_metadata_and_source_order_do_not_change_bytes(self):
        source = synthetic(((0x22, 0x25), (0x1A,)))
        report = inspect_model_primitives(source)
        edits = [identity(row, obj['object_index'], vertices=row['vertices']) for obj in report['objects'] for row in obj['primitives']]
        self.assertEqual(patch_model_primitives(source, report['source_sha256'], edits[::-1]), (source, []))
        self.assertEqual(replace_model_content(source, report['source_sha256'], source), (source, []))
        report['objects'][0]['primitives'][0]['vertices'][0] = 999
        report['objects'][0]['primitives'][0]['material']['clut'] = 999
        self.assertEqual(inspect_model_primitives(source)['objects'][0]['primitives'][0]['vertices'][0], 0)

    def test_exact_shapes_indices_uv_colors_identities_and_stale_hash_reject(self):
        source = synthetic(((0x22, 0x11, 0x1D),))
        digest = sha256(source).hexdigest()
        item = {'object_index': 0, 'primitive_index': 0, 'vertices': [0, 1, 2, 3]}
        invalid = [None, {}, [None], [item, item], [item] * (MAX_PRIMITIVE_EDITS + 1),
                   [{'object_index': 0, 'primitive_index': 0}]]
        for forbidden in ('group_index', 'flags', 'clut', 'tpage', 'normal_indices', 'material', 'byte_offset'):
            invalid.append([{**item, forbidden: 1}])
        for field in ('object_index', 'primitive_index'):
            for value in (None, True, 0.0, '0', -1, 100):
                invalid.append([{**item, field: value}])
        for vertices in ([0, 1, 2], [0, 1, 2, 5], [0, 1, 2, 8192], [0, 1, 2, True], [0, 1, 2, 1.0], None):
            invalid.append([{**item, 'vertices': vertices}])
        for values in (None, [[1, 2]], [[1, 2]] * 3, [[1, 256]] * 4, [[True, 2]] * 4, [[1, 2, 3]] * 4):
            invalid.append([{'object_index': 0, 'primitive_index': 0, 'uvs': values}])
        for values in (None, [[1, 2, 3]] * 4, [[1, 2]], [[1, 2, -1]], [[1, 2, True]]):
            invalid.append([{'object_index': 0, 'primitive_index': 0, 'colors': values}])
        invalid.extend(([{'object_index': 0, 'primitive_index': 2, 'colors': None}],
                        [{'object_index': 0, 'primitive_index': 4, 'uvs': None}]))
        for edits in invalid:
            with self.subTest(edits=str(edits)[:90]), self.assertRaises(ImportError):
                patch_model_primitives(source, digest, edits)
        for stale in (None, {}, '0' * 64, digest.upper()):
            with self.assertRaises(ImportError):
                patch_model_primitives(source, stale, [])

    def test_global_aliases_counts_and_explicit_terminators_are_qualified(self):
        source = synthetic(((0x22,), (0x22,)))
        invalid = [None, bytearray(source), source[:-1]]
        bad = bytearray(source); struct.pack_into('<I', bad, 32, 99); invalid.append(bytes(bad))
        bad = bytearray(source); bad[40:68] = bad[12:40]; invalid.append(bytes(bad))
        bad = bytearray(source); struct.pack_into('<I', bad, 20, struct.unpack_from('<I', bad, 12)[0]); invalid.append(bytes(bad))
        bad = bytearray(source); struct.pack_into('<I', bad, 4, 1); invalid.append(bytes(bad))
        # A complete group with no room for a zero terminator is valid for the
        # preview parser but deliberately outside this writer's source scope.
        one = bytearray(synthetic())
        vert, count, normal, nn, prim, claimed, opaque = struct.unpack_from('<7I', one, 12)
        group_end = 40 + 8 + 3 * 24
        del one[group_end:group_end + 8]
        struct.pack_into('<7I', one, 12, vert - 8, count, normal - 8, nn, prim, claimed, opaque)
        self.assertTrue(decode_tmd(bytes(one)))
        invalid.append(bytes(one))
        for data in invalid:
            with self.subTest(size=len(data) if data is not None else None), self.assertRaises(ImportError):
                inspect_model_primitives(data)

    def test_last_representable_u16_vertex_reference_remains_bounded(self):
        source = bytearray(synthetic())
        normal = 12 + struct.unpack_from('<I', source, 20)[0]
        source[normal:normal] = bytes((8193 - 5) * 8)
        struct.pack_into('<I', source, 16, 8193)
        struct.pack_into('<I', source, 20, normal - 12 + (8193 - 5) * 8)
        source = bytes(source)
        digest = sha256(source).hexdigest()
        changed, audit = patch_model_primitives(source, digest,
            [{'object_index': 0, 'primitive_index': 0, 'vertices': [8191, 1, 2, 3]}])
        self.assertEqual(audit[0]['after_value'], 8191)
        self.assertEqual(inspect_model_primitives(changed)['objects'][0]['primitives'][0]['vertices'][0], 8191)
        with self.assertRaises(ImportError):
            patch_model_primitives(source, digest,
                [{'object_index': 0, 'primitive_index': 0, 'vertices': [8192, 1, 2, 3]}])

    def test_legacy_v1_normal_refs_material_words_gpu_codes_footers_and_pads_are_immutable(self):
        source = synthetic(((0x13, 0x27),))
        rows = inspect_model_primitives(source)['objects'][0]['primitives']
        lit, baked = rows[0], rows[2]
        vert, _, normal, _, prim = struct.unpack_from('<5I', source, 12)
        offsets = [0, 4, 8, 12, 36, prim + 12, prim + 12 + 5, prim + 12 + 7,
                   lit['byte_offset'] + 2, lit['byte_offset'] + 6, lit['byte_offset'] + 20,
                   lit['byte_offset'] + 22, lit['byte_offset'] + 2 * 24,
                   baked['byte_offset'] + 3, baked['byte_offset'] + 7,
                   baked['byte_offset'] + 16 + 2, baked['byte_offset'] + 16 + 6,
                   12 + vert + 6, 12 + normal + 6, 12 + vert - 8]
        for offset in offsets:
            changed = bytearray(source); changed[offset] ^= 1
            with self.subTest(offset=offset), self.assertRaises(ImportError):
                replace_model_content(source, sha256(source).hexdigest(), bytes(changed), allow_materials=False)
        invalid_ref = bytearray(source); struct.pack_into('<H', invalid_ref, baked['byte_offset'] + 28, 7)
        with self.assertRaises(ImportError):
            replace_model_content(source, sha256(source).hexdigest(), bytes(invalid_ref))

    def test_vector_primitive_composition_and_object_operations_preserve_both(self):
        source = synthetic(((0x27,),))
        row = inspect_model_primitives(source)['objects'][0]['primitives'][0]
        effective, _ = patch_model_primitives(source, sha256(source).hexdigest(),
            [identity(row, vertices=[4, 3, 2, 1], uvs=[[1, 2], [3, 4], [5, 6], [7, 8]], colors=[[90, 100, 110]] * 4)])
        expected_packets = inspect_model_primitives(effective)['objects']
        operations = ((translate_shape_object, ([3, 4, 5],)), (rotate_shape_object, ('z', 1)),
                      (scale_shape_object, (150,)))
        for function, values in operations:
            with self.subTest(operation=function.__name__):
                changed = function(source, effective, sha256(effective).hexdigest(), 0, *values)
                self.assertEqual(inspect_model_primitives(changed)['objects'], expected_packets)
                _, audit = replace_model_content(source, sha256(source).hexdigest(), changed)
                self.assertEqual({a['kind'] for a in audit}, {'vertex', 'normal', 'primitive'} if function == rotate_shape_object else {'vertex', 'primitive'})
                self.assertEqual(audit_diffs(audit), {i: (a, b) for i, (a, b) in enumerate(zip(source, changed)) if a != b})
        vectors = bytearray(source); at = 12 + struct.unpack_from('<I', source, 12)[0]
        struct.pack_into('<h', vectors, at, 7); vectors = bytes(vectors)
        composed, _ = patch_model_primitives(vectors, sha256(vectors).hexdigest(), [identity(row, vertices=[4, 3, 2, 1])])
        self.assertEqual(struct.unpack_from('<h', composed, at)[0], 7)
        self.assertEqual(replace_model_content(source, sha256(source).hexdigest(), composed)[1][0]['kind'], 'vertex')

    def test_pose_prefix_frames_face_arrays_and_material_evidence_remain_coherent(self):
        source = synthetic(((0x27,), (0x13,)))
        row = inspect_model_primitives(source)['objects'][0]['primitives'][0]
        changed, _ = patch_model_primitives(source, sha256(source).hexdigest(),
            [identity(row, vertices=[4, 3, 2, 1], uvs=[[1, 2], [3, 4], [5, 6], [7, 8]], colors=[[90, 100, 110]] * 4)])
        preview = decode_tmd(source); obj = preview['objects'][0]; nv, nt = obj['vertex_count'], obj['triangle_count']
        preview['objects'] = preview['objects'][:1]; preview['vertices'] = preview['vertices'][:nv]
        for key in ('triangles', 'triangle_colors', 'triangle_uvs', 'triangle_materials'):
            preview[key] = preview[key][:nt]
        transforms = [{'object_index': 0, 'translation': [3, 4, 5], 'rotation_psx': [0, 0, 1024]}]
        preview.update(posed=True, pose={'object_transforms': transforms}, source_record={'immutable': True},
                       frames=[{'object_transforms': transforms}, {'object_transforms': [{'object_index': 0,
                           'translation': [20, 30, 40], 'rotation_psx': [0, 0, 0]}]}])
        preview['materials'][0]['blend'] = {'evidence': 'existing-address-binding'}
        baseline = deepcopy(preview)
        result = preview_model_shape(preview, changed, {'format': 'tmd-content-v1'})
        candidate = decode_tmd(changed)
        for key in ('triangles', 'triangle_colors', 'triangle_uvs', 'triangle_materials'):
            self.assertEqual(result[key], candidate[key][:nt])
        self.assertEqual(result['vertices'][0], [3.0, 4.0, 5.0])
        self.assertEqual(result['frames'][1]['vertices'][0], [20.0, 30.0, 40.0])
        self.assertEqual(result['source_record'], preview['source_record'])
        self.assertEqual(result['materials'], preview['materials'])
        self.assertEqual(preview, baseline)
        mismatched = deepcopy(preview); mismatched['objects'][0]['triangle_count'] += 1
        with self.assertRaises(ImportError): preview_model_shape(mismatched, changed, {})
        material = bytearray(changed); material[row['byte_offset'] + 16 + 2] ^= 1
        with self.assertRaises(ImportError): preview_model_shape(preview, bytes(material), {})

    def test_raw_overlay_scope_and_payload_include_general_content_audit(self):
        source = synthetic()
        row = inspect_model_primitives(source)['objects'][0]['primitives'][0]
        changed, _ = patch_model_primitives(source, sha256(source).hexdigest(), [identity(row, vertices=[4, 3, 2, 1])])
        archive = SimpleNamespace(node=SimpleNamespace(extent_lba=50),
            entry=lambda index: SimpleNamespace(start_lba=3), read_entry=lambda entry: source)
        assets = {'model': {'source_record': {'record_kind': 'raw_prot_entry', 'prot_entry_index': 0,
                                             'byte_offset': 0, 'byte_length': len(source), 'containing_size': len(source)}}}
        overlays, audit = model_shape_overlays(archive, assets, {'model': changed})
        self.assertEqual(overlays[0]['payload'], changed)
        self.assertEqual(overlays[0]['offset'], 53 * 2048)
        self.assertEqual(audit[0]['scope'], 'TMD-existing-layout-content')
        self.assertTrue(all(c['kind'] == 'primitive' for c in audit[0]['coordinate_changes']))
        self.assertEqual(model_shape_overlays(archive, assets, {'model': source}), ([], []))
        vectors = bytearray(source); at = 12 + struct.unpack_from('<I', source, 12)[0]
        struct.pack_into('<h', vectors, at, 7)
        _, audit = model_shape_overlays(archive, assets, {'model': bytes(vectors)})
        self.assertEqual(audit[0]['scope'], 'TMD-vertex-normal-XYZ-only')
        self.assertEqual(audit[0]['coordinate_changes'][0]['kind'], 'vertex')


@unittest.skipUnless(os.environ.get('LEGAIA_DISC_BIN'), 'requires private retail disc')
class RetailModelPrimitiveTests(unittest.TestCase):
    def test_town01_fresh_face_uv_rgb_build_stream_and_independent_readback(self):
        from importer.pipeline import _disc_context, import_scene
        from importer.assets import load_model_source
        from importer.core import decompress_lzs
        disc = os.environ['LEGAIA_DISC_BIN']
        with _disc_context(disc) as (_, _, _, archive):
            asset = import_scene(disc, 'town01')['assets']['models'][0]
            source = load_model_source(disc, asset)
            inspection = inspect_model_primitives(source); row = inspection['objects'][0]['primitives'][0]
            self.assertEqual(row['flags'], 0x21)
            vertices, uvs, colors = deepcopy(row['vertices']), deepcopy(row['uvs']), deepcopy(row['colors'])
            vertices[0], vertices[1] = vertices[1], vertices[0]
            uvs[0][0] = (uvs[0][0] + 1) % 256; colors[0][0] = (colors[0][0] + 1) % 256
            changed, audit = patch_model_primitives(source, inspection['source_sha256'],
                [identity(row, vertices=vertices, uvs=uvs, colors=colors)])
            self.assertEqual([i for i, (a, b) in enumerate(zip(source, changed)) if a != b], [48, 52, 62, 64])
            self.assertEqual(audit_diffs(audit), {i: (a, b) for i, (a, b) in enumerate(zip(source, changed)) if a != b})
            self.assertEqual(decode_tmd(source)['materials'], decode_tmd(changed)['materials'])
            overlays, changes = model_shape_overlays(archive, {asset['semantic_id']: asset}, {asset['semantic_id']: changed})
            self.assertEqual(changes[0]['scope'], 'TMD-existing-layout-content')
            overlay = overlays[0]
            self.assertLessEqual(overlay['new_encoded_size'], overlay['original_encoded_size'])
            decoded, _ = decompress_lzs(overlay['payload'], overlay['decoded_size'])
            start = asset['source_record']['byte_offset']
            self.assertEqual(decoded[start:start + len(changed)], changed)
            self.assertEqual(sha256(decoded).hexdigest(), overlay['decoded_after_sha256'])

    def test_vahn_idle_prefix_keeps_full_materials_and_verified_frame_coordinates(self):
        from importer.pipeline import _disc_context, import_scene
        from importer.assets import load_model_source
        from importer.animation import load_animation_preview
        disc = os.environ['LEGAIA_DISC_BIN']
        with _disc_context(disc):
            assets = import_scene(disc, 'town01')['assets']['models']
            asset = next(a for a in assets if a['semantic_id'] == 'asset://legaia/models/global-special/00f0')
            source = load_model_source(disc, asset)
            inspection = inspect_model_primitives(source); row = inspection['objects'][0]['primitives'][0]
            vertices = deepcopy(row['vertices']); vertices[0], vertices[1] = vertices[1], vertices[0]
            candidate, _ = patch_model_primitives(source, inspection['source_sha256'], [identity(row, vertices=vertices)])
            animation = load_animation_preview(disc, asset, 'idle')
        preview = deepcopy(animation['geometry'])
        preview['frames'] = deepcopy(animation['frames'])
        preview['pose'] = {'object_transforms': deepcopy(animation['frames'][0]['object_transforms'])}
        preview['posed'] = True
        self.assertEqual(len(inspection['objects']), 12)
        self.assertEqual(len(preview['objects']), 10)
        self.assertEqual(preview['materials'], decode_tmd(source)['materials'])
        result = preview_model_shape(preview, candidate, {'format': 'tmd-content-v1'})
        self.assertEqual(len(result['objects']), 10)
        self.assertEqual(result['materials'], preview['materials'])
        self.assertEqual(result['vertices'], animation['frames'][0]['vertices'])
        self.assertEqual([f['vertices'] for f in result['frames']], [f['vertices'] for f in animation['frames']])
        self.assertNotEqual(result['triangles'][0], preview['triangles'][0])


if __name__ == '__main__':
    unittest.main()
