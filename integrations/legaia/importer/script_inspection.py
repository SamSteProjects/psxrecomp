"""Read-only MAN script/dialogue inspection with explicit partial coverage.

Pinned evidence: asset/man_section.rs, asset/field_disasm/{decode,decode_subops}.rs,
engine-vm/field/step.rs, engine-core/{dialog,man_field_scripts/placements}.rs,
mes/lib.rs. No VM executes here. Unknown instruction widths stop that path;
there is no byte-by-byte recovery or magic scan through opaque payloads.
"""
from __future__ import annotations

from collections import deque
from copy import deepcopy
import hashlib
import struct
from typing import Any

from .core import ImportError, decompress_lzs, find_scene_bundle
from .pipeline import REFERENCE_COMMIT, _bounded_scene_range, _disc_context, import_scene

MAX_RECORD_BYTES = 65536
MAX_NODES = 4096
MAX_MESSAGE_TOKENS = 4096

_SUBSTITUTIONS = {0xC1: "character_name", 0xC2: "item_name", 0xC3: "magic_name",
                  0xC4: "item_name_alt", 0xC5: "spell_name", 0xC7: "quest_name"}


def decode_inline_message(data: bytes, pc: int, base_offset: int = 0) -> dict:
    """Decode one evidenced 0x1F-led MES segment, retaining unknown font codes."""
    if (not isinstance(data, bytes) or type(pc) is not int or
            not 0 <= pc < len(data) <= MAX_RECORD_BYTES or data[pc] != 0x1F):
        raise ImportError("inline message requires a bounded 0x1F lead")
    cursor, text, tokens = pc + 1, [], []
    while cursor < len(data):
        if len(tokens) >= MAX_MESSAGE_TOKENS:
            raise ImportError("inline message token count exceeds inspection bound")
        op = data[cursor]
        if op <= 0x1E:
            return {"pc": pc, "byte_offset": base_offset + pc, "length": cursor + 1 - pc,
                    "text": "".join(text), "tokens": tokens, "terminator": op,
                    "raw_hex": data[pc:cursor + 1].hex(), "terminated": True}
        length = 2 if 0xC0 <= op <= 0xCF or op in (0x5E, 0xFF) else 1
        if cursor + length > len(data):
            raise ImportError("truncated two-byte MES token")
        token = {"pc": cursor, "byte_offset": base_offset + cursor, "length": length,
                 "raw_hex": data[cursor:cursor + length].hex()}
        arg = data[cursor + 1] if length == 2 else None
        if op in _SUBSTITUTIONS:
            kind = _SUBSTITUTIONS[op]
            token.update(kind="substitution", substitution=kind, index=arg)
            text.append("{" + kind + ":" + str(arg) + "}")
        elif op in (0xCE, 0x5E):
            spacing = (arg - 0x2D) & 255 if op == 0x5E else arg
            token.update(kind="spacing", value=spacing)
            text.append("{spacing:" + str(spacing) + "}")
        elif op in (0xCF, 0xFF):
            token.update(kind="escaped_glyph", value=arg)
            text.append(chr(arg) if 0x20 <= arg <= 0x7E else f"{{glyph:{arg:02x}}}")
        elif 0xC0 <= op <= 0xCF:
            token.update(kind="wide_glyph", bank=op, index=arg)
            text.append(f"{{wide_glyph:{op:02x}:{arg:02x}}}")
        elif 0x80 <= op <= 0x9F:
            token.update(kind="pager_control", value=op)
            text.append(f"{{control:{op:02x}}}")
        elif 0x20 <= op <= 0x7E:
            token.update(kind="glyph", value=op, text=chr(op))
            text.append(chr(op))
        else:
            token.update(kind="glyph", value=op)
            text.append(f"{{glyph:{op:02x}}}")
        tokens.append(token)
        cursor += length
    raise ImportError("inline message has no terminator inside the MAN record")


