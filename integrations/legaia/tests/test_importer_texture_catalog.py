"""Structural texture assets contain no payload; previews resolve verified IDs."""
from contextlib import nullcontext
from copy import deepcopy
import json
import os
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from importer.core import ImportError
from importer.texture_catalog import load_texture_asset_catalog, preview_texture_asset
from importer.textures import TextureCatalog, decode_tim, load_scene_texture_catalog, parse_tim
from integrations.legaia.tests.test_importer_textures import block, tim


class TextureAssetCatalogTests(unittest.TestCase):
    def setUp(self):
        self.catalog = TextureCatalog("fixture", "0" * 64)
        payloads = [tim(8, palette=block(0, 100, 256, 2, [31] * 256 + [0x3E0] * 256)),
                    tim(16), tim(4, palette=b"")]
        for slot, data in enumerate(payloads):
            self.catalog.textures.append((parse_tim(data), {
                "semantic_id": f"texture://fixture/2/0/{slot}", "prot_entry_index": 2,
                "descriptor_index": 0, "pack_slot": slot, "byte_offset": 100 + slot * 100,
                "byte_length": len(data), "byte_coordinate_space": "decoded_lzs_descriptor"}))
        for mock in (patch("importer.texture_catalog._disc_context", side_effect=lambda _: nullcontext()),
                     patch("importer.texture_catalog.load_scene_texture_catalog", return_value=self.catalog)):
            mock.start()
            self.addCleanup(mock.stop)

    def test_metadata_is_deterministic_payload_free_and_detached(self):
        result = load_texture_asset_catalog("fixture", "fixture")
        self.assertEqual(result, load_texture_asset_catalog("fixture", "fixture"))
        self.assertEqual([a["palette_count"] for a in result["assets"]], [2, 0, 0])
        self.assertEqual([a["preview_supported"] for a in result["assets"]], [True, True, False])
        encoded = json.dumps(result)
        self.assertNotIn('"rgba"', encoded)
        self.assertNotIn('"data"', encoded)
        self.assertNotIn('"stp"', encoded)
        self.assertTrue(all(a["asset_kind"] == "texture" for a in result["assets"]))
        result["assets"][0]["source_record"]["byte_offset"] = 99999
        self.assertEqual(self.catalog.textures[0][1]["byte_offset"], 100)

    def test_palette_preview_reuses_decoder_and_fresh_source_metadata(self):
        identifier = self.catalog.textures[0][1]["semantic_id"]
        result = preview_texture_asset("fixture", "fixture", identifier, 1)
        self.assertEqual(result["rgba"], bytes([0, 255, 0, 255]) * 2)
        self.assertEqual(result["stp"], b"\0\0")
        self.assertEqual(result["palette_index"], 1)
        self.assertEqual(result["asset"]["source_record"]["disc"]["sha256"], "0" * 64)
        # The same structural ID receives current verified provenance, never a client locator.
        self.catalog.disc_sha256 = "1" * 64
        newer = preview_texture_asset("fixture", "fixture", identifier)
        self.assertEqual(newer["asset"]["source_record"]["disc"]["sha256"], "1" * 64)
        self.assertNotEqual(newer["rgba"], result["rgba"])

    def test_unknown_ids_palettes_names_and_duplicate_locators_reject(self):
        for identifier in (None, {}, "../image.tim", "texture://other/2/0/0"):
            with self.subTest(identifier=identifier), self.assertRaises(ImportError):
                preview_texture_asset("fixture", "fixture", identifier)
        for palette in (True, -1, 1.5, 2):
            with self.subTest(palette=palette), self.assertRaises(ImportError):
                preview_texture_asset("fixture", "fixture", "texture://fixture/2/0/0", palette)
        for scene in (None, "", "../town01", "town01/other", "a" * 129):
            with self.subTest(scene=scene), self.assertRaises(ImportError):
                load_texture_asset_catalog("fixture", scene)
        with self.assertRaisesRegex(ImportError, "local palette"):
            preview_texture_asset("fixture", "fixture", "texture://fixture/2/0/2")
        with self.assertRaisesRegex(ImportError, "palette count"):
            preview_texture_asset("fixture", "fixture", "texture://fixture/2/0/1", 1)
        self.catalog.textures.append(deepcopy(self.catalog.textures[0]))
        with self.assertRaisesRegex(ImportError, "ambiguous"):
            load_texture_asset_catalog("fixture", "fixture")


@unittest.skipUnless(os.environ.get("LEGAIA_DISC_BIN"), "requires private retail disc")
class RetailTextureAssetCatalogTests(unittest.TestCase):
    def test_actual_town01_catalog_and_preview_match_existing_decoder(self):
        from importer.pipeline import _disc_context
        disc = os.environ["LEGAIA_DISC_BIN"]
        with _disc_context(disc):
            report = load_texture_asset_catalog(disc, "town01")
            self.assertEqual(len(report["assets"]), 96)
            self.assertEqual(len({a["semantic_id"] for a in report["assets"]}), 96)
            json.dumps(report)
            original = load_scene_texture_catalog(disc, "town01")
            selected = next(a for a in report["assets"] if a["preview_supported"])
            decoded = preview_texture_asset(disc, "town01", selected["semantic_id"])
            source_tim = next(t for t, s in original.textures if s["semantic_id"] == selected["semantic_id"])
            expected = decode_tim(source_tim)
            for key in ("width", "height", "rgba", "stp"):
                self.assertEqual(decoded[key], expected[key])
            self.assertEqual(decoded["asset"], selected)
            with self.assertRaises(ImportError):
                load_texture_asset_catalog(disc, "no_such_scene")


if __name__ == "__main__":
    unittest.main()
