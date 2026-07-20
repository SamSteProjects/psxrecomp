# Legend of Legaia SDK

A modern, provenance-aware SDK and game-editor foundation for inspecting,
understanding, and eventually modifying *Legend of Legaia* through a native
PSXRecomp runtime.

> **Branch notice**
>
> This README describes the experimental `legaia-sdk-integration` branch. It is
> not necessarily representative of the repository's default branch. The branch
> contains accepted SDK foundations and active research, but it does **not** yet
> contain the finished Unity-like editor described in the roadmap below.

The project combines two deliberately separated layers: PSXRecomp provides the
generic PlayStation execution foundation, while `integrations/legaia/` adds
Legaia-specific import, semantic identity, provenance, layout profiles, and
future editor-facing contracts. Users supply their own legally obtained game
disc; retail assets are not included in this repository.

## Project Status

| Layer | Current state |
|---|---|
| Architecture and integration contracts | Complete for the current foundation |
| Deterministic `town01` importer | Accepted against the supported retail disc |
| Legaia Trace inspector | Implemented as a local, read-only metadata viewer |
| Model asset identity and provenance | Accepted for `town01` |
| Revisioned runtime-layout research | Implemented with explicit unknowns |
| Generic PSXRecomp observer protocol | Protocol 1.5 adds stateless profile-scoped observation guards and guarded bounded reads |
| Headless Legaia runtime observer | Stable retail town01 boundary-only acceptance; actor traversal remains gated by exit/re-entry validation |
| Windows startup and stale-cache correctness | Corrected with regression coverage |

Retail live actor snapshots, imported-to-runtime actor matching, RAM editing,
and authored game changes have not been accepted. The observer can establish a
scoped town01 boundary, but it still fails closed before actor traversal.

## Vision

The long-term goal is a Unity-like workflow built around the original game
engine. A future editor should be able to load scenes from a user-supplied disc,
show a 3D viewport and field-actor hierarchy, select an NPC, and trace each
property back to the disc record, script, asset, or runtime observation that
supports it.

Planned editor capabilities include:

- a 3D scene viewport, actor hierarchy, property inspector, and transform gizmos;
- model and animation selection;
- dialogue and story-flag editing;
- interaction and movement-script graphs;
- drag-and-drop NPC creation;
- live preview through the recompiled runtime; and
- eventual PS1-compatible and extended-native build targets.

These are roadmap goals, not current product features.

## What Works Today

### `town01` Scene Importer

The accepted importer follows this metadata-only pipeline:

```text
user-supplied Mode 2/2352 disc
  -> ISO9660
  -> PROT.DAT and CDNAME.TXT
  -> town01 scene range
  -> Legaia LZS decompression
  -> MAN actor placements
  -> deterministic metadata JSON
```

For the supported North American `SCUS-94254` build, the accepted result has:

- 52 imported `town01` actor placements;
- 52/52 unique, stable semantic actor IDs;
- confirmed imported X/Z positions and placement tiles;
- model pool, model index, and animation-record IDs;
- bounded source-record provenance; and
- explicit unknowns rather than invented values for unresolved properties such
  as Y position and initial rotation.

Repeated imports are byte-identical. The output contains structural metadata,
claims, evidence, confidence, and bounded source locators, but no extracted MAN,
TMD, TIM, dialogue, executable, or disc-sector payloads.

### Model Asset Identity

The additive model catalog identifies where models belong without exporting
their bytes:

- 119 stable model asset identities;
- 114 scene-local models and 5 global-special models;
- 52/52 actor model references resolved;
- 119 confirmed concrete source records;
- 29 referenced assets and 90 unused-but-represented pool assets;
- no aliases, null pool entries, or invalid indices in the accepted `town01`
  data; and
- 119/119 structural parity rows against the pinned reference implementation.

Asset IDs describe structural pool slots and provenance. They are not inferred
character names, runtime pointers, or exported model and texture data.

### Legaia Trace Inspector

Legaia Trace is the current read-only visual surface. It supports:

