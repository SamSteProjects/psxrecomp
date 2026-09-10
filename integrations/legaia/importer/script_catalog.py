"""Metadata-only script/dialogue assets and scoped encoded references.

Pinned evidence (pipeline.REFERENCE_COMMIT): engine-vm/src/field/step.rs
L/G/CFLAG and system-selector dispatch, and asset/src/field_disasm/render.rs
clean_scene_name. Parsing/boundaries remain owned by script_inspection/core.
No source text, instruction bytes, runtime flag values or reachable scene edges
are exposed by this catalog. Unknown regions are never scanned for resources.
"""
from __future__ import annotations

from collections import Counter
from copy import deepcopy
import hashlib
from typing import Any

from .core import (ImportError, decompress_lzs, find_scene_bundle, parse_man,
                   stable_actor_id, validate_metadata_only)
from .pipeline import REFERENCE_COMMIT, _bounded_scene_range, _disc_context
from .script_inspection import inspect_record
from .trigger_scripts import _p2_record, _p2_entry

MAX_MAN_BYTES = 4 * 1024 * 1024
MAX_ACTORS = 512
MAX_ASSETS = 8192
MAX_RELATIONSHIPS = 16384
LIMITATIONS = [
    "Partition-1 actor and partition-2 scripts; partition-0/controller records remain outside this catalog.",
    "Partial graphs remain partial; unknown or unvisited bytes are never scanned for dialogue, flags or transitions.",
    "Flag references retain encoded bank/selector and dispatch context; no current values, story names or universal flag IDs are inferred.",
    "Named transitions are encoded references, not proof of a reachable path or successful scene change.",
    "Dialogue assets contain counts and source hashes only; text and control tokens are available through private script inspection.",
]


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _flag_reference(row: dict) -> dict | None:
    mnemonic, args = row["mnemonic"], row["operands"]
    if mnemonic.startswith(("LFLAG_", "GFLAG_", "CFLAG_", "SYSFLAG_")):
        prefix, operation = mnemonic.split("_", 1)
        bank = {"LFLAG": "local", "GFLAG": "global", "CFLAG": "context", "SYSFLAG": "system"}[prefix]
        index = args["index"] if bank == "system" else args["bit"]
        scope = {"local": "dispatch_context_local_flags", "context": "dispatch_context_flags",
                 "global": "host_global_flags", "system": "system_bank_encoded_selector"}[bank]
    elif mnemonic == "COND_JMP" and args["mode"] == 0:
        bank, operation, index, scope = "extra", "TEST", args["test"] & 31, "host_extra_flags"
    else:
        return None
    return {"pc": row["pc"], "byte_offset": row["byte_offset"], "mnemonic": mnemonic,
            "bank": bank, "operation": operation.lower(), "index": index, "scope": scope,
            "extended_target": row["target_context"],
            "context_resolution": "extended_target_unresolved" if row["target_context"] is not None else "current_script_context",
            "index_semantics": "encoded_selector_not_resolved_runtime_bit" if bank == "system" else "operand_masked_to_five_bits",
            "status": "bank_width_unresolved" if bank == "local" and index >= 16 else "encoded_reference",
            "runtime_value": None}


def _transition(row: dict, record: bytes, known_scenes: set[str]) -> dict | None:
    if row["mnemonic"] != "SCENE_CHANGE":
        return None
    operand = row["pc"] + (2 if row["target_context"] is not None else 1)
    length = record[operand + 2]
    raw_name = record[operand + 3:operand + 3 + length]
    # Exact pinned clean_scene_name gate: nonempty, <=12, lowercase/digits.
    clean = 1 <= len(raw_name) <= 12 and all(97 <= byte <= 122 or 48 <= byte <= 57 for byte in raw_name)
    name = raw_name.decode("ascii") if clean else None
    entry = operand + 3 + length
    return {"pc": row["pc"], "byte_offset": row["byte_offset"], "mnemonic": row["mnemonic"],
            "extended_target": row["target_context"], "target_scene_name": name,
            "target_in_scene_index": name in known_scenes if name is not None else None,
            "status": "encoded_named_reference" if clean else "unsupported_name_encoding",
            "name_byte_length": length, "name_sha256": _sha(raw_name),
            "entry_x_encoded": record[entry], "entry_z_encoded": record[entry + 1],
            "direction_encoded": record[entry + 2], "reachability": "not_evaluated"}


