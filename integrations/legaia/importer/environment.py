"""Imported field environment placements, separate from MAN actors.

Pinned evidence: asset/field_objects.rs::parse_placements and
engine-core/scene/scene_ty.rs::field_floor_height_lut. This enumerates both
placed-object sweeps; it does not claim runtime window visibility or bindings.
Ground/decorations are different consumers and are not included here.
"""
from hashlib import sha256
import struct

from .core import ImportError, decompress_lzs, find_scene_bundle, parse_man
from .field_map import _validate_scene
from .pipeline import REFERENCE_COMMIT, _bounded_scene_range, _disc_context


def decode_environment_placements(data: bytes, man: bytes, scene: str) -> dict:
    _validate_scene(scene)
    if not isinstance(data, bytes) or len(data) != 0x12000:
        raise ImportError("environment requires the complete 0x12000-byte field MAP")
    parse_man(man, scene)
    floor_lut = struct.unpack_from("<16h", man, 2)
    placements, excluded = [], []
    for cell_index in range(128 * 128):
        col, row = cell_index % 128, cell_index // 128
        grid_offset = 0x8000 + cell_index * 2
        cell = struct.unpack_from("<H", data, grid_offset)[0]
        record_index = cell & 0x1FF
        offset = record_index * 32
        flags = struct.unpack_from("<H", data, offset + 0x12)[0]
        if not flags & 4:
            continue
        x, y, z, dx, dz = struct.unpack_from("<hhhbb", data, offset)
        anchor_x, anchor_z = col + dx, row + dz
        identifier = f"environment://{scene}/field-map/cells/{cell_index:05d}"
        if not 0 <= anchor_x < 128 or not 0 <= anchor_z < 128:
            excluded.append({"semantic_id": identifier, "reason": "footprint_anchor_outside_grid"})
            continue
        anchor_cell = struct.unpack_from("<H", data, 0x8000 + (anchor_z * 128 + anchor_x) * 2)[0]
        # Reference implementation reads the placement cell, despite its
        # floor_nibble field comment saying anchor. Preserve that distinction.
        tier = data[0x4000 + cell_index] & 15
        rotations = struct.unpack_from("<3H", data, offset + 8)
        placements.append({
            "semantic_id": identifier, "asset_kind": "environment_placement",
            "name": f"MAP object {record_index} at {col},{row}",
            "tile": {"x": col, "z": row}, "object_record_index": record_index,
            "source_record": {"grid_byte_offset": grid_offset, "grid_byte_length": 2,
                              "object_byte_offset": offset, "object_byte_length": 32,
                              "object_sha256": sha256(data[offset:offset + 32]).hexdigest()},
            "imported_transform": {"position": {"x": col * 128 + x + 64,
                                                   "y": -floor_lut[tier] + y,
                                                   "z": row * 128 - z + 64},
                                   "rotation_psx": dict(zip("xyz", rotations)),
                                   "coordinate_system": "retail_field_y_down"},
            "floor": {"tier": tier, "lut_value": floor_lut[tier], "record_y_offset": y,
                      "sample": "placement_cell_not_footprint_anchor"},
            "footprint_anchor": {"x": anchor_x, "z": anchor_z, "cell_word": anchor_cell,
                                 "bind_owned": bool(anchor_cell & 0x400)},
            "flags": flags, "mesh_drawn_flag": bool(flags & 2),
            "pack_index": None if record_index in (1, 2, 3) else struct.unpack_from("<H", data, offset + 16)[0],
            "model_resolution": "not_resolved", "animation_binding": "not_resolved",
        })
    return {"schema_version": "legaia.environment-placements.v1", "scene": scene,
            "reference_commit": REFERENCE_COMMIT, "placements": placements,
            "excluded": excluded, "floor_height_lut": list(floor_lut),
            "limitations": ["Placed-object source baseline only; ground and decorations are separate layers.",
                            "Mesh pack and MAN partition-0 animation bindings are not resolved here.",
                            "Source placements do not imply current runtime visibility or spawn state."]}


