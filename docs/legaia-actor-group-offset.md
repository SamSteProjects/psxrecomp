# Actor group placements

Choose **Actor group placements** in the editor toolbar (formerly Actor group offset). Select 2 through 128
imported actors in the active scene, optionally filtering the list by name or
stable ID. Enter X/Z offsets and choose **Preview group offset**. The table shows
Retail, Authored, Effective and Proposed positions independently. Preview does
not change the project. Changing the selection or offset clears the proposal.

**Apply group offset** moves the whole selected group through one project command.
One Undo restores every affected actor; Redo reapplies it. Other components and
imported evidence are preserved. Save/Open and the existing Build/export paths
consume the resulting Transform components normally. A zero offset creates no
history entry. This dialog's group selection is separate from the viewport's
single-entity selection and gizmos.

Offsets must be integer multiples of 64. Every proposed coordinate must fit the
exact MAN placement grid from 64 through 16384. One invalid actor rejects the
whole group before mutation. Y, facing, script targets, scheduling and runtime
positions are not changed or inferred. NPC drafts and environment instances
retain their dedicated tools. Runtime scripts may subsequently move an actor.

The command's review identity binds the project directory, source document,
scene, selected actor states and delta. Changed effective positions, another
source/project/scene, replay and malformed requests are rejected. Group history
also prevents changed-source reimport even after Undo leaves no active overrides.
Pending preview responses cannot attach after the dialog closes or its source
context changes. Live mode disables authoring.

## Inspect the proposal in the 3D scene

With the Authored scene loaded, choose **Inspect group in scene** after Preview.
The viewport moves only the proposed actors and shows a separate proposal bar
and reference markers. The source scene meshes and authored project stay intact.
**Group layer** switches between Proposed and Current authored positions with
the same camera; **Frame group** frames both sets of placement points.
**Return to group** restores current positions and retains the selection,
offsets and reviewed table for Apply. **Restore scene** discards the inspection.
Neither comparison nor Restore sends authoring commands. Single-entity transform handles are
disabled during inspection; proposed group handles are described below; scene GLB export requires Restore first.

Proposed positions use a detached scene-service view and the same source terrain
interpolation as the normal viewport. Missing surfaces keep the explicit
ground-plane preview convention; no runtime elevation is inferred. Proposals
are withdrawn on source/scene/project/mode changes or incompatible scene
geometry/pose inspection. This is an offline placement preview.

### 3D inspection evidence — 2026-09-30

26 focused project/scene/component/group tests passed in 1.301s with no skips.
Node checks cover exact coordinates, source/review identity, duplicate/missing
actors, elevation conventions and detached maps. Editor/module syntax passed.
Retail town01 actor0011/0012 inspection moved exactly the two proposed transforms,
preserved all other transforms and the mesh set, and derived new source terrain
height. Proposed/Current kept the camera; Return retained the draft; Restore
recovered every original transform. Source invalidation withdrew the proposal.
The inspection-only workflow sent zero authoring requests, preserved authoritative
project state and had zero page errors. Screenshots were inspected. A separate
Return-to-group Apply/Undo check restored all authored settings and dirty status;
proposal export was rejected with zero export requests. No Save or game launch.

Private evidence: `local-output/sdk-20260909/actor-group-scene-20260930/` contains
`group-scene-browser-check.json`, `group-scene-return-apply.json`,
`group-scene-proposed.png` and `group-scene-current.png`. The owned browser and
server were closed. The 405-test full checkpoint predates this addition.

## Group command and package evidence — 2026-09-30

23 focused retail-enabled project/group/build tests passed in 9.731 seconds, no
skips. Five group tests cover no-write preview and layered values, atomic rejection,
source/component preservation, one-step history, Save/Open, stale identities,
replay, zero-offset no-op and reimport protection under grouped Redo history.
JavaScript syntax and diff checks passed.

