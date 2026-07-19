# Legaia SDK integration audit

Status: Phase 0 architecture audit only. No runtime or editor integration is implemented.

Audit snapshots:

- PSXRecomp: `SamSteProjects/psxrecomp`, `origin/master` at `3ebddf408b28bdbea425ac86be584f52a708ce29` (2026-07-18).
- semantic reference: `AndrewAltimit/legend-of-legaia-re` at `d6e64c68ede25813d35db20980da82a1a025549b` (2026-07-18), inspected from a temporary read-only checkout outside this repository.
- work branch: `legaia-sdk-integration`.

This is an implementation audit, not a README comparison. Paths below are repository-relative to the repository named in each section. Maturity labels mean: **production** (normal supported path), **validated** (tests or runtime parity evidence), **partial** (useful but explicitly incomplete), and **research** (evidence-gathering, not a stable API).

In the matrix, “reuse” means reuse the documented knowledge, algorithms, evidence and—where license-compatible and appropriately attributed—selectively adapted implementation. It does **not** mean linking, shipping or requiring the legend-of-legaia-re repository or clean-room runtime.

## Capability matrix

| Capability | Existing implementation | Maturity | Integration decision | Missing or uncertain |
|---|---|---:|---|---|
| Disc reading | Legaia RE `crates/iso/src/raw.rs` (`RawDisc`, `resolve_disc_path`); PSXRecomp `runtime/src/iso_reader.cpp` and CD-ROM runtime | production | Reuse Rust reader for import; keep PSXRecomp CD path authoritative at runtime | One shared disc-identity manifest |
| ISO9660 access | Legaia RE `crates/iso/src/iso9660.rs` (`read_volume`, `list_directory`, `find_file_in_image`, `read_file_in_image`, `walk_files`) | validated | Direct Rust library or narrow helper CLI | Region/disc normalization policy |
| PROT entry lookup | `crates/prot/src/archive.rs` (`Archive`, `Entry`); `crates/engine-core/src/scene/prot_index.rs` (`ProtIndex`) | validated | Wrap as semantic import service | Stable exported DTO with raw spans |
| CDNAME scene naming | `crates/prot/src/cdname.rs`; `ProtIndex::scene_block`, `scene_names` | validated | Reuse directly | Alias policy across regions |
| Scene resolution | `crates/engine-core/src/scene/scene_ty.rs` (`Scene::load`), `scene/resolvers.rs`, `scene/host.rs` | validated/partial | Wrap, do not recreate | Some context-dependent/variant MAN selection remains evidence-sensitive |
| Field-pack parsing | `crates/asset/src/field_pack.rs`; `engine-core/src/scene_bundle.rs` (`find_bundle`, `walk_descriptors`, `extract_man_payload`, `extract_move_payload`) | validated/partial | Reuse parser and retain raw spans | Formal stable schema for every slot |
| TMD parsing | `crates/tmd/src/lib.rs`, `legaia_prims.rs`, `mesh.rs`, `vram_targeted.rs` | validated | Direct library for initial importer | Preserve primitive/object source spans in editor DTO |
| TIM and VRAM | `crates/tim/src/lib.rs`, `vram.rs`; `SceneResources::build_targeted_with_options` | validated | Reuse semantic preview; compare with PSXRecomp `vram_peek` | Cross-runtime VRAM placement correlation |
| MES/dialogue | `crates/mes/src/lib.rs`, `interp.rs`, `dialog_box.rs`, `picker.rs`; translation pipeline in `crates/rando/src/translate*` | validated/partial | Reuse decoding; wrap editing/serialization later | NPC-to-MES chain is scene/script contextual and must not be guessed |
| ANM animation | `crates/anm/src/lib.rs`, `player.rs`; `engine-vm/src/anim_vm/` | validated/partial | Reuse parser/player | Stable actor placement → clip proof per scene |
| Actor state | `crates/engine-vm/src/move_vm/state.rs::ActorState`; `engine-core/src/world/types.rs::Actor` | validated clean-room model | Adapt to imported/derived DTO, never treat as retail RAM layout | Retail actor-layout versioning and slot correlation |
| Actor enumeration | `crates/asset/src/man_section.rs::ActorPlacement`; `engine-core/src/man_field_scripts/placements.rs::classify_placements`; `web-viewer/src/field_npc.rs::build_npc_catalog*` | validated | Immediate reuse for read-only slice | Catalog identity currently uses record/catalog indices, not SDK semantic IDs |
| Field VM | `crates/engine-vm/src/field/` (`FieldCtx`, `FieldHost`, `step`); `crates/asset/src/field_disasm/` | validated/partial | Reuse decoder and semantics independently | Static walks can desync through embedded text/data; carry confidence |
| Move VM | `crates/engine-vm/src/move_vm/` (`MoveHost`, `step`, `actor_tick`) | validated/partial | Reuse for interpretation/preview | Retail script-to-live-actor binding evidence |
| Effect VM | `crates/engine-vm/src/effect_vm/` (`EffectHost`, `Pool`, catalog) | partial | Remain independent until later slice | Editor object model and live correlation |
| Story flags | `man_field_scripts/partitions.rs` (`GFlagSite`, `system_flag_census`, `flag_test_bytescan`, `motion_flag_census`); field VM flag ops | validated with explicit caveats | Wrap results as claims with evidence/confidence | Exact NPC interaction association requires record-level control-flow evidence |
| Dialogue conditions | Field disassembler plus `classify_placement`, `placement_inline_prologue`, flag censuses | partial | Adapt only proven record-local chains | No universal actor → condition → MES resolver |
| Collision | `crates/asset/src/field_objects.rs` (grid, placements, `WalkHeightfield`, collider centers); `engine-core/src/field_regions.rs`; world collision | validated/partial | Reuse for preview | Actor dynamic collision and retail RAM correlation |
| Camera data | `engine-core/src/field_regions.rs` (18-byte camera-region payloads), `world/types.rs::CameraState`; field VM camera handlers | partial | Reuse parsers and label uncertainty | Authoring-friendly camera schema and complete semantics |
| Rendering | Legaia RE `engine-render`, `asset-viewer`, `web-viewer`; PSXRecomp software/OpenGL/Vulkan GPU paths | production/validated | Use Legaia renderer for semantic preview, PSXRecomp for retail validation | Editor viewport packaging; do not replace either renderer |
| Runtime memory access | PSXRecomp `runtime/src/debug_server.c`: `read_ram`, `write_ram`, snapshots, watches | production diagnostics | Existing TCP protocol | Typed/batched reads and actor-layout descriptors |
| Runtime stepping | `pause`, `continue`, `step`, `run_to_frame`, history commands | production diagnostics | Existing TCP protocol | Startup/session capability handshake |
| Controller injection | `set_input`, `press`, `clear_input`, `pad_status` | production diagnostics | Existing TCP protocol | SDK-friendly symbolic button mapper |
| Overlay identification | `overlay_dump`, `overlay_loader_status`, `overlay_candidates`, capture/native rings | validated diagnostics | Wrap generic data | No single stable `current_overlay` response/capability contract |
| Overlay capture | `runtime/src/overlay_capture.c`, `overlay_loader.c`; `tools/compile_overlays.py`; `overlay_capture_dump` | validated | Keep independent; use only hashes/ranges/metadata in SDK | Safe metadata-only export distinct from proprietary capture bytes |
| Symbol maps/function naming | PSXRecomp generated `func_XXXXXXXX` and audit config; Legaia RE `ghidra/scripts/symbols.json`, `known_symbols.py`, `docs/reference/functions.md` | partial/research | Generate licensed metadata maps with provenance | Cross-revision/overlay symbol namespace and collisions |
| Disc patching | Legaia RE `crates/iso/src/write.rs`, `relayout.rs`; `crates/rando/src/disc.rs`, `ppf.rs` | validated for supported edits | Use as attributed reference for a later PSXRecomp-side export backend | General scene/NPC edits, archive/resource limits |
| Native asset overrides | Clean-room engine supports override-oriented scene/config paths; PSXRecomp has no semantic asset override layer | partial/absent | Design later in Legaia integration | Override manifest and safe runtime hooks |
| Live reload | Neither repository provides authored semantic live reload end-to-end | absent | New integration capability | Transaction protocol, invalidation, rollback |
| Project serialization | Legaia RE has configs/saves, not SDK authored projects; PSXRecomp has `game.toml`, not editor state | absent | New integration-owned schema | Versioning, migrations, undo journal |
| Testing/parity oracles | PSXRecomp TCP native/Beetle comparison, co-sim, frame/write traces; Legaia RE unit, fuzz, disc-gated and runtime-capture parity tests | strong | Reuse both independently | Cross-repository semantic/live contract suite |

