# Legaia reverse-engineering provenance

The reference repository is `AndrewAltimit/legend-of-legaia-re`, pinned to
`d6e64c68ede25813d35db20980da82a1a025549b`. It is an optional development reference
and parity oracle, not a runtime dependency, submodule or bundled implementation.
The 2026-09-09 importer work read the exact commit through `git show` in the
existing read-only reference checkout. The pin was not advanced.

The 2026-09-10 opening-trigger investigation uses the same pin's
`crates/engine-vm/src/field/step/menu_ctrl/nibble_e.rs::op_4c_ne`
(blob `61ad972bd5455bdb84b1ab376f6ad959cb23190b`) for MENU_CTRL ED/E8
operand widths and encoded continuations. P2 record 3 remains partially
decoded, and locating text inside its bytes does not authorize editing it.
See `legaia-sdk/trigger-script-inspection.md` for the bounded source check.

Our previous independently implemented SDK source was recovered from
`legaia-sdk-integration`, commit `28ce54367127e858c8ef2bfbd27ffe64f60e0e93`.
Current implementation remains in this Recomp checkout. SDK-Clone,
LegaiaRecomp and Andrew's checkout are references only.

The texture/animation resource-browser adapters reuse these verified decoders
without extending their format claims. Town01 discovery exposes 96 structural
TIM identities and 14 scene ANM identities through 39 validated MAN bindings.
Resource records contain source hashes/locators and counts, not pixel or frame
payloads. TIM-local palettes are inspection choices; animation timing and
unreferenced clip compatibility remain unknown.

| Knowledge | Exact Andrew source | Interpretation and current limit |
|---|---|---|
| Mode2/ISO | `crates/iso/src/raw.rs`, `iso9660.rs` | Sector payload and ISO traversal; exact SCUS build hash gate |
| PROT/CDNAME | `crates/prot/src/archive.rs`, `cdname.rs` | Structural ranges and raw TOC minus two conventions |
| Scene bundle | `crates/asset/src/scene_asset_table.rs`, `crates/engine-core/src/scene_bundle.rs` | Bounded descriptor/embedded table and MAN carrier detection |
| LZS | `crates/lzs/src/lib.rs` | 4KB ring decoder; retail `FUN_8001A55C` reference |
| MAN actor placement | `crates/asset/src/man_section.rs` | Partition1/local prefix/model selector/tile coordinate rules; retail `FUN_8003A1E4`, `FUN_8003D0BC`; no invented facing or height |
| Model pools | `crates/engine-core/src/scene_resources.rs`, `crates/asset/src/character_pack.rs`, `crates/web-viewer/src/field_npc.rs` | Scene/global structural model enumeration and 0xF0 selector boundary |
| TMD objects | `crates/tmd/src/lib.rs`, `mesh/basic.rs` | Relative pointers, 28-byte objects, signed vectors and quad split; no object pose inference |
| Legaia primitives | `crates/tmd/src/descriptor.rs`, `legaia_prims.rs` | Grouped packets, renderer mode rows, byte-offset vertex indices, color/UV/CLUT/tpage; retail `FUN_8002735C`, `FUN_80029888`, `DAT_8007326C` |
| TIM and scene textures | `crates/tim/src/lib.rs`, `crates/prot/src/timpack.rs`, field texture-uploader documentation | Structural pixel/CLUT uploads, static tpage/UV association; runtime residency and animation remain unresolved |
| Preview display axes | `crates/asset/src/scene_gltf.rs` | PSX mesh-local positive Y is down; display-only Y negation preserves raw model vertices |
| MAN runtime candidates | `docs/subsystems/script-vm.md`, `scripts/pcsx-redux/walk_actor_lists.py`, `crates/web-viewer/src/field_npc.rs` | Guarded actor+0x90 header and independent model-count evidence; no list-order or address identity |
| Field-party animation | `crates/asset/src/player_anm.rs`, `character_pack.rs`, `crates/engine-core/src/field_anim.rs`, `crates/tmd/src/mesh/{mod,vram_posed}.rs` | Six F0/F1/F2 idle/walk clips; ten rigid object channels; reference-derived 30 Hz; independent transform comparison, no live timing or exact GTE claim |
| Shared party textures | `crates/asset/src/field_char_textures.rs`, `pack.rs`, `crates/asset/tests/field_char_textures_real.rs` | PROT0874 section2 loader upload/CLUT rules; exact reference VRAM fingerprint and eight used material crops; no general scene residency claim |

Detailed inspected symbols, validation counts and unsupported cases live in
`integrations/legaia/provenance/importer-20260909.md`. The restored machine-readable
reference manifest preserves earlier source locators. Reference statements
about runtime behavior are reference evidence, not a claim that this import
session traced the running game. Imported metadata carries source spans,
disc identity, confidence, unresolved fields and claim evidence.

Runtime source provenance and the mixed known-good binary/source audit are in
`legaia-release-parity.md`. This document does not equate a later generated
source tree with the older known-good executable. Generic protocol restoration
must retain current runtime timing/performance improvements and adapt storage
and SHA APIs rather than overwrite newer files wholesale.

