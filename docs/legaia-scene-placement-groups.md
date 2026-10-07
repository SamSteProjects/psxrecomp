# Mixed scene placement groups

## Whole-degree mixed placement rotation (2026-10-06)

**Scene tools → Move scene placement group → Rotate positions by whole degrees in X/Z** now accepts an integer angle from -359 through 359 around a selected imported actor, NPC draft or static decoration. The existing quarter-turn choices remain available. Review, Current/Proposed viewport inspection, return to the same review and explicit Apply use the shared mixed-group workflow. Apply records one history step; Undo/Redo and Save/Open retain exact positions. An angle of zero is a no-op. This rotates placement positions; height, actor facing, scenery orientation, donor bindings and other components are held.

The SDK and browser share frozen Q30 whole-degree sine coefficients. Global proposed coordinates round half away from zero to 64 units for imported actors/NPCs and one unit for scenery. Off-grid scenery anchors remain fixed. Current coordinates must be bounded integers; final actor/native scenery ownership and range checks remain authoritative. `rotate_angle` accepts exactly `kind`, `anchor_entity_id` and integer `angle_degrees`; booleans, fractional values, out-of-range angles and extra fields reject. Fixed precision is an editor layout definition, not a recovered runtime rotation algorithm.

Seventeen focused Python checks passed across angle math, mixed groups/HTTP and NPC groups; two Node suites passed complete proposal decoding and existing layout regressions. All 4,314 cross-language vectors matched exactly across -359..359, both native precisions and signed/off-grid points. A fresh private muted headless retail editor passed -45°, 30° and 45° Review, an off-grid scenery anchor, input-change withdrawal, Current/Proposed matrix checks, held height/orientation, return and one-command Apply. Wide/400px screenshots were inspected, with zero page errors. Separate NPC checks preserve donor/metadata and the unselected draft.

Independent MAN actor decoding/opaque-byte comparison and full MAP directory/ZIP readback matched the reviewed positions; unselected actor/scenery changes remained exact. Undo/Redo/Save/Open passed. Native package SHA-256 `7360e2f054a8b781fea15942bcab3400502ef6fe57c792eb7e11ea17be14d4eb`. Evidence: `local-output/sdk-20260909/mixed-placement-angle-20261006/pass2/` (`proof.json`, `browser-proof.json`, `browser.log`, `review.png`, `review-400.png`, `proposed.png`, `audit.json`) and `parity.json`. The preserved first proof assumed every coordinate was stored as an override; the corrected fresh proof checks the effective position when an unchanged coordinate remains inherited.

No game launch, attachment, installed mod or full-disc export occurred. Native appearance/collision acceptance remains deferred; the full SDK goal stays active and development remains solo. See [mixed placement groups](legaia-scene-placement-groups.md).

## NPC drafts in mixed scene placement groups — 2026-10-05

**Scene tools → Select scene placements → Move scene placement group** now accepts
2–128 members spanning at least two of imported actors, authored NPC drafts and
static decorations. Shared offsets, alignment, distribution, spacing scale, position
rotation and coordinate reflection use the existing review workflow. NPCs keep native
64-unit X/Z coordinates and may be layout anchors. Their donor, name and other
metadata stay unchanged. Current/Proposed inspection holds source preview height.

NPC-inclusive reviews use version 2 and bind the full Current draft snapshot. NPC
Retail placement is absent and shown as **Authored only**; Retail reset is disabled
and rejected for the entire group. Existing actor/scenery version 1 reviews remain.
Apply validates the whole proposal before changing overrides and NPC drafts, then
records one combined Undo step. No-op operations preserve history and redo. Saved
selection sets now include NPC drafts; runtime placement semantics remain deferred.

