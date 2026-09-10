"""Read-only field MAP collision and trigger resources from the pinned reference.

Evidence at d6e64c68: engine-core scene/scene_ty.rs (073f3c19...),
world/field_movement.rs (12ce75c6...), field_regions.rs (8f54e888...).
docs/subsystems/field-locomotion.md, Trigger block, establishes all four
table strides (4,4,4,8). world/field_elevation.rs describes kind-2 ramp
adjustments, consistent with generated retail routine 80019278.
This is the source baseline, not a reconstructed live navigation system.
"""
from __future__ import annotations

from hashlib import sha256
import struct
from typing import Any

from .core import ImportError
from .pipeline import REFERENCE_COMMIT, _bounded_scene_range, _disc_context


LIMITATIONS = [
    "Source MAP baseline only; script collision paints, actor blockers and movement probes are not simulated.",
    "Ramp adjustments are relative to the four-corner floor-tier mean, and apply only when the object-cell 0x0800 flag is set; no complete floor heights or walkable mesh are inferred.",
    "Trigger rows are source references, not executed scripts or proven reachable scene transitions.",
    "Primary tables precede fallback tables; duplicate coordinates and source ordering are preserved.",
    "Wall rectangles cover only canonical integer X=1..16384 and Z=0..16255; X=0 aliasing, wrapping X and negative coordinates are excluded.",
    "Other MAP tables, camera zones and unvisited source bytes remain uninterpreted.",
]
DOMAIN = {"x_min": 0, "x_max": 16384, "z_min": 0, "z_max": 16256,
          "x_min_inclusive": False, "x_max_inclusive": True,
          "z_min_inclusive": True, "z_max_inclusive": False,
          "units": "guest_integer_world_units"}


def _validate_scene(scene: Any) -> None:
    if not isinstance(scene, str) or not scene or len(scene) > 128 or any(
            not (c.isascii() and (c.isalnum() or c in "_-")) for c in scene):
        raise ImportError("field map requires a structural scene name")


def _table_rows(block: bytes, kind: int, stride: int) -> tuple[int, list[bytes]]:
    if len(block) != 0x2000:
        raise ImportError("field MAP table block must be exactly 0x2000 bytes")
    offset, count = struct.unpack_from("<hh", block, 4 * kind + 2)
    if offset < 0 or count < 0 or (count and offset < 0x12) or offset + count * stride > len(block):
        raise ImportError(f"field MAP kind-{kind} table has unsupported or truncated bounds")
    return offset, [block[offset + i * stride:offset + (i + 1) * stride] for i in range(count)]


def _rectangles(grid: bytes) -> list[dict]:
    if len(grid) != 128 * 128:
        raise ImportError("field MAP collision grid must contain 16384 bytes")
    rectangles = []
    # Invert the reference's biased wall lookup only in its unambiguous
    # canonical positive-X domain. Integer X endpoints are (min, max],
    # unlike Z's [min, max). Row zero maps below Z=0 and is excluded.
    for row in range(1, 128):
        for column in range(128):
            wall = grid[row * 128 + column] >> 4
            for quadrant in range(4):
                if wall & (1 << quadrant):
                    x = column * 128 + (quadrant & 1) * 64
                    z = row * 128 - 128 + (quadrant >> 1) * 64
                    rectangles.append({"x_min": x, "x_max": x + 64,
                                       "z_min": z, "z_max": z + 64,
                                       "column": column, "row": row, "quadrant": quadrant})
    return rectangles