## Concrete PSXRecomp file and API map

### Build and game-project boundaries

- `recompiler/CMakeLists.txt`: targets `psxrecomp-game`, `PSXRecomp`, `psxrecomp-toml`, `psxrecomp-bios`, decoder/codegen tests.
- `recompiler/src/config_loader.cpp` and `recompiler/include/config.h`: parses BIOS/game TOML and emits configuration; this is runtime/recompiler configuration, not an SDK project model.
- `runtime/runtime.cmake`: reusable `psxrecomp_add_runtime_target()` helper; links generic hardware/runtime sources and generated BIOS/game C supplied by a game target.
- `runtime/CMakeLists.txt`: `psx-runtime` (4370), optional oracle target, and `psx-beetle` (4380).
- `docs/config_schema.md`: `[game]`, `[recompiler]`, `[runtime]`, `[audit]` contract.
- `docs/ARCHITECTURE.md` and `docs/EXECUTION_MODEL.md`: static → native overlay → dirty-RAM interpreter dispatch model.
- `generated/`: ignored derivative build output. Never an SDK source tree and never hand-edited.

### Execution, overlays, and hardware

- `runtime/src/main.cpp`: runtime process, `--game` config path, frame loop.
- `runtime/src/memory.c`: PS1 address translation and `psx_read_*` / `psx_write_*` accessors.
- `runtime/src/cpu.c`, `cpu_state.h`, `dispatch.c`: CPU state and dispatch.
- `runtime/src/overlay_capture.c`: records discovered RAM code ranges/content for recompilation.
- `runtime/src/overlay_loader.c`: content-addressed native overlay lookup/load/dispatch.
- `runtime/src/overlay_backend.c` and `overlay_compile_worker.c`: compiler backend and asynchronous compile orchestration.
- `runtime/src/dirty_ram_interp.c`: correctness fallback for runtime-installed code.
- `tools/compile_overlays.py`: capture-to-C/shared-library pipeline; `--static` emits `generated/overlays_static.c`.
- `runtime/src/gpu.c`, `dma.c`, `cdrom.c`, `interrupts.c`, `sio.c`, `spu.c`: generic PS1 hardware models. They are audit inputs only and out of scope for SDK refactoring.

