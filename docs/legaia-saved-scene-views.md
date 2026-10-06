# Saved scene views

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
