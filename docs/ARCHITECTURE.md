# Architecture

How PSXRecomp is put together, end to end. For the higher-level "why three ways
of running code" story, read [`EXECUTION_MODEL.md`](EXECUTION_MODEL.md) first;
this doc is the component-level view.

## Legaia SDK and authoring editor

Model GLB profile v6 resolves explicit material tuples through source corner
identities, not external shader assignments. `model_glb_materials.py` reuses the
qualified semantic writer and masked field locations; primitive CLUT/TPage and
whole-group ABE aliases must agree. Material spans compose with existing vector
and reference edits. The SDK regenerates bindings, rebuilds candidate material
associations and reviews exact source fields before the normal replacement
command. Legacy profiles retain material words. See
[material interchange](legaia-model-glb-materials.md).

`importer/worldmap_placements.py` qualifies sparse MAP gates, direct slot-1
model dictionary references and raw source seed transforms. The geometry v2
loader retains the ground preview and adds shared model assets and immutable
source entities. `editor/worldmap-scene.js` validates source ownership, finite
geometry, texture and graph budgets, then transposes source matrices and flips
Y once for the shared renderer. Hierarchy/picking are local inspection state;
no authored field selection or overrides change. Script-driven visibility and
resting transforms stay unknown. See [placements](legaia-worldmap-placements.md).

`importer/worldmap_geometry.py` resolves canonical walk kingdom MAP/MAN/TIM
carriers and derives the full source floor-nibble surface with existing terrain
math. `sdk/worldmap_geometry.py` qualifies the current project source key, returns
bounded geometry/texture data and never authors state. The World ground workspace
uses `SceneRenderer` with a display-only Y flip and no placement overrides.
Selection changes clear retained kingdoms; source/mode changes withdraw results.
Menu coordinates, runtime actors and unplaced mesh pools are not interpreted as
world transforms. See [world ground](legaia-worldmap-geometry.md).

Model GLB profile v5 resolves existing normal reference IDs through immutable
packet corners. `model_normal_references.py` qualifies aligned SVECTOR offsets
and object table bounds. The replacement writer admits these words only with
explicit normal-reference opt-in, persisted as `tmd-content-v3`; legacy v1/v2
bindings retain their immutable-reference contract. Shared references and raw
normal XYZ aliases remain consistent, and Build requalifies payloads against
retail source before fixed-capacity overlays. See
[normal references](legaia-model-glb-normal-references.md).

Model GLB profile v4 adds source-bound stored normal XYZ to the existing model
replacement service. Custom attribute rows resolve immutable source corner
owners and existing eight-byte normal-vector references; shared aliases must
agree after signed-i16 quantization. Only normal XYZ words are written, retaining
vector padding and references. Fresh export/review keys govern Apply and Build;
legacy codecs keep their narrower fields. The viewport does not establish
retail normal-based lighting parity. See [normal workflow](legaia-model-glb-normals.md).

`sdk/draft_review.py` qualifies a current authored-state key, prepares existing
NPC draft serializers in memory and returns metadata only. Both compressed and
streaming serializers compose `FacingAuthoringContext.patch_appended` before
branch edits, retaining original record identity after table relocation. The
editor review aborts pending reads and withdraws results when source inputs or
mode change. This service has no disc writer and does not change normal Build
acceptance. See [draft facing](legaia-draft-facing.md).

Coordinated scene animation (2026-10-02) adds a transient viewport service over
the existing verified scene graph. `sdk/scene_animation.py` groups exact existing
geometry bindings into bounded source-qualified tracks; the server composes
effective source assignments, shared channel contributions and model materials
through existing decoders. The UI receives sampled actor-local vertices and
stable animation IDs, never guest pointers or raw animation bank bytes.
`editor/scene-animation.js` owns preparation, shared preview ticks, source guards
and playback controls. The parent editor owns renderer state and an exclusive
inspection token, loads a detached scene copy, updates shared mesh vertices and
restores the canonical scene. Persistent commands are gated throughout transient
inspection. Preview sampling produces no authored or generated project state;
it does not model runtime script scheduling or assert retail timing.

Field branch authoring (2026-10-02) adds `BranchAuthoringContext` over the
existing verified unique P1/P2 MAN owner snapshot. Retail executing-handler
arithmetic overrides three incorrect pinned decoder interpretations without
changing the oracle checkout. Every source instruction/message boundary is
retained; only qualified target-word spans change. Existing operand serializers
qualify against retail first, then branch words compose last and the candidate
flow is independently rescanned. MAN layout, source preimages, untouched bytes,
recompression capacity and serialization readback remain mandatory.

