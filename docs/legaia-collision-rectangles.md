# Rectangular source wall editing

Refresh scene resources, open the collision asset, and choose **Edit source wall
bits**, then **Edit wall rectangle…**. Apply or discard a pending single-cell edit
before entering the rectangle tool. Enter inclusive first/last row and column,
choose one quadrant or all four, then select **Set wall bits** and the proposed Blocked value, or **Restore retail walls**. Restoration uses each selected bit's own verified retail value, including mixed blocked/unblocked cells; it preserves authored bits outside the selected area.

**Review rectangle** displays separate retail/current/proposed bits and counts
effective changes and the total resulting authored override. The table shows up
to64 selected bits; the complete reviewed selection remains bounded to4096 bits.
Review changes no project files or history. Changing a form field withdraws Apply.
**Apply rectangle** recomputes the proposal from freshly verified source MAP bytes
and requires the exact current review key, then uses the ordinary wall override
command for one Undo/Redo operation. Save/Open and normal Build retain that result.
No-op proposals disable Apply and create no history when submitted directly.

Rows1–127, columns0–127 and quadrants0–3 use the existing canonical MAP grid.
Reversed/out-of-range bounds, non-integer values, oversized selections or merged
overrides, extra fields, stale metadata/source and Live mode reject before edits.
Bits matching retail are removed from the override within the selected area;
unselected authored bits and other components remain preserved. Source wall bits
are the high nibble; floor-tier bits are the low nibble and remain unchanged.
Andrew's exact pinned `world/field_movement.rs` source was reread for that existing
distinction. No reference code copied and no new movement semantics inferred.

This edits the supported 0x12000-byte source MAP. Runtime script collision paints,
actor blockers, walkability, visibility and scene-entry behavior remain separate
unverified concerns. It does not create trigger/region records or live collision.

## Selecting walls in the scene viewport

Choose **Select wall rectangle** in an authored Edit scene. The tool loads the
verified source collision catalog if needed. Left-drag selects inclusive source
cells; release opens a seeded rectangle review. A click selects one cell. The
initial proposal blocks all four quadrants; the review form can select one
quadrant or Unblocked. Choose **Top (X/Z)** for a direct view, or use perspective.
Pan/orbit camera controls remain available. Escape cancels the active drag;
Escape with no drag exits selection mode. A camera/projection/viewport-size or
source change cancels a stale gesture. Outside bounds and oversized selections
are rejected. No pointer movement writes an authored command.

Picking uses the canonical reference X `(0,16384]`, Z `[0,16256)`. X=128 belongs
to column0, while Z=128 begins row2; quadrant64-unit boundaries retain the same
source decoder bias. Row zero and wrapped/aliased coordinates remain excluded.
The overlay uses Y=0 as a reference plane, not decoded terrain height. It draws
above the models, so mesh occlusion is not used to infer source wall eligibility.

After Review, **Inspect proposed walls**, **Inspect current walls** and
**Inspect retail walls** display the selected bits in the central scene. Orange
means blocked, blue unblocked; green outlines mark Current/Proposed differences.
The preview strip identifies the layer, selected count and reference plane.
**Return to wall review** retains the proposal and inputs. **Restore wall preview**
withdraws it. Input/source/mode/representation changes withdraw stale reviews.
Apply remains explicit and requires the freshly recomputed source-bound key.
The collision Inspector's numeric rectangle opener still rejects pending
single-cell edits until Apply or Discard.

## Verification — 2026-10-01

Seventeen focused retail-enabled Python checks passed in14.410s. Checks cover
multi-cell/quadrant composition, preservation outside the rectangle, floor bits,
one-command history, retail restoration, no-ops, stale/changed proposals, bounds,
merged4096 limit, Save/Open and exact normal MAP package readback. All27 Node
test files and28 editor syntax checks passed, including typed rectangle/report
guards and canonical field ordering. Initial tests assumed a MAP filename and
reused a full override in the drift fixture; corrected test setups retained the
production serializer and limits. A subsequent unblocking no-op confirmed the
retail sample area was originally unblocked.