- local JSON selection and drag-and-drop, with parsing in browser memory;
- no upload endpoint, remote storage, or browser persistence;
- searchable actor records and confidence filtering;
- X/Z structural placement projection and actor selection;
- imported transform and model-identity inspection;
- PROT and MAN source provenance;
- expandable claims, evidence, confidence, and notes;
- visible unresolved properties; and
- a responsive browser layout.

It does not render retail 3D models, connect to a running game, author changes,
or modify RAM.

### Provenance and Confidence

Every semantic property is represented as a claim with evidence and source
provenance. The shared confidence vocabulary is:

| Confidence | Meaning |
|---|---|
| **Confirmed** | Directly supported by validated structure, code, or repeatable evidence |
| **Strongly Inferred** | Multiple strong signals support the interpretation, but proof is incomplete |
| **Tentative** | Plausible and useful as a hypothesis, not safe as editor truth |
| **Unknown** | Evidence does not support a value |
| **Contradictory** | Credible evidence supports incompatible interpretations |

A conceptual claim can say that a two-byte field is a confirmed signed X
coordinate because a traced reader and writer agree, while the adjacent
unresolved field remains `Unknown`. Agreement between two tools is supporting
evidence; it does not silently promote a guess into a known property.

### Runtime Layout Research

The first revisioned `SCUS-94254` field-layout profile records what a future
observer may safely interpret:

- field actors are individually allocated linked nodes, not a fixed-stride
  contiguous actor array;
- the 32-entry interaction/collision census is rebuilt each frame;
- the census is filtered and distance-culled, so its position is not actor
  identity;
- observer-owned scene epochs prevent a reused RAM address from retaining
  semantic identity across transitions;
- known actor-prefix fields are documented with per-field evidence and
  confidence; and
- imported-to-runtime matching remains unresolved.

Addresses with incomplete evidence remain Strongly Inferred, Tentative, or
Unknown and are not presented as universal facts. See the
[runtime-layout research](docs/legaia-sdk/runtime-layout-research.md) and
[profile contract](docs/legaia-sdk/runtime-layout-profile.md) for the detailed
field map and selection rules.

### Generic PSXRecomp Observer Protocol

The generic newline-delimited JSON protocol is `psxrecomp-debug` **1.5**. It
provides:

- protocol and capability negotiation;
- runtime, BIOS, and main-executable identity;
- distinct executable-image, structural-range, and registration inspection;
- token-bound catalog paging and structured ownership reasons;
- process-local executable-image lifecycle and backend-owner observations;
- bounded exact-instruction execution witnesses with live identity and
  watched-generation currentness;
- stateless observation guards scoped to client-declared RAM signals and
  execution witnesses;
- guarded reads that withhold payload on a scoped-boundary mismatch;
- authoritative watched-page generation state;
- bounded multi-region RAM reads;
- frame-before and frame-after stamps;
- executable-ownership boundary stamps; and
- fail-closed address, length, aggregate, and response validation.

Native PSXRecomp implements the full identity and bounded-read surface.
DuckStation and Beetle expose only the generic subset they can support
truthfully. No Legaia-specific protocol command was added, and the present SDK
foundation requires no debugger RAM writes.

### Runtime Correctness and Portability

This branch also contains generic runtime corrections needed for trustworthy
observation:

- static overlay ranges participate in watched-page invalidation;
- replacing executable bytes at the same guest address cannot leave stale
  native code dispatchable;
- current RAM is revalidated before native dispatch becomes eligible again;
- Windows/MSVC startup portability issues were corrected; and
- fresh native launch and protocol 1.5 scoped-boundary acceptance passed.

These fixes establish correct failure behavior and a bounded generic ownership
catalog, but they do not establish the title-specific field-overlay identity
described next.

## Current Runtime Boundary

The generic runtime now models the following relationships explicitly:

- the loaded executable image;
- executable segments and structural ranges;
- dispatch registrations;
- immutable source identity;
- registration-time validated identity;
- current live identity; and
- active native ownership.
- exact-PC backend execution observations; and
- bounded DMA capture-instance creation and supersession.

