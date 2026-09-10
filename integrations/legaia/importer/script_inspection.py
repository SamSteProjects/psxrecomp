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
    # MES picker open bytes mask bit7; it does not introduce an actor target.
    header = 2 if lead & 0x80 and op not in (0x27, 0x28, 0x29) else 1
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
    elif op in (0x27, 0x28, 0x29):
        # Pinned mes/picker.rs: pager controls, not ordinary field-VM ops.
        # Decode only a structurally complete table + labels at this reached PC.
        # Do not infer the independent post-page continuation or execute choices.
        count = op - 0x25
        need(count * 2 + 1)
        cursor = operand + count * 2
        continuation = data[cursor]
        if continuation & 0x7F in (0x24, 0x25, 0x48):
            cursor += 1
        if data[cursor:cursor + 2] == b"\x4c\xff":
            cursor += 2
        options = []
        for index in range(count):
            entry = operand + index * 2
            delta = struct.unpack_from("<h", data, entry)[0]
            label = decode_inline_message(data, cursor)
            options.append({"index": index, "label": label["text"],
                            "label_pc": cursor, "label_length": label["length"],
                            "entry_pc": entry, "relative_jump": delta,
                            "encoded_target": entry + delta})
            cursor += label["length"]
        size, mnemonic = cursor - operand, "DIALOGUE_PICKER"
        branches = [{"pc": option["encoded_target"], "condition": f"menu_choice_{option['index']}"}
                    for option in options]
        args = {"option_count": count, "options": options,
                "continuation_byte": continuation, "runtime_choice": "not_observed",
                "unresolved_control_flow": f"dialogue picker 0x{op:02x} labels and choice targets decoded; pager continuation and runtime branch execution unresolved"}
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
    elif op == 0x2A and header == 1:
        # Retail PROT 897 table 801CECC0 routes 2A to 801E3568.
        # The 0x20 mask misses all flag routes and returns the same PC.
        size, mnemonic, branches = 0, "DISPATCH_HALT", []
        args = {"unresolved_control_flow":
                "retail dispatcher returns the same PC for opcode 0x2a; external entry ownership of trailing bytes remains unresolved"}
    elif op == 0x45:
        # Pinned executing step/camera.rs: selector high bits distinguish
        # a payload, save, absolute jump, and a ten-slot sparse parameter list.
        need(1)
        selector = data[operand]
        form = selector & 0xC0
        args = {"selector": selector}
        if form == 0x40:
            size, mnemonic = 19, "CAMERA_LOAD"
        elif form == 0x80:
            size, mnemonic = 1, "CAMERA_SAVE"
        elif form == 0xC0:
            size, mnemonic = 3, "CAMERA_APPLY_JUMP"
            need(size)
            target = struct.unpack_from("<H", data, operand + 1)[0]
            args["target"] = target
            branches = [{"pc": target, "condition": "unconditional"}]
        else:
            need(4)
            mask = (selector << 8) | data[operand + 1]
            slots = [slot for slot in range(10) if mask & (1 << (9 - slot))]
            size, mnemonic = 4 + 2 * len(slots), "CAMERA_CONFIGURE"
            need(size)
            args.update(mode=(selector >> 2) & 15, mask=mask,
                        apply_trigger=struct.unpack_from("<H", data, operand + 2)[0],
                        parameters=[{"slot": slot, "value": struct.unpack_from("<H", data, operand + 4 + 2 * index)[0]}
                                    for index, slot in enumerate(slots)])
    elif op == 0x43:
        # Pinned d6e64c68 decode_subops.rs and executing step/actor_ctrl.rs.
        # Face setup is a configuration/ramp, not a scalar heading.
        need(1)
        sub = data[operand]
        if sub == 7:
            size, mnemonic = 16, "FACE_ROTATION_SETUP"
            need(size)
            args = {"sub_op": sub, "face_id": data[operand + 1],
                    "payload_u32": struct.unpack_from("<I", data, operand + 2)[0],
                    "parameters_u16": list(struct.unpack_from("<4H", data, operand + 6)),
                    "target_i16": struct.unpack_from("<h", data, operand + 14)[0],
                    "heading": "not_a_scalar_heading", "runtime_effect": "not_evaluated"}
        elif sub == 8:
            size, mnemonic, args = 1, "FACE_ROTATION_RESET", {"sub_op": sub, "runtime_effect": "not_evaluated"}
        elif sub == 9:
            # Pinned actor_ctrl.rs and decode_subops.rs agree on nine operands.
            # Only the immediate form proves the 0xffff unchanged sentinel;
            # timed interpolation is delegated to the reference host.
            size, mnemonic = 9, "ACTOR_POSITION"
            need(size)
            x, y, z, ticks = struct.unpack_from("<4H", data, operand + 1)
            args = {"sub_op": sub, "encoded_xyz": [x, y, z], "ticks": ticks,
                    "mode": "immediate" if ticks == 0 else "host_tween",
                    "runtime_effect": "not_evaluated"}
            if ticks == 0:
                args["unchanged_axes"] = [axis for axis, value in zip("xyz", (x, y, z)) if value == 0xFFFF]
        else:
            raise ImportError(f"unsupported ACTOR_CTRL sub-op 0x{sub:02x}")
    elif op == 0x46:
        # Pinned executing field/step.rs and asset field_disasm/decode.rs
        # agree: selector 0x24 alone selects the five-byte operand form.
        need(1)
        selector = data[operand]
        size, mnemonic = (5 if selector == 0x24 else 2), "RENDER_CFG"
        need(size)
        args = {"selector": selector, "long_form": selector == 0x24,
                "values": list(data[operand + 1:operand + size])}
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
        if 0x30 <= sub <= 0x3F:
            size, mnemonic = 1, "FIELD_STATE_CONTROL"
            args = {"sub_op": sub, "can_yield": sub in (0x30, 0x31, 0x37)}
        elif 0x40 <= sub <= 0x4D and sub != 0x49:
            # Executing nibble_3_4.rs has encoded jumps for 43/44 and
            # a wider 45 form. Never treat this cluster as uniform width.
            size, mnemonic = (10 if sub == 0x45 else 5), "FIELD_RAMP"
            need(size)
            args = {"sub_op": sub}
            if sub == 0x45:
                args.update(selector=data[operand + 1],
                            values=list(struct.unpack_from("<hhh", data, operand + 2)),
                            ticks=struct.unpack_from("<H", data, operand + 8)[0], can_yield=True)
            else:
                value, ticks = struct.unpack_from("<hH", data, operand + 1)
                args.update(value=value, ticks=ticks)
                if (sub == 0x43 and ticks == 0) or (sub == 0x44 and ticks != 0):
                    mnemonic = "FIELD_ABSOLUTE_JUMP"
                    branches = [{"pc": value, "condition": "unconditional"}]
        elif sub == 0x81:
            # Executing pinned menu_ctrl/nibble_8.rs: u24 model and two
            # unsigned u16 frame operands; continuation is unconditional.
            size, mnemonic = 8, "SET_MODEL_ANIMATION"
            need(size)
            args = {"sub_op": sub,
                    "model_id": int.from_bytes(data[operand + 1:operand + 4], "little"),
                    "animation_frame": struct.unpack_from("<H", data, operand + 4)[0],
                    "tween_frames": struct.unpack_from("<H", data, operand + 6)[0]}
        elif sub in (0x85, 0x8E, 0x8F):
            # Pinned nibble_8.rs uses header+4 for all three acquire forms.
            # Require the entire encoded payload even though its host hook
            # receives the opcode PC instead of reading these bytes itself.
            size, mnemonic = 4, "CONTEXT_HALT_ACQUIRE"
            need(size)
            args = {"sub_op": sub, "can_wait_for_external_state": True}
            branches = [{"pc": operand + size, "condition": "acquire_succeeded"},
                        {"pc": pc, "condition": "acquire_wait"}]
        elif sub in (0x60, 0x61):
            size = 13 if sub == 0x60 else 15
            need(size)
            mnemonic = "EMITTER_SIX_WORDS" if sub == 0x60 else "EMITTER_ACQUIRE"
            args = {"sub_op": sub}
            if sub == 0x60:
                args["words"] = list(struct.unpack_from("<6h", data, operand + 1))
            else:
                args["can_wait_for_external_state"] = True
                branches = [{"pc": operand + size, "condition": "acquire_succeeded"},
                            {"pc": pc, "condition": "acquire_wait"}]
        elif sub in (0xA0, 0xA1, 0xA2):
            # Pinned executing menu_ctrl/nibble_9_a.rs sign-extends the
            # absolute target; negative targets remain out-of-bounds, not wrapped.
            size, mnemonic = 4, "FLAG_WORD_BRANCH"
            need(size)
            target = struct.unpack_from("<h", data, operand + 2)[0]
            bank = {0xA0: "actor_flags", 0xA1: "actor_local_flags", 0xA2: "global_story_word"}[sub]
            args = {"sub_op": sub, "flag_word": bank, "bit_encoded": data[operand + 1],
                    "target": target, "runtime_value": "not_observed"}
            branches = [{"pc": target, "condition": "flag_bit_set"},
                        {"pc": operand + size, "condition": "flag_bit_clear"}]
        elif 0x70 <= sub <= 0x73:
            size = 5 if sub < 0x72 else 6
            need(size)
            mnemonic = "COLLISION_WALL_PAINT"
            args = {"sub_op": sub, "rectangle_operands": list(data[operand + 1:operand + 5]),
                    "can_yield": sub < 0x72}
            if sub >= 0x72:
                args["mask"] = data[operand + 5]
        elif sub == 0xCD:
            size, mnemonic, branches = 1, "SCRIPT_CONTEXT_ALLOC", []
            args = {"sub_op": sub, "can_wait_for_external_state": True}
            if header == 1:
                # Retail PROT 897: 801E29E0 increments s8 by two; null
                # allocation or allocated flags bit 3 returns it. Otherwise
                # 801E2A18 restores the original PC and returns via 801DEE50.
                # This corrects the pinned VM's unconditional same-PC halt.
                branches = [{"pc": pc + 2, "condition": "allocation_absent_or_flag_3_set"},
                            {"pc": pc, "condition": "allocated_context_wait"}]
            else:
                args["unresolved_control_flow"] = "extended allocated-context entry and external resumption are unresolved"
        elif 0xC0 <= sub <= 0xCF and sub != 0xC9:
            # Pinned executing menu_ctrl/nibble_c.rs. C9 depends on host
            # comparison; CD allocates a context and halts, with no fallthrough.
            size = {0xC0: 1, 0xC1: 1, 0xC2: 2, 0xC3: 1, 0xC4: 3,
                    0xC5: 3, 0xC6: 3, 0xC7: 3, 0xC8: 1,
                    0xCA: 4, 0xCB: 4, 0xCC: 4, 0xCE: 2, 0xCF: 3}[sub]
            mnemonic = {0xC0: "MOVE_CANCEL", 0xC1: "TRIGGER_FLAG_RESET",
                        0xC2: "SET_FIELD_42", 0xC3: "SCRIPT_TELEPORT",
                        0xC4: "SUBTILE_BROADCAST", 0xC5: "PARTY_FLAG_TEST_CLEAR",
                        0xC6: "PARTY_FLAG_TEST_SET", 0xC7: "SOUND_TRIGGER",
                        0xC8: "TOGGLE_FIELD_74", 0xCA: "SET_SLOT",
                        0xCB: "ADJUST_SLOT_B", 0xCC: "ADJUST_SLOT_C",
                        0xCE: "SET_FIELD_B6AC", 0xCF: "POSITION_BROADCAST"}[sub]
            need(size)
            args = {"sub_op": sub}
            if sub in (0xC5, 0xC6):
                args["party_flag_index"] = struct.unpack_from("<H", data, operand + 1)[0]
            elif sub in (0xCA, 0xCB, 0xCC):
                raw = struct.unpack_from("<H", data, operand + 2)[0]
                args.update(slot=data[operand + 1], raw_value=raw,
                            value=struct.unpack_from("<h", data, operand + 2)[0],
                            uses_frame_delta=sub in (0xCB, 0xCC) and raw == 0xFFFF)
            else:
                args["values"] = list(data[operand + 1:operand + size])
        elif sub in (0xED, 0xE8):
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
            stops.append({"pc": pc, "owner_pc": ownership[pc],
                          "reason": f"branch target lands inside a decoded instruction or message owned by 0x{ownership[pc]:x}"})
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
            if not is_message and row["operands"].get("unresolved_control_flow"):
                stops.append({"pc": pc, "reason": row["operands"]["unresolved_control_flow"],
                              "kind": "known_instruction_unresolved_control_flow"})
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
