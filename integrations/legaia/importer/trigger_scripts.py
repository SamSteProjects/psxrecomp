"""Private, bounded inspection of freshly resolved MAP gate-1 MAN P2 scripts.

Pinned d6e64c68 evidence: asset/man_edit.rs::p2_pc0 and record_starts,
blob 7e35fc570fb448072005a8a7588d9e34ebbb3da0; engine-core/field_regions.rs,
blob 8f54e88895ecdf0ca3fe1fc5602ce583911c5feb. This adapter does not expand
the existing opcode decoder or run the P2 dispatcher's story-flag gates.
"""
from __future__ import annotations

from collections import Counter
from copy import deepcopy
from hashlib import sha256
import struct
from typing import Any

from .core import ImportError, decompress_lzs, find_scene_bundle
from .field_map import load_field_map_catalog
from .pipeline import REFERENCE_COMMIT, _bounded_scene_range, _disc_context
from .script_inspection import MAX_RECORD_BYTES, inspect_record

MAX_MAN_BYTES = 4 * 1024 * 1024
MAX_RECORDS = 8192
LIMITATIONS = [
    "Read-only source inspection; no guest writes, execution, script authoring or story-flag evaluation.",
    "Gate-1 references identify MAN partition-2 records; no current trigger activation or reachable destination is inferred.",
    "Only supported encoded continuations are followed; unknown opcodes stop paths and opaque bytes are never scanned.",
    "The P2 prefix and dispatch-gate arrays are bounded structurally, not interpreted as a name or evaluated condition.",
    "Aliased records and records intersecting MAN sections are unsupported; all partition starts constrain the inspected span.",
]


def _u24(data: bytes, offset: int) -> int:
    if not 0 <= offset <= len(data) - 3:
        raise ImportError("MAN 24-bit field exceeds its source span")
    return int.from_bytes(data[offset:offset + 3], "little")


def _p2_record(man: bytes, index: int) -> tuple[int, bytes]:
    if not isinstance(man, bytes) or not 0x2B <= len(man) <= MAX_MAN_BYTES:
        raise ImportError("trigger MAN payload is truncated or exceeds the bounded source size")
    counts = struct.unpack_from("<hhh", man, 0x22)
    if any(count < 0 for count in counts) or sum(counts) > MAX_RECORDS:
        raise ImportError("trigger MAN partition counts are invalid or exceed the record budget")
    if type(index) is not int or not 0 <= index < counts[2]:
        raise ImportError("trigger MAN partition-2 record index is outside the verified table")
    total = sum(counts)
    region = 0x2B + total * 3
    if region > len(man):
        raise ImportError("trigger MAN record-offset table is truncated")
    starts = [region + _u24(man, 0x2B + 3 * i) for i in range(total)]
    if any(not region <= start < len(man) for start in starts):
        raise ImportError("trigger MAN has out-of-bounds record starts")
    section = region + _u24(man, 0x28)
    sections = []
    for _ in range(6):
        end = section + 3 + _u24(man, section)
        if end > len(man):
            raise ImportError("trigger MAN section extends outside the decoded payload")
        sections.append((section, end))
        section = end
    start = starts[counts[0] + counts[1] + index]
    if Counter(starts)[start] != 1:
        raise ImportError("trigger MAN target record is aliased across the record table")
    end = min(candidate for candidate in starts + [a for a, _ in sections] + [len(man)] if candidate > start)
    if any(start < section_end and section_start < end for section_start, section_end in sections):
        raise ImportError("trigger MAN target record overlaps a section")
    if not 0 < end - start <= MAX_RECORD_BYTES:
        raise ImportError("trigger MAN target exceeds the bounded script record size")
    return start, man[start:end]


def _p2_entry(record: bytes) -> tuple[int, dict]:
    cursor = 0
    header = {}
    for label, stride in (("prefix_word_count", 2), ("c0_count", 1), ("c1_count", 2), ("c2_count", 2)):
        if cursor >= len(record):
            raise ImportError(f"partition-2 {label} header is truncated")
        count = record[cursor]
        cursor += 1 + count * stride
        if cursor > len(record):
            raise ImportError(f"partition-2 {label} payload crosses the bounded record")
        header[label] = count
    return cursor, header


def _inspect(man: bytes, scene: str, index: int) -> tuple[dict, dict]:
    offset, data = _p2_record(man, index)
    entry, header = _p2_entry(data)
    identity = f"script://{scene}/scripts/man-p2/{index:04d}"
    record = {"byte_offset": offset, "byte_length": len(data), "script_offset": entry,
              "sha256": sha256(data).hexdigest(), "header": header}
    return record, inspect_record(data, entry, semantic_id=identity, base_offset=offset)


