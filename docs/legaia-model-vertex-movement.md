# Model vertex movement viewport

## Align model vertex groups to an explicit native coordinate (2026-10-06)

**Move model geometry → Selected vertex group → Plane: Source coordinate** exposes **Plane coordinate**. Enter a signed16 object-local word, then **Align group X/Y/Z** to stage the chosen coordinate on that source axis. Minimum, bounds-center and maximum planes retain their existing behavior. The local draft supports Discard, Current/Draft comparison, exact scene inspection and all-instance preview before explicit Apply. The coordinate field locks during a staged transform. Source Y remains positive down; this edits model words, not actor placement or scene/world coordinates.

The existing `vertex_alignment` request and Apply endpoint retain exact fields: `anchor` now accepts either `min`/`center`/`max` or an integer from -32768 through 32767. Boolean, float, null, numeric-string and out-of-range anchors reject; blank/fractional/out-of-range UI input cannot stage a draft. Only the selected axis of 1–4096 unique, owned Current object rows changes. Source qualification, ownership, fixed layout, opaque words, normals and topology use the existing native serializer. A coordinate already occupied by every selected row is a no-op with no new history.

Five focused Python alignment checks passed explicit extrema/zero coordinates, independent candidate bytes, malformed requests, stale hashes, atomic refusal, no-op/history and existing bounds-plane/allocated-row behavior. Three Node suites passed vertex movement/review contracts, custom coordinate bounds, grid and connectivity regressions. A fresh private muted headless editor proof passed invalid-input refusal, staging/Discard, exact scene proposal values, Current/Proposed and all-instance preview/return, Apply, no-op and Undo/Redo with no unhandled page errors; wide/400px screenshots were inspected. Expected refusal notifications came from the deliberately invalid inputs. Save/Open retained exact native model bytes, and other authored state remained unchanged.

Independent expected-model construction and full containing LZS-section readback matched package directory and ZIP. Native package SHA-256 `301ca75e55dccd77010d9bed088b623d2f6007a99f39f1c85e925da841491728`, Build `40ed615acb36a58c` passed integrity verification with gameplay acceptance false. Evidence: `local-output/sdk-20260909/vertex-coordinate-plane-20261006/pass1/` (`proof.json`, `browser-proof.json`, `browser.log`, `draft-wide.png`, `draft-narrow.png`, `scene.png`). The initial test fixture selected an already occupied zero plane; it was corrected to a distinct coordinate to test a real history change.

No game launch, attachment, mod installation or full-disc export occurred. Native appearance and placement acceptance remain deferred; the full SDK goal stays active and development remains solo.

## Distribute selected model vertices along a source axis — 2026-10-05

**Move model geometry → Selected vertex group → Distribute group X/Y/Z** stages even
spacing between the selected Current axis endpoints. Select 2–4096 unique object-local
rows. Ordering uses axis coordinate then native vertex index; integer spacing rounds
half steps toward the positive axis. Endpoints and other coordinates stay fixed.
Two rows or an already evenly spaced group produce no draft change. Normal words,
primitive topology, ownership and unselected rows remain unchanged; no normal or
collision recomputation is implied.

Distribution is a distinct SDK operation with exact `{indices, axis}` values and an
inspected Current model hash. The local draft locks conflicting selection/movement,
supports Discard and Retail/Current/Draft comparison, and reaches single/all-instance
Current/Proposed scene inspection with Return/Restore. The parent workspace qualifies
its full geometry and exact operation values and labels the distribution axis. Apply
uses the normal model override/history path; Save/Open and Build consume the result.

Validation: six focused Python distribution/alignment cases, expanded vertex-movement
Node checks and both changed editor-module syntax checks pass. Coverage includes signed
extremes, stable coordinate/index ties, stale/invalid requests, appended vector ownership,
immutable source, no-op and forged scene-review replies. Actual private Town01 browser
checks draft locks, no-op/Discard, Current/Draft, single/all-instance scene comparison,
Return/Restore, 540px Apply and Undo/Redo without page errors. Save/Open and normal Build
pass; complete decoded carrier readback in the package directory and ZIP preserves all
neighbors. This retail edit changes only model byte1524. Package SHA256:
`59be7c6edc144766f4d51844f08d7004e8085df59e557a4b1ab38a44807d1ca8`.
Evidence: `local-output/sdk-20260909/vertex-distribution-20261005/proof.json`.
No game, installation or full-disc export ran. Gameplay appearance remains deferred;
the full SDK goal stays active.

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

## Selected vertex group movement - 2026-10-05

Move model geometry now supports a selected group of 1..4096 unique existing
object-local vertex indices. Enter comma-separated indices or click points to
toggle membership before moving. XYZ handles and numeric signed16 offsets move
the group from Current, with a bounds-centred handle, snap and Escape cancellation.
Dirty/invalid offsets lock membership and history; Discard restores zero offsets.
Retail/Current/Draft layers retain the selection/draft. Unselected vertices,
other objects, normals, topology and material words remain unchanged.

