"""GLB binary roundtrip tests; all permanent geometry/texture fixtures synthetic."""
import base64
from copy import deepcopy
import json
import os
from pathlib import Path
import struct
import sys
import tempfile
import unittest
from unittest.mock import patch
import zlib

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from importer.core import ImportError
from importer.export import encode_model_glb, write_model_export


def preview():
    return {
        "schema_version": "legaia.model-preview.v1", "semantic_id": "asset://synthetic/model",
        "coordinate_system": "retail_tmd_object_local", "posed": False,
        "vertices": [[0, 0, 0], [2, 0, 0], [0, 2, 0]], "triangles": [[0, 1, 2]],
        "triangle_colors": [[[128, 128, 128]] * 3], "triangle_uvs": [[[10, 20], [11, 20], [10, 21]]],
        "triangle_materials": [0], "materials": [{"textured": True, "clut": 0, "tpage": 0}],
        "objects": [{"object_index": 0, "triangle_start": 0, "triangle_count": 1,
                     "vertex_start": 0, "vertex_count": 3, "raw_object_word6": 123, "transform": None}],
        "textures": [{"material_index": 0, "status": "address_match", "width": 2, "height": 2,
                      "uv_origin": [10, 20], "rgba_base64": base64.b64encode(bytes(range(16))).decode(),
                      "source_ids": ["texture://synthetic/atlas"]}],
        "source_record": {"disc": {"sha256": "0" * 64}}, "reference_commit": "synthetic",
    }


def parse_glb(raw):
    magic, version, length = struct.unpack_from("<III", raw)
    assert (magic, version, length) == (0x46546C67, 2, len(raw))
    json_length, kind = struct.unpack_from("<I4s", raw, 12)
    assert kind == b"JSON" and json_length % 4 == 0
    doc = json.loads(raw[20:20 + json_length])
    offset = 20 + json_length
    bin_length, kind = struct.unpack_from("<I4s", raw, offset)
    assert kind == b"BIN\0" and bin_length % 4 == 0
    binary = raw[offset + 8:]
    assert len(binary) == bin_length
    assert 0 <= bin_length - doc["buffers"][0]["byteLength"] <= 3
    for view in doc["bufferViews"]:
        assert view["byteOffset"] % 4 == 0
        assert 0 <= view["byteOffset"] < view["byteOffset"] + view["byteLength"] <= len(binary)
    return doc, binary


def read_accessor(doc, binary, index):
    accessor = doc["accessors"][index]
    view = doc["bufferViews"][accessor["bufferView"]]
    count = int(accessor["type"][-1])
    assert accessor["componentType"] == 5126
    start = view["byteOffset"]
    result = list(struct.iter_unpack(f"<{count}f", binary[start:start + view["byteLength"]]))
    assert len(result) == accessor["count"]
    return result