Validation: 31 focused Python cases, new NPC source/DTO guards, legacy mixed-placement
Node checks and editor syntax passed. Actual private Town01 browser checks covered
three-kind selection, hierarchy membership, exact proposals with held height, review
without mutation, Current/Proposed inspection, atomic Apply/Undo/Redo and Save/reopen.
The 540px review was inspected; no page errors occurred. Normal Build emitted a
format 6 package whose complete native MAN and MAP carriers match preparation.
Readback confirmed imported actor record 12 at X/Z 3840/1920 and appended NPC record
53 at 3008/5696 with donor model 105 and animation 13. The decoded-size patch and
saved receipt match current inputs; Build preserved project/history/preexisting files.
Package SHA256: `e728785c95c6e58f925b3873b785c21b93396e6c711bb9c64f2f465182b61361`.
Evidence: `local-output/sdk-20260909/mixed-npc-placement-20261005/proof.json` and
`normal-build-proof.json`. No game launch, installation or full-disc export ran.
Gameplay remains deferred; the full SDK goal remains active. Work continues solo.

## Mirror mixed scene placement coordinates — 2026-10-05

**Move scene placement group → Mirror X/Z coordinates about anchor** reflects the
selected coordinate across its value at a selected imported actor/static-decoration
anchor: `proposed_axis = 2 * anchor_axis - Current_axis`. Final actor coordinates round
to 64 units with half steps away from zero; scenery retains integer precision. Off-grid
scenery anchors are supported and stay fixed. The other coordinate stays unchanged;
only changed actor axes become overrides. This reflects positions without mirroring
models, changing facing/object rotation, creating parenting or recomputing collision.

Exact typed `{kind, axis, anchor_entity_id}` requests use a distinct native-mirror
review algorithm binding. Review qualifies selection, source and full native proposals;
Current/Proposed inspection and Return author nothing. Input/source changes withdraw
review. Actor bounds and complete MAP offset/allocation checks reject atomically. Apply
records one Undo step through existing commands; no-ops preserve history and redo.
Shared descriptors, unselected instances, heights and unrelated components remain.

Validation: 28 focused Python layout/group/HTTP cases, expanded mixed-placement Node
checks and module syntax pass, including both axes, off-grid anchor, half rounding,
unchanged-axis metadata, invalid/stale requests, no-op/history, offset overflow and
forged/safe-arithmetic guards. Actual private Town01 browser checks X and Z reflection,
fixed off-grid anchor, Current/Proposed GPU matrices, held height/rotation, withdrawal/
Return and one Apply at 540px. Undo/Redo, Save/Open and normal Build pass with full MAP
directory/ZIP and independent MAN coordinate/opaque-byte readback. Package SHA256:
`41922554d2e88a1b07fcfd9482853c1a924286f1aab763e7e1b2650a6e451b9b`.
Evidence: `local-output/sdk-20260909/mixed-placement-mirror-20261005/proof.json`.
No game, installation or full-disc export ran. Runtime/script-driven placement and
collision acceptance stay deferred; the full SDK goal remains active and work stays solo.

## Rotate mixed placements at native coordinate precision — 2026-10-05

**Move scene placement group → Rotate positions -90°/+90°/180° in X/Z** accepts a
selected imported actor or static-decoration anchor at its native integer position.
Scenery anchors can lie between actor grid points. Signed quarter-turn permutations
rotate Current distances around that fixed anchor; final actor positions round to
64-unit coordinates with half steps away from zero, while scenery retains integer
precision. The anchor stays fixed. Rounding can bring placements together; use the
Retail/Current/Proposed review. This supersedes initial grid-only position rotation.

The SDK and browser qualify exact operation/selection/source and full native proposals.
Rotation has a distinct `native-coordinate-rotation.v1` review-key binding; old algorithm
tokens reject. Actor source-coordinate limits, signed scenery offsets, full MAP allocation,
atomic Apply/Undo and Save/Open remain. Heights, facing, object rotations, unselected
placements, shared edits and collision resources stay unchanged. Rotation changes
positions, not geometry, parenting or runtime placement semantics.

Validation: 25 focused Python layout/group/HTTP cases, expanded mixed-placement Node
checks and module syntax pass. Cover all signed quarter turns, integer/off-grid anchors,
positive half rounding, actor bounds, scenery overflow, no-op/history, source withdrawal,
old-token rejection and forged/safe-arithmetic guards. Actual private Town01 browser
checks all three turns about an off-grid decoration, Current/Proposed GPU matrices,
height/rotation preservation, operation withdrawal/Return and one Apply at 540px.
Undo/Redo, Save/Open and normal Build pass with full MAP directory/ZIP and independent
MAN coordinate/opaque-byte readback. Package SHA256:
`e36c50f5dedac90d3a3625f19f1094526eeb3a45738513854884c152b10b11e1`.
Evidence: `local-output/sdk-20260909/mixed-placement-native-rotation-20261005/proof.json`.
No game, installation or full-disc export ran; gameplay remains deferred and the full
SDK goal stays active. Implementation remains solo.

