# Legaia Trace SDK

**A local scene editor and authoring SDK for Legend of Legaia, built around PSXRecomp.**

Explore imported scenes, inspect models and scripts, edit supported game data, and build private mod packages with a record of the source bytes changed. The browser workspace brings scene previews, an asset database, project history, external asset interchange, and guarded runtime observation together.

This is the `legaia-sdk-integration` branch of PSXRecomp. The SDK lives in [`integrations/legaia`](integrations/legaia); the framework and native runtime remain part of this repository. For the underlying recompiler, see the [PSXRecomp framework README](README.psxrecomp.md).

[Get started](#get-started) · [Editor guide](integrations/legaia/README.md) · [SDK status](docs/SDK_STATUS.md) · [Runtime verification queue](docs/legaia-gameplay-verification-queue.md)

## What you can do

| Workspace | Supported workflows |
| --- | --- |
| **Scenes and assets** | Inspect assembled field scenes, pick actors and scenery, search imported resources, and save scene views and actor selections. |
| **Actors and scenery** | Author supported placement and appearance fields, apply actor presets, and review scenery offsets and rotations with project history. |
| **Models and textures** | Preview source models; exchange supported model fields through GLB, TMD, OBJ, or JSON; edit textures through PNG; review proposed changes before applying them. |
| **Animation** | Preview supported actor clips and scene animations, edit existing rigid-object channels, and export full clips as GLB. |
| **Dialogue and scripts** | Inspect decoded source paths, edit supported dialogue and script operands, and navigate source references. |
| **Field and world maps** | Inspect collision, regions, and trigger cells; review world-map landmarks; explore kingdom ground and source model placements; export source world scenes as GLB. |
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
| **Overview and progress** | [Editor guide](integrations/legaia/README.md), [SDK status](docs/SDK_STATUS.md), [feature matrix](docs/FEATURE_MATRIX.md) |
| **Scene workspace** | [Scene inspection](docs/legaia-sdk/scene-inspection.md), [project assets](docs/legaia-project-assets.md), [field source workspace](docs/legaia-field-source-workspace.md) |
| **Placement and scenery** | [Actor placement groups](docs/legaia-scene-placement-groups.md), [scenery rotation](docs/legaia-scenery-rotation-gizmo.md), [group rotation](docs/legaia-scenery-group-rotation.md) |
| **Models and textures** | [Model GLB editing](docs/legaia-model-glb.md), [source material bindings](docs/legaia-model-glb-materials.md), [texture PNG editing](docs/legaia-texture-png.md) |
| **Animation** | [Scene animation](docs/legaia-scene-animation.md), [animation GLB export](docs/legaia-animation-glb.md), [initial animation assignments](docs/legaia-initial-animation-assignment.md) |
| **Dialogue and scripts** | [Dialogue authoring](docs/legaia-sdk/dialogue-authoring.md), [script resources](docs/legaia-sdk/script-resources.md), [script operand files](docs/legaia-script-operand-files.md) |
| **World maps** | [Landmark authoring](docs/legaia-worldmap-authoring.md), [world geometry](docs/legaia-worldmap-geometry.md), [source placements](docs/legaia-worldmap-placements.md), [world GLB export](docs/legaia-worldmap-export.md) |
| **Project management** | [Project settings](docs/legaia-project-settings.md), [editable project copies](docs/legaia-project-copies.md), [saved scene views](docs/legaia-saved-scene-views.md) |
| **Build and NPC candidates** | [Build review](docs/legaia-build-review.md), [build reports](docs/legaia-sdk/build-review.md), [NPC Build boundaries](docs/legaia-npc-build-candidates.md) |
| **Live observation** | [Live follow](docs/legaia-sdk/live-follow.md), [runtime node review](docs/legaia-runtime-node-review.md), [gameplay verification queue](docs/legaia-gameplay-verification-queue.md) |

## Current boundaries

The SDK is under active development. Source inspection, editor previews, package generation, and gameplay verification have separate evidence and limits; the [SDK status](docs/SDK_STATUS.md) records the detailed results.

- **Edits retain source ownership.** Imports and replacements check source identities, supported fields, shared records, and allocation constraints. Existing model topology and supported record layouts constrain interchange.
- **Build support depends on capacity.** Recompressed data must fit its qualified source span. Donor-based NPC candidates can enter normal Build for qualified compressed MAN scenes that fit; streaming or oversized additions are rejected, and candidate features are disabled by default.
- **Browser previews have limits.** Source placements can differ from script-adjusted runtime positions and visibility. Texture associations may be partial, and normal diagnostics do not reconstruct retail lighting.
- **Runtime observation is read-only.** A compatible runtime must satisfy identity, execution-witness, and scene guards. Editor observation routes do not write live RAM.
- **Gameplay acceptance remains explicit.** A successful export or Build does not establish correct spawning, scripts, collision, rendering, or behavior in the game. Follow the documented verification queue for those checks.

## PSXRecomp and provenance

Legaia Trace extends the PSXRecomp framework with local import, inspection, authoring, and package workflows. See the [framework overview](README.psxrecomp.md), [reverse-engineering provenance](docs/REVERSE_ENGINEERING_PROVENANCE.md), and [third-party attribution](THIRD_PARTY_ATTRIBUTION.md) for the underlying project and reference sources.

The SDK has no runtime dependency on Andrew's Legend of Legaia research repository. Source evidence, projects, game-derived exports, and private packages remain local to the user.

Repository licensing is recorded in [LICENSE](LICENSE); third-party notices are recorded separately in [THIRD_PARTY_ATTRIBUTION.md](THIRD_PARTY_ATTRIBUTION.md).
