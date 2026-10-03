# Imported model texture-binding picker

In Edit mode, open a model's material editor, choose the target object/group/primitive, and expand **Choose a binding from an imported model**. **Browse source models** queries the AssetDB membership of the verified active scene. Choose a model, then **Load current source bindings**. The picker identifies each qualified source object, group and primitive and displays the effective model hash. Loading changes no draft or authored state.

**Use selected source binding in draft** copies page column/row, texture depth and indexed CLUT column/row into the selected target's existing controls. Direct 16-bit bindings retain the target's CLUT word. Untextured and reserved-depth rows are unavailable. Target UVs, geometry, normals, packet layout, group ABE drafts, source ABR and reserved bits remain separate. The catalog permits 2048 scene models; a loaded model shows its first 2048 qualified textured rows and states the total. Other target bindings remain editable through the numeric controls.

Review, inspect Proposed, return, and explicitly Apply through the existing material workflow. Copying withdraws a prior review. Closing, changing project/scene/mode/source, or a delayed cancelled request cannot populate the editor. Apply uses the target model's existing replacement command; the donor is a source reference for choosing values, not a new runtime dependency or allocation. Ordinary Undo/Redo, Save/Open and Build remain available. All instances using the target model share its replacement.

A binding does not establish suitable target UV coverage, live VRAM residency, palette animation, texture windows or PSX blend appearance. Source ABR remains read-only. Review recomputes static pixel associations and reports missing/ambiguous matches. Gameplay checks remain deferred. See [source materials](legaia-model-materials.md).

## Offline evidence, 2026-10-02

Private fixture and scripts: `local-output/sdk-20260909/material-binding-picker-20261002/parent/`.

- Three Python catalog cases pass: read-only AssetDB/global membership, stale/live/unqualified/duplicate/budget rejection, and source drift withdrawal.
- The pure donor Node guards and existing material lifecycle suite pass, including indexed/direct copy, target group draft preservation, copied-review invalidation and delayed-close rejection.
- Seven actual browser checks pass: catalog/load without authoring, draft copy, normal Review, Proposed/Return, 540px layout, exactly one Apply, and Undo/Redo/Save/Reload/Build. A separate screenshot follow-up confirms corrected UTF-8 labels and no page/HTTP errors or game requests.
- Dolk2 model0133 object0/group4/primitive36 copies a binding from model0000: page column5→9, CLUT column15→0 and row481→490. Existing group ABE stays true. Independent word-mask construction matches the complete candidate TMD; only Current-to-Proposed bytes1102/1103/1106 change. Against Retail, the earlier group ABE byte1095 also differs.
- Complete normal Build carrier decompression/readback matches that candidate and preserves every neighboring decoded byte and its118461-byte compressed span. Imported metadata and retail bytes stay unchanged.

Candidate SHA256: `8b6c772cac8ab297b393a6df00ec156e0e45c45c75b638313de833c7af4b05da`.
Package SHA256: `a952ee4f6443068d63f8ddc5b6f636aa31168d3625851d01fcc6a14d0e8a89a3`.

The owned browser and loopback proof server are closed. No game, dependency install or disc export ran. This fixture demonstrates source-byte authoring and packaging; it does not assert visual suitability or native acceptance.
