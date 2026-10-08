# Animation Script Operands

The fixed native writer is implemented and qualified. Project commands, editor controls, Current inspection, normal Build integration and clone-owned NPC editing are still pending. This is a foundation for script authoring, not a completed editor workflow or gameplay acceptance.

The immutable reference is Andrew Altimit's `d6e64c68ede25813d35db20980da82a1a025549b`, inspected from the read-only local checkout. `crates/engine-vm/src/field/step/menu_ctrl/nibble_8.rs`, sub-operation 1, reads three little-endian fields and advances by the header plus eight bytes. `crates/engine-vm/src/field/step/effect.rs`, high nibble 3, reads one argument and advances by the header plus two bytes. These agree with the SDK's existing source decoder.

| Instruction | Authored fields | Immutable native dispatch |
| --- | --- | --- |
| SET_MODEL_ANIMATION | model_id: unsigned 24-bit; animation_frame: unsigned 16-bit; tween_frames: unsigned 16-bit | Opcode 0x4C, selector 0x81, optional extended context |
| EFFECT_ANIMATION_TRIGGER | animation_operand: unsigned 8-bit | Opcode 0x34, selector high nibble 3; low nibble and optional extended context retained |

These names describe encoded instruction arguments. Numeric model/effect arguments are not resolved SDK asset or clip identities. Frame/tween units, valid content ranges, host effects and animation playback remain unverified. The variable-length ANIMATE instruction remains outside this writer until its element layout and ownership are implemented.

`integrations/legaia/importer/animation_operand_authoring.py` reuses verified MAN source ownership. Stable target IDs derive from scene, P1 actor/P2 script owner and four-digit hexadecimal instruction PC. A record must have no unknown or conflicting reached-path decoder stops. Edits require an exact field set and strict integers within native widths; booleans are rejected. No rounding, clamping, opcode replacement or guessed clip binding occurs.

Each changed field receives an audit with its source identity, context, PC, before/after values, byte extent and record/MAN hashes. Complete instruction layout and continuations remain unchanged. Original source buffers are immutable. Multiple independent instructions in the same record compose without erasing earlier edits.

The appended-MAN path rebases existing source owners after table growth, verifies unique record ownership and unchanged record extent, and checks the entire source instruction preimage even for a no-op. Only audited changed field spans are copied. Added NPC scripts themselves are not editable through this original-owner API.

Four focused Python tests passed with the private Retail disc enabled, with no failures, errors or skips. Synthetic checks cover ordinary/extended dispatch, all field widths, exact literal bytes, independent instructions in one record, appended rebasing, immutable no-ops, altered selector/context/preimage refusal, aliases, unknown/unreached instructions and foreign identities. The Retail check found 10 qualified instructions in Town01 and 25 in Map02, across both supported families; 92 changed fields matched an independent complete-MAN literal oracle, with MAN structure and all unrelated bytes retained. The boundary values prove encoding integrity, not that those values are valid gameplay content. Unsupported records stayed unavailable; no gates were weakened to obtain coverage.

Private evidence: `local-output/sdk-20260909/animation-operands-20261008/native.json`. It includes source hashes and per-owner discovery/refusal information; extracted bytes stay outside tracked documentation. No native Build, game, runtime attachment, install or disc export ran for this foundation.

The next implementation step is a coherent Review/Apply command workflow with Undo/Redo and Save/Open, followed by native Build composition and readback, editor and Current navigation, clone-owned NPC editing and portable presets. Those remain required before this capability can be classified as an authoring workflow. Manual gameplay can be deferred while those layers are implemented.
