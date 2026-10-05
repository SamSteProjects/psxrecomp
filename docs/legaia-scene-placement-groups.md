# Mixed scene placement groups

Use **Box select placements** to drag a rectangle over visible imported actor
and static-decoration meshes. Selection uses depth-tested pixels; hidden and
fully occluded meshes are not selected. Drag replaces the group, Ctrl/Command adds,
and Shift-drag pans. An empty rectangle clears the group. At most128 placements
can be selected; an oversized result preserves the previous group. This tool
requires loaded models in the Authored scene and excludes ground, NPC drafts
and placed scenery. Escape, camera/viewport changes and stale source cancel the
gesture. Selection changes no authored data or Undo history. The focused
Inspector and hierarchy remain synchronized; use **Move scene placement group**
for a mixed selection or **Saved scene selections** to retain its identities.


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

## Alignment and distribution

**Operation** now offers shared offsets, **Align X/Z to selected anchor**, and
**Distribute X/Z on grid** for the mixed selection. Alignment accepts any selected
imported actor or static decoration as its anchor, provided its chosen coordinate lies
on the 64-unit actor grid. Distribution requires all selected coordinates on that grid,
preserves the minimum and maximum, orders ties by stable identity and rounds intermediate
grid coordinates nearest with upward half ties. Adjacent gaps differ by at most one grid
interval. Off-grid anchors/coordinates and insufficient spans reject without authorship.

Choose the operation and anchor, then **Review group**. The same Retail/Current/Proposed
table and scene comparison show every candidate. Changing operation/anchor invalidates
Review. **Return to placement review** retains it. Layout inspection holds preview height
and rotation; shared-offset X/Z handles appear only in offset mode. **Apply group**
revalidates the exact layout, selection, project source, actor encoding and complete MAP
merge before publishing one Undo/Redo step. No-op layouts add no history. Save/Open and
normal Build use existing serializers. Heights, facing, unrelated components, unselected
instances, shared transforms and collision edits remain preserved; gameplay is deferred.

Private evidence: `local-output/sdk-20260909/mixed-placement-layout-20261005/` includes
`proof.json`, review/scene screenshots and normal Build audit. The actual retail editor
checked distribution, alignment to a decoration, mode withdrawal, GPU comparison, Return
and one Apply; history/persistence and full MAP/independently decoded MAN package readback
passed. No game launch or installation was performed.

## Reset X/Z to Retail

Choose **Reset X/Z to Retail** in **Operation**, then **Review group**. Every selected
actor/static decoration receives its exact imported source X/Z. The review separately
reports how many positions move and how many authored actor axes clear, including a
metadata-only reset when an explicit actor override already equals Retail. Current actor
component axes qualify the report. Inspect Proposed/Current and Return before **Apply group**.

Apply clears the selected actors' X/Z overrides and prunes empty Transform/components,
while preserving authored Y, facing and unrelated components. Static scenery resets use
instance-local source positions; shared authored descriptors remain intact for other
instances. Selected Y/rotation and unselected instance edits remain unchanged. A shared
transform can require an explicit compensation on a reset instance. This is a position
reset, not an entire Environment or actor-property reset. Off-grid integer actor positions
can be recovered because the candidate is checked against the valid source placement.

The existing source/review guards, atomic Undo/Redo step, no-op behavior, Save/Open and
normal Build remain. Private evidence: `local-output/sdk-20260909/mixed-placement-reset-20261005/`
contains `proof.json`, screenshots and audit. The actual retail editor and native package
readback verified selected source positions and retained unselected actor/scenery changes.
No game was launched or installed; gameplay verification remains deferred.