def inspect_trigger_script(disc: Any, scene: str, trigger_id: str) -> dict:
    """Resolve a fresh catalog trigger ID; accept no client record/source bindings."""
    if not isinstance(trigger_id, str) or not trigger_id.startswith("trigger://") or len(trigger_id) > 512:
        raise ImportError("trigger inspection requires a structural trigger identifier")
    with _disc_context(disc) as (_, digest, mapping, archive):
        catalog = load_field_map_catalog(disc, scene)
        trigger = next((a for a in catalog["assets"] if a["semantic_id"] == trigger_id), None)
        if trigger is None or trigger.get("asset_kind") != "trigger":
            raise ImportError("trigger identifier is absent from the verified scene catalog")
        encoded = trigger.get("encoded", {})
        if trigger.get("table_kind") != 1 or encoded.get("gate") != 1:
            raise ImportError("trigger inspection supports only gate-1 MAN partition-2 references")
        index = encoded["record_index"]
        report = inspect_partition_two_script(disc, scene, index)
        return {**report, "schema_version": "legaia.trigger-script-inspection.v1",
                "trigger_id": trigger_id, "trigger_source_record": deepcopy(trigger["source_record"])}


def inspect_partition_two_script(disc: Any, scene: str, index: int) -> dict:
    """Inspect a source-bounded P2 record without requiring a trigger alias."""
    with _disc_context(disc) as (_, digest, mapping, archive):
        start, end = _bounded_scene_range(archive, mapping, scene)
        try:
            bundle, raw = find_scene_bundle(archive, start, end)
        except ImportError:
            from .man_source import read_man_source
            carrier = read_man_source(archive, start, end, scene)
            if carrier.kind != "raw_streaming_man":
                raise ImportError("Partition-2 source changed during streaming resolution")
            man = carrier.payload
            record, inspection = _inspect(man, scene, index)
            identity = f"script://{scene}/scripts/man-p2/{index:04d}"
            source = {"disc": {"sha256": digest, "serial": "SCUS-94254"}, "iso_file": "PROT.DAT",
                      "prot_entry_index": carrier.entry_index, "prot_entry_name": scene,
                      "record_kind": "man_partition_2_script", "partition": 2, "record_index": index,
                      "byte_coordinate_space": "raw_man_payload", "byte_offset": record["byte_offset"],
                      "byte_length": record["byte_length"], "sha256": record["sha256"],
                      "decoded_man_sha256": sha256(man).hexdigest(), "containing_decoded_size": len(man),
                      "man_source": carrier.provenance()}
        else:
            descriptors = [d for d in bundle.descriptors if d.type_byte == 3 and d.size > 0]
            if len(descriptors) != 1 or descriptors[0].size > MAX_MAN_BYTES:
                raise ImportError("trigger inspection requires one bounded MAN descriptor")
            descriptor = descriptors[0]
            if sum(d.size > 0 and d.data_offset == descriptor.data_offset for d in bundle.descriptors) != 1:
                raise ImportError("trigger MAN compressed descriptor is aliased")
            offset = bundle.table_offset + descriptor.data_offset
            ceiling = min([bundle.table_offset + d.data_offset for d in bundle.descriptors
                           if d.size > 0 and d.data_offset > descriptor.data_offset] + [len(raw)])
            if not 0 <= offset < ceiling <= len(raw):
                raise ImportError("trigger MAN compressed span exceeds its container")
            man, consumed = decompress_lzs(raw[offset:ceiling], descriptor.size)
            record, inspection = _inspect(man, scene, index)
            identity = f"script://{scene}/scripts/man-p2/{index:04d}"
            source = {"disc": {"sha256": digest, "serial": "SCUS-94254"}, "iso_file": "PROT.DAT",
                      "prot_entry_index": bundle.entry_index, "prot_entry_name": scene,
                      "record_kind": "man_partition_2_script", "partition": 2, "record_index": index,
                      "byte_coordinate_space": "decoded_man_payload", "byte_offset": record["byte_offset"],
                      "byte_length": record["byte_length"], "sha256": record["sha256"],
                      "decoded_man_sha256": sha256(man).hexdigest(), "containing_decoded_size": len(man),
                      "compressed_stream_offset": offset, "compressed_stream_coordinate_space": "prot_entry",
                      "compressed_bytes_consumed": consumed, "compressed_stream_sha256": sha256(raw[offset:offset + consumed]).hexdigest()}
        return {"schema_version": "legaia.partition-two-script-inspection.v1", "read_only": True,
                "script_id": identity, "partition": 2, "record_index": index,
                "reference_commit": REFERENCE_COMMIT, "source_record": source,
                "record": record,
                "inspection": inspection, "limitations": list(LIMITATIONS)}