No proprietary disc/EXE/model/texture/dialogue, card, savestate, screenshot or
generated native game code belongs in Git. Actual imports, previews and builds
are local ignored evidence. Synthetic fixtures remain independently constructed.

Detailed animation and shared-texture controls are recorded in
`integrations/legaia/provenance/animation-20260909.md` and
`integrations/legaia/provenance/field-party-textures-20260909.md`. The independently
implemented pose decoder matched 20,845 posed vertices within 0.0001 units;
the independently reconstructed shared VRAM matched FNV64 `64615c6915ba9a80`.

Static GLB interchange reuses those verified previews without new retail
semantic claims. `integrations/legaia/provenance/model-export-20260909.md`
records accessor/color/UV conventions, bounded static-pose scope, the Khronos
validator result and independent Blender import/render. The exporter embeds
source provenance, preserves source units with unknown physical scale, and
does not invent skin hierarchy or animation channels.

Scene-header animation evidence is recorded in
`integrations/legaia/provenance/scene-animation-20260909.md`. All 39 eligible
town01 actor poses match the unchanged pinned reference over 5,028 vertices
within 0.000039 units. The ANM carrier uses descriptor type 0x05 and retains
the importer's container-relative locator. The central viewport applies one
Y reflection after pose assembly; heading identity and unknown-height ground
placement are explicit display conventions, not recovered retail fields.

Bounded field-script and inline-dialogue interpretation is recorded in
`integrations/legaia/provenance/script-inspection-20260909.md`. Pinned
`crates/mes/src/lib.rs` supplies token widths/substitutions; the field VM and
disassembler supply supported instruction widths and successors. Message bytes
are consumed atomically, and unknown or conflicting boundaries remain opaque.
The editor does not evaluate story flags or infer a live conversation branch.
Retail dialogue remains private; tracked tests use hashes and synthetic text.
Supported equal-span text writing and its pinned source blobs are documented in
[dialogue authoring](legaia-sdk/dialogue-authoring.md). Unknown instruction paths
remain rejected for authoring; no script execution or relocation is inferred.
The central [script resource catalog](legaia-sdk/script-resources.md) retains
source-qualified flag operands and named scene-change references. It does not
infer current flag values, persistent story identities or reachable scene edges.

The writable donor-pair foundation is documented in
`docs/legaia-sdk/man-assignment-authoring.md`. It uses the existing MAN header,
scene TMD and ANM associations, restricts changes to evidenced same-scene pairs
with matching channel counts, and rejects compressed growth. Its retail
two-byte round trip establishes encoding only, not script or gameplay
compatibility. Subsequent editor/project/build integration passes bounded
appearance/position/text composition; gameplay appearance remains unverified.

Authored TIM replacement follows pinned Andrew revision
`d6e64c68ede25813d35db20980da82a1a025549b`, TIM parser blob
`99607f6265e223153cc47678bff1d65d59b0ea54` and TIM pack reader blob
`f90c89f1aba8adf012395a6d752cef49a41d4960`. The writer retains original headers
and verified member boundaries. Actual town01 raw-pack overlays were checked
against disc user bytes; compressed-carrier composition is synthetic coverage.
See `legaia-sdk/texture-authoring.md`; no retail payloads are tracked.

## Facing script inspection (2026-09-10)

At pinned Andrew revision d6e64c68ede25813d35db20980da82a1a025549b,
asset/src/field_disasm/decode_subops.rs and
engine-vm/src/field/step/actor_ctrl.rs agree on op43/sub7's header+16 width
and sub8's header+1 reset. Setup exposes face ID, u32 payload, four u16
parameters and signed target. The SDK now decodes these read-only and retains
extended target-context handling. This is pinned reference evidence, not new
retail execution validation. Current reference field_channels.rs additionally
explains why face ID is not a scalar heading: the operation configures a
rotation matrix/ramp. No heading editor, lookup table or VM execution is added.

Facing decoder retail non-regression: all32 script inspection/catalog/trigger
checks passed with the private disc. Instrumented town01/town0c catalog paths
contained zero decoded facing setup/reset operations. The catalogs remained
91/421/60 and74/287/48 (scripts/dialogues/partial scripts), respectively.
This verifies unchanged supported scene coverage, not retail execution or
occurrence of the new facing operations. Private facing-script-coverage.json
retains the observation.

## Flag-word conditional branches (2026-09-10)

Retail stop inventory identified five MENU_CTRL A0 boundaries across town01
and town0c. Pinned d6e64c68 engine-vm/field/step/menu_ctrl/nibble_9_a.rs defines
header+4 operands, a signed i16 absolute target and fall-through continuation;
field/host.rs identifies actor/local/global flag-word banks for A0/A1/A2.
Inspection retains encoded bit and both branches without evaluating runtime
state. Negative targets are not wrapped into valid record offsets.

