"""Masked source material authoring, strict legacy reads and rigid previews."""
from copy import deepcopy
from hashlib import sha256
import os
from pathlib import Path
import struct
import sys
from types import SimpleNamespace
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from importer.animation import pose_vertices
from importer.assets import decode_tmd
from importer.core import ImportError
from importer.model_authoring import model_shape_overlays, preview_model_shape, replace_model_content, replace_model_shape
from importer.model_json import translate_shape_object
from importer.model_materials import inspect_model_materials, patch_model_materials
from importer.model_primitives import inspect_model_primitives, patch_model_primitives
from test_model_primitives import synthetic


def primitive_edit(index=0, object_index=0, **values):
    return dict(kind='primitive', object_index=object_index, primitive_index=index, values=values)


def group_edit(index=0, object_index=0, semi_transparent=False):
    return dict(kind='group', object_index=object_index, group_index=index,
                values={'semi_transparent': semi_transparent})


def texture_offset(flags):
    row, corners = (flags - 0x10) // 4, 4 if flags & 2 else 3
    return 0 if row < 2 else corners * 4 if row == 5 else 4


def seeded_material(data, clut=0x8123, tpage=0xbe61):
    result = bytearray(data)
    for obj in inspect_model_primitives(data)['objects']:
        for row in obj['primitives']:
            if row['uvs'] is not None:
                at = row['byte_offset'] + texture_offset(row['flags'])
                struct.pack_into('<H', result, at + 2, clut)
                struct.pack_into('<H', result, at + 6, tpage)
    return bytes(result)


def byte_diffs(before, after):
    return {i: (a, b) for i, (a, b) in enumerate(zip(before, after)) if a != b}


def audit_diffs(audit):
    result = {}
    for change in audit:
        if change['kind'] == 'primitive' and change['field'] == 'vertex_index':
            old, new = (struct.pack('<H', change[key] * 8) for key in ('before_value', 'after_value'))
        elif change['kind'] == 'primitive' and change['field'] in ('clut', 'tpage'):
            old, new = (struct.pack('<H', change[key]) for key in ('before_value', 'after_value'))
        elif change['kind'] in ('primitive', 'primitive_group'):
            old, new = (bytes([change[key]]) for key in ('before_value', 'after_value'))
        else:
            old, new = (struct.pack('<h', change[key]) for key in ('before_value', 'after_value'))
        for delta, (a, b) in enumerate(zip(old, new)):
            if a != b:
                at = change['byte_offset'] + delta
                if at in result:
                    raise AssertionError('Overlapping audit fields')
                result[at] = a, b
    return result