class GlbExportTests(unittest.TestCase):
    def test_binary_roundtrip_axis_winding_uv_png_and_provenance(self):
        source = preview()
        original = deepcopy(source)
        raw, audit = encode_model_glb(source)
        doc, binary = parse_glb(raw)
        attrs = doc["meshes"][0]["primitives"][0]["attributes"]
        self.assertEqual(read_accessor(doc, binary, attrs["POSITION"]), [(0, 0, 0), (0, -2, 0), (2, 0, 0)])
        self.assertEqual(read_accessor(doc, binary, attrs["COLOR_0"]), [(1, 1, 1)] * 3)
        self.assertEqual(read_accessor(doc, binary, attrs["TEXCOORD_0"]), [(0.25, 0.25), (0.25, 0.75), (0.75, 0.25)])
        image_view = doc["bufferViews"][doc["images"][0]["bufferView"]]
        image = binary[image_view["byteOffset"]:image_view["byteOffset"] + image_view["byteLength"]]
        self.assertEqual(image[:8], b"\x89PNG\r\n\x1a\n")
        offset, pixels = 8, bytearray()
        while offset < len(image):
            length, kind = struct.unpack_from(">I4s", image, offset)
            body = image[offset + 8:offset + 8 + length]
            crc = struct.unpack_from(">I", image, offset + 8 + length)[0]
            self.assertEqual(crc, zlib.crc32(kind + body))
            if kind == b"IDAT":
                pixels.extend(zlib.decompress(body))
            offset += 12 + length
        self.assertEqual(pixels, b"\0" + bytes(range(8)) + b"\0" + bytes(range(8, 16)))
        self.assertEqual(doc["extras"]["source_record"], source["source_record"])
        self.assertEqual(doc["nodes"][0]["extras"]["source_object"]["raw_object_word6"], 123)
        self.assertEqual(audit["texture_count"], 1)
        self.assertEqual(source, original)

    def test_explicit_pose_selection_and_float32_bounds(self):
        source = preview()
        source["frames"] = [{"posed": True, "coordinate_system": "retail_psx_actor_local_y_down",
                             "vertices": [[0.123456789, -4, 0], [2, -4, 0], [0, -2, 0]],
                             "object_transforms": [{"object_index": 0}]}]
        raw, audit = encode_model_glb(source, 0)
        doc, binary = parse_glb(raw)
        position = doc["meshes"][0]["primitives"][0]["attributes"]["POSITION"]
        values = read_accessor(doc, binary, position)
        self.assertEqual(doc["accessors"][position]["max"], [max(v[i] for v in values) for i in range(3)])
        self.assertTrue(audit["posed"])
        self.assertEqual(audit["frame_index"], 0)
        self.assertEqual(values[0][1], 4)
        with self.assertRaisesRegex(ImportError, "frame index"):
            encode_model_glb(source, 1)

    def test_missing_texture_is_explicit_and_colors_are_clamped(self):
        source = preview()
        source["textures"][0]["status"] = "missing"
        raw, audit = encode_model_glb(source)
        doc, binary = parse_glb(raw)
        self.assertNotIn("images", doc)
        self.assertIn("fallback", audit["diagnostics"][0])
        color = doc["meshes"][0]["primitives"][0]["attributes"]["COLOR_0"]
        self.assertAlmostEqual(read_accessor(doc, binary, color)[0][0], ((128 / 255 + .055) / 1.055) ** 2.4)
        source = preview()
        source["triangle_colors"][0][0] = [255, 129, 0]
        raw, audit = encode_model_glb(source)
        doc, binary = parse_glb(raw)
        color = doc["meshes"][0]["primitives"][0]["attributes"]["COLOR_0"]
        self.assertEqual(read_accessor(doc, binary, color)[0], (1, 1, 0))
        self.assertTrue(any("clamped" in s for s in audit["diagnostics"]))

    def test_malformed_geometry_texture_and_ranges_are_rejected(self):
        changes = [lambda p: p["vertices"][0].__setitem__(0, float("nan")),
                   lambda p: p["triangles"][0].__setitem__(1, 999),
                   lambda p: p["objects"][0].__setitem__("triangle_count", 0),
                   lambda p: p["objects"].append(deepcopy(p["objects"][0])),
                   lambda p: p["textures"][0].__setitem__("width", 10000),
                   lambda p: p["textures"][0].__setitem__("rgba_base64", "!"),
                   lambda p: p["triangle_uvs"][0][0].__setitem__(0, 0),
                   lambda p: p.__setitem__("coordinate_system", "already_y_up")]
        for change in changes:
            source = preview()
            change(source)
            with self.subTest(change=change), self.assertRaises(ImportError):
                encode_model_glb(source)

    def test_new_private_export_is_exclusive_and_reparse_paths_are_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "Exports"
            result = write_model_export(preview(), root)
            self.assertEqual(Path(result["path"]).parent, root.resolve())
            parse_glb(Path(result["path"]).read_bytes())
            with patch("importer.export.uuid.uuid4") as new_id:
                new_id.return_value.hex = Path(result["path"]).stem.removeprefix("model-")
                with self.assertRaises(FileExistsError):
                    write_model_export(preview(), root)
            fake = type("Info", (), {"st_mode": 0o40755, "st_file_attributes": 0x400})()
            with patch("importer.export.Path.lstat", return_value=fake):
                with self.assertRaisesRegex(ImportError, "reparse"):
                    write_model_export(preview(), root)