The browser selected town01 rows15–16, columns20–21, all four quadrants, Blocked.
It reviewed16 effective changes without writes, withdrew changed inputs, rejected
reversed bounds, applied one history entry, Undo/Redo, saved, rejected stale/extra
API fields, and disabled a repeated no-op. Zero page errors; compact final dialog
screenshot inspected. Owned test browser/server stopped; no game launched.

The final saved project produced a normal package with16 changes. Independent
ZIP readback matched the expected complete73728-byte MAP and preserved floor
tiers. Package SHA256:
`63176d4fd5b8b5bc89bbcf199ca25148e84543568b301a5de3d3d9af9ddefed1`.
Private evidence: `local-output/sdk-20260909/collision-rectangle-20261001/`,
including `project-final/`, test logs, browser checks, screenshots and package
proof. See [Deferred gameplay queue](legaia-gameplay-verification-queue.md).
This feature postdates integrated514; full SDK/runtime acceptance remains open.

## Spatial comparison extension — 2026-10-01

After Review, use **Spatial comparison** to switch Proposed, Current and Retail.
The diagram shows every selected bit rather than only the first64 table rows.
Orange means blocked, blue unblocked, dark areas are unreviewed quadrants, and
green outlines mark differences between Current and Proposed on every layer.
X increases right and Z increases down. Bounds and quadrant locations use the
same canonical reference plane as the scene source-wall overlay: each cell128
units and each quadrant64. This is a diagram of the source grid; terrain heights,
real movement, runtime paints and live scene identity are not inferred.

Switching layers changes no project data or requests. Editing the proposal
withdraws the comparison and Apply. The existing stale/source, one-command
history, Save/Open and normal Build behavior remains unchanged.

Parent integration passed22 focused retail-enabled Python tests in17.122s,
all27 Node tests and28 syntax checks. Five new loopback HTTP tests check exact
body fields, bounds, Edit mode, source failure/drift, stale metadata/proposals,
atomic Apply/Undo/Redo, no-op redo preservation and unchanged saved files on
failure. Geometry checks cover source bounds2560–2816 /1792–2048 and all four
quadrant locations. A synthetic browser fixture displayed16 reviewed bits,
verified blocked counts16 Proposed/4 Current/0 Retail, no layer-change requests
or writes, input withdrawal and zero page errors. Screenshot inspected; browser
closed. This browser fixture tests the production tool with synthetic responses,
not a fresh retail scene viewport. Private evidence:
`local-output/sdk-20260909/collision-spatial-20261001/`.
No game launched; this extension postdates the integrated514 checkpoint.

## Viewport verification — 2026-10-01

Two isolated subagents owned pure source-grid math/tests and the retained review
dialog; parent owned central scene/gesture/server integration and acceptance.
Twenty-one focused retail-enabled Python tests passed in10.570s, all30 Node files
and31 syntax checks passed. New math checks cover exact/fractional quadrant and
cell boundaries, invalid/nonfinite/domain inputs, reverse drags and4096-bit limits.
The first Python batch referenced two nonexistent module names; corrected to
existing environment/importer suites. A parent file edit briefly used the Windows
locale encoding and was restored to UTF-8 before final Node checks. The initial
browser found a disabled viewport button after scene readiness; draw now refreshes
its eligibility, and the same complete workflow passed after terminal failure.

Retail browser at2× DPI selected rows15–16/columns20–21 using real pointers,
verified16 bits and no draft command or saved-file changes, retained inputs and
Proposed16/Current0/Retail0 comparisons, input withdrawal, one Apply/Undo/Redo/Save.
A second browser passed tilted perspective reverse drag, Escape/camera change
cancellation, pending-close abort and late-response withdrawal. Final read-only
inspection on the saved project verified Proposed16/Current16/Retail0, explicit
layer/plane labels, no-op Apply disabled and retail-representation withdrawal.
Zero page errors; scene and review screenshots inspected.

Normal saved package SHA256:
`a8e9c953747947da0a147e6aeff86ce26c5c44fc322ff6b3cd68c09d4a3bd012`.
ZIP matches all73728 MAP bytes with six preserved scenery audit changes and17
collision changes (16 selected plus one previous outside bit). All selected wall
high nibbles are blocked; floor low nibbles, outside collision and the complete
scenery binding remain unchanged. Private copied-project path is recorded in
`local-output/sdk-20260909/wall-viewport-20261001/prepared.json`; browser/test/ZIP
proofs share that directory. No game launched. This feature postdates integrated548;
walkability, runtime paints/blockers and full16-layer acceptance remain open.

