# Source field-script facing operands

The SDK can inspect and author the facing sector in reached simple `CAM_CFG`
and nonparked `NPC_RUN` instructions. This is an exact source-operand operation.
It does not supply a general initial or live actor heading: the placement header
has no facing field, story branches choose instructions, extended dispatch can
target another actor, and subsequent instructions can replace the value.

## Retail mechanism proof

The implementation gate was verified statically from the user-owned North
American disc, without running the game. Disc SHA256:
`e6120a5d70716dd2f026a2da32d0171d52651971b52c4347a68541299f75258c`.

SCUS executable SHA256:
`292256e2e66db42727f613406785e444254d3f699569e611f65fcf1c6d2f3482`.
Its PS-X EXE load address is `0x80010000`. The direction LUT at guest
`0x80073F04`, executable file offset `0x64704`, contains eight little-endian
16-bit direction values `[0, 512, 1024, 1536, 2048, 2560, 3072, 3584]`.
The next eight addressable entries are other data, so sectors 8..15 are rejected.
The 32-byte table span SHA256 is
`b66eda11dc88faa4fcc6bfb9543a987bc97380588e058f97a12f5660f4313977`.

Fresh PROT entry 897 starts at relative LBA 47072, is 159 sectors / 325632 bytes,
and has SHA256
`216f846db5ab085a295cef4064747380a06c995caa3e1b2773e78a1d349f126b`.
The field overlay base is `0x801CE818`. Its first 202728 bytes exactly match the
existing known field-overlay capture, SHA256
`3026cd12a22c12f94ed05ef5af551df786267d2d29c330b5c57e82c5ec5aae19`.
The following mechanisms were read from the fresh retail entry, rather than
deduced solely from a reconstructed reference helper or the LUT contents.

| Source mechanism | Retail guest addresses and facts |
|---|---|
| Instruction header and extended context | `0x801DE858..0x801DE860` sets instruction pointer from source base + PC and operand pointer to lead + 1. `0x801DE880..0x801DE8B0` tests opcode bit 7 and resolves the encoded context. `0x801DE948..0x801DE94C` advances operand pointer and PC by one for that extended header. |
| Main opcode dispatch | `0x801DE950..0x801DE980` masks opcode with `0x7F`, subtracts `0x21`, and indexes the jump table at `0x801CECC0`. |
| `CAM_CFG` route | Opcode `0x38` table entry `0x801CED1C` points to `0x801DEE58`. |
| `CAM_CFG` scalar gate | `0x801DEE58` reads operand + 1; `0x801DEE60` masks it with `0x7F`; `0x801DEE64` branches to the different halt-acquire path when nonzero. |
| `CAM_CFG` facing write | `0x801DEE6C` reads operand + 0, `0x801DEE74` masks with `0x0F`, then the value is doubled and added to `0x80073F04`. `0x801DEE80` loads the LUT halfword. The jump delay slot at `0x801DEE8C` stores it to context + `0x26`. |
| `NPC_RUN` route | Opcode `0x4C` entry `0x801CED6C` points to `0x801E0C3C`. Outer nibble 5 indexes `0x801CEE74` to `0x801E1780`; inner nibble 1 indexes `0x801CEF34` to `0x801E1828`. |
| `NPC_RUN` preserved flag | `0x801E1828..0x801E1858` reads operand + 3 and uses bit 7 to set or clear context flag `0x01000000`. This upper bit remains unchanged by facing authoring. |
| `NPC_RUN` facing write | `0x801E18E4` reads that same operand + 3; `0x801E18EC` masks with `0x0F`; doubling/addition indexes `0x80073F04`; `0x801E18F8` loads the LUT halfword and `0x801E1900` stores context + `0x26`. |

The `CAM_CFG` write block `0x801DEE58..0x801DEE90` has SHA256
`372b08c651c0f4cbd4fbc9c32dcd51565c91400735ccfd4cab101c661f68bc24`.
The inspected `NPC_RUN` span `0x801E1828..0x801E1A68` has SHA256
`4267a1760dd9873712b272fd57fe33d6d72e2c323740495ec972af90422dea43`.
The encompassing dispatcher span `0x801DE840..0x801E3658` has SHA256
`e601bb7d9f45ad1dc3e85a105d2e758833205e784e93fd2bd195f4e19df9bf2f`.
These are metadata anchors; retail instruction streams and extracted assets are
not included in this document or repository tests.

Sector `s` therefore writes retail facing `s * 512`. Andrew's renderer converts
that to `(retail_facing + 2048) & 4095`; that renderer convention is separate from
the serialized operand and is not an additional authored value.

