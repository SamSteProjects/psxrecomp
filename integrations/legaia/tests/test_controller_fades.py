import struct
import unittest
from hashlib import sha256
from importer.core import ImportError, decompress_lzs
from importer.controller_fades import ControllerFadeAuthoringContext, validate_fade_values
from importer.controller_system_flags import ControllerRecordSource
from importer.man_layout import read_man_layout
from importer.serialization import compress_lzs, serialize_man_decoded
from test_controller_branches import source, OWNER

ID = 'script://fixture/controllers/man-p1/0000/fade/0005'
VALUES = dict(selector=255, signed_words=[-32768, 0, 32767])


class ControllerFades(unittest.TestCase):
    def test_full_man_literal_signed_limits_dispatch_and_roundtrip(self):
        for header in (b'\x4c', b'\xcc\x07'):
            for sub in (0x90, 0x91, 0x92):
                script = header+bytes([sub, 9])+struct.pack('<hhh', -1, 123, -234)
                script += b'\x26'+((-len(script)-1)&65535).to_bytes(2, 'little')
                src, man = source(script)
                for compression in ('none', 'lzs'):
                    ctx = ControllerFadeAuthoringContext(src if compression == 'none' else
                        ControllerRecordSource('fixture', man, compress_lzs(man), {}, compression='lzs'))
                    target = ctx.options(OWNER)['targets'][0]
                    self.assertEqual(target['sub_op'], sub)
                    self.assertEqual(ctx.patch({ID: target['values']}), (man, []))
                    for values in (VALUES, dict(selector=0, signed_words=[32767, -32768, -1])):
                        result, audit = ctx.patch({ID: values})
                        at = 57+5+len(header)+1
                        expected = bytearray(man)
                        expected[at:at+7] = bytes([values['selector']])+struct.pack('<hhh', *values['signed_words'])
                        self.assertEqual(result, bytes(expected)); self.assertEqual(ctx._man, man)
                        self.assertEqual(read_man_layout(result), read_man_layout(man))
                        self.assertEqual(audit[0]['decoded_byte_offset'], at)
                        self.assertEqual(audit[0]['before_values'], target['values'])
                        self.assertEqual(audit[0]['after_values'], values)
                        self.assertEqual(audit[0]['source_record_sha256'], sha256(man[57:-18]).hexdigest())
                        encoded, _ = serialize_man_decoded(compress_lzs(man), len(man), result, 'fixture')
                        self.assertEqual(decompress_lzs(encoded, len(man))[0], result)
                    target['values']['signed_words'][0] = 999
                    self.assertEqual(ctx.options(OWNER)['targets'][0]['values']['signed_words'][0], -1)

    def test_invalid_values_and_source_ownership_refuse(self):
        script = b'\x4c\x90\x00'+bytes(6)+b'\x26\xf6\xff'
        src, man = source(script); ctx = ControllerFadeAuthoringContext(src)
        for invalid in (True, -1, 256, 1.0, '1', None):
            with self.assertRaises(ImportError): ctx.patch({ID: dict(VALUES, selector=invalid)})
        for invalid in (True, -32769, 32768, 1.0, '1', None):
            with self.assertRaises(ImportError): validate_fade_values(dict(VALUES, signed_words=[invalid, 0, 0]))
        for words in ([], [0, 1], [0]*4, (0, 0, 0), None):
            with self.assertRaises(ImportError): validate_fade_values(dict(VALUES, signed_words=words))
        for values in ({}, dict(VALUES, speed=1), {'signed_words': [0, 0, 0]}):
            with self.assertRaises(ImportError): ctx.patch({ID: values})
        for owner in (OWNER.replace('fixture', 'foreign'), OWNER.replace('/controllers/', '/actors/'), OWNER.replace('/0000', '/0001')):
            with self.assertRaises(ImportError): ctx.options(owner)
            with self.assertRaises(ImportError): ctx.patch({owner.replace('scene://', 'script://')+'/fade/0005': VALUES})
        for pc in ('0006', '000e', 'ffff'):
            with self.assertRaises(ImportError): ctx.patch({ID[:-4]+pc: VALUES})
        with self.assertRaises(ImportError): ctx.patch({ID: VALUES}, original=man+b'x')
        with self.assertRaises(ImportError): ControllerFadeAuthoringContext(object())

    def test_partial_paths_and_other_menu_families_are_not_authoring_targets(self):
        src, _ = source(b'\x4c\x90\x00'+bytes(6)+b'\x4c\x93')
        ctx = ControllerFadeAuthoringContext(src)
        self.assertFalse(ctx.options(OWNER)['supported'])
        with self.assertRaises(ImportError): ctx.patch({ID: VALUES})
        for script in (b'\x4c\x9e'+bytes(32)+b'\x26\xdd\xff', b'\x4c\x9f\x26\xfd\xff'):
            src, _ = source(script); ctx = ControllerFadeAuthoringContext(src)
            self.assertFalse(ctx.options(OWNER)['inspection']['stops'])
            self.assertFalse(ctx.options(OWNER)['supported'])
            with self.assertRaises(ImportError): ctx.patch({ID: VALUES})
