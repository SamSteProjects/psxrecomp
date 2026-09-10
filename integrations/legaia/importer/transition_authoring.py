"""Bounded record-level scene-entry edits; no scene relocation or world mapping.

Pinned engine-vm/field/step.rs opcode3F consumes name + three unsigned bytes.
This serializer is a foundation API, not yet connected to project commands/build.
"""
from __future__ import annotations

import hashlib
from .core import ImportError
from .script_inspection import inspect_record

ENTRY_FIELDS = ("entry_x_encoded", "entry_z_encoded", "direction_encoded")


def patch_transition_entry(record: bytes, script_offset: int, pc: int,
                           edits: dict, *, base_offset: int = 0) -> tuple[bytes, list[dict]]:
    """Patch one verified named transition, preserving all other record bytes."""
    if type(pc) is not int or type(base_offset) is not int or base_offset < 0:
        raise ImportError("transition offsets must be nonnegative integer source offsets")
    if not isinstance(edits, dict) or not edits or set(edits) - set(ENTRY_FIELDS):
        raise ImportError("only encoded transition entry X, Z and direction can be edited")
    if any(type(value) is not int or not 0 <= value <= 255 for value in edits.values()):
        raise ImportError("encoded transition entry values must be integers from 0 through 255")
    report = inspect_record(record, script_offset)
    if report["stops"]:
        raise ImportError("transition edits require no unknown or conflicting source-path stops")
    node = next((node for node in report["instructions"] if node["pc"] == pc), None)
    if node is None or node["mnemonic"] != "SCENE_CHANGE":
        raise ImportError("transition PC must identify a decoded scene-change instruction")
    operand = pc + (2 if node["target_context"] is not None else 1)
    name_length = record[operand + 2]
    name = record[operand + 3:operand + 3 + name_length]
    if not 1 <= len(name) <= 12 or any(not (97 <= b <= 122 or 48 <= b <= 57) for b in name):
        raise ImportError("transition destination must have an evidenced clean scene name")
    entry = operand + 3 + name_length
    changed = bytearray(record)
    digest = hashlib.sha256(record).hexdigest()
    audit = []
    for index, field in enumerate(ENTRY_FIELDS):
        if field not in edits or edits[field] == record[entry + index]:
            continue
        offset = entry + index
        changed[offset] = edits[field]
        audit.append({"field": field, "pc": pc, "record_relative_byte_offset": offset,
                      "decoded_byte_offset": base_offset + offset,
                      "before_byte": record[offset], "after_byte": edits[field],
                      "source_record_sha256": digest})
    return bytes(changed), audit