def _load_environment_source(disc, scene: str):
    """Read source-controlled locations; never accept client-provided offsets."""
    _validate_scene(scene)
    with _disc_context(disc) as (_, digest, mapping, archive):
        start, end = _bounded_scene_range(archive, mapping, scene)
        entry = archive.entry(start)
        if entry.size_sectors * archive.SECTOR != 0x12000:
            raise ImportError("scene does not have the supported full field MAP footprint")
        data = archive.read_entry(entry, extended=True)
        bundle, raw = find_scene_bundle(archive, start, end)
        candidates = [d for d in bundle.descriptors if d.type_byte == 3 and d.size > 0]
        if len(candidates) != 1:
            raise ImportError("environment requires one unambiguous scene MAN descriptor")
        descriptor = candidates[0]
        if descriptor.size > 4 * 1024 * 1024:
            raise ImportError("environment MAN exceeds decoded byte bound")
        if sum(d.size > 0 and d.data_offset == descriptor.data_offset for d in bundle.descriptors) != 1:
            raise ImportError("environment MAN descriptor aliases another resource")
        offset = bundle.table_offset + descriptor.data_offset
        ceiling = min([bundle.table_offset + d.data_offset for d in bundle.descriptors
                       if d.data_offset > descriptor.data_offset] + [len(raw)])
        if not bundle.table_offset + 8 + len(bundle.descriptors) * 8 <= offset < ceiling <= len(raw):
            raise ImportError("environment MAN stream exceeds descriptor boundaries")
        man, consumed = decompress_lzs(raw[offset:ceiling], descriptor.size)
        result = decode_environment_placements(data, man, scene)
        result["source_record"] = {"disc_sha256": digest, "iso_file": "PROT.DAT",
                                   "map_entry_index": entry.index, "map_sha256": sha256(data).hexdigest(),
                                   "map_byte_length": len(data), "man_entry_index": bundle.entry_index,
                                   "man_descriptor_index": descriptor.index,
                                   "man_stream_offset": offset, "man_stream_bytes_consumed": consumed,
                                   "man_sha256": sha256(man).hexdigest()}
        return result, man, bundle, raw


def load_environment_placements(disc, scene: str) -> dict:
    return _load_environment_source(disc, scene)[0]


def _prop_record(man: bytes, index: int) -> dict:
    """Bound one partition-0 header using every record and section boundary."""
    from collections import Counter
    parsed = parse_man(man)
    if type(index) is not int or not 0 <= index < parsed.partition_counts[0]:
        raise ImportError("environment bind is outside MAN partition 0")
    total = sum(parsed.partition_counts)
    region = 0x2B + total * 3
    starts = [region + int.from_bytes(man[0x2B + i * 3:0x2E + i * 3], "little") for i in range(total)]
    if any(not region <= start < len(man) for start in starts):
        raise ImportError("environment MAN record table contains invalid offsets")
    start = starts[index]
    if Counter(starts)[start] != 1:
        raise ImportError("environment bind MAN record is aliased")
    section = region + int.from_bytes(man[0x28:0x2B], "little")
    sections = []
    for _ in range(6):
        end = section + 3 + int.from_bytes(man[section:section + 3], "little")
        sections.append((section, end))
        section = end
    end = min(p for p in starts + [a for a, _ in sections] + [len(man)] if p > start)
    if any(start < b and a < end for a, b in sections):
        raise ImportError("environment bind MAN record intersects a section")
    anim_offset = start + 1 + man[start] * 2
    if anim_offset >= end:
        raise ImportError("environment bind animation header is truncated")
    return {"record_index": index, "byte_offset": start, "byte_length": end - start,
            "sha256": sha256(man[start:end]).hexdigest(), "animation_id": man[anim_offset],
            "script_offset": anim_offset + 1 - start}


def load_environment_catalog(disc, scene: str) -> dict:
    """Resolve imported geometry identities and initial prop bindings.

    Pack selection follows the pinned reference's largest scene-entry pool
    heuristic. Expose that inference rather than presenting it as live proof.
    """
    from collections import Counter
    from .field_map import load_field_map_catalog
    from .pipeline import import_scene
    with _disc_context(disc):
        result, man, _, _ = _load_environment_source(disc, scene)
        document = import_scene(disc, scene)
        if document["source"]["disc_identity"] != "sha256:" + result["source_record"]["disc_sha256"]:
            raise ImportError("environment source identity changed during resolution")
        models = [a for a in document["assets"]["models"] if a["scope"] == "scene"]
        counts = Counter(a["source_record"]["prot_entry_index"] for a in models)
        if not counts:
            raise ImportError("environment has no scene-owned model pool")
        winner = min(counts, key=lambda entry: (-counts[entry], entry))
        pool = [a for a in models if a["source_record"]["prot_entry_index"] == winner]
        result["mesh_pool"] = {"prot_entry_index": winner, "model_count": len(pool),
                               "selection_evidence": "reference_largest_entry_pool_heuristic",
                               "confidence": "inferred"}
        triggers = load_field_map_catalog(disc, scene)
        if triggers["disc_sha256"] != result["source_record"]["disc_sha256"]:
            raise ImportError("environment trigger source identity changed")
        binds = {}
        for trigger in triggers["assets"]:
            if trigger.get("table_kind") != 1:
                continue
            encoded = trigger["encoded"]
            # Init binding ignores the dispatch gate. Primary source order
            # wins, including malformed first matches; do not fall through.
            binds.setdefault((encoded["tile_x"], encoded["tile_z"]), trigger)
        for placement in result["placements"]:
            index = placement["pack_index"]
            if index is not None and 0 <= index < len(pool):
                placement["model_resolution"] = "reference_pool_resolved"
                placement["model_asset_id"] = pool[index]["semantic_id"]
            else:
                placement["model_resolution"] = "unsupported_pool_index"
            anchor = placement["footprint_anchor"]
            trigger = binds.get((anchor["x"], anchor["z"]))
            if trigger is None:
                placement["animation_binding"] = "missing_owned_bind" if anchor["bind_owned"] else "unbound_static"
                placement["animation_id"] = None if anchor["bind_owned"] else 0
                continue
            try:
                record = _prop_record(man, trigger["encoded"]["record_index"])
                placement.update(animation_binding="imported_partition0_header", animation_id=record["animation_id"],
                                 script_binding={"semantic_id": f"script://{scene}/scripts/man-p0/{record['record_index']:04d}",
                                                 "source_record": record, "trigger_id": trigger["semantic_id"]})
            except ImportError as exc:
                placement.update(animation_binding="unsupported", animation_id=None, binding_reason=str(exc))
        result["limitations"][1] = "Mesh pool selection uses the pinned reference heuristic; initial prop bindings do not evaluate scripts."
        return result


