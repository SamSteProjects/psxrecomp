# Authored component review and revert

In the Project browser, filter to Authored assets and open an actor, partition-two
script or scene's asset details. **Review authored components** shows each stored
component separately. Expand one and choose **Revert … component** to remove all
of that component's authored settings. Other components and imported evidence
remain intact. Shared animation/scenery edits may affect other instances.

The action uses normal project history: Undo restores the component; Redo removes
it again. Save/Open retains the result. Reverting the last component removes the
owner from Authored assets while its imported representation remains available.
This operation requires Edit mode and does not require a running game or disc
read. Model/texture replacements, NPC drafts and templates retain their existing
dedicated editing/removal workflows.

The service supplies detached component data and a review identity bound to the
project directory, imported source document, owner, component and authored value.
The command accepts these identities only. Changed reviewed values or source,
another project, unsupported components, extra fields and replay after removal
are rejected before history or state changes. Unrelated component edits do not
invalidate the reviewed component. Clearing a component can recover unsupported
or obsolete authored operands without pretending to validate their retail writes.

## Evidence — 2026-09-30

25 focused project/text/selector/component tests passed in 1.334 seconds, with no
skips. Five new tests cover detached reviews, inherited transform restoration,
other component/source preservation, dirty/history/save/reopen, stale source and
project identities, command replay, scene/P2 scopes, Edit mode and HTTP shapes.
Editor syntax and diff checks passed.

A private town01 project retained three actor0001 menu overrides, actor0003's
model selector 240 and a transform override. Browser review/revert/Undo/Redo/Save
preserved the selector and unrelated menu data. An external transform change
made the old review stale; clicking Revert rejected it with identical authoritative
state. No page errors. The screenshot was inspected. Independent disk reopen
retained the saved transform removal, selector and all three menu edits. The later
stale-review probe was unsaved and did not rewrite that saved result.

Private evidence: `local-output/sdk-20260909/component-review-project-20260930/`
contains `component-review-browser-check.json` and `component-review.png`.
The owned browser closed and temporary server stopped. No game launched, no
package installed. This feature follows the 405-test full checkpoint and has the
focused validation above; it does not establish runtime/gameplay parity.
