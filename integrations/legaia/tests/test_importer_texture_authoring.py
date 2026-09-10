"""Exact TIM payload edits, carrier grouping and private retail source guards."""
from contextlib import nullcontext
from copy import deepcopy
import hashlib
import os
from pathlib import Path
import struct
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from importer.core import ImportError, decompress_lzs
from importer.serialization import compress_lzs
from importer.texture_authoring import TextureAuthoringContext, load_texture_authoring_context
from importer.textures import TextureCatalog, _pack_members, parse_tim
from integrations.legaia.tests.test_importer_textures import block, tim


def literals(data):
    return b"".join(b"\xff" + data[n:n + 8] for n in range(0, len(data), 8))


def fixture(compressed=False, compact=False):
    members = [tim(), tim()] if not compact else [tim(16, image=block(0, 0, 64, 1, bytes(128)))]
    base = 0 if compressed else 4
    pack = bytearray(base + 4 + 4 * len(members))
    if base:
        pack[:4] = b"\0\0\0\1"
    struct.pack_into("<I", pack, base, len(members))
    for slot, member in enumerate(members):
        struct.pack_into("<I", pack, base + 4 + slot * 4, (len(pack) - base) // 4)
        pack.extend(member)
        pack.extend(b"\xa5" * (-len(pack) % 4))
    pack.extend(b"opaque member tail")
    pack = bytes(pack)
    if compressed:
        stream = compress_lzs(pack) if compact else literals(pack)
        raw = bytearray(56)
        struct.pack_into("<I", raw, 0, 6)
        struct.pack_into("<II", raw, 8, (1 << 24) | len(pack), 56)
        struct.pack_into("<II", raw, 16, (3 << 24) | 1, 56 + len(stream) + 8)
        raw.extend(stream + b"OPAQUE!!" + b"\xffZ")
    else:
        raw = bytearray(pack)
    raw.extend(bytes(-len(raw) % 2048))
    entry = SimpleNamespace(index=5, start_lba=100, size_sectors=len(raw) // 2048)
    archive = SimpleNamespace(node=SimpleNamespace(extent_lba=20))
    archive.raw = bytes(raw)
    archive.entry = lambda index: entry if index == 5 else None
    archive.read_entry = lambda _entry, **_: archive.raw
    catalog = TextureCatalog("fixture", "0" * 64)
    ranges = _pack_members(pack, not compressed)
    for slot, (start, _) in enumerate(ranges):
        source = {"semantic_id": f"texture://fixture/5/{'0' if compressed else 'raw'}/{slot}",
                  "prot_entry_index": 5, "pack_slot": slot, "byte_offset": start,
                  "byte_length": len(members[slot]),
                  "byte_coordinate_space": "decoded_lzs_descriptor" if compressed else "prot_entry"}
        if compressed:
            source.update(descriptor_index=0, compressed_stream_offset=56)
        catalog.textures.append((parse_tim(members[slot]), source))
    return TextureAuthoringContext("fixture", "fixture", catalog), archive, catalog, pack


class TextureAuthoringTests(unittest.TestCase):
    def scope(self, archive, digest="0" * 64):
        return patch("importer.texture_authoring._disc_context", side_effect=lambda _: nullcontext((None, digest, {}, archive)))

    def test_raw_image_and_palette_edits_preserve_headers_other_members_and_opaque_bytes(self):
        context, archive, catalog, _ = fixture()
        identifier = catalog.textures[0][1]["semantic_id"]
        with self.scope(archive):
            original = context.original_tim(identifier)
            self.assertEqual(context.patch({identifier: original}), ([], []))
            self.assertEqual(context.patch({}), ([], []))
            replacement = bytearray(original)
            replacement[20] ^= 1  # Palette payload.
            replacement[-1] ^= 1  # Image payload.
            info = context.validate_replacement(identifier, bytes(replacement))
            self.assertTrue(info["image_changed"] and info["palette_changed"])
            overlays, audit = context.patch({identifier: bytes(replacement)})
            self.assertEqual((len(overlays), len(audit)), (1, 1))
            overlay = overlays[0]
            offset = overlay["offset"] - 120 * 2048
            applied = archive.raw[:offset] + overlay["payload"] + archive.raw[offset + overlay["size"]:]
            self.assertEqual(applied[:offset], archive.raw[:offset])
            self.assertEqual(applied[offset + overlay["size"]:], archive.raw[offset + overlay["size"]:])
            self.assertEqual(context.original_tim(identifier), original)
            self.assertEqual(context.options(identifier)["carrier"]["kind"], "raw_tim_pack")

    def test_same_lzs_carrier_members_merge_once_and_leave_consumed_span_boundary_exact(self):
        context, archive, catalog, original_pack = fixture(compressed=True)
        edits = {}
        with self.scope(archive):
            expected = bytearray(original_pack)
            for _, source in catalog.textures:
                original = context.original_tim(source["semantic_id"])
                replacement = original[:-1] + bytes([original[-1] ^ 1])
                edits[source["semantic_id"]] = replacement
                offset = source["byte_offset"]
                expected[offset:offset + len(replacement)] = replacement
            overlays, audit = context.patch(edits)
            self.assertEqual((len(overlays), len(audit)), (1, 2))
            overlay = overlays[0]
            self.assertEqual(overlay["carrier_kind"], "lzs_descriptor_tim_pack")
            decoded = decompress_lzs(overlay["payload"], len(original_pack))[0]
            self.assertEqual(decoded, bytes(expected))
            start = overlay["offset"] - 120 * 2048
            self.assertEqual(start, 56)
            self.assertEqual(archive.raw[start + overlay["size"]:start + overlay["size"] + 8], b"OPAQUE!!")
            self.assertEqual(overlay["expected_sha256"], hashlib.sha256(archive.raw[start:start + overlay["size"]]).hexdigest())
            applied = archive.raw[:start] + overlay["payload"] + archive.raw[start + overlay["size"]:]
            self.assertEqual(applied[:start], archive.raw[:start])
            self.assertEqual(applied[start + overlay["size"]:], archive.raw[start + overlay["size"]:])
            self.assertEqual(context.patch({s["semantic_id"]: context.original_tim(s["semantic_id"]) for _, s in catalog.textures}), ([], []))

    def test_replacement_layout_length_and_unknown_ids_reject_without_changing_source(self):
        context, archive, catalog, _ = fixture()
        identifier = catalog.textures[0][1]["semantic_id"]
        with self.scope(archive):
            original = context.original_tim(identifier)
            cases = [original + b"\0", original[:-1], bytearray(original)]
            for offset in (4, 12, 14, 16, 18, 56):
                candidate = bytearray(original)
                candidate[offset] ^= 1
                cases.append(bytes(candidate))
            for candidate in cases:
                with self.subTest(length=len(candidate)), self.assertRaises(ImportError):
                    context.patch({identifier: candidate})
                self.assertEqual(context.original_tim(identifier), original)
            with self.assertRaises(ImportError):
                context.patch({"texture://other/5/raw/0": original})
            with self.assertRaises(ImportError):
                context.patch({identifier: original, "../source": original})

    def test_compressed_growth_still_rejects_and_alias_or_truncated_carrier_fails_closed(self):
        context, archive, catalog, _ = fixture(compressed=True, compact=True)
        identifier = catalog.textures[0][1]["semantic_id"]
        with self.scope(archive):
            original = context.original_tim(identifier)
            replacement = original[:20] + bytes(range(128))
            with self.assertRaisesRegex(ImportError, "relocation is unsupported"):
                context.patch({identifier: replacement})
            self.assertEqual(context.original_tim(identifier), original)
            baseline = archive.raw
            for destination, reason in ((56, "aliases"), (57, "truncated")):
                changed = bytearray(baseline)
                struct.pack_into("<I", changed, 20, destination)
                archive.raw = bytes(changed)
                self.assertFalse(context.options(identifier)["supported"])
                with self.assertRaisesRegex(ImportError, reason):
                    context.original_tim(identifier)
            archive.raw = baseline
        with self.scope(archive, "1" * 64):
            with self.assertRaisesRegex(ImportError, "disc changed"):
                context.original_tim(identifier)


@unittest.skipUnless(os.environ.get("LEGAIA_DISC_BIN"), "requires private retail disc")
class RetailTextureAuthoringTests(unittest.TestCase):
    def test_actual_town01_tim_patch_maps_exact_user_bytes_and_keeps_disc_unchanged(self):
        from importer.pipeline import _disc_context
        disc = os.environ["LEGAIA_DISC_BIN"]
        with _disc_context(disc) as (image, _, _, _):
            context = load_texture_authoring_context(disc, "town01")
            identifier = "texture://town01/5/raw/0"
            original = context.original_tim(identifier)
            self.assertEqual(len(original), 33312)
            replacement = bytearray(original)
            replacement[20] ^= 1
            replacement[-1] ^= 1
            overlays, audit = context.patch({identifier: bytes(replacement)})
            self.assertEqual((len(overlays), len(audit)), (1, 1))
            self.assertTrue(audit[0]["image_changed"] and audit[0]["palette_changed"])
            overlay = overlays[0]
            self.assertEqual((overlay["offset"], overlay["size"]), (1221000, 33312))
            self.assertEqual(image.read_user(0, overlay["offset"], overlay["size"], image.size // 2352 * 2048), original)
            self.assertEqual(parse_tim(overlay["payload"]).image.metadata(), parse_tim(original).image.metadata())
            self.assertEqual(context.original_tim(identifier), original)
            self.assertEqual(context.patch({identifier: original}), ([], []))


if __name__ == "__main__":
    unittest.main()
