# Static scenery group placement

In an authored field scene, click a static decoration and Ctrl/Command-click
additional decorations in the hierarchy or viewport. Shift-click selects a range
of visible static decorations in the hierarchy; Ctrl/Command+Shift adds that
range. Groups support2–128 instances. The focused decoration stays in the
Inspector and selected mesh bounds appear in the scene. Actor groups, NPC drafts,
placed objects and static decoration groups remain separate selections.

Choose **Move scenery group…**, enter common integer X and Z offsets, then
**Review group**. The table shows retail, current and proposed coordinates for
all selected instances. **Inspect proposed scenery** displays reviewed placements
in the textured scene without changing the project. **Inspect current scenery**
uses existing placements. Both retain the review; **Return to scenery review**
restores ordinary display and reopens it, while **Restore scenery preview**
discards the inspection. Preview retains each instance's current source Y and
rotation. Editing offsets withdraws the review and Apply.

While inspecting Proposed, drag **Scenery X** or **Scenery Z** to offset the
whole group. Free movement uses integer scene units; the viewport Snap control
optionally rounds movement to16/64/256/1024 units. Source Y and rotation remain
held. Releasing requests a fresh review and updates the retained table/offsets;
it does not apply a project command. During review the viewport restores the
prior verified proposal. Rejection retains that proposal and reports the reason.
**Restore scenery preview** can cancel a pending request; a late response cannot
reinstate it. Current inspection has no group drag handles.

Choose **Arrange scenery group…** to align or distribute the current selection.
For **Align**, choose X or Z and a selected anchor; every target adopts that
anchor's current coordinate on the chosen axis. The other axis remains unchanged.
For **Distribute**, targets sort by current axis coordinate and stable identity;
endpoints stay fixed and intermediate positions use evenly spaced integer units,
rounding half units upward. This is not grid snapping. A span smaller than the
number of intervals is rejected rather than collapsing positions. Review,
Proposed/Current comparison, Return/Restore, Apply, Undo/Redo, Save/Open and Build
use the same scenery workflow. Arrangement inspection has no move handles.

**Apply group** recomputes against fresh source bytes and the same selection,
full project metadata, scene and offsets. It merges one Environment override,
with one Undo/Redo operation. Save/Open and normal Build preserve the result.
Zero offset preserves the exact existing binding, including redundant axes and
instance order, with no history. Source/scene/mode changes withdraw stale UI.
The serializer validates the entire merged binding and descriptor allocation
capacity before any project mutation. Existing shared transforms, Y, rotations,
unselected instance edits, Collision and retail provenance remain preserved.
No grid anchors, floor tiers, mesh identities, script records or runtime state
are authored by this tool.

The same existing source decoration coordinate interpretation is reused:
X increases with descriptor X; world Z increases when descriptor Z decreases.
Supported encoded offsets remain signed16; group delta inputs accept integers
within ±65535 but each resulting descriptor must remain within its encoded range.
Only source cells marked for the static decoration sweep and non-reserved,
non-placed descriptors are supported. Individual overrides allocate only unused
zero-filled descriptors through the existing MAP serializer.

This does not establish terrain height after a move, runtime visibility, movement,
collision interaction or script behavior. Group rotations
remain future work. Imported actors and static decorations can also be selected
together through the separate [mixed placement tool](legaia-scene-placement-groups.md);
that tool uses64-unit X/Z offsets and excludes drafts and placed scenery.

## Verification — 2026-10-01

Two implementation subagents owned separate new service/UI files; parent owned
project/server/editor integration and retail verification. A third read-only
review found no remaining actionable issue. Parent fixed zero-delta normalization
so it cannot silently reorder/clean existing overrides.

Twenty-one focused retail-enabled Python tests passed in16.060s. They cover
shared/instance precedence, outside edits, Y/rotation/Collision preservation,
Z sign, source/static/range/capacity/metadata guards, review no writes, atomic
Apply/Undo/Redo, exact zero-delta no-op and Save/Open. HTTP checks verify request
field rejection and stale Apply. Retail scene transforms match the reviewed
coordinates and normal Build ZIP matches the complete expected73728-byte MAP.
All28 Node tests and29 editor syntax checks passed.

The actual retail browser selected town01 decoration cells1833 and2089, reviewed
X+128 / Z+64, inspected Proposed and Current matrices, retained Y, withdrew
changed inputs, applied, Undo/Redo and saved. Current comparison restored both
original matrices exactly; review/inspection did not change saved bytes.
Shared record194 X64/Y-rotation64 and an existing cell2089 Z32 offset were retained
and composed with the new group positions. Collision remained unchanged.
Zero page errors; dialog and textured scene screenshots inspected. A second
browser pass verified zero-offset Apply disabled, actor selection clearing group
and preview, a hierarchy Shift range of12 decorations, and cancellation of
a pending review without reinstatement or saved-file changes.