@unittest.skipUnless(os.environ.get("LEGAIA_DISC_BIN"), "requires private retail disc")
class RetailGlbExportTests(unittest.TestCase):
    def test_partial_object_actor_frames_export_through_server_adapter(self):
        from importer.pipeline import import_scene
        from sdk.project import ProjectService
        from sdk.server import EditorServer
        disc = os.environ['LEGAIA_DISC_BIN']
        with tempfile.TemporaryDirectory() as temp:
            for scene,index,objects,triangles in (('station',10,7,290),('balden2',15,1,174)):
                project=ProjectService(Path(temp)/scene)
                project.import_metadata(import_scene(disc,scene),disc)
                server=EditorServer(('127.0.0.1',0),project)
                try:
                    model=server.actor_animation_preview(f'scene://{scene}/actors/man-p1/{index:04d}')
                    original=deepcopy(model)
                    for frame in (0,len(model['frames'])-1):
                        raw,audit=encode_model_glb(model,frame)
                        doc,binary=parse_glb(raw)
                        self.assertEqual((audit['object_count'],audit['triangle_count']),(objects,triangles))
                        self.assertEqual([n['name'] for n in doc['nodes']],[f'object-{i}' for i in range(objects)])
                        exported=sum(doc['accessors'][primitive['attributes']['POSITION']]['count']
                                     for mesh in doc['meshes'] for primitive in mesh['primitives'])
                        self.assertEqual(exported,triangles*3)
                        self.assertNotIn('animations',doc) # Explicit posed snapshot, not a clip export.
                    clip_raw,clip_audit=encode_model_glb(model,clip_fps=15)
                    clip_doc,_=parse_glb(clip_raw)
                    self.assertEqual(len(clip_doc['animations'][0]['channels']),objects*2)
                    self.assertEqual(clip_audit['frame_count'],len(model['frames']))
                    self.assertEqual(clip_audit['object_count'],objects)
                    self.assertEqual(model,original)
                finally:
                    server.server_close()


    def test_actual_party_pose_and_scene_tree_export(self):
        from importer.assets import load_model_preview
        from importer.animation import load_animation_preview
        from importer.pipeline import import_scene
        from importer.textures import load_scene_texture_catalog, load_asset_texture_catalog, associate_material
        disc = os.environ["LEGAIA_DISC_BIN"]
        imported = import_scene(disc, "town01")
        scene_catalog = load_scene_texture_catalog(disc, "town01")
        for suffix, clip, expected in (("/00f0", "idle", (10, 496, 4)), ("/0088", None, (1, 328, 2))):
            asset = next(a for a in imported["assets"]["models"] if a["semantic_id"].endswith(suffix))
            if clip:
                animation = load_animation_preview(disc, asset, clip)
                model = animation.pop("geometry")
                model["frames"] = animation.pop("frames")
                model["animation"] = animation
            else:
                model = load_model_preview(disc, asset)
            textures = load_asset_texture_catalog(disc, asset, scene_catalog)
            model["textures"] = []
            for index, material in enumerate(model["materials"]):
                uv = [v for tri, mi in zip(model["triangle_uvs"], model["triangle_materials"])
                      if mi == index and tri for v in tri]
                if not uv:
                    continue
                bounds = tuple(fn(v[axis] for v in uv) for fn, axis in ((min, 0), (min, 1), (max, 0), (max, 1)))
                model["textures"].append(dict(associate_material(textures, material, bounds), material_index=index))
            raw, audit = encode_model_glb(model, 0 if clip else None)
            doc, _ = parse_glb(raw)
            self.assertEqual((audit["object_count"], audit["triangle_count"], audit["texture_count"]), expected)
            self.assertEqual(len(doc["images"]), expected[2])
            self.assertNotIn("animations", doc)


if __name__ == "__main__":
    unittest.main()