def _instruction(data: bytes, pc: int) -> dict:
    lead = data[pc]
    op = lead & 0x7F
    header = 2 if lead & 0x80 else 1
    operand = pc + header

    def need(count):
        if operand + count > len(data):
            raise ImportError(f"truncated opcode 0x{op:02x}")

    need(0)
    args, branches = {}, None
    if op in (0x21, 0x24, 0x25, 0x48):
        size, mnemonic = 0, "NOP"
    elif op == 0x22:
        need(1)
        size, mnemonic, args = 1, "EXEC_MOVE", {"move_id": data[operand]}
    elif op == 0x23:
        need(2)
        size, mnemonic = 2, "MOVE_TO"
        coords = list(data[operand:operand + 2])
        args = {"encoded_xz": coords, "world_xz": [(v & 127) * 128 + (128 if v & 128 else 64) for v in coords]}
    elif op == 0x26:
        need(2)
        delta = struct.unpack_from("<h", data, operand)[0]
        size, mnemonic, args = 2, "JMP_REL", {"delta": delta}
        branches = [{"pc": (operand + delta) & 0xFFFF, "condition": "unconditional"}]
    elif 0x2B <= op <= 0x33:
        need(1)
        group, operation = divmod(op - 0x2B, 3)
        size, mnemonic = 1, ("LFLAG", "GFLAG", "CFLAG")[group] + ("_SET", "_CLEAR", "_TEST")[operation]
        args = {"bit": data[operand] & 31, "raw_operand": data[operand]}
        if operation == 2:
            args["can_wait_for_flag"] = True
    elif op == 0x34:
        # Pinned executing VM step/effect.rs::op_34: only these two
        # forms have unconditional, fixed-width encoded continuations.
        # Spawn/capture forms depend on host control flow and remain opaque.
        need(1)
        selector = data[operand]
        sub = selector >> 4
        args = {"sub_op": sub, "raw_selector": selector}
        if sub == 0:
            size, mnemonic = 6, "EFFECT_COLOR_INTENSITY"
            need(size)
            args.update(rgb=list(data[operand + 1:operand + 4]),
                        intensity=struct.unpack_from("<h", data, operand + 4)[0])
        elif sub == 3:
            size, mnemonic = 2, "EFFECT_ANIMATION_TRIGGER"
            need(size)
            args["animation_operand"] = data[operand + 1]
        else:
            raise ImportError(f"unsupported EFFECT sub-op 0x{sub:x}; host-dependent or unimplemented continuation")
    elif op in (0x37, 0x41, 0x47):
        size, mnemonic = (3 if op == 0x47 else 2), "MOTION_YIELD"
    elif op in (0x35, 0x36, 0x38, 0x39, 0x3A, 0x3B, 0x3C, 0x3D, 0x44, 0x4A):
        size, mnemonic = {0x35: (3, "BGM"), 0x36: (4, "SCENE_FADE"), 0x38: (2, "CAM_CFG"),
                          0x39: (1, "GIVE_ITEM"), 0x3A: (3, "ADD_MONEY"), 0x3B: (2, "SET_ITEM_COUNT"),
                          0x3C: (1, "PARTY_ADD"), 0x3D: (1, "PARTY_REMOVE"),
                          0x44: (1, "SPAWN_RECORD"), 0x4A: (2, "WAIT_FRAMES")}[op]
    elif op == 0x3E:
        need(1)
        warp = 100 <= data[operand] < 255
        size, mnemonic = (5, "WARP") if warp else (2, "INTERACT")
        if warp:
            branches = []  # Scene transfer, not a proved local continuation.
    elif op == 0x3F:
        need(3)
        length = data[operand + 2]
        need(6 + length)
        size, mnemonic = 6 + length, "SCENE_CHANGE"
        name = data[operand + 3:operand + 3 + length]
        args = {"scene_name_bytes_hex": name.hex(), "scene_name_ascii":
                name.rstrip(b"\0").decode("ascii") if all(v < 128 for v in name) else None}
        branches = []
    elif op == 0x40:
        need(1)
        size, mnemonic = 1 + data[operand], "INLINE_DATA"
    elif op == 0x42:
        need(4)
        if data[operand] > 1:
            raise ImportError("unsupported conditional jump mode")
        delta = struct.unpack_from("<h", data, operand + 2)[0]
        size, mnemonic = 4, "COND_JMP"
        args = {"mode": data[operand], "test": data[operand + 1], "delta": delta}
        branches = [{"pc": (operand + 2 + delta) & 0xFFFF, "condition": "test_passed"},
                    {"pc": operand + 4, "condition": "test_failed"}]
    elif op == 0x49:
        need(1)
        sub = data[operand]
        if sub not in (1, 3, 7):
            raise ImportError(f"unsupported STATE_RESUME sub-op 0x{sub:02x}")
        size, mnemonic, args = 2, "STATE_RESUME", {"sub_op": sub, "can_wait_for_external_state": True}
    elif op == 0x4B:
        need(2)
        size, mnemonic = 2 + 4 * data[operand], "ANIMATE"
        args = {"count": data[operand], "base_id": data[operand + 1]}
    elif op == 0x4C:
        need(1)
        sub = data[operand]
        if sub in (0xED, 0xE8):
            # Pinned d6e64c68 engine-vm/field/step/menu_ctrl/nibble_e.rs
            # op_4c_ne, blob 61ad972bd5455bdb84b1ab376f6ad959cb23190b:
            # sub-D advances header+2; sub-8 advances header+9. Both
            # advance after their host call, including extended-context form.
            size = 2 if sub == 0xED else 9
            need(size)
            args = {"sub_op": sub}
            if sub == 0xED:
                mnemonic = "SET_FIELD_STATE_BA66"
                args.update(address="0x8007BA66", value=data[operand + 1])
            else:
                mnemonic = "CAMERA_ZOOM"
                args.update(zip(("zoom_x", "zoom_y", "zoom_z", "mode"),
                                struct.unpack_from("<hhhh", data, operand + 1)))
        elif sub in (0x50, 0x51, 0x52, 0x53, 0x54):
            size, mnemonic = {0x50: (3, "SET_ACTOR_MODEL"), 0x51: (5, "NPC_RUN"),
                              0x52: (2, "MENU_ACTIVATION_WAIT"), 0x53: (1, "DIALOG_WAIT"),
                              0x54: (1, "DIALOG_ADVANCE_WAIT")}[sub]
            args = {"sub_op": sub}
        else:
            raise ImportError(f"unsupported MENU_CTRL sub-op 0x{sub:02x}")
    elif 0x50 <= op <= 0x77:
        # The pinned executing VM covers through 0x77, while its disassembler
        # claims through 0x7F. Higher indices remain unsupported here.
        need(1)
        route = op >> 4
        size, mnemonic = (3, "SYSFLAG_TEST") if route == 7 else (1, "SYSFLAG_SET" if route == 5 else "SYSFLAG_CLEAR")
        args = {"index": ((lead & 0x8F) << 8) | data[operand]}
        if route == 7:
            need(3)
            delta = struct.unpack_from("<h", data, operand + 1)[0]
            args["delta"] = delta
            branches = [{"pc": (operand + 1 + delta) & 0xFFFF, "condition": "flag_set"},
                        {"pc": operand + 3, "condition": "flag_clear"}]
    else:
        raise ImportError(f"unsupported opcode 0x{op:02x}; no byte recovery performed")
    need(size)
    args["encoded_hex"] = data[operand:operand + size].hex()
    return {"pc": pc, "length": header + size, "opcode": op, "mnemonic": mnemonic,
            "operands": args, "raw_hex": data[pc:operand + size].hex(),
            "target_context": data[pc + 1] if header == 2 else None,
            "successors": branches if branches is not None else [{"pc": operand + size, "condition": "encoded_continuation"}]}


