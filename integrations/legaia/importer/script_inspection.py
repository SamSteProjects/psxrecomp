"""Read-only MAN script/dialogue inspection with explicit partial coverage.

Pinned evidence: asset/man_section.rs, asset/field_disasm/{decode,decode_subops}.rs,
engine-vm/field/step.rs, engine-core/{dialog,man_field_scripts/placements}.rs,
mes/lib.rs. No VM executes here. Unknown instruction widths stop that path;
there is no byte-by-byte recovery or magic scan through opaque payloads.

Executing SCUS-94254 evidence takes precedence where the pinned VM differs:
PROT[897], load 0x801CE818, SHA256 216f846db5ab085a295cef4064747380a06c995caa3e1b2773e78a1d349f126b.
45/C0 advances after a camera call; 4C43/44 write/ramp without jumping;
4C/A0..A2 branches relative to its signed-word location. Retail consumers
store and sign-extend 16-bit PCs; source inspection does not prove a high-bit
target is usable at runtime. Extended SYSFLAG raw operand addressing remains
unsupported rather than inheriting the pinned generic header assumption.
"""
from __future__ import annotations

from collections import deque
from copy import deepcopy
import hashlib
import struct
from typing import Any

from .core import ImportError
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


def _native_payload_span(data: bytes, start: int, label: str) -> dict:
    """Bound SCUS8003CA38 bytes without assigning text or VM ownership."""
    cursor = start
    for tokens in range(MAX_MESSAGE_TOKENS):
        if cursor >= len(data):
            raise ImportError(f"truncated {label} payload; no recovery performed")
        value = data[cursor]
        if value <= 0x1E:
            return {"pc": start, "length": cursor + 1 - start,
                    "terminator": value, "token_count": tokens}
        cursor += 2 if value & 0xF0 == 0xC0 else 1
        if cursor > len(data):
            raise ImportError(f"truncated {label} two-byte token")
    raise ImportError(f"{label} token count exceeds inspection bound")


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
        args.update(target_position={"x": args["world_xz"][0], "y": None, "z": args["world_xz"][1]},
                    coordinate_system="retail_field_world_units", movement_kind="teleport",
                    runtime_effect="not_evaluated")
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
                            "label_tokens": label["tokens"], "label_terminator": label["terminator"],
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
        # Fixed color/animation forms and uncaptured spawn packets advance.
        # Captured payload ownership depends on actor match and stays opaque.
        need(1)
        selector = data[operand]
        sub = selector >> 4
        args = {"sub_op": sub, "raw_selector": selector}
        if sub == 0:
            size, mnemonic = 6, "EFFECT_COLOR_INTENSITY"
            need(size)
            args.update(rgb=list(data[operand + 1:operand + 4]),
                        intensity=struct.unpack_from("<h", data, operand + 4)[0])
        elif sub == 1:
            size, mnemonic = 12, "EFFECT_SPAWN_PACKET"
            # Retail peeks just past the base packet; record end cannot stand
            # in for an absent capture marker. Existing actor skips capture.
            need(size + 1)
            args.update(packet_bytes=list(data[operand + 1:operand + size]),
                        runtime_actor_match="not_observed", runtime_effect="not_evaluated")
            marker = data[operand + size]
            args["following_byte"] = marker
            if marker == 0x40:
                need(size + 2)
                length = data[operand + size + 1]
                need(size + 2 + length)
                args.update(capture_payload={"pc": operand + size + 2, "length": length,
                                             "encoded_hex": data[operand + size + 2:operand + size + 2 + length].hex()},
                            conditional_continuations={"existing_actor": operand + size,
                                                       "new_actor_capture": operand + size + 2 + length},
                            unresolved_control_flow="EFFECT spawn capture has conditional payload ownership; actor match and both parent continuations remain unresolved")
                branches = []
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
        if op == 0x4A:
            need(2)
            args = {"duration_ticks": struct.unpack_from("<H", data, operand)[0],
                    "timing_units": "host_frame_delta_ticks", "seconds": None,
                    "execution": "not_evaluated", "accumulator_width": "signed16"}
        if op == 0x44:
            need(1)
            # Pinned step.rs calls FUN_8003BDE0 with global_index-N0-N1.
            # This is a partition2 script context, not a partition1 NPC ID.
            args = {"global_record_index": data[operand],
                    "target_partition": 2,
                    "index_semantics": "global_index_minus_partition0_and_partition1_counts"}
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
    elif op == 0x4D:
        # Pinned executing step.rs / FUN_801E3614: outside branch uses
        # the skip-word location as its relative base, not the next opcode.
        size, mnemonic = 6, "BBOX_TEST"
        need(size)
        delta = struct.unpack_from("<h", data, operand + 4)[0]
        args = {"tile_bounds": list(data[operand:operand + 4]), "delta": delta,
                "coordinate_mode": "runtime_global_flag_dependent"}
        branches = [{"pc": operand + 6, "condition": "inside_box"},
                    {"pc": (operand + 4 + delta) & 0xFFFF, "condition": "outside_box"}]
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
        # Executing retail 801DF210..288: C0 calls 801DE084 with a signed
        # parameter read at operand+1, then advances PC by header+3. The
        # pinned camera.rs incorrectly treats that camera argument as a PC.
        need(1)
        selector = data[operand]
        form = selector & 0xC0
        args = {"selector": selector}
        if form == 0x40:
            size, mnemonic = 19, "CAMERA_LOAD"
        elif form == 0x80:
            size, mnemonic = 1, "CAMERA_SAVE"
        elif form == 0xC0:
            size, mnemonic = 3, "CAMERA_APPLY"
            need(size)
            args.update(apply_trigger=struct.unpack_from("<h", data, operand + 1)[0],
                        mode=(selector >> 2) & 15, runtime_effect="not_evaluated")
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
        if sub in (0, 1, 0xA, 0xB):
            # Native shared handler801DF384: failure restores original PC;
            # success calls801D25EC with signed parameters+3/+5, then PC+8.
            # Wide forms additionally read+7 and advance2. These are not
            # resume destinations, contrary to the pinned actor_ctrl.rs.
            size, mnemonic = (9 if sub >= 0xA else 7), "ACTOR_ACQUIRE_REQUEST"
            need(size)
            args = {"sub_op": sub, "encoded_xz": list(data[operand + 1:operand + 3]),
                    "parameters_i16": list(struct.unpack_from("<2h", data, operand + 3)),
                    "callback": "0x801D25EC", "runtime_acquisition": "not_observed",
                    "runtime_effect": "not_evaluated"}
            if sub >= 0xA:
                args["vertical_operand_i16"] = struct.unpack_from("<h", data, operand + 7)[0]
            branches = [{"pc": operand + size, "condition": "actor_acquisition_succeeded"},
                        {"pc": pc, "condition": "actor_acquisition_pending"}]
        elif sub == 2:
            # Pinned executing actor_ctrl.rs: seven operands including selector,
            # three actor operands, a u16 argument and a trailing byte.
            size, mnemonic = 7, "THREE_ACTOR_TALK"
            need(size)
            args = {"sub_op": sub, "actor_operands": list(data[operand + 1:operand + 4]),
                    "argument_u16": struct.unpack_from("<H", data, operand + 4)[0],
                    "trailing_operand": data[operand + 6],
                    "runtime_effect": "not_evaluated"}
        elif sub == 7:
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
        # Retail PROT897, 801E08C4: completion dispatch, not a claim
        # that the menu is complete. A/B and out-of-range forms have
        # no advancing completion path.
        sizes = {1: 2, 3: 2, 7: 2, 2: 6, 4: 6, 5: 13,
                 6: 4, 8: 4, 9: 4, 0xC: 4, 0xD: 4}
        mnemonic = "STATE_RESUME"
        args = {"sub_op": sub, "can_wait_for_external_state": True, "runtime_state": "not_observed"}
        if sub == 0:
            # Retail801E08EC reads length at operand+2 (not pinned +1),
            # skips length arguments at+3, then walks one native payload.
            # Completion includes the terminator; the embedded bytes stay
            # opaque, not parent MES dialogue or editable script anchors.
            need(3)
            length = data[operand + 2]
            need(3 + length)
            payload = _native_payload_span(data, operand + 3 + length, "STATE_RESUME0")
            size = 3 + length + payload["length"]
            args.update(prefix_byte=data[operand + 1], argument_length=length,
                        arguments=list(data[operand + 3:operand + 3 + length]),
                        embedded_payload=payload, payload_ownership="runtime_menu_unresolved")
        else:
            if sub not in sizes:
                raise ImportError(f"unsupported STATE_RESUME sub-op 0x{sub:02x}")
            size = sizes[sub]
            need(size)
            args["payload"] = list(data[operand + 1:operand + size])
        branches = [{"pc": operand + size, "condition": "external_state_completed"}]
    elif op == 0x4B:
        need(2)
        size, mnemonic = 2 + 4 * data[operand], "ANIMATE"
        args = {"count": data[operand], "base_id": data[operand + 1]}
    elif op == 0x4C:
        need(1)
        sub = data[operand]
        if 0x00 <= sub <= 0x0F or 0x20 <= sub <= 0x2F:
            # Pinned menu_ctrl.rs and Retail PROT897 outer handlers:
            # 801E0C70 advances adjusted PC2; 801E0EB8 routes all paths
            # through801DF098, which also advances2 before returning.
            # Dispatch extension is already included in the header.
            size = 1
            mnemonic = 'PARTY_LEADER_REQUEST' if sub < 0x10 else 'PARTY_VIEW_SWAP_REQUEST'
            args = {'sub_op': sub, 'party_selector': sub & 7,
                    'party_binding': 'runtime_party_identity_unresolved',
                    'runtime_effect': 'not_evaluated'}
        elif 0x10 <= sub <= 0x1F:
            # Pinned menu_ctrl.rs outer nibble1 consumes five payload bytes
            # and advances unconditionally after the host call.
            size, mnemonic = 6, "MENU_CTRL_SUB1"
            need(size)
            args = {"sub_op": sub, "values": list(data[operand + 1:operand + 6]),
                    "destination_semantics": "host_defined"}
        elif 0x30 <= sub <= 0x3F:
            size, mnemonic = 1, "FIELD_STATE_CONTROL"
            args = {"sub_op": sub, "can_yield": sub in (0x30, 0x31, 0x37)}
            if sub in (0x35, 0x36):
                # Retail PROT[897] 801E0F84/801E0F9C: LHU/SH ctx+62,
                # PC+2, literal AND/OR, including the jump delay-slot store.
                args.update(flag_word="actor_local_flags",
                            and_mask=0xFF7F if sub == 0x35 else 0xFFFF,
                            or_mask=0x020A if sub == 0x35 else 0x028A,
                            runtime_effect="not_evaluated")
        elif sub == 0x49:
            # Retail outer4 advances adjusted PC6 before sub9. All
            # flag-selected field4A/global-delta writes and ramp exits
            # return that advanced PC, including 801E175C and205C.
            # The pinned sub9 Yield descriptions disagree with retail.
            size, mnemonic = 5, "FIELD_4A_STATE_WRITE"
            need(size)
            args = {"sub_op": sub, "value": struct.unpack_from("<h", data, operand + 1)[0],
                    "ticks_signed": struct.unpack_from("<h", data, operand + 3)[0],
                    "runtime_field_mode": "story_word_bits_24_25_not_observed",
                    "runtime_effect": "not_evaluated", "can_yield": False}
        elif 0x40 <= sub <= 0x4D:
            # Retail 801E1138 adds 6 to the adjusted opcode PC. Sub43/44
            # handlers 801E1234/126C write or ramp ctx24/28 and preserve that
            # continuation. The pinned nibble_3_4.rs invents absolute jumps.
            # Sub45 has a wider form; never treat this cluster as uniform.
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
        elif sub == 0x80:
            # Retail 801E1ECC: halt-acquire success advances3, then
            # adds native MES-walker length+1 for each child payload.
            # Child ownership is external; never decode these as parent
            # instructions or infer an actor from the dispatch selector.
            need(2)
            count = data[operand + 1]
            cursor = operand + 2
            children = []
            for index in range(count):
                child = _native_payload_span(data, cursor, "MENU80 child")
                children.append({"index": index, **child})
                cursor += child["length"]
            size, mnemonic = cursor - operand, "ALLOCATE_CHILD_PAYLOADS"
            args = {"sub_op": sub, "count": count, "children": children,
                    "child_ownership": "runtime_allocator_unresolved", "runtime_effect": "not_evaluated"}
            branches = [{"pc": cursor, "condition": "halt_acquire_succeeded"},
                        {"pc": pc, "condition": "halt_acquire_pending"}]
        elif sub == 0x83:
            # Retail801E20A8 walks inclusive byte-coordinate bounds,
            # requests tile pool2, writes +2=value/+3=0 on lookup hit,
            # and returns adjusted PC+7 at212C/2130. It does not fall
            # through to the separate84 global write at2134.
            size, mnemonic = 6, "FIELD_TILE_RECT_REQUEST"
            need(size)
            args = {"sub_op": sub, "column_start": data[operand + 1],
                    "row_start": data[operand + 2], "column_end": data[operand + 3],
                    "row_end": data[operand + 4], "value": data[operand + 5],
                    "bounds": "inclusive_encoded_bytes", "tile_pool_selector": 2,
                    "tile_byte_writes": {"offset_2": data[operand + 5], "offset_3": 0},
                    "tile_binding": "runtime_lookup_unresolved", "runtime_effect": "not_evaluated"}
        elif sub in (0x82, 0x84):
            # Retail801E206C/2134: byte selector/value + two fixed writes,
            # adjusted PC+3. Native page table identity remains unresolved.
            size = 2
            need(size)
            mnemonic = "MIRROR_CHARACTER_FIELDS" if sub == 0x82 else "SET_GLOBAL_B630"
            args = {"sub_op": sub, "runtime_effect": "not_evaluated"}
            if sub == 0x82:
                args.update(character_selector=data[operand + 1],
                            field_pairs=[["0x6CC", "0x6CE"], ["0x6D0", "0x6D2"]],
                            actor_binding="runtime_character_table_unresolved")
            else:
                args.update(value=data[operand + 1], address="0x8007B630")
        elif sub == 0x89:
            # Retail801E22C8 uses the signed helper, stores the low word
            # at80073F00 and returns through the fixed PC+4 exit3620.
            size, mnemonic = 3, "SET_GLOBAL_73F00"
            need(size)
            args = {"sub_op": sub, "value": struct.unpack_from("<h", data, operand + 1)[0],
                    "address": "0x80073F00", "runtime_effect": "not_evaluated"}
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
        elif sub in (0x90, 0x91, 0x92):
            # Retail801E24B4 reads words at operand+2/+4/+6,
            # calls801DDE34, then advances adjusted PC9.
            size, mnemonic = 8, 'FIELD_FADE_REQUEST'
            need(size)
            args = {'sub_op': sub, 'selector': data[operand + 1],
                    'signed_words': list(struct.unpack_from('<hhh', data, operand + 2)),
                    'parameter_semantics': 'runtime_field_effect_unresolved',
                    'runtime_effect': 'not_evaluated'}
        elif sub == 0x9E:
            # Retail801E24F8 reads16 consecutive halfwords and advances34.
            # Destination stores and negated scratch values are runtime effects.
            size, mnemonic = 33, 'FIELD_TABLE_COPY'
            need(size)
            args = {'sub_op': sub, 'signed_words': list(struct.unpack_from('<16h', data, operand + 1)),
                    'destination_semantics': 'runtime_table_binding_unresolved',
                    'runtime_effect': 'not_evaluated'}
        elif sub == 0x9F:
            # Retail801E2548 ->801E2DC4 calls8003CF40 with801DA930;
            # its delay slot advances adjusted PC2 and returns that PC.
            # The pinned nibble_9_a.rs same-PC halt is not Retail continuation.
            size, mnemonic = 1, 'FIELD_CALLBACK_REGISTER'
            args = {'sub_op': sub, 'callback_address': '0x801DA930',
                    'registration_function': '0x8003CF40',
                    'callback_activation': 'not_observed', 'runtime_effect': 'not_evaluated'}
        elif sub in (0xA0, 0xA1, 0xA2):
            # Retail 801E255C..25DC adds 5 to adjusted PC and reads signed16
            # at operand+2 via 8003CE9C. Common3614/361C adds delta-2, yielding
            # operand+2+delta. The pinned nibble_9_a.rs incorrectly uses an
            # absolute target. All caller PCs are subsequently narrowed 16-bit.
            size, mnemonic = 4, "FLAG_WORD_BRANCH"
            need(size)
            delta = struct.unpack_from("<h", data, operand + 2)[0]
            target = (operand + 2 + delta) & 0xFFFF
            bank = {0xA0: "actor_flags", 0xA1: "actor_local_flags", 0xA2: "global_story_word"}[sub]
            args = {"sub_op": sub, "flag_word": bank, "bit_encoded": data[operand + 1],
                    "delta": delta, "target": target, "runtime_value": "not_observed"}
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
        elif sub in (0x8C, 0x8D):
            # Executing PROT897, 801E23EC/2404: adjusted PC advances by
            # 4/6, then shared360C/3614 adds signed16 delta-2. C reads at
            # operand+1; D match reads at operand+3 through3608. The pinned
            # VM's absolute targets and D no-match halt disagree with retail.
            size = 3 if sub == 0x8C else 5
            need(size)
            relative = 1 if sub == 0x8C else 3
            delta = struct.unpack_from("<h", data, operand + relative)[0]
            target = (operand + relative + delta) & 0xFFFF
            mnemonic = "FIELD_68_BRANCH" if sub == 0x8C else "ACTOR_SEARCH_BRANCH"
            args = {"sub_op": sub, "delta": delta, "target": target,
                    "runtime_effect": "not_evaluated"}
            if sub == 0x8C:
                args.update(field_offset="0x68", runtime_value="not_observed")
                matched, other = "field_68_zero", "field_68_nonzero"
            else:
                args.update(character_selector=data[operand + 1], marker=data[operand + 2],
                            actor_binding="runtime_search_table_unresolved")
                matched, other = "search_match", "search_empty_or_no_match"
            branches = [{"pc": target, "condition": matched},
                        {"pc": operand + size, "condition": other}]
        elif sub == 0x8A:
            # Pinned executing menu_ctrl/nibble_8.rs: fixed header+10
            # continuation after three signed words and one packed u24.
            size, mnemonic = 10, "WRITE_FIELD_QUAD"
            need(size)
            args = {"sub_op": sub,
                    "signed_words": list(struct.unpack_from("<hhh", data, operand + 1)),
                    "packed_u24": int.from_bytes(data[operand + 7:operand + 10], "little"),
                    "destination_semantics": "host_defined"}
        elif sub == 0xD8:
            # Retail PROT[897] 801E2DD4 reads selector+three signed
            # words. First word adds a runtime global then wraps i16;
            # 801E2E18 calls801D77F4 and 801E2E24 advances adjusted PC9.
            # Pinned nibble_d agrees on layout, not the runtime offset.
            size, mnemonic = 8, "FIELD_WORD_TRIPLET_REQUEST"
            need(size)
            args = {"sub_op": sub, "selector": data[operand+1],
                    "signed_words": list(struct.unpack_from("<hhh", data, operand+2)),
                    "first_word_adjustment": "runtime_offset_then_signed_16_wrap",
                    "runtime_offset": "unknown",
                    "parameter_semantics": "runtime_selector_and_word_meanings_unresolved",
                    "runtime_effect": "not_evaluated"}
        elif sub in (0xD4, 0xD5):
            # Retail PROT[897] 801E2C3C/2CC8: two word loads into a
            # fixed16x1 VRAM rectangle; StoreImage/pixel mask/LoadImage,
            # then common801E2D58 adds6 to adjusted PC. Pinned nibble_d
            # agrees. This is source inspection, not a VRAM simulation.
            size = 5
            need(size)
            mnemonic = "VRAM_STP_SET_REQUEST" if sub == 0xD4 else "VRAM_STP_CLEAR_REQUEST"
            args = {"sub_op": sub, "vram_x": int.from_bytes(data[operand+1:operand+3], "little"),
                    "vram_y": int.from_bytes(data[operand+3:operand+5], "little"),
                    "width": 16, "height": 1,
                    "pixel_rule": "set_bit_15_for_nonzero_pixels" if sub == 0xD4 else "clear_bit_15_except_0x8000",
                    "asset_binding": "runtime_vram_source_asset_unresolved",
                    "runtime_effect": "not_evaluated"}
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
        elif sub == 0xE1:
            # Retail801E30B8 optionally calls8003C764, then always walks
            # the payload through8003CA38. It advances adjusted PC by
            # 3 + walker length (which excludes its terminator).
            # Keep native child bytes atomic; they are not parent MES text.
            payload = _native_payload_span(data, operand + 1, 'MENU_E1 text-actor')
            size, mnemonic = 1 + payload['length'], 'TEXT_ACTOR_PAYLOAD_REQUEST'
            args = {'sub_op': sub, 'embedded_payload': payload,
                    'nonzero_first_byte': data[operand + 1] != 0,
                    'payload_ownership': 'runtime_text_actor_not_parent_dialogue',
                    'actor_binding': 'runtime_allocation_unresolved',
                    'runtime_effect': 'not_evaluated'}
        elif sub == 0xE2:
            # Retail801E30E4 reads a signed halfword at+1, stores it at
            # 8007BA78, sets8007B83C=26, and returns PC+6. The final two
            # operand bytes are consumed but not read by this handler.
            size, mnemonic = 5, "FMV_TRIGGER_REQUEST"
            need(size)
            args = {"sub_op": sub,
                    "fmv_id_signed": struct.unpack_from("<h", data, operand + 1)[0],
                    "trailing_bytes": list(data[operand + 3:operand + 5]),
                    "native_writes": {"0x8007BA78": "fmv_id_signed", "0x8007B83C": 26},
                    "runtime_effect": "not_evaluated"}
        elif sub == 0xE3:
            # Retail801E3108 resolves selector+1, copies actor fields into
            # current s5 (not camera -> resolved actor), then advances3.
            # Missing lookup skips only the copy; current-context post-updates
            # still run. No selector is correlated to an imported actor here.
            size, mnemonic = 2, "ACTOR_STATE_COPY"
            need(size)
            args = {"sub_op": sub, "actor_selector": data[operand + 1],
                    "copy_direction": "resolved_actor_to_dispatch_context",
                    "field_offsets": ["0x14", "0x16", "0x18", "0x26"],
                    "on_lookup_miss": "no_field_copy",
                    "source_lookup": "0x8003C83C", "actor_binding": "runtime_lookup_unresolved",
                    "runtime_effect": "not_evaluated"}
        elif sub == 0xEB:
            # Retail801E34DC advances adjusted PC5 before actor lookup.
            # On miss,801E360C loads the word at sub-op+2, subtracts2,
            # and adds it to that advanced PC. Thus the relative base is
            # the word location, not an absolute PC as pinned Andrew claims.
            size, mnemonic = 4, "ACTOR_LOOKUP_BRANCH"
            need(size)
            word_pc = operand + 2
            raw = struct.unpack_from("<H", data, word_pc)[0]
            target = (word_pc + raw) & 0xFFFF
            args = {"sub_op": sub, "actor_selector": data[operand + 1],
                    "target_word": raw, "target_word_pc": word_pc,
                    "target_pc": target, "encoding": "relative_u16_wrap16",
                    "actor_binding": "runtime_lookup_unresolved",
                    "runtime_effect": "not_evaluated"}
            branches = [{"pc": operand + size, "condition": "actor_lookup_found"},
                        {"pc": target, "condition": "actor_lookup_missing"}]
        elif sub == 0xEA:
            # Retail table801CF030 ->801E34CC calls8003C7EC and adds2
            # to PC in its delay slot, then returns advanced s8. Pinned halt is false.
            size, mnemonic = 1, "FIELD_CALLBACK_C7EC"
            args = {"sub_op": sub, "callback_address": "0x8003C7EC",
                    "runtime_effect": "not_evaluated"}
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
            need(size)
            if sub == 0x50:
                value = struct.unpack_from("<h", data, operand + 1)[0]
                args.update(model_selector_signed=value, model_selector_u16=value & 0xFFFF,
                            high_pool_flag=value >= 0xF0, asset_binding="runtime_pool_bases_unresolved",
                            runtime_effect="not_evaluated")
            if sub == 0x51:
                x, z, depth, move = data[operand + 1:operand + 5]
                args.update(x_encoded=x, z_encoded=z, depth_encoded=depth, move_id=move,
                            target_position={"x": (x & 0x7F) * 128 + 64 + (64 if x & 0x80 else 0),
                                             "y": None,
                                             "z": (z & 0x7F) * 128 + 64 + (64 if z & 0x80 else 0)},
                            coordinate_system="retail_field_world_units",
                            parked_target=(x & 0x7F, z & 0x7F) == (0x7F, 0x7F),
                            runtime_effect="not_evaluated")
        else:
            raise ImportError(f"unsupported MENU_CTRL sub-op 0x{sub:02x}")
    elif op == 0x4F:
        # Retail801E0C0C reads three bytes, zero-extends into scene
        # halfwords10/12/14, then advances adjusted PC4. Not a jump.
        size, mnemonic = 3, "SCENE_REGISTER_WRITE"
        need(size)
        args = {"values": list(data[operand:operand + size]),
                "field_offsets": ["0x10", "0x12", "0x14"],
                "runtime_scene": "not_observed", "runtime_effect": "not_evaluated"}
    elif op == 0x4E:
        # Retail PROT897 801E0A04..0C08: selector, source/comparison
        # nibbles, signed threshold, relative target word at operand+4.
        # Bank sources A/B add a high threshold word after the target.
        # Default sources C..F and comparison modes2..F never branch.
        need(2)
        selector, mode = data[operand:operand + 2]
        source, comparison = mode >> 4, mode & 15
        size = 8 if source in (10, 11) else 6
        need(size)
        low = struct.unpack_from("<H", data, operand + 2)[0]
        threshold = struct.unpack_from("<h", data, operand + 2)[0]
        if size == 8:
            threshold = struct.unpack_from("<i", struct.pack("<HH", low,
                        struct.unpack_from("<H", data, operand + 6)[0]))[0]
        delta = struct.unpack_from("<H", data, operand + 4)[0]
        target = (operand + 4 + delta) & 0xFFFF
        sources = {0: "character_field_6ce_scaled_by_6cc",
                   1: "character_field_6d2_scaled_by_6d0", 2: "character_level_6f8",
                   3: "bank_8008459c", 4: "bios_random_low_byte",
                   5: "slot_table_0", 6: "slot_table_1", 7: "slot_table_2", 8: "slot_table_3",
                   9: "bank_800845a4", 10: "bank_8008459c", 11: "bank_800845a4"}
        args = {"selector": selector, "source_mode": source, "comparison_mode": comparison,
                "value_source": sources.get(source, "zero_default"),
                "threshold": threshold, "threshold_width": 32 if size == 8 else 16,
                "threshold_scaling": "runtime_factor_mul_i32_div256_toward_zero" if source < 2 else "none",
                "delta_u16": delta, "encoded_target": target, "runtime_value": "not_observed"}
        enabled = source < 12 and comparison in (0, 1)
        mnemonic = "VALUE_COMPARE_BRANCH" if enabled else "VALUE_COMPARE_CONTINUE"
        if enabled:
            args["comparison"] = "value_lt_threshold" if comparison == 0 else "threshold_lt_value"
            branches = [{"pc": target, "condition": "comparison_true"},
                        {"pc": operand + size, "condition": "comparison_false"}]
        else:
            branches = [{"pc": operand + size,
                         "condition": "source_default_no_branch" if source >= 12 else "comparison_mode_no_branch"}]
    elif 0x50 <= op <= 0x7F:
        # Retail 801E3568 routes the complete raw 5x/6x/7x range. It reads
        # index at s0+1 and TEST delta at s0+2/+3. Extended prelude adjusts
        # operand(s6) and PC but never s0; the pinned generic extended
        # interpretation therefore has unproved operand/selector semantics.
        if header != 1:
            raise ImportError("extended SYSFLAG raw operand addressing is unresolved; no generic header interpretation")
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
    # Conditional capture bytes remain opaque, but cannot also become parent
    # instructions through another queued edge. Keep this separate from exact
    # instruction ownership so the report does not count them as decoded bytes.
    conditional_capture = {}
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
        if pc in conditional_capture:
            stops.append({"pc": pc, "owner_pc": conditional_capture[pc],
                          "reason": "decoded path enters conditional capture ownership; parent region is ambiguous"})
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
            if any(byte in conditional_capture for byte in range(pc, pc + row["length"])):
                stops.append({"pc": pc, "reason": "decoded boundary overlaps conditional capture ownership; parent region is ambiguous"})
                conflict = True
                continue
            if not is_message and row["mnemonic"] == "EFFECT_SPAWN_PACKET" and "capture_payload" in row["operands"]:
                payload = row["operands"]["capture_payload"]
                capture_range = range(pc + row["length"], payload["pc"] + payload["length"])
                if any(byte in ownership or byte in conditional_capture or byte in entries for byte in capture_range):
                    stops.append({"pc": pc, "reason": "conditional capture ownership conflicts with a decoded or queued parent path"})
                    conflict = True
                    continue
                for byte in capture_range:
                    conditional_capture[byte] = pc
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
            "entry_pc": script_offset,
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
        from .man_source import read_man_source
        carrier=read_man_source(archive,start,end,scene)
        man=carrier.payload
        consumed=carrier.encoded_size if carrier.kind=='descriptor_man' else None
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
                "man_source":carrier.provenance(),
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
