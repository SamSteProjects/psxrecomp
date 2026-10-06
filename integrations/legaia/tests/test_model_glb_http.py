"""Exact HTTP model interchange envelopes and an optional private retail roundtrip."""
import base64
from copy import deepcopy
from hashlib import sha256
from http.client import HTTPConnection
import json
import os
from pathlib import Path
import struct
import tempfile
import unittest
from unittest.mock import patch

from importer.assets import decode_tmd
from importer.model_primitives import inspect_model_primitives
from sdk.project import ProjectService
from test_model_glb_workflow import (move_exported_source_vertex, move_exported_source_rgb,
                                     rewire_exported_source_corner)
from test_model_primitive_workflow import http_server


ROOT = Path(__file__).resolve().parents[3]


def authored_snapshot(project):
    """Export files may change; source evidence, authoring and history may not."""
    return deepcopy((project._document(), project.imports, project.selected,
                     project.undo_stack, project.redo_stack)), {
        str(path.relative_to(project.root)): path.read_bytes()
        for path in project.root.rglob('*')
        if path.is_file() and not path.relative_to(project.root).parts[0] == 'Exports'
    }


def move_source_corner_uv(content, profile, corner_id=0, delta=1):
    """Change all copies of one source UV via independent FLOAT accessors.

    Source corner ordinals and the retained export crop define the conversion;
    the test never imports its expected TMD candidate through the GLB codec.
    """
    json_length, json_kind = struct.unpack_from('<II', content, 12)
    if json_kind != 0x4e4f534a:
        raise AssertionError('Missing GLB JSON')
    document = json.loads(content[20:20 + json_length])
    binary_start = 28 + json_length
    result = bytearray(content)
    node = next(row for row in document['nodes'] if row.get('name') == 'object-0')
    changed = set()

    def offsets(index, shape, width):
        accessor = document['accessors'][index]
        if accessor['componentType'] != 5126 or accessor['type'] != shape or accessor.get('sparse'):
            raise AssertionError('Expected nonsparse FLOAT SDK source attributes')
        view = document['bufferViews'][accessor['bufferView']]
        start = binary_start + view.get('byteOffset', 0) + accessor.get('byteOffset', 0)
        return [start + index * view.get('byteStride', width) for index in range(accessor['count'])]

    for primitive in document['meshes'][node['mesh']]['primitives']:
        attrs = primitive['attributes']
        if 'TEXCOORD_0' not in attrs:
            continue
        identities = offsets(attrs['_LEGAIA_SOURCE_CORNER'], 'SCALAR', 4)
        uvs = offsets(attrs['TEXCOORD_0'], 'VEC2', 8)
        if len(identities) != len(uvs):
            raise AssertionError('Source corner/UV counts differ')
        crop = next(row for row in profile['uv_crops']
                    if row['material_index'] == primitive['material'])
        for source_at, uv_at in zip(identities, uvs):
            if struct.unpack_from('<f', content, source_at)[0] == corner_id and uv_at not in changed:
                struct.pack_into('<f', result, uv_at,
                                 struct.unpack_from('<f', content, uv_at)[0] + delta / crop['width'])
                changed.add(uv_at)
    if not changed:
        raise AssertionError('Source corner was absent from the textured GLB')
    return bytes(result)


class ModelGlbHttpEnvelopeTests(unittest.TestCase):
    def test_malformed_envelopes_and_declared_limits_reject_before_decoding(self):
        with tempfile.TemporaryDirectory(prefix='model-glb-http-envelope-') as directory:
            project = ProjectService(Path(directory))
            before = authored_snapshot(project)
            with http_server(project) as (server, post), \
                    patch('sdk.model_glb.export_model') as export, \
                    patch('sdk.model_glb.preview_import') as review, \
                    patch('sdk.model_glb.pose_import') as pose, \
                    patch('sdk.model_glb.apply_import') as apply:
                valid = dict(asset_id='asset://fixture/model/0', content_base64='eA==', binding={})
                cases = [('/api/model-glb-export', {'asset_id': valid['asset_id'], 'path': 'client-path'}),
                         ('/api/model-glb-export', {'asset_id': False}),
                         ('/api/model-glb-preview', {**valid, 'extra': True}),
                         ('/api/model-glb-preview', {**valid, 'binding': []}),
                         ('/api/model-glb-preview', {**valid, 'binding': {'profile': 'x' * (128 * 1024)}}),
                         ('/api/model-glb-pose-preview', {**valid, 'content_base64': '!bad'}),
                         ('/api/model-glb-pose-preview', {**valid, 'content_base64': ''}),
                         ('/api/model-glb-import', valid),
                         ('/api/model-glb-import', {**valid, 'review_key': '0' * 64, 'extra': True}),
                         ('/api/model-glb-preview', []),
                         ('/api/model-glb-preview', True)]
                for route, body in cases:
                    with self.subTest(route=route, body_type=type(body).__name__):
                        status, result = post(route, body)
                        self.assertEqual(status, 400)
                        self.assertIsInstance(result['error'], str)
                        self.assertEqual(authored_snapshot(project), before)
                # Large declared lengths prove the HTTP gate without allocating
                # a 44 MiB payload or invoking a source decoder.
                for route, length in [('/api/model-glb-export', 32769),
                                      ('/api/model-glb-preview', 44 * 1024 * 1024 + 1)]:
                    with self.subTest(route=route, length=length):
                        connection = HTTPConnection('127.0.0.1', server.server_port, timeout=10)
                        try:
                            connection.request('POST', route, body=b'{}', headers={
                                'Content-Type': 'application/json', 'Content-Length': str(length)})
                            response = connection.getresponse()
                            self.assertEqual(response.status, 400)
                            self.assertIn('at most', json.loads(response.read())['error'])
                        finally:
                            connection.close()
                for decoder in (export, review, pose, apply):
                    decoder.assert_not_called()
                self.assertEqual(authored_snapshot(project), before)