Retail town01 browser checks selected actors0001/0002, rejected a non-grid input
and a last-actor bounds failure, then previewed/applied +64 X/Z. Preview made zero
authoring requests; Apply made one. Undo/Redo restored the group and preserved
existing menu edits. Save completed, and a closed pending preview discarded its
late response. Zero page errors. Initial and final screenshots were inspected;
the final read-only table separately shows all four position layers.

Independent disk reopen and package ZIP/LZS readback matched the exact expected
MAN: four actor placement bytes, all three existing menu runs and model selector
240. Unrelated MAN bytes remained equal to the composed expected source. Package
SHA256: `cf2f42b2604cca3e3fccfdb778c0934e94ab00942df0fcff366f3ce87ed196c0`.
Private evidence is under `local-output/sdk-20260909/actor-batch-project-20260930/`:
`actor-batch-browser-check.json`, `actor-batch-package-check.json`,
`actor-batch-preview.png` and `actor-batch-final.png`.

No game launched, no package installed. Owned browser and server closed. Gameplay
visibility, collision and script-controlled movement remain deferred. The 405-test
full checkpoint predates this feature; focused evidence above is current.

## Integrated source checkpoint — 2026-09-30

The retail-enabled discovery suite passed 421 tests in 172.966s with no skips
against unchanged `be7a5e42686119b2290643556a9827775cfb21c7`. This includes
this feature's Python service tests and supersedes the earlier 405-test full
checkpoint referenced above. Five Node checks and editor/module syntax passed
separately. Browser/package/rendered evidence and gameplay acceptance remain
separate; no game was launched for this checkpoint.

## Drag the proposed group — 2026-09-30

In Proposed mode, drag **Group X** or **Group Z** at the group center. Movement
snaps relative to the gesture start in 64-unit increments. Selected actors move
together temporarily; accepted preview heights stay held until release. Release
validates every actor and recalculates source terrain preview heights through the
detached scene service. It does not author the project. Escape cancels temporary
movement; a bounds or validation failure preserves the accepted proposal.
Current authored mode has no group handles. Source/context/review guards remain.

Return to group shows updated offsets and the Retail/Authored/Effective/Proposed
table. Review then Apply for one command and one Undo entry. Runtime positions
and elevation remain unverified.

Node offset, immutability and bounds checks, editor/module syntax and diff checks
passed. Actual headless retail town01 actor0011/0012 pointer drags accepted +256 X
and +64 Z without authored writes. Escape restored the prior proposal; a 20480-unit
bounds move was rejected. Current mode hid handles; Return retained offsets.
Apply sent one command; Undo restored authored assets and dirty status. Zero page
errors. Final screenshot inspected. No Save, installation or game launch.

Private evidence: `local-output/sdk-20260909/actor-group-gizmo-20260930/`
contains `group-gizmo-browser-check.json` and `group-gizmo-proposed.png`.
Owned browsers/servers closed. These JavaScript/browser checks postdate the
421-test Python checkpoint; the backend was unchanged.

## Select actors in the viewport or hierarchy — 2026-09-30

Ctrl-click (Command-click on platforms providing Meta) toggles an imported actor
in the active scene into a group. The first toggle includes the focused imported
actor, if eligible. Cyan highlights distinguish group membership from the focused
actor shown in the Inspector. Selection is bounded to 128 actors; NPC drafts,
scenery and runtime nodes keep their separate tools. In the viewport, selection
uses the frontmost visible mesh; occluded actors can be selected in the hierarchy.

The selection bar offers **Frame actor group**, **Review group offset** and
**Clear group**. Review seeds the existing checkbox dialog; dialog membership may
then be edited separately. It uses the same proposal inspection, relative X/Z
handles and atomic Apply/Undo workflow described above. Selecting a group makes
no project or selection-service requests, creates no history and is not saved.
Normal entity selection or Clear removes the group. Hierarchy search preserves
membership. Source/project/scene changes and leaving Edit withdraw it. While any
group is selected, single-actor handles are suppressed; a one-actor group cannot
open the group review. Shift-drag remains viewport pan.

