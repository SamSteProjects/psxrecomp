# Legaia reverse-engineering provenance

The reference repository is `AndrewAltimit/legend-of-legaia-re`, pinned to
`d6e64c68ede25813d35db20980da82a1a025549b`. It is an optional development reference
and parity oracle, not a runtime dependency, submodule or bundled implementation.
The 2026-09-09 importer work read the exact commit through `git show` in the
existing read-only reference checkout. The pin was not advanced.

The 2026-10-02 material GLB extension uses the existing independently qualified
CLUT/TPage/group ABE source fields and masks. Actual Blender attribute readback
and independent byte comparisons verify indexed selector edits, TPage column
edits and untextured sentinels without source layout growth. Normal-reference
and stored normal edits survive composition and package readback. The reference
pin is unchanged; runtime blend mode and appearance are not inferred from the
source ABE or shader. Private proof:
`local-output/sdk-20260909/model-glb-materials-20261002/research/`.

The 2026-10-02 sparse world placement extension follows the same pinned
field_objects source gates, source XYZ/yaw and direct kingdom model dictionary
slots. An independent MAP walker qualifies all 301/272/236 seeds; raw TMD object
and packet readback matches all loaded topology and source member hashes. Source
transforms do not establish runtime resting positions or visibility. Ground
geometry and the reference pin remain unchanged; partial model texture coverage
is explicit. Private proof:
`local-output/sdk-20260909/worldmap-placements-20261002/research/`.

The 2026-10-02 world walk-ground importer follows the pinned kingdom-bundle and
field_objects::build_walk_heightfield conventions. Independent raw retail
qualification verifies canonical/overlapping PROT carriers, complete MAP spans,
slot-2 MAN floor LUTs and slot-0 TIM packs. Ordered source geometry, UVs and cell
selectors match all three kingdoms. Static atlas matching retains missing
palettes explicitly. No guessed mesh placement, menu-to-world mapping, overview
geometry or runtime parity is claimed; the reference pin remains unchanged.
Private evidence: `local-output/sdk-20260909/worldmap-geometry-20261002/`.

The 2026-10-02 normal-reference extension uses the same independently qualified
lit packet offsets and eight-byte SVECTOR table bounds. Blender flat/Gouraud
rewiring changes only the selected reference byte, preserves the complete
normal table and composes with the prior authored normal word. The explicit
content-v3 boundary retains legacy immutable-reference semantics. No reference
pin, runtime dependency or lighting/gameplay acceptance changes. Private proof:
`local-output/sdk-20260909/model-glb-normal-references-20261002/research/`.

The 2026-10-02 GLB normal work qualifies lit FT3/FT4/GT3/GT4 packet offsets
against the pinned descriptor and independent retail table readback. Normal
references are eight-byte SVECTOR offsets. Actual flat/Gouraud Blender edits
change only qualified normal XYZ words, preserving references and padding.
The pin is unchanged; no reference runtime dependency or lighting/gameplay
acceptance is introduced. Private qualification proof remains under
`local-output/sdk-20260909/model-glb-normals-20261002/research/`.

The 2026-10-02 appended-draft facing work reuses the existing verified facing
operand catalog and MAN record layout. Independent private Town0b/Dolk2 readback
confirms original-owner relocation, preserved upper flags and unchanged donor
facing. It introduces no new opcode interpretation, live heading claim or
reference dependency, and does not advance the pin. The read-only editor review
reports candidate provenance without gameplay or allocation acceptance.

The 2026-10-02 central flag assets adapt the existing independent script catalog
and source-preserving operand writer. Script/context/bank/retail-index identity,
source hashes/locators and per-PC operations are retained; no reference code,
new decoder coverage or runtime bank identity is introduced. Local/context,
global, system-selector and extra-mask evidence remains at the existing pin.
Fresh three-scene metadata and real operand history/persistence are verified;
story meanings, current values and execution are unresolved. See
[flag assets](legaia-flag-assets.md).

The 2026-10-02 initial animation picker reuses independently implemented MAN
assignment and scene ANM decoders. Fresh Town0b evidence qualifies actors0019
and0049 sharing scene TMD0102: ANM records13/12, six channels,15/30frames.
An observed clip choice changes only MAN animation byte9471,14→13; normal
package readback and appended-draft header rebasing pass. Exact TMD source,
active mapping, non-aliased pair and ANM record SHA checks remain mandatory.
Imported channel authoring is not retargeted. Runtime script behavior/timing is
unverified. No reference code or retail data is staged; the reference pin stays
unchanged. See [initial assignment workflow](legaia-initial-animation-assignment.md).

