"""Independent fixed-window retail evidence for world-map menu wire fields.

The private disc is read only. Only name/discovery consumers are proved here;
destination and X/Y encodings do not become travel or pixel-coordinate claims.
"""
import hashlib
import os
import struct
import unittest

from importer.pipeline import _disc_context


@unittest.skipUnless(os.environ.get('LEGAIA_DISC_BIN'), 'requires unchanged private retail disc')
class WorldmapRetailEvidence(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with _disc_context(os.environ['LEGAIA_DISC_BIN']) as (image, _, _, _):
            cls.executable = image.read_file(image.find('SCUS_942.54'))
        if hashlib.sha256(cls.executable).hexdigest() != '292256e2e66db42727f613406785e444254d3f699569e611f65fcf1c6d2f3482':
            raise AssertionError('The executing evidence requires the unchanged supported SCUS executable')
        cls.load = struct.unpack_from('<I', cls.executable, 0x18)[0]
        if cls.load != 0x80010000:
            raise AssertionError('Unexpected executable load address')

    def span(self, start, end):
        return self.executable[0x800 + start - self.load:0x800 + end - self.load]

    def window(self, start, end, sha256):
        value = self.span(start, end)
        self.assertEqual(len(value), end - start)
        self.assertEqual(hashlib.sha256(value).hexdigest(), sha256)

    def word(self, address):
        return struct.unpack('<I', self.span(address, address + 4))[0]

    def fields(self, address):
        value = self.word(address)
        return value >> 26, (value >> 21) & 31, (value >> 16) & 31, value & 65535

    def branch_target(self, address):
        delta = self.word(address) & 65535
        if delta >= 32768:
            delta -= 65536
        return address + 4 + delta * 4

    def test_twenty_source_rows_terminate_before_names_without_table_overlap(self):
        self.window(0x80073a98, 0x80073b18,
                    'e3effa628a8ce190d988cb63b136fab87752aaaa4c1d6d7a628e3cbea62600dd')
        self.window(0x80073b18, 0x80073d18,
                    '941520f73b011d1705dcfdcf9023560602b5938754e9c58068e08c90c79f9a30')
        table = self.span(0x80073a98, 0x80073b18)
        rows = []
        for index in range(len(table) // 6):
            row = struct.unpack_from('<BBHBB', table, index * 6)
            if row[0] == 255:
                break
            rows.append(row)
        self.assertEqual((len(rows), index), (20, 20))
        self.assertTrue(all(row[0] < 16 for row in rows))
        self.assertNotIn(14, {row[0] for row in rows})
        self.assertEqual(0x800 + 0x80073a98 - self.load, 0x64298)
        self.assertEqual(0x64298 + index * 6, 0x64310)
        self.assertEqual(len(table) - (index + 1) * 6, 2)
        self.assertEqual(table[-2:], bytes(2))
        self.assertEqual({row[2] for row in rows}, {85, 244, 354, 391, 533})

    def test_walker_uses_discovery_plus32_and_last_emitted_name(self):
        self.window(0x80031870, 0x800318e0,
                    '9e3bb811f9b8f120cc0a6d2b818c6bea51d04ce44b4444e0814ab665eede18fa')
        self.assertEqual(self.word(0x80010d38 + (0x19 - 2) * 4), 0x80031870)
        self.assertEqual(self.fields(0x80031898), (36, 18, 21, 0))  # name byte
        self.assertEqual(self.fields(0x8003189c), (9, 0, 2, 255))
        self.assertEqual(self.branch_target(0x800318a0), 0x800318e0)  # terminator
        self.assertEqual(self.branch_target(0x800318a8), 0x800318d4)  # last emitted name
        self.assertEqual(self.fields(0x800318b0), (36, 18, 4, 1))  # discovery byte
        self.assertEqual(self.word(0x800318b4), 0x0c00f399)  # JAL8003CE64
        self.assertEqual(self.fields(0x800318b8), (9, 4, 4, 32))  # delay slot adds32
        self.assertEqual(self.branch_target(0x800318bc), 0x800318d4)  # hidden row skip
        self.assertEqual(self.fields(0x800318c0), (13, 17, 2, 0x8000))
        self.assertEqual(self.fields(0x800318c4), (41, 19, 2, 0))  # source row string ID
        self.assertEqual(self.word(0x800318d0), 0x02a08021)  # s0=name after emission only
        self.assertEqual(self.fields(0x800318d4), (9, 18, 18, 6))
        self.assertEqual(self.word(0x800318d8), 0x0800c626)  # loop, no64-row cap

    def test_name_resolver_masks_source_row_index_and_uses_stride32(self):
        self.window(0x800300a8, 0x800300dc,
                    '9546ef02decb59fbd363619f8ef83d327e8367818fa71cd32df5426d606ca5a6')
        self.assertEqual(self.fields(0x800300a8), (15, 0, 4, 0x8007))
        self.assertEqual(self.fields(0x800300ac), (9, 4, 4, 0x3a98))
        self.assertEqual(self.fields(0x800300b0), (12, 5, 3, 0x3ff))
        self.assertEqual(self.word(0x800300b4), 0x00031040)  # index*2
        self.assertEqual(self.word(0x800300b8), 0x00431021)  # plus index
        self.assertEqual(self.word(0x800300bc), 0x00021040)  # index*6
        self.assertEqual(self.fields(0x800300c4), (36, 2, 3, 0))
        self.assertEqual(self.fields(0x800300cc), (9, 2, 2, 0x3b18))
        self.assertEqual(self.word(0x800300d0), 0x00031940)  # name*32
        self.assertEqual(self.word(0x800300d8), 0x00621821)  # name pointer, no index guard

    def test_discovery_bitmap_address_and_msb_first_mask_are_exact(self):
        self.window(0x8003ce64, 0x8003ce9c,
                    'b4f9cf72c7afddb13a75f5072eb90990d380d3153716a3f087adcc1ae6d900fe')
        self.assertEqual(self.fields(0x8003ce64), (15, 0, 3, 0x8008))
        self.assertEqual(self.fields(0x8003ce68), (9, 3, 3, 0x4140))
        self.assertEqual(self.word(0x8003ce6c), 0x000410c3)  # index>>3
        self.assertEqual(self.fields(0x8003ce74), (36, 2, 3, 0x1618))
        self.assertEqual(0x80084140 + 0x1618, 0x80085758)
        self.assertEqual(self.fields(0x8003ce78), (12, 4, 4, 7))
        self.assertEqual(self.fields(0x8003ce7c), (9, 0, 2, 128))
        self.assertEqual(self.word(0x8003ce80), 0x00821007)  # mask0x80>>(index&7)
        self.assertEqual(self.word(0x8003ce84), 0x00621824)
        self.assertEqual(self.fields(0x8003ce90), (9, 0, 5, 255))
        self.assertEqual(self.word(0x8003ce98), 0x00a01021)  # returns0 or255
        self.assertEqual([(value + 32) >> 3 for value in (0, 255)], [4, 35])
        self.assertEqual([0x80 >> ((value + 32) & 7) for value in (0, 7, 8, 255)],
                         [128, 1, 128, 1])


if __name__ == '__main__':
    unittest.main()