## Retail restoration evidence, 2026-10-03

**Restore retail walls** sets each selected bit to its own verified source value rather than clearing the whole selection. It removes the selected authored wall overrides and preserves outside bits; a single quadrant can be restored while retaining others. The existing bounded rectangle request accepts `blocked: "retail"` alongside the prior boolean paint values. Source review hashes include this operation, and Apply re-qualifies the same request through the existing wall override command. Floor tiers and unknown MAP bytes remain source-owned. The Blocked checkbox is hidden for restoration to avoid suggesting one uniform value.

Five focused Python cases pass with private input and no skips, including mixed source patterns, exact outside-bit/floor preservation, Undo/Redo, persistence, bounds/drift/budget rejection and existing retail package regression. Both rectangle and viewport Node guard suites pass. Eight actual browser checks pass through operation-change withdrawal, mixed retail values, Proposed/Return,540px layout, one Apply, Undo/Redo, Save/reload, no-op disabled Apply and normal Build. The screenshot is inspected; no page errors or game requests occur.

Independent full MAP construction/readback matches all73,728 bytes. The restored Town01 row2/column13 retains its mixed retail quadrants; the only remaining changed byte is32767 (`0x7FFF`), whose deliberately retained outside quadrant bit is XOR0x10. Every low floor nibble matches source. Package SHA256: `143ca9497ec65065a56765605cedc07ff4e7f782335019c1880399ebeaf8b036`.

Private fixture, browser proof, screenshot and readback are under `local-output/sdk-20260909/wall-retail-restore-20261003/parent/`. Owned browser/server handles are terminal. No game, dependency installation or full-disc export ran; native collision and movement behavior remain deferred.

## 2026-10-06: source wall quadrant painting

The source wall rectangle comparison is now an editable paint workspace. `Keep Current walls; paint individual quadrants` preserves the selected rectangle's Current baseline; Block, Unblock and Restore retail brushes change individual Proposed quadrants by pointer click/drag or keyboard Enter/Space. Painting clears the previous Review and disables Apply until fresh Review. Keyboard painting retains focus. Rectangle input changes discard the paint draft. Current/Retail comparison layers remain read-only; fresh reviewed patterns can be inspected in the scene and applied as one Undo step. Scene inspection now expands Scene tools so Return to wall review is accessible.

The version-2 rectangle review binds a canonical, bounded `cell_edits` list to the same imported MAP/source/project context. Duplicate, out-of-selection, invalid and stale quadrant requests reject. The existing source wall-bit serializer merges the pattern with authored edits outside the selection and preserves all floor nibbles and unrelated MAP bytes. Uniform rectangle requests retain their version-1 contract.

Validation: twelve focused Python rectangle/HTTP/painting checks and Node rectangle/paint qualification checks passed. Actual retail browser workflow passed pointer drag, keyboard focus, retail restoration, draft invalidation, fresh Review, scene inspection/return, private Apply, Undo/Redo and Save/Open, with no page errors. Native private Build readback matched exactly: two wall bits in one MAP byte changed; every floor nibble and unrelated byte remained identical. Package SHA-256 `3410ed6f08330eca2e0866f34bedadd052f50584cbc7bec9d307f4a8cf3b1ec5`. Evidence: `local-output/sdk-20260909/wall-paint-20261006/proof.json`; wide/narrow screenshots inspected. No game launch, runtime attach or mod installation occurred. Source walls remain a static reference baseline; runtime/script collision paints, actor blockers and gameplay acceptance are deferred. The full SDK goal remains incomplete.

To paint a pattern, load a source collision resource, choose Edit source wall bits and Edit wall rectangle. Set bounded rows/columns and choose Keep Current walls. Review once to obtain qualified source cells; paint the Proposed map with the desired brush. Review again, inspect the proposal if needed, return to the review and Apply. The resulting pattern is one Collision command; Save persists it and a normal private Build serializes it. Current and Retail layers show comparison only.