### Debug protocol and clients

- `runtime/src/debug_server.c`, `runtime/include/debug_server.h`: native JSON-over-newline server, localhost port 4370, command dispatch at emulation-thread safe points.
- `runtime/src/beetle_debug_server.c`: overlapping protocol against Beetle on port 4380.
- `tools/duckstation/psxrecomp_oracle.patch`: DuckStation implementation used by the oracle workflow.
- `tools/debug_client.py`: CLI and generic key/value command client.
- `TCP_COMMANDS.md`: canonical public inventory and response-bounding rules.

Existing commands needed by the first slice include `ping`, `get_registers`, `read_ram`, `write_ram`, `vram_peek`, `gpu_state`, `irq_state`, `dma_state`, `watch`, `unwatch`, normalized `wtrace_*`, `set_input`, `clear_input`, `pause`, `continue`, `step`, `run_to_frame`, `history`, `get_frame`, `frame_range`, `set_snapshot`, `get_snapshots`, `overlay_dump`, `overlay_loader_status`, `overlay_candidates`, `overlay_capture_dump`, `dispatch_*`, and `fntrace_*`.

### Validation extension points

- `runtime/tests/`: hardware, overlay and runtime regression tests.
- `recompiler/tests/`: decode, reachability and codegen regression tests.
- `tools/cosim.py`, `docs/internal/COSIM_ORACLE.md`: compiled/interpreted or oracle state comparison.
- Frame fingerprints, ordered write recording, wtrace/rtrace and bounded rings are implemented in `debug_server.c`; they are stronger correlation evidence than ad-hoc logging.

## Concrete legend-of-legaia-re file and API map

### Disc and archive crates

- `legaia-iso`: `RawDisc`, ISO9660 `Volume`/`DirectoryRecord`, sector-aware patching and PROT relayout.
- `legaia-prot`: `Archive`, `Entry`, `cdname::IndexMap`, block/range helpers.
- `legaia-lzs`: decode and repack.
- `legaia-extract`: `legaia-extract` pipeline and disc-gated validation suite.

### Format crates

- `legaia-tim`: `Tim`, `Image`, `Clut`, `parse`, `decode_rgba8`, `Vram`.
- `legaia-tmd`: `Tmd`, `Object`, `PrimHeader`, `parse`; Legaia primitive walker and `mesh` builders.
- `legaia-mes`: `MesBlob`, `RecordBoundary`, `Token`, `Interpreter`, `extract_message`, `extract_all_messages`, `DialogPlayer`.
- `legaia-anm`: `AnmPack`, `RecordRange`, `RecordHeader`, `parse`, `AnimPlayer`.
- `legaia-asset`: `field_pack`, `man_section`, `field_objects`, `field_disasm`, streaming/bundle detectors and classifiers.

### Semantic engine and scene surfaces

