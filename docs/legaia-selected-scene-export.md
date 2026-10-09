# Selected Scene GLB Export

Select an actor, NPC draft or scenery placement in the scene hierarchy, then use **Export selected GLB** in the scene tools. A single selection exports that placement. A placement group exports every selected member at its existing scene position, including temporarily hidden members. Shared geometry is retained once and referenced by each placement; the export does not recenter the group.

The private GLB is written to the project's `Exports` directory. The result dialog reports instance and geometry counts, the file path, source provenance and limitations. Group provenance records canonical stable placement identities in `selected_entity_ids`; each root node retains its source instance metadata and transform.

The endpoint uses the active imported scene and its current source key. Group selection is bounded to 2–128 unique identities. Missing, ambiguous, nonrenderable or geometry-unavailable members reject the complete export. Stale source keys, simultaneous single/group selectors, client geometry and arbitrary paths are refused. A late response cannot replace the result dialog after the scene or selected placement group changes.

Finish or discard active mesh and placement proposals before exporting. This is a static source-scene reference in source units. Runtime visibility, lighting, physical scale and gameplay behavior remain unverified. Exporting writes a private file without editing scene placements, imports, authoring history or Build identity; this workflow does not add scene GLB import or native animation support.

## Offline Verification — 2026-10-08

Three focused Python export tests cover full-scene and single-placement behavior plus complete-group membership, shared meshes, retained transforms, detached inputs and partial/ambiguous selection refusal. The actual Dolk2 editor probe selects two imported actors, an NPC draft and scenery, temporarily hides one selected member, exports through the normal button and independently reads the GLB roots and exact source-coordinate matrices. It checks shared geometry, six malformed/stale HTTP refusals, unchanged camera, zero authoring commands and exact imports/authored state/history/Build identity. JavaScript syntax and Python source checks also pass.

Private evidence is retained under `local-output/sdk-20260909/selected-group-glb-20261008/`. No game or runtime attachment ran. Manual gameplay verification remains deferred; the full SDK goal remains active.
