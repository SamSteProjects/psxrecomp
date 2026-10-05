# Model vertex movement viewport

In Edit model vectors, select an existing vertex and choose **Move inspected vertex
in 3D**. The viewport shows object-local geometry with a wireframe overlay. Move
the X/Y/Z handles, or type three signed16 coordinates. Positive source Y points
down in the display. Snap steps are 1, 16 and 64 source units. Frame object changes
only the camera. Retail/Current/Draft switches between imported geometry, inspected
authored geometry and the local vertex draft. Retail uses original topology and
disables picking/handles; this viewport does not reconstruct Retail lighting or
texture residency. Reset draft vertex to Retail copies the original row into a
local draft and still requires Apply. Appended rows/objects have no Retail reset.

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


## Retained editing and history - 2026-10-05

Apply now keeps the workspace open and reloads a qualified Current source. The
camera and selected row remain when available. Edit another vertex in the same
session. Undo project change and Redo project change use ordinary project history;
discard a dirty or invalid draft first. Ctrl-Z/Shift-Ctrl-Z also works outside text
inputs. Text inputs retain their native text undo. History can include other project
changes; it is not a private per-vertex history.

Publishing requires the same project/scene/mode. A fresh source report is required
before continued editing. If publishing succeeds but refresh fails, the tool clears
stale geometry and disables editing/history; Close and reopen to recover. The backend
change remains published and available through normal project history. Missing initial
vertex rows reject; selection after history navigation remains within the fresh tables.

Two native retained edits changed object0 vertex0 to352/-32/241 and vertex1 to368/0/145.
Button/keyboard Undo/Redo, camera retention, fresh source, draft locks, two history
steps and Save/Open passed. Full native section reconstruction and normal Build/ZIP
readback change only model bytes1516/1524. Injected refresh failure blocked editing;
Close/reopen recovered and Redo restored the final source. Final recovery check and
screenshots are private: `local-output/sdk-20260909/vertex-session-final-20261005/`.
No game was launched; appearance remains in the manual queue.


## Move an entire object - 2026-10-05

Choose Entire object in Scope. XYZ inputs become offsets from the qualified Current
object; the handles originate at its bounds centre. Every owned vertex, including
hidden/unreferenced rows, moves together. No actor transform, pose channel, normals
or topology changes. The signed16 offsets and each resulting signed16 vertex are
validated locally and again by the normal project command. Apply object translation
publishes one history step, keeps the workspace open and resets offsets to zero
against refreshed Current. Discard before changing scope/object or using history.
Current comparison hides the handles; Draft shows the translated mesh and markers.

Native Town01 model0000 object0 was translated by208/-16/32 across all50 vertices.
The editor/history/Save/Open workflow passed. The edit needed17 extra compressed
bytes, so normal Build now uses qualified pack relocation for this capacity case.
Other qualification errors do not trigger fallback, and fitting content still uses
fixed-span overlays. Source-bound model/pack provenance remains required. Independent
full-section Build/ZIP and native logical/raw-sector readback passed. Evidence is
private: `local-output/sdk-20260909/object-move-20261005/`. Gameplay remains deferred.


## Inspect an object draft in the placed scene - 2026-10-05

In Entire object scope, enter or drag a valid nonzero offset, choose Scene instance
(or all supported model instances), then Inspect object draft in scene. A current
authored scene with a supported consumer is required. The raw local geometry draft
is checked against the normal native object proposal before requesting scene placement.
Imported/effective hashes, owner, bounds, all native geometry and material words stay
qualified; HTTP texture/blend display enrichment is handled separately. Placement
and supported pose are retained; this does not prove runtime residency or visibility.

Use Current/Proposed comparison and isolation in the scene workspace. Return to
movement draft and Restore scene preview both retain the draft and instance choice.
Apply remains explicit after returning. Closing the movement editor withdraws any
owned scene proposal. Changed scene/source/draft and late replies reject. Selected vertex scope now supports the same scene action, as described below. Native Town01 single/all-instance checks,
comparison, both returns, late changed-draft rejection and unchanged complete project/
history/assets passed with zero writes/page errors. Screenshots and evidence:
`local-output/sdk-20260909/movement-scene-final-check-20261005/`. No game was launched.


## Inspect a vertex draft in the placed scene - 2026-10-05

Selected vertex scope now supports Inspect movement draft in scene. Pick or choose
an existing object-local vertex, edit signed16 XYZ, and choose one supported scene
instance or all instances of the shared model. Preview and Apply share the same
candidate serializer; no mutation is implicit. A read-only raw vector review is
qualified against exact Current/Proposed geometry, native material words, bounds,
object, kind, row and XYZ before a source-qualified placed proposal is displayed.
The normal Return/Restore, Current/Proposed comparison and isolation controls apply.
Source placement and supported pose stay fixed; this does not prove game visibility.

API: /api/model-vector-preview takes asset_id, object_index, kind, vector_index,
values (signed16 XYZ) and expected_sha256. /api/model-vector-scene-preview adds
entity_id, source_key and optional boolean all_instances. Extra fields, stale source,
invalid owner/row/XYZ and non-Edit mode reject. Neither route creates authored files
or history. Existing /api/model-vector Apply remains the only vertex publication.

Native Town01 model0000 object0 vertex1 draft368/-16/32 passed both instance modes,
comparison, both return paths and changed-draft late-reply rejection with complete
project/history/assets unchanged. Normal Apply parity and retention of authored
face/topology content passed focused checks. Private native evidence and screenshots:
`local-output/sdk-20260909/vertex-scene-20261005/`. Gameplay remains deferred.


## Retail comparison and vertex reset in the movement workspace - 2026-10-05

Move model geometry now offers Retail, Current and Draft layers. Retail loads the
independently decoded imported geometry, including its original face topology;
Current retains all authored changes. Layer switching retains the local draft and
camera. Retail comparison hides handles and disables picking. Original object-local
row identity is retained; appended vectors and copied objects have no Retail counterpart.

Reset draft vertex to Retail copies only that original signed16 XYZ into the local
draft. Explicit Apply uses the existing hash-qualified vector command and creates
one ordinary history step. Whole-object reset is unavailable. Source qualification
rejects malformed coordinates, ownership and face ranges; baseline reads write no
project/history/authored files. Added source data remains under the existing response
budget.

Native Town01 model0000 object0 vertex0 reset from Current352/-32/241 to
Retail320/-32/241 passed comparison, draft retention/locks, Apply, refreshed baseline,
Undo/Redo and Save/Open. The complete project document and authored files were
unchanged before Apply; only that vector changed, with vertex1's authored368/0/145
retained. Zero page errors and game launches. Screenshots inspected. Focused source
HTTP/history and JavaScript baseline/ownership/malformed-data checks passed.
Evidence: `local-output/sdk-20260909/retail-movement-20261005/proof.json`.
No new gameplay verification gate or package is required for this editor workflow;
in-game appearance remains on the existing manual queue. The SDK goal stays active.