The exact same qualified candidate drives read-only object/scene previews and
/api/model-vertices-translation Apply. Index ownership, uniqueness, source hashes,
scene keys, complete geometry and resulting signed16 bounds are checked. Apply
creates one project history step; zero offsets create none. One/all-instance scene
inspection retains the group on Return/Restore. No actor placement or pose edit.

Native Town01 model0000 object0 group[0,2] offset[16,-8,32] passed point toggling,
gizmo drag/Escape, invalid draft locks, scene Current/Proposed, all-instance mode,
Apply, Undo/Redo and Save/Open. Complete document/authored files unchanged before
Apply and throughout the separate interaction check. Full Retail-section directory
and ZIP readback matches the exact two-row candidate; only eight model bytes change.
Eight focused API/content/object/allocated-object checks and JavaScript guards pass.
Screenshots inspected; zero page errors/game launches. Private evidence:
`local-output/sdk-20260909/vertex-group-20261005/proof.json`.
Package SHA256: `bd600024ab3ef57fd9905667eeff3497125ae5700e5e278a01a3c6deddc85f4f`.
Game appearance remains deferred in the gameplay queue. The full SDK goal is active.

## Marquee selection for model vertex groups - 2026-10-05

In Selected vertex group scope, Shift-drag a rectangle to replace membership;
Ctrl+Shift-drag (or Meta+Shift) adds to it. The visible dashed overlay does not orbit
the camera. Selection uses all projected object-local rows, including hidden rows
and rows beyond the point-marker drawing cap. Reversed rectangles and viewport
clipping are supported. Empty/very small rectangles retain membership; exceeding
4096 unique vertices rejects without changing it. The group status shows a count.

Marquee selection is local and requires zero valid offsets, picking enabled and
Current/Draft geometry. Retail and dirty/invalid drafts cannot select. Controls and
handles lock during the gesture. Escape, pointer cancellation/capture loss, blur,
wheel input, viewport resize and changed source/draft/camera cancel without committing
membership. Source context and viewport dimensions are requalified before release.
Closing the workspace releases pointer capture and the blur listener.

Native Town01 model0000 selected the expected27 rows, passed additive membership,
Escape/blur/resize and Retail/dirty-draft guards, then applied X16 to exactly those
rows through the existing one-step group command. Other vertices, normals and
native topology stayed exact; Undo/Redo and Save/Open passed. Complete document and
authored files unchanged before Apply and in the final read-only visual check.
Changed draft cancels the live rectangle; overlay screenshot inspected. Pure checks
cover boundaries, reversed/clipped rectangles, hidden/deep rows, immutable inputs,
add/replace, uniqueness, drawing-cap independence and4096 overflow. Static module
routing was fixed after the initial native404; final native checks have zero errors.
Evidence: `local-output/sdk-20260909/vertex-marquee-final-20261005/proof.json`.
No Build/runtime behavior changes or game launches. Existing group movement output
remains on the deferred gameplay queue. The full SDK goal stays active.

## Reusable saved model vertex groups - 2026-10-05

Selected vertex group scope now has a project-local library: Save, Recall, Rename,
Update membership and Delete. Up to128 named groups retain stable UUIDs, model/scene
identity, object-local indices and source provenance. Names are unique per model.
Save/Open and project copy preserve them. Create/rename/update/delete use ordinary
project commands, dirty tracking and Undo/Redo; selection metadata never edits game
geometry. Recall is read-only and fills the local group at zero offsets. Dirty,
invalid offsets, gizmo/marquee gestures, pending requests and changed context lock library actions.

Retail rows bind to the original model hash and retain ownership across coordinate
and compatible content edits. Allocated rows/objects additionally bind to the typed
vector/object allocation fingerprint. This fingerprint is deliberately strict:
another allocation invalidates recall for allocated selections until explicitly
updated against Current. It never silently substitutes a reused index. Group validation on Open checks
portable metadata without disc access; recall requalifies Current row bounds, source,
scene key and the saved review key. Reimport cannot reinterpret selections/history.
The source import, authored geometry, pose and selection metadata stay separate.

Native Town01 model0000 passed create, local recall, rename, membership update,
delete/Undo/Redo, Save/Open, then recalled rows1/2 and applied X16 to exactly those
rows. Recall still worked after the coordinate edit. All first-phase model content,
imported records, scene overrides and Authored files stayed unchanged; metadata and
geometry used separate history entries. Recall snapshots are read-only. Screenshots
inspected, zero page errors/game launches. Paired normal Builds with/without the
library emitted identical native payloads.25 focused project/library/copy/view/
selection checks plus JavaScript exact-recall guards passed. Private evidence:
`local-output/sdk-20260909/saved-vertex-groups-20261005/proof.json`.
No new gameplay acceptance gate; existing movement output remains queued. Goal active.

## Selected vertex plane alignment - 2026-10-05

Selected vertex group scope now offers Align group X/Y/Z at the selected rows'
minimum, maximum or bounds-centre source coordinate. Centre is (min+max)/2 rounded
to the nearest signed16 integer with half ties away from zero, including negative
centres. This changes one axis of selected rows only. Other coordinates, vertices,
objects, normals, faces/material words and allocation ownership remain unchanged.
No actor transform or pose channel changes; native positive Y still points down.

