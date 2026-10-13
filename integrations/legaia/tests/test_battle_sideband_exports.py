"""Source exports preserve literal native geometry, pixels and project state."""
import base64
from copy import deepcopy
from hashlib import sha256
import json
import os
from pathlib import Path
import tempfile
import unittest

from sdk.project import ProjectService, ProjectError
from sdk.project_assets import source_key
from sdk.battle_sideband import resources, export
from importer.texture_png import decode_png
from test_importer_export import parse_glb
from test_animation_clip_export import values
from test_model_primitive_workflow import http_server


@unittest.skipUnless(os.getenv('LEGAIA_DISC_BIN'), 'Private retail source is required')
class SidebandExportTests(unittest.TestCase):
    def test_all_models_pages_and_masks_match_source(self):
        with tempfile.TemporaryDirectory() as root:
            p = ProjectService(Path(root))
            p.disc_path = os.environ['LEGAIA_DISC_BIN']
            p.save()
            held = deepcopy((p._document(), p.undo_stack, p.redo_stack))
            args = dict(expected_project_path=str(p.root), expected_source_key=source_key(p))
            report = resources(p, **args)
            cases, positions, page_exports = [], 0, 0
            for record in report['catalog']['models']:
                receipt = export(p, **args, asset_id=record['semantic_id'], catalog_source_key=report['catalog']['source_key'], palette_index=0, export_kind='glb')
                data = base64.b64decode(receipt['file_base64'])
                self.assertEqual(sha256(data).hexdigest(), receipt['sha256'])
                self.assertEqual(len(data), receipt['byte_length'])
                doc, binary = parse_glb(data)
                g = receipt['inspection']['preview']
                self.assertEqual(doc['extras']['source_record'], record['source_record'])
                self.assertFalse(doc.get('animations'))
                self.assertFalse(doc.get('skins'))
                for node in doc['nodes']:
                    if 'mesh' not in node:
                        continue
                    obj = node['extras']['source_object']
                    for primitive in doc['meshes'][node['mesh']]['primitives']:
                        expected = []
                        for tri in range(obj['triangle_start'], obj['triangle_start'] + obj['triangle_count']):
                            if g['triangle_materials'][tri] != primitive['material']:
                                continue
                            for corner in (0, 2, 1):
                                x, y, z = g['vertices'][g['triangles'][tri][corner]]
                                expected.append((x, -y, z))
                        actual = values(doc, binary, primitive['attributes']['POSITION'])
                        self.assertEqual(actual, expected)
                        positions += len(actual)
                cases.append(receipt)
            seen_modes = set()
            for record in report['catalog']['textures']:
                retain = record['mode'] not in seen_modes
                for palette in (0, record['palette_count'] - 1):
                    for kind in ('png', 'stp'):
                        receipt = export(p, **args, asset_id=record['semantic_id'], catalog_source_key=report['catalog']['source_key'], palette_index=palette, export_kind=kind)
                        data = base64.b64decode(receipt['file_base64'])
                        self.assertEqual(sha256(data).hexdigest(), receipt['sha256'])
                        self.assertEqual(len(data), receipt['byte_length'])
                        decoded = decode_png(data)
                        source = receipt['inspection']['preview']
                        expected = base64.b64decode(source['rgba_base64']) if kind == 'png' else bytes(v for bit in base64.b64decode(source['stp_base64']) for v in (bit * 255, bit * 255, bit * 255, 255))
                        self.assertEqual(decoded['rgba'], expected)
                        self.assertEqual((decoded['width'], decoded['height']), (record['width'], 256))
                        page_exports += 1
                        if retain:
                            cases.append(receipt)
                seen_modes.add(record['mode'])
            self.assertEqual((len(report['catalog']['models']), positions, page_exports), (41, 90063, 500))
            self.assertEqual(held, (p._document(), p.undo_stack, p.redo_stack))
            if os.getenv('LEGAIA_SIDEBAND_EXPORT_CASES'):
                Path(os.environ['LEGAIA_SIDEBAND_EXPORT_CASES']).write_text(json.dumps(dict(report=report, cases=cases, position_samples=positions, page_exports=page_exports, unchanged=True)), encoding='utf-8')

    def test_http_types_freshness_and_exact_fields(self):
        with tempfile.TemporaryDirectory() as root:
            p = ProjectService(Path(root))
            p.disc_path = os.environ['LEGAIA_DISC_BIN']
            p.save()
            args = dict(expected_project_path=str(p.root), expected_source_key=source_key(p))
            report = resources(p, **args)
            model, page = report['catalog']['models'][0], report['catalog']['textures'][0]
            request = dict(args, asset_id=model['semantic_id'], catalog_source_key=report['catalog']['source_key'], palette_index=0, export_kind='glb')
            held = deepcopy((p._document(), p.undo_stack, p.redo_stack))
            with http_server(p) as (_, post):
                self.assertEqual(post('/api/battle-sideband-export', request)[0], 200)
                for kind in ('png', 'stp'):
                    self.assertEqual(post('/api/battle-sideband-export', dict(request, asset_id=page['semantic_id'], export_kind=kind))[0], 200)
                for field, invalid in [('expected_project_path', str(p.root) + '-foreign'), ('expected_source_key', 'stale'),
                                       ('catalog_source_key', 'stale'), ('asset_id', 'foreign'), ('palette_index', True),
                                       ('export_kind', 'unknown'), ('export_kind', 'png'), ('asset_id', page['semantic_id'])]:
                    self.assertEqual(post('/api/battle-sideband-export', dict(request, **{field: invalid}))[0], 400)
                self.assertEqual(post('/api/battle-sideband-export', dict(request, extra=True))[0], 400)
                self.assertEqual(post('/api/battle-sideband-export', args)[0], 400)
            self.assertEqual(held, (p._document(), p.undo_stack, p.redo_stack))