The whole-image interpretation of field overlay 0897 remains deliberately
unaccepted: `0x801CE818` is not an authoritative image event and no canonical
whole-overlay range/hash is claimed. Protocol 1.4 established a
fail-closed **field execution identity** from three independent current
instruction witnesses, combined with executable build and scene signals. This
identity repeated across field-scene replacements and fresh launches.

Protocol 1.5 now establishes a stateless boundary over only the profile's scene
signals and three witnesses. Repeated fresh-runtime town01 boundary-only passes
retained one scoped token while unrelated global executable state changed and
frames advanced. No actor bytes were read and no RAM writes occurred. Normal
bounded navigation did not reach a town01 exit, so live exit invalidation and
re-entry epoch creation remain unaccepted; actor traversal stays disabled.

## What Is Not Implemented Yet

- accepted retail Legaia actor enumeration;
- imported-to-runtime actor matching;
- click-to-select NPCs in the running game;
- transform gizmos or actor movement/editing;
- dialogue editing;
- story-flag naming and editing;
- interaction-script or movement-script graphs;
- adding new NPCs;
- authored project persistence;
- model or texture replacement;
- disc rebuilding or patch generation;
- native extended asset loading;
- a full 3D editor viewport; or
- playable SDK-authored modifications.

## Architecture

The project has three layers:

1. **PSXRecomp**
   - statically recompiles PlayStation MIPS R3000A code to generated C and then
     native code;
   - runs the recompiled BIOS and game against a PS1 hardware and memory runtime;
   - handles overlays, generated/native registrations, and interpreter fallback
     for runtime-installed code that is not safely native yet;
   - owns the generic debug protocol and runtime-correctness boundary.
2. **Legaia integration layer**
   - owns disc and scene import, semantic IDs, provenance, asset identities,
     revisioned runtime-layout profiles, and the future authoring model;
   - keeps imported, derived, authored, live, and generated state distinct.
3. **Legaia Trace**
   - is the current read-only visual consumer of importer metadata;
   - is intended to become an editor-facing surface only after the underlying
     identity and authoring contracts are accepted.

PSXRecomp's execution model remains generic. It supports a recompiled BIOS and
main executable, content-checked native overlays, and a correctness-first MIPS
interpreter fallback. Missing native coverage may reduce performance; it must
not reduce correctness. See [Execution Model](docs/EXECUTION_MODEL.md),
[Architecture](docs/ARCHITECTURE.md), and [Building](docs/BUILDING.md).

