# Architecture

How PSXRecomp is put together, end to end. For the higher-level "why three ways
of running code" story, read [`EXECUTION_MODEL.md`](EXECUTION_MODEL.md) first;
this doc is the component-level view.

## Legaia SDK and authoring editor

`model-vertex-connectivity.js` derives bounded object-local selections from qualified Current preview triangle indices and ranges. The movement editor owns local selection/staleness/draft locks; the existing saved-group service owns persistence and history. Connectivity does not infer spatial welding or runtime ownership, and this module introduces no authored geometry or serialization.

`model_vertex_grid.py` qualifies an explicit selected-axis/source-unit grid operation through the existing native vector writer, preserves signed16 bounds and audits against retail layout. Project object-preview and model-replacement history own Review/Apply; the movement editor owns local staging, source freshness and complete candidate/scene qualification. Native Build reuses the existing model replacement composition.

`script-node-layers.js` renders selected source boundaries from the already qualified branch snapshot/review DTOs. It validates bounded raw spans and source shape, derives exact per-node byte differences, and keeps unavailable/unvisited paths explicit. `script-branches.js` owns selection and review lifecycle, Current composition remains in SDK operand writers, and stale/failed/discarded reviews withdraw the renderer. No new endpoint, authored state or serializer is introduced.

`source_build_script.py` resolves imported script owners in verified emitted MAN carriers, reusing bounded saved-package/PROT qualification from `npc_build_script.py` and existing native layout/instruction readers. It introduces no authored state or serializer. `source-build-script.js` owns receipt selection, source/state freshness checks, raw-record hash/difference qualification, bounded paired display and local download; the script dialog owns disposal and shared busy state.

`effect_color_authoring.py` qualifies five-byte RGB/signed-intensity source windows over existing decoded instruction/owner evidence. `ScriptEffectColors` is project-local authored state, owned by the command service and shared script operand/reset registries. `effect_colors.merge_patch` independently checks native composition audits. Both MAN Build gates include this family, preventing a color-only scene from silently bypassing fixed operand serialization. `script-effect-colors.js` owns the typed forms; the main editor supplies selection, source context and command lifecycle.

`audio-note-timeline.js` derives bounded encoded-note relationships from the already qualified sequence DTO. FIFO same-channel/key pairing is explicit display policy, not runtime voice identity. `audio-sequence.js` owns lazy timeline lifecycle, source withdrawal and source-row navigation. The timeline introduces no endpoint, command or authored state; its only server change is static module registration.

`animation_glb_rig.py` qualifies an explicitly selected skin's joint manifest and inverse-bind accessor; the existing animation decoder samples rigid joint/ancestor channels without importing mesh skinning. Both SDK workflows normalize `external_skin_index` into source-bound Review identities and retained recipes. `animation-glb-rig.js` validates those bindings and Review evidence; shared mapping controls own skin selection and invalidation.

