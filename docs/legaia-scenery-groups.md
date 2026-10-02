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
collision interaction or script behavior. Group gizmo dragging, group rotations,
alignment and mixed entity groups remain future work.

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