def _decode(scene: str, digest: str, entry: Any, data: bytes,
            fallback: tuple[Any, bytes] | None) -> tuple[dict, bytes]:
    if len(data) != 0x12000:
        raise ImportError("unsupported field MAP: extended first scene entry is not 0x12000 bytes")
    grid = data[0x4000:0x8000]
    limitations = list(LIMITATIONS)

    def source(record_entry, offset, payload, containing_hash, **extra):
        return {"disc": {"sha256": digest, "serial": "SCUS-94254"},
                "iso_file": "PROT.DAT", "prot_entry_index": record_entry.index, "prot_entry_name": scene,
                "prot_start_lba": record_entry.start_lba,
                "byte_offset": offset, "byte_length": len(payload),
                "byte_coordinate_space": "prot_entry", "sha256": sha256(payload).hexdigest(),
                "containing_span_sha256": containing_hash, **extra}

    map_hash = sha256(data).hexdigest()
    collision = {"semantic_id": f"collision://{scene}/field-map", "asset_kind": "collision",
                 "name": "Field MAP source collision", "scope": "scene", "status": "source_baseline",
                 "preview_supported": True, "grid_width": 128, "grid_height": 128,
                 "cell_size": 128, "subcell_size": 64,
                 "wall_cell_count": sum(bool(v >> 4) for v in grid),
                 "blocked_subcell_count": sum((v >> 4).bit_count() for v in grid),
                 "floor_tier_counts": [sum((v & 15) == tier for v in grid) for tier in range(16)],
                 "source_record": source(entry, 0x4000, grid, map_hash, containing_span_byte_offset=0,
                                         containing_span_byte_length=len(data)),
                 "reference_commit": REFERENCE_COMMIT, "limitations": list(limitations)}
    assets = [collision]
    collision["elevation_overrides"] = []
    tables = [("primary", entry, data[0x10000:], 0x10000, (0, 1, 3))]
    if fallback is not None:
        tables.append(("fallback", fallback[0], fallback[1], 0, (1,)))
    else:
        limitations.append("Fallback trigger table unavailable: no bounded contiguous next scene entry.")
    for table_name, table_entry, block, base, kinds in tables:
        table_hash = sha256(block).hexdigest()
        spans = []
        decoded_tables = {}
        # The pinned locomotion format describes strides for every kind.
        # Validate even unexposed tables so they cannot alias emitted rows.
        for kind in range(4):
            stride = 8 if kind == 3 else 4
            offset, rows = _table_rows(block, kind, stride)
            end = offset + len(rows) * stride
            if rows and any(offset < other_end and other_start < end for other_start, other_end in spans):
                raise ImportError("field MAP known tables overlap ambiguously")
            if rows:
                spans.append((offset, end))
            decoded_tables[kind] = offset, rows
        offset, rows = decoded_tables[2]
        for index, row in enumerate(rows):
            x, z, coarse, quads = struct.unpack("<BBbB", row)
            # Each quadrant is a 64-unit subcell; PSX field Y increases down.
            # Preserve duplicate rows in primary/fallback order: first hit wins.
            deltas = [-32 * coarse - 16 * ((quads >> shift) & 3)
                      for shift in (0, 2, 4, 6)]
            collision["elevation_overrides"].append({
                "table_source": table_name, "record_index": index,
                "tile_x": x, "tile_z": z, "coarse_signed": coarse,
                "packed_subcell_steps": quads, "subcell_delta_y": deltas,
                "source_record": source(table_entry, base + offset + index * 4, row, table_hash,
                                        table_source=table_name, table_kind=2, record_index=index,
                                        containing_span_byte_offset=base, containing_span_byte_length=len(block)),
            })
        for kind in kinds:
            stride = 8 if kind == 3 else 4
            offset, rows = decoded_tables[kind]
            for index, row in enumerate(rows):
                is_region = kind == 3
                identifier = (f"region://{scene}/field-map/{table_name}/{index:04d}" if is_region else
                              f"trigger://{scene}/field-map/{table_name}/kind-{kind}/{index:04d}")
                asset = {"semantic_id": identifier, "asset_kind": "region" if is_region else "trigger",
                         "name": f"{table_name.title()} {'region' if is_region else 'kind-' + str(kind)} {index}",
                         "table_source": table_name, "table_kind": kind, "record_index": index,
                         "status": "decoded_source_record", "preview_supported": False,
                         "collision_id": collision["semantic_id"], "reference_commit": REFERENCE_COMMIT,
                         "source_record": source(table_entry, base + offset + index * stride, row, table_hash,
                                                 table_source=table_name, table_kind=kind, record_index=index,
                                                 containing_span_byte_offset=base, containing_span_byte_length=len(block)),
                         "limitations": [LIMITATIONS[2], LIMITATIONS[3]]}
                if is_region:
                    x0, z0, x1, z1, region_type = row[:5]
                    xmin, xmax, zmin, zmax = min(x0, x1), max(x0, x1), min(z0, z1), max(z0, z1)
                    if xmin == xmax:
                        xmax += 2
                    if zmin == zmax:
                        zmin -= 2
                    asset.update(encoded={"x0": x0, "z0": z0, "x1": x1, "z1": z1, "type": region_type},
                                 tile_bounds={"x_min": xmin, "x_max": xmax, "z_min": zmin, "z_max": zmax},
                                 bounds_semantics="half_open_tile_coordinates")
                else:
                    x, z, a, b = row
                    encoded = {"tile_x": x, "tile_z": z}
                    if kind == 0:
                        encoded.update(dest_x=a, dest_z=b)
                        asset.update(trigger_type="intra_scene_teleport",
                                     destination_world={"x": a * 64 + 64, "z": (b + 1) * 64},
                                     destination_scene=None)
                    else:
                        encoded.update(record_index=a, gate=b)
                        asset.update(trigger_type={0: "object_bind", 1: "partition_2_trigger"}.get(b, "unknown_gate"),
                                     script_reference={"partition": {0: 0, 1: 2}.get(b), "record_index": a,
                                                       "status": "unresolved_source_reference"})
                        if b not in (0, 1):
                            asset["status"] = "unknown_gate"
                    asset["encoded"] = encoded
                assets.append(asset)
    collision["elevation_override_count"] = len(collision["elevation_overrides"])
    return {"schema_version": "legaia.field-map-assets.v1", "scene": scene, "disc_sha256": digest,
            "reference_commit": REFERENCE_COMMIT, "assets": assets, "limitations": limitations}, grid