class ModelMaterialTests(unittest.TestCase):
    def test_all_24_layouts_exact_masks_shared_header_and_catalog(self):
        for flags in range(0x10, 0x28):
            with self.subTest(flags=hex(flags)):
                source = seeded_material(synthetic(((flags, flags),)))
                catalog = inspect_model_materials(source)
                self.assertEqual(set(catalog), {'schema_version', 'source_sha256', 'objects'})
                self.assertEqual(catalog['schema_version'], 'legaia.model-materials.v1')
                self.assertEqual(catalog['source_sha256'], sha256(source).hexdigest())
                obj = catalog['objects'][0]
                self.assertEqual(set(obj), {'object_index', 'groups'})
                self.assertEqual([g['group_index'] for g in obj['groups']], [0, 1])
                group = obj['groups'][1]
                self.assertEqual(set(group), {'group_index', 'byte_offset', 'flags', 'mode', 'semi_transparent', 'primitives'})
                self.assertEqual(group['flags'], flags)
                self.assertEqual(group['mode'], 0x27)
                self.assertTrue(group['semi_transparent'])
                self.assertEqual([r['primitive_index'] for r in group['primitives']], [2, 3])
                row = group['primitives'][0]
                self.assertEqual(set(row), {'primitive_index', 'byte_offset', 'textured', 'clut', 'tpage',
                    'page_column', 'page_row', 'texture_bpp', 'clut_column', 'clut_row', 'source_blend_mode'})
                self.assertEqual(row['byte_offset'], group['byte_offset'] + 8)
                expected = bytearray(source)
                expected[group['byte_offset'] + 7] = 0x25
                edits = [group_edit(1)]
                family = (flags - 0x10) // 4
                if family in (0, 1, 4, 5):
                    self.assertTrue(row['textured'])
                    self.assertEqual((row['clut'], row['tpage'], row['source_blend_mode']), (0x8123, 0xbe61, 3))
                    self.assertEqual((row['page_column'], row['page_row'], row['texture_bpp']), (1, 0, 4))
                    self.assertEqual((row['clut_column'], row['clut_row']), (35, 4))
                    edits.append(primitive_edit(2, page_column=15, page_row=1, texture_bpp=8,
                                                clut_column=63, clut_row=511))
                    at = row['byte_offset'] + texture_offset(flags)
                    struct.pack_into('<H', expected, at + 2, 0xffff)
                    struct.pack_into('<H', expected, at + 6, (0xbe61 & 0xfe60) | 0x9f)
                else:
                    self.assertFalse(row['textured'])
                    self.assertTrue(all(row[k] is None for k in row if k not in ('primitive_index', 'byte_offset', 'textured')))
                candidate, audit = patch_model_materials(source, catalog['source_sha256'], edits)
                self.assertEqual(candidate, bytes(expected))
                self.assertEqual(byte_diffs(source, candidate), audit_diffs(audit))
                shared = [a for a in audit if a['kind'] == 'primitive_group']
                self.assertEqual(shared, [dict(kind='primitive_group', object_index=0, group_index=1,
                    field='gpu_mode', byte_offset=group['byte_offset'] + 7, before_value=0x27,
                    after_value=0x25, primitive_indices=[2, 3])])
                for change in audit:
                    if change['kind'] == 'primitive':
                        self.assertEqual(set(change), {'kind', 'object_index', 'primitive_index', 'group_index',
                            'field', 'byte_offset', 'before_value', 'after_value'})
                        self.assertEqual(change['group_index'], 1)
                        self.assertEqual(change['primitive_index'], 2)
                        mask = 0x7fff if change['field'] == 'clut' else 0x019f
                        self.assertEqual((change['before_value'] ^ change['after_value']) & (0xffff ^ mask), 0)
                parsed = inspect_model_primitives(candidate)['objects'][0]['primitives']
                self.assertTrue(all(p['material']['semi_transparent'] == (p['group_index'] == 0) for p in parsed))
                self.assertEqual(patch_model_materials(candidate, sha256(candidate).hexdigest(), edits), (candidate, []))
                self.assertEqual(replace_model_content(source, catalog['source_sha256'], candidate), (candidate, audit))

    def test_noop_metadata_detached_and_source_order_unchanged(self):
        source = seeded_material(synthetic(((0x22, 0x1a), (0x27,))))
        catalog = inspect_model_materials(source)
        edits = []
        for obj in catalog['objects']:
            for group in obj['groups']:
                edits.append(group_edit(group['group_index'], obj['object_index'], group['semi_transparent']))
                for row in group['primitives']:
                    if row['textured']:
                        edits.append(primitive_edit(row['primitive_index'], obj['object_index'],
                            **{k: row[k] for k in ('page_column', 'page_row', 'texture_bpp', 'clut_column', 'clut_row')}))
        self.assertEqual(patch_model_materials(source, catalog['source_sha256'], edits[::-1]), (source, []))
        self.assertEqual(replace_model_content(source, catalog['source_sha256'], source, allow_materials=False), (source, []))
        catalog['objects'][0]['groups'][0]['primitives'][0]['clut'] = 0
        catalog['objects'][0]['groups'][0]['mode'] = 0
        self.assertEqual(inspect_model_materials(source)['objects'][0]['groups'][0]['mode'], 0x27)
        self.assertEqual(inspect_model_materials(source)['objects'][0]['groups'][0]['primitives'][0]['clut'], 0x8123)

    def test_target_depth_clut_gates_repair_and_reserved_inheritance(self):
        source = seeded_material(synthetic(), tpage=0xfe00 | 0x60 | 0x100 | 1)
        digest = sha256(source).hexdigest()
        row = inspect_model_materials(source)['objects'][0]['groups'][0]['primitives'][0]
        self.assertEqual(row['texture_bpp'], 16)
        with self.assertRaisesRegex(ImportError, 'indexed'):
            patch_model_materials(source, digest, [primitive_edit(clut_column=row['clut_column'])])
        indexed, changes = patch_model_materials(source, digest, [primitive_edit(texture_bpp=8, clut_column=9)])
        self.assertEqual([c['field'] for c in changes], ['clut', 'tpage'])
        result = inspect_model_materials(indexed)['objects'][0]['groups'][0]['primitives'][0]
        self.assertEqual((result['texture_bpp'], result['clut_column']), (8, 9))
        direct, changes = patch_model_materials(indexed, sha256(indexed).hexdigest(), [primitive_edit(texture_bpp=16)])
        self.assertEqual([c['field'] for c in changes], ['tpage'])
        self.assertEqual(inspect_model_materials(direct)['objects'][0]['groups'][0]['primitives'][0]['clut'], result['clut'])
        reserved = seeded_material(synthetic(), tpage=0xfe00 | 0x60 | 0x180 | 1)
        digest = sha256(reserved).hexdigest()
        row = inspect_model_materials(reserved)['objects'][0]['groups'][0]['primitives'][0]
        self.assertIsNone(row['texture_bpp'])
        self.assertEqual(patch_model_materials(reserved, digest, [primitive_edit(page_column=1)]), (reserved, []))
        self.assertEqual(replace_model_content(reserved, digest, reserved), (reserved, []))
        with self.assertRaisesRegex(ImportError, 'Reserved'):
            patch_model_materials(reserved, digest, [primitive_edit(page_column=2)])
        with self.assertRaisesRegex(ImportError, 'indexed'):
            patch_model_materials(reserved, digest, [primitive_edit(clut_column=row['clut_column'])])
        repaired, changes = patch_model_materials(reserved, digest, [primitive_edit(texture_bpp=4, clut_row=7)])
        self.assertEqual([c['field'] for c in changes], ['clut', 'tpage'])
        self.assertEqual(inspect_model_materials(repaired)['objects'][0]['groups'][0]['primitives'][0]['texture_bpp'], 4)
        group, changes = patch_model_materials(reserved, digest, [group_edit()])
        self.assertEqual(len(changes), 1)
        self.assertEqual(changes[0]['kind'], 'primitive_group')
        self.assertEqual(inspect_model_materials(group)['objects'][0]['groups'][0]['primitives'][0]['tpage'], row['tpage'])

    def test_strict_edit_shapes_duplicates_bounds_and_stale_source(self):
        source = synthetic(((0x22, 0x1a),))
        digest = sha256(source).hexdigest()
        item = primitive_edit(page_column=3)
        invalid = [None, {}, [None], [item, item], [item] * 257,
            [primitive_edit()], [group_edit(semi_transparent=1)],
            [{**item, 'object_index': True}], [{**item, 'primitive_index': 0.0}],
            [{**item, 'byte_offset': 48}], [{**item, 'kind': 'raw'}],
            [primitive_edit(99, page_column=3)], [primitive_edit(2, page_column=3)],
            [group_edit(99)], [group_edit(-1)],
            [primitive_edit(page_column=-1)], [primitive_edit(page_column=16)],
            [primitive_edit(page_row=2)], [primitive_edit(clut_column=64)], [primitive_edit(clut_row=512)],
            [primitive_edit(texture_bpp=3)], [primitive_edit(texture_bpp=24)],
            [primitive_edit(page_column=True)], [primitive_edit(clut_row=1.0)],
            [primitive_edit(source_blend_mode=1)], [primitive_edit(tpage=7)], [primitive_edit(clut=7)],
            [dict(kind='group', object_index=0, group_index=0, values={'semi_transparent': False, 'mode': 0})]]
        for edits in invalid:
            with self.subTest(edits=str(edits)[:100]), self.assertRaises(ImportError):
                patch_model_materials(source, digest, edits)
        for stale in (None, True, '0' * 64, digest.upper()):
            with self.assertRaises(ImportError):
                patch_model_materials(source, stale, [])

    def test_protected_bits_layout_aliases_terminators_and_strict_v1(self):
        source = seeded_material(synthetic(((0x13, 0x27),)))
        digest = sha256(source).hexdigest()
        catalog = inspect_model_materials(source)
        group = catalog['objects'][0]['groups'][0]
        row = group['primitives'][0]
        at = row['byte_offset']
        vert, _, normal, _, prim = struct.unpack_from('<5I', source, 12)
        # Forbidden bits are tested independently of the serializer's masks.
        mutations = [(0, 1), (4, 1), (12, 1), (36, 1), (prim + 12 + 2, 1),
            (prim + 12 + 5, 1), (group['byte_offset'] + 7, 1), (group['byte_offset'] + 7, 4),
            (at + 3, 128), (at + 6, 32), (at + 6, 64), (at + 7, 2),
            (at + 20, 1), (at + 22, 1), (at + 2 * 24, 1),
            (catalog['objects'][0]['groups'][1]['primitives'][0]['byte_offset'] + 3, 1),
            (12 + vert + 6, 1), (12 + normal + 6, 1), (12 + vert - 8, 1)]
        for offset, mask in mutations:
            candidate = bytearray(source); candidate[offset] ^= mask
            with self.subTest(offset=offset, mask=mask), self.assertRaises(ImportError):
                replace_model_content(source, digest, bytes(candidate))
        for edits in ([primitive_edit(page_column=2)], [primitive_edit(clut_column=2)], [group_edit()]):
            candidate, audit = patch_model_materials(source, digest, edits)
            self.assertTrue(audit)
            with self.assertRaises(ImportError): replace_model_content(source, digest, candidate, allow_materials=False)
            with self.assertRaises(ImportError): replace_model_shape(source, digest, candidate)
        aliased = bytearray(synthetic(((0x22,), (0x22,)))); aliased[40:68] = aliased[12:40]
        count = bytearray(source); struct.pack_into('<I', count, 32, 99)
        no_terminator = bytearray(synthetic())
        end = 40 + 8 + 3 * 24
        del no_terminator[end:end + 8]
        struct.pack_into('<I', no_terminator, 12, struct.unpack_from('<I', no_terminator, 12)[0] - 8)
        struct.pack_into('<I', no_terminator, 20, struct.unpack_from('<I', no_terminator, 20)[0] - 8)
        self.assertTrue(decode_tmd(bytes(no_terminator)))
        for bad in (None, bytearray(source), source[:-1], bytes(aliased), bytes(count), bytes(no_terminator)):
            with self.subTest(source_type=type(bad).__name__), self.assertRaises(ImportError): inspect_model_materials(bad)
        with self.assertRaises(ImportError): replace_model_content(source, digest, source, allow_materials=1)

    def test_material_face_and_vector_composition_preserves_each_layer(self):
        source = seeded_material(synthetic(((0x27,),)))
        digest = sha256(source).hexdigest()
        effective, _ = patch_model_materials(source, digest,
            [primitive_edit(page_column=3, clut_column=4), group_edit()])
        material_catalog = inspect_model_materials(effective)['objects']
        faces, _ = patch_model_primitives(effective, sha256(effective).hexdigest(),
            [dict(object_index=0, primitive_index=0, vertices=[4, 3, 2, 1],
                  uvs=[[1, 2], [3, 4], [5, 6], [7, 8]], colors=[[90, 100, 110]] * 4)])
        candidate = translate_shape_object(source, faces, sha256(faces).hexdigest(), 0, [3, 4, 5])
        self.assertEqual(inspect_model_materials(candidate)['objects'], material_catalog)
        self.assertEqual(inspect_model_primitives(candidate)['objects'], inspect_model_primitives(faces)['objects'])
        _, audit = replace_model_content(source, digest, candidate)
        self.assertEqual({a['kind'] for a in audit}, {'vertex', 'primitive', 'primitive_group'})
        self.assertEqual({a.get('field') for a in audit if a['kind'] == 'primitive'}, {'vertex_index', 'uv', 'color', 'clut', 'tpage'})
        self.assertEqual(audit_diffs(audit), byte_diffs(source, candidate))
        self.assertEqual(replace_model_content(effective, sha256(effective).hexdigest(), candidate,
                                             allow_materials=False)[0], candidate)
        # Author material fields after existing face/vector edits as well.
        without_materials = translate_shape_object(source, source, digest, 0, [3, 4, 5])
        without_materials, _ = patch_model_primitives(without_materials, sha256(without_materials).hexdigest(),
            [dict(object_index=0, primitive_index=0, vertices=[4, 3, 2, 1],
                  uvs=[[1, 2], [3, 4], [5, 6], [7, 8]], colors=[[90, 100, 110]] * 4)])
        reverse, _ = patch_model_materials(without_materials, sha256(without_materials).hexdigest(),
            [primitive_edit(page_column=3, clut_column=4), group_edit()])
        self.assertEqual(reverse, candidate)

    def test_v2_split_merge_reorders_materials_without_stale_textures_or_pose_changes(self):
        source = synthetic(((0x22,), (0x13,)))
        candidate, _ = patch_model_materials(source, sha256(source).hexdigest(), [primitive_edit(clut_column=9)])
        decoded = decode_tmd(source)
        self.assertEqual(len(decoded['materials']), 1)
        preview = deepcopy(decoded); obj = preview['objects'][0]
        nv, nt = obj['vertex_count'], obj['triangle_count']
        preview['objects'] = preview['objects'][:1]; preview['vertices'] = preview['vertices'][:nv]
        for key in ('triangles', 'triangle_colors', 'triangle_uvs', 'triangle_materials'): preview[key] = preview[key][:nt]
        transforms = [dict(object_index=0, translation=[3, 4, 5], rotation_psx=[0, 0, 1024])]
        other = [dict(object_index=0, translation=[20, 30, 40], rotation_psx=[0, 0, 0])]
        raw_vertices = deepcopy(preview['vertices'])
        preview.update(posed=True, pose={'object_transforms': transforms}, source_record={'immutable': True},
            frames=[dict(object_transforms=t, vertices=pose_vertices(raw_vertices, preview['objects'], t),
                         source_marker=i) for i, t in enumerate((transforms, other))],
            textures=[{'material_index': 0, 'private': 'old-crop'}],
            texture_catalog={'source_key': 'old'}, texture_scope='old')
        preview['vertices'] = pose_vertices(raw_vertices, preview['objects'], transforms)
        preview['materials'][0]['blend'] = {'old-binding': True}
        baseline = deepcopy(preview)
        result = preview_model_shape(preview, candidate, {'format': 'tmd-content-v2'})
        fresh = decode_tmd(candidate)
        self.assertEqual(len(result['materials']), 2)
        self.assertEqual(result['materials'], fresh['materials'])
        self.assertEqual(result['triangle_materials'], fresh['triangle_materials'][:nt])
        self.assertEqual(result['vertices'], baseline['vertices'])
        self.assertEqual([f['vertices'] for f in result['frames']], [f['vertices'] for f in baseline['frames']])
        self.assertEqual(result['objects'], baseline['objects'])
        self.assertEqual(result['source_record'], baseline['source_record'])
        self.assertEqual(result['pose'], baseline['pose'])
        self.assertEqual(result['textures'], [])
        self.assertNotIn('texture_catalog', result); self.assertNotIn('texture_scope', result)
        self.assertEqual(preview, baseline)
        with self.assertRaises(ImportError): preview_model_shape(preview, candidate, {'format': 'tmd-content-v1'})
        merged = preview_model_shape(result, source, {'format': 'tmd-content-v2'})
        self.assertEqual(merged['materials'], decoded['materials'])
        self.assertEqual(merged['triangle_materials'], decoded['triangle_materials'][:nt])
        self.assertEqual(merged['vertices'], baseline['vertices'])
        # Two source rows with different bindings can swap table order safely.
        different, _ = patch_model_materials(source, sha256(source).hexdigest(), [primitive_edit(1, clut_column=9)])
        reordered, _ = patch_model_materials(different, sha256(different).hexdigest(),
            [primitive_edit(0, clut_column=9), primitive_edit(1, clut_column=35)])
        current = decode_tmd(different); current['textures'] = [{'material_index': 0}, {'material_index': 1}]
        changed = preview_model_shape(current, reordered, {'format': 'tmd-content-v2'})
        self.assertEqual(changed['materials'], decode_tmd(reordered)['materials'])
        self.assertNotEqual(changed['materials'], current['materials'])
        self.assertEqual(changed['textures'], [])

    def test_raw_overlay_material_scope_exact_payload_and_noop(self):
        source = synthetic()
        candidate, audit = patch_model_materials(source, sha256(source).hexdigest(),
            [primitive_edit(page_column=3), group_edit()])
        body = b'PREFIX' + source + b'NEIGHBOR'
        archive = SimpleNamespace(node=SimpleNamespace(extent_lba=50),
            entry=lambda index: SimpleNamespace(start_lba=3), read_entry=lambda entry: body)
        assets = {'model': {'source_record': {'record_kind': 'raw_prot_entry', 'prot_entry_index': 0,
            'byte_offset': 6, 'byte_length': len(source), 'containing_size': len(body)}}}
        overlays, changes = model_shape_overlays(archive, assets, {'model': candidate})
        self.assertEqual(len(overlays), 1)
        self.assertEqual(overlays[0]['payload'], candidate)
        self.assertEqual(overlays[0]['offset'], 53 * 2048 + 6)
        self.assertEqual(overlays[0]['size'], len(source))
        self.assertEqual(changes[0]['scope'], 'TMD-existing-layout-material-content')
        self.assertEqual(changes[0]['coordinate_changes'], audit)
        self.assertEqual(model_shape_overlays(archive, assets, {'model': source}), ([], []))


