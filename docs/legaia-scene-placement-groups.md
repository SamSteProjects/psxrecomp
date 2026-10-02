# Mixed scene placement groups

In an authored imported field scene, choose **Select scene placements** and click
imported actors and static decorations in the hierarchy or viewport to toggle
membership. The focused object remains available in the Inspector; selected
bounds identify the group. Select 2–128 targets, including at least one imported
actor and one static decoration. **Clear placement group** clears membership.
NPC drafts, ground and placed scenery are excluded.

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
