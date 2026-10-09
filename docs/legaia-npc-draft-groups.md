# Move a group of NPC drafts

## Copy selected NPC arrangements - 2026-10-05

**Repeat draft...** now offers **Copy selected NPC arrangement** when the current
or recalled selection contains at least two same-scene NPC drafts. Mixed selection
members outside the NPC group are excluded with a count. Copy the arrangement in
a line or rectangular grid: each member keeps its own retail donor and receives
the same native-grid offset per repetition, preserving relative X/Z positions.
Copies receive independent stable IDs and bounded member-derived names. They are
independent NPC drafts; no parenting, prefab inheritance or runtime spawning is
asserted. The project-wide 128-draft limit and native coordinate bounds apply.

Review creates no project changes. Detached scene inspection retains original
entities and each copied member's model binding, with Current/Proposed/Return.
Source/input changes withdraw the review. Apply adds all copies in one Undo step;
Redo and Save/Open preserve them through the existing normal Build pipeline.

Offline: 13 focused Python checks and Node proposal/scene contracts pass. A private
retail browser copied two differently bound NPCs, checked held originals, exact
relative placement and member-specific geometry, then Apply/Undo/Redo/reload.
The 540px review was inspected. Normal format-7 Build independently decoded the
complete candidate MAN and all nine appended records: new record57 is X3392/Z5632,
model105/animation13; record58 is X3072/Z5632, model111/animation56. Current saved
receipt and preserved project/history/preexisting files pass. Evidence lives in
`local-output/sdk-20260909/npc-arrangement-repeat-20261005/` (`project-verified-2`,
`proof.json`, `normal-build-proof.json`, `arrangement-540.png`). Package SHA-256:
`88fe43534bacd8dfe12a5d9a9e02d3b56f0d2fc834e636cc2397880056c2f6ab`.
Gameplay spawning, scheduling, scripts, collision and visibility remain deferred.
No game launch, install or disc export occurred.

## Reviewed NPC group retail donor assignment - 2026-10-05

The NPC Inspector now offers **Assign NPC group donor...** for 2 through 128
same-scene drafts. Current or recalled scene selections seed the dialog; mixed
selections retain only NPC members with an exclusion note. Choose an imported
retail donor, review the exact membership, then inspect the detached proposed
scene with Current/Proposed comparison and Return before Apply. Identity, name
and X/Z stay fixed; imported actors and unselected scene content stay unchanged.

This changes inherited native model, initial animation, scripts and related actor
data. It is donor reuse, not arbitrary model/animation assignment. Source changes,
input changes and malformed proposals reject or withdraw Apply. One Apply creates
one Undo step; Redo and Save/Open preserve the reviewed donor bindings.

Offline evidence: eight focused Python cases and the Node proposal guards pass.
The actual private browser passed Review without mutation, detached scene model
bindings, Current/Proposed/Return, input withdrawal, Apply, Undo/Redo and reload.
The final read-only check passed the tightened guards and an inspected 540px
layout. Normal Build independently decoded the complete format-7 compressed MAN:
selected records 53/54 retained X/Z 2944/5568 and 3136/5568 while changing donor
model/animation from 105/13 to 111/56. All five unselected appended records retained
105/13 and their positions. Saved receipt freshness and project preservation pass.
Evidence: `local-output/sdk-20260909/npc-donor-group-20261005/` (`proof.json`,
`normal-build-proof.json`, `ui-final.log`, `donor-group-540.png`). Package SHA-256:
`e936966c4e152a74f4fe35c1ffd722b499c888d79e3316e3ef9eac486117a58c`.
Gameplay visibility, spawning, scheduling and inherited script behavior remain
unverified. No game launch, install or disc export occurred.

## Saved NPC selections feed group authoring - 2026-10-05

Opening **Move NPC draft group...** now checks the NPC members of the current
scene placement selection, including recalled saved selections. A focused draft
remains the default when no NPC group is selected. The dialog copies membership
and qualifies every selected NPC against the active scene before opening.
Unavailable, wrong-scene, duplicate or oversized selections reject with a visible
error. Existing checkbox/search controls still let the user change membership.