The project service binds Review/Apply to all authored inputs, fresh source
hashes and disc stamp, independently from geometry preview freshness. The
`ScriptBranches` component participates in ordinary history, Save/Open, normal
and experimental exports, component review and operand transfer. A detached
frontend module displays bounded source/current/proposed neighborhoods, decoded
conditions and unresolved regions, links disassembly selection in both directions,
and retains per-branch drafts across ordinary refresh. Story reachability and
termination are not inferred. See [the branch contract](legaia-script-branches.md).

Model content authoring (2026-10-02) adds a source-qualified packet inspector
and exact byte-mask writer to the existing model replacement path. A separate
`tmd-content-v1` binding allows XYZ plus existing face references, UV pairs and
baked RGB; legacy `tmd-shape` validation remains XYZ-only. Disjoint table/vector/
primitive ownership, explicit terminators, declared counts, bounded fields and
whole-candidate decoding precede an exact audit of every changed byte. Stable
object/group/primitive identities and current/source/candidate hashes bind UI
review to atomic Apply. The normal model command owns history and persistence;
container composition/recompression and independent readback enter normal Build.
Candidate preview now updates topology/color/UV arrays through existing pose
prefixes/frames and rebuilds source-address texture crops. The browser uses paired
Current/Proposed cameras and retained scene proposals with close/context guards.
[The model content contract](legaia-model-content.md) records pinned packet evidence
and preserves the unfinished allocator/material/lighting scope.

The transition graph workspace (2026-10-02) consumes the existing source-qualified
scene/project graph APIs. A detached browser decoder validates stable scene,
owner, partition and instruction identities, source hashes/extents, separate
entry layers, imported-scene context and exact coverage totals. Scene responses
bind both source and transition annotation keys; project responses bind the
complete project transition key. A pure filtered projection groups parallel
instructions only for diagram arrows and limits the canvas to 80 nodes/160 pairs;
its separate instruction list keeps all matches for bounded pagination. The
workspace uses a deterministic column layout, source/destination selection,
direct-neighbor focus, pan/zoom and ordinary source-script/scene navigation.
Long arrows pass between scene boxes; badges render above crossing lines. Dynamic
frame handlers leave with removed nodes, and context/close guards disable retained
callbacks. Project-only authored/import changes close stale dialogs; a late failure from a
previous request cannot clear a newly opened workspace. Nothing in
this visualization evaluates runtime routes or changes authored/imported data.

Source trigger cells (2026-10-02) use a scene-owned `TriggerCells` override,
qualified by original MAP SHA256 and stable primary kind/row IDs. The importer
writer changes only the first two bytes of existing kind-0/1 rows. The review
service rechecks complete bindings and project/source freshness before atomic
Apply; inherited cells normalize to absence. The shared Inspector opens cell
controls, while a separate trigger annotation key updates the source-cell
workspace without changing imported spatial records or model geometry. Normal
Build independently reconstructs the requested trigger byte audit and composes
it with disjoint region, scenery and collision writes. Unknown payloads stay
unchanged; reference Y, activation, runtime footprints and contact remain outside
this authoring contract. See [trigger cells](legaia-trigger-cells.md).

Source-facing operands (2026-10-02) use a separate `ScriptFacing` component keyed
by immutable source owner and PC. Fresh MAN qualification and retail-proved
operand masks permit sectors0–7 while preserving every upper bit and other byte.
They do not introduce `Transform.heading` or choose a story branch. The editor
renders imported/authored/effective source values and an operand compass; normal
Build independently validates their full byte audit when composing MAN families.
Operand JSON and bundles reuse that same service. Experimental NPC append export
rejects this component. Gate-0 MAP references retain a flat MAN index with no
asserted partition; gate-1 explicitly retains its P2-local index space. Additional
registered actor components render properties/details/actions from the Inspector
schema, with direct generic property editing disabled. See
[source-facing contracts and retail evidence](legaia-script-facing.md).


Source region authoring reuses the bounded field MAP table parser. The
serializer writes only four corner bytes per existing primary row and supplies
complete byte audits. `sdk.region_bounds` requalifies the entire retained
binding and current review before single-history project commands. Effective
annotations travel beside immutable `legaia.field-spatial.v1` metadata; the
region annotation key is separate from the geometry source key. Normal Build
merges original-source region, scenery and wall writes with overlap rejection
into one guarded MAP carrier. No activation simulation or runtime dependency is
introduced. See [region bounds](legaia-region-bounds.md).

