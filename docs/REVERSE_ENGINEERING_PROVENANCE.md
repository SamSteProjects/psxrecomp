# Legaia reverse-engineering provenance

The reference repository is `AndrewAltimit/legend-of-legaia-re`, pinned to
`d6e64c68ede25813d35db20980da82a1a025549b`. It is an optional development reference
and parity oracle, not a runtime dependency, submodule or bundled implementation.
The 2026-09-09 importer work read the exact commit through `git show` in the
existing read-only reference checkout. The pin was not advanced.

Our previous independently implemented SDK source was recovered from
`legaia-sdk-integration`, commit `28ce54367127e858c8ef2bfbd27ffe64f60e0e93`.
Current implementation remains in this Recomp checkout. SDK-Clone,
LegaiaRecomp and Andrew's checkout are references only.

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
| Preview display axes | `crates/web-viewer/src/scene_gltf.rs` | PSX mesh-local positive Y is down; display-only Y negation preserves raw model vertices |
| MAN runtime candidates | `docs/subsystems/script-vm.md`, `scripts/pcsx-redux/walk_actor_lists.py`, `crates/web-viewer/src/field_npc.rs` | Guarded actor+0x90 header and independent model-count evidence; no list-order or address identity |

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
