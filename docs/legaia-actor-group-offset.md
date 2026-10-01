# Actor group placement offsets

Choose **Actor group offset** in the editor toolbar. Select 2 through 128
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
Neither comparison nor Restore sends authoring commands. Transform handles are
disabled during inspection; scene GLB export requires Restore first.

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
