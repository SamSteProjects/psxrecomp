# Saved scene views

## Hierarchy inspection state — 2026-10-07

New saved views also retain the typed hierarchy query and collapsed groups. Recall restores search and folds with the existing camera/display state. Matching groups temporarily expand while searching; clearing the search reveals the recalled folds. Legacy views omit this optional field and preserve their previous behavior. See [workflow and acceptance](legaia-hierarchy-views.md).

## Frame the isolated group — 2026-10-06

After isolating a selection, use **Frame isolated** to fit its visible mesh bounds. Camera angles and Perspective/orthographic mode stay as selected; viewport aspect, current transforms and near-plane depth are included. Hidden layers are skipped. If every isolated member is hidden by its layer, framing is disabled. Restore the layer to frame again. Save the result through **Saved scene views** to retain that camera. Framing changes only the editor camera.

Perspective, Front, Side and narrow viewport checks passed against every projected mesh corner. Layer visibility and the captured group remained unchanged; saved camera recall, NPC unavailable-view recovery and portable Open passed. Native Build output stayed identical. Inspected wide/narrow screenshots and proof: `local-output/sdk-20260909/scene-isolation-framing-20261006/final/`. No gameplay verification was performed.


## NPC visibility and deletion — 2026-10-06

NPC drafts now participate in saved isolated groups, single-instance isolation and manual hidden-instance views. Use **Authored scene**; retail-only views cannot retain authored NPC visibility. Save/Replace require a currently available draft belonging to the saved scene. Mixed static decoration views still bind their exact source MAP. These bookmarks retain editor visibility only; NPC placement, models and game behavior are unchanged.

Deleting a referenced draft withdraws active isolation and disables Recall for any saved view whose hidden or isolated NPC is missing. The dialog shows the missing count and recovery note. The project still opens with the unavailable view metadata, which can be renamed or deleted. Restoring the original draft with Undo, when history is available, restores recall. Undo history is not retained by Open. To replace an unavailable view, prepare a new current display first; use **Show hidden** to clear deleted draft IDs from manual visibility if necessary, then **Replace with current view**. Recall checks missing drafts before changing scenes or display, and validates current membership/renderability before applying a view.

Thirteen focused Python checks, Node guards and the final retail-source browser passed single/mixed/hidden NPC Save/Recall, deletion rejection, unchanged display during unavailable review, Undo recovery, portable Open of missing and restored snapshots, and unchanged normal Build output. Evidence: `local-output/sdk-20260909/scene-npc-visibility-20261006/final/proof.json`. This supersedes the saved-NPC exclusions in the older milestones below. No game was launched.


## Selection groups — 2026-10-06

Select actors with Ctrl/Command in the Hierarchy, select a scenery group, or use **Select scene placements** for a mixed group. **Isolate selection (N)** shows the captured group of up to 128 visible, renderable instances. **Restore scene** removes isolation while preserving the camera, hidden instances and layer switches. A hidden or unrenderable member disables the action. Temporary groups can include NPC drafts. Selection changes do not replace an active isolation; Restore before choosing a different group. Current source/scene changes withdraw the group.

Save the isolated group through **Saved scene views** to recall the same actor/decorative visibility later. Group bookmarks retain sorted unique `isolated_entity_ids`, while existing single-instance views retain `isolated_entity_id`. These mutually exclusive forms have the same source membership, static MAP and renderability guards. Save, Replace, Undo/Redo and portable Open preserve group metadata. Saved visibility continues to exclude NPC drafts and model filters; no actor placement or game data is changed by isolation or view metadata.

Eleven focused Python checks, Node guards and actual retail-source browser isolation/Restore/save/recall/history checks passed. The browser also rejected a hidden group member and withdrew isolation after a private actor transform change; Undo restored the original authored data. Complete native Build output was unchanged by the saved view. Screenshot inspected; no page errors. Evidence: `local-output/sdk-20260909/scene-group-isolation-20261006/final/proof.json`. No game was launched.


## Selected instance isolation