@unittest.skipUnless(os.environ.get('LEGAIA_DISC_BIN'), 'requires private retail disc')
class RetailModelMaterialTests(unittest.TestCase):
    def test_town01_compressed_member_masks_and_exact_independent_readback(self):
        from importer.pipeline import _disc_context, import_scene
        from importer.assets import load_model_source
        from importer.core import decompress_lzs
        disc = os.environ['LEGAIA_DISC_BIN']
        with _disc_context(disc) as (_, _, _, archive):
            asset = import_scene(disc, 'town01')['assets']['models'][0]
            source = load_model_source(disc, asset)
            catalog = inspect_model_materials(source); group = catalog['objects'][0]['groups'][0]
            row = group['primitives'][0]
            self.assertTrue(row['textured'])
            candidate, audit = patch_model_materials(source, catalog['source_sha256'],
                [primitive_edit(row['primitive_index'], clut_column=(row['clut_column'] + 1) % 64),
                 group_edit(group['group_index'], semi_transparent=not group['semi_transparent'])])
            self.assertEqual(audit_diffs(audit), byte_diffs(source, candidate))
            self.assertEqual([a['field'] for a in audit], ['gpu_mode', 'clut'])
            overlays, changes = model_shape_overlays(archive, {asset['semantic_id']: asset}, {asset['semantic_id']: candidate})
            self.assertEqual(changes[0]['scope'], 'TMD-existing-layout-material-content')
            self.assertEqual(changes[0]['coordinate_changes'], audit)
            self.assertEqual(len(overlays), 1)
            overlay = overlays[0]
            self.assertLessEqual(overlay['new_encoded_size'], overlay['original_encoded_size'])
            decoded, _ = decompress_lzs(overlay['payload'], overlay['decoded_size'])
            start = asset['source_record']['byte_offset']
            self.assertEqual(decoded[start:start + len(candidate)], candidate)
            self.assertEqual(sha256(decoded).hexdigest(), overlay['decoded_after_sha256'])


if __name__ == '__main__':
    unittest.main()