## Scale mixed placements at native coordinate precision — 2026-10-05

**Move scene placement group → Scale spacing at native precision** scales selected
imported actor and static-decoration X/Z distances around a selected placement anchor.
Enter an integer percentage from 1 through 1000. Current coordinates must be integers;
decorations and decoration anchors can lie between actor grid points. Final actor
coordinates round to their native 64-unit spacing, decorations to native integer units,
with half steps away from zero. The anchor stays fixed and 100 percent is a no-op.
Rounding can bring placements together; review Retail/Current/Proposed before applying.
This replaces the initial grid-only spacing scale; scenery no longer snaps to actor
precision and rounding applies to final coordinates rather than relative distances.

Current/Proposed scene inspection changes no authored data. Changed inputs withdraw the
review. Apply rechecks project/source, selection, exact operation and full proposal,
then records one atomic Undo step. The scale arithmetic has a distinct review-key
algorithm binding. Actor coordinate bounds and scenery signed-offset limits remain.
Height, facing, object rotations, shared descriptor edits and unselected placements
stay unchanged. Scaling changes spacing, not geometry or collision resources.

Validation: 18 focused Python layout/group cases, expanded Node qualification and module
syntax checks pass, covering native signed half rounding, off-grid anchor, 100-percent
identity, actor bounds, scenery offset overflow and atomic rejection. Actual private
Town01 browser checks exercise 50/100/175 percent, fixed off-grid decoration anchor,
Current/Proposed GPU matrices, withdrawal/Return, one Apply and all action bounds at
540px. Undo/Redo, Save/Open and normal Build pass; independent MAN actor decoding and
complete MAP directory/ZIP readback preserve opaque/unselected bytes. Package SHA256:
`2178e97c3548ff3c392d371f8e7869038c50408cdb9f765b1b31418663b2d373`.
Evidence: `local-output/sdk-20260909/mixed-placement-native-scale-20261005/proof.json`.
No game, installation or full-disc export ran; gameplay appearance remains deferred.
The full SDK goal stays active.

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
bounds identify the group. Select 2-128 targets spanning at least two kinds: imported
actors, NPC drafts and static decorations. **Clear placement group** clears membership.
Ground and placed scenery are excluded. NPC-inclusive saved selection sets are supported.
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

## Quarter-turn position rotation

Choose **Rotate positions -90° / +90° / 180° in X/Z**, select an **Anchor**, then
**Review group**. The anchor can be a selected imported actor or static decoration;
Current X/Z must be integers; decoration anchors can lie between actor grid points.
The anchor stays fixed. Final actor coordinates round to 64 units, with half steps
away from zero; scenery coordinates keep native integer precision.
+90 maps relative (X,Z) to (-Z,X); -90 maps to (Z,-X); 180 negates both. The review
shows native Retail/Current/Proposed positions without publishing edits. Rounding
can bring placements together. Proposed actor
coordinates must remain native-grid representable; decoration offsets and the complete
MAP allocation must remain valid. Invalid anchors, turns or candidates reject atomically.

Inspect Proposed/Current, **Return to placement review**, then **Apply group**.
This rotates positions about the anchor while holding height, actor facing and scenery
rotations. Existing shared transforms, unselected edits, collision and unrelated actor
components stay unchanged. Changing the operation/anchor requires a new Review. Layout
inspection has no shared-offset handles. One Apply records one Undo step; coincident
positions are a no-op. Save/Open and normal Build preserve the result.

Historical grid-only checkpoint evidence: `local-output/sdk-20260909/mixed-placement-rotation-20261005/` contains
retail browser proof/screenshots and independently decoded native package readback.
This does not prove script-driven placement, collision or game visibility; gameplay
verification remains in the deferred queue.
