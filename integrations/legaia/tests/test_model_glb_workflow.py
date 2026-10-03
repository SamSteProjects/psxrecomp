"""Model GLB service freshness, composition and ordinary replacement history.

Synthetic service tests mock only the pure GLB boundary and verified disc read;
the optional retail case uses the real codec and normal Build container writer.
"""
from contextlib import nullcontext
from copy import deepcopy
from hashlib import sha256
import json
import os
from pathlib import Path
import struct
import sys
import tempfile
from types import ModuleType, SimpleNamespace
import unittest
from unittest.mock import patch
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from importer.assets import decode_tmd
from importer.core import ImportError as RetailImportError
from importer.model_primitives import inspect_model_primitives, patch_model_primitives
from sdk import model_glb
from sdk.project import ProjectError, ProjectService
from sdk.scene_preview import source_key
from test_importer_assets import model
from test_project_workflow import synthetic_scene


ROOT = Path(__file__).resolve().parents[3]
ASSET = 'asset://fixture/model/0'
SCENE = 'scene://fixture'
ZERO_QUANTIZATION = dict(vertex_max_error=0, uv_max_error=0, color_max_error=0, normal_max_error=0,
                         quantized_component_count=0)


def vertex_edit(source, value=7):
    result = bytearray(source)
    at = 12 + struct.unpack_from('<I', source, 12)[0]
    struct.pack_into('<h', result, at, value)
    return bytes(result)


def packet_edit(source):
    row = inspect_model_primitives(source)['objects'][0]['primitives'][0]
    vertices, uvs, colors = (deepcopy(row[k]) for k in ('vertices', 'uvs', 'colors'))
    vertices[0], vertices[1] = vertices[1], vertices[0]
    uvs[0][0] += 1
    colors[0][0] += 1
    return patch_model_primitives(source, sha256(source).hexdigest(), [
        dict(object_index=0, primitive_index=0, vertices=vertices, uvs=uvs, colors=colors)])[0]


def uv_edit(source):
    row = inspect_model_primitives(source)['objects'][0]['primitives'][0]
    uvs = deepcopy(row['uvs'])
    uvs[0][0] += 1
    return patch_model_primitives(source, sha256(source).hexdigest(), [
        dict(object_index=0, primitive_index=0, uvs=uvs)])[0]


def color_edit(source):
    row = inspect_model_primitives(source)['objects'][0]['primitives'][0]
    colors = deepcopy(row['colors'])
    colors[0][0] += 1
    return patch_model_primitives(source, sha256(source).hexdigest(), [
        dict(object_index=0, primitive_index=0, colors=colors)])[0]


def reference_edit(source):
    row = inspect_model_primitives(source)['objects'][0]['primitives'][0]
    vertices = deepcopy(row['vertices'])
    vertices[0] = vertices[1]
    return patch_model_primitives(source, sha256(source).hexdigest(), [
        dict(object_index=0, primitive_index=0, vertices=vertices)])[0]


def move_exported_source_vertex(content, object_index=0, vertex_index=0, dx=1.0):
    """Edit every displayed copy of one source vertex in the actual GLB.

    This independent test helper reads only standard GLB/accessor structure and
    the source ordinal attribute, rather than importing or patching TMD bytes.
    """
    magic, version, total = struct.unpack_from('<III', content)
    if (magic, version, total) != (0x46546C67, 2, len(content)):
        raise AssertionError('Not an SDK GLB')
    json_length, json_kind = struct.unpack_from('<II', content, 12)
    if json_kind != 0x4E4F534A:
        raise AssertionError('Missing GLB JSON')
    document = json.loads(content[20:20 + json_length])
    bin_header = 20 + json_length
    bin_length, bin_kind = struct.unpack_from('<II', content, bin_header)
    if bin_kind != 0x004E4942 or bin_header + 8 + bin_length != len(content):
        raise AssertionError('Missing embedded GLB buffer')
    start = bin_header + 8
    result = bytearray(content)
    node = next(n for n in document['nodes'] if n.get('name') == f'object-{object_index}')
    mesh = document['meshes'][node['mesh']]
    changed = set()
    def accessor_offsets(index, shape):
        accessor = document['accessors'][index]
        if accessor['componentType'] != 5126 or accessor['type'] != shape or accessor.get('sparse'):
            raise AssertionError('Source authoring requires nonsparse FLOAT attributes')
        view = document['bufferViews'][accessor['bufferView']]
        width = {'SCALAR': 4, 'VEC3': 12}[shape]
        stride = view.get('byteStride', width)
        offset = start + view.get('byteOffset', 0) + accessor.get('byteOffset', 0)
        return [offset + i * stride for i in range(accessor['count'])]
    for primitive in mesh['primitives']:
        attributes = primitive['attributes']
        if '_LEGAIA_SOURCE_VERTEX' not in attributes:
            continue
        ordinals = accessor_offsets(attributes['_LEGAIA_SOURCE_VERTEX'], 'SCALAR')
        positions = accessor_offsets(attributes['POSITION'], 'VEC3')
        if len(ordinals) != len(positions):
            raise AssertionError('Source ordinal count differs')
        for at, position in zip(ordinals, positions):
            if struct.unpack_from('<f', content, at)[0] == vertex_index and position not in changed:
                before = struct.unpack_from('<f', content, position)[0]
                struct.pack_into('<f', result, position, before + dx)
                changed.add(position)
    if not changed:
        raise AssertionError('Export omitted the expected source vertex')
    return bytes(result)