For mixed selections, the NPC tool includes only NPC members and reports how many
other placements it excludes. Use mixed scene placements to edit all kinds together.
This closes the saved-selection-to-authoring handoff for offset/layout/removal review;
selection alone does not change project or game data. The existing review source
binding, detached scene proposal, atomic command history and serializer remain.

Validation: 16 focused SDK group/selection cases, the expanded group and saved
selection Node checks, and editor syntax passed. Actual private Town01 browser
checks covered focused default membership, saving/reloading/recalling an NPC pair,
exact checked members and review targets, preview without mutation, Apply/Undo/Redo,
unchanged unselected drafts, explicit mixed-selection scope, Save/reload and disk
reopen. The 540px dialog was inspected; no page errors occurred. Normal format 7
Build readback matched the complete prepared MAN and all seven appended NPC rows,
including the edited pair with donor model/animation preserved. Saved package
verification matches current inputs; Build preserves project/history/preexisting
files. Package SHA256:
`cafe9311747208ea97b8dbc54cb50e7a772397aaaeb1189761b8444011550cc4`.
Evidence: `local-output/sdk-20260909/npc-selection-group-handoff-20261005/proof.json`
and `normal-build-proof.json`. No game launch, installation or full-disc export ran.
Gameplay remains deferred; the full SDK goal remains active and work stays solo.

## Native-grid NPC group rotation, scale and reflection - 2026-10-05

The NPC group Inspector tool now adds position rotation (-90/+90/180 degrees),
spacing scale (1-1000 integer percent), and X/Z coordinate reflection about a
selected NPC anchor. It operates on 2-128 existing NPC drafts in the active Edit
scene. Rotation uses exact X/Z quarter-turn permutations; scale rounds final
coordinates to the native 64-unit grid with half steps away from zero. Reflection
changes one coordinate. The selected anchor stays fixed. These layouts change
positions, preserving model geometry, facing, donor bindings and other metadata.
Rounded placements can coincide; inspect Current/Proposed before Apply.

Exact typed layout requests, a distinct native-layout review-key binding, complete
source snapshots and full bounds validation qualify the whole group. Invalid,
stale or out-of-bounds proposals publish nothing. The existing detached scene
preview and atomic Apply/Undo/Redo work unchanged; no-ops retain redo history.
Offset, alignment, distribution and removal remain compatible.

Validation: 16 focused Python cases and group/repetition/mixed-NPC Node checks passed.
Actual private Town01 browser checks covered all three rotations, scale and both
reflection axes, fixed anchor, input withdrawal, Current/Proposed/Return, exact
renderer matrices, unchanged geometry/unselected entities and preview without
mutation. One reflection passed atomic Apply/Undo/Redo, Save/reload and disk reopen;
the 540px dialog was inspected, with no page errors. Normal format 7 Build readback
matched the complete prepared MAN and all seven appended NPC positions, model 105
and animation 13. Saved package verification matched current inputs; Build preserved
project/history/preexisting files. Package SHA256:
`b3185a16a71aea60a3ffba163d1f0131f021daeab4168751fb07f0ac72eab560`.
Evidence: `local-output/sdk-20260909/npc-native-layout-20261005/proof.json` and
`normal-build-proof.json`. No game launch, installation or full-disc export ran.
Gameplay remains deferred; the full SDK goal stays active and work stays solo.

## Reviewed NPC draft group removal — 2026-10-05

The NPC group tool now offers **Remove selected NPC drafts** alongside offset,
alignment and distribution. Review retains exact selected draft metadata and a
full-project source-bound key. Its detached scene proposal removes those authored
instances while preserving every imported and unselected entity. Changing the
operation withdraws Apply. **Remove reviewed drafts** issues `delete_actor_drafts`
and creates one atomic Undo entry; Undo restores stable identities and all metadata.
Only two through 128 existing drafts in the active Edit scene are eligible.
Malformed requests, wrong command types, missing drafts and stale reviews reject
before mutation. Imported donor actors remain unchanged.

