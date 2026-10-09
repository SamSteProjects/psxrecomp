import unittest
from importer.core import ImportError, decompress_lzs
from importer.controller_party_selectors import ControllerPartySelectorAuthoringContext, validate_party_selector_values
from importer.controller_system_flags import ControllerRecordSource
from importer.serialization import compress_lzs
from importer.man_layout import read_man_layout
from test_controller_branches import source, OWNER

ID = 'script://fixture/controllers/man-p1/0000/party-selector/0005'


class ControllerPartySelectors(unittest.TestCase):
    def test_all_native_bits_headers_selectors_and_carriers(self):
        for header in (b'\x4c', b'\xcc\xf8'):
            for sub in (*range(16), *range(0x20, 0x30)):
                script = header+bytes([sub])
                script += b'\x26'+((-len(script)-1)&65535).to_bytes(2, 'little')
                src, man = source(script)
                for compression in ('none', 'lzs'):
                    ctx = ControllerPartySelectorAuthoringContext(src if compression == 'none' else
                        ControllerRecordSource('fixture', man, compress_lzs(man), {}, compression='lzs'))
                    target = ctx.options(OWNER)['targets'][0]
                    self.assertEqual(target['values'], {'party_selector': sub & 7})
                    self.assertEqual(target['sub_op'], sub)
                    self.assertEqual(target['preserved_bits'], sub & 0xf8)
                    self.assertEqual(target['selector_mask'], 7)
                    self.assertEqual(ctx.patch({ID: target['values']}), (man, []))
                    for selector in range(8):
                        result, audit = ctx.patch({ID: {'party_selector': selector}})
                        at = 57+5+len(header); expected = bytearray(man); expected[at] = (sub & 0xf8) | selector
                        self.assertEqual(result, bytes(expected)); self.assertEqual(ctx._man, man)
                        self.assertEqual(read_man_layout(result), read_man_layout(man))
                        self.assertEqual(decompress_lzs(compress_lzs(result), len(result))[0], result)
                        if selector != sub & 7:
                            self.assertEqual(audit[0]['byte_length'], 1)
                            self.assertEqual(audit[0]['before_hex'], bytes([sub]).hex())
                            self.assertEqual(audit[0]['after_values'], {'party_selector': selector})
                            self.assertEqual(audit[0]['sub_op'], sub)
                    target['values']['party_selector'] = 99
                    self.assertEqual(ctx.options(OWNER)['targets'][0]['values'], {'party_selector': sub & 7})

    def test_domains_owner_stops_and_unvisited_tail(self):
        src, man = source(b'\x4c\x2a\x26\xfd\xff\xee\x00')
        ctx = ControllerPartySelectorAuthoringContext(src)
        for value in (True, -1, 8, 1.0, '1', None):
            with self.assertRaises(ImportError): validate_party_selector_values({'party_selector': value})
        for value in ({}, {'party_selector': 1, 'extra': 0}, None):
            with self.assertRaises(ImportError): ctx.patch({ID: value})
        for identity in (ID.replace('fixture', 'foreign'), ID.replace('/party-selector/', '/scene-byte/'),
                         ID[:-4]+'0006', ID.replace('/controllers/', '/actors/')):
            with self.assertRaises(ImportError): ctx.patch({identity: {'party_selector': 0}})
        with self.assertRaises(ImportError): ctx.patch({ID: {'party_selector': 0}}, original=man+b'x')
        options = ctx.options(OWNER); self.assertFalse(options['inspection']['stops'])
        result, audit = ctx.patch({ID: {'party_selector': 7}}); expected = bytearray(man); expected[63] = 0x2f
        self.assertEqual(result, bytes(expected)); self.assertEqual(audit[0]['before_values'], {'party_selector': 2})
        for script in (b'\x4c', b'\xcc\xf8', b'\x4c\x20\xee', b'\x4c\x30\x26\xfd\xff'):
            src, _ = source(script); ctx = ControllerPartySelectorAuthoringContext(src)
            self.assertFalse(ctx.options(OWNER)['supported'])
            with self.assertRaises(ImportError): ctx.patch({ID: {'party_selector': 0}})

    def test_two_sites_patch_order_and_operation_retention(self):
        src, man = source(b'\x4c\x08\xcc\xf8\x2b\x26\xfa\xff')
        ctx = ControllerPartySelectorAuthoringContext(src); targets = ctx.options(OWNER)['targets']
        edits = {targets[1]['semantic_id']: {'party_selector': 0}, ID: {'party_selector': 7}}
        result, audit = ctx.patch(edits); expected = bytearray(man); expected[63] = 0x0f; expected[66] = 0x28
        self.assertEqual(result, bytes(expected)); self.assertEqual(ctx.patch(dict(reversed(list(edits.items())))), (result, audit))
        self.assertEqual([row['mnemonic'] for row in audit], ['PARTY_LEADER_REQUEST', 'PARTY_VIEW_SWAP_REQUEST'])


if __name__ == '__main__': unittest.main()
