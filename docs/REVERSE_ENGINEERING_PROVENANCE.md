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
