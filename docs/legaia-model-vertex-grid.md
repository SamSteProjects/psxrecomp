# Snap selected model vertices to a native grid

Open a model's **Move vertices in 3D** editor and choose **Selected vertex group**. Enter or pick the object-local indices, choose **Grid spacing** and the X/Y/Z checkboxes, then choose **Stage group grid snap**. Grid coordinates are relative to the object-local origin and use native source units. Positive source Y points down.

The nearest grid multiple is used; exact halfway cases round away from zero. For example, at spacing 16, `-8` becomes `-16` and `8` becomes `16`. Spacing is an integer from 1 through 32768. If any selected coordinate would exceed signed16, the whole operation is rejected. Values are never clamped. Unselected axes and vertices, stored normals, topology, materials and other objects remain unchanged.

Staging is local. Compare Draft, Current and Retail, optionally choose **Inspect movement draft in scene**, then return to the movement editor. **Apply vertex group grid snap** publishes one model replacement/history step. Discard restores Current; Undo/Redo and Save/Open use the existing project workflow. An already snapped group is a no-op. The existing drag **Snap** control continues to quantize movement steps separately.

The API operation is `vertex_grid`, with exact values `indices`, `axes` and `spacing`; Apply uses `/api/model-vertices-grid` with the inspected Current SHA256. The importer reuses the qualified native vector writer and audits the final candidate against the retail binding. Grid snapping is authoring geometry; it does not change actor placement, skeleton pose or runtime grid behavior.

## Acceptance

Focused checks cover signed halfway values, selected-axis/subset preservation, overflow, malformed/stale requests, no-op and atomic history. Actual editor and native package readback evidence is retained privately under `local-output/sdk-20260909/vertex-grid-20261006/`. Gameplay acceptance remains deferred.

Eight focused Python checks, the new Node grid check and existing movement-preview checks pass. An actual Town01 model workflow stages indices `[0,1,2]` on X/Z at spacing16, compares Draft/Current/Retail, reviews the scene and returns, applies once, checks no-op, uses Undo/Redo and reopens the saved project. Wide/narrow display was inspected. The scene toolbar now recognizes grid values rather than expecting a translation offset.

The native model SHA256 is `7508d0da0666dfc7c76901db77b414849ec009710aa05304f4da913f9667cdfe`; package SHA256 is `c171e5e2a8a1e5a2c4c65595785f3b8a17e050e3e10ced471522e07663c6ee9d`. Full decoded-container equality was checked from both generated output and the package ZIP, with only model byte positions1520,1528 and1532 changing. Normals, opaque padding, packets and all other rows/objects remain exact. No game, installation or full-disc export ran.