## Source authoring contract

`importer.facing_authoring.FacingAuthoringContext` shares the immutable,
uniquely owned MAN records qualified by `DialogueAuthoringContext`. It accepts
P1 actor and supported P2 script owners. Every candidate is identified by
`script://<source-owner-without-scene-scheme>/facing/<four-hex-digit-PC>`.

`options(owner)` returns `supported`, `targets`, `unavailable`, `reason`,
`source` and `limitations`. Each target carries the source owner and exact PC,
mnemonic, encoded dispatch target, exact decoded MAN operand byte offset,
source record SHA256, `values: {sector}`, the full `before_raw` byte and
`preservation_mask: 240`. Extended context values remain source operands;
their runtime binding is not asserted.

`validate_facing_values` accepts exactly `{sector: integer 0..7}`. `patch(edits,
original=None)` qualifies the complete requested edit set against the immutable
source and returns an equal-length MAN plus a detached, ordered byte audit. An
optional `original` must match that source exactly. It writes
`(original_byte & 0xF0) | sector`; all other bytes remain unchanged. Audit rows
contain facing/owner IDs, PC, mnemonic, encoded context, record-relative and
decoded MAN offsets, original/new bytes and sectors, record SHA256 and decoded
MAN SHA256. Unchanged values yield no changes.

The service rejects aliased records, unknown/conflicting full-script stops,
unreached PCs, malformed identities, additional client fields, booleans and
out-of-range sectors. `CAM_CFG` requires operand + 1 masked with `0x7F` to be
zero; its facing byte is at PC + header size. `NPC_RUN` requires a nonparked
target; its facing byte is at PC + header size + 3. A parked target has both
low-seven-bit coordinate values equal to 127. Source sectors above 7 cannot be
rewritten through this supported direction workflow.

The existing `depth_encoded` name on `NPC_RUN` does not imply a scalar depth or
speed authoring field. Facing edits preserve all four upper bits, including the
proved bit-7 model flag, and leave X/Z and the move selector intact. Existing
movement edits can compose on their distinct source bytes; the final Build
must validate the complete source-qualified composition and compressed carrier.
This serializer deliberately has no appended-NPC rebasing method. Experimental
donor-append export must reject projects with `ScriptFacing` edits until that
separate workflow has qualified source relocation and initialization behavior.

## Initial-facing limits and reference provenance

SCUS source instructions `0x8003A474..0x8003A4F8` independently prove the
installation prologue gate: first raw opcode must be exactly `0x24` or `0x25`;
the loop calls `0x801DE840`, stops after raw `0x21`, a masked opcode below
`0x20`, or a non-advancing returned PC. This proves the retail execution
mechanism, not which branch current story flags choose.

Pinned Andrew revision remains
`d6e64c68ede25813d35db20980da82a1a025549b`:

| Pinned source | Blob SHA1 | Evidence used |
|---|---|---|
| `crates/engine-core/src/man_field_scripts/npc_motion.rs:451–507` | `a8573a0f44b09a81290cffbea31e4aac42b96c35` | First linear prologue-facing interpretation, cross-context/parked exclusions and renderer conversion. |
| `crates/engine-vm/src/field/step.rs:290–322` | `9c7801d1626c6f6eb8bd48f9f7c3e5851379e674` | Simple versus halt-acquire `CAM_CFG` paths, corroborated by the retail dispatch. |
| `crates/engine-vm/src/field/step/menu_ctrl/nibble_5_6_7.rs:72–94` | `0146f87c0c381d06ffaa14d27f4f8197b04ec587` | `NPC_RUN` operand structure. |
| `docs/subsystems/field-locomotion.md:758–773` | `220746dd6a415bfd61cc8982f18c9aae691279d4` | No placement facing field, LUT convention and NPC operand interpretation. |

The reference `placement_initial_facing` chooses the first linear facing leg
and does not evaluate story flags. Its result remains a reference-derived
candidate, not a proven current initial heading. Fresh Town01 inventory found
52 marker-bearing actors, 33 with own linear facing candidates and 85
`NPC_RUN` candidate writes; 23 of those actors have no full-script stops. None
has one unconditional linear prologue facing candidate. Authoring a chosen
source instruction is supported; replacing that uncertainty with a universal
actor heading would be unsupported.

## Focused offline evidence