Focused SDK group/repetition checks (eleven Python cases) and Node report/scene
qualification pass. Actual private browser verifies review without mutation,
detached removal, operation invalidation, Apply, exact Undo/Redo, save/reload and
independent disk reopen; 540px layout passes with no page errors. A private normal format-7 Build passes current-input saved package verification.
Its final decompressed native MAN matches the prepared candidate and contains
exactly the four remaining appended NPC rows, with both removed identities absent.
Package SHA-256: `e1026d3eb4f83f54970f58b475c157177258f71a05c5b2d5672631dae16b90ef`.
Build leaves the project document/history and preexisting file bytes unchanged.
Evidence is under
`local-output/sdk-20260909/npc-draft-removal-20261005/`. Gameplay remains unverified;
no game launch, install or disc export was performed.

Select an authored NPC draft, then choose **Move NPC draft group...** in its
Inspector. The action is available when this scene contains at least two drafts.
The current selection seeds checked NPC members, including a recalled saved set.
A mixed selection contributes only its NPC members; the dialog reports excluded
placements. Use mixed scene placements to edit every kind together. If there is
no NPC group selection, the focused draft is checked by default.
Use mixed scene placements when editing NPC drafts together with imported actors
or static scenery.

Search by authored name or stable ID. **Select visible drafts** adds every matching
draft to the selection; clearing the search does not clear selection. **Clear
selection** removes all members. Include at least two drafts before reviewing.

Enter X/Z offsets in multiples of64 retail units, then choose **Preview group
movement**. The table shows each draft's Current and Proposed coordinates. Every
result must fit64..16384. An invalid last member rejects the complete proposal;
a zero offset is inspectable but leaves Apply disabled.

**Inspect group in scene** shows the detached proposal with the existing
Proposed/Current comparison. **Return to NPC draft group** retains the accepted
review; **Restore scene preview** discards the scene comparison. Preview and
inspection create no authored changes. Height is sampled source scenery for
preview only; this tool does not author Y or infer runtime collision.

**Apply group movement** validates the complete current project and applies all
selected X/Z positions as one Undo entry. Undo restores the entire group; Redo
reapplies it. Save/Open preserves the resulting positions. Original names, donor
bindings, imported records and unselected drafts stay unchanged. Each draft can
still be moved or edited independently afterward.

The review uses `draft-group-offset.v1` and source-bound typed reports. A changed
project, source scene, draft collection, selection or offset requires fresh review.
Closed dialogs abort pending review/scene requests; removed selection callbacks
cannot modify the dialog's current selection. Scene inspection qualifies exact
selected positions and model/display transforms, donor metadata, asset geometry,
and unchanged unselected scene content before presenting the proposal.


## Alignment and distribution

Choose **Placement operation** after selecting the group:

- **Align X/Z to anchor** uses the selected anchor's Current coordinate. The
  other axis remains unchanged; the anchor must belong to the group.
- **Distribute along X/Z** retains the smallest/largest Current coordinates and
  places intermediate drafts as evenly as the64-unit retail grid permits.
  Current coordinate, then stable ID, determines order for tied positions.

Intermediate half-grid values round upward. For three positions128,192,320,
X distribution yields128,256,320: the ideal middle224 rounds to256. The endpoints
and every Z value stay unchanged. At least one64-unit interval per gap is required;
a group with insufficient span rejects. Coincident alignment remains an author
choice, without collision or runtime behavior guarantees.

Changing operation or alignment anchor clears the accepted report. Preview shows
both unchanged and changed members. Already-correct layouts leave Apply disabled;
Apply changes the complete reviewed group in one Undo entry. Layout review uses
`draft-group-layout.v1`; existing offset keys remain `draft-group-offset.v1`.