Field source footprints adapt freshly verified MAP metadata without another
format decoder. `sdk.field_spatial.build_field_spatial` preserves primary and
fallback source ordering, row identities, containing-table bounds and hashes.
Triggers invert raw 128-unit dispatcher tiles; regions invert 128-unit tiles with
a 64-unit bias. Source geometry lives only in transient preview responses.
The hierarchy, shared Inspector and viewport selection use existing resource
IDs, while actor/scenery selections and authored transforms remain separate.
The graph qualifies gate-1 rows against unique source P2 records and records
both row hashes; runtime dispatch, height and reachability stay unevaluated.
See [field source workspace](legaia-field-source-workspace.md).

Central transition resources adapt the existing decoded transition graph.
Instruction identities stay separate from authoring operand IDs; imported,
authored and effective entry layers retain original script ownership and record
hashes. Refresh and graph callers reverify requested edits through the existing
MAN transition serializer. Catalog partial status reports unvisited bytes;
actual decoder stops independently determine whether source edits can qualify.
A scene transition-state key tracks annotations separately from geometry.
The shared Inspector navigates to exact source PCs and already imported targets;
static destination arrival coordinates do not create source trigger transforms,
runtime bindings or route assertions. See [transition assets](legaia-transition-assets.md).

The SDK asset-reference service verifies imported project sources and adapts
explicit membership, assignment and active derived-catalog relationships into
bounded one-hop views. The editor consumes that contract for dependency and
referenced-by navigation; it does not infer runtime use from source ownership.
Imported, effective, authored and decoded evidence remains distinct. See
[Asset reference navigation](legaia-asset-references.md).

The title-specific product lives under `integrations/legaia`; it does not put
retail addresses or asset layouts into the generic runtime. Its local editor
is served by `tools/legaia_editor.py` within that directory.

```text
User-owned disc -> ImportService -> imported metadata -> AssetDatabase
                                                   -> Scene / components
ProjectService -> authored overrides -> Undo commands -> effective editor view
                                                   -> project.legaia.json
Generic runtime protocol -> guarded ObserverService -> separate Live view
```

`sdk/project.py` owns project persistence, the asset catalog, scene projection,
selection and undo commands. `sdk/server.py` serializes mutations and exposes
the loopback editor API. `editor/` is the user interface. `importer/` owns
verified disc/container/record decoding. `observer/` and `layouts/` own the
read-only runtime adapter and title-specific evidence profiles.

`sdk/run.py` owns one private Windows child process. It validates the selected
runtime, configured retail executable, BIOS and generated mod package, creates
project-local run resources, and checks listener PID plus runtime/mod identity
before exposing Attach. Stop addresses only that retained process. Readiness
proves identity and activation; field gameplay is a separate acceptance step.

`importer/textures.py` decodes structural TIM packs and resolves TMD UV crops
against uploaded pixel/CLUT address candidates. Only unique static address
matches produce textures; missing or ambiguous associations remain explicit.
Raw object coordinates are preserved; the preview converts PSX Y-down for
upright display using pinned reference evidence.

`importer/animation.py` adds provenance-scoped F0/F1/F2 field-party idle/walk
clips from PROT0874 section1. Ten rigid object channels form a posed preview;
equipment descriptor templates are excluded. Clip IDs, frame counts, source
spans and reference-derived timing remain separate from live animation state.
The editor can select clips, step frames and play/pause. Shared party texture
uploads from section2 use a model-scoped catalog rather than being merged into
every scene texture bank. Neither path invents a skeletal parent hierarchy or
claims exact GTE arithmetic, live equipment state or general NPC animation.

`importer/scene_animation.py` verifies MAN header associations against the
scene's type-5 ANM bank and assembles matching rigid object channels. It keeps
zero IDs, global banks and mismatched channel counts explicit. Its request
catalog supplies either one baked pose or a bounded full clip; NPC cadence
and runtime script clip changes remain unknown.

The actor-animation HTTP adapter resolves the active imported actor itself;
clients cannot provide a different asset or animation binding. Its verified
full clip feeds the shared frame-step/playback viewer. An actor-specific
export route redecodes the binding and bakes the requested frame through the
same GLB exporter, preserving actor and ANM provenance. Unknown NPC cadence is
labelled as a manual preview rate. Asset search consumes SDK model/entity/scene
records and indexes their names, stable IDs, references and provenance; it does
not parse retail formats in the browser.

`importer/script_inspection.py` verifies the actor against a fresh scene import,
then follows supported encoded MAN instruction boundaries. Inline MES tokens
are consumed atomically so dialogue punctuation cannot become phantom script
opcodes. Unknown instructions stop a path; overlapping boundaries invalidate
the graph. The actor inspector presents dialogue, instruction successors,
opaque ranges and source details without executing scripts or evaluating story
flags. Raw source bytes are transient private inspection output, never part of
the portable project metadata or tracked source.