`tests/test_facing_authoring.py` covers both opcode families and normal/extended
headers, preserved high bits and instruction shape, source/identity validation,
no-op/atomic composition, aliased and unknown/conflicting records, nonscalar
and parked exclusions, detached metadata and raw streaming sources. Retail
checks skip cleanly without `LEGAIA_DISC_BIN`; with the private disc they verify
the actual dispatch tables, operand masks, context writes and LUT, then make
exact single-byte changes in Town0b and Town01 source records.

Town0b actor `scene://town0b/actors/man-p1/0019` provides an unconditional
`CAM_CFG` fixture: record offset 9461, length 113, record SHA256
`04659e35af297acefa6b11fc9d1222d7ea9e5f12790297184d296655603ac6d2`;
entry PC 13 with marker `0x25`; `CAM_CFG` PC 17 (`0x11`), operand + 0 at decoded
MAN offset 9479 is `0x81`, operand + 1 is zero, terminator PC 37 is `0x21`.
Setting sector 3 changes only offset 9479 from `0x81` to `0x83`, retaining its
upper flag. Its decoded MAN SHA256 is
`ba0333709dc512cbd9f35a6e6c5323f444138e5877171486fcc5636b2a9f50be`;
the carrier is PROT entry 11, stream offset 165206, consumed length 28024.

Town01 actor `scene://town01/actors/man-p1/0014` has a supported `NPC_RUN`
source instruction at PC 33 (`0x21`), source sector 2. Changing it to sector 6
changes only its facing operand and preserves the MAN placement header.
Its branch execution and visible heading remain gameplay verification items.
No game launch, runtime observation, input, audio, or current-story acceptance
is implied by these offline checks.

## Connected editor, project and Build

Select an imported actor and choose **Inspect facing instructions** in the
shared Inspector. In Script facing operands, choose a source instruction and
enter sector0–7. The compass previews that instruction operand: sector0 sits at
the top of the diagram; retail angle is sector×512 and degrees are sector×45.
The Retail/Authored/Effective table remains distinct from an unapplied draft.
Apply facing, Clear facing override and Discard facing draft connect to guarded
commands. Pending drafts disable project history/save actions. Closing or
refreshing the script disposes its owned controls. P2 script inspections support
the same source qualification and display encoded context uncertainty.

`ScriptFacing: {entries: {facing_id: {sector}}}` persists as an authored component.
`set_facing_target` accepts only type, entity_id, facing_id and values;
`clear_facing_target` accepts only the first three. Set requalifies the entire
owner edit set against fresh source; identical authored commands add no history.
Clear remains available offline for a syntactically valid source owner. Import
metadata stays immutable. Component review/removal, Undo/Redo, Save/Open and
source-bound operand JSON/bundles preserve the same identities and limits.

Normal Build reimports source, rediscovers each exact candidate and verifies
source record/MAN hashes, owner/PC/context, original byte, requested low nibble,
unchanged upper nibble, nonoverlap and every other byte. It composes facing with
supported MAN families before carrier serialization and independent decode.
Experimental appended-NPC Export disc remains unsupported for ScriptFacing.

Central validation passed56 retail-enabled Python tests without skips in70.133s,
7 relevant Node checks and3 changed-module syntax checks. Nine real browser
workflow checks passed with zero page/HTTP errors and zero run requests;
Draft/Effective screenshots were visually inspected. A fresh real P2 script
`scene://town0b/scripts/man-p2/0008` validates/renders31 facing controls, including
NPC_RUN PC207, encoded context49, source MAN byte31233. The supplemental HTTP
check authors/clears that instruction without asserting its runtime target.

Retained private fixture: `local-output/sdk-20260909/script-facing-20261002/project/`.
It sets Town0b actor0019 CAM_CFG PC0x0011 to sector5. Independent original-disc,
compressed-MAN and ZIP readback proves exactly MAN9479 changes0x81→0x85:
retail sector1/512/45° becomes authored sector5/2560/225°; bit0x80 remains intact.
The changed MAN SHA256 is `267738766cb13cbc7a2b2093ab06d8b7715d1b7247d169348180ec1a85a9a993`.
The built package is `authored-build/legaia.sdk.760132307200-0.1.0-19dab14dc2db8d24.psxmod`
under that fixture's parent proof directory, SHA256
`556dbae3db541bbd729188d81832ace68aeceac381d74c85495038c06d6c36ea`.
`build-check.json`, browser/Node/Python logs and screenshots remain private there.
No package installed or game launched. Later acceptance remains in the
[gameplay queue](legaia-gameplay-verification-queue.md); full SDK/runtime scope
is still incomplete.
