"""PNG service freshness, review-only isolation, HTTP and normal history."""
import base64
from contextlib import nullcontext
from copy import deepcopy
from hashlib import sha256
from http.client import HTTPConnection
import json
from pathlib import Path
import struct
import tempfile
import unittest
from unittest.mock import Mock, patch
import zlib

from importer.texture_authoring import _validate
from importer.texture_png import decode_png
from sdk import texture_png
from sdk.project import ProjectService, ProjectError
from test_importer_textures import tim, block
from test_model_primitive_workflow import http_server
from test_project_workflow import synthetic_scene

ASSET = 'texture://fixture/1/raw/0'


def png_rgba(width, height, rgba):
    def chunk(kind, data):
        return struct.pack('>I', len(data)) + kind + data + struct.pack('>I', zlib.crc32(kind + data))
    rows = b''.join(b'\0' + rgba[y * width * 4:(y + 1) * width * 4] for y in range(height))
    return b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', width, height, 8, 6, 0, 0, 0)) + chunk(b'IDAT', zlib.compress(rows)) + chunk(b'IEND', b'')


class TexturePngWorkflow(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='texture-png-workflow-')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        disc = self.root / 'fixture.bin'; disc.write_bytes(b'qualified fixture identity')
        self.project = ProjectService(self.root / 'project')
        self.project.import_metadata(synthetic_scene(), str(disc)); self.project.save()
        self.source = tim(image=block(0, 0, 1, 1, [0x3210]))
        self.context = Mock()
        self.context.options.return_value = dict(supported=True)
        self.context.original_tim.return_value = self.source
        self.context.validate_replacement.side_effect = lambda asset, value: _validate(self.source, value)
        for item in (patch.object(ProjectService, '_texture_context', return_value=self.context),
                     patch('importer.pipeline._disc_context', side_effect=lambda _: nullcontext())):
            item.start(); self.addCleanup(item.stop)

    def snapshot(self):
        return deepcopy((self.project._document(), self.project.imports,
                         self.project.undo_stack, self.project.redo_stack))

    def export(self):
        return texture_png.export_texture(self.project, ASSET, 0)

    def edited(self, png):
        image = decode_png(png); rgba = bytearray(image['rgba'])
        rgba[4:8] = bytes((0, 255, 0, 255))  # existing green entry replaces red index1
        return png_rgba(image['width'], image['height'], rgba)

    def test_review_pixels_apply_undo_redo_reopen_and_retail_restore(self):
        png, stp, binding, exported = self.export(); before = self.snapshot()
        self.assertEqual(exported['pending_changes']['total_change_count'], 0)
        content = self.edited(png)
        report = texture_png.preview_import(self.project, ASSET, content, binding, 'existing', stp)
        self.assertEqual(report['pending_changes']['pixel_indices_changed'], 1)
        self.assertEqual(report['pending_changes']['palette_words_changed'], 0)
        pixels = texture_png.pixels_import(self.project, ASSET, content, binding, 'existing', stp)
        self.assertEqual(pixels['report'], report)
        self.assertNotEqual(pixels['current_png_base64'], pixels['proposed_png_base64'])
        self.assertEqual(self.snapshot(), before)
        texture_png.apply_import(self.project, ASSET, content, binding, 'existing', stp, report['review_key'])
        self.assertEqual(len(self.project.undo_stack), len(before[2]) + 1)
        authored = deepcopy(self.project.texture_overrides)
        self.project.undo(); self.assertEqual(self.project.texture_overrides, {})
        self.project.redo(); self.assertEqual(self.project.texture_overrides, authored)
        reopened = ProjectService.open(self.project.save())
        self.assertEqual(reopened.texture_overrides, authored)
        self.assertEqual(self.project.imports, before[1])
        _, _, current, _ = self.export()
        restore = texture_png.preview_import(self.project, ASSET, png, current, 'existing', stp)
        texture_png.apply_import(self.project, ASSET, png, current, 'existing', stp, restore['review_key'])
        self.assertFalse(self.project.texture_overrides)
        self.project.undo(); self.assertEqual(self.project.texture_overrides, authored)

    def test_binding_review_and_context_guards_leave_state_unchanged(self):
        png, stp, binding, _ = self.export(); content = self.edited(png); before = self.snapshot()
        for field, value in [('asset_id', ASSET + 'x'), ('source_sha256', '0' * 64),
                             ('effective_sha256', '0' * 64), ('project_source_key', 'stale')]:
            bad = deepcopy(binding); bad[field] = value
            with self.subTest(field=field), self.assertRaises(ProjectError):
                texture_png.preview_import(self.project, ASSET, content, bad)
        with self.assertRaises(ProjectError):
            texture_png.apply_import(self.project, ASSET, png, binding, 'existing', stp, '0' * 64)
        report = texture_png.preview_import(self.project, ASSET, content, binding, 'existing', stp)
        with self.assertRaises(ProjectError):
            texture_png.apply_import(self.project, ASSET, content, binding, 'rebuild', stp, report['review_key'])
        noop = texture_png.preview_import(self.project, ASSET, png, binding, 'existing', stp)
        with self.assertRaisesRegex(ProjectError, 'no quantized'):
            texture_png.apply_import(self.project, ASSET, png, binding, 'existing', stp, noop['review_key'])
        self.assertEqual(self.snapshot(), before)
        self.project.mode = 'live'
        with self.assertRaisesRegex(ProjectError, 'Edit'):
            self.export()

    def test_direct_rgb24_report_can_count_more_than_rgb16_word_capacity(self):
        profile = dict(bpp=24, width=512, height=256, entry_count=0)
        counts = dict(color_max_error=0, color_rms_error=0, quantized_pixel_count=0,
                      distinct_requested_words=65537, output_palette_size=0,
                      stp_changed_pixels=0, forced_black_stp_pixels=0, forced_transparent_stp_pixels=0)
        self.assertEqual(texture_png._quantization(dict(quantization=counts), profile), counts)
        counts['distinct_requested_words'] = profile['width'] * profile['height'] + 1
        with self.assertRaises(ProjectError):
            texture_png._quantization(dict(quantization=counts), profile)

    def test_http_envelopes_export_files_and_reviewed_import(self):
        before = self.snapshot()
        with http_server(self.project) as (server, post):
            status, exported = post('/api/texture-png-export', dict(asset_id=ASSET, palette_index=0))
            self.assertEqual(status, 200, exported)
            for name in ('path', 'stp_path', 'binding_path'):
                self.assertTrue(Path(exported[name]).is_relative_to(self.project.root / 'Exports'))
                self.assertTrue(Path(exported[name]).is_file())
            body = dict(asset_id=ASSET, png_base64=base64.b64encode(self.edited(base64.b64decode(exported['png_base64']))).decode(),
                        stp_png_base64=exported['stp_png_base64'], binding=exported['binding'], palette_mode='existing')
            status, report = post('/api/texture-png-preview', body)
            self.assertEqual(status, 200, report)
            status, pixels = post('/api/texture-png-pixels-preview', body)
            self.assertEqual(status, 200, pixels)
            self.assertEqual(pixels['report'], report)
            invalid = [('/api/texture-png-export', {'asset_id': ASSET, 'palette_index': True}),
                       ('/api/texture-png-preview', {**body, 'extra': 1}),
                       ('/api/texture-png-preview', {**body, 'png_base64': '!bad'}),
                       ('/api/texture-png-preview', {**body, 'stp_png_base64': ''}),
                       ('/api/texture-png-preview', {**body, 'binding': {'x': 'x' * 131072}}),
                       ('/api/texture-png-import', body),
                       ('/api/texture-png-import', {**body, 'review_key': '0' * 64})]
            for route, request in invalid:
                with self.subTest(route=route):
                    status, result = post(route, request); self.assertEqual(status, 400, result)
            for route, limit in [('/api/texture-png-export', 32768), ('/api/texture-png-preview', 24 * 1024 * 1024)]:
                connection = HTTPConnection('127.0.0.1', server.server_port, timeout=10)
                connection.request('POST', route, b'{}', {'Content-Type': 'application/json', 'Content-Length': str(limit + 1)})
                response = connection.getresponse(); self.assertEqual(response.status, 400); response.read(); connection.close()
            self.assertEqual(self.snapshot(), before)
            status, result = post('/api/texture-png-import', {**body, 'review_key': report['review_key']})
            self.assertEqual(status, 200, result); self.assertEqual(result['texture_png_report'], report)


if __name__ == '__main__':
    unittest.main()