`audio_waveform.py` shares source qualification and prefix decoding between metadata inspection and private PCM preview. `/api/audio-pcm` emits a bounded source-qualified preview payload without adding bytes to project metadata. `audio-waveform-contract.js` owns the shared metadata DTO; `audio-audition.js` verifies PCM SHA/envelopes, owns explicit-rate Play/Stop/context cleanup and writes exact mono WAV locally. Playback uses the browser [Web Audio API](https://developer.mozilla.org/en-US/docs/Web/API/BaseAudioContext/createBuffer); preview settings never become retail/runtime pitch or authored bank data.

`importer/audio_waveform.py` owns bounded zero-history SPU-ADPCM prefix decoding and envelope/flag evidence. `/api/audio-waveform` binds scene, entry, bank and sample identities through the SDK resource service. `editor/audio-waveform.js` validates source/prefix/envelope/marker contracts, renders frame coordinates and owns stale/close withdrawal. No sample rate, playback or authored bank serialization is introduced.

`importer/audio_bank.py` independently qualifies bounded contiguous/split VAB carriers and program, packed tone and sample-size tables. `sdk/resources.py` and `/api/audio-bank` enforce current scene and physical entry identities; `editor/audio-bank.js` verifies the DTO, owns the read-only filtered table view and withdraws stale sources. Metadata does not establish PCM, playback, instrument mapping or native authoring.

`importer/actor_runtime_capacity.py` qualifies the complete source SCUS/load image and retail function hashes before deriving the static actor-pool bound. `sdk/npc_build.py` assesses appended MAN counts before encoding and includes source evidence in normal package audits. The lower bound rejects guaranteed overflow; it does not resolve scenery/script demand or enable native gameplay acceptance.

`sdk/model_materials.py` exposes a bounded, read-only AssetDB model catalog tied to the active scene source key. `editor/model-material-donor.js` qualifies its DTO and extracts only semantic page/depth/indexed CLUT values from a qualified Current model snapshot. The existing material editor owns requests, draft capture, review and Apply; copied values create no donor runtime dependency or new serialization family. Target geometry, UVs and blend flags retain existing ownership. Packet-group copy constructs source-qualified primitive diffs in a separate candidate draft map, validates the whole resulting batch and budget, then replaces drafts atomically. It preserves group and unrelated primitive contributions.

`sdk/animation_glb.py` resolves qualified assigned pose/model witnesses while keeping the selected actor identity distinct from imported shared-clip contribution ownership. V2 sidecars encode both witnesses; exact regenerated binding and source-key checks gate review/Apply. The existing AnimationChannels command targets the named clip owner, preserving other components and contributors. Unassigned v1 sidecars retain their exact format.

`editor/worldmap-placement-yaw.js` converts pointer positions through the frozen horizontal-plane homogeneous projection, unwraps consecutive angles, and snaps/wraps encoded source yaw. Its SVG ring owns temporary gesture state only. The placement editor combines mutually exclusive translation/yaw tools under the same draft restoration and reviewed Apply boundary. Existing source serializers, Build composition and exports remain authoritative.

`editor/worldmap-placement-gizmo.js` owns only temporary projected-axis pointer gestures and signed source-offset snapping. `worldmap-placement-editor.js` binds its frozen source/camera/viewport context to the existing source-qualified record inspector, previews all shared instances, and restores drafts/reviews on cancellation. No gesture writes project state; reviewed Apply uses the normal WorldMapPlacements command. Dialog cancellation releases busy state only for its owned request.

`sdk/worldmap_placement_export.py` binds Current/Proposed geometry to the source MAP/floor context and the normal WorldMapPlacements serializer. It revalidates proposal keys, composes only qualified record transforms, and retains per-instance retail and exported identity. The shared world encoder adds explicitly bounded placement provenance and representation while preserving its retail-only default contract. The editor verifies representation, MAP/review/hash binding and late-response state before download. Exports are artifacts, not authoring commands or gameplay acceptance.

`sdk/worldmap_placements.py` owns source-record transform qualification, strict persisted WorldMapPlacements components, immutable MAP/floor/disc bindings, reviewed command keys and exact offset/yaw serialization. Its Build stage merges disjoint full-MAP claims and rejects conflicting source bytes. The dedicated editor consumes SDK records, validates review coverage, constructs source-offset/yaw matrices independently, and uses the existing scene renderer for Current/Proposed and picking. Global landmark menus and evaluated runtime state remain separate.

`sdk/npc_build.py` qualifies compressed MAN donor additions for two fixed-span overlay claims. It independently rereads the source carrier, updates only the original consumed stream and decoded-size word, checks exact decompression and unchanged descriptor/payload boundaries, then rechecks authored identity. `build.py` composes other normal asset writers and labels the disabled package feature as source NPC candidates. Build review v2 serializes drafts inclusively; package fit does not establish guest allocation, scheduling or opaque script acceptance.

`importer/worldmap_export.py` adapts the qualified world source graph into the existing scene-export contract. Column-major source matrices become row-major display matrices with one Y reflection; model GLB local reflection is composed by the established scene encoder. `sdk/worldmap_export.py` reloads immutable source geometry, validates disc identity and state before writing a uniquely named artifact in project `Exports`, and returns bounded bytes with the provenance audit. The editor validates the artifact binding and digest before downloading; visibility controls affect export scope, not source placement confidence.

`sdk/environment_rotation_math.py` and `editor/environment-rotation-math.js` retain identical frozen Q30 quarter-wave source-yaw tables. Python integer and JavaScript BigInt arithmetic round rotated displacements to signed source units before the existing cell-local descriptor merger checks capacity and range. `environment_rotation_group.py` retains the legacy quarter-turn operation and adds an exact `yaw_units` variant; reviewed keys bind either shape to source, selection and project state. The editor validates proposals independently, and the existing Environment command/writer owns persistence and Build. This is an editor placement convention, not a reconstruction of retail GTE arithmetic.

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

### Verified model-source service - 2026-10-06

`SDK ModelSourceService` keeps immutable Retail TMD derivations and scene import
qualifications behind `_disc_context`: each new operation still hashes the full
disc, and nested scope exit checks detect changes before publishing cached data.
Qualification keys bind the imported document and verified disc digest. LRU
limits are eight scene qualifications, 32 models and32 MiB; caches/locks are
process-local and omitted from persistence. Project deepcopies start with fresh
services. Authored native files and original GLB receipts are read and qualified
every time. Detached GLB reconstruction shares the one verified Retail source
for that model, with an imported-evidence digest guard, not arbitrary disc reads.
This belongs in the integration's source service; the editor consumes its APIs.


### Project-wide historical animation input service (2026-10-06)

`animation_sources.library` projects the Current receipt collection across all
recorded scenes without depending on active scene, actor selection or live RAM.
It validates sealed receipt metadata and distinct referenced GLB files within
the 32-receipt/64-MiB project bounds. Its key binds project root, mode, receipts
and native overrides. SDK download and removal Review operations require that
key and exact root identity; the editor validates replies and hashes downloads.
The Asset database toolbar hosts `animation-source-library.js`, which filters
SDK records without interpreting MAN/ANM addresses. Metadata removal passes
through ProjectService commands and the existing validated Undo/Redo path.
Source bytes are retained for Undo and only Current references enter snapshots.
Receipts are historical external inputs, never native replay authority or live
identity evidence; native authoring continues to require fresh qualified Review.


### External rigid-object mapping (2026-10-06)

Animation bindings optionally carry `external_object_nodes` as an authored
interchange choice. SDK services strip only that field when qualifying the
remaining export identity against current retail/native provenance. The GLB
importer validates one unique reachable node per native object, rejects conflicts
with preserved source identities, and uses the existing hierarchy/sample/native
channel serializer. Review authorization includes the ordered mapping even when
two choices produce identical native bytes. Receipt metadata retains and checks
the mapping; frontend binding/report decoders verify it before pose or Apply.
Editor node inventories are bounded display metadata and do not invent retail
bone semantics. Skinning and automatic skeletal retargeting remain unsupported.


### External animation time sampling (2026-10-06)

Bindings optionally carry `external_sampling` with exactly `start_seconds` and
`rate`. SDK services validate finite bounds and omit this authored choice only
when qualifying fresh export identity. The importer preserves native frame
count and uses `float32(start_seconds + float32(i/fps) * rate)` with endpoint hold.
Explicit sampling permits external key times up to 3600 seconds; legacy imports
retain their native-duration guard and report shape. Existing hierarchy, channel,
quantization, ownership and native packing checks remain in force.

Review keys include normalized sampling independently of candidate bytes. Source
receipts validate and retain the choice; historical input remains distinct from
current native replay authority. `animation-glb-sampling.js` shares controls and
validation between both animation dialogs, with fresh Review required after
changes. Native playback timing and skeletal retargeting remain separate gaps.


### Model GLB source-object identity (2026-10-06)

`importer.model_glb.source_object_identity` resolves preserved object-index tags
before canonical object-N name fallback. Tagged nodes may be renamed, unnamed or
reordered; canonical tag/name contradictions and invalid indices reject. The
fixed-layout importer still validates unique complete native object coverage,
static scene ownership, source aliases, topology, transforms and packet fields.
Source metadata selects an existing object, never retail ownership or capacity.
Material-face selection shares this resolver after complete Current no-op GLB
qualification, so renamed inputs cannot diverge between geometry and material
workflows. Binding schemas and native command formats remain unchanged.


### Fixed-layout model rigid hierarchy baking (2026-10-06)

The model importer reuses bounded static-node validation and parent-first rigid
composition from animation interchange. Model-specific source identity, one-scene,
1024-node, complete reachability and unowned-mesh checks remain explicit. It
transforms represented POSITION aliases and rotates raw stored normal vectors
through the native/GLB Y conversion before existing quantization and packet audit.
Unused vector slots and padding remain source bytes. Unlit sentinels are checked
before rotation; legacy lit profiles without normal authoring reject rotation.

These transforms bake external geometry into existing native object slots;
scene placement and animation records remain separate authored concepts. Native
capacity, object count and packet topology are unchanged. Material-face selection
continues through complete Current native roundtrip qualification and the shared
object resolver, including transform-only groups. Review schemas, authorization,
commands and normal Build serializers remain unchanged.


### Model-only uniform scale composition (2026-10-06)

`importer.model_glb_transforms.static_model_hierarchy` extracts bounded positive
uniform scale from copied node TRS or affine matrix metadata, then delegates
source mapping, tree validation and rigid orientation qualification to the
existing animation hierarchy implementation. Model poses carry translation,
rotation and composed scale. Parent scale affects child translation before parent
rotation; native positions receive the composed scale before rotation/translation.
Raw stored normals retain magnitude and use only the composed orientation.

The original GLB metadata is not mutated. Local and composed scales are bounded
1/1024..1024, while existing source integer, alias and packet guards still qualify
native output. Model binding/review schemas, Project commands and Build formats
stay unchanged. Animation import keeps unit scale; this module does not extend
native animation formats or scene-instance transforms.


### Positive nonuniform model scale and normal directions (2026-10-06)

Model hierarchy poses now store full linear matrices, translations, cofactor
normal matrices, measured singular scale bounds and an optional uniform-only rotation.
Local matrix columns are divided by their positive axis lengths for the existing
rigid orientation/TRS validation. Parent linear matrices multiply child linear
matrices and translations; this preserves shear arising from valid nested TRS.
The implementation follows the
[glTF node transform order and local matrix decomposition rules](https://registry.khronos.org/glTF/specs/2.0/glTF-2.0.html#transformations).

For positive determinant transforms, the cofactor matrix has the same normal
direction as inverse-transpose; its common determinant factor cancels when
restoring the original raw normal magnitude. Zero normals stay zero. Uniform-only
poses keep their prior quaternion normal path. The importer converts native normal
axes before/after this operation and applies the existing integer/alias guards.
Legacy lit profiles cannot omit required normal edits. Local axes and actual
composed singular scales are bounded 1/1024..1024. A one-sided Jacobi SVD uses
copied columns, three pair rotations per sweep and at most 32 sweeps; nonconvergence
rejects. It avoids the loss of small singular values from forming A^T A, admits
bounded reciprocal parent/child scales and still rejects excessive intermediate
ancestors. The boundary allowance is 64 ulps of the largest singular scale because
absolute roundoff follows that scale, including on small rotated axes. Accepted
boundary noise is clamped in pose diagnostics only; geometry and normals use the
original composed matrix. No source metadata is mutated; no new dependency,
binding, command or Build format is introduced.


### Explicit model object mapping (2026-10-06)

Model binding v1/v2/v3 may carry an optional `external_object_nodes` authoring
choice. `_prepare` removes only this optional choice when comparing the fresh
regenerated source binding, then includes it in the Review digest and report.
Omitted mappings retain the previous binding/review shape. Explicit null rejects.
The importer passes the choice into the shared rigid node ownership validator,
while retaining model-specific 1024-node, complete reachability, mesh ownership,
local/composed scale, packet layout and native field checks. Model material-face
selection receives the same qualified object-to-node mapping.

The model GLB dialog owns a separate mapping control and bounded node inventory.
Its file revision captures the mapping text; event changes and silent text changes
both withdraw accepted Review. Choice equality is checked in Review and proposed
model responses. Mapping controls lock during pending operations, while the
existing command, persistence and Build paths consume the verified native model
without introducing a new native format or runtime identity assumption.


### Fixed-layout model GLB source receipts (2026-10-06)

`sdk/model_glb_sources.py` owns historical input receipts separately from the
retail model source cache (`sdk/model_sources.py`) and allocation-ledger mesh
receipts (`sdk/model_mesh_sources.py`). A model receipt seals original GLB bytes,
source binding/mapping, candidate digest and Review digest; it does not grant
replay authority. Optional project `model_sources` metadata is validated on
Save/Open and copied with SHA-addressed files in `Authored/Models/GLBSources`.
Native Apply and receipt publication replace the existing native history entry
with one combined before/after snapshot. Undo/Redo qualifies source files and
restored native bindings before changing state. Failed publication restores
metadata/history; immutable unregistered files may remain for later cleanup.

Authored state keys and export input capture include registered receipts/files,
so project copy and normal Build snapshots remain reproducible. Legacy empty
collections keep old document/key shapes. The owning GLB dialog dynamically opens
read-only input recovery; downloads verify exact originals and never treat an
archived source key as Current authority. No native model, Build package or runtime
format changes. Receipt management and project-wide model source browsing remain
separate pending features.


### Reviewed model source receipt removal

`model_glb_sources.review_removal` seals the current scene/project source key,
project root, selected receipt, complete model source collection digest and project
document digest excluding that collection. The explicit removal route recomputes
this report and requires its exact Review key and request fields before publication.
This guards receipt-only changes that do not alter the scene preview source key.

The `remove_model_source` command publishes only receipt metadata and creates one
`model_sources` history entry. Undo/Redo validates all restored receipt files before
changing state or history stacks. Native replacement collections remain unchanged;
physical source files remain available for recovery. Shared GLB byte budget is
released only when the last registered reference is removed. The browser keeps
removal separate from downloads and Review, locks closing during publication and
refreshes the parent editor from the returned project state. The retail model source
cache and native package formats remain unchanged.


### Project-wide model input library

`model_glb_sources.library` validates all registered receipts and SHA-addressed
files before returning a deterministic scene/model/receipt ordering and distinct
byte totals. Its key binds project root, Edit/Live mode, the receipt collection and
native model overrides; active scene and selection are deliberately independent.
Library download and removal routes require the exact project root, library key
and receipt. Download rechecks the key after reading. Reviewed removal recomputes
the report and preserves the same metadata-only history and immutable source files.

`editor/model-source-library.js` owns a project-level modal with scene/search
filters, qualified original GLB/binding/receipt recovery, Refresh and explicit
Review/removal. It consumes SDK responses without parsing retail structures.
Recovery is available in Live mode; removal is exposed only in Edit mode. The
panel refreshes after publication, and registered shared-byte accounting is
separate from physical file deletion. Source receipts remain historical evidence,
not authority to replay a stale external import.


### Model input source navigation

The project input modal exposes an optional navigation callback, separately from
receipt mutation. Before leaving the modal it requalifies the selected receipt.
`navigateModelSource` captures project root, mode and library key, checks the exact
receipt before and after scene navigation, then verifies the stable model identity
in the current SDK asset inventory. It selects the authored or imported inspector
layer from current project state. The parent editor supplies its normal scene API
and model inspector; pending model edits prevent navigation. Historical bindings
remain recovery evidence, while the normal current export creates fresh bindings.


### Historical model input native comparison

`model_glb_sources.compare_native` resolves a qualified library receipt and reads
its Retail source through `ModelSourceService` inside one verified disc context.
If an authored binding exists, `read_model_replacement` qualifies the actual native
file and its source evidence. The response separates source, current and historical
candidate hashes and labels current representation explicitly. Library key,
selected imported-document digest and disc path are rechecked before publication.

The exact-field read-only HTTP route is consumed by the project input panel.
Browser decoding binds receipt/project/library identities, bounded native size,
hash equality claims, representation and no-write claims. The operation never
changes the active scene, selected entity, receipt collection or command history.
It reports current-byte equality, not historical binding replay authority or
validated in-game appearance.


### Animation input source navigation

`navigateAnimationSource` captures a saved receipt, project root, mode and library
key, requalifies it before and after scene navigation, then resolves target kind.
Imported inputs require one exact current scene entity and use normal selection.
Retained inputs refresh the SDK asset catalog, recheck the library and require one
source-scene authored-retained animation with the exact UUID. The existing retained
asset decoder validates the current record, model, source hashes and provenance
before the existing clip inspector opens. Actor assignment is not substituted for
retained clip identity, and historical bindings are never replayed.

The parent editor supplies scene/selection APIs and current asset/inspector services.
The library modal releases its read operation before handing off navigation; close
or context changes during verification prevent the handoff. Native authoring and
command history are unaffected; current inspector controls own any later explicit
export, Review or Apply.


### Historical animation input native comparison

`animation_sources.compare_native` verifies a qualified project-library receipt
inside one checked disc context. Imported inputs resolve the exact recorded
scene-ANM clip and model witness from Retail metadata, verify its record preimage,
then extract the same index from the normally composed authored bank. Source actor
initial assignments remain separate from this shared-clip identity.

Retained inputs validate their current native ledger and Retail donor witnesses,
then reconstruct only the selected UUID from frozen donor bytes and current edits.
The reconstruction view includes a retired capture for readback without changing
its actual removal mask. The response explicitly distinguishes captured bytes
from membership in the emitted native bank. Record hashes/counts, immutable byte
and rigid-object budgets, library key, selected import evidence and disc path are
qualified before returning. SDK and browser preserve project/receipt/scene identity
and reject stale or forged requests. This read-only route never creates an Undo
step, navigates scenes, publishes native bytes or authorizes historical replay.


### Operation-owned model LZS derivations - 2026-10-06

`ProtArchive._model_lzs_sections` holds immutable decoded model container bytes
only while its outer `_disc_context` is active. `assets._model_container` keys
sections by the complete frozen `ProtEntry` and section index; both misses and
hits verify the requested compressed-stream offset. The existing model reader
still checks the full disc digest, containing size and final model byte span.
Insertion-order LRU retains at most eight sections and 16 MiB. The outer context
clears the archive cache in `finally`, including disc-stamp and decoder failures;
nested scope exits preserve it for the remaining outer operation. This does not
change scene geometry caching, persistent SDK model-source caching or file formats.
It avoids repeatedly decoding a shared container for different models in a cold
scene. A local actual Town01 measurement reduced model-container decodes from
118 to 2 and cold preview time from 19.445 to 11.611 seconds, with identical
normalized output. Fresh SDK HTTP proof and operation-lifetime tests preserve
full verification for each separate operation; no gameplay acceptance is claimed.


### Signed static model transforms and native winding - 2026-10-06

`model_glb_transforms` factors reflected local matrices into a proper rigid
rotation and one signed axis, retaining the full affine hierarchy. Local magnitudes
and composed singular values use the existing bounds. `ModelPose.reflected` derives
from the final composed determinant. Its normal cofactor includes determinant sign
so normalization restores original native magnitude with inverse-transpose direction.
The positive-uniform quaternion path remains unchanged.

Current v6 `model_glb` profiles reverse native winding for reflected mapped objects
by exchanging corners 1 and 2. Existing qualified packet writers carry vertex refs,
UV, Gouraud RGB and normal operands through that permutation; flat fields retain
corner zero and opaque/material/padding bytes remain untouched. Legacy profiles
reject reflections before source field publication. Review, pending audits, native
replacement history, retained GLB receipts and normal Build require no format or
endpoint changes. Reflections preserve allocation-ledger identities and tombstones.
The glTF determinant/winding rule is format evidence; the native packet permutation
and raw normal magnitude policy are independently implemented and checked against
all 24 supported packet families. Private actual browser/Build proof does not claim
in-game rendering or normal-based retail lighting acceptance.


### Verified mesh recovery artifacts - 2026-10-06

`model-mesh-sources.js` validates exact sealed receipt fields, disjoint ordered
ledger spans and bounded single/batch recipe shapes. Every artifact uses the
existing Current-qualified SDK source-download route, whose native reader verifies
retained ledger reconstruction. `qualifyMeshSourceDownload` compares the complete
selected record with the displayed receipt and independently hashes the returned
GLB. Detached settings/receipt JSON is published only after that source check and
a final context guard. Dialog-owned AbortController and pending controls prevent
closed or concurrent reads from publishing artifacts. Initial recovery availability
is tied to the parent mesh source read; native import recipes are never replayed.

## Mesh settings draft recovery (2026-10-06)

`model-mesh-settings.js` decodes bounded single/batch recipes and qualifies them against a freshly decoded GLB inventory and Current native triangle donors. `model-mesh-append.js` owns the file read, generation/context checks and abortable inventory request; it publishes draft controls only after successful qualification. A batch recipe hands the qualified inventory and detached settings to `model-mesh-batch.js`, which restores selected sections and per-section choices. Missing donors produce an empty selection and disable Review. Loading settings never calls native Apply; existing Review/Apply endpoints retain their current-source, file-hash and review-key checks. No receipt or recipe is accepted as write authority.

## Project mesh input library (2026-10-06)

`model_mesh_library.py` collects sealed `mesh_imports` receipts from project-native model bindings. It qualifies per-model catalogs with scene-scoped shallow views, leaving the actual active scene and selection untouched. One outer verified disc operation owns retail/container reads; all retained inputs reconstruct through existing ledger validation. A key seals root, mode, imported evidence and native bindings before/after verification and download. The global reader bounds receipts and distinct GLB bytes and exposes exact-field HTTP routes for catalog and recovery only.

`mesh-source-library.js` validates grouped receipt ownership, order, recipes, deduplicated counts and byte totals. It independently checks recovered GLB SHA-256 before publishing any artifact. Operation-owned busy state and abort controllers prevent concurrent downloads and late publication after close. Source navigation requalifies the same root/mode/library/receipt before and after a scene change, then opens the Current authored model when present. Mesh settings return through the regular draft/Review/Apply workflow; the library never writes native geometry or removes ledger receipts.

## Mesh import native comparison (2026-10-06)

The mesh library comparison is a read-only derivative of qualified retained input and native ledger state. It uses the independently qualified base binding and replays the prefix before the receipt, the prefix after its import span and the complete Current ledger. Historical bytes must match the receipt candidate hash; complete replay must match Current replacement bytes. Stable face identities introduced by the span are intersected with Current active identities to derive active/retired counts. Whole-model byte equality and face lifetime are separate claims; neither asserts per-face content equality or gameplay behavior. Root/mode/import/native and disc-path guards reject drift before publication. The HTTP route accepts only receipt, project path and library key. The UI validates exact fields, bounded counts and independent boolean/hash consistency before displaying a result.

## Source wall paint drafts (2026-10-06)

`collision_rectangle.review` accepts optional exact-field quadrant edits within its bounded rectangle. Current-baseline mode reads each effective source bit; explicit paint overrides supply a boolean or retail restoration. Canonical sorted edits participate in the review key and v2 response. Apply recomputes that key and publishes one existing Collision command. Native MAP packing stays with `patch_collision_walls`, which audits allowed high-nibble masks and rejects unrelated byte changes. No new height or runtime collision semantics are introduced.

`wallRectangleMap` publishes keyboard-accessible Proposed quadrant controls; Current/Retail layers have no paint handlers. The rectangle controller retains detached qualified source cells for draft display, owns paint choices, invalidates old Review on every changed paint, and requalifies the complete pattern before enabling Apply/scene inspection. Context/generation/abort guards remain on the source read. Scene inspection expands the tool section so its return controls remain visible.


## 2026-10-06: reusable authored wall patterns

Source wall drafts can now be downloaded as portable JSON, loaded at a new First row/column, rotated clockwise or mirrored across X/Z. Patterns contain authored Block, Unblock and Restore retail operations only. They contain no captured retail/Current source bits or write authority. Loading and transforming stage a Current-baseline draft and withdraw previous Review; a fresh native Review is required before Apply. Restore retail resolves the destination's verified source value. Uniform fills retain their full operation set through export and transforms.

The strict `legaia.wall-pattern.v1` format uses relative 64-unit subcells, even bounded dimensions and at most 4096 unique typed operations. File imports are bounded to 512 KiB. Destination staging preserves the existing 4096 selected-bit Review budget, including single-quadrant selections, and rejects out-of-grid placements before changing draft controls. Invalid files preserve existing draft values and disable old Apply authority; closed or superseded readers cannot publish a draft.

Validation: three focused Python native paint/history/HTTP checks and both Node wall-pattern and rectangle programs passed. Maximum-size 4096-operation JSON round-trips within the file budget. Actual retail browser checks passed relocation, rotation, mirroring, exact download/reimport, invalid-file rejection, fresh Review, scene inspection/return, private Apply, Undo/Redo and Save/Open. Wide/narrow screenshots were inspected; no page errors occurred. Private Build readback matched all MAP bytes independently: only wall bits at byte `0x4815` changed (XOR `0x50`); every floor nibble and other byte remained exact. Native MAP SHA-256 `e2b15ff7fdf124d3979af68b6e11f49a6a7cb6905f1e5eecd5faabd4528d8aa0`; package SHA-256 `9c0b5fb9e856dc8343ee1977b9cc89edad5e847193b7863ba4ec6965e003581d`. Evidence: `local-output/sdk-20260909/wall-pattern-20261006/proof.json`. No game launch, runtime attachment or mod installation occurred. Gameplay acceptance remains deferred and the full SDK goal remains incomplete.


## 2026-10-06: repeated wall-pattern placement

Source wall patterns now support repeated rows/columns with explicit gaps in whole 128-unit native grid cells. Stage repeated pattern expands the current authored operations into one Current-baseline draft, preserving quadrant parity and all untouched gap bits. A fresh Review is required before the single atomic Apply. Counts do not change the draft until Stage; repeating again repeats the newly staged pattern. The expanded pattern remains downloadable in the existing portable format and supports rotation/mirroring.

The pure repetition service rejects invalid counts/gaps, grid extent overflow, more than 4096 operations and selected-quadrant Review extent overflow before mutating controls. Sparse gaps count toward the Review extent budget. The existing native source validation, rectangle review seals, serializer and command history remain authoritative.

Validation: both Node pattern/rectangle checks, JavaScript syntax and three focused Python paint/history/HTTP checks passed. Node coverage includes exact operation placement, gap preservation, quadrant parity, rotation equivalence, detached input and count/extent/destination rejection. Actual retail editor workflow staged a 2-by-2 pattern with gaps, downloaded its exact 12 operations, rejected oversized repetition without altering the draft, completed fresh Review and scene inspection/return, and passed private Apply, Undo/Redo and Save/Open. The Review selected 60 wall bits with seven effective changes. Independent full MAP Build readback exactly matched the intended repeated bits and a pre-existing authored gap bit; all floor nibbles and unrelated bytes were preserved. Native MAP SHA-256 `8f9440f1f32d5e842fb14e38a3e878ef4f93920bc478a40b5f3f97448def4d3b`; package SHA-256 `2f2a3d306971882239cef8a88e8f7a4769891d1c34c4b4fe09ab389962c098d9`. Wide/narrow layouts were inspected and browser errors were empty. Evidence: `local-output/sdk-20260909/wall-pattern-repeat-20261006/proof.json`. No game launch, runtime attachment or installation occurred. Gameplay acceptance remains deferred and the full SDK goal remains incomplete.


## 2026-10-06: native floor-selector authoring backend

A distinct `FloorTiers` scene component now authors existing MAN height selectors in the MAP low nibble, independently of wall quadrants. The bounded floor rectangle service exposes read-only source-qualified Review and sealed Apply, supporting tier 0..15 or restoration to each selected retail value. Canonical floor rows/columns are 0..127, including row zero; the wall-biased row/Z convention is not reused. At most 4096 combined authored selectors are accepted. Imported MAP/MAN disc identity, MAP hash, LUT values and MAN provenance bind the Review; changed inputs or project state reject Apply.

Normal commands preserve other scene components, support one Undo step, dirty tracking, Save/Open and component review. Ordinary Build and the shared MAP composer merge low-nibble changes with wall high-nibble edits while rejecting overlapping edits; audits identify floor masks and before/after tiers. Existing LUT entries, ramp flags/records and other native spans are not changed. Shared selectors can affect neighboring surfaces and placed objects; complete live floor heights and gameplay behavior remain unverified.

Validation: four focused Python floor cases and seven existing wall rectangle/paint cases passed. Private retail HTTP Review/Apply, stale rectangle rejection, one Undo step, Undo/Redo and Save/Open passed. Independent full MAP construction matched both ordinary Build and the shared composer exactly, including wall/floor edits in the same byte. Native MAP SHA-256 `77fdc3c86a4f14bbdd7948a4734d916a6358aa23c2cf24ae72ae14666f387820`; package SHA-256 `2c21fc94ca8259ad88dd988b488e7be7e0914d53b6dc938d08443dffb30f0392`. Evidence: `local-output/sdk-20260909/floor-authoring-20261006/proof.json`. The shared composer was exercised with Town01, not with an actual appended-NPC or streaming scene. Status: writable SDK backend; editor controls and Current authored terrain/placement preview are pending next. No game launch, runtime attachment or installation occurred. The full SDK goal remains incomplete.


## 2026-10-06: floor editor and authored height previews

The collision inspector now opens `Edit floor tiers`, with bounded native floor rows/columns, sixteen source-qualified MAN selector choices, retail restoration and separate Retail/Current/Proposed rows. Review supplies the immutable signed MAN values and reference Y labels; input changes withdraw old Apply authority. Inspect proposed floor scene uses a detached SDK project view and the existing Proposed/Current scene comparison with Return to floor review. Apply is one normal floor command, followed by the usual history, Save and Build workflow. The dialog and reader reject stale context and dispose owned requests on close.

Current ground geometry now decodes authored low-nibble selectors before texture association. Floor edits participate in geometry cache identity. Current placed-object transforms use the same evidenced placement-cell selector, composing its LUT height delta with existing scenery offsets/rotations. Retail source records/transforms remain immutable. Adjacent corner consumers and unknown actor preview surface sampling use the updated reference ground. These are source-derived preview heights; native ramp behavior, object visibility and live movement remain unverified.

Validation: eighteen focused Python checks passed across new floor preview composition, floor Review/history/HTTP, environment/texture projection and scene caching. Node floor decoder and existing wall guards passed; editor/module syntax checks passed. Actual retail browser workflow passed typed LUT labels, input invalidation, fresh Review, Proposed scene inspection/return, private Apply, Undo/Redo and Save/Open. Independent vertex-by-vertex comparison proved exact changed ground corners, unchanged topology/materials/UVs and the expected placed-object height delta; source transforms remained identical. Normal private Build matched the full MAP independently, preserving the existing wall bit in the same byte. Native MAP SHA-256 `25bdeeb8a832129ae434a1e072beeb24bbe9e7e2909738c38042cb1120bdb5b7`; package SHA-256 `b91a7e2c9366b65f39517d1df050ab9edf608629bc939ab8006f6216c19ddd7e`. Wide/narrow dialog screenshots were inspected; no page errors occurred. Evidence: `local-output/sdk-20260909/floor-editor-20261006/attempt2/proof.json`. The first browser attempt exposed an inaccessible modal entry point; the collision inspector entry was added before the successful fresh attempt. No game launch, runtime attachment or installation occurred. The full SDK goal remains incomplete; gameplay acceptance stays deferred.


## 2026-10-06: native floor picking in the scene viewport

`Pick floor selector` now resolves the actually visible ground instance and GPU-selected triangle, then opens its nearest projected corner in the floor editor. The draft is seeded with the exact native row/column and Current tier, not an inferred height. Ground preview metadata carries each vertex's source-qualified selector index, so tiers with equal MAN heights remain distinct. Picking can load the scene's collision source automatically and does not change authored state; Review remains required before Apply. Dragging still orbits. Stale scene/project/camera/viewport context and foreign or partial ground ownership reject selection. Outer preview corners use the decoder's evidenced edge clamp and are explicitly labelled when selected.

The independent bounded picker qualifies source cell identity, four-corner coordinates, two-triangle connectivity and typed tier metadata. Floor row zero is supported without the wall-grid bias. The new mode shares the existing viewport controls and excludes competing model-face picking and transition arrival movement. Current authored ground tiers are re-picked from the rebuilt preview, while source provenance stays immutable.

Validation: fourteen distinct focused Python cases passed across terrain metadata, floor preview and scene caching; new floor picking, floor Review and existing model face Node checks passed, as did editor/module syntax. Actual retail browser workflow used real WebGL picking to open native floor row0/column127 at its original tier, confirmed a no-op Review with disabled Apply, made one reviewed private change, and picked again at the authored Current tier. Undo/Redo, Save/Open and independent full MAP Build readback passed while retaining an earlier wall edit. Native MAP SHA-256 `7f2948c1b0212b9dd38041ed8b9d78ef5ae72c965fcc8f5eeace13051e13022b`; package SHA-256 `82db32a6a81544bfbd2f9dc4057a599ebac95b6b73a3fc1d8f796a00be3c1e31`. The picked-floor screenshot was inspected; no page errors occurred. Evidence: `local-output/sdk-20260909/floor-picking-20261006/attempt2/proof.json`. The first test used a point measured before the toolbar layout resized the canvas; a fresh attempt recalculated after source load/layout and passed. No game launch, runtime attachment or installation occurred. Source ground remains a reference surface; native ramps, reachability and gameplay acceptance are deferred. The full SDK goal remains incomplete.

## 2026-10-06: mixed floor-selector painting

The source floor editor now paints individual native shared corner selectors inside one bounded rectangle. Keep Current preserves unpainted selectors; the brush supports any existing MAN tier or retail restoration. Pointer and Enter/Space editing show numbered Proposed points with native coordinates and reference heights. Painting withdraws old Review authority; changing rectangle inputs clears the draft. Fresh Review, Proposed scene inspection/return and normal Apply carry the same canonical selector list. The reviewed patch is one normal Undo step.

The optional v2 Review seals sorted unique row/column/tier operations with the existing project, MAP/MAN, disc and height-table evidence. Duplicate, out-of-bounds, untyped, null and stale inputs reject. Uniform v1 requests remain supported. Native Build preserves wall high bits, unpainted Current selectors and outside authored floor selectors; restoring retail removes redundant overrides. Shared-corner reference heights remain distinct from ramp behavior and live gameplay acceptance.

Validation: nineteen distinct focused Python checks passed across floor authoring/history/HTTP, preview composition, terrain and scene caching. Node mixed floor Review and viewport picking guards passed, with editor/module syntax and diff checks. A fresh private retail browser project passed pointer and keyboard painting, retail restoration, fresh Review, exact Proposed/Current ground and placed-object reference heights, immutable source transforms, Return, Apply, Undo/Redo and Save/Open. Independent full MAP construction matched ordinary Build exactly while retaining a wall edit in the same byte and an outside authored selector. Native MAP SHA-256 `753e0544250c26503d30a2483a85e1d13ed9e36149ae9a8111f003e763db0d40`; package SHA-256 `b62a156e1e1e4926d80b92f66fe45c2549e96c3cdef85f887f93ee3363e795cb`. Wide/narrow screenshots were inspected; page errors were empty. Evidence: `local-output/sdk-20260909/floor-paint-20261006/attempt2/proof.json`. The first harness compared JavaScript negative zero with serialized zero; its expectation was corrected before the fresh successful run. No game launch, runtime attachment or installation occurred. The full SDK goal remains active and incomplete; gameplay verification stays deferred.

## 2026-10-06: reusable authored floor patterns

The floor editor now captures authored selector operations as portable JSON, loads them at a destination, rotates clockwise, mirrors X/Z and repeats them with whole native selector-step gaps. Keep Current captures only explicit paint operations; uniform tier/retail operations capture the selected extent. Loading and transforms stage drafts only, preserving unpainted Current selectors and requiring a fresh source-qualified Review before scene inspection or Apply. Retail restoration resolves against the destination source. File reads are bounded to 512 KiB and reject stale dialog/project context; invalid pattern, repeat or destination choices retain the existing draft.

Each pattern carries its sixteen signed MAN reference values. Every used numeric tier must have the same value at the destination index; different scene height tables reject rather than guessing a replacement. Duplicate-height indices remain distinct. Native floor rows/columns 0..127 are supported, independently of wall row bias; complete extents and operation counts stay within the 4096-selector Review budget. Rotation, mirroring and repetition preserve typed operations; gaps do not copy source retail values. No native Apply authority travels in pattern files.

A browser-discovered no-op bug was fixed: differing storage order of equivalent existing floor edits no longer makes Current Review appear changed. Review compares canonical selector content, and sealed no-op Apply returns without rewriting overrides or adding history. Regression checks preserve an unsorted existing component exactly.

Validation: four focused Python floor authoring/history/HTTP checks passed, including the new no-op regression; Node floor pattern and floor Review checks passed, plus module syntax and diff checks. A fresh private retail browser workflow passed pointer/keyboard painting, rotation, mirroring, a 2-by-2 repeat with gaps, exact download/reimport, invalid-repeat draft preservation, mismatched MAN-height rejection, fresh Review, exact Proposed/Current ground and placed-object reference heights, Return, Apply, Undo/Redo and Save/Open. Its twelve staged operations covered twenty-five selectors; an existing gap selector, outside floor edit and wall bit survived. Independent complete MAP Build readback matched exactly. Native MAP SHA-256 `831bf000fc402b6fa419c1bb0df3d462b09968d52a7b8e8a7cc66317537dc884`; package SHA-256 `22ccffe40e1a13e3c80852b28b371375feb1e89b549b1f2b0d542e7430d172fe`. Wide/narrow screenshots were inspected; no page errors occurred. Evidence: `local-output/sdk-20260909/floor-pattern-20261006/attempt2/proof.json`. The first run exposed the storage-order no-op bug; the fresh run passed after the fix. No game launch, runtime attachment or installation occurred. Gameplay acceptance remains deferred; the full SDK goal stays active and incomplete.

## 2026-10-06: native MAN floor-height authoring foundation

A source-qualified `FloorHeights` scene component now authors the sixteen signed MAN table values independently of MAP floor selectors. Read-only HTTP Review exposes separate Retail/Current/Proposed values and a sealed Apply key; strict typed bounds, source disc/import/MAN identity, stale-input rejection, one normal Undo step, retail restoration and Save/Open are implemented. The low-level serializer changes only requested two-byte entries in MAN `0x02..0x22`; partition counts, actor records and opaque bytes stay fixed. Build labels distinguish source floor heights, floor selectors and collision walls.

Ordinary Build composes header edits with supported MAN data and independent MAP overrides. Appended-NPC and streaming preparation have explicit height composition hooks, separate from MAP handling, with overlap rejection. Synthetic appended-header composition is checked; actual appended/streaming package delivery has not been exercised for this new component. No new runtime behavior or allocation support is inferred from those hooks.

Current ground geometry and placed/decorative object reference transforms now consume the effective authored MAN LUT, composed with Current selectors and scenery transforms. Height edits invalidate geometry cache identity. Decoration metadata now carries its evidenced source selector/LUT/record-offset facts, enabling the same height delta without replacing imported transforms. Floor-selector Review and reusable patterns qualify the Current height table. Source metadata remains immutable; ramps, native runtime overrides and movement acceptance remain unverified. Editor height-table controls and retained Proposed scene inspection are pending next; this checkpoint is a writable SDK/Build and Current-preview foundation.

Validation: twelve distinct focused Python checks passed across height codec/history/HTTP/native Build, floor preview composition, existing selector authoring/history/HTTP and decoration decoding; module imports and diff checks passed. Private retail HTTP Review/Apply, stale heights, one-step Undo/Redo and Save/Open passed. Independent complete decoded MAN and MAP comparisons passed, preserving the existing wall/selector edits. Every ground vertex matched its expected tier delta (1,088 changed corners), and all 208 qualified placed/decorative transforms matched independently while retaining source metadata. Geometry cache identity changed. Native MAN SHA-256 `c6dc3f80d15540c7017f2d48b23fa85acc5234eb6d757f84b4d1614d23d5aa31`; MAP SHA-256 `2222ae211d70fa0b303fb7f5010ceb88699cad90edefd5cdd7b5a70c126e66e1`; final labelled package SHA-256 `99c3a091359cb948193cab4b3f0f18b7acd9c0fa85b11b060bd8c4e99e2041fd`. Evidence: `local-output/sdk-20260909/floor-heights-20261006/proof.json`. An initial test used the wrong MAP filename; it was corrected before the passing native check. The labelled package was written to a fresh output directory after the existing-output guard correctly refused replacing an older manifest. No game launch, runtime attachment or installation occurred. The full SDK goal remains active/incomplete; gameplay acceptance stays deferred.

## 2026-10-06: height-table editor and Proposed scene inspection

`Edit floor heights` now opens from the source collision inspector and Scene Tools, exposing all sixteen source-qualified Retail/Current/draft MAN values and draft reference Y. Signed integer bounds, reset-to-retail, discard-to-Current, fresh Review and normal one-command Apply are connected. Input changes withdraw old Apply and scene-inspection authority. Owned reads abort on close and reject stale scene/project context; the dialog remains bound to its reviewed source. The SDK context route supplies Current values without authoring a change.

Inspect proposed height scene builds a detached project view, validates the original Review and Current scene key, then uses the existing Proposed/Current scene comparison and Return to height review. The source project stays unchanged until Apply. Scene changes invalidate the retained editor. The endpoint rejects foreign active-scene ownership and changed height/Review inputs. Client qualification checks signed vectors, source carrier/hash identity and every exact two-byte MAN audit span, including raw-streaming carrier bounds. This completes the prior height-authoring foundation's normal editor workflow; actual appended/streaming package acceptance and gameplay remain pending.

Validation: four focused Python height codec/context/history/proposal and preview checks passed; the new Node height Review validator passed typed bounds, source identity, exact MAN audit and detached-response guards. Editor/module syntax and diff checks passed. A private retail browser workflow passed sixteen-tier loading, edit/Review, invalid-value withdrawal, retail and Current resets, fresh Review, read-only Proposed inspection/Return, Apply, Undo/Redo and Save/Open. Independent Proposed and Current comparisons matched all ground vertices (1,088 changed corners) and all 208 qualified placed/decorative reference transforms; source records remained immutable. Normal Build independently matched the complete decoded MAN and MAP, retaining prior wall and selector edits. Native MAN SHA-256 `c6dc3f80d15540c7017f2d48b23fa85acc5234eb6d757f84b4d1614d23d5aa31`; MAP SHA-256 `2222ae211d70fa0b303fb7f5010ceb88699cad90edefd5cdd7b5a70c126e66e1`; package SHA-256 `99c3a091359cb948193cab4b3f0f18b7acd9c0fa85b11b060bd8c4e99e2041fd`. Wide/narrow dialog screenshots were inspected; no page errors occurred. Evidence: `local-output/sdk-20260909/floor-height-editor-20261006/proof.json`. No game launch, runtime attachment or installation occurred. The full SDK goal remains active/incomplete and gameplay verification stays deferred.

## 2026-10-06: floor-height delivery with NPC appends and raw streaming

Native package composition is now exercised against retail Town01 and Dolk2: one NPC in a compressed fixed span, eight NPCs requiring compressed relocation, a raw streaming MAN without an NPC, and a raw streaming MAN with an appended NPC requiring relocation. Each height-edited package is reopened independently and its complete decoded MAN compared with an otherwise identical NPC/MAP build using retail heights; only the requested two-byte tier entry may differ. The complete emitted MAP also matches an independent wall-bit and floor-selector calculation, including relocated archive delivery. Actor counts, imported metadata, authored state and history remain unchanged by Build; the authored project passes Save/Open and Review Build. This supersedes the earlier unexercised appended/streaming height-delivery limitation.

Build summaries now name source floor heights when an NPC composition contains the emitted height audit. Missing/empty/unrelated nested audits cannot add that label. Relocation feature descriptions retain the packaged edit list and no longer claim that all allocated clips are unassigned. Gameplay remains explicitly unverified.

Validation: four opt-in retail delivery checks and nine focused Build-report checks passed against the final code (13 total); Python syntax and diff checks passed. Evidence: `local-output/sdk-20260909/floor-height-delivery-20261006/final/proof.json`. The initial compressed verifier used an incorrect carrier field name; that verifier was corrected before the final passing run. No game launch, runtime attachment, installation or full-disc export occurred. Manual floor collision, movement, ramps and NPC behavior acceptance remain deferred; the full SDK goal remains active/incomplete.

## 2026-10-06: selection-group isolation and saved group views

The viewport now isolates the active actor, scenery or mixed placement selection (1..128 renderable instances), including temporary groups containing NPC drafts. Isolation is pinned to the captured group; Restore preserves the camera, manual hidden instances and scene-layer switches. A selected hidden or unrenderable member disables isolation. Scene/project/source/representation changes and active proposals withdraw it, using the existing current-scene binding. Single-instance behavior remains available.

Saved scene views now retain canonical group isolation IDs for imported actors, static decorations and ground, with source MAP binding and every-instance membership/renderability checks. Existing scalar single-instance bookmarks and views without visibility retain their format and behavior. Metadata CRUD/history/Save/Open and Recall use the normal view workflow; NPC-draft visibility remains unsupported in saved views, as before. These are editor display changes, not scene-content edits.

Validation: eleven focused Python saved-view tests and Node view/visibility guards passed, including group history, portable Open, exact static MAP ownership, malformed/duplicate/oversized/hidden-member rejection and legacy compatibility. The actual retail-source browser passed actor-group and mixed actor/NPC/decoration isolation, Restore preservation, mixed actor/decoration bookmark save/recall, metadata Undo/Redo/Save, hidden-member rejection and withdrawal after a private transform change (then Undo). No page errors occurred. Save/Open retained the group exactly; the native package matched the pre-view Build hash. Screenshot inspected. Evidence: `local-output/sdk-20260909/scene-group-isolation-20261006/final/proof.json`. The initial browser verifier assumed an actor kind tag absent from the actual preview; selection now uses SDK entity identity and the corrected workflow passed. No game launch, runtime attachment or installation occurred. The full SDK goal remains active/incomplete, with gameplay acceptance deferred.

## 2026-10-06: saved NPC visibility and unavailable-draft recovery

Saved scene views now capture NPC draft isolation, mixed actor/NPC/static-decoration groups and manually hidden NPCs in the Authored scene representation. NPC-only visibility uses the authored entity identity without inventing a MAP provenance binding; environment members retain the existing source MAP checks. Save/Replace require available, validated same-scene drafts. The existing saved-placement identity validator is reused. Portable Open retains canonical references to deleted drafts, allowing view metadata to remain manageable rather than blocking the project.

Recall is disabled with an explicit missing-draft count and recovery note when hidden or isolated NPC IDs are unavailable. A fresh-state missing-draft guard runs before scene/representation/camera changes. Client validation also checks actual draft scene membership even when preview eligibility IDs are outdated, plus per-instance renderability and Authored representation. Undo restoration of the original draft identity makes all affected views recallable again. Metadata Rename/Delete remain available for unavailable views. This supersedes the earlier saved-NPC-visibility exclusion.

Validation: thirteen focused Python view tests passed, including NPC save/open, deletion with retained portable metadata, unavailable Save/Replace rejection, Undo restoration, malformed IDs and foreign-scene/retail-representation rejection. Node visibility/representation/missing-membership guards and editor syntax passed. A fresh retail-source browser saved and recalled single-NPC, mixed-NPC and hidden-NPC views, deleted the draft, checked all three disabled recalls with unchanged display, saved the unavailable project, restored the draft with Undo and recalled every view. Portable Open passed for both unavailable and restored snapshots; native Build matched the pre-view package hash. The existing group, hidden-member and changed-source withdrawal checks also passed; no page errors. Screenshot inspected. Evidence: `local-output/sdk-20260909/scene-npc-visibility-20261006/final/proof.json`. A Node negative case exposed and led to fixing stale eligibility accepting a foreign-scene NPC before the final passing runs. No game launch, runtime attachment or installation occurred; the full SDK goal remains active/incomplete and gameplay acceptance stays deferred.

## 2026-10-06: frame isolated selections

**Frame isolated** fits the currently visible mesh bounds of the captured isolation group in the viewport. It preserves yaw, pitch, projection, manual hidden instances and layer switches, and accounts for current instance transforms, perspective depth and viewport aspect with ten-percent edge padding. Hidden-layer members are skipped; the action is disabled when no isolated mesh is visible. Saved scene views retain and recall the fitted camera through the existing metadata workflow. Scene content and game coordinates are unchanged.

Validation: the pure camera helper passed eighteen perspective/orthographic, aspect and orientation combinations against the actual renderer projection, plus mutation and invalid-input checks. A fresh retail-source editor browser passed Perspective, Front, Side and narrow-viewport fitting of every current mesh corner, layer skipping/disable, exact saved camera recall, NPC deletion/recovery, metadata history and portable Open. Wide and narrow screenshots were inspected; no page errors. Complete native Build output remained identical before and after the view changes (SHA-256 `ec0f718a3ebfc735e209f6cd935d4d726c5827650095422c5256557c7f7811e3`). Evidence: `local-output/sdk-20260909/scene-isolation-framing-20261006/final/proof.json`. No game launch, runtime attachment or installation occurred. Gameplay acceptance remains deferred and the full SDK goal remains active/incomplete.

## 2026-10-06: historical runtime positions in the central viewport

Saved runtime node reviews now offer **Show historical positions** for the matching current Edit-mode scene. Complete bounded XYZ file samples appear as dashed amber markers with historical/unconfirmed labels, using the existing scene display transform. Incomplete and out-of-range samples are skipped with counts; no Y or identity is inferred. Active controls stay outside the collapsed scene-tool drawer: Frame historical positions, Return to historical review and Clear. Showing samples preserves the camera; explicit framing preserves its angles/projection and scene visibility. These samples are ephemeral display data, not Live observations, actor bindings or persistent edits. Project/mode/scene/source/representation changes withdraw the overlay, and Undo does not resurrect it.

Validation: focused Node review tests passed detached data, matching Edit-scene checks, bounded complete coordinates and authority rejection; existing review/comparison and camera projection tests also passed. A fresh browser with synthetic historical files over the actual retail town01 scene passed show/frame/return/clear, wide/narrow layout, foreign-scene and empty-sample rejection, real source-change withdrawal and Undo. Authored/imported state and its build-state key remained unchanged after verification; no page errors. Wide and narrow screenshots inspected. Evidence: `local-output/sdk-20260909/historical-runtime-viewport-20261006/final-pass/proof.json`. The first browser run exposed hidden controls in the tool drawer, which were fixed. Subsequent verifier corrections distinguished collapsed evidence text and read-only preview requests from authoring. No game launch, runtime attachment, installation or new gameplay validation occurred. Real captured-coordinate/identity acceptance remains deferred; the full SDK goal remains active/incomplete.

## 2026-10-06: spatial comparison of historical runtime files

The saved-runtime comparison report now connects to the central viewport through **Show historical comparison positions**. Baseline samples are blue, comparison samples amber, with Both/Baseline/Comparison layer selection. Dashed segments join different complete coordinates with the same declared node key; file-only keys have markers without segments. Matching keys remain unconfirmed identities, and lines imply neither motion paths nor chronology. Each file is revalidated and the comparison is reconstructed rather than trusting report rows. The limit is 128 nodes per file / 256 displayed samples; missing or out-of-range XYZ values are skipped independently. Frame uses only the selected layer and disables for an empty layer. Return reopens the full comparison evidence; Clear and source-context withdrawal remain ephemeral.

Validation: Node guards passed layer construction, detached evidence, complete-key segments, unchanged positions, file-only keys, missing coordinates, same-scene/Edit/profile checks, malformed layer rejection and the 256-sample bound. Existing runtime review/comparison and camera tests passed. Fresh retail-source browser workflows with synthetic historical files passed both-file rendering, all three layers, layer-switch display preservation, framing, wide/narrow layouts, Return/Clear, empty-layer disable, foreign-scene rejection, source-change withdrawal and Undo; authored state and its build-state key were unchanged after verification. The single-file browser regression also passed. Final comparison screenshots inspected; no page errors. Evidence: `local-output/sdk-20260909/historical-runtime-comparison-viewport-20261006/final-pass/proof.json`, with the single-file proof in `single-regression/`. The first comparison run exposed Return rebuilding a closed dialog without reopening it; this was fixed before passing runs. No real runtime capture, game launch, attachment, installation or gameplay acceptance occurred. Full SDK goal remains active/incomplete.

## 2026-10-06: inspect historical samples from the viewport

Historical overlays now expose a bounded node selector and **Inspect historical sample**, plus an explicit **Pick historical sample** viewport mode. Inspection opens the existing detached review or comparison filtered to that key, preserving complete evidence and original download metadata. Single-file details expand to show coordinates, capture frames and recorded fields. Coincident baseline/comparison markers deduplicate their declared key; different overlapping keys require choosing the selector. Explicit pick gestures take precedence over scene mesh selection and transform handles, guard project/source/camera/viewport context, and never submit authoring commands. Dragging remains camera navigation. Empty layers disable inspection/picking and withdraw pick mode; source changes retain the existing overlay withdrawal. Imported entity selection stays independent.

Validation: Node screen-space hit tests passed the 256-point bound, duplicate-key handling, ambiguity, empty samples and invalid geometry. Existing review/comparison and editor syntax checks passed. Fresh retail-source browsers with synthetic historical files passed selector and actual canvas inspection for single reviews and paired comparisons, capture evidence, preserved camera/selection, all layers, wide/narrow framing, clear/return, empty/foreign rejection and source-change withdrawal. Authored state and its build-state key were unchanged after verification; no page errors. Evidence dialogs inspected. Proofs: `local-output/sdk-20260909/historical-runtime-sample-inspector-20261006/proof.json` and `comparison/proof.json`. No real runtime capture, game launch, attachment, installation or gameplay acceptance occurred. Full SDK goal remains active/incomplete.

## 2026-10-06: verification boundary and current capability overview

`SDK_CURRENT_STATUS.md` is the current subsystem overview; dated detailed checkpoints retain their historical source revisions. Integrated offline checks now record source hashes and preserve a split baseline after a progress-file lock error. Test fixtures must include the real project collections, catalog identity and each delegated source-key boundary; production checks remain explicit. Corrected targeted module acceptance is recorded separately from full-suite acceptance. This checkpoint changes no production architecture and establishes no runtime/gameplay acceptance.

## 2026-10-06: historical actor coordinate comparison

`editor/historical-actor-comparison.js` revalidates historical file/layer samples and compares an explicitly selected key against the current scene entity and matching viewport DTO. Native imported/current/override coordinates and derived viewport surface coordinates remain distinct; unknown axes yield unknown deltas. The output is detached metadata with no identity, authoring or Live authority. The dialog binds source, actor, representation, key, layer and overlay lifetime; stale snapshots stay readable but cannot be exported as current. Historical control synchronization is shared by drawing and busy-state changes so request completion restores toolbar actions without a canvas redraw. Static module serving is explicitly registered; no retail codec or native Build implementation changes.

## 2026-10-06: explicit external animation timeline behavior

`importer.animation_glb.sampling_config` accepts optional `mode` (`clamp`, `repeat`, `ping_pong`). Omitted/explicit clamp canonicalizes to the original two-field start/rate recipe, preserving old review and retained-input identities. Cyclic modes map one common selected-channel key extent before hierarchy sampling; per-object loops are not inferred. Their reviewed `external_time_range` is derived from validated source channels (null for static files). Both frontends share typed mode/range validation and sampling controls, and mode changes withdraw the reviewed candidate. Existing imported/allocated source recipes retain and replay the choice through normal commands/history and native Build; no frame allocation, native loop flag or gameplay timing is invented.

## Source audio Asset Database checkpoint (2026-10-06)

Validation: the retail-enabled 37-test focused Python regression passed with no skips/errors/failures; four existing Node contract checks and all five changed JavaScript module syntax checks passed. Fresh retail-project browser checks passed active/project discovery, source/confidence filtering, typed complete/partial header inspection, provenance visibility, metadata download and reference navigation with no page errors. Wide/narrow screenshots were inspected. Project documents, files, Undo/Redo history and the reference fixture remained unchanged. Normal native Build before/after browsing was byte-identical (package SHA-256 `7ec8b65439c3a5893fc264b95ba1d4a7d8c11af7f7687fe7dc7344a3bfbb6b98`). Private proof: `local-output/sdk-20260909/audio-catalog-20261006/proof.json`. No game launch, runtime attachment, installation or full-disc export occurred; gameplay remains deferred and the full SDK goal remains active.

Audio is now a central read-only resource category in active-scene and project Asset Database scopes, with stable PROT identities, searchable provenance/confidence, a typed header inspector, reference navigation and metadata evidence download. Discovery checks leading signatures across the verified archive and reads recognized entries only inside physical next-TOC boundaries. Retail source evidence found 218 records: 83 supported VAB+SEQ sound packs and 135 qualified leading VAB headers in unresolved containers. Partial records preserve their header and failure reason; they do not invent a sequence or complete bank. Source/chunk hashes, declared programs/samples and SEQ timing headers remain separate from runtime playback.

Evidence uses the pinned Andrew reference `d6e64c68ede25813d35db20980da82a1a025549b` (`sound_pack.rs`, VAB and SEQ header parsers), read through `git show` because the reference checkout HEAD has advanced. The catalog neither adopts that newer revision nor adds it as a runtime dependency. Events, waveform tables, audio preview/edit/replacement, duration, XA, interior audio containers and scene playback assignments remain incomplete. No runtime or gameplay acceptance is asserted. Private evidence: `local-output/sdk-20260909/audio-catalog-20261006/`.

## Source SEQ event inspector checkpoint (2026-10-06)

Validation: all 41 retail-enabled focused Python tests passed without skips/errors/failures. Node source/summary/timing contracts, stale-source withdrawal, close/late-response ownership and existing asset inspector guards passed; all three changed JavaScript modules passed syntax checks. The production frontend decoder qualified all 83 freshly read retail source reports (258,065 events). Fresh browsers passed complete and partial carriers, hidden unsupported actions, pagination/filtering, exact metadata download, pending close and wide/narrow layouts, with no page errors; final screenshots inspected. HTTP exact-field, stale-key/hash and unsupported carrier checks rejected before mutation. Project/history/files and reference fixture were unchanged. Normal native Build before/after inspection was byte-identical (SHA-256 `1e358a48f13f35757fb08a06fd2550b74e5957cf94495ce45fca5c0b75aa6eec`). Private proof: `local-output/sdk-20260909/audio-sequence-20261006/proof.json`, `retail-sequences.json`, `all-source-node.json` and focused logs. No game launch, runtime attachment, installation or full-disc export; gameplay remains deferred and the full SDK goal stays active.

Supported source audio records now offer **Inspect sequence events**. The read-only inspector shows bounded ordered channel/meta instructions, source byte ranges, encoded operands, running-status use, cumulative ticks and timing integrated from declared SEQ tempo. Kind/channel/search filters, 128-row pagination and complete metadata download work on complete or explicitly partial sequences. Missing sequence carriers expose no action. Source changes withdraw displayed events; close/late-response ownership prevents stale publication. The source-qualified HTTP reader requires exact request fields, the current project scene source key and the original physical entry hash, freshly verifies imported/disc provenance and reads only that entry's supported sequence carrier.

The pinned Andrew SEQ parser supplies format evidence for VLQ/running status and fixed-size tempo/end-of-track meta events. Unlike its synthesized termination on unknown system/meta events, this SDK stops at the unresolved source offset and labels the decoded prefix partial without inventing end-of-track. Across all 83 supported retail carriers, 82 reached encoded end-of-track and PROT 1045 stopped at a non-seven-bit channel operand; 258,065 events were decoded, with at most 6,451 in one source. These are source syntax/timing facts, not waveform validity, audible duration, looping, scene assignment or runtime cadence. Waveform synthesis, playback and audio authoring remain incomplete.

`audio_sequence_authoring.py` is a pure native SEQ/carrier codec. It qualifies Retail/Current hashes and decoded source event identity, permits only fixed-width reached channel/tempo operands, preserves opaque and nonsequence bytes, and checks output by decoding again. `sdk/audio_authoring.py` now owns source-qualified audio overrides, detached review, atomic commands and native Build composition; project lifecycle, export/copy snapshots and Build keys validate that collection. Browser editing controls remain pending. See [SEQ operand groundwork](legaia-audio-sequence-authoring.md).