def _catalog(man: bytes, scene: str, source: dict, known_scenes: set[str]) -> dict:
    """Internal decoder-product adapter; public callers provide a disc, not bytes."""
    if not isinstance(man, bytes) or not 0 < len(man) <= MAX_MAN_BYTES:
        raise ImportError("script catalog MAN exceeds the bounded source size")
    parsed = parse_man(man, scene)
    if len(parsed.actors) > MAX_ACTORS or parsed.partition_counts[2] > MAX_ACTORS:
        raise ImportError("script catalog partition count exceeds bound")
    total = sum(parsed.partition_counts)
    region = 0x2B + total * 3
    aliases = Counter(region + int.from_bytes(man[0x2B + 3*i:0x2E + 3*i], "little") for i in range(total))
    assets, references, transitions = [], 0, 0
    dialogue_count = partial_count = unavailable_count = 0
    records = [(1, actor.record_index, actor) for actor in parsed.actors]
    records += [(2, index, None) for index in range(parsed.partition_counts[2])]
    for partition, index, actor in records:
        actor_id = stable_actor_id(scene, 1, index) if actor is not None else None
        owner = actor_id or f"scene://{scene}/scripts/man-p2/{index:04d}"
        script_id = "script://" + owner.removeprefix("scene://")
        label = f"Actor {index:04d}" if actor is not None else f"Partition 2 script {index}"
        record, offset, entry = b"", None, None
        try:
            if actor is not None:
                offset = actor.byte_offset
                record = man[offset:offset + actor.byte_length]
                entry = 1 + actor.local_count * 2 + 4
            else:
                offset, record = _p2_record(man, index)
                entry = _p2_entry(record)[0]
            report = inspect_record(record, entry, semantic_id=script_id, base_offset=offset)
        except ImportError as exc:
            report = {"status": "unavailable", "instructions": [], "dialogues": [],
                      "opaque_regions": ([{"pc": 0, "byte_offset": offset, "length": len(record)}]
                                         if offset is not None else []),
                      "stops": [{"pc": entry, "reason": str(exc)}]}
        locator = dict(deepcopy(source), record_index=index, partition=partition,
                       byte_offset=offset, byte_length=len(record) if offset is not None else None,
                       byte_coordinate_space="decoded_lzs_descriptor", sha256=_sha(record) if offset is not None else None,
                       record_alias_count=aliases[offset] if offset is not None else None)
        flags = [ref for row in report["instructions"] if (ref := _flag_reference(row)) is not None]
        destinations = [ref for row in report["instructions"] if (ref := _transition(row, record, known_scenes)) is not None]
        references += len(flags)
        transitions += len(destinations)
        if references + transitions > MAX_RELATIONSHIPS:
            raise ImportError("script catalog encoded relationship count exceeds bound")
        partial_count += report["status"] == "partial"
        unavailable_count += report["status"] == "unavailable"
        assets.append({"semantic_id": script_id, "asset_kind": "script", "kind": "script", "scope": "scene",
                       "name": label + (" script" if actor is not None else ""), "actor_semantic_id": actor_id,
                       "owner_semantic_id": owner, "partition": partition,
                       "script_id": script_id, "source_record": locator, "status": report["status"],
                       "entry_pc": entry, "instruction_count": len(report["instructions"]),
                       "dialogue_count": len(report["dialogues"]), "stop_count": len(report["stops"]),
                       "menu_count": sum(row["mnemonic"] == "DIALOGUE_PICKER" for row in report["instructions"]),
                       "menus": [{"pc": row["pc"], "byte_offset": row["byte_offset"],
                                  "byte_length": row["length"], "option_count": row["operands"]["option_count"],
                                  "sha256": _sha(record[row["pc"]:row["pc"] + row["length"]]),
                                  "status": "decoded_menu_unresolved_continuation"}
                                 for row in report["instructions"] if row["mnemonic"] == "DIALOGUE_PICKER"],
                       "opaque_byte_count": sum(row["length"] for row in report["opaque_regions"]),
                       "opaque_ranges": [{key: row[key] for key in ("pc", "byte_offset", "length")} for row in report["opaque_regions"]],
                       "stops": deepcopy(report["stops"]), "flag_references": flags, "transitions": destinations,
                       "reference_commit": REFERENCE_COMMIT, "limitations": list(LIMITATIONS)})
        for message in report["dialogues"]:
            offset, length = message["byte_offset"], message["length"]
            message_locator = dict(deepcopy(locator), byte_offset=offset, byte_length=length,
                                   script_record_byte_offset=locator["byte_offset"], sha256=_sha(man[offset:offset + length]))
            if actor is not None:
                message_locator["actor_record_byte_offset"] = actor.byte_offset
            assets.append({"semantic_id": message["semantic_id"], "asset_kind": "dialogue", "kind": "dialogue",
                           "scope": "scene", "name": f"{label} dialogue {message['pc']:04x}",
                           "owner_semantic_id": owner, "partition": partition,
                           "actor_semantic_id": actor_id, "script_id": script_id, "pc": message["pc"],
                           "byte_length": length, "token_count": len(message["tokens"]),
                           "text_length": len(message["text"]), "text_sha256": _sha(message["text"].encode("utf-8")),
                           "source_record": message_locator, "status": "decoded_segment",
                           "script_status": report["status"], "reference_commit": REFERENCE_COMMIT,
                           "limitations": list(LIMITATIONS)})
            dialogue_count += 1
        if len(assets) > MAX_ASSETS:
            raise ImportError("script and dialogue asset count exceeds catalog bound")
    result = {"schema_version": "legaia.script-asset-catalog.v1", "scene": scene,
              "reference_commit": REFERENCE_COMMIT, "metadata_only": True, "runtime_state": "not_observed",
              "source_record": dict(deepcopy(source), decoded_man_sha256=_sha(man), decoded_man_size=len(man)),
              "actor_count": len(parsed.actors), "script_count": len(records), "dialogue_count": dialogue_count,
              "partition_two_script_count": parsed.partition_counts[2],
              "partial_script_count": partial_count, "unavailable_script_count": unavailable_count,
              "flag_reference_count": references, "transition_count": transitions,
              "asset_count": len(assets), "assets": assets, "limitations": list(LIMITATIONS)}
    validate_metadata_only(result)
    return result