- `crates/engine-core/src/scene/prot_index.rs`: `ProtIndex::open`, `from_bytes`, entry byte/LBA/size access and CDNAME block lookup.
- `crates/engine-core/src/scene/scene_ty.rs`: `Scene`, `SceneEntry`, `EventScripts`, `Scene::load`, field MAP/MAN/terrain/collision accessors.
- `crates/engine-core/src/scene/host.rs`: `SceneHost`, `SceneTickEvent`, `BgmDirector`; lifecycle and field entry are split under `scene/host/`.
- `crates/engine-core/src/scene_resources.rs`: `SceneResources`, `ResolvedTmd`, `ResolvedAnm`, `BuildOptions`, `SceneLoadKind`.
- `crates/engine-core/src/man_field_scripts/placements.rs`: `PlacementKind`, `classify_placements`, `classify_placement`, `placement_inline_prologue`.
- `crates/engine-core/src/man_field_scripts/records.rs`: `ManScriptRecord`, `walk_partition1_scripts`.
- `crates/engine-core/src/man_field_scripts/partitions.rs`: flag sites/censuses with explicit clean/text-alias uncertainty.
- `crates/engine-core/src/man_field_scripts/npc_motion.rs`: placement movement route, facing and walk/touch binding analysis.
- `crates/engine-core/src/man_field_scripts/scene_triggers.rs`: destinations, conditional flag-gated destinations, FMV/BGM/stager evidence.
- `crates/engine-core/src/field_regions.rs`: MAP region table, tile triggers, intra-scene teleports and camera-region records.
- `crates/engine-core/src/world/types.rs`: clean-room `Actor`, collision and camera state; not a claim about retail RAM layout.
- `crates/engine-vm/src/field/`: `FieldCtx`, `FieldHost`, `step`.
- `crates/engine-vm/src/move_vm/`: `ActorState`, `MoveOpcode`, `MoveHost`, `step`, `actor_tick`.
- `crates/engine-vm/src/effect_vm/`: `EffectHost`, `Pool`, effect catalog.
- `crates/web-viewer/src/field_scene.rs`: `build_field_scene` assembles geometry, placements, terrain and walk ground.
- `crates/web-viewer/src/field_npc.rs`: `build_npc_catalog*` resolves MAN placements to model/ANM/kind/inline dialogue, while explicitly flagging conditional/special/unposable cases.

### Tools and build targets

- Workspace binaries include `legaia-extract`, `legaia-engine` (package `legaia-engine-shell`), `asset-viewer`, `legaia-rando`, and format-specific CLIs.
- Useful existing commands: `legaia-engine list-scenes --disc`, `info --disc --scene`, `play`, `play-window`; `asset-viewer field`; `legaia-rando translate`; `tmd dump-obj`.
- `crates/rando/src/disc.rs` (`DiscPatcher`), `crates/iso/src/write.rs`, and `crates/rando/src/ppf.rs` provide supported patch/PPF foundations. They are not a general arbitrary-scene serializer.
- `ghidra/scripts/symbols.json`, `known_symbols.py`, `docs/reference/functions.md`, `docs/reference/memory-map.md`, and per-format/subsystem docs form the research/name layer. Generated per-function dumps remain excluded.

## Findings and uncertainties

1. The first import slice is substantially solved semantically: disc → PROT/CDNAME → scene → assembled geometry → MAN placements → model/ANM is existing code.
2. `build_npc_catalog` derives a useful interaction classification and inline dialogue label, but it is not a universal proof of a retail NPC-to-MES relationship. MES references, embedded inline dialogue, and scene variants must remain separate claims.
3. Static field-script analysis explicitly encounters decode desynchronization and text aliases. The SDK must carry `clean`, alias suspicion, evidence source, and competing claims rather than flattening them.
4. PSXRecomp supplies generic memory, stepping, VRAM, trace and overlay diagnostics. It does not currently expose a canonical current scene or typed retail actor table.
5. Runtime RAM addresses and actor slots are recyclable. A semantic actor cannot be identified by address or slot alone; correlation must include scene/overlay epoch and observations.
6. PSXRecomp uses PolyForm Noncommercial 1.0.0. Legend-of-legaia-re declares `MIT OR Unlicense`. Code reuse must be reviewed deliberately; process/JSON boundaries reduce license and clean-room coupling but do not grant commercial redistribution rights.
7. PSXRecomp's root ignore rules cover BIOS, `generated/`, broad per-game content and common dumps, but do not yet define the future SDK's extracted/cache paths. Before any extractor is wired in, add explicit ignores for the chosen `integrations/legaia` user-data/cache directories and test them with `git check-ignore`.

## Audit conclusion

Build the importer, SDK model, editor services and live correlation inside PSXRecomp's isolated `integrations/legaia/` layer, around the running recompiled engine. Use the pinned legend-of-legaia-re revision as a development reference and parity oracle for parsers, viewers, semantics and evidence; selectively adapt only what the SDK needs with attribution. Do not add a submodule, Cargo dependency, required subprocess or second shipped runtime. Use PSXRecomp's TCP protocol as the live boundary.