Node checks cover primary seeding, toggles/removal, ineligible members, stale IDs,
128-actor bounds and detached inputs. Retail town01 browser checks exercised
hierarchy Ctrl-click on actor0011/0012 and an actual Ctrl-click on visible actor0016
mesh pixels, with no selection/authoring requests or authoritative state change.
Filtering retained membership; framing and cyan highlights were inspected.
Review retained both actors, real +64 X dragging remained unapplied until one
command, and Undo restored authored settings and dirty status. Clear/plain-click
checks passed. Injected client mode/source changes cleared selection; actual
Live was disabled because no runtime was checked. No Live/runtime parity claim.
Zero page errors; no Save, package installation or game launch.

Private evidence: `local-output/sdk-20260909/actor-multiselect-20260930/`
contains `actor-multiselect-browser-check.json` and `actor-multiselect.png`.
Owned browser/server processes closed. These UI checks postdate the 421-test
Python checkpoint; the Python backend was unchanged. Box/range selection is described below; mixed actor/scenery selection remains
future work.

## Box and range selection — 2026-09-30

Choose **Box select actors**, then drag a rectangle in the viewport. Releasing
replaces group membership with imported actors whose visible mesh pixels fall
inside the box. Ctrl/Command-drag adds them to the group. Reverse dragging works;
an empty box clears the group. Escape, blur or pointer cancellation preserves
prior membership. Shift-drag still pans; switch Box select off to resume orbit.
Source/project/scene, camera and representation guards reject stale gestures.

Mesh selection reads the existing depth-tested ID render in strips of at most
64 rows, preserving hidden/layer filters and restoring the displayed render even
on read failure. Transparent/depth behavior follows the existing viewport picking
approximation, not retail ordering tables. If meshes are unavailable but a current
placement preview exists, marker positions are used and occlusion is explicitly
unknown. This fallback has not been browser-verified by the evidence below.

In the hierarchy, Shift-click selects the inclusive range from the last focused
or toggled actor in the filtered actor list. Ctrl/Command-Shift-click adds that
range. An anchor excluded by the filter starts a new range at the clicked actor.
Ranges can include hidden actors explicitly through the hierarchy. Scenery and
NPC draft rows are not members. A selection exceeding 128 actors is rejected
atomically. Membership stays transient and project provenance is unchanged.
Proposal inspection disables box and range selection; Restore re-enables them.

Node checks passed for reversed/filtered ranges, replace/add merges, stale IDs,
128-member rejection, rectangle reversal/clamping/zero-area/high-DPI conversion,
64-row readback strips, ID deduplication and restoration after read failure.
Actual browser checks at 2x DPI (2106x1458 pick surface) used town01 source meshes.
Independent full ID-pixel readback found nine visible imported actors in the
focused scene; hiding actor0011 excluded it. Actual box drags matched exact IDs,
including reverse and additive boxes. Empty box cleared membership and Escape
preserved it. Forward/reversed/filtered/additive ranges passed. Review seeded the
exact selected IDs and proposal inspection blocked selection. Injected source
withdrawal rejected the pending box. Authoritative state was unchanged, with zero
selection-service/authoring requests and page errors. Screenshots inspected.

Private evidence: `local-output/sdk-20260909/actor-box-range-20260930/`
contains `actor-box-range-browser-check.json`, `actor-box-active.png` and
`actor-box-selected.png`. No Save, package installation or game launch. Owned
browsers/servers closed. UI checks postdate the 421-test Python checkpoint; the
Python backend was unchanged. Runtime placement/visibility acceptance is deferred.

## Latest integrated source checkpoint — 2026-09-30

The retail-enabled SDK discovery suite passed 425 tests in 172.910s, exit0,
no skips, against unchanged `55f5db15ec610db8642e1e995c29a0b4c6855730`.
This includes group component review/revert and supersedes the earlier 421-test
checkpoint and historical predates notes above. All six Node checks and editor/
group/renderer syntax passed separately against the same source. Browser/package/
rendered evidence and gameplay acceptance remain separate. No game launched.
Private log/metadata: `sdk-regression-20260930-group-components.log/.json`
under `local-output/sdk-20260909/`. Log SHA256:
`69e0a61d32f73d1b313b00b543b0199f8787519991430e17eff44e23c31be60c`.