`sdk/scene_preview.py` combines verified poses and texture associations into
one bounded geometry cache keyed by project, import digest, scene and source
file identity. Nested decoders share one verified disc handle only within the
synchronous request; subsequent operations reverify and source changes reject.
Authored transforms do not invalidate geometry. `editor/scene-renderer.js`
consumes SDK matrices and decoded triangles, draws depth-tested textured meshes
and performs ID-buffer picking. The existing overlay supplies selection and
gizmos. Unknown Y uses a display ground plane; unknown facing uses identity.
Source units, overlapping placements and unsupported marker fallbacks remain
visible. These are authored scene references, not reconstructed runtime
visibility, ground geometry or live entity poses.

`observer/correlation.py` samples bounded MAN-header and model evidence under
the same scene epoch. `RuntimeCandidates` components are transient and cleared
when attachment or observation fails. Single candidates remain candidates;
addresses, list order and nearest positions never become imported IDs.

One project has one verified disc identity. Structural scene/actor/model IDs
remain stable across import and reopen, and are scoped by that disc identity;
runtime pointers are never asset IDs. Each entity projects Transform,
ModelRenderer, Animation and RetailMetadata components only where evidence
exists. Unknown retail height, initial facing and animation asset resolution
remain explicit. Merely exposing a component does not establish its semantics.

Imported metadata is copied into content-addressed `Imported/` records and
checked on reopen and save. `project.legaia.json` contains source identity,
local disc reference, import digests and authored component overrides. It does
not embed game binaries or model payloads. Undo/redo changes only authored
state; an effective transform merges authored fields with imported fields.
An authored height does not turn an unknown imported height into a known fact.
Reimport rejects changed evidence underneath authored actors.

Authored actor templates are separate UUID project records with source disc,
scene and actor provenance. Versioned v1 scopes capture position axes,
appearance donors or both. `authored-actor-preset-v2` requires an existing
authored initial-animation witness and optionally captures authored position
and appearance. The frozen template's clip proof is independent of the source
actor's later overrides. A detached final-component proposal validates the
appearance and animation together before single or group atomic application.
Omitted components and imported facts remain intact; inherited clip matches
normalize to absence rather than empty overrides. Portable v1/v2 metadata
envelopes retain exact import hashes and fresh witness proof. Existing Build
writers compose the resulting initial MAN header once. There is no spawning,
new clip pairing or channel retargeting. See the
[animated preset workflow](legaia-animated-actor-presets.md).

`sdk/resources.py` exposes source-verified texture and animation discovery.
The central AssetDatabase stores derived catalogs separately from its immutable
model imports, keyed by scene and current source key. Refresh does not dirty or
save project content. Opening another project creates a new database; the editor
discards resource views when the source key changes. A failed refresh removes
the preceding catalog rather than presenting it as freshly verified.

Texture IDs resolve through the existing bounded scene TIM catalog. Pixel
responses carry RGBA and separate STP bytes; project metadata contains neither.
The texture inspector displays TIM-local palette choices without assuming
runtime palette selection, atlas residency or blend behavior. Animation records
aggregate verified MAN-to-ANM bindings and retain exact actor/model references.
The browser requires an explicit actor association before previewing its clip.
Unreferenced ANM records and shared-party texture uploads remain outside this
scene-resource catalog's advertised scope.

The resource catalog also indexes actor scripts and inline dialogue by their
existing structural identities. Metadata-only script records carry per-PC flag
and transition references, partial-decode status and source hashes. Dialogue
records link to their script and actor; the browser opens the verified inspector
at that segment. No retail message text is added to the project asset database.
See [script resources](legaia-sdk/script-resources.md) for scope and evidence.

Supported dialogue text uses authored `Dialogue.runs` keyed by actor and
record-relative message/run PCs. Set/Clear commands share project history and
save/open; source verification precedes editing and building. The serializer
merges exact audited glyph spans with placement and appearance changes, leaving
controls and opaque data unchanged. Greedy compressed overflow can invoke a
bounded optimal LZS parse for inputs up to 256 KiB; references expand exactly
within output bounds. See [dialogue authoring](legaia-sdk/dialogue-authoring.md).

The browser's opt-in Live follower consumes the same guarded observation API.
It chains accepted epoch IDs, allows only one capture at a time, and stops on
rejection instead of reconnecting or retrying automatically. Selected observed
candidate positions are a separate read-only canvas overlay; they never replace
authored model placements or become confirmed entity bindings. See
[Live follow](legaia-sdk/live-follow.md).

