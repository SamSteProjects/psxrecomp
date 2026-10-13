"""Fixed sideband source spans, literal pixels and fresh read-only HTTP APIs."""
import base64
from copy import deepcopy
from hashlib import sha256
import json
import os
from pathlib import Path
import struct
import tempfile
import unittest

from importer.battle_sideband import decode_catalog, texture_preview, SLOT_BYTES
from importer.core import ImportError
from importer.pipeline import _disc_context, import_scene
from importer.textures import decode_tim
from sdk.project import ProjectService
from sdk.project_assets import source_key
from test_model_primitive_workflow import http_server


class SidebandBoundsTests(unittest.TestCase):
    def test_missing_entries_hash_and_footprints_refuse(self):
        for entries, digest in [(None, '0' * 64), ({893: b''}, '0' * 64),
                                ({893: b'', 894: b''}, 'bad'), ({893: b'', 894: b''}, '0' * 64)]:
            with self.assertRaises(ImportError):
                decode_catalog(entries, digest)


@unittest.skipUnless(os.getenv('LEGAIA_DISC_BIN'), 'Private retail source is required')
class SidebandSourceTests(unittest.TestCase):
    def test_all_fixed_models_and_native_page_pixels(self):
        with _disc_context(os.environ['LEGAIA_DISC_BIN']) as (_, digest, _, archive):
            entries = {i: archive.read_entry(archive.entry(i)) for i in (893, 894)}
        catalog = decode_catalog(entries, digest)
        self.assertEqual([b['slot_count'] for b in catalog['banks']], [103, 78])
        self.assertEqual((len(catalog['models']), len(catalog['textures']), len(catalog['slots'])), (41, 125, 181))
        self.assertEqual(sum(r['kind'] == 'opaque' for r in catalog['slots']), 15)
        self.assertEqual(sum(r['references_beyond_texture_pool'] for r in catalog['models']), 5)
        for record in catalog['models'] + catalog['textures']:
            s = record['source_record']
            content = entries[s['prot_entry_index']]
            self.assertEqual(sha256(content).hexdigest(), s['entry_sha256'])
            self.assertEqual(sha256(content[s['slot_offset']:s['slot_offset'] + SLOT_BYTES]).hexdigest(), s['slot_sha256'])
            self.assertEqual(sha256(content[s['byte_offset']:s['byte_offset'] + s['byte_length']]).hexdigest(), s['sha256'])
        for record in catalog['textures']:
            s = record['source_record']
            content = entries[s['prot_entry_index']]
            raw = content[s['byte_offset']:s['byte_offset'] + s['byte_length']]
            clut, page = raw[4:record['image_offset']], raw[record['image_offset']:]
            # A display-only wrapper permits an independent existing TIM decoder
            # to check every pixel. The native source is not a TIM file.
            virtual = (struct.pack('<III4H', 16, 8, 12 + len(clut), 0, 0, 256, record['clut_rows']) + clut +
                       struct.pack('<I4H', 12 + len(page), 0, 0, record['width'] // 4, 256) + page)
            for palette in (0, record['palette_count'] - 1):
                actual = texture_preview(content, record, palette)
                expected = decode_tim(virtual, palette)
                self.assertEqual(actual['rgba'], expected['rgba'])
                self.assertEqual(actual['stp'], expected['stp'])
            for palette in (True, -1, record['palette_count']):
                with self.assertRaises(ImportError):
                    texture_preview(content, record, palette)

    def test_all_http_previews_history_and_source_guards(self):
        with tempfile.TemporaryDirectory() as root:
            project = ProjectService(Path(root))
            project.disc_path = os.environ['LEGAIA_DISC_BIN']
            project.import_metadata(import_scene(project.disc_path, 'town01'))
            project.save()
            project = ProjectService.open(project.root)
            held = deepcopy((project._document(), project.undo_stack, project.redo_stack))
            args = dict(expected_project_path=str(project.root), expected_source_key=source_key(project))
            cases = []
            with http_server(project) as (_, post):
                status, report = post('/api/battle-sideband-resources', args)
                self.assertEqual(status, 200, report)
                for record in report['catalog']['models'] + report['catalog']['textures']:
                    request = dict(args, asset_id=record['semantic_id'], catalog_source_key=report['catalog']['source_key'], palette_index=0)
                    status, value = post('/api/battle-sideband-preview', request)
                    self.assertEqual(status, 200, value)
                    self.assertEqual(value['record'], record)
                    self.assertTrue(value['read_only'])
                    self.assertFalse(value['project_changed'])
                    self.assertEqual(len(base64.b64decode(value['source_slot_base64'])), SLOT_BYTES)
                    if record['asset_kind'] == 'tmd_model' or record['mode'] not in {v['record'].get('mode') for v in cases}:
                        cases.append(value)
                first = report['catalog']['models'][0]
                request = dict(args, asset_id=first['semantic_id'], catalog_source_key=report['catalog']['source_key'], palette_index=0)
                for field, invalid in [('expected_project_path', str(project.root) + '-foreign'), ('expected_source_key', 'stale'),
                                       ('asset_id', 'foreign'), ('catalog_source_key', 'stale'), ('palette_index', True), ('palette_index', 1)]:
                    self.assertEqual(post('/api/battle-sideband-preview', dict(request, **{field: invalid}))[0], 400)
                self.assertEqual(post('/api/battle-sideband-resources', dict(args, extra=True))[0], 400)
                self.assertEqual(post('/api/battle-sideband-preview', args)[0], 400)
            self.assertEqual(held, (project._document(), project.undo_stack, project.redo_stack))
            if os.getenv('LEGAIA_SIDEBAND_CASES'):
                Path(os.environ['LEGAIA_SIDEBAND_CASES']).write_text(json.dumps(dict(report=report, cases=cases)), encoding='utf-8')