## Alignment and distribution - 2026-09-30

Use the **Placement operation** selector in the same group dialog. **Align X/Z to
anchor** offers only selected actors as anchors and defaults to the focused group
member where possible. Every other selected actor takes that anchor's effective
coordinate on the chosen axis; the anchor itself stays unchanged. Other axes,
source height, facing and script scheduling stay unchanged. Alignment can overlap
actors on one axis; collision/walkability is not inferred.

**Distribute along X/Z** orders actors by their current effective coordinate,
using stable imported IDs to break ties. The first/last coordinate endpoints stay
fixed. Interior coordinates round to the nearest64-unit retail grid (exact ties
upward), making adjacent gaps differ by at most64. At least one grid interval
per gap is required; insufficient span rejects. This is position distribution,
not mesh-edge spacing or a change to model scale/orientation.

Choose **Preview group layout**, review Retail/Authored/Effective/Proposed rows,
then optionally **Inspect group in scene**. Proposed/Current, Frame group, Return
and Restore use the existing coordinate/terrain preview. Offset drag handles are
only shown for offset proposals. Return retains operation/anchor/report. Changing
membership or operation invalidates review; the server recomputes the exact
operation before **Apply group layout**. One command/Undo changes only owners
whose selected-axis value differs; zero-change previews disable Apply. Other
components and immutable import remain unchanged. Save/Open and Build use the
normal Transform overrides.

`/api/actor-placement-layout` accepts actor IDs and a strict layout object:
`{kind:"align",axis:"x"|"z",anchor_entity_id:...}` or
`{kind:"distribute",axis:"x"|"z"}`. Scene inspection adds only review_key at
`/api/actor-placement-layout-scene`. `layout_actor_placements` additionally binds
scene_id and review_key and permits no extra fields. Review identity includes the
source/project/all selected overrides plus operation and deterministic targets.
Stale/replayed requests and Live commands reject before mutation.

Ten focused Python tests passed in1.250s, covering effective layers, deterministic
tie order, balanced grid spacing, unchanged endpoints/axes/components, detached
projection, atomic stale/Live/malformed/HTTP rejection, no-op and history/persistence.
Existing Node group/scene checks and editor/module syntax passed. Retail browser
actors0011/0012/0013 passed Align X to0011, no-write scene comparison, retained
camera/Return, one Apply/Undo, Distribute Z, Save/reload and last-member stale
rejection; zero page errors. A final UI check verified operation labels, visible
spacing limitations, zero-change review/disabled Apply and unchanged state.
Screenshots inspected; browsers/server closed.

Independent saved-project build plus ZIP/LZS MAN readback matched the full expected
source with actor0013 Z=3648 (retail2880), actor0012/0011 endpoints1856/5440 unchanged,
earlier position edits, donor0005 initial pairs, three menus and selector240.
Private evidence lives under `local-output/sdk-20260909/group-layout-20260930/`,
including group-layout-browser-check.json, layout-noop-browser-check.json,
group-layout-package-check.json and proposal/review PNGs. Package SHA256:
`9469e6b0ba790f166e6f7b540887ee15cde09d60a1c6a0e749d118038724c00f`.
No package installed or game launched. The425-test checkpoint predates this feature.

## Integrated source checkpoint - 2026-09-30

All441 retail-enabled SDK Python discovery tests passed in177.315s, exit0, no
skips, on unchanged source `e76b05fb1775802057e41c33a5a1e4e36301a093`. This includes
the Python services described above; all eight Node checks and five syntax checks
also passed on that source. The earlier425 checkpoint predates these additions;
441 is the current integrated result. Existing browser/package/disk evidence
remains separate. No game launched; deferred gameplay acceptance is unchanged.
See SDK_STATUS.md for exact source/command/log/hash metadata.