**Isolate selected** temporarily shows one supported selected mesh instance.
Isolation remains pinned to that instance until **Restore scene**, so surrounding
walls/ground cannot obscure Front or Side inspection. The existing **Focus**
button frames it. Isolation preserves manual hidden objects and scene layer
switches; restoring it does not force previously hidden objects visible.
Project/scene/source/representation changes and scene proposals withdraw the
isolation. Toggling isolation authors no model/component/history state. New saved
views can retain isolation as editor display metadata, alongside manual visibility.

## Axis views - 2026-10-04

The scene toolbar has **Top (X/Z)**, **Front (X/Y)** and **Side (Z/Y)**.
All three use orthographic projection and preserve the camera target and scale.
Front looks along -Z with +X right and +Y up; Side looks along -X with +Z left
and +Y up. These axes describe editor display coordinates. They do not infer
unknown retail actor heights or establish runtime placement.

Right-drag pans on the camera plane, including display Y in Front/Side. Scroll
keeps the point under the cursor fixed on that plane. Both are camera operations;
no actor/scenery components are authored. Front and Side use exactly zero pitch,
which saved views now validate and persist. Perspective retains its .12-radian
minimum, including when switching from a level orthographic camera. Orbiting and
existing source-bound saved view/history behavior remain available.


In Edit mode, open **Saved scene views** beside the scene selection tools.
Name and save the current camera. **Recall scene view** opens its imported scene
and restores projection, camera target/orbit/distance, authored or retail
representation, the Actors/Scenery/Ground toggles, grid and source-bound manual
visibility/isolation in new views. Recall creates no
history command and changes no actor components.

Names are unique within a scene. Rename, replace with the current view and
delete each make one Undo/Redo entry. Use **Save project** to retain views
across sessions; projects can hold up to 128 views. Replacing a camera requires
its scene to be active. A saved view retains the imported scene hash, so
changed-source reimport rejects while a bound view or its history remains.

Camera targets are editor display coordinates, including display height.
They do not establish retail Y, collision height, facing or live actor identity.
Visibility supports imported actors, authored NPC drafts, static decorations and ground. Hidden IDs are
unique and canonically sorted (up to 32768); an isolated target must not be manually
hidden. Environment visibility retains its source MAP hash, with fresh native static
cell verification on Save/Replace and current preview membership/renderability/hash
checks on Recall. Portable Open validates metadata without requiring a disc. Old views
without optional visibility/grid fields retain their former recall behavior.
Model filters, selected actors, proposal previews and runtime
observations are not captured. Live mode and active pose/group/collision proposal
inspections disable the tool. Closed or changed recall context withdraws camera
application; stale view reviews reject.

Validation on 2026-10-01: 14 focused Python/HTTP checks, Node source/display
validation and module syntax passed. Retail-source headless browser checked
camera/representation/layer recall, cross-scene navigation, metadata CRUD/history
and unchanged actor data with no page errors. No game was launched. Its Python services and Node guard checks are included in the integrated
463-test checkpoint on source `2ca0a1a4`; browser evidence remains separate.
Gameplay verification remains deferred.

Axis-view validation: six focused Python project checks and two Node checks;
private Town01 headless browser GPU picks, Front/Side pan, cursor-anchored zoom,
source/game-state preservation, saved recall, Undo/Redo and Save/reopen passed.
Evidence: `local-output/sdk-20260909/scene-axis-views-20261004/integer-cursor/proof.json`.
No game launched; runtime/gameplay acceptance remains separate.

Selected-instance isolation and manual-hidden restoration passed in the same
private browser project, including immediate availability after entity selection
and representation-key withdrawal. `isolation-proof.json` records the checks;
focused Front/Side screenshots were inspected. Model/history/dirty/source state
remained unchanged, with no browser errors or game launch.

Visibility/grid validation — 2026-10-05: nine focused Python cases, scene-view/camera
Node suites and both module syntax checks pass. Private retail Town01 browser saves a
hidden imported actor and isolated static decoration, recalls camera/grid/isolation,
preserves hiding on Restore, and checks metadata Undo/Redo plus Save/Open. Retail to
Authored preview reload retains recalled isolation at 540px. Screenshot inspected;
no page errors or changes to imported/authored game data and Build/preview keys.
Evidence: `local-output/sdk-20260909/saved-scene-visibility-20261005/proof.json`.
No package, game, installation or full-disc export ran. Full SDK/runtime acceptance
remains incomplete and gameplay verification stays deferred.