The 2026-10-01 raw MAN normal-Build integration reread that exact pin through
command-scoped `git show`: `crates/engine-core/src/scene_bundle.rs::streaming_man_payloads`
extracts chunk payloads after the four-byte header; `crates/asset/src/man_section.rs::actor_placement`
documents local-count/header offsets and the tile/bit7 coordinate encoding.
The SDK reuses its independent typed-source loader, placement/header/script
compositors and equal-span structural writer. Retail Dolk2 package members,
opaque bytes, layout, same-scene donor and raw ANM composition were checked.
This does not establish runtime initialization, script reachability or gameplay.
See [Raw MAN normal Build](legaia-raw-MAN-normal-build.md). No reference code copied.

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


The original P2[20] conflict diagnosis used the pinned camera0xC0 absolute-jump
interpretation and withdrew its graph. That interpretation is superseded by
independent retail handler validation on2026-10-02: the camera handler reads a
signed parameter, calls camera processing, and returns ordinary PC+4 or extended
PC+5. It does not replace the PC. The false edge and resulting overlap disappear.
Retail validation likewise establishes continuing FIELD43/44 operations and
relative flag-word target arithmetic. The pinned checkout is preserved unchanged;
SDK decoding follows the executing source evidence. Exact handler/consumer hashes,
qualified branch families and deferred runtime limits are documented in
[the branch evidence contract](legaia-script-branches.md). Earlier catalog counts
in this chronology describe those historical decoder versions.


### Transition entry serializer foundation (2026-09-10)

Pinned field/step.rs opcode3F reads entry_x,entry_z,dir as three unsigned bytes
after the clean scene name. The new record-level transition_authoring adapter
edits only these encoded fields, rejects unresolved/conflicting source paths,
requires a decoded SCENE_CHANGE and clean unchanged destination, and returns
per-byte source-hash audit records. It does not assign world coordinates, rename
destinations or relocate instructions. Two synthetic tests cover ordinary and
extended headers, exact unchanged spans/no-op and invalid inputs. A private
retail P2[0] probe changes exactly one byte and retains record length; evidence
is transition-entry-probe.json. An initial metadata-only report lookup correctly
had no raw_hex; the probe then used the verified private MAN context instead.
Project commands, persistence, Build composition and editor integration remain
pending; no playable transition edit is claimed.

## NPC_RUN move-selector authoring — September 30

Pinned Andrew reference `d6e64c68ede25813d35db20980da82a1a025549b`,
`crates/engine-vm/src/field/step/menu_ctrl/nibble_5_6_7.rs`, sub-1, reads the
selector at operand+4 and passes it to `op4c_n5_sub1_npc_run`; continuation
remains header+5 bytes. Retail town01 actor0011 at PC0x23 contains selector13.
The SDK edits this byte only, or composes it with the supported X/Z edits.
Depth, dispatch context and continuation are preserved. All256 byte values
round-trip through normal and extended headers in synthetic checks. Meanings
for selector values and actual runtime behavior remain unverified.

## EXEC_MOVE selector authoring — September 30

The same pinned Andrew revision, `crates/engine-vm/src/field/step.rs`, opcode
0x22, reads `[22, move_id]`, sets move-table state and calls `host.exec_move`;
continuation is pc+header_size+1. Retail town01 actor0003 PC0x12 contains byte9.
Ordinary and extended-target headers retain their context and width while only
the selector changes. No coordinates occur in this instruction. The selector
name denotes an encoded table operand, not a proven animation asset binding.
Its gameplay effects and selected table content remain unverified.


## Flag operand and wait target authoring — September 30

Evidence was checked directly with git show at pinned Andrew revision
`d6e64c68ede25813d35db20980da82a1a025549b`, independently of the checkout's
advanced HEAD `574ee5f603ed3ca9bd95c796711e595d9c2ad8a8`. No pin or reference
checkout was changed.

`crates/engine-vm/src/field/step.rs` opcodes0x2B..0x33 mask ordinary flag operands
to five low bits; upper bits do not form the selected bit index. `field/ctx.rs`
defines the local bank as u16 at+0x62. CFLAG_SET8 additionally copies context
+0x26 to+0x5A. The extended-dispatch halt check permits CFLAG_CLEAR10 as a special
unhalt operation, while the system script0xFB bypasses that check independently.
SDK authoring excludes local bits16..31 and context SET8/CLEAR10 (including
ordinary CLEAR10 conservatively), preserving opcode, upper operand bits,
extended target, source layout and branch bytes. System selectors and flag
branch operands remain unavailable. Identical indices across owners/contexts
are not evidence of one runtime variable. Reference discovery retains retail
groups and separately validated authored/effective operands without live values.

The pinned opcode0x4A handler reads a u16 little-endian WAIT_FRAMES target,
accumulates host.frame_delta into a signed16 saturating wait_accum and either
halts at the same PC or clears the accumulator and advances by header+2.
The SDK exposes host ticks, unknown seconds and unevaluated execution; authored
targets0..32767 respect the reference accumulator's positive range. Larger retail
targets remain explicitly unsupported rather than normalized. No guarantee of
actual game duration or scheduling is inferred from this reference handler.

