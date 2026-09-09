"""Synthetic TIM/address proofs, plus opt-in private retail smoke."""
import os
from pathlib import Path
import struct
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from importer.core import ImportError
from importer.textures import (TextureCatalog, _pack_members, associate_material,
                               decode_tim, load_scene_texture_catalog, parse_tim)


def block(x, y, w, h, words):
    payload = words if isinstance(words, bytes) else struct.pack(f"<{len(words)}H", *words)
    return struct.pack("<I4H", 12 + len(payload), x, y, w, h) + payload


def tim(bpp=4, *, image=None, palette=None, flags=None):
    if image is None:
        image = block(0, 0, 1, 1, [0x3210])
    if palette is None and bpp < 16:
        palette = block(0, 100, 1 << bpp, 1,
                        [0, 31, 0x3E0, 0xFC00] + [0] * ((1 << bpp) - 4))
    mode = (4, 8, 16, 24).index(bpp) | (8 if palette else 0)
    return struct.pack("<II", 0x10, mode if flags is None else flags) + (palette or b"") + image


def catalog(*items):
    return TextureCatalog("synthetic", "0" * 64,
                          [(parse_tim(item), {"semantic_id": f"texture://synthetic/{i}"})
                           for i, item in enumerate(items)])


def material(bpp=4, clut=100 << 6, page_x=0, page_y=0):
    return dict(textured=True, clut=clut,
                tpage=page_x // 64 | (page_y // 256) << 4 | (4, 8, 16).index(bpp) << 7,
                semi_transparent=False)


class TimTests(unittest.TestCase):
    def test_four_bit_order_transparency_and_stp(self):
        decoded = decode_tim(tim())
        self.assertEqual((decoded["width"], decoded["height"]), (4, 1))
        self.assertEqual(decoded["rgba"], bytes([0, 0, 0, 0, 255, 0, 0, 255,
                                                  0, 255, 0, 255, 0, 0, 255, 255]))
        self.assertEqual(decoded["stp"], bytes([0, 0, 0, 1]))

    def test_eight_bit_and_palette_selection(self):
        palettes = block(0, 100, 256, 2, [31] * 256 + [0x3E0] * 256)
        decoded = decode_tim(tim(8, image=block(0, 0, 1, 1, [0xFF00]), palette=palettes), 1)
        self.assertEqual(decoded["rgba"], bytes([0, 255, 0, 255]) * 2)
        with self.assertRaisesRegex(ImportError, "complete requested palette"):
            decode_tim(tim(8), 1)

    def test_sixteen_bit_and_opaque_stp_black(self):
        decoded = decode_tim(tim(16, image=block(0, 0, 2, 1, [0, 0x8000])))
        self.assertEqual(decoded["rgba"], bytes([0, 0, 0, 0, 0, 0, 0, 255]))
        self.assertEqual(decoded["stp"], b"\0\1")

    def test_twenty_four_bit_rgb_rows(self):
        decoded = decode_tim(tim(24, image=block(0, 0, 3, 1, b"\1\2\3\4\5\6")))
        self.assertEqual(decoded["rgba"], b"\1\2\3\xff\4\5\6\xff")
        self.assertEqual(decoded["width"], 2)
        with self.assertRaisesRegex(ImportError, "row padding"):
            parse_tim(tim(24, image=block(0, 0, 1, 1, [0])))

    def test_retail_opaque_flag_exception_is_preserved(self):
        self.assertEqual(parse_tim(tim(flags=0x10008)).flags, 0x10008)
        for flags in (4, 7, 0x20008, 0x10009):
            with self.subTest(flags=flags), self.assertRaisesRegex(ImportError, "unsupported TIM"):
                parse_tim(tim(flags=flags))

    def test_lengths_and_vram_bounds_are_checked(self):
        raw = tim()
        for malformed in (b"", raw[:6], raw[:-1], tim(image=block(1024, 0, 1, 1, [0])),
                          tim(image=block(1023, 0, 2, 1, [0, 0])),
                          tim(image=block(0, 511, 1, 2, [0, 0]))):
            with self.subTest(length=len(malformed)), self.assertRaises(ImportError):
                parse_tim(malformed)
        bad = bytearray(raw)
        struct.pack_into("<I", bad, 8, 12)
        with self.assertRaisesRegex(ImportError, "block length"):
            parse_tim(bytes(bad))

    def test_pack_offsets_use_correct_origin_and_reject_aliasing(self):
        payload = tim()
        standalone = struct.pack("<III", 0x1000000, 1, 2) + payload
        nested = struct.pack("<II", 1, 2) + payload
        self.assertEqual(_pack_members(standalone, True), [(12, len(standalone))])
        self.assertEqual(_pack_members(nested, False), [(8, len(nested))])
        for bad in (struct.pack("<IIII", 0x1000000, 2, 3, 3) + payload,
                    struct.pack("<III", 0x1000000, 1, 0xFFFFFFFF),
                    struct.pack("<III", 0x1000000, 1, 0)):
            with self.assertRaises(ImportError):
                _pack_members(bad, True)