## Saved View Metadata Transfer

In **Scene tools → Saved scene views**, select a saved view from the active scene and choose **Export selected view JSON**. The file carries the source view ID/name, exact imported scene digest and supported camera, representation, layers, grid, hierarchy and visibility metadata. It contains no project root path or native game payload. Export uses the current saved snapshot and an 8 MiB serialized-file budget.

Choose **Import scene view JSON** to inspect a detached file recipe. Import requires the same qualified active scene source and supported display/visibility identities. A distinct copy name is suggested and can be edited. **Import as new saved view** revalidates the recipe against current state, then uses the existing `create_scene_view` command. The new UUID is selected; the source view is preserved. Duplicate names, foreign scene/import hashes, unsupported fields, invalid cameras and unresolved visibility members refuse. New views count toward the normal 128-view budget. Recall remains the existing editor display action.

File reads and commands respect Edit/busy/project context. Closing or reopening invalidates pending file reads; a late read cannot publish into the new dialog. Source changes disable an incompatible pending recipe. Import uses shared dirty tracking, Save/Open, change review and one-step Undo/Redo. Native scene/actor content and Build inputs are unaffected. Original transfer files remain user-managed metadata; import stores the qualified view recipe in the project rather than a retained native asset input.

Offline checks passed on 2026-10-08: thirteen existing saved-view Python cases, two Node transfer/view suites and JS syntax passed. The new contract checks detached exact transfer metadata, source/scene binding, unique-name/new-identity commands and malformed/forged/bounds refusals. A private Town01 browser exported actual metadata, refused a foreign import digest, closed during a delayed file read, reopened safely, imported the exact recipe with a distinct selected UUID and completed Save/independent Open and Undo/Redo. The native Build input key and complete actor state stayed unchanged. Wide/400 px screenshots were inspected, with no page errors. Original private document/history/imports/database/files were restored with two legitimate Redo entries and helpers closed.

Evidence: `local-output/sdk-20260909/scene-view-transfer-20261008/`. Initial harness navigation used a collapsed Scene tools drawer, and a later file-selection step ran before the reopened dialog became visible. The harness now opens the drawer and waits for the live controls; the passing run also verifies cancellation/reopen. No package Build, native recompilation, game or runtime attachment ran. This editor metadata transfer requires no gameplay verification; full SDK development continues solo.
## Complete Selection Visibility — 2026-10-08

**Hide selected** applies to the complete selected actor, NPC draft, scenery or mixed placement group. The button reports the number of selected members. If some members are visible and others manually hidden, clicking hides all members together; when all are manually hidden, **Show selected** clears their manual hiding together. Single-placement selection keeps the same toggle behavior.

These actions affect temporary viewport visibility. They preserve placement selection, active focus, camera, scene layers, isolation and authored data. A hidden layer or an active isolation can still conceal a member after manual hiding is cleared. **Show hidden** clears all manual hiding as before. Exports continue to include selected members regardless of temporary hiding.

The complete selection must resolve uniquely in the current scene; missing, duplicate or oversized membership is refused without partially changing visibility. Busy requests disable the actions and their handlers refuse invocation until completion. Existing saved scene views retain the resulting manual visibility through their source-bound capture/recall workflow.

Offline checks passed: an actual Dolk2 four-member actor/NPC/scenery group exercised partial hiding, complete hide/show, unchanged selection and camera/layers/isolation, Show hidden, busy refusal/recovery and injected invalid-membership refusal. Full imports/authored data/history/Build identity stayed exact with zero authoring commands. Saved-view and hierarchy Node suites plus syntax/diff checks passed. Private evidence: `local-output/sdk-20260909/selected-group-visibility-20261008/`. No game or runtime attachment ran; gameplay remains deferred.