Alignment stages a local Draft. Current/Retail comparisons and one/all-instance
placed-scene inspection retain it through Return/Restore. Nonuniform alignment hides
translation handles and locks XYZ offsets, membership, library and history until
Apply/Discard. Explicit Apply uses /api/model-vertices-alignment and one normal
model override/history step. Already-flat selections make no draft/history change.
Raw and scene previews share the exact source-qualified candidate; keys, native
ownership, complete geometry, axis/anchor/membership and stale replies are checked.

Native Town01 model0000 object0 rows[0,1,2] aligned on the centre Y plane passed
no-op/Discard, draft locks, Current/Draft, placed scene comparison, all-instance mode,
Return/Restore, Apply, Undo/Redo and Save/Open. Complete document/Authored files
unchanged before Apply; candidate matches independent exact-axis reconstruction.
Full Retail-section normal Build directory/ZIP readback passed; only model offsets
1518/1526/1527/1534/1535 change. Seven focused alignment/group/allocated-object checks
and JavaScript geometry/rounding/review guards passed; screenshots inspected, zero
page errors/game launches. Allocated-row content replay retains source ownership.
Evidence: `local-output/sdk-20260909/vertex-alignment-20261005/proof.json`.
Package SHA256: `b56e76531495b9a39f9e2831f5f0727461551f185cebd14e479dcf228bd077d4`.
Appearance and scene/save-load stability remain on the deferred queue. Goal active.

## Selected group scaling

Choose Selected vertex group, select or recall object-local indices, then choose Scale
percent and Pivot. Stage group scale previews a local uniform scale from Current.
Origin uses [0,0,0] in the source object's coordinates; Group bounds center uses the
selection's axis-aligned min/max midpoint, preserving half-unit pivots until final
rounding. Percent is an integer1..1000; mirrored, negative and zero scaling are excluded.
Final native coordinates use nearest signed16 words, ties away from zero. Overflow
rejects the entire operation. Normals/topology remain fixed; lighting is not reconstructed.

Retail/Current/Draft layers compare geometry. Inspect movement draft in scene qualifies
the exact selected scale against the native candidate, with Current/Proposed placement
and supported pose preserved. Return to movement draft or Restore scene preview retains
the staged scale. Apply vertex group scale creates one normal project replacement;
Discard restores Current. Selection, offsets, picking, saved-group editing and history
are locked while a transform draft exists. After Apply, the same workspace refreshes
Current and normal Undo/Redo are available. Save/Open persists the authored model and
normal Build uses the existing qualified writer/relocation path. Gameplay remains a
separate verification gate.

Verification: 6 focused synthetic Python checks, the Node geometry workflow checks
and 2 JavaScript syntax checks passed. The actual headless retail editor exercised
100% no-op, Stage/Discard, draft locks, Retail/Current/Draft, exact placed-scene Review,
Return/Restore and all-instance inspection, then one Apply, source refresh, Undo/Redo
and Save/Open. Before Apply, document and authored files remained unchanged. Normal
private Build passed independent directory/ZIP decompression to the complete expected
scene section. Only nine bytes inside the selected XYZ words changed; unselected rows,
opaque padding, normals and packets were byte-identical. Package SHA/ZIP integrity
matched. Scene screenshot inspected. The initial browser attempt found a missing
root scene label/qualification path; it was fixed and the failed attempt preserved.
No game launched or installed. Evidence:
`local-output/sdk-20260909/vertex-scaling-20261005/proof.json`.

## Selected group rotation

In **Move model geometry**, choose **Selected vertex group**, enter or recall the
object-local indices, choose **Turn** (-90, +90 or 180 degrees) and **Pivot** (group bounds
center or object-local origin), then click **Rotate group X/Y/Z**. Axes refer to retail
source coordinates, where positive Y points down. Rotation uses the same signed axis
permutations as whole-object rotation. The pivot retains half-unit coordinates and final
words round nearest with half ties away from zero. There is no arbitrary-angle operation.

This stages a local draft. Selection, offsets, picking and project history lock until
Discard or Apply; Current/Retail comparison remains available. Inspect the draft in the
scene, compare Current/Proposed, and Return or Restore to retain it. Exact operation,
indices, axis, turn, pivot, geometry and source hashes qualify Review. Apply uses
`/api/model-vertices-rotation` and one existing model replacement command; Undo/Redo,
Save/Open and normal Build preserve the authored result. An unchanged result adds no
history. Signed16 overflow rejects the entire draft. Only selected vertex XYZ words change;
unselected rows, stored normals, padding, packets and native ownership remain fixed.
Normals are not reconstructed, so lighting/gameplay acceptance remains a manual check.

Evidence: `local-output/sdk-20260909/vertex-rotation-20261005/proof.json` and its browser
screenshots/native Build audit. The private browser and directory/ZIP readback did not
launch, install or control the game.