A prior-decoder comparison on town01 isolated five newly decoded P2[4]
dialogue IDs at012f,014b,0165,01a3,01c0. Catalog totals are now91 scripts,
426 dialogue segments,517 script/dialogue assets,60 partial scripts and1134
flag references. All34 targeted retail-enabled checks pass. This is bounded
source decoding, not proof of branch execution or runtime flag identity.

The five newly visible P2[4] segments remain read-only: its graph has an
out-of-record target atPC5 and unsupported opcode27 atPC483. Retail authoring
options returned no writable runs; a direct edit was rejected with project
state unchanged. No playable build is claimed for these newly decoded segments.


### Scripted actor-position inspection (2026-09-10)

Pinned `d6e64c68ede25813d35db20980da82a1a025549b` reference files
`crates/asset/src/field_disasm/decode_subops.rs` and
`crates/engine-vm/src/field/step/actor_ctrl.rs` agree that ACTOR_CTRL sub9
consumes nine operand bytes: selector, three unsigned 16-bit coordinates and
unsigned 16-bit ticks. Inspection preserves those encoded values and the
unconditional encoded continuation. For zero ticks the executor leaves axes
with value0xffff unchanged; nonzero ticks delegate to a host tween, so the
inspector does not apply the sentinel rule or infer a resulting position there.
No runtime movement, heading, placement serialization or new writable field is
claimed. Normal/extended headers, truncations and sentinel scope pass focused
checks; all five retail-enabled script catalog tests pass with426 dialogue
segments and1134 flag references unchanged.

Halt-acquire sub0/1/A/B remains unsupported: the pinned executor reads the signed
target through operand+4/+8 but its failed-predicate continuation advances to
operand+4/+8. This overlap requires stronger retail evidence before assigning
instruction ownership. No guessed continuation was added to increase coverage.


The subsequent extended-context authoring check verifies that immediate and
timed ACTOR_POSITION instructions, including their unresolved target byte,
remain exactly unchanged when an adjacent five-byte glyph run is replaced.
Every non-glyph byte and the decoded instruction list compare equal before and
after the real patch operation. This supports source-span authoring integrity,
not target identity or runtime behavior. Eight dialogue-authoring tests passed
with retail input enabled; no new runtime patch or authoring restriction was
needed.


### Dialogue option menu inspection (2026-09-10)

Pinned d6e64c68ede25813d35db20980da82a1a025549b `crates/mes/src/picker.rs`
identifies bare27/28/29 controls as2/3/4-option menus. Each signed16-bit jump
is relative to its own table entry, not the open byte. A structurally complete
label region is required: labels may immediately follow the table, follow
24/25/48, or follow4C FF. Existing bounded MES decoding preserves label tokens.
Inspection consumes the complete menu atomically and exposes labels/encoded
targets, but leaves pager continuation unresolved with no traversed successors.
High-bit forms remain unsupported by this adapter; no runtime choice is inferred.

Town01 actor0001 exposes four options at PC107. Its real authoring options still
reject writing. Private picker-inspection.json retains source operands/stops;
retail text is not tracked. Four focused tests plus23 inspection and5 catalog
tests pass with retail enabled, including unchanged catalog totals. Shared
actor/trigger tables list labels and encoded targets; JavaScript syntax passes,
while browser layout and actual menu execution remain unverified.


The high-bit picker forms are now supported per the same pinned parser:
A7/A8/A9 still use a one-byte open control, not the field VM's extended target
header. Their first jump entry remains at open+1; target_context stays absent.
High-bit24/25/48 continuation controls also retain their one-byte footprint.
Raw control bytes remain preserved. Focused tests cover all counts, continuation
forms, raw identity and every truncation; generic extended field instructions
retain their previous handling. Twenty-eight focused/retail inspection tests
and five retail catalog tests pass. This supersedes the initial high-bit-form
limitation above, without resolving menu execution or authoring.


Pinned field/host.rs::op4c_n_a_flag_set maps0/1/2 to ctx.flags,
ctx.local_flags and host.global_flags(), masking the encoded bit to five bits.
The catalog now indexes FLAG_WORD_BRANCH using those same existing bank scopes,
while preserving unresolved local indices16..31. This adds exactly11 town01
references, taking1134 to1145; private flag-word-catalog.json lists their source
owners/PCs. The first retail count assertion correctly failed at the old total;
it was updated after isolating the new reference family. Seven tests then pass.


Menu inspection now follows only the per-choice encoded targets proved by the
pinned picker reference. It does not add a linear successor after the labels.
Pager continuation remains a known unresolved stop, preserving read-only status.
Compared in the same run against a decoder with menu successors suppressed,
town01 gains113 dialogue IDs and loses17 from P2[20] through existing graph
conflict rejection. Counts become522 dialogues,613 assets and1183 flag references;
60 partial scripts and one transition remain. Private menu-branch-coverage.json
records exact added/removed IDs. Synthetic coverage proves skipped opaque bytes
stay unvisited and an edge into a label invalidates the graph. Six focused,
23 inspection,7 catalog and8 authoring tests pass, with retail enabled where
applicable. No runtime reachability or new authoring support is claimed.
