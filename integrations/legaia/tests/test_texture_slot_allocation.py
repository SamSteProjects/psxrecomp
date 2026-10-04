"""Exact native slot append and raw/compressed archive construction checks."""
from copy import deepcopy
from hashlib import sha256
import struct
import unittest

from importer.core import ImportError, parse_scene_assets, decompress_lzs
from importer.textures import _pack_members, parse_tim
from importer.texture_slot_allocation import append_texture_pack
from importer.texture_layout_allocation import resize_tim_image
from importer.model_pack_archive import _archive
from importer.model_pack_composition import compose_model_pack_archive
from test_importer_textures import tim, block
from test_importer_texture_authoring import fixture as texture_fixture
from test_texture_pack_growth import fixture as growth_fixture
from test_model_pack_archive import archive_source


class TextureSlotAllocation(unittest.TestCase):
    def test_append_keeps_slots_gap_tails_and_optional_existing_edits(self):
        for standalone in (False, True):
            _, _, _, source = texture_fixture(compressed=not standalone)
            base = 4 if standalone else 0
            members = _pack_members(source, standalone)
            # Retain an explicit nonzero gap beyond the native offset table.
            gap_start = base + 4 + len(members) * 4
            gapped = bytearray(source[:gap_start] + b'GAP!' + source[gap_start:])
            for slot, (start, _) in enumerate(members):
                struct.pack_into('<I', gapped, base + 4 + slot * 4, (start + 4 - base) // 4)
            source = bytes(gapped)
            members = _pack_members(source, standalone)
            old = parse_tim(source[members[0][0]:members[0][1]])
            original = source[members[0][0]:members[0][0] + old.byte_length]
            resized, _ = resize_tim_image(original, sha256(original).hexdigest(), 8, 3, 7)
            edits = [dict(slot_index=0, source_tim_sha256=sha256(original).hexdigest(), tim=resized)]
            additions = [tim(16, image=block(640, 32, 3, 1, b'\x00\x80' * 3)),
                         tim(8, image=block(768, 48, 2, 1, bytes([1, 2, 3, 4])))]
            snapshot = deepcopy((edits, additions))
            for selected in (None, [], edits):
                candidate, audit = append_texture_pack(source, sha256(source).hexdigest(), additions,
                                                       edits=selected, standalone=standalone)
                new = _pack_members(candidate, standalone)
                self.assertEqual(len(new), 4)
                self.assertEqual(candidate[base + 4 + 4 * 4:new[0][0]], b'GAP!')
                for slot, (start, end) in enumerate(members):
                    old_tim = parse_tim(source[start:end])
                    payload = resized if selected and slot == 0 else source[start:start + old_tim.byte_length]
                    tail = source[start + old_tim.byte_length:end]
                    row = audit['members'][slot]
                    self.assertEqual(candidate[new[slot][0]:new[slot][1]], payload + tail + bytes(row['alignment_padding_bytes'] + (audit['existing_edit_audit']['members'][slot]['alignment_padding_bytes'] if selected else 0)))
                for slot, addition in enumerate(additions, 2):
                    self.assertEqual(candidate[new[slot][0]:new[slot][0] + len(addition)], addition)
                self.assertEqual(audit['added_slot_indices'], [2, 3])
                self.assertFalse(audit['gameplay_verified'])
            self.assertEqual((edits, additions), snapshot)

    def test_rejects_unqualified_incomplete_and_out_of_vram_additions(self):
        _, _, _, source = texture_fixture(compressed=True)
        valid = tim(16)
        for additions in ([], [valid] * 129, (valid,), [bytearray(valid)], [valid + b'X'],
                          [tim(16, image=block(1023, 0, 2, 1, bytes(4)))],
                          [tim(16, image=block(0, 512, 2, 1, bytes(4)))],
                          [tim(24, image=block(0, 0, 2, 1, bytes(4)))],
                          [tim(8, palette=block(1008, 500, 256, 1, bytes(512)))]):
            with self.assertRaises(ImportError):
                append_texture_pack(source, sha256(source).hexdigest(), additions)
        for kwargs in ({'edits': False}, {'standalone': 1}):
            with self.assertRaises(ImportError):
                append_texture_pack(source, sha256(source).hexdigest(), [valid], **kwargs)
        with self.assertRaises(ImportError):
            append_texture_pack(source, '0' * 64, [valid])
        # A full native table must reject additions before attempting a rebuild.
        payload = tim(16, image=block(0, 0, 2, 1, bytes(4)))
        count = 1024
        start = 4 + count * 4
        full = struct.pack('<I', count) + struct.pack('<1024I', *[(start + i * len(payload)) // 4 for i in range(count)]) + payload * count
        with self.assertRaises(ImportError):
            append_texture_pack(full, sha256(full).hexdigest(), [valid])

    def test_composed_raw_and_compressed_archive_reopen_both_headers(self):
        added = tim(16, image=block(640, 0, 64, 32, b'\x01\x80' * 2048))
        for header in (0, 2048):
            source, _, native, pack, _, _ = growth_fixture()
            carrier = _archive(source).read_entry(_archive(source).entry(1))
            source, _ = archive_source(carrier, header)
            resized, _ = resize_tim_image(native, sha256(native).hexdigest(), 128, 32, 0x8000)
            edits = [dict(slot_index=0, source_tim_sha256=sha256(native).hexdigest(), tim=resized)]
            proposed, _ = append_texture_pack(pack, sha256(pack).hexdigest(), [added], edits=edits)
            request = dict(kind='texture-addition-pack', entry_index=1, table_offset=0, descriptor_index=0,
                           expected_pack_sha256=sha256(pack).hexdigest(), pack=proposed,
                           layout_edits=edits, slot_additions=[added])
            result, audit = compose_model_pack_archive(source, sha256(source).hexdigest(), [request], header_offset=header)
            raw = _archive(result).read_entry(_archive(result).entry(1))
            row = parse_scene_assets(raw, 1).descriptors[0]
            decoded, _ = decompress_lzs(raw[row.data_offset:], row.size)
            self.assertEqual(decoded, proposed)
            self.assertTrue(audit['final_texture_additions_verified'])
            self.assertEqual(result[-8 * 2048:], source[-8 * 2048:])
            with self.assertRaises(ImportError):
                compose_model_pack_archive(source, sha256(source).hexdigest(), [dict(request, pack=proposed + b'X')], header_offset=header)
            _, fake, _, _ = texture_fixture()
            source, _ = archive_source(fake.raw, header)
            original = _archive(source).read_entry(_archive(source).entry(1))
            proposed, _ = append_texture_pack(original, sha256(original).hexdigest(), [added], standalone=True)
            request = dict(kind='texture-addition-raw', entry_index=1, expected_pack_sha256=sha256(original).hexdigest(),
                           edits=[], slot_additions=[added])
            result, audit = compose_model_pack_archive(source, sha256(source).hexdigest(), [request], header_offset=header)
            emitted = _archive(result).read_entry(_archive(result).entry(1))
            self.assertEqual(emitted[:len(proposed)], proposed)
            self.assertEqual(emitted[len(proposed):], bytes(len(emitted) - len(proposed)))
            self.assertEqual(result[-8 * 2048:], source[-8 * 2048:])
            self.assertTrue(audit['final_texture_additions_verified'])
            with self.assertRaises(ImportError):
                compose_model_pack_archive(source, sha256(source).hexdigest(), [request, request], header_offset=header)
            for additions in (None, [], True):
                with self.assertRaises(ImportError):
                    compose_model_pack_archive(source, sha256(source).hexdigest(), [dict(request, slot_additions=additions)], header_offset=header)


if __name__ == '__main__':
    unittest.main()
