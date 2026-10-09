import unittest
from importer.core import ImportError, decompress_lzs
from importer.controller_scene_bytes import ControllerSceneByteAuthoringContext, validate_scene_byte_values
from importer.controller_system_flags import ControllerRecordSource
from importer.serialization import compress_lzs
from importer.man_layout import read_man_layout
from importer.script_inspection import _instruction, inspect_record
from test_controller_branches import source, OWNER

ID = 'script://fixture/controllers/man-p1/0000/scene-byte/0005'


class ControllerSceneBytes(unittest.TestCase):
    def test_literal_byte_span_both_dispatch_headers_and_carriers(self):
        for header in (b'\x4c', b'\xcc\xf8'):
            script = header+b'\xdf\x01'
            script += b'\x26'+((-len(script)-1)&65535).to_bytes(2, 'little')
            src, man = source(script)
            for compression in ('none', 'lzs'):
                ctx = ControllerSceneByteAuthoringContext(src if compression == 'none' else
                    ControllerRecordSource('fixture', man, compress_lzs(man), {}, compression='lzs'))
                options = ctx.options(OWNER); target = options['targets'][0]
                self.assertEqual(target['values'], {'value': 1})
                self.assertEqual(ctx.patch({ID: target['values']}), (man, []))
                for value in (0, 255):
                    result, audit = ctx.patch({ID: {'value': value}})
                    at = 57+5+len(header)+1; expected = bytearray(man); expected[at] = value
                    self.assertEqual(result, bytes(expected)); self.assertEqual(ctx._man, man)
                    self.assertEqual(read_man_layout(result), read_man_layout(man))
                    self.assertEqual(decompress_lzs(compress_lzs(result), len(result))[0], result)
                    self.assertEqual(audit[0]['byte_length'], 1)
                    self.assertEqual(audit[0]['before_hex'], '01')
                    self.assertEqual(audit[0]['after_values'], {'value': value})
                target['values']['value'] = 42
                self.assertEqual(ctx.options(OWNER)['targets'][0]['values'], {'value': 1})
            node = _instruction(header+b'\xdf\xff', 0)
            self.assertEqual(node['operands']['runtime_effect'], 'not_evaluated')
            self.assertEqual(node['successors'], [{'pc': len(header)+2, 'condition': 'encoded_continuation'}])
            for size in range(len(header)+1, len(header)+2):
                with self.assertRaises(ImportError): _instruction((header+b'\xdf\x01')[:size], 0)

    def test_domains_owner_and_reached_source_qualification(self):
        src, man = source(b'\x4c\xdf\x01\x26\xfc\xff')
        ctx = ControllerSceneByteAuthoringContext(src)
        for value in (True, -1, 256, 1.0, '1', None):
            with self.assertRaises(ImportError): validate_scene_byte_values({'value': value})
        for value in ({}, {'value': 1, 'extra': 0}, None):
            with self.assertRaises(ImportError): ctx.patch({ID: value})
        for identity in (ID.replace('fixture', 'foreign'), ID.replace('/scene-byte/', '/three-word/'),
                         ID[:-4]+'0006', ID.replace('/controllers/', '/actors/')):
            with self.assertRaises(ImportError): ctx.patch({identity: {'value': 0}})
        with self.assertRaises(ImportError): ctx.patch({ID: {'value': 0}}, original=man+b'x')
        src, _ = source(b'\x4c\xdf\x01\x43\x11')
        ctx = ControllerSceneByteAuthoringContext(src)
        self.assertFalse(ctx.options(OWNER)['supported'])
        with self.assertRaises(ImportError): ctx.patch({ID: {'value': 0}})

    def test_unvisited_tail_is_not_reinterpreted_or_modified(self):
        src, man = source(b'\x4c\xdf\x01\x26\xfc\xff\x43\x11\xff\x00')
        ctx = ControllerSceneByteAuthoringContext(src); options = ctx.options(OWNER)
        self.assertTrue(options['supported']); self.assertFalse(options['inspection']['stops'])
        self.assertEqual(options['inspection']['status'], 'partial')
        result, _ = ctx.patch({ID: {'value': 255}})
        expected = bytearray(man); expected[64] = 255
        self.assertEqual(result, bytes(expected))
        self.assertEqual(inspect_record(result[57:-18], 5)['opaque_regions'], options['inspection']['opaque_regions'])
