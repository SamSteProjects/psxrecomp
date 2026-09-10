"""Bounded record-level scene-entry edits; no scene relocation or world mapping.

Pinned engine-vm/field/step.rs opcode3F consumes name + three unsigned bytes.
Project commands and Build consume these audited, source-preserving edits.
"""
from __future__ import annotations

import hashlib
import re
from copy import deepcopy
from .core import ImportError
from .dialogue_authoring import DialogueAuthoringContext, load_dialogue_authoring_context
from .script_inspection import inspect_record

ENTRY_FIELDS = ("entry_x_encoded", "entry_z_encoded", "direction_encoded")
LIMITATIONS = [
    "Only encoded entry X, Z and direction bytes are editable; world coordinates and direction semantics are not inferred.",
    "Destination names, instruction sizes and opaque bytes remain unchanged.",
    "Unknown or conflicting source paths and aliased records are unsupported.",
    "Encoded entry edits do not establish live transition reachability or gameplay behavior.",
]


def reference_entry_interpretation(values: dict) -> dict:
    """Pinned engine interpretation, not an observation of the recomp runtime."""
    if set(values) != set(ENTRY_FIELDS) or any(type(v) is not int or not 0 <= v <= 255 for v in values.values()):
        raise ImportError("entry interpretation requires all three encoded bytes")
    def coordinate(value):
        return (value & 0x7f) * 128 + (128 if value & 0x80 else 64)
    return {"x": coordinate(values["entry_x_encoded"]),
            "z": coordinate(values["entry_z_encoded"]),
            "facing_angle_12bit": (values["direction_encoded"] & 7) * 512,
            "evidence": "pinned_reference_implementation", "runtime_verified": False,
            "source": "crates/engine-core/src/world/field_loop.rs:275-308"}


class TransitionAuthoringContext:
    """Immutable MAN snapshot with stable transition IDs and audited byte edits."""

    def __init__(self, source: DialogueAuthoringContext):
        self._source = source
        self._man = source._man  # Immutable source shared with the verified MAN reader.

    def provenance(self) -> dict:
        result = self._source.provenance()
        result["limitations"] = list(LIMITATIONS)
        return result

    def options(self, owner: str) -> dict:
        offset, record, entry = self._source.verified_record(owner)
        report = inspect_record(record, entry)
        transitions, reason = [], None
        if report["stops"]:
            reason = "Transition edits require no unknown or conflicting source-path stops"
        else:
            for node in report["instructions"]:
                if node["mnemonic"] != "SCENE_CHANGE":
                    continue
                pc = node["pc"]
                operand = pc + (2 if node["target_context"] is not None else 1)
                start = operand + 3 + record[operand + 2]
                values = dict(zip(ENTRY_FIELDS, record[start:start + 3]))
                try:
                    patch_transition_entry(record, entry, pc, values)
                except ImportError:
                    continue
                transitions.append(dict(
                    semantic_id=f"script://{owner.removeprefix('scene://')}/transition/{pc:04x}",
                    owner_id=owner, pc=pc, decoded_byte_offset=offset + start,
                    destination=node["operands"]["scene_name_ascii"], values=values,
                    reference_interpretation=reference_entry_interpretation(values),
                    source_record_sha256=hashlib.sha256(record).hexdigest()))
            if not transitions:
                reason = "No supported named transitions occur on the inspected paths"
        return dict(supported=bool(transitions), reason=reason, transitions=transitions,
                    source=self.provenance(), limitations=list(LIMITATIONS))

    def patch(self, edits: dict, *, original: bytes | None = None) -> tuple[bytes, list[dict]]:
        if original is not None and original != self._man:
            raise ImportError("transition MAN source differs from the verified baseline")
        if not isinstance(edits, dict) or len(edits) > 1024:
            raise ImportError("transition edit set exceeds the bounded transition count")
        staged, occupied = [], set()
        digest = hashlib.sha256(self._man).hexdigest()
        for identifier, values in edits.items():
            match = re.fullmatch(r"script://([A-Za-z0-9_-]+/(?:actors/man-p1|scripts/man-p2)/[0-9]{4})/transition/([0-9a-f]{4})", identifier) if isinstance(identifier, str) else None
            if match is None:
                raise ImportError("transition identifier must contain its source owner and fixed hexadecimal PC")
            owner = "scene://" + match[1]
            options = self.options(owner)
            if not any(item["semantic_id"] == identifier for item in options["transitions"]):
                raise ImportError("transition is not a supported span in the verified source record")
            offset, record, entry = self._source.verified_record(owner)
            _, audit = patch_transition_entry(record, entry, int(match[2], 16), values, base_offset=offset)
            for change in audit:
                absolute = change["decoded_byte_offset"]
                if absolute in occupied:
                    raise ImportError("transition edits overlap another authored span")
                occupied.add(absolute)
                staged.append(dict(change, transition_id=identifier, owner_id=owner,
                                   source_decoded_man_sha256=digest))
        result = bytearray(self._man)
        staged.sort(key=lambda item: item["decoded_byte_offset"])
        for change in staged:
            result[change["decoded_byte_offset"]] = change["after_byte"]
        return bytes(result), deepcopy(staged)


def load_transition_authoring_context(disc, scene: str) -> TransitionAuthoringContext:
    return TransitionAuthoringContext(load_dialogue_authoring_context(disc, scene))


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
