# Saved scene views

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
Visibility supports imported actors, static decorations and ground. Hidden IDs are
unique and canonically sorted (up to 32768); an isolated target must not be manually
hidden. Environment visibility retains its source MAP hash, with fresh native static
cell verification on Save/Replace and current preview membership/renderability/hash
checks on Recall. Portable Open validates metadata without requiring a disc. Old views
without optional visibility/grid fields retain their former recall behavior.
Model filters, selected actors, new NPC draft visibility, proposal previews and runtime
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