class EnvironmentPreviewCatalog:
    """Request-scoped, verified environment bindings and source geometry."""
    def __init__(self, disc, metadata, models, anm):
        from .animation import animation_record_ranges
        self.disc, self.metadata, self._anm = disc, metadata, anm
        self._placements = {p["semantic_id"]: p for p in metadata["placements"]}
        self._models = {a["semantic_id"]: a for a in models}
        self._ranges = animation_record_ranges(anm)

    def pose_preview(self, identifier: str, frame_index: int = 0) -> dict:
        from copy import deepcopy
        from .animation import decode_animation_record, pose_vertices, _bounds
        from .assets import load_model_preview
        placement = self._placements.get(identifier)
        if placement is None:
            raise ImportError("environment identity is not in the verified catalog")
        if type(frame_index) is not int or frame_index < 0:
            raise ImportError("environment frame index must be a nonnegative integer")
        asset = self._models.get(placement.get("model_asset_id"))
        anim = placement.get("animation_id")
        if asset is None or anim is None:
            raise ImportError("environment mesh or prop binding remains unsupported")
        geometry = load_model_preview(self.disc, asset)
        pose = {"environment_id": identifier, "animation_id": anim,
                "frame_index": frame_index, "binding": deepcopy(placement.get("script_binding")),
                "kind": "unposed_static"}
        if anim:
            if not 1 <= anim <= len(self._ranges):
                raise ImportError("environment animation ID exceeds scene bank")
            start, end = self._ranges[anim - 1]
            raw = self._anm[start:end]
            decoded = decode_animation_record(raw)
            if not frame_index < decoded["frame_count"]:
                raise ImportError("environment frame index exceeds clip")
            if decoded["bone_count"] != len(geometry["objects"]):
                raise ImportError("environment animation channel count differs from mesh")
            transforms = decoded["frames"][frame_index]["object_transforms"]
            geometry["vertices"] = pose_vertices(geometry["vertices"], geometry["objects"], transforms)
            pose.update(kind="imported_prop_animation", animation_record_index=anim - 1,
                        animation_record_sha256=sha256(raw).hexdigest(), frame_count=decoded["frame_count"],
                        object_transforms=deepcopy(transforms))
        elif frame_index:
            raise ImportError("unposed environment object has only frame zero")
        geometry.update(bounds=_bounds(geometry["vertices"]), pose=pose,
                        posed=bool(anim), coordinate_system="retail_psx_actor_local_y_down")
        return geometry


def load_environment_preview_catalog(disc, scene: str) -> EnvironmentPreviewCatalog:
    from .pipeline import import_scene
    with _disc_context(disc):
        metadata = load_environment_catalog(disc, scene)
        source, _, bundle, raw = _load_environment_source(disc, scene)
        if source["source_record"] != metadata["source_record"]:
            raise ImportError("environment source changed during preview resolution")
        document = import_scene(disc, scene)
        if document["source"]["disc_identity"] != "sha256:" + source["source_record"]["disc_sha256"]:
            raise ImportError("environment mesh disc identity changed")
        candidates = [d for d in bundle.descriptors if d.type_byte == 5 and d.size > 0]
        if len(candidates) != 1:
            raise ImportError("environment preview requires one scene animation descriptor")
        descriptor = candidates[0]
        if descriptor.size > 4 * 1024 * 1024:
            raise ImportError("environment animation bank exceeds byte bound")
        if sum(d.size > 0 and d.data_offset == descriptor.data_offset for d in bundle.descriptors) != 1:
            raise ImportError("environment animation descriptor aliases another resource")
        offset = bundle.table_offset + descriptor.data_offset
        ceiling = min([bundle.table_offset + d.data_offset for d in bundle.descriptors
                       if d.data_offset > descriptor.data_offset] + [len(raw)])
        if not bundle.table_offset + 8 + len(bundle.descriptors) * 8 <= offset < ceiling <= len(raw):
            raise ImportError("environment animation stream exceeds descriptor boundaries")
        anm, _ = decompress_lzs(raw[offset:ceiling], descriptor.size)
        return EnvironmentPreviewCatalog(disc, metadata, document["assets"]["models"], anm)