@unittest.skipUnless(os.environ.get('LEGAIA_DISC_BIN'), 'requires private retail disc')
class ModelGlbRetailHttpTests(unittest.TestCase):
    def test_town01_export_review_candidate_apply_history_and_reopen(self):
        from importer.pipeline import _disc_context, import_scene

        disc = os.environ['LEGAIA_DISC_BIN']
        private = ROOT / 'local-output/sdk-20260909'
        private.mkdir(parents=True, exist_ok=True)
        with _disc_context(disc):
            document = import_scene(disc, 'town01')
            asset = next(row for row in document['assets']['models']
                         if row['semantic_id'].endswith('/scene-tmd/0000'))
            asset_id = asset['semantic_id']
            with tempfile.TemporaryDirectory(prefix='model-glb-http-retail-', dir=private) as directory:
                project = ProjectService(Path(directory))
                project.import_metadata(document, disc)
                project.save()
                retail = project._model_source(asset_id, project.active_scene)
                imported = deepcopy(project.imports)
                before = authored_snapshot(project)
                with http_server(project) as (server, post):
                    status, exported = post('/api/model-glb-export', {'asset_id': asset_id})
                    self.assertEqual(status, 200, exported)
                    self.assertEqual(set(exported), {'path', 'filename', 'binding_path',
                        'binding_filename', 'binding', 'report', 'content_base64'})
                    raw = base64.b64decode(exported['content_base64'], validate=True)
                    binding = exported['binding']
                    output, sidecar = Path(exported['path']), Path(exported['binding_path'])
                    self.assertEqual(output.parent, project.root / 'Exports')
                    self.assertEqual(output.name, exported['filename'])
                    self.assertEqual(sidecar, output.with_suffix('.binding.json'))
                    self.assertEqual(sidecar.name, exported['binding_filename'])
                    self.assertEqual(output.read_bytes(), raw)
                    self.assertEqual(json.loads(sidecar.read_text(encoding='utf-8')), binding)
                    self.assertEqual((output.parent / '.gitignore').read_bytes(), b'*\n')
                    self.assertEqual(binding['source_sha256'], sha256(retail).hexdigest())
                    self.assertEqual(binding['effective_sha256'], binding['source_sha256'])
                    self.assertEqual(authored_snapshot(project), before)
                    body = dict(asset_id=asset_id, content_base64=exported['content_base64'], binding=binding)
                    status, noop = post('/api/model-glb-preview', body)
                    self.assertEqual(status, 200, noop)
                    self.assertEqual(noop, exported['report'])
                    self.assertEqual(noop['changes'], [])
                    self.assertEqual(noop['pending_changes'], [])
                    status, result = post('/api/model-glb-import', {**body, 'review_key': noop['review_key']})
                    self.assertEqual(status, 400)
                    self.assertIn('no source-quantized', result['error'])
                    self.assertEqual(authored_snapshot(project), before)

                    row = inspect_model_primitives(retail)['objects'][0]['primitives'][0]
                    self.assertIsNotNone(row['uvs'])
                    uv_delta = 1 if row['uvs'][0][0] < 255 else -1
                    vertex_at = 12 + struct.unpack_from('<I', retail, 12)[0]
                    old_x = struct.unpack_from('<h', retail, vertex_at)[0]
                    dx = 1 if old_x < 32767 else -1
                    edited = move_exported_source_vertex(raw, dx=dx)
                    edited = move_source_corner_uv(edited, binding['profile'], delta=uv_delta)
                    self.assertIsNotNone(row['colors'])
                    color_delta = .75 if row['colors'][0][0] < 255 else -.75
                    edited = move_exported_source_rgb(edited, gouraud=row['gouraud'], delta=color_delta)
                    target_vertex = row['vertices'][2]
                    self.assertNotEqual(row['vertices'][1], target_vertex)
                    edited = rewire_exported_source_corner(edited, target_vertex, corner_id=1)
                    proposed = bytearray(retail)
                    struct.pack_into('<h', proposed, vertex_at, old_x + dx)
                    # Town01's first verified 0x21 packet stores first U at
                    # payload +4; an explicit source assertion avoids guessing.
                    self.assertEqual(row['flags'], 0x21)
                    uv_at = row['byte_offset'] + 4
                    self.assertEqual(retail[uv_at], row['uvs'][0][0])
                    proposed[uv_at] += uv_delta
                    proposed[row['byte_offset']] += 1 if color_delta > 0 else -1
                    reference_at = row['byte_offset'] + 16  # Proven 0x21 corner 1 reference.
                    self.assertEqual(struct.unpack_from('<H', retail, reference_at)[0], row['vertices'][1] * 8)
                    struct.pack_into('<H', proposed, reference_at, target_vertex * 8)
                    proposed = bytes(proposed)
                    edited_body = {**body, 'content_base64': base64.b64encode(edited).decode('ascii')}
                    status, review = post('/api/model-glb-preview', edited_body)
                    self.assertEqual(status, 200, review)
                    self.assertEqual(review['proposed_sha256'], sha256(proposed).hexdigest())
                    self.assertEqual(review['glb_sha256'], sha256(edited).hexdigest())
                    self.assertEqual(len(review['pending_changes']), 4)
                    self.assertEqual({(entry['kind'], entry.get('field'))
                                      for entry in review['pending_changes']}, {('vertex', None), ('primitive', 'uv'), ('primitive', 'color'), ('primitive', 'vertex_index')})
                    self.assertAlmostEqual(review['quantization']['color_max_error'], .25)
                    self.assertFalse(review['project_changed'])
                    self.assertFalse(review['gameplay_verified'])
                    self.assertEqual(authored_snapshot(project), before)
                    status, candidate = post('/api/model-glb-pose-preview', edited_body)
                    self.assertEqual(status, 200, candidate)
                    self.assertEqual(candidate['report'], review)
                    self.assertEqual(candidate['preview']['semantic_id'], asset_id)
                    self.assertTrue(candidate['preview']['model_glb_proposal'])
                    for field in ('vertices', 'triangles', 'triangle_uvs', 'triangle_colors'):
                        self.assertEqual(candidate['preview'][field], decode_tmd(proposed)[field])
                    self.assertEqual(authored_snapshot(project), before)
                    for rejected in [{**edited_body, 'review_key': '0' * 64},
                                     {**body, 'review_key': review['review_key']}]:
                        status, _ = post('/api/model-glb-import', rejected)
                        self.assertEqual(status, 400)
                        self.assertEqual(authored_snapshot(project), before)

                    status, applied = post('/api/model-glb-import', {**edited_body, 'review_key': review['review_key']})
                    self.assertEqual(status, 200, applied)
                    self.assertEqual(applied['model_glb_report'], review)
                    self.assertEqual(len(project.model_sources), 1)
                    receipt = next(iter(project.model_sources.values()))
                    self.assertEqual(receipt['binding'], edited_body['binding'])
                    self.assertEqual(receipt['candidate_sha256'], review['proposed_sha256'])
                    from sdk.model_glb_sources import read_source
                    from base64 import b64decode
                    self.assertEqual(read_source(project, receipt), b64decode(edited_body['content_base64']))
                    self.assertEqual(applied['project']['mode'], 'edit')
                    self.assertEqual(len(project.undo_stack), 1)
                    self.assertEqual(project.model_overrides[asset_id]['format'], 'tmd-content-v1')
                    self.assertEqual(project.read_model_replacement(asset_id, project.model_overrides[asset_id]), proposed)
                    current = authored_snapshot(project)
                    status, rejected = post('/api/model-glb-import', {**edited_body, 'review_key': review['review_key']})
                    self.assertEqual(status, 400)
                    self.assertIn('binding differs', rejected['error'])
                    self.assertEqual(authored_snapshot(project), current)
                    status, _ = post('/api/undo', {})
                    self.assertEqual(status, 200)
                    self.assertNotIn(asset_id, project.model_overrides)
                    status, _ = post('/api/redo', {})
                    self.assertEqual(status, 200)
                    self.assertEqual(project.read_model_replacement(asset_id, project.model_overrides[asset_id]), proposed)
                    status, _ = post('/api/project/save', {})
                    self.assertEqual(status, 200)
                    status, opened = post('/api/project/open', {'path': str(project.root)})
                    self.assertEqual(status, 200, opened)
                    restored = server.project
                    self.assertIsNot(restored, project)
                    self.assertEqual(restored.imports, imported)
                    self.assertEqual(restored.read_model_replacement(asset_id, restored.model_overrides[asset_id]), proposed)
                    self.assertEqual(restored._model_source(asset_id, restored.active_scene), retail)
                    self.assertEqual(project.imports, imported)


if __name__ == '__main__':
    unittest.main()