def _load(disc: Any, scene: str) -> tuple[dict, bytes]:
    _validate_scene(scene)
    with _disc_context(disc) as (_, digest, mapping, archive):
        start, end = _bounded_scene_range(archive, mapping, scene)
        entry = archive.entry(start)
        if entry.size_sectors * archive.SECTOR != 0x12000:
            raise ImportError("unsupported field MAP: first scene entry extended footprint is not 0x12000")
        data = archive.read_entry(entry, extended=True)
        fallback = None
        if start + 1 < end:
            following = archive.entry(start + 1)
            if following.start_lba == entry.start_lba + 36 and following.size_sectors >= 4:
                block = archive.image.read_user(archive.node.extent_lba, following.start_lba * archive.SECTOR,
                                               0x2000, archive.node.size)
                fallback = following, block
        return _decode(scene, digest, entry, data, fallback)


def load_field_map_catalog(disc: Any, scene: str = "town01") -> dict:
    """Return deterministic metadata only; never publish the source grid here."""
    return _load(disc, scene)[0]


def preview_field_map(disc: Any, scene: str, asset_id: str) -> dict:
    """Freshly resolve the scene collision ID and emit bounded private rectangles."""
    _validate_scene(scene)
    if not isinstance(asset_id, str) or asset_id != f"collision://{scene}/field-map":
        raise ImportError("field MAP preview requires this scene's collision asset identifier")
    catalog, grid = _load(disc, scene)
    rectangles = _rectangles(grid)
    return {"asset": catalog["assets"][0], "coordinate_system": "psx_guest_xz",
            "rectangles": rectangles, "domain": dict(DOMAIN),
            "rectangle_count": len(rectangles),
            "excluded_subcell_count": catalog["assets"][0]["blocked_subcell_count"] - len(rectangles),
            "rectangle_bounds_semantics": "x_min < integer_x <= x_max; z_min <= integer_z < z_max",
            "triggers": [a for a in catalog["assets"] if a["asset_kind"] == "trigger"],
            "regions": [a for a in catalog["assets"] if a["asset_kind"] == "region"],
            "limitations": catalog["limitations"]}