def move_exported_source_rgb(content, primitive_index=0, slot=0, gouraud=False, delta=1):
    """Edit raw RGB by independently reading source corner and RGB accessors."""
    json_length = struct.unpack_from('<I', content, 12)[0]
    document = json.loads(content[20:20 + json_length])
    binary_start = 28 + json_length
    result = bytearray(content)
    node = next(row for row in document['nodes'] if row.get('name') == 'object-0')
    changed = set()

    def offsets(index, shape, width):
        accessor = document['accessors'][index]
        if accessor['componentType'] != 5126 or accessor['type'] != shape or accessor.get('sparse'):
            raise AssertionError('Expected nonsparse FLOAT SDK attributes')
        view = document['bufferViews'][accessor['bufferView']]
        start = binary_start + view.get('byteOffset', 0) + accessor.get('byteOffset', 0)
        return [start + i * view.get('byteStride', width) for i in range(accessor['count'])]

    for primitive in document['meshes'][node['mesh']]['primitives']:
        attrs = primitive['attributes']
        identities = offsets(attrs['_LEGAIA_SOURCE_CORNER'], 'SCALAR', 4)
        colors = offsets(attrs['_LEGAIA_SOURCE_RGB'], 'VEC3', 12)
        if len(identities) != len(colors):
            raise AssertionError('Source corner/RGB counts differ')
        for identity_at, color_at in zip(identities, colors):
            corner_id = struct.unpack_from('<f', content, identity_at)[0]
            if int(corner_id) // 4 == primitive_index and (not gouraud or int(corner_id) % 4 == slot) and color_at not in changed:
                value = struct.unpack_from('<f', content, color_at)[0]
                if value < 0:
                    raise AssertionError('Target has no stored RGB')
                struct.pack_into('<f', result, color_at, value + delta)
                changed.add(color_at)
    if not changed:
        raise AssertionError('Export omitted the expected RGB slot')
    return bytes(result)


def rewire_exported_source_corner(content, target_vertex, corner_id=0):
    """Change a fixed corner's vertex ID and POSITION to an existing GLB alias."""
    json_length = struct.unpack_from('<I', content, 12)[0]
    document = json.loads(content[20:20 + json_length])
    binary_start = 28 + json_length
    result = bytearray(content)
    node = next(row for row in document['nodes'] if row.get('name') == 'object-0')
    aliases = []

    def offsets(index, shape, width):
        accessor = document['accessors'][index]
        if accessor['componentType'] != 5126 or accessor['type'] != shape or accessor.get('sparse'):
            raise AssertionError('Expected nonsparse FLOAT SDK source attributes')
        view = document['bufferViews'][accessor['bufferView']]
        start = binary_start + view.get('byteOffset', 0) + accessor.get('byteOffset', 0)
        return [start + i * view.get('byteStride', width) for i in range(accessor['count'])]

    for primitive in document['meshes'][node['mesh']]['primitives']:
        attrs = primitive['attributes']
        ids = offsets(attrs['_LEGAIA_SOURCE_VERTEX'], 'SCALAR', 4)
        corners = offsets(attrs['_LEGAIA_SOURCE_CORNER'], 'SCALAR', 4)
        positions = offsets(attrs['POSITION'], 'VEC3', 12)
        if not len(ids) == len(corners) == len(positions):
            raise AssertionError('Source attribute counts differ')
        aliases.extend(zip(ids, corners, positions))
    position = next((content[at:at + 12] for identity_at, _, at in aliases
                     if struct.unpack_from('<f', content, identity_at)[0] == target_vertex), None)
    if position is None:
        raise AssertionError('Target vertex has no displayed alias')
    changed = set()
    for identity_at, owner_at, at in aliases:
        if struct.unpack_from('<f', content, owner_at)[0] == corner_id:
            struct.pack_into('<f', result, identity_at, target_vertex)
            result[at:at + 12] = position
            changed.add(at)
    if not changed:
        raise AssertionError('Source corner is absent')
    return bytes(result)


class ModelGLBServiceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='model-glb-service-')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        data = bytearray(model(0x23))
        normal = len(data)
        struct.pack_into('<II', data, 20, normal - 12, 1)
        data.extend(struct.pack('<hhhh', 0, 4096, 0, 123))
        self.source = bytes(data)
        disc = self.root / 'fixture.bin'
        disc.write_bytes(b'synthetic source identity; disc decoder is mocked')
        self.project = ProjectService(self.root)
        self.project.import_metadata(synthetic_scene(), str(disc))
        self.project.save()
        self.imported = deepcopy(self.project.imports)
        self.exports = []
        self.analysis = dict(quantization=deepcopy(ZERO_QUANTIZATION))
        leaf = ModuleType('importer.model_glb')
        leaf.export_model_glb = self.export_boundary
        leaf.import_model_glb = self.import_boundary
        def source_lookup(project, asset, scene):
            document = project.imports.get(scene)
            if not document or not any(a['semantic_id'] == asset for a in document['assets']['models']):
                raise ProjectError('Unknown imported source model')
            return self.source
        patches = [patch.dict(sys.modules, {'importer.model_glb': leaf}),
                   patch.object(ProjectService, '_model_source', source_lookup),
                   patch('importer.pipeline._disc_context', side_effect=lambda _disc: nullcontext()),
                   patch('importer.assets.load_model_preview', side_effect=lambda _disc, _asset: decode_tmd(self.source))]
        for item in patches:
            item.start()
            self.addCleanup(item.stop)

    def export_boundary(self, effective, preview):
        self.exports.append(deepcopy(preview))
        return b'qualified-glb-boundary-mock', dict(schema_version='legaia.model-glb-profile.v5',
                                                   effective_sha256=sha256(effective).hexdigest())

    def import_boundary(self, effective, content, profile):
        self.assertEqual(profile['effective_sha256'], sha256(effective).hexdigest())
        if content == b'edit-vertex':
            candidate = vertex_edit(effective)
        elif content == b'edit-uv':
            candidate = uv_edit(effective)
        elif content == b'edit-color':
            candidate = color_edit(effective)
        elif content == b'edit-reference':
            candidate = reference_edit(effective)
        elif content == b'edit-packet':
            candidate = packet_edit(effective)
        elif content == b'retail':
            candidate = self.source
        elif content == b'edit-normal':
            candidate = bytearray(effective)
            struct.pack_into('<h', candidate, len(candidate) - 8, 10)
            candidate = bytes(candidate)
        elif content == b'edit-opaque':
            candidate = bytearray(effective)
            candidate[0] ^= 1
            candidate = bytes(candidate)
        else:
            candidate = effective
        return candidate, deepcopy(self.analysis)

    def state(self):
        return deepcopy((self.project.imports, self.project.overrides, self.project.model_overrides,
                         self.project.undo_stack, self.project.redo_stack, self.project.active_scene)), {
            str(p.relative_to(self.root)): p.read_bytes()
            for p in self.root.rglob('*') if p.is_file()}

    def effective(self, project=None):
        project = project or self.project
        binding = project.model_overrides.get(ASSET)
        return project.read_model_replacement(ASSET, binding) if binding else self.source

    def test_noop_export_preview_are_read_only_and_detached(self):
        before = self.state()
        content, binding, report = model_glb.export_model(self.project, ASSET)
        self.assertEqual(set(binding), model_glb.BINDING_KEYS)
        self.assertEqual(binding['source_sha256'], sha256(self.source).hexdigest())
        self.assertEqual(binding['project_source_key'], source_key(self.project))
        self.assertEqual(report['schema_version'], 'legaia.model-glb-review.v1')
        self.assertEqual(report['changes'], [])
        self.assertEqual(report['pending_changes'], [])
        self.assertEqual(report['quantization'], ZERO_QUANTIZATION)
        self.assertEqual((report['object_count'], report['vertex_count'], report['primitive_count']), (1, 4, 1))
        self.assertFalse(self.exports[-1]['posed'])
        self.assertEqual(model_glb.preview_import(self.project, ASSET, content, binding), report)
        with self.assertRaisesRegex(ProjectError, 'no source-quantized'):
            model_glb.apply_import(self.project, ASSET, content, binding, report['review_key'])
        report['limitations'].append('mutable caller data')
        self.exports[-1]['vertices'][0][0] = 900
        self.assertNotIn('mutable caller data', model_glb.preview_import(self.project, ASSET, content, binding)['limitations'])
        self.assertEqual(self.state(), before)

    def test_composition_apply_once_history_save_and_reset(self):
        self.project.set_model_vector(ASSET, 0, 'vertices', 1, [13, 14, 15], sha256(self.source).hexdigest())
        current = self.effective()
        self.project.set_model_vector(ASSET, 0, 'normals', 0, [1, 4096, 0], sha256(current).hexdigest())
        self.project.set_model_replacement(ASSET, packet_edit(self.effective()))
        current = self.effective()
        _, binding, _ = model_glb.export_model(self.project, ASSET)
        before = self.state()
        candidate, report = model_glb.pose_import(self.project, ASSET, b'edit-uv', binding)
        self.assertEqual(self.state(), before)
        self.assertEqual({row['field'] for row in report['pending_changes']}, {'uv'})
        self.assertTrue(any(row.get('field') == 'color' for row in report['changes']))
        self.assertTrue(any(row.get('field') == 'vertex_index' for row in report['changes']))
        self.assertEqual(candidate[-8:], current[-8:])
        self.assertEqual(decode_tmd(candidate)['vertices'][1], [13, 14, 15])
        with patch.object(self.project, 'set_model_replacement', wraps=self.project.set_model_replacement) as writer:
            self.assertEqual(model_glb.apply_import(self.project, ASSET, b'edit-uv', binding, report['review_key']), report)
            writer.assert_called_once_with(ASSET, candidate)
        self.assertEqual(self.effective(), candidate)
        self.assertEqual(len(self.project.undo_stack), 4)
        self.assertEqual(self.project.model_overrides[ASSET]['format'], 'tmd-content-v1')
        self.project.undo()
        self.assertEqual(self.effective(), current)
        self.project.redo()
        self.assertEqual(self.effective(), candidate)
        restored = ProjectService.open(self.project.save())
        self.assertEqual(self.effective(restored), candidate)
        self.assertEqual(restored.imports, self.imported)
        _, new_binding, unchanged = model_glb.export_model(self.project, ASSET)
        self.assertTrue(unchanged['changes'])
        self.assertEqual(unchanged['pending_changes'], [])
        with self.assertRaises(ProjectError):
            model_glb.apply_import(self.project, ASSET, b'qualified-glb-boundary-mock', new_binding, unchanged['review_key'])
        # Fresh v4 exports explicitly expose existing stored normal words.
        normal_reset = model_glb.preview_import(self.project, ASSET, b'retail', new_binding)
        self.assertTrue(any(row['kind'] == 'normal' for row in normal_reset['pending_changes']))
        self.project.set_model_replacement(ASSET, vertex_edit(self.source))
        _, reset_binding, _ = model_glb.export_model(self.project, ASSET)
        reset = model_glb.preview_import(self.project, ASSET, b'retail', reset_binding)
        self.assertEqual(reset['changes'], [])
        self.assertTrue(reset['pending_changes'])
        model_glb.apply_import(self.project, ASSET, b'retail', reset_binding, reset['review_key'])
        self.assertNotIn(ASSET, self.project.model_overrides)
        self.assertEqual(self.project.imports, self.imported)

    def test_binding_source_mode_and_review_freshness_fail_without_mutation(self):
        _, binding, _ = model_glb.export_model(self.project, ASSET)
        report = model_glb.preview_import(self.project, ASSET, b'edit-vertex', binding)
        before = self.state()
        malformed = [{**binding, 'extra': True}, {**binding, 'asset_id': 'asset://foreign/model'},
                     {**binding, 'effective_sha256': '0' * 64},
                     {**binding, 'profile': {**binding['profile'], 'schema_version': 'legaia.model-glb-profile.v1'}},
                     {**binding, 'profile': {**binding['profile'], 'schema_version': 'legaia.model-glb-profile.v2'}},
                     {**binding, 'profile': {**binding['profile'], 'unexpected': 'payload'}}]
        for value in malformed:
            with self.subTest(binding=value), self.assertRaises(ProjectError):
                model_glb.preview_import(self.project, ASSET, b'edit-vertex', value)
            self.assertEqual(self.state(), before)
        for content, key in [(b'edit-vertex', '0' * 64), (b'edit-uv', report['review_key'])]:
            with self.assertRaisesRegex(ProjectError, 'after review'):
                model_glb.apply_import(self.project, ASSET, content, binding, key)
            self.assertEqual(self.state(), before)
        self.project.mode = 'live'
        with self.assertRaisesRegex(ProjectError, 'Edit mode'):
            model_glb.preview_import(self.project, ASSET, b'edit-vertex', binding)
        self.project.mode = 'edit'
        source = self.source
        self.source = vertex_edit(source, 42)
        with self.assertRaisesRegex(ProjectError, 'binding differs'):
            model_glb.preview_import(self.project, ASSET, b'edit-vertex', binding)
        self.source = source
        with patch('sdk.scene_preview.source_key', side_effect=[binding['project_source_key'], 'f' * 64]):
            with self.assertRaisesRegex(ProjectError, 'while verifying'):
                model_glb.preview_import(self.project, ASSET, b'edit-vertex', binding)
        self.assertEqual(self.state(), before)
        self.project.set_model_vector(ASSET, 0, 'vertices', 0, [3, 4, 5], sha256(source).hexdigest())
        changed = self.state()
        with self.assertRaisesRegex(ProjectError, 'binding differs'):
            model_glb.apply_import(self.project, ASSET, b'edit-vertex', binding, report['review_key'])
        self.assertEqual(self.state(), changed)

    def test_raw_rgb_review_apply_history_and_save_preserve_other_fields(self):
        self.project.set_model_vector(ASSET, 0, 'normals', 0, [1, 4096, 0], sha256(self.source).hexdigest())
        current = self.effective()
        _, binding, _ = model_glb.export_model(self.project, ASSET)
        before = self.state()
        self.analysis['quantization'] = dict(ZERO_QUANTIZATION, color_max_error=.25,
                                              quantized_component_count=1)
        candidate, report = model_glb.pose_import(self.project, ASSET, b'edit-color', binding)
        self.assertEqual(self.state(), before)
        self.assertEqual(report['quantization']['color_max_error'], .25)
        self.assertEqual([(row['kind'], row.get('field'), row.get('axis'))
                          for row in report['pending_changes']], [('primitive', 'color', 'r')])
        self.assertEqual(candidate, color_edit(current))
        self.assertEqual(candidate[-8:], current[-8:])
        self.assertEqual(sum(a != b for a, b in zip(current, candidate)), 1)
        model_glb.apply_import(self.project, ASSET, b'edit-color', binding, report['review_key'])
        self.assertEqual(len(self.project.undo_stack), 2)
        self.project.undo()
        self.assertEqual(self.effective(), current)
        self.project.redo()
        restored = ProjectService.open(self.project.save())
        self.assertEqual(self.effective(restored), candidate)
        self.assertEqual(restored.imports, self.imported)

    def test_reference_proposal_composes_read_only_and_uses_normal_history(self):
        current = color_edit(vertex_edit(self.source))
        self.project.set_model_replacement(ASSET, current)
        _, binding, _ = model_glb.export_model(self.project, ASSET)
        before = self.state()
        candidate, report = model_glb.pose_import(self.project, ASSET, b'edit-reference', binding)
        self.assertEqual(self.state(), before)
        self.assertEqual(candidate, reference_edit(current))
        self.assertEqual([(row['kind'], row.get('field')) for row in report['pending_changes']],
                         [('primitive', 'vertex_index')])
        self.assertTrue(any(row.get('field') == 'color' for row in report['changes']))
        self.assertEqual(decode_tmd(candidate)['vertices'], decode_tmd(current)['vertices'])
        model_glb.apply_import(self.project, ASSET, b'edit-reference', binding, report['review_key'])
        self.assertEqual(len(self.project.undo_stack), 2)
        self.project.undo()
        self.assertEqual(self.effective(), current)
        self.project.redo()
        restored = ProjectService.open(self.project.save())
        self.assertEqual(self.effective(restored), candidate)
        self.assertEqual(restored.imports, self.imported)

    def test_source_owned_bytes_quantization_and_report_budgets_reject(self):
        _, binding, _ = model_glb.export_model(self.project, ASSET)
        before = self.state()
        normal = model_glb.preview_import(self.project, ASSET, b'edit-normal', binding)
        self.assertTrue(any(row['kind'] == 'normal' for row in normal['pending_changes']))
        self.assertEqual(self.state(), before)
        for content in (b'edit-opaque',):
            with self.subTest(content=content), self.assertRaises((ProjectError, RetailImportError)):
                model_glb.preview_import(self.project, ASSET, content, binding)
            self.assertEqual(self.state(), before)
        for value in ({}, {**ZERO_QUANTIZATION, 'uv_max_error': float('nan')},
                      {**ZERO_QUANTIZATION, 'vertex_max_error': -1},
                      {**ZERO_QUANTIZATION, 'color_max_error': float('inf')},
                      {**ZERO_QUANTIZATION, 'color_max_error': -1},
                      {**ZERO_QUANTIZATION, 'normal_max_error': float('inf')},
                      {**ZERO_QUANTIZATION, 'quantized_component_count': True},
                      {**ZERO_QUANTIZATION, 'quantized_component_count': 65537}):
            self.analysis['quantization'] = value
            with self.subTest(value=value), self.assertRaises(ProjectError):
                model_glb.preview_import(self.project, ASSET, b'edit-vertex', binding)
        self.analysis['quantization'] = deepcopy(ZERO_QUANTIZATION)
        for constant in ('MAX_PROFILE_BYTES', 'MAX_AUDIT_ROWS', 'MAX_REVIEW_BYTES', 'MAX_GLB_BYTES'):
            with patch.object(model_glb, constant, 0), self.assertRaises(ProjectError):
                model_glb.preview_import(self.project, ASSET, b'edit-vertex', binding)
        self.assertEqual(self.state(), before)

    def test_texture_crops_follow_effective_uvs_without_mutating_source(self):
        asset = self.project.imports[SCENE]['assets']['models'][0]
        asset['source_record']['prot_entry_name'] = 'fixture'
        catalog = SimpleNamespace(scene='fixture', metadata=lambda: {})
        seen = []
        def associate(_catalog, _material, bounds):
            seen.append(bounds)
            return dict(status='resolved', bounds=list(bounds), rgba=bytes([255, 255, 255, 255]), stp=bytes([0]))
        current = packet_edit(self.source)
        self.project.set_model_replacement(ASSET, current)
        before = self.state()
        with patch('importer.textures.load_scene_texture_catalog', return_value=catalog), \
                patch('importer.textures.load_asset_texture_catalog', return_value=catalog), \
                patch('importer.textures.associate_material', side_effect=associate):
            model_glb.export_model(self.project, ASSET)
        row = inspect_model_primitives(current)['objects'][0]['primitives'][0]
        self.assertEqual(seen, [(min(p[0] for p in row['uvs']), min(p[1] for p in row['uvs']),
                                 max(p[0] for p in row['uvs']), max(p[1] for p in row['uvs']))])
        self.assertEqual(self.exports[-1]['triangle_uvs'], decode_tmd(current)['triangle_uvs'])
        self.assertEqual(self.exports[-1]['textures'][0]['rgba_base64'], '/////w==')
        self.assertEqual(self.state(), before)