def inspect_record(data: bytes, script_offset: int, *, semantic_id: str = "script://synthetic",
                   base_offset: int = 0) -> dict:
    """Follow only supported encoded continuations, consuming MES atomically.

    This graph does not determine which story branch or dialogue box is active.
    Unknown boundaries are left opaque; conflicting boundaries invalidate the
    decoded graph instead of exposing potentially misclassified text as code.
    """
    if not isinstance(data, bytes) or not 0 < len(data) <= MAX_RECORD_BYTES:
        raise ImportError("script record exceeds bounded inspection size")
    if type(script_offset) is not int or not 0 <= script_offset <= len(data):
        raise ImportError("script entry offset is outside the record")
    queue = deque([script_offset])
    entries = {script_offset}
    visited, ownership = set(), {}
    instructions, dialogues, stops = [], [], []
    conflict = False
    while queue:
        pc = queue.popleft()
        if pc in visited or pc == len(data):
            continue
        visited.add(pc)
        if len(visited) > MAX_NODES:
            stops.append({"pc": pc, "reason": "instruction graph exceeds node bound"})
            break
        if not script_offset <= pc < len(data):
            stops.append({"pc": pc, "reason": "encoded target leaves the bounded script region"})
            continue
        if pc in ownership:
            stops.append({"pc": pc, "reason": "branch target lands inside a decoded instruction or message"})
            conflict = True
            continue
        try:
            if data[pc] == 0x1F:
                row = decode_inline_message(data, pc, base_offset)
                row["semantic_id"] = f"{semantic_id}/dialogue/{pc:04x}"
                successors = [{"pc": pc + row["length"], "condition": "encoded_continuation"}]
                is_message = True
            else:
                row = _instruction(data, pc)
                row["byte_offset"] = base_offset + pc
                successors = row["successors"]
                is_message = False
            if (any(byte in ownership for byte in range(pc, pc + row["length"])) or
                    any(byte in entries for byte in range(pc + 1, pc + row["length"]))):
                stops.append({"pc": pc, "reason": "decoded boundaries overlap; region is ambiguous"})
                conflict = True
                continue
            for byte in range(pc, pc + row["length"]):
                ownership[byte] = pc
            (dialogues if is_message else instructions).append(row)
            entries.update(edge["pc"] for edge in successors)
            queue.extend(edge["pc"] for edge in successors)
        except ImportError as exc:
            stops.append({"pc": pc, "reason": str(exc)})
    if conflict:
        instructions, dialogues, ownership = [], [], {}
    opaque = []
    cursor = script_offset
    while cursor < len(data):
        if cursor in ownership:
            cursor += 1
            continue
        start = cursor
        while cursor < len(data) and cursor not in ownership:
            cursor += 1
        opaque.append({"pc": start, "byte_offset": base_offset + start, "length": cursor - start,
                       "raw_hex": data[start:cursor].hex(),
                       "reason": "Unsupported, unvisited or ambiguous bytes; no instruction width inferred."})
    return {"status": "partial" if stops or opaque else "decoded_supported_paths",
            "instructions": sorted(instructions, key=lambda row: row["pc"]),
            "dialogues": sorted(dialogues, key=lambda row: row["pc"]),
            "opaque_regions": opaque, "stops": stops}


