# Mixed scene placement groups

In an authored imported field scene, choose **Select scene placements** and click
imported actors and static decorations in the hierarchy or viewport to toggle
membership. The focused object remains available in the Inspector; selected
bounds identify the group. Select 2–128 targets, including at least one imported
actor and one static decoration. **Clear placement group** clears membership.
NPC drafts, ground and placed scenery are excluded.
[Saved scene selections](legaia-scene-selections.md) retains and recalls mixed
membership across project sessions or scene changes.

Choose **Move scene placement group…** and enter common X and Z offsets. Both
must be integer multiples of 64 within -16320 through 16320. Actor coordinates
must remain representable in the source placement encoding; decoration
coordinates, the complete merged Environment binding and descriptor allocation
must also remain valid. This shared step preserves the actor coordinate rules.

**Review group** shows retail, current and proposed X/Z for every target without
changing the project. **Inspect proposed placements** or **Inspect current
placements** displays the corresponding scene and frames the group. Proposed
inspection holds the current preview height and rotations; runtime height and
behavior remain unknown. **Return to placement review** retains the table and
input. **Restore placement preview** withdraws the inspection. Editing offsets,
changing selection/source/scene/mode, or cancelling a pending request invalidates
the review; a late response cannot reinstate it.

While inspecting Proposed, drag **Placements X** or **Placements Z** to shift
the full group. Handles always snap the relative movement in 64-unit steps,
including when the general Snap moves checkbox is off. Both object types keep
their current displayed height and rotations. Release requests a fresh review;
it does not apply changes. Current has no movement handles. Rejected requests
retain the verified proposal, and Restore cancels a pending review. Escape,
camera/representation/source changes and resize cancel an in-progress gesture.
Return retains the freshly reviewed numeric offsets for explicit Apply.

**Apply group** validates the same full project/source context, selection and
offsets again, then publishes the actor Transform and scene Environment changes
as one Undo/Redo operation. Existing actor components, authored Y, decoration
Y/rotation, shared transforms, unselected instance edits and Collision remain
preserved. A zero offset is an exact no-op and Apply stays disabled. Save/Open and
normal Build use the existing actor and MAP serialization paths.

This operation does not infer terrain height, author facing or create parenting
relationships. Actor-only groups and static-decoration-only groups retain their
existing tools, including their separate alignment/distribution workflows.

## Verification status — 2026-10-01

Forty-seven focused Python checks passed, alongside all 31 Node files and 32
editor syntax checks. Actual retail browser selection, retained Proposed/Current
matrices, height/rotation preservation, no-op/input withdrawal, atomic Undo for
both owners, Redo/Save and pending cancellation passed with zero page errors.
Fresh representation/source-mode guards withdrew empty selection and retained
inspection without writes. Screenshots inspected. Reopening the saved project
and normal MAN/MAP Build passed complete ZIP readback and independent coordinate
decoding, preserving opaque data, unselected scenery, existing collision and
floor tiers. Private evidence: `local-output/sdk-20260909/scene-placement-group-20261001/`.
The 548-test checkpoint predates this tool. No game launched. Runtime visibility,
collision, script-driven placement and scene lifecycle remain in the
[deferred manual queue](legaia-gameplay-verification-queue.md).

## Viewport-handle verification — 2026-10-01

31 focused retail-enabled Python checks passed in18.361s; all32 Node and33 syntax
checks passed. Real2×-DPI top-view pointer drags produced X64/Z128, retained
Current/Proposed matrices, held height/rotation, rejection/pending Restore, atomic
Apply/Undo/Redo/Save and no authored command during dragging. Fresh Escape/camera/
resize cancellation passed without writes; zero page errors, screenshots inspected.
Exact normal MAN/MAP package ZIP and independent actor/grid decoding preserved
unselected actor/scenery changes, source rotations/heights, collision/floor bits
and the saved selection library. Private evidence:
`local-output/sdk-20260909/scene-placement-drag-20261001/`.
No game launched. Runtime visibility, placement scripts and collision remain in
[the deferred gameplay queue](legaia-gameplay-verification-queue.md).