@unittest.skipUnless(os.environ.get('LEGAIA_DISC_BIN'), 'requires private retail disc')
class ModelGLBRetailWorkflow(unittest.TestCase):
    def test_fresh_town01_glb_apply_save_build_and_independent_source_member_readback(self):
        from importer.core import decompress_lzs, parse_lzs_sections
        from importer.pipeline import _disc_context, import_scene
        from sdk.build import build_project

        disc = os.environ['LEGAIA_DISC_BIN']
        private = ROOT / 'local-output/sdk-20260909'
        private.mkdir(parents=True, exist_ok=True)
        with _disc_context(disc) as (_image, _disc_hash, _mapping, archive):
            document = import_scene(disc, 'town01')
            asset = next(a for a in document['assets']['models']
                         if a['semantic_id'].endswith('/scene-tmd/0000'))
            with tempfile.TemporaryDirectory(prefix='model-glb-build-', dir=private) as directory:
                project = ProjectService(Path(directory))
                project.import_metadata(document, disc)
                original = project._model_source(asset['semantic_id'], project.active_scene)
                imported = deepcopy(project.imports)
                glb, binding, noop = model_glb.export_model(project, asset['semantic_id'])
                self.assertEqual(noop['pending_changes'], [])
                self.assertEqual(noop['changes'], [])
                edited_glb = move_exported_source_vertex(glb)
                row = inspect_model_primitives(original)['objects'][0]['primitives'][0]
                self.assertIsNotNone(row['colors'])
                color_delta = .75 if row['colors'][0][0] < 255 else -.75
                edited_glb = move_exported_source_rgb(edited_glb, gouraud=row['gouraud'], delta=color_delta)
                self.assertEqual(row['flags'], 0x21)
                target_vertex = row['vertices'][2]
                self.assertNotEqual(row['vertices'][1], target_vertex)
                edited_glb = rewire_exported_source_corner(edited_glb, target_vertex, corner_id=1)
                candidate, review = model_glb.pose_import(project, asset['semantic_id'], edited_glb, binding)
                vertex_at = 12 + struct.unpack_from('<I', original, 12)[0]
                expected = bytearray(original)
                struct.pack_into('<h', expected, vertex_at,
                                 struct.unpack_from('<h', original, vertex_at)[0] + 1)
                expected[row['byte_offset']] += 1 if color_delta > 0 else -1
                reference_at = row['byte_offset'] + 16  # 0x21 refs begin at +14; corner 1 at +16.
                self.assertEqual(struct.unpack_from('<H', original, reference_at)[0], row['vertices'][1] * 8)
                struct.pack_into('<H', expected, reference_at, target_vertex * 8)
                self.assertEqual(candidate, bytes(expected))
                self.assertEqual(len(review['pending_changes']), 3)
                self.assertEqual({(entry['kind'], entry.get('field')) for entry in review['pending_changes']},
                                 {('vertex', None), ('primitive', 'color'), ('primitive', 'vertex_index')})
                self.assertAlmostEqual(review['quantization']['color_max_error'], .25)
                model_glb.apply_import(project, asset['semantic_id'], edited_glb, binding, review['review_key'])
                self.assertEqual(len(project.undo_stack), 1)
                project.undo()
                self.assertNotIn(asset['semantic_id'], project.model_overrides)
                project.redo()
                project.save()
                restored = ProjectService.open(project.root)
                self.assertEqual(restored.read_model_replacement(asset['semantic_id'],
                    restored.model_overrides[asset['semantic_id']]), candidate)
                result = build_project(restored)
                self.assertEqual(result['overlay_count'], 1)
                self.assertEqual(result['report']['validation']['live_runtime'], 'not_run')
                audit = json.loads(Path(result['audit']).read_text(encoding='utf-8'))
                locator = asset['source_record']
                entry = archive.entry(locator['prot_entry_index'])
                body = archive.read_entry(entry)
                sections = parse_lzs_sections(body)
                section = sections[locator['container_section']]
                end = (sections[locator['container_section'] + 1].stream_offset
                       if locator['container_section'] + 1 < len(sections) else len(body))
                baseline, consumed = decompress_lzs(body[section.stream_offset:end], section.decoded_size)
                offset = (archive.node.extent_lba + entry.start_lba) * 2048 + section.stream_offset
                overlay = next(row for row in audit['overlays'] if row['offset'] == offset)
                with zipfile.ZipFile(result['path']) as package:
                    payload = package.read(overlay['file'])
                decoded, read = decompress_lzs(payload, section.decoded_size)
                self.assertEqual(len(payload), consumed)
                self.assertLessEqual(read, consumed)
                begin, length = locator['byte_offset'], locator['byte_length']
                self.assertEqual(baseline[begin:begin + length], original)
                self.assertEqual(decoded[begin:begin + length], bytes(expected))
                self.assertEqual(decoded[:begin], baseline[:begin])
                self.assertEqual(decoded[begin + length:], baseline[begin + length:])
                self.assertEqual(project.imports, imported)
                self.assertEqual(project._model_source(asset['semantic_id'], project.active_scene), original)


if __name__ == '__main__':
    unittest.main()