The data layers are imported (retail facts), derived (decoded previews and
indexes), authored (project edits), live (epoch-scoped observations) and
generated (private build output). Live observation never changes imported or
authored state. Missing runtime identity, guards or witnesses produce an
unavailable response, not an unguarded RAM read. Live mode cannot issue editor
authoring commands. A build pipeline must eventually consume authored values
through independently validated serializers. `importer/serialization.py` now
implements the representable MAN X/Z inverse and bounded deterministic LZS
encoding. `sdk/build.py` verifies a fresh retail import, preserves opaque bytes,
and emits a hash-guarded `.psxmod` using the framework's format-6 `disc_user`
overlays. The runtime applies these to data sectors as they are read; it does
not modify the stock image. Unsupported authored fields and compressed growth
fail before publishing a package. Visual actor-change acceptance is distinct
from successful package construction or boot. See `FEATURE_MATRIX.md` for
current coverage and `TEST_PLAN.md` for the acceptance gates.

Clearing all effective edits also has a build result: a verified retail baseline
with a manifest-only package and zero data overlays. Build reimports the source
scenes to check provenance, records `build_kind=retail`, and does not manufacture
unchanged payload patches. Prior authored packages remain available, so the
same private Run lifecycle can compare an authored build against its revert.

`importer/export.py` encodes the verified preview into a standalone GLB with
embedded PNG textures, bounded accessors and source provenance. The editor
submits only the asset/clip/frame identity; the server regenerates verified
geometry and writes a unique file under the private project `Exports` folder.
Client geometry and output paths are rejected. Export is a full raw model or
one baked pose, with a single display-axis conversion and corrected winding;
it does not author replacement retail data or invent glTF animation channels,
joint hierarchy or physical meter scale.

## Two programs: the recompiler and the runtime

PSXRecomp is split into two CMake projects that are built and run separately:

```
  recompiler/           runtime/
  ───────────           ────────
  MIPS  ──▶  C           C + hardware simulation  ──▶  native game binary
  (build-time tool)      (linked with the generated C)
```

- **`recompiler/`** (C++20) is an offline tool. It reads MIPS R3000A machine code
  and emits C source files under `generated/`.
- **`runtime/`** (C99 + C++17) is the engine. It loads the game's assets into an
  emulated PS1 address space, links the generated C in as native functions, and
  simulates the console's hardware around them.

