"""Exact primary field MAP region-corner writes against immutable source bytes.

Evidence: d6e64c68, engine-core/src/field_regions.rs, RegionTable::parse/scan.
The primary kind-3 table contains [x0, z0, x1, z1, type, pad x3] rows.
Only its four corner bytes are writable here. Type, opaque padding, source
ordering and every other MAP byte remain unchanged. The derived bounds use
the existing importer convention; no runtime height or activation is asserted.
"""
from __future__ import annotations

from hashlib import sha256
from typing import Any

from .core import ImportError
from .field_map import _table_rows, _validate_scene


MAP_SIZE = 0x12000
PRIMARY_BLOCK_OFFSET = 0x10000
BLOCK_SIZE = 0x2000
REGION_STRIDE = 8
MAX_REGION_RECORDS = (BLOCK_SIZE - 0x12) // REGION_STRIDE
CORNER_FIELDS = ("x0", "z0", "x1", "z1")


def _tile_bounds(x0: int, z0: int, x1: int, z1: int) -> dict[str, int]:
    x_min, x_max = min(x0, x1), max(x0, x1)
    z_min, z_max = min(z0, z1), max(z0, z1)
    if x_min == x_max:
        x_max += 2
    if z_min == z_max:
        z_min -= 2
    return {"x_min": x_min, "x_max": x_max, "z_min": z_min, "z_max": z_max}


def region_authoring_options(original: bytes, scene: str) -> dict[str, Any]:
    """Return detached, metadata-only bindings for the supported primary rows."""
    _validate_scene(scene)
    if not isinstance(original, bytes) or len(original) != MAP_SIZE:
        raise ImportError("Region authoring requires the supported 0x12000-byte MAP")
    block = original[PRIMARY_BLOCK_OFFSET:]
    tables: dict[int, tuple[int, list[bytes]]] = {}
    spans: list[tuple[int, int]] = []
    for kind in range(4):
        stride = REGION_STRIDE if kind == 3 else 4
        offset, rows = _table_rows(block, kind, stride)
        end = offset + len(rows) * stride
        if rows and any(offset < other_end and other_start < end
                        for other_start, other_end in spans):
            raise ImportError("field MAP known tables overlap ambiguously")
        if rows:
            spans.append((offset, end))
        tables[kind] = offset, rows
    offset, rows = tables[3]
    if len(rows) > MAX_REGION_RECORDS:
        raise ImportError("Primary field MAP region count exceeds supported bounds")
    records = []
    for index, row in enumerate(rows):
        x0, z0, x1, z1, region_type = row[:5]
        records.append({
            "region_id": f"region://{scene}/field-map/primary/{index:04d}",
            "record_index": index,
            "byte_offset": PRIMARY_BLOCK_OFFSET + offset + index * REGION_STRIDE,
            "byte_length": REGION_STRIDE,
            "sha256": sha256(row).hexdigest(),
            "encoded": {"x0": x0, "z0": z0, "x1": x1, "z1": z1,
                        "type": region_type},
            "tile_bounds": _tile_bounds(x0, z0, x1, z1),
        })
    return {"source_sha256": sha256(original).hexdigest(), "records": records}


def patch_field_regions(original: bytes, expected_sha256: str, scene: str,
                        edits: list[dict]) -> tuple[bytes, list[dict]]:
    """Patch only qualified region corners and audit every changed byte."""
    options = region_authoring_options(original, scene)
    if not isinstance(expected_sha256, str) or expected_sha256 != options["source_sha256"]:
        raise ImportError("Region MAP source hash differs from the authored binding")
    if not isinstance(edits, list) or len(edits) > MAX_REGION_RECORDS:
        raise ImportError(f"Region authoring accepts at most {MAX_REGION_RECORDS} edits")
    records = {row["region_id"]: row for row in options["records"]}
    seen: set[str] = set()
    qualified = []
    for edit in edits:
        if not isinstance(edit, dict) or set(edit) != {"region_id", *CORNER_FIELDS}:
            raise ImportError("Region edits require region_id and x0, z0, x1, z1 only")
        identifier = edit["region_id"]
        if not isinstance(identifier, str) or identifier not in records:
            raise ImportError("Region edit requires an existing primary row in this scene")
        if identifier in seen:
            raise ImportError("Duplicate primary field MAP region edit")
        seen.add(identifier)
        for field in CORNER_FIELDS:
            if type(edit[field]) is not int or not 0 <= edit[field] <= 255:
                raise ImportError(f"Region {field} must be an integer byte in 0..255")
        qualified.append((records[identifier], edit))

    result = bytearray(original)
    audit = []
    for record, edit in sorted(qualified, key=lambda pair: pair[0]["record_index"]):
        for delta, field in enumerate(CORNER_FIELDS):
            offset = record["byte_offset"] + delta
            before, after = original[offset], edit[field]
            if before == after:
                continue
            result[offset] = after
            audit.append({
                "region_id": record["region_id"],
                "record_index": record["record_index"],
                "field": f"region.{field}",
                "byte_offset": offset,
                "before_value": before,
                "after_value": after,
                "scope": "source-MAP-region-bounds-only",
            })
    differences = {offset: (before, after)
                   for offset, (before, after) in enumerate(zip(original, result))
                   if before != after}
    audited = {row["byte_offset"]: (row["before_value"], row["after_value"])
               for row in audit}
    if len(result) != len(original) or differences != audited or len(audited) != len(audit):
        raise ImportError("Region patch altered an unaudited byte")
    return bytes(result), audit
