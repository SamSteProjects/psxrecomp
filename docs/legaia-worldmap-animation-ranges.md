# World Animation Range Authoring

The selected World object's Saved World Animation Channels Inspector offers three scopes:

| Scope | Meaning |
| --- | --- |
| Single Frame | Set the inspected frame's explicit pose. |
| Hold Pose Across Frame Range | Set the same explicit pose at every included frame. |
| Offset Pose Across Frame Range | Add the difference between the entered pose and inspected Current pose to each included Current frame. Existing frame-to-frame motion remains intact. |

Inspect Current animation channels first, select the rigid object, and choose an inclusive range containing the inspected frame. Enter the desired pose at that frame. Offset mode derives per-axis deltas from that pose; inputs are target values rather than independent delta fields. Translation remains signed native -2048..2047. Rotations use exact 16-unit steps within a 4096-unit turn and wrap at the turn boundary. If any resulting frame exceeds translation capacity, the entire proposal is refused before native Review; values are never clipped.

Confirm shared-record consent, Review, inspect the Current/Proposed Preview at relevant frames, then Apply. The native ANM record is shared by every object selecting it; the preview displays the selected scene instance. Other objects and frames outside the range retain their saved edits. Apply uses the normal native channel command, one Undo/Redo entry and Save/Open persistence. Retail provenance remains immutable.

Restore Retail Object Pose also respects the chosen frame scope. It removes only the selected object's saved rows within that scope, restoring each frame's own original pose. It does not repeat the inspected Retail pose.

Offline checks passed: thirty independently decoded native frames prove offset values and sibling-row preservation. Seven invalid proposal/source checks include a later-frame translation overflow and altered native bytes. Independent complete-bank byte patching, native Apply, Undo/Redo and Save/Open pass with an unchanged original project. Evidence: `local-output/sdk-20260909/worldmap-animation-authoring-20261011/offset-native-proof.json`. Normal data-package Build `9f5b6fb89876bb4e` passes complete Current MAN/MAP/ANM, six sibling slots, directory/ZIP readback and 61 exact typed channel axes across all three kingdoms. SHA256: `34bc792bf9ca4d430daa02949e9fee8f5d501799ec0c19359005cff5a15c3efb`. Evidence: `offset-build-proof.json`. The actual Map02 editor workflow passes range selection, motion-preserving Review/Preview/Apply, sibling retention, one history entry, Undo/Redo and Save/Open. Wide/400-pixel captures were inspected and page errors are absent. Evidence: `offset-range-browser-proof.json`. Native timing, activation and gameplay remain unverified.

## Channel Request Capacity

Offline checks passed: placed-object channel Review and Apply have dedicated 1 MiB JSON request limits, covering the declared 4,096-row native authoring budget. The editor Apply route dispatches the existing `set_world_animation_channels` project command; source freshness, explicit shared consent, Review key, one-step history and persistence stay under its existing ownership. The generic command endpoint retains its 32 KiB limit. Early oversized-envelope refusal happens before reading the body.

Three focused HTTP checks pass: a synthetic 512-frame/eight-object native draft reaches Review and matches independently packed bytes across all 4,096 rows; dedicated Apply dispatch preserves exact command fields; malformed and oversized requests refuse without reaching mutation. Three existing native authoring checks pass. This capacity fixture is synthetic; it does not establish a Retail clip of that size. Actual Map02 range Review/Preview/Apply passes via the dedicated route, retaining sibling edits and one-step history, Undo/Redo and Save/Open. Wide/400-pixel captures were inspected; page errors are absent and the original project stays unchanged. Evidence: `local-output/sdk-20260909/worldmap-animation-authoring-20261011/animation-http-budget-browser-proof.json`. No package Build, native recompilation, game, installation or disc export ran. Gameplay remains deferred and the full SDK goal stays active.