The project uses
[`AndrewAltimit/legend-of-legaia-re` at `d6e64c68`](https://github.com/AndrewAltimit/legend-of-legaia-re/tree/d6e64c68ede25813d35db20980da82a1a025549b)
as a pinned, attributed research reference and parity oracle. It is not a Git
submodule, runtime or Python/Cargo dependency, required subprocess, shipped
component, or wholesale copy. PSXRecomp-side evidence is retained independently
for adapted interpretations.

## Repository Layout

| Path | Purpose |
|---|---|
| `integrations/legaia/` | Isolated Legaia SDK integration root |
| `integrations/legaia/tools/` | Importer command-line entry points |
| `integrations/legaia/tests/` | Synthetic and opt-in disc-gated tests |
| `integrations/legaia/layouts/` | Revisioned runtime-layout profile and validator |
| `integrations/legaia/inspector/` | Legaia Trace browser application |
| `docs/legaia-sdk/` | Architecture, evidence, acceptance, and roadmap documents |
| `runtime/` | Generic PS1 runtime, hardware, overlays, and debug server |
| `recompiler/` | MIPS R3000A analysis and C code generation |
| `tools/debug_client.py` | Generic native/oracle debug-protocol client |

Generated game C, local imports, overlay captures, and retail-derived output are
not SDK source and must remain outside version control.

## Quick Start

### Run the importer

From the repository root in PowerShell:

```powershell
python integrations/legaia/tools/legaia_import.py `
  --disc "<path-to-your-legally-obtained-disc.bin>" `
  --scene town01 `
  --output "<local-output>\imported-town01.json"
```

The importer currently accepts the supported Mode 2/2352 North American build
and emits metadata JSON. Keep generated retail output outside the repository.

### Run importer and layout tests

```powershell
python -m unittest discover integrations/legaia/tests -v
```

Retail-disc acceptance is opt-in. Set the environment variable only for the
current PowerShell session:

```powershell
$env:LEGAIA_DISC_BIN = "<path-to-your-legally-obtained-disc.bin>"
python -m unittest discover integrations/legaia/tests -v
```

Disc-gated tests skip cleanly when `LEGAIA_DISC_BIN` is absent; synthetic tests
are not a substitute for retail acceptance.

### Run Legaia Trace

Legaia Trace requires Node.js 22.13.0 or newer. Its checked-in package scripts
support this local workflow:

```powershell
Set-Location integrations\legaia\inspector
npm ci --ignore-scripts
npm run dev
```

Open the local URL printed by the development server, then choose **Open
import** or drag in the importer JSON. Validation commands are `npm test` and
`npm run lint -- --ignore-pattern work` (the extra ignore excludes local
deployment artifacts, not source).

### Query a locally built runtime

These commands require a running native PSXRecomp runtime on its default local
debug port:

```powershell
python tools/debug_client.py protocol-info
python tools/debug_client.py runtime-identity
python tools/debug_client.py executable-catalog images 8
python tools/debug_client.py executable-catalog registrations 8
python tools/debug_client.py executable-regions 0 8
python tools/debug_client.py read-regions signal_a=0x80000000:4 signal_b=0x80000010:16
```

The client prints compact executable-region summaries while preserving the
protocol's structured output. The examples perform reads only. See
[TCP Commands](TCP_COMMANDS.md) for the complete generic command surface.

### Build the generic PSXRecomp foundation

PSXRecomp builds on Windows with MSVC or MinGW, macOS on Apple Silicon or
Intel, and Linux with Clang or GCC. CMake 3.20+ is required; platform-specific
dependencies and supported generators are documented in
[Building](docs/BUILDING.md). Clone with submodules because the generic runtime
has third-party UI dependencies:

```powershell
git clone --recurse-submodules https://github.com/SamSteProjects/psxrecomp.git
Set-Location psxrecomp
cmake -S recompiler -B recompiler/build -DCMAKE_BUILD_TYPE=Release
cmake --build recompiler/build --config Release
cmake -S runtime -B runtime/build -DCMAKE_BUILD_TYPE=Release
cmake --build runtime/build --config Release --target psx-runtime
```

Game-specific generated code and configuration are separate inputs to the
generic runtime. A legally obtained BIOS is required for execution and is not
included.

## Testing and Acceptance

The branch is validated in distinct layers rather than through one misleading
aggregate test count:

- synthetic importer parsing, bounds, determinism, and provenance tests;
- an opt-in real-disc gated test for the supported build;
- repeated deterministic output and JSON Schema validation;
- metadata-only and absolute-path scans;
- Legaia Trace production-build, rendering, lint, and privacy tests;
- model-identity structural parity against the pinned reference;
- layout-profile schema, canonical serialization, and fail-closed validation;
- generic observer-protocol, bounds, capability, and compatibility tests;
- watched-page and stale-cache regression tests;
- Windows/MSVC startup regression tests; and
- fresh native-wire protocol acceptance with bounded-read latency checks.

`test_reachable_discovery_codegen.py` has a separately tracked
invalid-discovery-mode fail-closed failure. Current project documentation does
not attribute it to the Legaia SDK changes, and this branch's README work does
not modify it.

## Legal and Data Boundaries

- Users must supply their own legally obtained game disc and BIOS where needed.
- No game assets, executable bytes, dialogue dumps, extracted models or
  textures, disc sectors, or RAM snapshots are included.
- Generated retail importer JSON is kept outside the repository.
- Importer output is metadata-only; it identifies structures and provenance
  without embedding asset payloads.
- Overlay captures and other files containing retail bytes must remain local.
- This is an independent project and is not affiliated with or endorsed by
  Sony Interactive Entertainment or the owners of *Legend of Legaia*.

Repository components have distinct licensing and attribution boundaries.
PSXRecomp is distributed under the [PolyForm Noncommercial 1.0.0 license](LICENSE).
The pinned reference repository declares its own license and remains an external
research source; see the [Legaia integration data and license boundary](integrations/legaia/README.md#proprietary-data).
Third-party libraries retain their respective licenses. No license is changed
by this integration.

## Roadmap

**Completed foundation**

- architecture and integration contracts;
- deterministic `town01` import and semantic actor IDs;
- concrete model asset identity and provenance;
- read-only Legaia Trace inspector;
- runtime-layout research and revisioned profile;
- generic observer protocol;
- executable image/range/registration modeling and bounded catalog paging;
- accepted multi-witness field execution identity; and
- stale-cache correction and native startup acceptance.

**In progress**

- live scene-exit invalidation and re-entry epoch acceptance; and
- keeping retail actor traversal gated until that transition proof exists.

**Next**

- complete live transition acceptance for the scoped scene epoch;
- accepted linked actor-node snapshots;
- evidence-backed runtime fields; and
- imported/runtime correlation research.

**Later**

- live inspector integration;
- transform authoring;
- dialogue and story-flag editing;
- movement and interaction tools;
- new actor creation; and
- PS1-compatible and extended-native build or patch targets.

No completion dates are assigned, and later milestones remain subject to
evidence, compatibility, and data-boundary review.

## Documentation

- [Legaia SDK architecture](docs/legaia-sdk/architecture.md)
- [`town01` retail-disc acceptance](docs/legaia-sdk/town01-acceptance.md)
- [Model asset identity](docs/legaia-sdk/model-asset-identity.md)
- [Runtime-layout research](docs/legaia-sdk/runtime-layout-research.md)
- [Runtime-layout profile contract](docs/legaia-sdk/runtime-layout-profile.md)
- [Future correlation signals](docs/legaia-sdk/runtime-correlation-signals.md)
- [Runtime bridge](docs/legaia-sdk/runtime-bridge.md)
- [Field-overlay 0897 identity attempt](docs/legaia-sdk/field-overlay-0897-identity.md)
- [Accepted field execution identity](docs/legaia-sdk/field-execution-identity.md)
- [Headless runtime observer](docs/legaia-sdk/headless-runtime-observer.md)
- [Scene epoch observation](docs/legaia-sdk/scene-epoch-observation.md)
- [Scoped scene epoch](docs/legaia-sdk/scoped-scene-epoch.md)
- [Live actor-node snapshot](docs/legaia-sdk/live-actor-node-snapshot.md)
- [Debug protocol versioning](docs/debug-protocol-versioning.md)
- [Executable identity](docs/executable-identity.md)
- [Executable image model](docs/executable-image-model.md)
- [Executable image lifecycle](docs/executable-image-lifecycle.md)
- [Backend-neutral execution ownership](docs/execution-ownership.md)
- [Execution witness model](docs/execution-witness-model.md)
- [Execution witness protocol](docs/execution-witness-protocol.md)
- [Observation guard model](docs/observation-guard-model.md)
- [Observation guard protocol](docs/observation-guard-protocol.md)
- [Executable lifecycle protocol](docs/executable-lifecycle-protocol.md)
- [Executable catalog pagination](docs/executable-catalog-pagination.md)
- [Executable ownership diagnostics](docs/executable-ownership-diagnostics.md)
- [Bounded `read_regions` command](docs/read-regions-command.md)
- [Native runtime launch acceptance](docs/runtime-launch-acceptance.md)
- [Legaia integration README](integrations/legaia/README.md)
- [Generic PSXRecomp architecture](docs/ARCHITECTURE.md)
- [Generic execution model](docs/EXECUTION_MODEL.md)
- [Build guide](docs/BUILDING.md)

## Project Status Summary

The project currently provides a validated, provenance-aware scene and asset
importer, a read-only visual inspector, a runtime-layout knowledge base, and a
generic PSXRecomp observation protocol. It does not yet provide the finished
Unity-like editing workflow, but the accepted foundation is being built
specifically toward that goal.
