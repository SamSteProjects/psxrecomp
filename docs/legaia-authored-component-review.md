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

## Integrated source checkpoint — 2026-09-30

The retail-enabled discovery suite passed 421 tests in 172.966s with no skips
against unchanged `be7a5e42686119b2290643556a9827775cfb21c7`. This includes
this feature's Python service tests and supersedes the earlier 405-test full
checkpoint referenced above. Five Node checks and editor/module syntax passed
separately. Browser/package/rendered evidence and gameplay acceptance remain
separate; no game was launched for this checkpoint.

## Review and revert a selected actor group — 2026-09-30

Select 2–128 imported active-scene actors through Ctrl-click, ranges or box
selection, then choose **Review group components**. The component selector lists
supported authored components present in the selected group. Each actor shows
its authored settings separately or explicitly inherits retail. With no authored
components there is nothing to revert. NPC drafts, scenery, P2 scripts and other
scenes retain their existing dedicated workflows.

**Revert reviewed group component** removes that entire component from affected
actors only, preserving other components and imported evidence. All members are
validated before mutation; one Undo/Redo restores/removes the affected group.
Empty owner override records are removed. Existing Save/Open and build consumers
use the resulting normal override state. An all-inherited review is a no-op.

The read-only `/api/actor-component-batch` report binds project root, imported
source document, active scene, selected IDs, chosen component and every member's
authored/inherited state. The strict `revert_actor_group_component` command
recomputes that identity before mutation. Changes to the last or an inherited
member reject the whole command. Unrelated component changes are preserved and
do not invalidate the chosen component review. Replay, wrong owners, malformed
fields and Live authoring are rejected. Pending reports cannot attach after
closure or changed selection/source context. Reopen a stale review to refresh it.

Fifteen focused Python tests passed in 1.771s without skips, including four new
group tests for detached reviews, inherited members, atomic stale rejection,
source preservation, unrelated components, one-entry history, persistence,
no-op/replay and HTTP field validation. Editor syntax and diff checks passed.
Retail town01 browser selected actor0001/0002/0003: two authored Transform members
and one inheriting member. Review made no writes; one command reverted the two
Transforms while retaining menu and selector components. Undo restored authored
assets and dirty status. Adding a Transform to the inherited third member after
review rejected the whole revert without additional changes. Closing a held
read-only response discarded it. Zero page errors; screenshot inspected.

Private evidence: `local-output/sdk-20260909/group-component-review-20260930/`
contains `group-component-browser-check.json` and `group-component-review.png`.
Fixture preparation saved two private position overrides; review checks made no
further Save or installation. No game launched; owned browser/server closed.
This feature's Python and UI checks postdate the earlier 421-test source checkpoint.
A new full-suite result and gameplay/runtime acceptance are not claimed.

## Latest integrated source checkpoint — 2026-09-30

The retail-enabled SDK discovery suite passed 425 tests in 172.910s, exit0,
no skips, against unchanged `55f5db15ec610db8642e1e995c29a0b4c6855730`.
This includes group component review/revert and supersedes the earlier 421-test
checkpoint and historical predates notes above. All six Node checks and editor/
group/renderer syntax passed separately against the same source. Browser/package/
rendered evidence and gameplay acceptance remain separate. No game launched.
Private log/metadata: `sdk-regression-20260930-group-components.log/.json`
under `local-output/sdk-20260909/`. Log SHA256:
`69e0a61d32f73d1b313b00b543b0199f8787519991430e17eff44e23c31be60c`.