A parent HTTP fixture initially used an absent metadata_path attribute, the first
browser probe assumed state.authored, and the initial batch command named a
nonexistent test module. Those fixture errors were corrected; production behavior
was unchanged. The source-bound zero-delta fix was separately tested.

Private evidence: `local-output/sdk-20260909/scenery-group-20261001/`.
The saved project generated package SHA256
`eca7822f30607c925c345ad825a1075331167b8d0b042c35b54104f3df25f4f4`.
ZIP readback matched six scenery audit changes and one preserved collision change
in a single full MAP overlay, with unchanged floor tiers. No game launched and
no runtime behavior inferred. See [Deferred verification](legaia-gameplay-verification-queue.md).
This feature postdates the integrated514 checkpoint; full SDK acceptance remains
incomplete.

## Drag and preview refresh verification — 2026-10-01

An isolated UI subagent extended proposal review; a second isolated service/test
subagent repaired actor transform preview keys. Parent integrated gestures and
centrally passed45 focused Python tests in16.686s, all28 Node tests and29 syntax
checks. Active imported actor X/Z/Y edits, Clear/Undo/Redo refresh instance
identity while geometry remains cached. Unknown actor Y resamples source ground
height after horizontal movement. Existing appearance/cache tests retain their
geometry assertions while full preview identity now changes with transforms.

Retail browser pointers moved the two selected walls X+73, then Z+128 with
64-unit snapping. Drafts issued no command; rejected signed-range movement kept
the exact report. Pending review restored prior matrices, Restore aborted it,
and late response could not reinstate the preview. Current inspection restored
exact matrices and had no handles. Apply/Undo/Redo/Save passed with preserved Y,
shared offsets/rotation and Collision. Individual decoration and actor X+64
pointer drags refreshed correctly, undid cleanly and left saved bytes unchanged.
Zero page errors; textured preview and review screenshots inspected.

The initial pointer harness exposed canvas focus scrolling15 pixels, causing
incorrect movement deltas; preventScroll fixes the actual cause. Initial UI file
encoding was normalized to UTF-8 before final syntax/Node checks. The actor
browser check initially failed because Transform was absent from the preview
key; the corrected service passed the same check after an owned SDK restart.

Private evidence: `local-output/sdk-20260909/scenery-group-drag-20261001/`.
The copied saved project produced package SHA256
`d5ce6e02dc710814a1fa015b2634eabbac3cba951ddd218de63dc032241eacc2`.
ZIP readback exactly matched73728 MAP bytes, six scenery audits and one preserved
collision change with floor tiers unchanged. No game launched. This focused
milestone postdates integrated514 and does not establish runtime acceptance.

## Arrangement verification — 2026-10-01

Two isolated subagents owned service/refactor tests and the new dialog/Node tests;
parent owned command/HTTP/scene integration and final verification. Fifty-three
focused retail-enabled Python tests passed in17.726s, all29 Node tests and30
syntax checks passed. Seven new service tests exercise deterministic rounding,
shared/instance precedence, no-op metadata preservation, stale operations/source,
signed bounds and whole merged descriptor capacity. HTTP review rejects missing
or extra fields and invalid anchors/axes; one Apply is atomic, stale replay is
rejected, Undo/Redo restore documents and no review saves bytes.

The retail copied project selected cells1833,2089,2345. X alignment to cell2345
changed two proposals while preserving Z/Y; Proposed matrices matched the table
and Current matrices restored exactly. Distribution on Z retained endpoints
2048/2368 and moved only cell2089 from2272 to2208. Both views had no group drag
handles. Changed controls withdrew Apply. Apply/Undo/Redo/Save passed; repeating
distribution was an exact no-op with Apply disabled. Closing a pending review
aborted it and a late valid response did not restore inspection. Zero page errors;
textured scene and compact review screenshots inspected.

The initial final browser step waited on a disabled arrangement button because
Save correctly withdrew the old source-bound selection. The fixture was restored
to its baseline and the harness corrected to reselect before no-op review; the
complete workflow then passed. This was a harness assumption, not a product fix.

Private evidence: `local-output/sdk-20260909/scenery-layout-20261001/`.
Saved package SHA256:
`75d11678520b6acb2f4b21987436a8f21390f5cf1575b0db65dc2d5de8e0a055`.
ZIP readback exactly matches73728 MAP bytes, six scenery audit changes and one
preserved collision change. Independent grid/descriptor decoding matches each
selected world coordinate; selected Y/rotation and floor tiers remain unchanged.
No game launched; gameplay and full16-layer SDK acceptance remain incomplete.
