# Rectangular source wall editing

Refresh scene resources, open the collision asset, and choose **Edit source wall
bits**, then **Edit wall rectangle…**. Apply or discard a pending single-cell edit
before entering the rectangle tool. Enter inclusive first/last row and column,
choose one quadrant or all four, and choose the proposed Blocked value.

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