Private retail evidence includes town01 actor0002 CFLAG_SET PC0x0C bit2-to3
at MAN4772, and actor0044 WAIT_FRAMES PC0x019F16-to17 at MAN24483. Combined ZIP
readback changed only these two offsets; compressed actor append rebased the
wait to24486. Source record/MAN hashes, package hashes and diagnostic projects
are retained under ignored local-output/sdk-20260909. These prove serialization
and editor persistence, not story semantics, runtime behavior or gameplay
acceptance. Browser forms keep retail/authored/effective operands separate and
use ordinary project commands; no guest RAM mutation is involved.


### Equal-span field menu labels (2026-09-30)

Pinned `d6e64c68ede25813d35db20980da82a1a025549b`:
`crates/mes/src/picker.rs` establishes masked0x27/28/29 openings, signed
entry-relative jump tables, immediate/continuation label starts and MES spans.
The SDK label writer uses those decoded spans and existing MAN ownership and
plain-glyph validation. It preserves branch/control bytes and compares graph,
token and record boundaries after editing. Static labels do not establish
pager continuation execution, runtime choices, font layout or story reachability.
See [menu-label authoring](legaia-menu-label-authoring.md) for current evidence.


### Renderer newline authoring boundary (2026-09-30)

At pin`d6e64c68ede25813d35db20980da82a1a025549b`,
`crates/font/src/lib.rs` defines `NEWLINE=0x7C`; Font::layout resets X and
advances Y by LINE_HEIGHT for that byte, and wrapping retains existing newlines.
`docs/formats/dialog-font.md` attributes the newline to the retail renderer
(FUN_80036888/FUN_80036044). MES decoding independently surfaces it as Glyph.
The SDK preserves MES classification while excluding it from editable plain-glyph
spans and new authored strings. This distinguishes source bytecode decoding from
renderer controls; it does not simulate layout or prove current gameplay.
Legacy project loading may retain an old pipe edit for review/clear, but the
serializer always uses strict validation.58 focused tests and separate retail
browser rejection/legacy review passed; the397-test checkpoint predates the fix.

## Retail glyph preview - 2026-09-30

The independent font importer uses the unchanged pin, `crates/font/src/lib.rs`
and `docs/formats/dialog-font.md`, checked through `git show`. Retail page,
CLUT, width table, hashes and limits are recorded in the
[glyph preview guide](legaia-text-glyph-preview.md). Stencil normalization and
advances are reference evidence plus retail extraction; layout and runtime tint
are not live evidence. Browser canvas readback and visual inspection passed.
No reference implementation or retail pixels are bundled.

## Script model-selector authoring - 2026-09-30

The unchanged pin's `field/step/menu_ctrl/nibble_5_6_7.rs::op_4c_n5`
and `field/host.rs::op4c_n5_sub0_set_actor_model` establish signed16 layout,
signed >=0xF0 high-pool dispatch and primitive state writes. Independent source
patching preserves every other byte and extended context. Pool-to-asset resolution
and mesh restaging are not asserted. Source/retail/browser/output evidence and
limits are recorded in [the guide](legaia-script-model-selectors.md).

## Source-bound GLB baked RGB (2026-10-02)

Pinned Andrew reference `d6e64c68ede25813d35db20980da82a1a025549b`
`crates/tmd/src/descriptor.rs` and `crates/tmd/src/legaia_prims.rs` qualify flat
shared and Gouraud per-corner RGB words, command/padding exclusion and no-RGB
textured lit rows. Independent retail byte masks and Blender 5.2.2 round trips
change only flat byte300 or Gouraud byte460. The authored material baseline is
retained. Profile v2 raw attributes are SDK interchange metadata, not retail
format facts or runtime lighting evidence. See [workflow](legaia-model-glb-rgb.md)
and private `local-output/sdk-20260909/model-glb-rgb-20261002/research/qualification-proof.json`.

## Source-bound GLB existing face references (2026-10-02)

Pinned Andrew `d6e64c68ede25813d35db20980da82a1a025549b` descriptor and primitive
walker qualify little-endian u16 SVECTOR byte offsets: vertex ID times eight.
Immutable primitive/corner IDs and object-specific source counts own v3 GLB
reference writes. Independent retail walking and Blender 5.2.2 update both
aliases of a quad corner and change only byte434 (136 to0); vertex coordinates
and the authored RGB/material baseline remain exact. No new vector/packet
allocation or runtime acceptance is inferred. See [workflow](legaia-model-glb-faces.md)
and private `local-output/sdk-20260909/model-glb-faces-20261002/research/qualification-proof.json`.
