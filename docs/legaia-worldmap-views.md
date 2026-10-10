# Saved World Inspection Views

In **World ground**, inspect a kingdom and open **Saved world views**. Enter a name and choose **Save world view** to retain the camera, Retail/Current layer, model display, instance scope, selected source entity and wireframe display. Creating a view selects its new entry. **Rename**, **Replace**, **Recall** and **Delete** operate on that selection. Views are listed for the loaded kingdom.

Recall freshly qualifies the native kingdom, selected entity, asset and complete source instance membership before restoring the display. A Current view also requires qualified imported-disc placement context. A changed source, stale project/view key, missing instance or changed display during qualification refuses recall. Loading the requested layer must succeed before the saved camera and selection are applied. This does not restore a historical authored placement snapshot: Current uses the project's current authored placements.

Views use the existing project saved-view collection, typed commands, dirty tracking, Undo/Redo and Save/Open. The shared limit is 128 field and World views. Each World record is bounded to 128 KiB, with a 16 KiB source record and at most 512 asset instance identities. Rename and Delete require Edit mode but can work without the disc. Retail views can be created in disc-backed empty projects. Field saved-view lists and counts exclude World records, and field commands reject them.

These are editor display settings. They do not change imported provenance, authored native transforms, Build inputs, export scope or runtime state. Source spawn seeds do not establish runtime visibility or resting positions.

## Offline Checks — 2026-10-09

Seventeen focused Python checks cover World metadata commands and existing field views: fresh source/ownership binding, finite bounded display values, no-op history, duplicate names, stale keys, changed membership, Current import prerequisites, offline Rename/Delete, Undo/Redo and Save/Open. The native review decoder passes all three kingdom reports and rejects sixteen forged variants per report; recalled display data is detached. Existing field visibility/group/NPC decoder checks, four JavaScript syntax checks and four SDK Python AST checks pass.

Actual muted editor browser workflows verify three native kingdoms with asset groups of 126, 138 and 109 instances. Save, Rename, Replace, exact camera/selection/group/layer/wireframe Recall, Undo/Redo, stale-source HTTP refusal and recall after Save/Open pass. The field view list remains empty while three World records persist. A final browser smoke verifies automatic selection of a newly created second view, Delete restoring the previous choice, and fresh Recall. No page errors occurred. Desktop and 400px saved-view layouts were inspected.

Private evidence: `local-output/sdk-20260909/worldmap-views-20261009/`. Only saved-view document metadata changes; all other fixture files and the full project document excluding saved views match the baseline. Imported/authored inputs and same-root authored Build identity remain unchanged. No Build, game launch, runtime attachment, installation or disc export occurred. Gameplay verification remains deferred and the full SDK goal remains active.
