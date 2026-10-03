# Editing world source placements

Open **World placements**, choose map01, map02 or map03, and **Inspect placements**.
Select an object record or click a mesh in the viewport. The Inspector shows
immutable source positions, current authored values, effective source positions
and the number of cells using that record. **Frame record** fits all affected
source instances; drag to orbit and scroll to zoom.

Edit signed16 **Record offset X/Y/Z** and **Yaw units**0..4095. These are record
offsets, not absolute world coordinates. X adds to the cell's source X, Y adds
to its negated floor-table height, and Z subtracts from the cell's source Z.
The renderer reflects source Y once. Model selectors, cells, footprint anchors,
other rotation axes, flags and opaque record bytes remain unchanged.

Shared records require **Edit every cell using this shared record**. The choice
is explicit because one tree record can serve many world cells. Records also
serving unresolved or excluded source cells are unavailable for authoring.

**Review transform** performs fresh source qualification and reports the exact
changed bytes and every affected source identity. **Current** and **Proposed**
compare the complete source scene with the same camera. Drafts block project
Save/history and competing mesh selection until Apply or Discard. **Review retail
reset** prepares removal of the selected record's override. Review writes no
project or disc bytes. **Apply reviewed transform** uses its source-bound key
and records one Undo step. Undo/Redo and Save/Open preserve retail provenance.
Authored assets list each kingdom's source placement component.

Normal **Build** emits a source-hashed full MAP overlay. Disjoint existing MAP
changes merge into that overlay; conflicting bytes reject before package writes.
The package feature remains disabled by default. Source object transforms are
spawn seeds: scripts may change visibility and resting positions, and collision,
binding and runtime behavior remain unverified. The existing World ground and
world-source GLB exports retain their explicit retail-source scope.

## Offline evidence — 2026-10-02

All three kingdoms pass unchanged round-trip and independent authored MAP
construction, source-only field masks, shared-scope rejection, reviewed Apply,
Undo/Redo, Save/Open and normal package readback.17 focused Python cases pass
with private source input and no skips, including ordinary Build regressions.
Node checks independently verify source bounds, review coverage, offset signs,
yaw matrix arithmetic and Y reflection.

Eight actual browser scenarios pass: pending mesh-selection protection, draft
Save/history gates, shared-record rejection, independent Proposed matrix values
and changed GPU pixels,540px layout, Apply/history/persistence, normal Build and
an actual GPU mesh pick. No page errors or game requests occurred. Independent
readback of the browser package changes only MAP bytes15265/15275 against retail;
record0477 affects57 source seeds. Its complete73,728-byte payload matches direct
source reconstruction. Private proof is retained under
`local-output/sdk-20260909/worldmap-placement-authoring-20261002/`.

No game, install or disc export ran. Visibility, placement/collision behavior and
script-driven transforms remain on the deferred gameplay queue.

[Current/Proposed scene GLB exports](legaia-worldmap-placement-export.md) now retain authored or reviewed world placement transforms without applying proposals. The original World ground exports remain retail-source.

[Viewport translation handles](legaia-worldmap-placement-gizmo.md) now edit source X/Y/Z drafts with explicit shared scope, snapping, Frame anchor and cancellable previews. Review and Apply remain the only authoring path.