def inspect_actor_script(disc: Any, scene: str, actor: dict) -> dict:
    """Return a private, read-only inspection of a freshly verified MAN actor."""
    with _disc_context(disc) as (_, digest, mapping, archive):
        imported = import_scene(disc, scene)
        expected = next((a for a in imported["actors"] if a["semantic_id"] == actor.get("semantic_id")), None)
        if expected is None or any(actor.get(key) != expected[key] for key in
                                   ("source_record", "model_reference", "placement_fields")):
            raise ImportError("script actor provenance does not match the freshly imported scene")
        start, end = _bounded_scene_range(archive, mapping, scene)
        bundle, raw = find_scene_bundle(archive, start, end)
        candidates = [d for d in bundle.descriptors if d.type_byte == 3 and d.size > 0]
        if len(candidates) != 1:
            raise ImportError("script inspection requires one bounded MAN descriptor")
        descriptor = candidates[0]
        offset = bundle.table_offset + descriptor.data_offset
        ceiling = min([bundle.table_offset + d.data_offset for d in bundle.descriptors
                       if d.data_offset > descriptor.data_offset] + [len(raw)])
        if not 0 <= offset < ceiling <= len(raw):
            raise ImportError("MAN script compressed span exceeds its container")
        man, consumed = decompress_lzs(raw[offset:ceiling], descriptor.size)
        source = expected["source_record"]
        a, length = source["byte_offset"], source["byte_length"]
        if not 0 < length <= MAX_RECORD_BYTES or a + length > len(man):
            raise ImportError("actor script record exceeds the MAN source span")
        data = man[a:a + length]
        entry = 1 + data[0] * 2 + 4
        identity = "script://" + actor["semantic_id"].removeprefix("scene://")
        decoded = inspect_record(data, entry, semantic_id=identity, base_offset=a)
        return {"schema_version": "legaia.actor-script-inspection.v1", "read_only": True,
                "semantic_id": identity, "actor_semantic_id": actor["semantic_id"],
                "reference_commit": REFERENCE_COMMIT, "source_record": deepcopy(source),
                "record": {"record_index": source["record_index"], "byte_offset": a,
                           "byte_length": length, "script_offset": entry, "local_count": data[0],
                           "raw_hex": data.hex(), "sha256": hashlib.sha256(data).hexdigest(),
                           "compressed_bytes_consumed": consumed},
                **decoded,
                "limitations": ["Read-only inspection; no guest state, script execution or editing capability.",
                                "Encoded continuations are shown without evaluating story flags, interaction state or current runtime PCs.",
                                "Dialogue segments are not grouped into boxes or assigned to a current conversation branch.",
                                "Name substitutions, spacing and unknown font/control codes remain explicit tokens.",
                                "Unknown opcodes/sub-ops stop that path; opaque bytes are not scanned for apparent dialogue or instructions."]}
