# Architecture

How PSXRecomp is put together, end to end. For the higher-level "why three ways
of running code" story, read [`EXECUTION_MODEL.md`](EXECUTION_MODEL.md) first;
this doc is the component-level view.

## Legaia SDK and authoring editor

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

Authored transform templates are separate project records with source disc,
scene and actor provenance. They capture only explicitly authored position
axes and apply absolute values through the normal undo command to an existing
same-disc actor. Unspecified axes and imported facts remain intact. Templates
neither create native entities nor imply model/animation replacement support;
Build applies the same representable-field checks as ordinary edits.

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

Supported dialogue text uses authored `Dialogue.runs` keyed by actor and
record-relative message/run PCs. Set/Clear commands share project history and
save/open; source verification precedes editing and building. The serializer
merges exact audited glyph spans with placement and appearance changes, leaving
controls and opaque data unchanged. Greedy compressed overflow can invoke a
bounded optimal LZS parse for inputs up to 256 KiB; references expand exactly
within output bounds. See [dialogue authoring](legaia-sdk/dialogue-authoring.md).

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