def load_script_asset_catalog(disc: Any, scene: str) -> dict:
    """Read one verified scene MAN, then inspect bounded P1/P2 records once."""
    with _disc_context(disc) as (_, digest, mapping, archive):
        start, end = _bounded_scene_range(archive, mapping, scene)
        bundle, raw = find_scene_bundle(archive, start, end)
        descriptors = [d for d in bundle.descriptors if d.type_byte == 3 and d.size > 0]
        if len(descriptors) != 1:
            raise ImportError("script catalog requires exactly one scene MAN descriptor")
        descriptor = descriptors[0]
        if descriptor.size > MAX_MAN_BYTES:
            raise ImportError("script catalog MAN descriptor exceeds source size bound")
        if sum(d.size > 0 and d.data_offset == descriptor.data_offset for d in bundle.descriptors) != 1:
            raise ImportError("script catalog MAN compressed descriptor is aliased")
        offset = bundle.table_offset + descriptor.data_offset
        ceiling = min([bundle.table_offset + d.data_offset for d in bundle.descriptors
                       if d.data_offset > descriptor.data_offset] + [len(raw)])
        if not 0 <= offset < ceiling <= len(raw):
            raise ImportError("script catalog MAN stream exceeds its descriptor bounds")
        man, consumed = decompress_lzs(raw[offset:ceiling], descriptor.size)
        source = {"disc": {"sha256": digest, "serial": "SCUS-94254"}, "iso_file": "PROT.DAT",
                  "prot_entry_index": bundle.entry_index, "scene_table_offset": bundle.table_offset,
                  "descriptor_index": descriptor.index, "descriptor_type": 3,
                  "compressed_stream_offset": offset, "compressed_bytes_consumed": consumed}
        return _catalog(man, scene, source, set(mapping.values()))
