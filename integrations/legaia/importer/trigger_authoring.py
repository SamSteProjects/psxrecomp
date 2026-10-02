"""Exact primary MAP trigger-cell writes against immutable retail source bytes.

Pinned evidence d6e64c68: field_regions.rs parses four-byte kind-0/1 rows;
lookup_tile_trigger compares their first two coordinate bytes independently
of gate meaning. Unknown gate bytes remain unknown and are never changed.
This serializer does not paint object-cell flags, resolve/rebind scripts,
change teleport destinations, or assert runtime activation/floor heights.
"""
from __future__ import annotations

from hashlib import sha256
from typing import Any

from .core import ImportError
from .field_map import _table_rows, _validate_scene


MAP_SIZE = 0x12000
PRIMARY_BLOCK_OFFSET = 0x10000
BLOCK_SIZE = 0x2000
TRIGGER_STRIDE = 4
MAX_PRIMARY_TRIGGER_RECORDS = (BLOCK_SIZE - 0x12) // TRIGGER_STRIDE
COORDINATE_FIELDS = ("tile_x", "tile_z")


def trigger_authoring_options(original: bytes, scene: str) -> dict[str, Any]:
    """Return detached metadata for existing primary kind-0/1 source rows."""
    _validate_scene(scene)
    if not isinstance(original, bytes) or len(original) != MAP_SIZE:
        raise ImportError("Trigger authoring requires the supported 0x12000-byte MAP")
    block = original[PRIMARY_BLOCK_OFFSET:]
    tables: dict[int, tuple[int, list[bytes]]] = {}
    spans: list[tuple[int, int]] = []
    for kind in range(4):
        stride = 8 if kind == 3 else TRIGGER_STRIDE
        offset, rows = _table_rows(block, kind, stride)
        end = offset + len(rows) * stride
        if rows and any(offset < other_end and other_start < end
                        for other_start, other_end in spans):
            raise ImportError("field MAP known tables overlap ambiguously")
        if rows:
            spans.append((offset, end))
        tables[kind] = offset, rows
    if sum(len(tables[kind][1]) for kind in (0, 1)) > MAX_PRIMARY_TRIGGER_RECORDS:
        raise ImportError("Primary field MAP trigger count exceeds supported bounds")
    records = []
    for kind in (0, 1):
        offset, rows = tables[kind]
        for index, row in enumerate(rows):
            x, z, first, second = row
            encoded = {"tile_x": x, "tile_z": z}
            encoded.update({"dest_x": first, "dest_z": second} if kind == 0 else
                           {"record_index": first, "gate": second})
            records.append({
                "trigger_id": f"trigger://{scene}/field-map/primary/kind-{kind}/{index:04d}",
                "table_kind": kind,
                "record_index": index,
                "byte_offset": PRIMARY_BLOCK_OFFSET + offset + index * TRIGGER_STRIDE,
                "byte_length": TRIGGER_STRIDE,
                "sha256": sha256(row).hexdigest(),
                "encoded": encoded,
                "tile_bounds": {"x_min": x, "x_max": x + 1, "z_min": z, "z_max": z + 1},
            })
    return {"source_sha256": sha256(original).hexdigest(), "records": records}


def patch_field_triggers(original: bytes, expected_sha256: str, scene: str,
                         edits: list[dict]) -> tuple[bytes, list[dict]]:
    """Patch only primary trigger X/Z cells and audit every changed byte."""
    options = trigger_authoring_options(original, scene)
    if not isinstance(expected_sha256, str) or expected_sha256 != options["source_sha256"]:
        raise ImportError("Trigger MAP source hash differs from the authored binding")
    if not isinstance(edits, list) or len(edits) > MAX_PRIMARY_TRIGGER_RECORDS:
        raise ImportError(f"Trigger authoring accepts at most {MAX_PRIMARY_TRIGGER_RECORDS} edits")
    records = {row["trigger_id"]: row for row in options["records"]}
    seen: set[str] = set()
    qualified = []
    for edit in edits:
        if not isinstance(edit, dict) or set(edit) != {"trigger_id", *COORDINATE_FIELDS}:
            raise ImportError("Trigger cell edits require trigger_id, tile_x and tile_z only")
        identifier = edit["trigger_id"]
        if not isinstance(identifier, str) or identifier not in records:
            raise ImportError("Trigger edit requires an existing primary kind-0/1 row in this scene")
        if identifier in seen:
            raise ImportError("Duplicate primary field MAP trigger edit")
        seen.add(identifier)
        for field in COORDINATE_FIELDS:
            if type(edit[field]) is not int or not 0 <= edit[field] <= 255:
                raise ImportError(f"Trigger {field} must be an integer byte in 0..255")
        qualified.append((records[identifier], edit))
    result = bytearray(original)
    audit = []
    for record, edit in sorted(qualified, key=lambda pair: (pair[0]["table_kind"], pair[0]["record_index"])):
        for delta, field in enumerate(COORDINATE_FIELDS):
            offset = record["byte_offset"] + delta
            before, after = original[offset], edit[field]
            if before == after:
                continue
            result[offset] = after
            audit.append({
                "trigger_id": record["trigger_id"],
                "table_kind": record["table_kind"],
                "record_index": record["record_index"],
                "field": f"trigger.{field}",
                "byte_offset": offset,
                "before_value": before,
                "after_value": after,
                "scope": "source-MAP-trigger-cell-only",
            })
    differences = {offset: (before, after)
                   for offset, (before, after) in enumerate(zip(original, result)) if before != after}
    audited = {row["byte_offset"]: (row["before_value"], row["after_value"]) for row in audit}
    if len(result) != len(original) or differences != audited or len(audited) != len(audit):
        raise ImportError("Trigger patch altered an unaudited byte")
    return bytes(result), audit
