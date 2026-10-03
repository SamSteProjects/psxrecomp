# Export a source world kingdom

The **World ground** inspector can export a supported walk kingdom as a static GLB. Inspect **map01**, **map02**, or **map03**, then choose **Export source scene GLB**. With **Source model placements** enabled, this includes the whole source ground and qualified sparse model instances. With placements disabled, it exports only the ground. Select a source hierarchy entity and choose **Export selected GLB** to export that ground or model instance at its existing world position.

The browser downloads the GLB, and the SDK stores the same audited GLB under the current project's `Exports/` folder. Export does not edit the project, add history, change authored geometry, or launch the game. A stale source key disables export until the current kingdom is inspected again. Closing a pending inspector withdraws its browser action and prevents a late download.

Import the downloaded GLB into Blender or another glTF viewer for inspection. Repeated source models share meshes while retaining separate entity transforms and source metadata. Selected exports retain their original world transform; they are not moved to the origin. Source units are retained, with no evidenced conversion to physical meters. Blender edits do not enter the SDK through this inspection export workflow.

## What the file represents

Ground comes from the source kingdom MAP, its qualified MAN floor lookup, and its TIM atlas. Sparse objects use the source placement graph and model pool. Their transforms are source spawn seeds: scripts, animation, runtime visibility, and eventual resting positions are not evaluated. The export is the supported walk kingdom graph, not an overview-world-map reconstruction or a captured running-game scene. Menu landmark X/Y is unrelated to these 3D positions.

Vertices receive one source-Y-down to glTF-Y-up reflection, with reversed triangle winding. Instance matrices preserve source rotation and translation without applying a second reflection. Embedded PNGs use the qualified texture crops; RGB modulation, UVs, material selectors, and source IDs follow the existing scene exporter. Missing or unsupported texture associations retain its vertex-color fallback. Crop images can repeat across different source materials. PSX semitransparent blending and runtime palette changes are not reconstructed.

Each GLB retains source graph confidence, MAP/container hashes and spans, texture/model provenance, coverage, and limitations in glTF extras and its audit. Scope may be `source-scene`, `ground`, or `selected`. Bounds, canonical identities, matrix/source-position agreement, coverage, imported-disc identity, and current project state are checked before private export writes. The download budget is 32 MiB; the API response budget is 64 MiB. No disc image is written.

## Verification

Private evidence is under `local-output/sdk-20260909/worldmap-glb-20261002/research/`. `prepare.py` independently parses GLB accessors, root matrices, PNG chunks/pixels, and material metadata for all three kingdoms. It checks every exported world-space corner against its source graph, triangle winding, shared meshes, stored float32 colors and UVs, original selected transforms, and source confidence. Full scene, ground, selected ground, and selected seed exports all pass. The saved project, selection, and Undo/Redo state remain unchanged; only derived export files are created.

| Kingdom | Full GLB bytes | Entity roots | Source geometries | glTF meshes | Embedded PNGs | World corners checked |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| map01 | 4,041,148 | 302 | 27 | 28 | 60 | 113,118 |
| map02 | 3,933,244 | 273 | 23 | 25 | 43 | 113,337 |
| map03 | 3,988,212 | 237 | 27 | 41 | 58 | 114,024 |

Actual installed Blender 5.2.2 LTS imported the complete map01 GLB. Its 302 entity roots contain 303 mesh objects sharing 28 mesh datablocks, 67 materials, and 60 images. Every local triangle matches the GLB, all packed PNG bytes match, and source confidence metadata survives. The maximum observed world-coordinate difference is 0.0009765625 source units from Blender floating-point transforms. The background Blender command completed and exited with code 0; no game ran.

Four focused permanent tests cover nonidentity yaw and Y translation with one reflection, shared geometry, colors/UVs/provenance, selected and ground scopes, invalid matrix/identity/range/confidence/counts, private export equality, wrong imported-disc identity, and stale source checks before loading and after encoding. Parent integration passed 16 focused Python cases, three Node suites, nine actual browser scenarios, and five independent download comparisons. Browser checks cover all three full kingdoms, selected seed, ground-only mode, 540px layout, pending-close withdrawal, stale-key disabling, and unchanged saved authored files. Download bytes, stored file bytes, Base64, and audit SHA256 agree. Gameplay verification remains deferred.