A **game repository** (e.g. TombaRecomp) contains no framework source — it links
this framework in (as a submodule) and provides the game's config, seeds, and
build glue. See [`BUILDING.md`](BUILDING.md#linking-the-framework).

## The recompiler (`recompiler/`)

Two entry points share the same translation core:

- `src/main_bios.cpp` — ingests the flat BIOS ROM (`SCPH1001.BIN`, loaded at
  `0xBFC00000`) and emits `generated/SCPH1001_*.c`.
- `src/main_psx.cpp` — ingests a `PS-X EXE` extracted from a game disc and emits
  `generated/<serial>_*.c`.

The translation pipeline:

| Stage | File | Job |
|---|---|---|
| Decode | `mips_decoder.cpp` (+ vendored `rabbitizer`) | Decode MIPS instructions |
| Control flow | `control_flow.cpp`, `basic_block.cpp` | Build basic blocks / CFG |
| Discovery | `function_discovery.cpp`, `function_analysis.cpp` | Find function entry points (seeded from Ghidra exports) |
| Codegen | `code_generator.cpp`, `full_function_emitter.cpp`, `strict_translator.cpp` | Emit C: one function per guest function, plus a dispatch table |

Output is **two files** per program: a `_full.c` (the function bodies) and a
`_dispatch.c` (the address→function dispatch table). Both are build artifacts and
are **never hand-edited** — if the C is wrong, the fix is in the recompiler.

GTE (the PS1 geometry coprocessor) instructions are emitted inline;
COP0 kernel-mode instructions the BIOS needs are handled in codegen.

## The runtime (`runtime/`)

The runtime is assembled by one CMake helper, `psxrecomp_add_runtime_target()`
(defined in `runtime/runtime.cmake`), which a game's `CMakeLists.txt` calls with
the paths to its generated C. The runtime provides:

- **Memory & address space** (`memory.c`) — the 2 MB main RAM, scratchpad, BIOS
  ROM, and MMIO regions, with the dispatch that routes a guest PC to its native
  function (static, overlay, or interpreter).
- **Hardware simulation via MMIO handlers** — GPU (`gpu.c`, `gpu_sw_renderer.c`,
  `gpu_gl_renderer.c`), DMA (`dma.c`), timers (`timers.c`), CD-ROM
  (`cdrom.c`, `iso_reader.cpp`), MDEC, SIO0 controllers/memory cards
  (`sio.c`, `memcard.c`), SPU (`spu.c`), GTE (`gte.cpp`), and interrupt delivery
  (`interrupts.c`).
- **Host services** — window/input/audio via SDL3 by default (SDL2 is an
  explicit compatibility backend), a cooperative-thread
  scheduler on host fibers (`psx_fiber.c`: Win32 Fibers / POSIX `ucontext`), and
  the optional debug TCP server (`debug_server.c`).

### BIOS: LLE baseline + a swappable HLE tier

The recompiled `SCPH1001.BIN` is the **low-level (LLE) baseline**: it *is* the
kernel, and it is the reference implementation and the correctness oracle. There
are no per-vector HLE shims replacing it.

On top of that, PSXRecomp carries an optional **HLE tier** (`bios_hle`, on by
default for player convenience) that skips the BIOS boot sequence and intercepts
a small set of BIOS services — always falling through to the recompiled BIOS for
anything it doesn't implement. LLE stays fully linked and is what every accuracy
check runs against. Turn it off with `[runtime] bios_hle = false` or
`PSX_BIOS_HLE=0`; with it off the build behaves as pure LLE. (Design notes:
[`docs/internal/HLE_SCHEDULER_CARVEOUT_PLAN.md`](internal/HLE_SCHEDULER_CARVEOUT_PLAN.md).)

Those are **two independent axes**, and the distinction matters because a build
links more than one BIOS ([`BIOS_SELECTION.md`](BIOS_SELECTION.md)):

| axis | what it needs from the image | on retail SCPH-1001 | on bundled OpenBIOS |
|---|---|---|---|
| boot-skip | `shell_entry_phys` — works under pure LLE | yes | yes |
| kernel-call HLE | `deliver_event_ret` — the kernel's own DeliverEvent `$ra` | yes | refused, loudly |

So **"skip the BIOS and go straight to the game" means the same thing on every
BIOS**: the boot-skip is not synthesis, it just returns immediately from the
shell call, so it needs nothing BIOS-specific beyond knowing where the shell is
entered. Whether the *kernel-call* tier is additionally available is a separate,
per-image question, and refusing it must never cancel the boot-skip — deriving
one from the other is the bug fixed in 2026-07. Both axes are decided in one pure
place, `psx_bios_hle_plan()`
([`runtime/include/bios_hle_plan.h`](../runtime/include/bios_hle_plan.h)), which
is unit-tested over the whole matrix.

### Static / overlay / interpreter dispatch

This is the heart of the system and has its own doc,
[`EXECUTION_MODEL.md`](EXECUTION_MODEL.md). In brief: a guest PC resolves to
statically-recompiled native code (BIOS + main EXE), a runtime-compiled **native
overlay** (`overlay_capture.c` → `tools/compile_overlays.py` →
`overlay_loader.c`), or the small **dirty-RAM interpreter**
(`dirty_ram_interp.c`) — in that priority order.

### Overlay compile backend

When an overlay needs compiling, the runtime spawns a C compiler on the
recompiler-emitted C and loads the resulting DLL — it does not JIT in-process.
The backend tier is resolved in `overlay_backend.c` (see `main.cpp` around the
`code_provider` setup):

```
  static  →  gcc  →  tcc
```

- **static** — the overlay was baked into the binary at build time (best case).
- **gcc** — used when a system `gcc` is on `PATH` (the development default).
- **tcc** — TinyCC, the toolchain-free fallback **bundled beside shipped
  executables** in `overlay_toolchain/` (an embedded Python + `tcc.exe`) so
  players never need a compiler installed.

Compiled overlays are stored in a content-addressed cache namespaced by
compiler and target ABI (`<game>/gcc/<arch-abi>/…` vs `<game>/tcc/…`); a `gcc`
shard wins over a `tcc` shard for the same region. See
[`docs/FEATURES.md`](FEATURES.md), [`docs/OVERLAY_CACHE_V2.md`](OVERLAY_CACHE_V2.md),
and [`docs/ASYNC_OVERLAY_COMPILE.md`](ASYNC_OVERLAY_COMPILE.md).

## Renderers

Three GPU backends behind one interface:

- **Software rasterizer** — CPU, most portable, the reference look.
- **OpenGL** — GPU-authoritative VRAM/FBO renderer, the default; moves
  rasterization and supersampling onto the GPU. Falls back to software if GL
  init fails. (See [`docs/internal/GL_RENDERER_HANDOFF.md`](internal/GL_RENDERER_HANDOFF.md).)
- **Vulkan** — experimental. The build option `PSX_ENABLE_VULKAN` defaults **ON**
  (compiled when the SDK tools are present), but it is not the runtime default
  renderer: selecting it also requires the game to offer Vulkan and the user to
  request it, otherwise the runtime falls back to OpenGL.

Widescreen (a genuine wider GTE FOV, not a stretch) is opt-in and gen-time; see
[`WIDESCREEN.md`](WIDESCREEN.md) and
[`docs/internal/NATIVE_WIDE_PLAN.md`](internal/NATIVE_WIDE_PLAN.md).

## The oracle model (how correctness is checked)

PSXRecomp validates itself against **Beetle PSX** (the mednafen-psx libretro
core), run as a **separate process** with an identical TCP JSON debug protocol:

- `psx-runtime` — the recompiled runtime (debug server on port 4370).
- `psx-beetle` — Beetle PSX (debug server on port 4380).

A tool written against one works against the other by switching ports; cross-
checking is done by querying both, never by sharing state in one process. There
is also a first-divergence **co-sim** build that cycle-locksteps the compiled
backend against the interpreter. See
[`docs/internal/COSIM_ORACLE.md`](internal/COSIM_ORACLE.md),
[`docs/config_schema.md`](config_schema.md), and [`TCP_COMMANDS.md`](TCP_COMMANDS.md).

## Configuration

A game is configured by its **game config** (`game.toml`). A **BIOS config**
(`bios/*.toml`) describes a BIOS image's identity and address model.

The two are **not merged.** The BIOS config is consumed only by the recompiler
at build time (`psxrecomp-bios`, and `psxrecomp-game` for the address model);
the shipping runtime never loads it — `runtime/src/main.cpp` contains no call to
`load_bios_config`. `[runtime]` keys therefore take effect only from `game.toml`,
`settings.toml`, the CLI, and the environment. Full schema:
[`docs/config_schema.md`](config_schema.md).

## Where to go next

- [`EXECUTION_MODEL.md`](EXECUTION_MODEL.md) — static/native/interp in depth.
- [`BUILDING.md`](BUILDING.md) — dependencies + build steps.
- [`../CONTRIBUTING.md`](../CONTRIBUTING.md) — dev workflow and rules.
- [`../CLAUDE.md`](../CLAUDE.md) — the exhaustive engineering constitution.

Authored TIM files are content-addressed under private project Authored/Textures.
Project references carry a hash, length, format and source scene; imported
metadata stays immutable. Apply/Clear use normal history. Preview caches include
texture references and verify authored file integrity before serving cached
geometry. Model and scene previews use effective scene TIMs, with separate party
banks. Builds batch member replacements by source carrier, preserve headers and
opaque bytes, and reject compressed growth beyond the original allocation.
See `legaia-sdk/texture-authoring.md` for the exact writable boundary.

ProjectService exposes a project-wide authored asset projection keyed by existing
actor, texture and template IDs. It derives rows from authored state without
registering them as imported facts or decoding retail resources. The browser
merges by stable identity, labels authored settings separately from source
provenance, and switches through SceneService before selecting an inactive
scene actor or opening its texture. Replacement previews still verify source
identity even when launched without a derived catalog refresh.

Field MAP decoding provides derived collision, trigger and region assets through
the existing resource service. The scene window and source carrier are verified
before table decoding; signed bounds and table overlap are checked. A separate
preview endpoint returns source-wall rectangles in guest X/Z coordinates. The
editor projects those at a labeled display Y=0 and never derives collision
semantics itself. Invalid responses and source changes discard the overlay.
See `legaia-sdk/field-map-workspace.md` for reference sources and scope.

The trigger inspector follows verified gate-1 references through the resource
service to a bounded MAN P2 inspection response. The importer resolves source
identity and record bounds; the editor only renders instructions, dialogue and
explicit unresolved paths. Reports never enter authored or imported state.
See `legaia-sdk/trigger-script-inspection.md` for the source contract and limits.

Build results include a UI report projected from the validated audit. An input
metadata digest lets the editor retain and mark older reports stale across
commands and undo, while project replacement clears them. The digest is not
an ongoing file-integrity check. See `legaia-sdk/build-review.md`.

Runtime discovery prepares exact-PC witness collection only after compatible
identity negotiation. Owned launch readiness invokes that preparation before
the user enters a field. Initial missing witnesses are collection setup, not
scene evidence; subsequent observation retains all currentness and hash checks.
Late attachment and post-restore observation still require actual re-execution.


## SDK inspector property contract — 2026-09-30

`inspector_schema.py` owns versioned component property metadata exposed through
ProjectService state. `component-inspector.js` consumes it for layered Transform
controls, layered appearance references, read-only ModelRenderer/Animation/runtime
status and SDK provenance/evidence details, with an escaped
read-only fallback for unregistered components. Command adapters whitelist
supported project commands; metadata does not authorize runtime writes.
Existing SDK validation/history/serialization remain authoritative. Specialized
donor/script/asset action adapters have not all migrated. See
[the property contract](legaia-inspector-schema.md).


Inspector action metadata now resolves through an explicit editor handler
registry for six donor/model/script/candidate tools. SDK labels, capability/value
conditions and Edit requirements drive button presentation. Handlers retain
independent Edit/source/selection/busy checks and existing validated workflows;
unknown action IDs do not render. Metadata never supplies executable commands.
Specialized forms and remaining animation/template/asset actions are separate
migration work.

## Reviewed external rigid animation import

`importer/animation_glb.py` validates GLB channels and performs source-preserving
TR quantization. `sdk/animation_glb.py` owns fresh binding resolution, effective
baseline comparison, per-actor contribution merging and exact shared-bank
composition. `sdk/server.py` owns bounded HTTP transport, private GLB/sidecar
export and model-preview decoration. `editor/animation-glb.js` owns explicit
file selection, review freshness and dialog lifecycle. Apply uses ordinary
`AnimationChannels` commands; no new persistence or runtime writer is introduced.
See [animation GLB workflow](legaia-animation-glb.md).

## Source-bound GLB RGB interchange

Model profile v2 exports a raw float-vector RGB attribute per existing source
color slot, separately from render `COLOR_0`. The importer owns exact packet
locations, shared flat/Gouraud identities and no-RGB sentinels. The model service
rebuilds the binding from effective source bytes and restricts pending changes
to positions, UVs and baked RGB; the registered model tool reuses Review, posed
inspection, normal replacement history, persistence and Build. Legacy v1 codec
profiles retain their original positions/UV behavior. No runtime lighting or
new packet allocation is inferred.

## Source-bound GLB face references

Profile v3 retains immutable object/primitive/corner ownership while allowing
existing source vertex IDs to change a polygon connection. Source references
encode SVECTOR byte offsets (vertex ID times eight). The importer validates
object-specific capacities and all alias references, independently of glTF
material assignments. Positions remain owned by the selected source vertex ID.
The service and registered model inspector reuse exact replacement audits,
posed preview, commands, persistence and normal Build. Legacy profiles retain
their own supported field sets; no new packet/vector allocation is inferred.

## Scenery yaw milestone — 2026-10-02

Scenery yaw gestures use pure source-frame rotation/command helpers and finite affine renderer overrides. GPU instances and imported transforms remain immutable during pointer motion. Pointer release submits the existing Environment command. Source/context/camera/layer guards and current canvas bounds cancel stale gestures; window resize also cancels before release. Shared descriptor previews respect explicit individual yaw overrides. No separate serialization or patch writer is introduced. See [workflow and evidence](legaia-scenery-rotation-gizmo.md).

## Scenery group rotation — 2026-10-02

The scenery rotation-group service composes source-qualified per-cell position and yaw overrides through the existing Environment writer. Review keys bind selection, selected anchor, quarter-turn operation and current source/project key. Source layout uses exact integer quarter turns; source yaw is a scalar edit retaining X/Z angles. The renderer previews both full matrices and position overrides without imported/GPU mutation; framing, picking and outlines share the result. One ordinary Environment command owns Apply/history/persistence/build. Closed pending reviews and stale source withdraw retained inspection. See [workflow](legaia-scenery-group-rotation.md).

## Source-normal direction diagnostic — 2026-10-02

Static model previews add triangle-aligned raw source normals and coverage metadata. Flat and Gouraud source references are decoded once in the importer; the editor and GPU renderer consume qualified SDK arrays. Authored previews refresh these arrays, partial animation geometry trims them consistently, and assembled posed scene assets discard them. Static normal coloring uses separate normal GPU buffers and inverse-transpose model transforms, without mode-change uploads. Texture alpha/STP and pick ownership remain identical, while grid/wireframe retain their prior appearance. Unposed-only UI/renderer guards prevent inventing animated directions. Structural normal-table source bounds remain hard requirements. See [workflow](legaia-model-source-normals.md).
