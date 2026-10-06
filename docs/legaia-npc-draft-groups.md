# Move a group of NPC drafts

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
