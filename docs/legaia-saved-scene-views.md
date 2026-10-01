# Saved scene views

In Edit mode, open **Saved scene views** beside the scene selection tools.
Name and save the current camera. **Recall scene view** opens its imported scene
and restores projection, camera target/orbit/distance, authored or retail
representation, and the Actors/Scenery/Ground toggles. Recall creates no
history command and changes no actor components.

Names are unique within a scene. Rename, replace with the current view and
delete each make one Undo/Redo entry. Use **Save project** to retain views
across sessions; projects can hold up to 128 views. Replacing a camera requires
its scene to be active. A saved view retains the imported scene hash, so
changed-source reimport rejects while a bound view or its history remains.

Camera targets are editor display coordinates, including display height.
They do not establish retail Y, collision height, facing or live actor identity.
Individual hidden objects, model filters, selected actors, proposal previews
and runtime observations are not captured. Live mode and active pose/proposal
inspections disable the tool. Closed or changed recall context withdraws camera
application; stale view reviews reject.

Validation on 2026-10-01: 14 focused Python/HTTP checks, Node source/display
validation and module syntax passed. Retail-source headless browser checked
camera/representation/layer recall, cross-scene navigation, metadata CRUD/history
and unchanged actor data with no page errors. No game was launched. These checks
postdate the integrated 457-test checkpoint; gameplay verification remains
separate and deferred.
