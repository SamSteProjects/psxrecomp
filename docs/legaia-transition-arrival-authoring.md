# Reviewed arrival edits in the destination viewport

Open a transition resource and choose Compare arrival in destination scene. The named
destination must already be imported. In the viewport controls, enter Arrival X/Z in
64-unit grid steps (64..16384) and facing sector0..7. Review proposed arrival shows the
green Proposed marker alongside blue Retail and gold Current. Frame fits all three.
The source byte audit records the Retail-to-Proposed native bytes. The Current operand
change count separately describes the pending edit relative to saved Current values.
Changing a draft withdraws Apply; Discard restores the saved values and removes Proposed.

Apply reviewed arrival requalifies the exact request and source byte audit, then uses
the ordinary set_transition_arrival command. It creates one normal Undo step and refreshes
Current in the loaded destination. Save/Open and normal Build use the same Transitions
component and serializer. This changes an existing source entry; destination names,
record lengths, other source instructions and other authored entries remain intact.
Only requested X/Z and low-three-bit facing change. Upper direction bits retain Current.
Reference Y changes inspection only; height, source triggers and runtime pose are unknown.
Scene/project/source changes withdraw the comparison/review. Enable Move arrival draft
to drag the X/Z handles in the destination viewport. The axes follow positive raw guest
coordinates through the scene transform, and snap to the native 64-unit grid. Purple
Draft is not reviewed; no request, override or history is created by the drag. Explicit
Review replaces Draft with the green Proposed marker; Apply publishes the reviewed edit.
Facing remains unchanged by dragging. Reference Y remains an inspection setting.
Escape, camera/viewport/focus or context changes cancel an unfinished drag and restore
the prior local draft/review only if its qualified source is still current. The numeric
controls remain available. Out-of-range coordinates reject without publishing.

Review endpoint: /api/transition-arrival-review accepts exactly asset_id,
project_state_key, destination_source_key and arrival. Apply accepts those fields plus
review_key. Review resolves the stable source ID through its imported scene, verifies the
source and loaded destination, independently qualifies the target byte audit, and does
not publish overrides or change the active scene. Apply repeats Review and compares the
review digest before publishing through the existing command. Unsupported/aliased or
changed source records, invalid grid points, wrong destination/mode and stale proofs reject.

Native validation on 2026-10-04: Town01 partition-two record0000 PC0x16 entering map01.
Current arrival128/3264 facing2 was reviewed/applied as256/3264 facing3. Browser proof
covers Proposed/Current rendering, stale draft withdrawal, refreshed Current and zero
errors; desktop/narrow screenshots were inspected. One Undo step, Save/Open and Undo/Redo
passed. Full normal Build MAN and delivered ZIP readback equal the independently expected
output, changing only offsets28574 and28576. Five focused Python checks and JavaScript
review/provenance/byte-audit guards passed, including preserved direction bits and invalid
source/grid/key rejection. A latest native report qualified zero Current delta and two
retained Retail-to-Current byte changes. No game was launched; execution remains queued
for manual verification. Evidence and exact package are private local-output artifacts.

Drag validation: the native editor moved X256 to X1664 while retaining Z3264 and
facing3. No request/history during drag, Escape and camera cancellation, restored
reviewed Apply, one-step Undo/Redo and Save/Open passed. Final Build directory and
delivered ZIP full MAN readback match the expected native output. Zero browser errors.
Evidence: `local-output/sdk-20260909/arrival-gizmo-final-20261004/`.