Offline2026-10-05: 10 focused Python cases and expanded Node contracts pass. Actual
private editor review/scene/distribution Undo/Redo, alignment Apply, Save/reload and
disk reopen pass; the540px layout is inspected with no page errors. Normal Build
accepts six drafts through compressed capacity-growth relocation. Saved package
verification matches current inputs and the package's decoded MAN matches the
prepared candidate byte for byte, with every appended position correct. Project
metadata/history and preexisting files stay unchanged during Build.
Package SHA256: `d6dc02e375d60518fd862fa22bdf32ff017ae5e9c4e92d58f31193290dcd3ad9`.
Evidence: `local-output/sdk-20260909/npc-draft-layout-20261005/{proof,normal-build-proof}.json`.
No game, installation or full-disc export; runtime acceptance remains deferred.

## Build and runtime scope

Normal Build consumes these ordinary authored draft positions through the existing
source-qualified NPC candidate pipeline. Use **Review Build** for current complete
project readiness. This tool adds no serializer, spawn behavior or script meaning.
Runtime spawning, scheduling, visibility, collision and safe total actor-pool
headroom require the existing separate evidence and gameplay checks. An accurate
editor preview or serialized MAN is not gameplay acceptance.

## Offline evidence — 2026-10-05

Eight focused Python group/repetition cases, Node report/scene checks and module
syntax pass. Actual private HTTP/browser selection, review, scene comparison,
zero/bounds rejection, Apply/Undo/Redo/Save/reload and independent disk reopen pass.
The first search fixture matched all shared-prefix names; stable-ID filtering
corrected it. Narrow buttons/table cells are repaired and the final540px screenshot
is inspected. The layout recheck creates no changes; no page errors occur.

Prepared native PROT decompression/reopen matches all six draft positions and
final MAN hash, preserving the four unselected positions. Native helper initially
pointed at the preceding grid fixture; corrected preparation/readback passes.
PROT SHA256: `62e6776ba35f56bb173bfc9fd2b9692b728add3370ee2abb70e23fa9a911d049`.
No normal package Build, game, installation or full-disc export occurs. Evidence:
`local-output/sdk-20260909/npc-draft-group-20261005/{proof,native-proof}.json`.
## NPC Grid Snap — 2026-10-08

The NPC draft group inspector offers **Snap X to grid**, **Snap Z to grid** and **Snap X/Z to grid**. Select 2–128 authored drafts in the current scene and enter spacing in multiples of 64 from 64 through 4096. Snapping uses the scene origin and rounds halfway positive coordinates upward. Native coordinate bounds are 64–16384; an out-of-range result rejects the complete group without clamping. Donor binding, names, scripts, facing and unselected drafts remain unchanged. Elevation is still a source-scene preview rather than authored NPC height.

Preview qualifies complete membership and exact proposed coordinates. Changing spacing, operation or selection withdraws the prior review. **Inspect group in scene** shows the proposed positions through the existing source-qualified NPC scene decoder; returning retains the reviewed proposal. One Apply records one Undo step. Already snapped groups create no history entry. Save/Open and the existing native NPC allocation/Build pipeline retain these positions.

Offline checks passed: nine focused Python snap/group cases, two Node suites and syntax/AST/diff checks. Actual Town01 editor checks exercised all three axes modes, malformed spacing, proposed mesh positions and one Apply. An independent complete appended-MAN reconstruction retained donor/script metadata and unselected bytes. The normal private Build's relocation package header, embedded PROT scene and compressed MAN were read back independently and matched the reconstructed candidate; full directory/ZIP, unchanged Build inputs, Undo/Redo, Save/Open and baseline restoration passed. The fixture requires the existing relocation format and still reports `build_ready=false`; these checks do not establish playable installation or gameplay. Wide/400-pixel controls were inspected. Private evidence: `local-output/sdk-20260909/npc-grid-snap-20261008/`; package SHA-256 `c6d4b81ebe0f4070e5c13dd2cbbb94beaebb0f2dd0ea791575d024683f145ed4`. No game, runtime attachment, installation or disc export ran; the full SDK goal remains active.
