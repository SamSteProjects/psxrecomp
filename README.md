# Legaia Trace SDK

**A local scene editor and authoring SDK for Legend of Legaia, built around PSXRecomp.**

Explore imported scenes, inspect models and scripts, edit supported game data, and build private mod packages with a record of the source bytes changed. The browser workspace brings scene previews, an asset database, project history, external asset interchange, and guarded runtime observation together.

This is the `legaia-sdk-integration` branch of PSXRecomp. The SDK lives in [`integrations/legaia`](integrations/legaia); the framework and native runtime remain part of this repository. For the underlying recompiler, see the [PSXRecomp framework README](README.psxrecomp.md).

[Get started](#get-started) · [Latest updates](#latest-updates--october-13-2026) · [Current SDK status](docs/SDK_CURRENT_STATUS.md) · [Editor guide](integrations/legaia/README.md)

## Latest updates — October 13, 2026

This publication includes SDK source through `14fa7e72d`. The new work expands battle, PLAYER, monster, field-equipment, and Art animation workflows while retaining the world-map authoring tools from the previous update.

- **Battle packs:** discover models and TIM atlases, inspect source textures and rigid reference poses, and export qualified models/clips. Supported model GLB, palette, and indexed PNG/STP changes use reviewed native authoring, retained original-input recovery, shared history, and private package delivery. Image-only and whole-texture restoration have distinct scopes.
- **PLAYER and field equipment:** inspect equipment assemblies, preview supported action frames, export selected equipment models/poses/clips, and author supported native model and action-channel data. Field variants have textured previews and idle/walk clip exports. Shared field TIM/PNG workflows preserve source layout and explicit STP handling.
- **Monsters:** inspect native archive models, palettes, stored motion frames, and records. Supported model GLB, palette/PNG, numeric motion, and motion GLB workflows retain original inputs and compose Current model, texture, and animation data through history and native package delivery. Cached playback and channel timelines expose source motion without asserting retail cadence.
- **Summons and battle effects:** a separate source inspector discovers 41 object-local models and 125 palette/page resources. Qualified GLB and PNG/STP downloads preserve source evidence; this lane is read-only and does not infer scene membership or runtime texture associations.
- **PLAYER Art animation:** inspect 109 logical records and 87 physical streams with explicit archive/equipment selection, cached frame playback, and native channel timelines. Qualified Retail/Current pose/clip export, reviewed numeric channel authoring, Current/Proposed comparison, persistence, and native data-package delivery are connected.
- **Art GLB import, in progress:** normal controls now support bounded uploads, explicit FPS, optional animation/node selection, validated Review, mandatory Proposed comparison, and one-step Apply. Historical input registration and exact-byte recovery are connected. Broader source/frame/part/close guards, authored geometry/reimport, and combined native delivery still need verification.

The [bounded battle verification campaign](docs/legaia-battle-sdk-verification-20261013.md) records 98 native checks across 60 modules, completion of the initial fixture-dependent cases, 48 selected client checks, and 435 editor syntax checks at the stated campaign revision. These are recorded offline results, not a fresh whole-SDK or runtime acceptance run for this publication. Later Art work has its own focused evidence and remaining checks.

See [current status](docs/SDK_CURRENT_STATUS.md), [status history](docs/SDK_STATUS.md), and the [gameplay verification queue](docs/legaia-gameplay-verification-queue.md) for scope and evidence. Source previews, private package bytes, and successful offline checks do not establish correct gameplay, native timing, or runtime residency. Later dated checkpoints supersede earlier unfinished-work notes.

## What you can do

| Workspace | Supported workflows |
| --- | --- |
| **Scenes and assets** | Inspect assembled field scenes, pick actors and scenery, search imported resources, and save scene views and actor selections. |
| **Actors and scenery** | Author supported placement and appearance fields, apply actor presets, and review scenery offsets and rotations with project history. |
| **Models and textures** | Preview source models; exchange supported model fields through GLB, TMD, OBJ, or JSON; edit textures through PNG; review proposed changes before applying them. |
| **Animation** | Preview supported actor clips and scene animations, edit existing rigid-object channels, and export full clips as GLB. |
| **Dialogue and scripts** | Inspect decoded source paths, edit supported dialogue and script operands, and navigate source references. |
| **Field and world maps** | Inspect collision, regions, and trigger cells; author supported world textures, models, and decorations; inspect source object binds/scripts/animation frames; export qualified Retail/Current/Proposed world scopes as GLB. |
| **Battle and motion** | Inspect and author qualified battle-pack, PLAYER, monster, and Art resources; preview source motion; recover retained inputs; export supported equipment, poses, and clips. |
| **Projects and packages** | Save and reopen authored projects, undo and redo edits, copy projects for experiments, review Build inputs, and generate audited `.psxmod` packages. |
| **Runtime observation** | Connect to a compatible runtime, inspect accepted position samples, and follow scene observations when identity and observation guards match. |

Support is qualified by source record and scene. The editor exposes unsupported or unresolved data instead of assuming that every resource can be edited or built.

## Get started

You need **Python 3.11 or newer**, a browser, and your own **North American SCUS-94254 Mode 2/2352 disc image** for retail import. Retail game assets and proprietary BIOS images are not included.

Clone this branch:

```powershell
git clone --branch legaia-sdk-integration --single-branch https://github.com/SamSteProjects/psxrecomp.git legaia-trace-sdk
cd legaia-trace-sdk
```

From the repository root, launch the editor:

```powershell
python integrations/legaia/tools/legaia_editor.py --project local-output/my-legaia-project
```

1. Open the loopback URL printed in the terminal, normally `http://127.0.0.1:4388`.
2. Import your disc image and choose `town01` or another supported scene.
3. Explore the hierarchy and viewport, select a resource, and inspect its retail and authored values.
4. Apply a supported edit and **Save**. Use **Review Build** to inspect supported inputs before producing a private package.

Keep projects and exports under the ignored `local-output/` directory. Reusing a project path reopens the saved project and validates its imported evidence. Launching the editor does not require a running game; runtime observation is an optional separate connection.

For package installation and runtime checks, read the [editor guide](integrations/legaia/README.md) and [release parity notes](docs/legaia-release-parity.md). Native framework setup is documented in the [framework README](README.psxrecomp.md) and [local codegen SDK guide](docs/LOCAL_CODEGEN_SDK.md).

## Documentation

| Topic | Guides |
| --- | --- |
| **Overview and progress** | [Current status](docs/SDK_CURRENT_STATUS.md), [status history](docs/SDK_STATUS.md), [editor guide](integrations/legaia/README.md), [feature matrix](docs/FEATURE_MATRIX.md) |
| **Scene workspace** | [Scene inspection](docs/legaia-sdk/scene-inspection.md), [project assets](docs/legaia-project-assets.md), [field source workspace](docs/legaia-field-source-workspace.md) |
| **Placement and scenery** | [Actor placement groups](docs/legaia-scene-placement-groups.md), [scenery rotation](docs/legaia-scenery-rotation-gizmo.md), [group rotation](docs/legaia-scenery-group-rotation.md) |
| **Models and textures** | [Model GLB editing](docs/legaia-model-glb.md), [source material bindings](docs/legaia-model-glb-materials.md), [texture PNG editing](docs/legaia-texture-png.md) |
| **Animation** | [Scene animation](docs/legaia-scene-animation.md), [animation GLB export](docs/legaia-animation-glb.md), [initial animation assignments](docs/legaia-initial-animation-assignment.md) |
| **Dialogue and scripts** | [Dialogue authoring](docs/legaia-sdk/dialogue-authoring.md), [script resources](docs/legaia-sdk/script-resources.md), [script operand files](docs/legaia-script-operand-files.md) |
| **World maps** | [Landmark authoring](docs/legaia-worldmap-authoring.md), [world geometry](docs/legaia-worldmap-geometry.md), [source placements](docs/legaia-worldmap-placements.md), [world GLB export](docs/legaia-worldmap-export.md) |
| **World asset authoring** | [World textures](docs/legaia-worldmap-texture-authoring.md), [World models](docs/legaia-worldmap-model-authoring.md), [decoration allocation and groups](docs/legaia-worldmap-placement-allocation.md) |
| **World source behavior** | [Project behavior resources](docs/legaia-worldmap-behavior-resources.md), [source object binds](docs/legaia-worldmap-object-bind.md), [interaction scripts](docs/legaia-worldmap-object-script.md), [animation frame preview](docs/legaia-worldmap-object-animation.md), [static footprints](docs/legaia-worldmap-footprint.md) |
| **Battle and equipment** | [Battle resources and authoring](docs/legaia-battle-character-resources.md), [pack reference poses](docs/legaia-battle-pack-reference-pose.md), [PLAYER assemblies](docs/legaia-player-battle-assembly.md), [PLAYER action GLB](docs/legaia-player-action-glb.md), [field equipment](docs/legaia-field-equipment-preview.md) |
| **Monster and source effects** | [Monster archive workflows](docs/legaia-monster-archive.md), [summon/effect sources](docs/legaia-battle-sideband.md), [shared field textures](docs/legaia-field-texture-authoring.md) |
| **Art animation and verification** | [PLAYER Art animation](docs/legaia-player-art-animation.md), [bounded battle verification](docs/legaia-battle-sdk-verification-20261013.md) |
| **Project management** | [Project settings](docs/legaia-project-settings.md), [editable project copies](docs/legaia-project-copies.md), [saved scene views](docs/legaia-saved-scene-views.md) |
| **Build and NPC candidates** | [Build review](docs/legaia-build-review.md), [build reports](docs/legaia-sdk/build-review.md), [NPC Build boundaries](docs/legaia-npc-build-candidates.md) |
| **Live observation** | [Live follow](docs/legaia-sdk/live-follow.md), [runtime node review](docs/legaia-runtime-node-review.md), [gameplay verification queue](docs/legaia-gameplay-verification-queue.md) |

## Current boundaries

The SDK is under active development. Source inspection, editor previews, package generation, and gameplay verification have separate evidence and limits; the [SDK status](docs/SDK_STATUS.md) records the detailed results.

- **Edits retain source ownership.** Imports, replacements, and supported allocations check source identities, editable fields, shared records, and native layout constraints. Arbitrary topology, headers, opaque bytes, or unsupported allocations remain rejected.
- **Build support depends on the authoring lane.** Some edits must fit their original compressed span; supported growth workflows use qualified relocation and native ownership checks. Donor-based NPC candidates can enter normal Build for qualified compressed MAN scenes that fit; streaming or oversized additions in that candidate lane remain rejected, and candidate features are disabled by default.
- **Behavior and motion remain source-qualified.** Script operands and animation authoring have record-specific bounds. Unknown instructions, missing binds, unsupported clips, conflicting owners, and unavailable capacity remain explicit. Source playback and authored channels do not prove native timing, runtime activation, or gameplay behavior.
- **Browser previews have limits.** Source placements can differ from script-adjusted runtime positions and visibility. Texture associations may be partial, and normal diagnostics do not reconstruct retail lighting.
- **Runtime observation is read-only.** A compatible runtime must satisfy identity, execution-witness, and scene guards. Editor observation routes do not write live RAM.
- **Art GLB delivery is still being qualified.** Upload/Review/Proposed/Apply controls have focused offline evidence; the broader guard, authored-geometry/reimport, and combined delivery campaign remains unfinished. This is bounded rigid-motion interchange, not arbitrary animation retargeting.
- **Gameplay acceptance remains explicit.** A successful export or Build does not establish correct spawning, scripts, collision, rendering, or behavior in the game. Follow the documented verification queue for those checks.

## PSXRecomp and provenance

Legaia Trace extends the PSXRecomp framework with local import, inspection, authoring, and package workflows. See the [framework overview](README.psxrecomp.md), [reverse-engineering provenance](docs/REVERSE_ENGINEERING_PROVENANCE.md), and [third-party attribution](THIRD_PARTY_ATTRIBUTION.md) for the underlying project and reference sources.

The SDK has no runtime dependency on Andrew's Legend of Legaia research repository. Source evidence, projects, game-derived exports, and private packages remain local to the user.

Repository licensing is recorded in [LICENSE](LICENSE); third-party notices are recorded separately in [THIRD_PARTY_ATTRIBUTION.md](THIRD_PARTY_ATTRIBUTION.md).
