# Model vertex movement viewport

In Edit model vectors, select an existing vertex and choose **Move inspected vertex
in 3D**. The viewport shows object-local geometry with a wireframe overlay. Move
the X/Y/Z handles, or type three signed16 coordinates. Positive source Y points
down in the display. Snap steps are 1, 16 and 64 source units. Frame object changes
only the camera. Current/Draft switches between inspected geometry and the local
vertex draft; this viewport does not reconstruct Retail lighting or texture residency.

Only the selected native vertex row changes. Normals, topology, other vectors and
other objects stay fixed. A dirty or invalid draft locks object/index selection
until Discard. Current comparison hides the movement handles. Escape cancels an
unfinished drag; camera, viewport, focus and source-context changes also cancel it.
Apply vertex draft uses the ordinary model-vector command with the inspected native
hash and creates one Undo step. Source changes withdraw the editor; pending requests
disable its controls. Closing releases the renderer, resize observer and gizmo
listeners. Save/Open and normal Build retain the existing model override pipeline.

The source uses the existing qualified vector-table inspection API, including
native object/vector ownership and stable face coverage. No pose, animation channel,
new geometry or new vertex identity is created. Unsupported native layouts reject.

Native validation on 2026-10-05: `asset://town01/models/scene-tmd/0000`, object0,
vertex0 moved from `[320,-32,241]` to `[464,-32,241]`. Styled editor checks passed
draft-only dragging, snap16, Escape, Current comparison, overflow rejection and one
Apply, with zero page errors. Screenshot inspected. Source JSON qualification and
seven focused Python model/vector/Build checks passed. Save/Open and Undo/Redo passed.

Independent full-section reconstruction from the verified Retail disc equals both
normal Build directory and delivered ZIP payload readback. Exactly model byte1516
changed; all unrelated section bytes, vectors, normals and topology are preserved.
The early harness compared an updated source hash with its old value, then attempted
to parse compressed section overlays as full PROT entries; corrected native readback
uses the actual compressed model section and verifies its complete bytes.

Private evidence: `local-output/sdk-20260909/vertex-move-20261005/proof.json`.
No game was launched or output installed; in-game model appearance remains deferred.


## Direct viewport selection - 2026-10-05

Move vertices in3D also opens directly from the model shape panel. With Pick vertices
enabled, click a projected point to select its existing object-local row. The query
uses a10-pixel radius, choosing nearest screen position, then frontmost projected
depth and lowest row index for ties. It includes hidden vertices; orbit to separate
coincident points. An orbit drag never selects. Dirty or invalid drafts block another
selection until Discard; numeric object/index selection remains available.

The point overlay is transparent over the geometry. It draws at most1024 projected
rows plus the selected row, and reports how many points were drawn. Picking considers
all qualified projected rows, including rows outside this drawing cap. Current and
Draft comparison and the existing source-hash guarded Apply path remain available.

A native Town01 model0000 workflow selected exact vertices1 and2 in both Draft and
Current layers. Dirty/invalid locks, pick toggle, orbit exclusion and close cleanup
passed. Complete project document/history unchanged, zero authoring requests or browser
errors. The first screenshot exposed an opaque overlay hiding the geometry; the final
run fixes it and its screenshot was inspected. Pure screen/depth/index/bound checks
passed. Evidence: `local-output/sdk-20260909/vertex-picking-final-20261005/proof.json`.
No game was launched; no additional gameplay acceptance is needed for point selection.