class MaterialAssociationTests(unittest.TestCase):
    def test_exact_crop_agrees_with_independent_tim_decode(self):
        raw = tim()
        result = associate_material(catalog(raw), material(), (0, 0, 3, 0))
        self.assertEqual(result["status"], "address_match")
        self.assertEqual(result["rgba"], decode_tim(raw)["rgba"])
        self.assertEqual(result["source_ids"], ["texture://synthetic/0"])
        self.assertIn("not_runtime_residency", result["evidence"])

    def test_cross_tim_palette_and_flat_strip_upload(self):
        image = tim(image=block(64, 256, 1, 1, [0]), palette=b"")
        palette = tim(16, image=block(0, 0, 1, 1, [0]),
                      palette=block(0, 100, 16, 2, [31] * 16 + [0x3E0] * 16))
        result = associate_material(catalog(image, palette),
                                    material(clut=(100 << 6) | 1, page_x=64, page_y=256),
                                    (0, 0, 0, 0))
        self.assertEqual(result["status"], "address_match")
        self.assertEqual(result["rgba"], bytes([0, 255, 0, 255]))
        self.assertEqual(len(result["source_ids"]), 2)
        with self.assertRaisesRegex(ImportError, "complete requested palette"):
            decode_tim(image)

    def test_partial_image_and_missing_palette_are_explicit(self):
        result = associate_material(catalog(tim()), material(), (0, 0, 4, 0))
        self.assertEqual(result["status"], "missing")
        self.assertNotIn("rgba", result)
        missing = associate_material(catalog(tim(palette=b"")), material(), (0, 0, 0, 0))
        self.assertEqual(missing["status"], "missing")

    def test_conflicting_uploads_fail_but_identical_duplicates_agree(self):
        raw = tim()
        duplicate = associate_material(catalog(raw, raw), material(), (0, 0, 0, 0))
        self.assertEqual(duplicate["status"], "address_match")
        self.assertEqual(len(duplicate["source_ids"]), 2)
        conflict = associate_material(catalog(raw, tim(image=block(0, 0, 1, 1, [1]))),
                                      material(), (0, 0, 0, 0))
        self.assertEqual(conflict["status"], "ambiguous")
        self.assertNotIn("rgba", conflict)

    def test_eight_and_sixteen_bit_page_sampling(self):
        for bpp in (8, 16):
            raw = tim(bpp, image=block(64, 256, 1, 1, [0x0101 if bpp == 8 else 31]))
            result = associate_material(catalog(raw), material(bpp, page_x=64, page_y=256),
                                        (0, 0, 16 // bpp - 1, 0))
            self.assertEqual(result["status"], "address_match")
            self.assertEqual(result["rgba"], decode_tim(raw)["rgba"])

    def test_unsupported_modes_and_uv_bounds(self):
        for change in ({"textured": False}, {"tpage": 0x180}, {"tpage": 0x200}, {"clut": None}):
            result = associate_material(catalog(tim()), dict(material(), **change), (0, 0, 0, 0))
            self.assertEqual(result["status"], "unsupported")
        for bounds in ((1, 0, 0, 0), (0, 0, 256, 0), (True, 0, 0, 0)):
            with self.assertRaises(ImportError):
                associate_material(catalog(tim()), material(), bounds)


@unittest.skipUnless(os.environ.get("LEGAIA_DISC_BIN"), "requires private retail disc")
class RetailTextureTests(unittest.TestCase):
    def test_town01_structural_catalog_and_real_tmd_address_match(self):
        from importer.pipeline import import_scene
        from importer.assets import load_model_preview
        disc = os.environ["LEGAIA_DISC_BIN"]
        textures = load_scene_texture_catalog(disc, "town01")
        self.assertEqual(len(textures.textures), 96)
        self.assertEqual({source["prot_entry_index"] for _, source in textures.textures}, {5})
        self.assertEqual(len(textures.diagnostics), 1)  # explicit global scope note
        for image, _ in textures.textures:
            pixels = decode_tim(image)
            self.assertEqual(len(pixels["rgba"]), pixels["width"] * pixels["height"] * 4)
        imported = import_scene(disc, "town01")
        asset = next(a for a in imported["assets"]["models"] if a["semantic_id"].endswith("/0088"))
        preview = load_model_preview(disc, asset)
        self.assertEqual(len(preview["materials"]), 2)
        for index, mat in enumerate(preview["materials"]):
            uv = [v for tri, mi in zip(preview["triangle_uvs"], preview["triangle_materials"])
                  if mi == index for v in tri]
            bounds = (min(v[0] for v in uv), min(v[1] for v in uv),
                      max(v[0] for v in uv), max(v[1] for v in uv))
            result = associate_material(textures, mat, bounds)
            self.assertEqual(result["status"], "address_match")
            self.assertEqual(result["source_ids"], [f"texture://town01/5/raw/{93 + index}"])


if __name__ == "__main__":
    unittest.main()
