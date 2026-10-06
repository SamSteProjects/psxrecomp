# Legaia SDK validation plan

## Source-qualified saved NPC flag explanations - 2026-10-05

Saved-script comparison now labels NPC-owned flag-bit index bytes alongside
appearance, dialogue, waits, movement and facing. Each explanation is bound to the
current NPC's typed request, source donor/PC/opcode/context, exact native source
change, final record allocation and saved before/after bytes. Both records must
qualify the supported instruction; widths and special side effects stay excluded.
Upper bits, extended dispatch, no-op receipts, stale/forged metadata and overlap
are checked independently. Other differences remain unexplained. This does not
assert runtime flag identity, story meaning or behavioral equivalence.

Validation: 13 focused Python checks and the Node comparison suite pass, including
all nine operations in ordinary/extended forms, forged receipts, typed values,
upper bits and dispatch. Existing saved Town01 Build `9ad4a9c1b39b7fda` explains
28 of31 changed bytes across all six authored families, leaving three unexplained.
Streaming Build `ee3148f1c5861326` independently qualifies one flag span in each of
two NPC records. Actual read-only browser comparison renders all six labels; its
540px table was visually inspected. Project documents, history and all file hashes
stay unchanged for both projects. Evidence:
`local-output/sdk-20260909/npc-flags-script-comparison-20261005/proof.json`.

No new Build, game launch or full-disc export was needed. Flag-bearing portable
presets remain to be connected. Manual gameplay acceptance stays deferred and the
full SDK goal remains active/incomplete.

## NPC-owned flag authoring through editor and normal Build - 2026-10-05

NPC flags now connect source-qualified inspection and review to the root Inspector
and Asset Details, reviewed project commands, Undo/Redo, Save/Open and both normal
Build carrier paths. Complete entries belong to the NPC's recorded donor; stale
reviews, foreign owners, invalid bit indices and unsupported side-effect selectors
reject. Input changes withdraw browser proposals. Repetition qualifies and retains
flags. Preset capture currently rejects flag-bearing NPCs to prevent losing their
entries; portable preset integration and saved-script authored-span explanations
remain pending. See [NPC flag workflow](legaia-npc-flags.md).

Validation: 22 focused Python checks pass with the private retail fixture enabled;
two Node suites pass. A later added stale-position review regression also passes.
The actual browser verifies Review/Apply/Clear, changed-input withdrawal,
Undo/Redo and Save/reload; the 540px dialog was visually inspected. Private Town01
Build `9ad4a9c1b39b7fda` independently reopens with bit0; its record differs from
the verified prior five-family record by exactly one operand byte. Package SHA256:
`11c66953be270113d45838106195c8a1bdacd307cc499751c59bee36294c68b1`.
Private streaming Rayman Build `ee3148f1c5861326` independently reopens two NPCs
with indices3/4 and exactly one changed byte per record against their verified
baseline. Package SHA256:
`032ff923b60c8299c500c0ea5ee9521ccfe48889781aa7166d9b81f61689d6b6`.
Upper bits, the five existing own script families, placement, imports and other
draft fields stay held. Evidence: `local-output/sdk-20260909/npc-flags-editor-20261005/proof.json`
and `local-output/sdk-20260909/npc-flags-streaming-20261005/proof.json`.

No game launch or full-disc export occurred. Runtime variable identity, story
meaning and gameplay effects remain unknown; manual acceptance stays deferred.
The full SDK goal remains active/incomplete.

## NPC-owned flag operand serialization foundation - 2026-10-05

Appended NPC records now have a native serializer for source-qualified LFLAG,
GFLAG and CFLAG SET/CLEAR/TEST bit indices. It resolves final record allocations,
requires each donor-qualified instruction and operand preimage, preserves the
upper three operand bits and extended dispatch context, and changes only the
requested low five bits. Existing width and special side-effect exclusions remain
in force. No-op requests still require an exact preimage. Unsupported paths,
foreign owners, duplicate requests and invalid typed values reject.

Validation: 14 focused Python checks pass, including all nine supported operations
with ordinary and extended dispatch. A fresh private retail Town01 proof appends
two donor0040 clones, composes independent appearance, waits and movement, then
sets separate flag-bit indices 3 and 4. Exactly two bytes change; the source donor,
MAN layout, upper bits, all unrelated bytes, project files and history stay held.
Evidence: `local-output/sdk-20260909/npc-flags-native-20261005/proof.json`.

At this earlier checkpoint it was a serialization foundation; the newer
checkpoint above connects editor/project/normal Build. Presets and saved-script explanations also remain to be connected.
Runtime variable identity, story meaning and gameplay effects are not asserted.
No game launch or full-disc export occurred. Manual gameplay acceptance remains
deferred and the full SDK goal remains active/incomplete.

## Keep dense source scenes previewable with authored NPCs - 2026-10-05

The Rayman viewport failure was a combined entity-budget mismatch, not an endless
decode. Its supported source scene occupies 512 actor/scenery entries plus one
derived ground mesh; two authored NPCs raised the total to 515 and the old final
512-entry check rejected the whole preview after decoding. Scene preview now keeps
separate allowances for 512 source entries, one terrain instance and 128 independent
NPC drafts, with an explicit combined ceiling of 641 entries. A 129th active-scene draft
rejects before geometry decoding. Existing geometry/triangle/texture budgets stay
held. Shared scene constants align animation, NPC repetition/group/appearance,
preset proposal and texture-usage decoders with the supported total. The separate
world-source scene graph keeps its own existing budget.

Validation: 16 focused Python checks and nine Node suites pass. The synthetic
boundary includes all 512 source entries, ground and 128 NPCs with unchanged project
history/imports and exact source identity retention; 129 drafts reject. Actual retail
Rayman browser preview now reaches readiness in 9896 ms (one measured cold load),
with 515 entities, 514 rendered instances, 93 geometries, 15971 triangles and 5533230
texture bytes. Environment/terrain/animation errors are null. Frame All and the
NPC Focus control pass, including changed camera target and closer distance.
Overview, focused NPCs and 540px scene screenshots were visually inspected.
Project/imports/history and existing file hashes stay unchanged. Evidence:
`local-output/sdk-20260909/rayman-preview-loading-20261005/proof.json`.
A separately profiled server preview takes about 23 seconds with profiler overhead;
the earlier 60-second readiness failure is resolved by the capacity fix.

No Build/Save/authoring command, game launch or full-disc export occurred.
One unsupported scenery instance remains a source marker. Unknown NPC height,
initial heading and live placement are still explicit preview conventions; rendered
models do not establish gameplay alignment. Manual runtime acceptance stays deferred
and the full SDK goal remains active/incomplete.

## Streaming NPC readback and saved-inspector receipt fix - 2026-10-05

A fresh normal Build of the retail streaming `rayman` scene now has independent
readback proof for two NPC clones carrying appearance, dialogue, waits, movement
and NPC_RUN facing. The check found and fixed a saved-inspector bug: streaming
receipts use `actor_changes` for allocations, while compressed receipts use `actor`.
The inspector now selects the exact family from the qualified carrier schema and
rejects unknown/ambiguous receipts or missing/unbounded allocation rows. Output
DTOs remain unchanged; compressed saved inspection is also reverified.

Validation: 20 focused Python checks pass; one optional private Town01-fixture
check skips. Saved streaming Build `e5ec43a38c122f65` independently reopens record92
with sector0/wait12/X3264 and record93 with sector7/wait11/X3200. Both retain Z5696
movement, appearance model90/animation22, own padded text, placement Z5760 and upper
facing flags. The entire emitted MAN equals a separately reconstructed post-append
baseline plus intended clone edits and terminal zero padding; all other record bytes
stay held. Project/imports/history stay fixed. Package SHA256:
`04a1befcb91bfbe3c54002b02ab04123eef33537b3079cd4c27cb29e782b704f`.
Read-only browser comparison labels all five families, and the 540px table was
visually inspected. Browser project files/history stay unchanged. Evidence:
`local-output/sdk-20260909/npc-owned-streaming-20261005/proof.json`.
This closes the separate retail streaming check for NPC-owned facing and movement
and supplies retail streaming evidence for own waits/text/appearance together.

The first browser probe exceeded its 60-second full-scene viewport readiness
window. The script comparison was then verified after project readiness, separately
from scene rendering. Rayman preview loading was subsequently diagnosed as an entity-budget mismatch
and resolved in the newer checkpoint above. This earlier checkpoint did not verify
its full rendered scene. No game or full-disc export
ran. Runtime allocation/scheduling, branch execution and visible facing still need
later gameplay acceptance. The full SDK goal remains active/incomplete.

## Explain NPC-owned facing in saved script comparison - 2026-10-05

The retail-donor/generated-NPC comparison now labels **Own script facing sector**
for exact source-qualified authored bytes. Receipt rows must match the native
facing serializer, retail donor/PC/context/hash, current owned sector, final clone
allocation and separate source/generated offsets. The generated target must remain
supported after own movement. Typed sectors, full upper flags, opcode/dispatch and
CAM_CFG mode stay bound. No-op or duplicate/overlapping spans, parked targets and
forged/stale receipt rows reject. The browser independently checks raw ordinary and
extended CAM_CFG/NPC_RUN forms and the exact owned nibble. Other bytes remain
unexplained; labels establish no branch execution or runtime heading.

Validation: 39 focused Python checks and the Node comparison suite pass with the
retail disc enabled. Read-only actual browser inspection of saved Build
`2ef03e22f5a78f7b` accounts for 27 of 30 changed bytes across appearance, dialogue,
waits, movement and facing; three remain unexplained. The 540px comparison table
was visually inspected. Project document/history and all existing project file
hashes stayed fixed. Evidence:
`local-output/sdk-20260909/npc-facing-script-comparison-20261005/proof.json`.
No Build/Save/authoring command or game launch occurred. The separate own-facing
retail streaming package check is now verified above; later gameplay remains open.
The full SDK goal remains active/incomplete.

## Transfer NPC-owned facing presets - 2026-10-05

NPC preset capture now freezes supported own facing sectors alongside appearance,
dialogue, waits and movement. Facing-bearing exports use **legaia.npc-preset-file.v6**;
v1-v5 retain their existing formats and bounds. V6 contains bounded source-bound
metadata only. Export/import and instance placement freshly qualify the facing
against the same donor and its own movement-composed record; parked targets reject.
The import/placement dialogs show facing counts and require separate reviewed Apply.
Frozen presets stay independent of later source NPC edits. History and Save/Open
retain exact facing metadata without changing existing actors or imported scenes.

Validation: 37 focused Python checks and two Node suites pass. Actual editor
capture/download/upload, reviewed library import, changed-input withdrawal,
Undo/Redo, Save/reload and reviewed detached-scene placement passed. The 540px
import dialog was visually inspected. Recipient normal Build `2ef03e22f5a78f7b`
was independently reopened: sector0 and upper flags, X3200/Z5696/selector10,
wait11, own text and model105/animation13 all survived. Placement was X3200/Z5824;
source NPCs/imports stayed fixed. Package SHA256:
`8a4c6fb933dce117e9796c2a2ad35944ada8db6f7eab37aaac2cfc6dbdc65524`.
Evidence: `local-output/sdk-20260909/npc-facing-presets-20261005/proof.json`.
No game launched. Visible facing, dispatch and branch execution still need later
gameplay acceptance. Facing explanations in saved-script comparison are now supported, as recorded
above. The separate own-facing retail streaming package check is now verified above.
The full SDK goal remains active/incomplete.

## Independently author NPC script facing - 2026-10-05

NPC Inspector and registered Asset Details now offer **Edit NPC script facing**.
Source-qualified CAM_CFG/NPC_RUN targets expose an own sector0..7 override with
retail sector, preserved upper flags and unresolved dispatch context. Review
changes withdraw Apply. Apply/Clear use one history step; Undo/Redo and Save/Open
retain facing with appearance, dialogue, waits, movement, name and placement.
Script donor changes require clearing the retained facing binding first.

Facing qualifies the NPC's own movement-composed record. Parked NPC_RUN targets
are unavailable, and movement review rejects parking a target with an owned facing
override. Normal compressed/streaming MAN composition applies facing after movement,
uses final clone allocation and records npc_facing_changes. Repetition qualifies and
retains own facing. Preset capture and v6 transfer now retain facing; see the latest
checkpoints above. Saved-script facing explanations are also now supported.

Validation: 45 focused Python checks and two Node suites pass. Actual root editor
Review/Apply/withdrawal/Clear/history/persistence and the inspected 540px dialog
passed. Normal Build `a27a96074d841507` independently reopened sector0 with preserved
upper flags, own X3200/Z5696/selector10 movement, wait11, text and model105/animation13.
Placement, imports and existing preset metadata stayed fixed. Package SHA256:
`582f053dd091e1234eaabf2383620fef902b74f5852608b85f5641f924fdb910`.
Evidence: `local-output/sdk-20260909/npc-facing-editor-20261005/proof.json`.
This earlier package check covers compressed MAN; streaming readback is now
verified in the newer rayman checkpoint above. Source operands establish no
initial/live Transform heading, dispatch identity or execution. No game launched;
gameplay stays deferred and the full SDK goal is active/incomplete.

## NPC-owned facing serializer foundation - 2026-10-05

Added source-qualified facing serialization for uniquely allocated NPC clones.
Simple CAM_CFG and nonparked NPC_RUN targets accept sector0..7 only. Requests bind
a draft, its retail script donor and supported instruction ID. The shared allocation
guard verifies final record indices, extent, local/script entry ownership and aliases.
Dispatch/opcode, CAM_CFG mode and full operand preimages remain source-bound,
including no-op requests. Only the low facing nibble changes; upper flags stay held.

Facing composes with independently authored NPC_RUN movement X/Z/selectors and
wait/appearance edits. A composed parked NPC_RUN target rejects facing authoring.
Unknown/conflicting paths, nondirection LUT slots, halt-acquire CAM_CFG mode, wrong
owners/fields/types, stale flags/context, aliased records and duplicate writes reject.
The adapter emits exact source/final byte offsets and hashes, and asserts no runtime
dispatch, initial Transform heading or gameplay behavior.

Validation: 17 focused Python checks pass with the retail disc enabled. Synthetic
cases cover both opcode families, ordinary/extended contexts, all eight sectors,
two final clones, no-op/stale and unsupported targets, aliases and composition.
A fresh town01 donor0040 check composed own movement, waits and initial appearance,
then wrote sector0/7 to two clones. Exactly two facing bytes changed; upper flags,
all other candidate bytes, MAN layout and source donor records stayed fixed relative
to the post-append/composition baseline. Project document, history and existing file
hashes stayed unchanged. Evidence:
`local-output/sdk-20260909/npc-facing-native-20261005/proof.json`.
Project commands, editor controls and normal Build integration have now landed;
see the latest checkpoints above, including v6 preset transfer. No Build, export or game launch
occurred. Manual gameplay remains deferred; the full SDK goal is active/incomplete.

## Inspect NPC-owned movement targets in the scene - 2026-10-05

The NPC movement editor now offers retail donor, current NPC and reviewed proposal
scene target layers. Enter an explicit reference Y and choose **Show NPC script
targets**. The existing viewport target overlay frames qualified MOVE_TO/NPC_RUN
X/Z markers with source PCs. Selector-only EXEC_MOVE has no scene position.
Script Y, dispatch identity, branch execution and live actor position stay unknown;
markers never move NPC placement or scene geometry.

Target selection/Inspect returns to the retained movement editor at that instruction,
including unapplied inputs and reviewed Apply. Changed inputs invalidate a proposal
overlay. Clear, stale source state or overlay replacement dispose the hidden editor;
ordinary imported-script overlays keep their existing behavior. Inspector and Asset
Details use the same NPC movement editor entry.

Validation: 18 focused Python checks and two Node suites pass. Actual browser
verified three markers, explicit/invalid height guards, current X3200/Z5696,
reviewed X3264/Z5696 and retail X13888/Z5056, return-to-editor review retention,
input withdrawal and Clear cleanup. The scene overlay and 540px scrollable controls
were visually inspected. Project document, history and all existing file hashes
remained unchanged; only source/review preview requests ran. Evidence:
`local-output/sdk-20260909/npc-movement-target-scene-20261005/proof.json`.
No Build/Save/authoring command or game launch occurred. Reference Y is a display
choice, not a recovered script height or gameplay alignment claim. Manual gameplay
remains deferred and the full SDK goal stays active/incomplete.

## Preserve NPC-owned edits through repetition - 2026-10-05

Line/grid and selected-arrangement repetition retain each source NPC's own
appearance, dialogue, wait targets and script movement in independent copies.
The single-NPC browser decoder now compares each complete proposed draft with
its source; omitted, substituted or extra fields reject. UUID uniqueness and
placement remain checked. Spacing changes placement only, never script targets.

Repetition now freshly qualifies retained source operands/appearance witnesses
before review and Apply. The single review binds the complete project source key,
checks freshness after qualification, and rejects direct Live-mode review.
Line/grid review algorithms advance to v2; saved NPC identities are unchanged.
A library or other project change withdraws a prior review rather than replaying it.
Arrangement copies use the same source qualification with atomic batch history.

Validation: 30 focused Python checks and two Node suites pass. Actual editor review,
detached scene comparison, input withdrawal, Apply/Undo/Redo and Save/reload passed
for a four-family NPC. Existing scene entities, the original NPC and imports stayed
fixed; the 540px scrollable dialog was inspected. Normal compressed MAN Build
`0be50da61dbc2529` reopened both independently allocated records with retained
appearance/dialogue/wait/movement edits. Positions differ at X3200 vs X3264,
Z5760; script targets remain X3200/Z5696 with selector10 and own wait11.
Package SHA256: `c021d76f28f93bc257c3e0b25386df826b3544b9dc17d6cbb12e4ef3e6ad1e80`.
Evidence: `local-output/sdk-20260909/npc-owned-repetition-20261005/proof.json`.
No game launched. This proves editor metadata and emitted bytes, not runtime
allocation, scheduling or movement behavior. Gameplay stays deferred; the full
SDK goal remains active/incomplete.

## Explain NPC movement edits in saved-script comparison - 2026-10-05

The saved normal Build comparison now labels source-qualified NPC movement
operand bytes alongside appearance, dialogue and waits. Each movement audit row
must match its recorded script donor, reached supported instruction, PC, field,
dispatch context, source hash and exact requested before/after bytes. Final record
allocation and source/generated relative offsets must match. Missing audit rows
or other bytes receive no explanation; invalid rows reject the comparison.
The browser independently checks raw ordinary/extended opcodes, operand offsets,
current authored values and exact byte encoding before rendering X/Z/selector
labels. Bounded span counts accommodate all supported operand families.

Validation: 23 focused Python checks and the Node comparison suite pass, including
MOVE_TO/NPC_RUN/EXEC_MOVE, ordinary/extended contexts, missing bindings, forged
owners/fields/context/offsets, byte substitutions, overlap and collection bounds.
Actual saved Build `4725587333eecfe2` yielded 29 changed bytes: 26 accounted for by
qualified appearance/dialogue/wait/movement spans and three remaining unexplained.
The real editor comparison and inspected 540px table passed without authoring,
Build/Save or Run calls. Project document, history and all existing file hashes
remained unchanged. Evidence:
`local-output/sdk-20260909/npc-movement-script-comparison-20261005/proof.json`.
This explains exact authored bytes only; it proves no runtime dispatch, movement
behavior or branch execution. No game launched; gameplay stays deferred and the
full SDK goal remains active/incomplete.

## Movement-bearing NPC presets - 2026-10-05

NPC preset capture now freezes supported own script movement together with
appearance, dialogue and waits. Export uses **legaia.npc-preset-file.v5** when
movement is present, with the existing 512 KiB metadata bound. Formats v1-v4
remain supported. Capture, export/import and reviewed placement freshly qualify
the donor-owned instruction targets and operand fields; malformed owners, types,
grid coordinates, missing targets and unsupported opcode fields reject. Frozen
metadata stays independent of subsequent source-draft edits. Import adds only a
library entry; a separate reviewed placement creates the NPC.

The library/import summary reports movement target counts. Review changes withdraw
Apply, and exact reviewed placement metadata must retain all supported edit families.
Script movement coordinates remain separate from the chosen NPC placement.

Validation: 35 focused Python checks passed, one existing optional check skipped,
and two Node suites passed. The actual editor captured/downloaded/uploaded a v5
preset, reviewed an independent library import, exercised Undo/Redo and Save/reload,
and reviewed/inspected/applied an independent instance. Existing entities and source
draft/import metadata stayed fixed. The 540px import dialog was visually inspected.
Normal compressed MAN Build `4725587333eecfe2` was independently reopened: emitted
NPC movement X3200/Z5696/selector10, own wait11, own text and model105/animation13
all survived transfer. Chosen placement X3200/Z5760 remained independent.
Package SHA256: `48a4564f2c96a8224f1413583f8732262a74c05d3ed2565f211a97272f001ed8`.
Evidence: `local-output/sdk-20260909/npc-movement-presets-20261005/proof.json`.
The private readback helper initially expected a hex field instead of an audit byte;
corrected readback passed against the existing Build without rerunning gameplay.
No game was launched. Runtime dispatch/selector behavior and streaming retail
package acceptance remain unverified; gameplay is deferred. The full SDK goal is
active/incomplete.

## Independently author NPC script movement - 2026-10-05

NPC Inspector and registered Asset Details now offer **Edit NPC script movement**.
The source-qualified picker groups reached instructions and exposes only their
supported X/Z and encoded move-selector fields. Each field has a retail value and
an independent own-override checkbox. Review preserves unselected operands; input
changes withdraw Apply. Apply/Clear use one NPC history step. Undo/Redo and
Save/Open retain script donor, appearance, dialogue, waits, name and placement.
Changing script donor requires clearing retained movement first.

The editor labels encoded dispatch context as unresolved. Script targets remain
separate from placement/live coordinates; selector meaning, Y, depth, branch
execution and runtime behavior are not inferred. Native serialization composes
NPC movement before other supported edits against final allocated record IDs.
Normal compressed/streaming MAN paths record npc_movement_changes separately.
Movement-bearing NPC preset capture/transfer/placement is now supported; see the
latest v5 checkpoint above.

Validation: 40 focused Python checks and two Node suites pass. Actual root editor
source loading, field Review/Apply, withdrawal, Clear, Undo/Redo and Save/reload
passed; the 540px grouped dialog was inspected. Normal Build `f58172af849a0417`
independently reopened the emitted NPC record with X3200/Z5696/move selector 10,
retained 11-tick wait, own dialogue and model105/animation13. Imports and authored
placement remained fixed. Package SHA256:
`46cca87024e38f696ab6749d2b151e1792e2abc8d4ec1fce620b02bb07567c08`.
Evidence: `local-output/sdk-20260909/npc-movement-editor-20261005/proof.json`.
The actual package check covers compressed MAN; streaming integration has not yet
received a separate retail package check for NPC movement. Saved-script comparison
now explains qualified movement operands; other unqualified changes stay unexplained. No game was launched.
Gameplay remains deferred and the full SDK goal stays active/incomplete.

## NPC-owned movement operand serializer - 2026-10-05

Added native serialization for source-qualified movement operands in allocated
NPC scripts: MOVE_TO/NPC_RUN encoded X/Z and NPC_RUN/EXEC_MOVE move selectors.
Requests name a draft, its retail script donor and stable supported instruction
IDs. Final clone indices, local/script entry ownership, exact extent and alias
checks are now shared with NPC wait serialization. Source-stopped paths, wrong
owners, unsupported fields, stale opcode/dispatch/operand preimages and overlapping
writes reject. Source-identical requests also qualify current preimages.

Only requested fixed-width operand bytes may change. NPC_RUN depth, extended
context, Y, placement, opaque bytes and unrelated candidate content remain held.
Script targets are not current NPC transforms or live actor coordinates; selector
meanings and runtime dispatch remain unresolved. Bounds remain 128 allocated drafts
and 1024 requested targets with a 4 MiB MAN candidate.

Validation: 18 focused Python checks pass across movement/waits/appearance/dialogue.
Ordinary/extended MOVE_TO/NPC_RUN/EXEC_MOVE, two clones, final offsets, no-op,
wrong values/fields/donors, aliases and stopped paths are covered. A fresh retail
actor0040 two-clone candidate composes independent X/Z and selector edits with own
waits and initial appearance. Exactly six movement bytes changed; layout, waits,
all unrelated candidate bytes and every project file/history entry remain held.
The existing retail NPC wait probe passed again after sharing allocation guards.
Evidence: `local-output/sdk-20260909/npc-movement-native-20261005/proof.json`.
Project commands, persistence, editor controls, presets and normal Build integration
remain next. No game was launched; runtime movement remains deferred. The full SDK
goal stays active/incomplete.

## Explain NPC authored edits in saved-script comparison - 2026-10-05

Retail donor/generated NPC comparison now labels exact bytes accounted for by
saved initial-appearance, own-dialogue and own-wait audit spans. Each span binds
the emitted allocation, separate retail/generated offsets, exact before/after
bytes and the current NPC authored field. Overlapping or inconsistent spans,
wrong owners, preimages, values or allocations reject. Source/header bounds and
receipt integrity are rechecked. The browser independently verifies the same
span bytes and authored bindings before displaying the explanations.

Unaccounted changes remain **Other record change - unexplained**. They are not
classified as authored edits or presumed to be harmless append rebasing. Counts
report only changed bytes within qualified spans. Existing header/tail byte
comparison, opaque-path limits and runtime uncertainty remain intact. The whole
workflow is read-only and the bounded/paged comparison table remains available.

Validation: 19 focused Python checks and the Node comparison contract pass.
Actual retail saved Build `a61cd16b02574b72` contains 26 changed bytes: 23 accounted
for by initial appearance, own dialogue and own wait; 3 remain unexplained. The
real server/dialog rendered all categories, the 540px screenshot was inspected,
and every project file/history entry remained unchanged. No command, Save, Build
or Run was called. Evidence:
`local-output/sdk-20260909/npc-authored-script-comparison-20261005/proof.json`.
No game was launched. Gameplay equivalence remains unverified and the full SDK
goal stays active/incomplete.

## Preserve NPC-owned waits in reusable presets - 2026-10-05

NPC preset capture now freezes supported own wait targets together with own
dialogue and independent initial appearance. Capturing, portable transfer and
reviewed placement freshly qualify the wait operands against the recorded script
donor. Changing the source draft later does not change the captured definition.
Library import creates an independent preset identity; placement remains a separate
reviewed command. Inspector library/import summaries show the owned wait count.
The preceding temporary rejection of wait-bearing capture is superseded.

Wait-bearing presets use portable format **legaia.npc-preset-file.v4**, bounded
at 512 KiB. V1 donor-only, v2 text and v3 appearance formats retain their formats and
bounds. Exact donor-owned wait IDs and duration_ticks integers 0..32767 are required;
older formats cannot carry wait bindings. Presets contain metadata, not retail
script/model payloads or live state. Undo/Redo and Save/Open retain all bindings.

Validation: 19 focused Python checks and two Node suites pass, including frozen
capture, v4 transfer/placement, wrong types/owners and older-format rejection.
Actual browser capture/download/upload, reviewed library import with input
withdrawal, Undo/Redo, Save/reload and scene-reviewed placement passed across two
private projects. The 540px review was visually checked. Normal recipient Build
`a61cd16b02574b72` independently read back own wait 11 ticks, model105/animation13
and complete own dialogue. Package SHA256:
`006d1deec3bfce5982734a2844e2ef647975c15ce50befe3af72bff4adf26889`.
Evidence: `local-output/sdk-20260909/npc-waits-presets-20261005/proof.json`.
No game was launched; runtime timing, residency and script compatibility remain
deferred. The full SDK goal stays active/incomplete.

## Independently author NPC wait targets - 2026-10-05

NPC Inspector and registered Asset Details now offer **Edit NPC wait targets**.
The source-qualified picker separates retail targets from optional NPC-owned
WAIT_FRAMES overrides and accepts integer duration_ticks 0..32767. Review binds the
full current project/draft; input changes withdraw Apply, and stale reviews reject.
Apply/Clear make one existing NPC history step. Undo/Redo and Save/Open retain
script donor, own appearance, own dialogue, name and placement. Changing the script
donor with retained waits requires clearing them first. Asset summaries label own
wait targets separately; no runtime timing, seconds or reachability is asserted.

Normal compressed/streaming MAN composition now uses the native clone adapter
against final allocated record identities. The saved package records a separate
npc_wait_changes audit. NPC preset capture currently rejects wait-bearing drafts
explicitly, preventing silent omission; preset capture/transfer/placement support
is still next.

Offline validation: 36 focused Python checks and two Node contracts pass.
The actual root editor passed source loading, reviewed Apply, input withdrawal,
Clear, Undo/Redo and Save/reload. The 540px dialog screenshot was inspected.
Normal Build `5e3865fd5768fd42` independently reopened the emitted NPC script with an
exact 11-tick operand, model105/animation13 and complete own dialogue. Other drafts
and imports stayed fixed. Package SHA256:
`e3ab5e46486e9869c807360b6f3192b24f3b0ecbdea78ba2600c0e889948e54b`.
Evidence: `local-output/sdk-20260909/npc-waits-editor-20261005/proof.json`.
This actual package check covers the compressed MAN route; streaming composition
is integrated but has not received a separate retail package check for own waits.
No game was launched. Runtime timing acceptance remains deferred and the full
SDK goal remains active/incomplete.

## NPC-owned wait operand native adapter - 2026-10-05

Added a source-qualified serializer for independent WAIT_FRAMES operands on
allocated NPC scripts. Requests bind a draft, recorded retail script donor and
supported stable wait IDs with integer duration_ticks 0..32767. The adapter resolves
final record indices after all appends, verifies extent/local entry ownership,
rejects aliases/retail targets, requalifies current instruction layout and checks
exact operand preimages. Only selected two-byte targets can change. Limits are
128 drafts and1024 targets per candidate. Seconds and runtime scheduling are not
inferred; unknown/stopped source paths remain unsupported.

Nine focused checks pass across NPC waits, existing wait/appearance/dialogue
adapters. Coverage includes two independent clones, ordinary/extended waits,
boundaries, source-identical no-op, stale preimages, final offsets, aliases,
malformed ownership/values and decoder stops. Fresh town01 discovery qualifies
waits for actors0040/0044/0046. A retail two-clone candidate from actor0040 holds
independent11/22-tick targets, composed with the existing model/animation appearance
patch. Layout, all non-wait candidate bytes, donor candidate record and every
project file/history entry remain unchanged. Append's supported spawn-reference
rebasing is already part of the pre-wait candidate baseline; this is not a claim
that append preserves raw retail records byte-for-byte.
Evidence: `local-output/sdk-20260909/npc-waits-native-20261005/proof.json`.
Project commands, persistence, presets, editor controls and normal Build integration
remain next. No game was launched; runtime timing acceptance stays deferred.
The full SDK goal remains active and incomplete.

## Review NPC appearance in the placed scene - 2026-10-05

The NPC appearance picker now offers **Inspect NPC appearance in scene** after
Review. It renders a detached Proposed scene at the selected NPC's existing
placement, with Current/Proposed switching and Return to NPC appearance. Return
retains the reviewed choice; changing the choice withdraws inspection and Apply.
The SDK requalifies the witness and review before creating the detached view.
Project metadata, retail imports, script donor, own dialogue and history remain
unchanged. Scene identity, retained placement/script/evidence, unrelated entities
and model/geometry ownership are checked before displaying the proposal.

Offline validation: 11 focused Python checks and the Node appearance contracts
pass. Actual retail HTTP rejects stale reviews and unsupported fields. The full
editor passed clear-override model92-to-model105 comparison, both layer switches,
return-to-review and changed-choice withdrawal without command, Save, Build or
Run calls. The scene screenshot was inspected. Evidence: proposal-proof.json and
appearance-proposal-scene.png under
`local-output/sdk-20260909/npc-appearance-editor-20261005/`.
This is a visual authoring preview; runtime compatibility remains unverified.
No game was launched. Gameplay acceptance stays deferred and the full goal active.

## Independently author an NPC initial appearance - 2026-10-05

NPC Inspector and registered Asset Details now offer **Choose NPC initial
appearance**. The reviewed picker uses freshly source-qualified retail witnesses
for existing local model/animation pairs. Apply changes one authored binding,
retaining the script donor, own dialogue, name and placement. Changing the picker
withdraws Apply. Clear restores the script donor's initial pair. Undo/Redo and
Save/Open preserve the independent binding; changing script donor while bindings
are retained requires clearing them first.

Scene preview, asset/model references, model navigation and animation inspection
follow the appearance witness; retail script inspection continues to follow the
script donor. Frame inspection still targets the authored NPC placement. Normal
compressed/streaming MAN composition uses the native adapter from the preceding
checkpoint to patch final allocated header offsets only. Saved Build inspection
now qualifies the emitted pair against its recorded appearance witness.

NPC presets capture both supported own appearance and dialogue. Portable format
v3 binds the appearance witness to the script donor and owning import, retaining
the 512 KiB authored metadata bound. V1 donor-only and v2 text-only files retain
their existing formats/bounds. Transfer and placement reverify compatible pairs;
no retail script/model payload or runtime state is copied into the preset.

Offline evidence: 42 focused Python checks and five Node contracts pass. Actual
Inspector/Asset Details review, withdrawal, Apply, Undo/Redo, Save/reload, scene
and model reference checks passed; the 540px layout was inspected. Normal Build
`47edfdee85c4fdb2` contains exact model92/animation9 and the complete authored glyph
span, preserving script donor0012 and other drafts/imports. Retail witness0040
animation inspection and frame1 scene placement passed without history changes.
V3 capture/export and synthetic cross-project transfer/instantiation preserve both
bindings. Evidence is under `local-output/sdk-20260909/npc-appearance-editor-20261005/`.
No game was launched. Initial assignment does not prove script compatibility,
residency, eventual appearance or gameplay; those checks remain deferred.

## Independent NPC appearance native adapter - 2026-10-05

Added a source-qualified native adapter that keeps an NPC's script donor separate
from its initial model/animation witness. Requests identify an allocated draft and
a retail witness record; native numbers and bytes are not supplied by clients.
The existing MAN assignment validator checks local bank membership, compatible
object/channel counts and donor ownership. Only the selected clone's two initial
header bytes can change. Final record identities resolve offsets after all appends;
intermediate allocation offsets are not reused. Retail records, aliases, ambiguous
allocations, unsupported pairs and changed header preimages reject.

Focused synthetic checks cover two clones, later table growth, exact byte scope,
repeat/preimage rejection, malformed ownership, aliases and incompatible channels.
A retail town01 candidate changed model105/animation13 to qualified model92/
animation9 from donor0040 while retaining script donor0012 and authored dialogue.
Exactly two header bytes changed; all other bytes and the second clone remained
unchanged. Project state/history/files were preserved. Evidence is under
`local-output/sdk-20260909/npc-appearance-native-20261005/`.

This is native foundation work, not yet an editor feature or normal Build input.
Next: integrate an independent appearance binding into project commands, scene
preview/asset/animation references, persistence, presets and normal Build, then
verify the complete editor workflow. Runtime compatibility and gameplay remain
unverified; no game was launched. The full SDK goal remains active.

## Retain NPC dialogue in reusable presets - 2026-10-05

Capturing an NPC preset now freezes its supported own dialogue with the retail
donor, name and native-grid placement defaults. Later edits or deletion of the
capture NPC do not change the preset. Reviewed placement deep-copies those edits
into an independent new NPC, where normal dialogue authoring and Build apply.
Capture, transfer and placement reverify the text runs through the existing
source-qualified equal-span serializer; unknown/aliased runs, controls, oversized
text and a mismatched donor reject. Runtime state and other script edits remain
outside this snapshot.

NPC preset JSON v2 carries only source-bound preset metadata and user-authored
text edits, with a 512 KiB file bound. Donor-only NPC v1 and ordinary actor preset
files retain their 8 KiB bound and original format. A version/content mismatch
rejects. The editor displays the owned-run count and verifies that placement
retains the exact captured text. No retail script bytes or native packets are
included in the portable file.

Offline evidence: 16 focused Python checks and the NPC preset/file browser
contracts pass. A real two-project browser workflow captured text, downloaded
and uploaded v2 JSON, reviewed/imported a new library identity, passed Undo/Redo
and Save/reload, then reviewed scene placement and created an independent NPC.
Existing source drafts/imports and recipient scene entities remained unchanged.
The inspected 540px layout is readable. Normal Build `2e2e86485096975f` reads
back the complete authored glyph span including space padding. Evidence is under
`local-output/sdk-20260909/npc-dialogue-presets-20261005/`. No game was launched;
manual spawning, reachability and dialogue-layout acceptance remain deferred.

## Author dialogue independently for an NPC - 2026-10-05

NPC Inspector and registered Asset Details now offer **Edit NPC dialogue**.
The workspace freshly verifies the retail donor's supported plain-glyph runs,
shows retail and authored text separately, and reviews a complete NPC-local edit
set before Apply. Checked runs override this NPC only; unchecking restores retail
text. Shorter replacements are space-padded, longer text and control/substitution
edits reject. Existing decoder gates for unknown stops, aliases and menu ownership
remain intact. Static paths do not establish runtime dialogue reachability.

One reviewed command updates the authored NPC draft with one Undo step. Undo/Redo,
Save/Open, draft copies and authored-input freshness retain the NPC-local text.
Changing donor while text is retained rejects with an explicit clear-first message;
text-run identities cannot silently migrate to another donor. NPC presets still
capture donor/placement definitions; text presets remain a separate future feature.

Normal Build patches only the audited appended record, after allocation and before
other scene composition, using freshly verified source glyph preimages and bounded
equal-span offsets. Compressed and streaming MAN paths share the same adapter.
Retail donor records, other NPCs, record extents, controls and section layout remain
unchanged by these text edits. Build audits expose the NPC-owned text spans.

Offline evidence: 41 focused Python checks and four Node contract suites pass. Real editor
Review/Apply/Undo/Redo/Save workflows and inspected 540px layouts passed in private
format6 fixed-span and format7 relocated projects. Normal packages independently
read back exact NPC text; complete generated donor records match their prior
Builds exactly. Asset Details reopening shows the persisted own text; its action
row now wraps to keep buttons inside the dialog. Both source/generated
comparisons show 26 changed bytes including placement headers. Evidence is under
`local-output/sdk-20260909/npc-dialogue-20261005/`. No game was launched; spawning,
reachability, text layout and runtime behavior remain deferred manual acceptance.

## Compare saved NPC records with retail donors - 2026-10-05

The generated NPC script workspace now offers **Compare generated record with
retail donor**. Both records are freshly inspected against the current project,
verified source disc and intact saved Build receipt. The dialog compares exact
bytes at the same relative record offsets and retains separate retail and
generated MAN offsets, record hashes, lengths and script-entry offsets.

Changes before both script entries are labelled record header; other changes
are labelled script or remaining record bytes. Missing bytes are explicit, and
large differences are paginated in groups of 128. Script tails include opaque
and unvisited data. Matching bytes establish neither instruction equivalence
nor runtime spawning, scheduling or execution. Closing returns to the generated
record workspace with the selected NPC retained. Stale inputs and inconsistent
comparison counts, bytes, scopes or identities reject before rendering.

Offline evidence: focused Python and Node comparison, generated-record and
retail-source checks pass. Real browser comparison passed format6 fixed-span
and format7 relocated packages, including inspected 540px layouts. Both have
2 changed header bytes and 507 identical common bytes; their script tails match.
Retail MAN offset 8487 remains distinct from generated offsets 44648 and 44720.
Project history, authored inputs and every preexisting file remained unchanged;
no Save, Build or game launch occurred. Evidence is under
`local-output/sdk-20260909/npc-script-comparison-20261005/`. Manual gameplay
verification remains deferred; this milestone is read-only package evidence.

## Inspect NPC scripts emitted in saved Builds - 2026-10-05

NPC Inspector and Asset Details now offer **Inspect saved Build script...**.
Choose an intact saved package matching current authored inputs. The SDK verifies
the receipt/audit/manifest/archive and user-owned source disc, reconstructs the
emitted PROT from verified fixed-span overlays or relocation data, then reads the
actual generated MAN record by the audited NPC allocation index. Final table
spans are parsed from emitted bytes, never copied from intermediate append offsets.

The read-only workspace exposes generated dialogue, instruction navigation and
raw/record evidence with Build-scoped script identities. Retail donor inspection
remains separate. Stale inputs, wrong NPC/record/package identities, changed
payloads, ambiguous overlay spans and invalid record bounds reject. Package and
source-disc integrity do not establish runtime spawning, scheduling or execution.
The former **Inspect serialized candidate** label is corrected to **Inspect donor
append prototype**; prototype text now directs complete-project readiness to
Review Build rather than claiming that normal NPC Build is unavailable.

Offline evidence: 21 focused Python checks and Node generated/donor/Asset/NPC
Inspector contracts pass. Actual browser workflows passed both Inspector entries,
generated/retail separation, path navigation and inspected 540px layouts for a
format6 fixed-span package and a format7 relocated package. Stale-input receipts
reject. Final bounded payload reads and record/hash guards accept both actual
package responses. Generated offsets are44648 and 44720 respectively. Project,
history, Build input identity and preexisting files are unchanged. No new Build,
Save, game launch, install or disc export occurred. Evidence:
`local-output/sdk-20260909/npc-saved-build-script-20261005/` (`proof.json`,
`final-readback.json`, `fixed-540.png`, `relocated-540.png`). Gameplay remains deferred.

## NPC retail donor script inspection - 2026-10-05

Authored NPCs now expose **Inspect retail donor script...** in the NPC Inspector
and a registered **Inspect retail donor script** action in Asset Details. The SDK
qualifies the active draft/donor and freshly verifies the imported donor against
the user-owned disc. The read-only workspace shows decoded dialogue, searchable
instruction paths, flow overview, successor navigation, source spans, raw record
and explicit decoder stops. Unknown paths and branch reachability stay unknown.

The report captures full project source identity and exact draft/donor provenance;
stale or forged bindings and authoring/generated claims reject. Source offsets
belong to the imported donor, not allocated NPC code or a live actor. This view
adds no NPC script authoring or runtime execution claim. Donor authoring remains
separate from this retail-only inspection.

Offline: 20 focused Python checks and donor-script, Asset Inspector and NPC
Inspector Node contracts pass. The private retail browser passed both entry points,
exact source response, instruction navigation and retained NPC selection. The
540px layout was inspected. Donor0012 has 25 decoded instructions and16 dialogue
segments; its record SHA-256 is
`5063e5eb8bfd400fba142b0eabee28f50c46b900aa319ebdf86fd0b4eea73a65`.
Project document, Undo/Redo history, normal Build input identity and preexisting
files stayed unchanged. No commands, Save, Build, game launch, install or disc
export occurred. Evidence: `local-output/sdk-20260909/npc-donor-script-20261005/`
(`proof.json`, `browser.log`, `donor-script-540.png`). Gameplay remains deferred.
See [NPC donor script workflow](legaia-npc-donor-scripts.md).

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

## Repair saved selections after NPC deletion - 2026-10-05

Saved selections containing deleted NPCs now support **Replace with current
placements**. Select available placements in the saved scene, then replace the
membership. The set keeps its stable identity and name; one Undo restores its
previous members, including missing NPC references. The dialog identifies
unavailable NPCs and explains the repair path. Recall still rejects missing NPCs.

Replacement proves the original import and MAP binding before dropping members,
including removal of all scenery. New membership must be available in the owning
scene. Stale keys, source drift, empty/invalid replacements or a project change
during source proof reject before publication. Repair changes editor metadata only.

Validation: 16 focused scene/actor selection Python cases and both Node selection
suites passed. Checks cover source drift, stale keys, unavailable replacements,
metadata Undo/Redo, persistence and unchanged Build identity. Actual private Town01
browser checks passed the missing-member note, rejected Recall, same-ID/name repair,
Undo/Redo, Save/reload, disk reopen and successful repaired NPC focus. The 540px
message was inspected; no page errors occurred. Imports, game overrides, NPC data
and Build input identity stayed unchanged. Evidence:
`local-output/sdk-20260909/npc-selection-repair-20261005/proof.json`.
No game launch, Build, installation or full-disc export ran for this metadata-only
repair. Gameplay remains deferred; the full SDK goal stays active and work stays solo.
See [Saved scene selections](legaia-scene-selections.md).

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
See [NPC draft group workflow](legaia-npc-draft-groups.md).

## Saved scene selections include NPC drafts - 2026-10-05

**Saved scene selections** now stores 1-128 scene placements including authored
NPC drafts, imported actors and static decorations. Save an individual NPC from
its Inspector focus or capture a mixed selection. Recall focuses the NPC Inspector
for a single draft and restores mixed membership for the placement tool, including
when switching from another imported scene. Saved sets retain identities, so NPC
moves and renames do not restore old transforms or duplicate actors.

NPC-only sets require no MAP hash. Scenery membership retains fresh MAP source
proof, and NPC members must be available in the owning scene for Create/Replace/
Recall. Deleted NPC references remain portable metadata: Save/Open, Rename and
Delete still work, while Recall reports the unavailable member. Undoing deletion
restores recall. Existing source-bound actor/scenery sets remain compatible.

Validation: 17 focused Python cases, scene/actor selection Node checks and editor
syntax passed. Actual private Town01 browser checks passed mixed and NPC-only Save,
library Undo/Redo, Save/reload, NPC Inspector focus, cross-scene mixed recall, opening
the recalled mixed placement dialog, missing-NPC rejection and deletion Undo.
The 540px dialog was inspected; no page errors occurred. Imports, NPC content,
game overrides and Build input identity remained unchanged by selection metadata.
Evidence: `local-output/sdk-20260909/npc-saved-selections-20261005/proof.json`.
No game launch, Build, installation or full-disc export ran for this metadata-only
feature. Gameplay remains deferred and the full SDK goal remains active. Work is solo.
See [Saved scene selections](legaia-scene-selections.md).

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
selection sets and runtime placement semantics are separate work.

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
See [Mixed scene placements](legaia-scene-placement-groups.md).

## NPC preset file transfer — 2026-10-05

NPC presets now use metadata-only `legaia.npc-preset-file.v1` JSON in the shared
preset export/import workflow. The editor downloads `npc-preset.json`, reviews an
independent named library import, then places a new NPC through the separate
reviewed placement workflow. File/schema scope, exact source/components, capture
provenance, matching import hashes and the 8 KiB limit are checked. Export/import
freshly verify the owning retail scene against the project user's disc. Unknown
payload fields, changed sources and stale library reviews reject. Imported-actor
preset application remains separate.

Actual private two-project browser acceptance verifies download/upload, a new
library identity with retained provenance/defaults, changed-name review withdrawal,
library Undo/Redo, Save/reload and disk reopen, then detached scene inspection and
placement without the original capture draft. Source project document/history and
all file bytes stay unchanged; recipient imports and existing scene entities stay
unchanged. The 946-byte exported file contains metadata only. The 540px import
review is visually inspected with no page errors. Focused NPC/template-file Python
and Node checks and existing animation-preset regression checks pass.

The recipient's private normal format-6 Build uses the compressed reserved-span
route. Native MAN bytes exactly match preparation; descriptor decoded size and
new record 53 read back at X 2944 / Z 5632, model index 105, animation ID 13. Saved
receipt verification matches current inputs. Package SHA-256:
`5f3f409de8ac2e613f18602bb1771312bca52b00c2d2caf1dbcfd9adf3d3b5c6`.
Evidence: `local-output/sdk-20260909/npc-preset-transfer-20261005/proof.json`,
`normal-build-proof.json` and `transfer-review-540.png`. No game, install or full-disc
export occurred. Prefab inheritance, cross-scene remapping and runtime gameplay
acceptance remain unsupported or deferred. See [NPC presets](NPC_PRESETS.md).

## Reusable NPC draft presets — 2026-10-05

The preset library now supports a separate `npc-draft-preset-v1` scope. Select an
NPC draft and choose **NPC presets…** to capture its retail donor, authored name
and native X/Z defaults with owning scene, import hash and original draft provenance.
Review a new named instance at a chosen 64-unit-grid placement, compare the detached
scene with Current, then Apply. Capture and placement each have their own Undo step;
rename, delete, Save and reopen use the existing project template library. A preset
survives deletion of its original draft. Imported-actor template Apply rejects this
scope; cross-scene, stale, Live-mode and invalid placement requests fail closed.

Focused Python/Node checks and an actual private browser pass capture, changed-input
review withdrawal, exactly one scene addition, preservation of existing entities,
Apply, atomic Undo/Redo, Save/reload and disk reopen. Narrow review actions wrap
within the 540px viewport. A private normal format-7 Build contains all seven authored
NPC rows; the preset instance reads back from native MAN at X 3008 / Z 5632. Complete
native MAN bytes match preparation and saved receipt verification matches current
inputs. Package SHA-256:
`18ea1110520c28bdb321499dc8f466f868512be03b982736eddc8429c1e43adc`.
Evidence: `local-output/sdk-20260909/npc-presets-20261005/proof.json`,
`normal-build-proof.json` and `preset-review-540.png`.

This is project-local donor/placement reuse, not prefab inheritance or an authored
script/appearance snapshot. Shared asset edits remain project-wide. See the NPC
preset transfer milestone for file interchange; cross-scene remapping remains
unsupported. Runtime spawning,
scheduling, collision and visibility remain deferred to manual gameplay; no game,
install or full-disc export was performed. See [NPC presets](NPC_PRESETS.md).

## NPC animation frames at authored scene placement — 2026-10-05

**Inspect animation in scene** now targets the selected NPC draft when entered
through its donor animation Inspector. The donor remains the verified animation
source; the NPC becomes the explicit display target. Existing imported-actor
inspection retains its prior target selection. A dedicated adapter qualifies the
current scene source, unique authored entity, recorded donor/model and authored
X/Z placement before accepting an NPC target. Wrong source, model, donor, duplicate
entity or changed placement rejects the inspection.

The existing isolated geometry workflow changes only the target's display geometry
key. Authored/source position, sampled elevation, display position and model-to-scene
transform remain intact. NPC selection and framing synchronize with the inspection;
the scene bar uses its authored name. Frame changes retain the same NPC geometry
instance. Restore returns the qualified Current scene. This is display-only pose
inspection, not animation assignment, runtime playback or gameplay acceptance.

Focused NPC Inspector Node checks pass source/target/placement rejection. Actual
private browser with shared authored channels and a different authored donor
appearance verifies exact frame vertices, unchanged donor/all other entities,
retained authored transform, NPC selection, frame advancement and restoration.
The 540px viewport is visually inspected with no page errors. Project document,
history and every project file byte remain unchanged. Evidence:
`local-output/sdk-20260909/npc-animation-scene-target-20261005/proof.json` and
`npc-scene-540.png`. No Build, game launch, install or disc export occurred.

## NPC animation Inspector matches shared authored preview — 2026-10-05

The NPC animation button previously opened the imported donor clip even when the
Authored viewport showed shared authored animation channels. It now uses a
qualified SDK draft model reference and the current NPC pose kind: imported pose
opens the retail donor clip; authored pose opens shared authored channels. Labels
identify the representation. Unsupported/missing poses have no fallback action;
pending refresh, busy state and detached scene proposals cannot arm navigation.
The click rechecks source context and binding before opening the model dialog.

The retail donor model and clip owner remain explicit. The donor's authored
appearance is separate. `ModelRenderer.asset_id` already retained the retail
model; inspection corrected the initial suspected wrong-model diagnosis. This
change fixes the animation representation mismatch and strengthens binding checks,
without claiming an NPC runtime animation identity or an established idle stance.

Focused NPC Inspector and Asset Inspector Node checks pass source/pose coherence,
imported/authored channel choice, unknowns and mismatched donor/model rejection.
Actual private browser uses a verified donor appearance override (0105 to 0092)
and a native shared channel edit in `animation://town01/scene-anm/0012`. It opens
model 0105 with the correct donor owner and authored representation; its first
frame differs from the retail response. The 540px dialog passes with no page errors.
Project document, history and all file bytes remain unchanged during inspection.
Evidence: `local-output/sdk-20260909/npc-donor-animation-binding-20261005/proof.json`.
No Build, game launch, install or disc export occurred. Gameplay stays deferred.

## NPC recorded donor-model inspection — 2026-10-05

Authored NPC records and central project inventory entries now expose the SDK's
existing `draft_initial_model_assignment` reference. It retains source draft/name,
owning scene, model asset ID, retail donor ID and `runtime_binding=not_asserted`.
Unresolved donor model references remain null. The draft assignment uses the retail
donor independently of that donor's authored appearance.

NPC Asset Details shows **Recorded donor model** as a read-only SDK reference and
provides **Inspect recorded donor model** when model preview capability and a
coherent assignment are present. The adapter qualifies source/name/scene/donor,
assignment kind and layer before registering navigation; the editor checks the
current SDK reference again before opening the imported model view. The project
inventory adapter also rejects inconsistent model bindings. There is no runtime
residency/pose claim or property-writing action.

Validation: 22 focused Python Inspector/inventory cases pass, including retail
donor separation and explicit unknowns. Asset Inspector and project inventory Node
checks pass binding, malformed-reference, capability and unresolved-action checks.
Actual private browser matches SDK fields in active/project scopes and opens the
exact recorded model response; 540px layout passes, with no page errors. Document,
Undo/Redo and all project file bytes remain unchanged. Evidence:
`local-output/sdk-20260909/npc-donor-model-navigation-20261005/proof.json`.
No Build, game launch, install or disc export was performed. Gameplay stays deferred.

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

## NPC drafts in the central project Asset Database — 2026-10-05

The SDK project inventory now registers each validated NPC draft as an explicitly
`authored` actor entry. Its stable authored UUID, exact name, donor binding and
X/Z placement remain project metadata. The single owning-scene membership carries
that import's hash as context; it has no retail source record or decoded-catalog
key. Imported/catalog records cannot supply authored NPC identities. Existing
source freshness and asset/membership/metadata budgets cover these entries.

The browser retains imported and authored distinctions, filters by owning scene,
and opens the typed NPC Asset Details and Inspector through existing selection.
The membership control says **Authored NPC owning scene** and explains that its
import hash is context, not a retail origin. Project scope is labeled **Project
resources**. This does not establish runtime residency, spawning or visibility.

Focused validation: nine SDK inventory cases plus two HTTP cases pass; Node
checks cover authored membership, donor/scene/coordinate coherence, source
substitution rejection and scene filtering. Actual private browser checks verify
indexed NPC membership, exact SDK fields, selection and the 540px layout, with no
page errors or project/document/history/file changes. Evidence is under
`local-output/sdk-20260909/npc-project-assets-20261005/`. No Build, game launch,
install or disc export was needed. Manual gameplay verification remains deferred.

## Authored NPC Asset Details — 2026-10-05

NPC draft cards in active-scene and project scopes now use the SDK-owned
`AssetNpcDraft` descriptor. It presents the authored identity, name, project scene,
retail donor binding and authored X/Z coordinates with Project/Authored state
badges. Imported actor cards retain their existing descriptor. The separate
`authored_asset_inspectors` mapping preserves imported asset contracts.

The adapter rejects inconsistent draft identities, scene/name/donor records and
invalid native-grid coordinates before mounting the descriptor. Its only registered
action, **Select NPC draft**, uses existing scene navigation and opens the draft
Inspector. This exposes current SDK authored records; it does not add imported
Asset Database memberships or establish runtime spawning/visibility.

Validation: twelve Python Inspector schema cases and the expanded Node asset
Inspector checks pass. Actual private browser checks match every SDK property in
both scopes, select the correct NPC Inspector and pass at 540px with no page errors.
Project document, Undo/Redo and all project file bytes remain unchanged. Evidence:
`local-output/sdk-20260909/npc-draft-asset-inspector-20261005/proof.json` and
`asset-540.png`. No Build, game launch, install or disc export was performed;
manual gameplay verification remains deferred.

## NPC draft Inspector schema checkpoint — 2026-10-05

Eleven Python Inspector schema cases pass read-only contracts, authored X/Z paths,
separate unresolved placement Y/derived preview elevation, no fallback paths,
donor source metadata and detached schema instances. New NPC rendering and prior
environment Node checks pass escaping, no input generation, authored versus preview
values, unknowns and pending/source-during-proposal/unavailable labels. Both editor
module syntax checks pass. Actual private browser matches every SDK property,
retains specialized controls, verifies current snapshot and controlled stale/proposal
context, Retail missing-preview and Authored return. The540px Inspector screenshot
is inspected, with no page errors. All project document/history/files stay unchanged;
only scene-preview reads occur, with no authoring/Save/Build/Run/game/install/export.
Proof: `local-output/sdk-20260909/npc-draft-inspector-schema-20261005/proof.json`.
Campaign follow-up: live pending-refresh/close races, changed donor while geometry
loads, unavailable geometry and source surface, all pose kinds and broader component
migration. Existing gameplay spawning/visibility/collision gates remain separate.

## NPC draft layout/normal-package checkpoint — 2026-10-05

Ten focused Python group/repetition cases and expanded Node contracts pass selected
anchor, exact layout fields, command type binding, preserved other axis, nearest
64-unit distribution/endpoints, insufficient span, changed-count/no-op handling,
atomic history and persistence. Existing offset/detached scene guards remain.
Module syntax passes. Actual private HTTP/browser passes three-member distribution,
Proposed/Current scene qualification, operation-change withdrawal, Undo/Redo, Z
alignment, Save/reload and independent disk reopen. Both layouts use separate batch
history entries; imported/donor metadata and unselected drafts remain unchanged.
The540px layout is inspected and no page errors occur.

Private ordinary Build review includes six drafts and reports ready. Format7 normal
package uses compressed NPC capacity-growth relocation; saved-package verification
matches current inputs. Full decoded final MAN equals the prepared candidate byte
for byte and all appended positions match authored state. Build leaves project
metadata/history and preexisting files unchanged. No gameplay, installation or disc
export. Proof: `local-output/sdk-20260909/npc-draft-layout-20261005/{proof,normal-build-proof}.json`.
Campaign follow-up: Z distribution, X alignment, all tie orders, endpoint span/count
edges, late/closed/stale anchor responses, mixed donors/scenes and runtime spawning,
scheduling, visibility, collision and total actor-pool headroom acceptance.

## NPC draft group movement checkpoint — 2026-10-05

Eight focused Python group/repetition cases pass detached full-group review,
canonical selection order, exact offsets, invalid last target, stale/tampered
review, Live rejection, zero-delta no-op, one Undo entry and Save/Open. New Node
contracts pass source/request/target binding, detached copies, unchanged unselected
scene content, donor/model/display preservation and malformed response rejection.
Existing repetition Node and both editor module syntax checks pass.

Actual private HTTP/browser passes selected subset movement, visible/search
selection, detached scene qualification, no preview mutation, zero delta/bounds
rejection, Apply/Undo/Redo/Save/reload and independent disk reopen. Initial shared-
prefix name search was corrected to stable ID. Narrow clipped actions and cramped
table cells were fixed; the read-only recheck preserves all document/history/files.
Final540px screenshot inspected, no page errors. Native prepared PROT readback
matches six draft positions, including two moved members, and final MAN/PROT hashes;
all project files stay unchanged during native preparation/readback. Initial copied
helper path was corrected to this fixture. No normal Build, gameplay or disc export.
Proof: `local-output/sdk-20260909/npc-draft-group-20261005/{proof,native-proof}.json`.
Campaign follow-up: close/abort races, fresh server project switches, maximum count,
source reimport/other-scene donors, source terrain changes, normal-package routes
and runtime visibility/collision/scheduling/actor-pool headroom acceptance.

## NPC grid repetition checkpoint — 2026-10-05

Twelve focused Python repetition/review cases and expanded Node coordinate checks
pass. Cover row-major grid with negative spacing, distinct pattern binding, stale
columns rejection, project-wide count limit, grid/bounds validation, single-row
zero Z spacing, detached preview, one batch history entry and persistence.
Actual private HTTP/browser review and detached scene pass exact grid coordinates;
line omits optional columns and keeps legacy placement. Pattern changes withdraw
Apply, multi-row zero Z rejects, preview creates no drafts, and Apply/Undo/Redo/
Save/reload plus independent disk reopen pass. No page errors; 540px inspected.
Native prepared PROT reopen/decompression matches all six draft placements and
final MAN hash, with partition-one count59 and one growth sector. Original donor
binding/imports stay unchanged. No normal Build, game, install or disc export.
Proof: `local-output/sdk-20260909/npc-grid-repetition-20261005/proof.json` and
`native-proof.json` in the same directory. Initial out-of-bounds fixtures and
logical-versus-physical table-offset assumptions were corrected before acceptance.
Campaign follow-up: grid columns/count edges, all four spacing sign combinations,
close during scene inspection, multi-scene drafts, normal-package routes and
runtime spawning, scheduling, visibility, collision and actor-pool total headroom.

## NPC Build scope presentation checkpoint — 2026-10-05

Ten focused Python draft repetition/review/HTTP cases, both existing Node contracts
and repetition module syntax pass. Current builder scope is shared by repetition
and experimental review: qualified compressed fixed-span/capacity-growth and raw
streaming relocation routes retain existing gates. Experimental review explicitly
says normal Build readiness is not assessed here; its legacy false flag remains.
Actual SDK scope notes equal visible repetition notes, malformed notes clear the
report and disable Apply, and the 540px dialog is inspected. Close cleanup passes,
no page errors occur, and project document/history/files remain unchanged after
fixture setup. No Build, gameplay, install or full-disc export runs.
Proof: `local-output/sdk-20260909/npc-build-scope-notes-20261005/proof.json`.
This corrects author-facing scope only; it adds no serializer or runtime support.
Campaign follow-up: candidate variants and full-project Review Build readiness,
plus runtime spawning/scheduling and actor-pool headroom remain separate checks.

## General saved-Build freshness checkpoint — 2026-10-05

Expanded general/asset Node Build-history contracts and module syntax pass.
Receipt binding covers archive/disc hashes, kind, report count and current-input
flag agreement with the receipt key. Actual private saved package verification
passes; controlled stale `/api/state` responses withdraw verification tables and
reject history listing before rendering entries, even with unchanged local cache.
A forged returned receipt hash rejects against the selected list entry after a
valid server-state check. Close removes the dialog, 540px failure screenshot is
inspected and no page errors occur. Project document/history/files stay unchanged;
no new Build, Command/Save/Run, game, install or full-disc export occurs.
Proof: `local-output/sdk-20260909/build-history-freshness-20261005/proof.json`.
Campaign follow-up: compare responses during server changes, server path switches,
GET-state failures, close during freshness reads, additional input receipts and
package replacement between list/verify. This fixes presentation freshness and
receipt selection binding; native package serialization and runtime are unchanged.

## Asset saved-Build evidence checkpoint — 2026-10-05

Six focused Python Build-history integrity cases, new asset matching/receipt
Node contracts, existing Build-history decoder checks and module syntax pass.
Cover exact direct versus owner IDs, full nested ledger retention, detached data,
current versus historical inputs, receipt/hash/kind/count mismatch, malformed
identity and no-record semantics. Private normal Town01 Build and actual saved
package verification pass. Asset Details inspection equals SDK verification and
retains all 130 model coordinate words. Controlled DTO UI checks cover complete
301-row paging, removed callback inertia, fresh-server source-key withdrawal and
close cleanup. Pending Verify is disabled and 540px actions/layout are inspected.
The initial harness used hidden `innerText`; corrected full record readback passes.
Inspection leaves project document/history/files unchanged and creates no output;
fixture setup performs the private normal Build. No game or install ran.
Proof: `local-output/sdk-20260909/asset-build-records-20261005/proof.json`.
Campaign follow-up: multiple real receipts, all asset families, owner-only records,
zero matches, invalid/incomplete/truncated histories, selecting another Build,
closing during verification, stale source membership and package file tampering
between list/verify. Shared-ID membership and source-disc/native gameplay integrity
are separate evidence gates; absence from an edit audit is not absence from a game.

## Shared scenery Inspector layout checkpoint — 2026-10-05

Three focused Node Inspector checks and module syntax pass. Actual private
Town01 browser verifies seven scenery section toggles, all header arrows/Home/End,
collapse/expand all, retained unsubmitted individual-transform input values,
same-instance collapsed state and focused-header restoration, detached old header/
tool callback rejection, layout retention across scenery, actor filter/layout
regression and the actual controller's project-boundary reset. Every header fits
at 540px and the Inspector-tab screenshot is inspected. Project document, history
and files stay unchanged; only preview/selection requests occur, with no page
errors or authoring/Save/Build/Run. Evidence:
`local-output/sdk-20260909/scenery-inspector-sections-20261005/proof.json`.
Campaign follow-up: mixed actor/scenery rerenders, unavailable scenery snapshots,
project/source/representation changes, maximum evidence and focused form inputs.
Collapsing retains form nodes; selection/source rerenders retain existing draft
behavior. This is session layout, with no persistence or native byte changes.
No manual gameplay gate is added by this display feature.

## SDK scenery Inspector checkpoint — 2026-10-05

12 focused Python inspector-schema/environment-project cases, scenery adapter
Node checks and module syntax pass. Cover detached read-only metadata definitions,
separate Retail/Current paths, missing Current values without invented inheritance,
escaping, no authoring controls and explicit pending-preview status. Actual private
Town01 browser checks all properties of the four SDK sections, authored placement
versus imported placement, matching GPU translation, Frame and existing shared/
individual source-qualified controls, root Inspector pending-warning withdrawal,
Retail/Authored reload with reselection and the 540px Inspector-tab layout.
Project document, history and files remain unchanged; no page errors or
Command/Save/Build/Run requests. Evidence:
`local-output/sdk-20260909/environment-inspector-schema-20261005/proof.json`.
Earlier browser harness failures remain recorded; final fresh fixture passes.
Campaign follow-up: ground/unrenderable instances, missing source fields, shared
record compensation, individual rotation, source withdrawal during authoring,
maximum evidence size and future schema upgrades. Existing Build/native-byte
placement checks remain separate; no native serialization path changed here.
Runtime transforms, visibility and collision still need deferred gameplay checks.

## Selected asset evidence download checkpoint — 2026-10-05

Focused export and asset-inspector Node checks, nine Python inspector-schema
cases and module syntax pass. Cover complete selected records, separate authored
metadata, multiple membership retention, UTF-8 size bounds, unsupported/cyclic
metadata, busy/pending duplicate suppression, local/server source withdrawal and
closed details during pending fetch. Private Town01 browser downloads actual
active and project-scope model records; both JSON files equal the selected records,
with source hashes and authored settings retained. Fresh-server source mismatch
blocks download; 540px button bounds and screenshot pass. Project document,
history and files remain unchanged. No authoring, Save, Build or Run requests.
Proof: `local-output/sdk-20260909/asset-record-evidence-20261005/proof.json`.
The first attempt failed due to a missing static route; its log is retained and
the route fix passed a fresh-fixture browser run. Campaign follow-up: every asset
family, multiple actual shared-scene memberships, unavailable source records,
source replacement during pending fetch and near-budget project metadata. This
is catalog evidence export; native payload integrity and gameplay are not claimed.

## Mixed placement mirror checkpoint — 2026-10-05

28 focused Python layout/group/HTTP cases, expanded mixed-placement Node checks and
module syntax pass. Cover both native reflection axes, off-grid fixed anchor, final
actor half rounding, unchanged other-axis metadata, atomic invalid/stale requests,
native bounds/offset overflow, no-op redo and forged/safe arithmetic. Actual private
Town01 browser checks both axes, operation withdrawal, Current/Proposed GPU matrices
with height/rotation held, Return and one Apply at 540px. Undo/Redo, Save/Open and
normal Build pass with full MAP directory/ZIP and independent MAN placement/opaque
readback; the unchanged actor axis remains unauthored. Screenshot inspected, no page
errors. Proof: `local-output/sdk-20260909/mixed-placement-mirror-20261005/proof.json`.
Campaign follow-up: maximum mixed selections, coincident results, both anchor types,
repeated reflection, boundary coordinates, source withdrawal and shared MAP ownership.
Model geometry/facing/rotations and collision are retained, not reflected; script-driven
placement and collision consistency remain separate manual gates. No game,
installation or full-disc export ran.

## Native-precision mixed rotation checkpoint — 2026-10-05

25 focused Python layout/group/HTTP cases, mixed-placement Node checks and module
syntax pass. Cover exact quarter turns, integer/off-grid anchors, final actor half
rounding, fixed anchor, native bounds, scenery overflow, no-op/history, stale/old
algorithm tokens and forged/safe arithmetic. Actual private Town01 browser checks
-90/+90/180 about an off-grid decoration, operation withdrawal, Current/Proposed GPU
matrices with height/rotation held, Return and 540px one Apply. Undo/Redo, Save/Open and
normal Build pass, with complete MAP directory/ZIP and independent native MAN placement
and opaque-byte readback. Screenshot inspected, no page errors. Proof:
`local-output/sdk-20260909/mixed-placement-native-rotation-20261005/proof.json`.
Campaign follow-up: maximum selections, extreme source/offset bounds, rounding
coincidences, repeated turns and actor anchors with native integer scenery distances.
Rotation changes positions only; actor facing, scenery rotation, collision consistency
and script-driven runtime placement remain separate manual gates. No game,
installation or full-disc export ran.

## Saved scene visibility/grid checkpoint — 2026-10-05

Nine focused Python view cases, scene-view/camera Node suites and both editor syntax
checks pass. Cover typed visibility/grid, canonical IDs, imported actor membership,
source-qualified static cells, MAP hash mismatch, atomic rejection, history/persistence
and legacy views. Private Town01 browser saves a manually hidden actor and isolated
static decoration; actual renderer display checks camera/grid/visibility recall and
Restore preserving manual hiding. Metadata Undo/Redo, Save/Open and 540px recall from
Retail to Authored after preview reload pass, with no page errors and unchanged imported,
authored-game, normal-Build and scene-preview keys. Screenshot inspected. Proof:
`local-output/sdk-20260909/saved-scene-visibility-20261005/proof.json`.
Campaign follow-up: maximum hidden selections, ground-only binding, cross-scene recall,
closed/stale context during preview loading, unavailable source meshes, shared model
hiding and source replacement. New NPC draft visibility remains unsupported. This is
editor metadata; runtime appearance/collision parity remains a separate manual gate.
No package, game, installation or full-disc export ran.

## Complete Build-review download checkpoint — 2026-10-05

Ordinary/NPC Build-review Node suites and module syntax pass. Cover all 301 changes
beyond the display cap, all native/other records, blocked and null assessments, v2
candidate coverage, stale/source/no-output claims and a 32 MiB UTF-8 limit. Actual
private retail browser downloads match the entire accepted response at desktop/540px,
including 130 coordinate records, with pending disable and mounted UI stale rejection.
Narrow action bounds, screenshot, close disposal, no page errors and unchanged project,
history and all fixture files pass. Proof:
`local-output/sdk-20260909/build-review-download-20261005/proof.json`.
Campaign follow-up: near-limit reports, actual server serialization blockers, project
replacement during review and repeated downloads/close while another operation is busy.
The export is metadata only; packaging and gameplay are separate gates. No game,
installation, package or full-disc export ran.

## Build-review native coordinate checkpoint — 2026-10-05

Nine focused Python Build-review/model-growth/normal-package cases, ordinary and
NPC Build-review Node suites, and module syntax pass. Cover source/no-output guards,
relocation ledger retention, independent signed native-word readback, deterministic
normal package output, immutable 128-row pages and malformed ledger rejection.
Actual private Town01 browser reads 130 native changes across both pages, checks
paging bounds and close disposal, and preserves project/history/all fixture files.
The 540px screenshot is inspected; no page errors or authoring/Save/Build/Run requests.
Evidence: `local-output/sdk-20260909/build-review-model-coordinates-20261005/proof.json`.
Campaign follow-up: maximum ledger size, normal-coordinate records, mixed primitive
and removal records, authored-input withdrawal while paging, and topology layouts.
Topology bindings without ledgers remain hashes/relocation evidence only. Synthetic
normal packages were tested; this retail browser check writes no package. Gameplay
acceptance remains manual; no game, installation or full-disc export ran.

## Model vertex distribution checkpoint — 2026-10-05

Six focused Python distribution/alignment cases cover signed extrema, nearest spacing,
coordinate/index ties, endpoint/other-word preservation, stale/invalid HTTP requests,
preview without mutation, no-op/history and allocated vector ownership. Expanded Node
checks cover immutable local geometry and forged operation/value/source/full-preview
replies; both changed editor-module syntax checks pass. Actual Town01 browser exercises
locks, no-op/Discard, Current/Draft, single/all-instance scene comparison, Return/Restore,
540px Apply and Undo/Redo with no page errors. Save/Open and normal Build pass, with
complete decoded carrier directory/ZIP readback and a single changed model byte.
Evidence: `local-output/sdk-20260909/vertex-distribution-20261005/proof.json`.
Campaign follow-up: maximum selections, multiple objects and authored topology layouts,
all three source axes, coincident results, source withdrawal and history across reopening.
Normals/collision are retained; gameplay appearance remains a separate manual gate.
No game, installation or full-disc export ran.

## Native-precision mixed placement scale checkpoint — 2026-10-05

18 focused Python layout/group cases, expanded Node DTO checks and module syntax pass.
The earlier four HTTP checks passed at the grid-only checkpoint; this checkpoint's
actual retail browser exercises the layout-review/command routes with an off-grid
anchor. Coverage includes signed half-away rounding at native actor/decor precision,
100-percent identity, 1–1000 integer limits, actor native bounds, scenery signed-offset
overflow, exact operation qualification, atomic rejection/history and persistence.
Actual Town01 browser checks 50/100/175 percent, fixed off-grid anchor, Current/Proposed
GPU matrices, withdrawal/Return, one Apply and all action bounds at 540px. Undo/Redo,
Save/Open and normal Build pass with independent MAN placement/opaque-byte checks,
complete MAP readback and ZIP integrity. Proof:
`local-output/sdk-20260909/mixed-placement-native-scale-20261005/proof.json`.
Campaign follow-up: 128 placements, percentage extremes, coincident rounding results,
source replacement during review, mixed descriptor ownership and repeated history.
Runtime movement, collision consistency and gameplay appearance remain manual gates.
No game, installation or full-disc export ran.

## Asset-reference download checkpoint — 2026-10-05

Focused Node checks cover full Active/Project JSON round trips, exact source/root/scope
qualification, input immutability, safe bounded filenames and the 32 MiB UTF-8 budget.
Actual private retail browser checks exercise both downloads while a zero-match filter
is active, pending-discovery disable, decoder readback, dialog disposal and 540px button
reachability. Document/history/files and project/scene/selection stay unchanged, with no
authoring, Save, Build or Run. Proof:
`local-output/sdk-20260909/asset-reference-download-20261005/proof.json`.
Campaign follow-up: withdraw source context while open, busy transitions, failed/aborted
project discovery, close during discovery, all resource kinds and maximum-sized reports.
Saved references do not establish runtime use or gameplay acceptance.

## Retained project provenance search checkpoint — 2026-10-05

Focused Node checks cover variant names/aliases, import/catalog hashes, claim/evidence
metadata, positive/excluded fields and immutable chosen-source qualification. Eight
existing project-source Python cases and both modified editor syntax checks pass.
Actual three-scene retail browser proof reproduces the prior module's missing hash,
finds a shared asset by nonchosen Map01 provenance, keeps chosen Dolk2 in Details and
checks exclusions/540px UI with unchanged document/history/files and no authoring,
Save, Build or Run. Private proof:
`local-output/sdk-20260909/project-provenance-search-20261005/proof.json`.
Campaign follow-up: all resource kinds, absent catalogs, 64 memberships, alternate source
scene filters, long/quoted aliases and source-refresh withdrawal. Search metadata is not
runtime use or a joined cross-membership binding; gameplay acceptance stays separate.


## Inspector property-category checkpoint — 2026-10-05

Focused Node checks cover category/query/actual authored-identity composition, empty
categories and immutable inputs; component state/reference suites and syntax also pass.
Actual retail browser evidence covers exact visible IDs, zero search results, category
retention across two actors, Reset, asset navigation, 540px layout, collapse/keyboard
restoration and unchanged document/history/files with zero authoring/Save/Build/Run.
Private proof: `local-output/sdk-20260909/inspector-property-category-20261005/proof.json`.
Campaign follow-up: an absent remembered category, translated/long labels, unregistered
components, stale detached filter controls and alternate project/mode refresh. Category
labels do not establish actual authored overrides or live observation; gameplay remains
deferred separately.


## Inspector property-state checkpoint — 2026-10-05

Focused checks cover catalog completeness/detachment/no capabilities, layer ownership,
precise authored workflow, unknown/malformed/escaped state labels, unknown/false values,
unsupported Y Build status and unchanged command/action/reference eligibility. Actual
retail browser proof covers actor/asset labels against the SDK, reference navigation,
540px legibility, collapse/keyboard restore and unchanged document/history/files with
zero authoring/Save/Build/Run requests. Private evidence:
`local-output/sdk-20260909/inspector-property-states-20261005/proof.json`.
Campaign follow-up: all registered component/asset inspectors, empty inherited states,
localized/long labels, mode/source refresh and screen-reader explanation. Real live
capture freshness/identity remains in the deferred runtime acceptance work, not proven
by a property-state presentation label.


## Mixed actor/scenery position rotation checkpoint — 2026-10-05

Focused development checks completed: -1/+1/2 exact quarter turns, actor and decoration
anchors, fixed pivot, invalid/bool/float/extra fields, off-grid anchor, native actor bound
rejection, stale Apply, preserved Y/rotation/shared/unselected data, no-op redo, one history
step and Save/Open. Existing offset/layout/reset and Node proposal-qualification checks
pass. Private retail browser/native package proof:
`local-output/sdk-20260909/mixed-placement-rotation-20261005/proof.json`.
All three turns, input withdrawal, Current/Proposed matrices, Return, one Apply, full MAP
readback and independent MAN coordinates/opaque preservation passed; no game ran.

Campaign follow-up: mixed selections up to 128, signed MAP/capacity boundaries, source and
selection changes during pending rotation, narrow viewport accessibility and exact native
readback for all turns. Deferred gameplay must check visibility, facing retained as
reviewed, collision and script-owned placement/lifecycle in the produced runtime.


## Mixed placement Retail reset checks

- Restore exact Retail X/Z for every selected actor/static decoration; clear selected
  actor X/Z overrides, prune empty containers and preserve height/facing/other components.
- Qualify Current authored-axis witnesses; distinguish coordinate changes from redundant
  override clearing. A second reset is a no-op and preserves history/redo/dirty state.
- Preserve shared scenery edits, selected Y/rotation and unselected instances; use
  per-instance compensation for source positions when shared transforms remain authored.
- Recover invalid off-grid integer actor coordinates through a valid source candidate;
  reject extra reset fields, stale sources and forged authored-axis reports.
- Verify readonly review/scene Return, one Apply/history, Undo/Redo, Save/Open, exact MAN
  source positions and full MAP Build directory/ZIP readback with unselected edits intact.
- Keep game visibility, collision and gameplay acceptance separate and deferred.

## Mixed scene placement layout checks

- Align X/Z to a selected actor/decoration anchor; require the 64-unit actor grid.
- Distribute grid-aligned mixed coordinates with fixed endpoints, nearest spacing,
  upward half ties and stable-ID ordering for equal positions; reject insufficient span.
- Validate all actor bounds, static descriptor ranges/capacity and complete merged MAP
  bindings before an atomic Apply; preserve unselected axes/components/shared edits.
- Qualify exact operation/selection/source and arithmetic; mode/anchor changes withdraw
  review. Layout scene inspection holds height/rotation and has no shared-offset handles.
- Compare Current/Proposed GPU matrices and Return; verify readonly files before Apply,
  one Undo/Redo step, no-op, Save/Open and full MAP plus independent MAN Build readback.
- Keep runtime height, collision, script behavior and gameplay acceptance deferred.

## Retained animation assignment-user navigation checks

- List all authored initial users with stable actor identities; keep capture provenance
  and runtime playback distinct. Unassigned and retired clips show an empty state.
- Match registered users to exact Current retained record/hash/model components and
  effective initial-animation identities; reject missing/duplicate/extra/forged users.
- Guard source/project/scene changes, busy actions and pending previews. Close aborts
  a pending preview without selecting a user or publishing an authored change.
- Navigate to each listed actor through normal selection, frame and synchronize the
  Hierarchy/Inspector; preserve document, history, files, mode and scene.
- Keep every action reachable at desktop and 540px widths; long clip/source IDs wrap.
- No Build/Save/game request is needed for this readonly Inspector workflow.

## Selected vertex group rotation checks

- Compare native/browser X/Y/Z turns -90/+90/180 about source origin and group bounds
  center, including half-unit pivot rounding and positive-Y-down conventions.
- Reject invalid axis/turn/pivot, booleans, duplicate/out-of-range rows, stale source
  hashes and signed16 overflow atomically. A centered single-row turn is a no-op.
- Preserve other vertices, stored normals, opaque padding, packets and allocated ownership.
- Check staging, Discard, locks, layers, qualified scene Current/Proposed, Return/Restore
  and all instances without project/file mutation before explicit Apply.
- Verify one history step, refreshed Current, Undo/Redo, Save/Open and normal Build;
  independently decode directory and ZIP payloads to the complete expected section.
- Defer game appearance/lighting acceptance; native byte preservation is not gameplay proof.

## Selected vertex group scaling checks

- Compare browser and native candidate at origin/bounds-center pivots, including
  negative and half-unit rounding,100% no-op and signed16 overflow rejection.
- Reject duplicate/out-of-range indices, booleans, invalid percent/pivot and stale hash.
- Preserve unselected words, normals, packet topology and allocated row ownership.
- Stage/Discard, layer comparison, selection/history locks, scene Return/Restore and
  all-instance inspection must preserve a readonly exact draft before explicit Apply.
- Verify one project history entry, refreshed Current, Undo/Redo, Save/Open and normal
  Build; independently decode directory/ZIP payloads to the complete expected section.
- Keep manual game appearance/lighting acceptance separate from source byte readback.

## Retained asset-to-selected-actor assignment checks

- Select an imported actor distinct from the capture owner and open an active clip.
- Verify exact asset scope, explicit target ID and source row qualification; block
  retired clips, missing/non-imported target, Live mode and missing capability.
- Review an incompatible target: report the captured-model/retargeting blocker without
  a command. Review a compatible target and verify source/native-selector witnesses.
- Preview the proposed target initial pose and return to reviewed assignment; Apply
  exactly once. Preserve target selection, imports, capture owner and retained ledger.
- Verify fresh assigned-actor metadata, Undo/Redo, Save/Open and normal Build readback.
- Exercise target/source changes and prevent asset assignment views from issuing
  lifecycle or Clear commands. Game suitability/playback acceptance remains manual.

## Direct retained asset lifecycle checks

- Open exact assigned, unassigned and retired assets with unrelated actor selected.
- Verify single-record identity/hash/owner/model/count/status qualification; mismatched
  library data must never publish actionable controls.
- Verify asset lifecycle view hides and guards actor-assignment actions.
- Preview and Review stay readonly; assigned retirement reports its reference blocker
  without clearing an actor. Retire unassigned and restore retired through exact Apply.
- Verify automatic catalog status, stable UUID/capture hash, imports/selection unchanged,
  two atomic commands, Undo/Redo, Save/Open and normal Build/native readback.
- Exercise stale source, late result, close, Live and capability handoff guards.
- Retain manual game appearance/playback acceptance separately.

## Direct retained asset GLB workflow checks

- Open assigned and retired animation assets without selecting their capture actor.
- Prepare explicit-rate export and verify both downloads against the bound response.
- Select changed rigid-channel GLB and original binding; Review and pose preview
  remain readonly. Closing preview returns to the reviewed replacement editor.
- Apply exactly once; verify stable UUID, new hash, atomic assignment witnesses,
  preserved retirement, fresh resource catalog and unchanged retail imports.
- Verify Undo/Redo, Save/Open and normal private Build readback.
- Reject busy/stale source handoffs, Live mode, missing capability and stale bindings.
- Defer game appearance/playback acceptance to manual gameplay verification.

## Direct retained asset editing - 2026-10-05

Open an assigned and retired clip from the Asset Database with a different actor
selected. Verify source options finish loading before interacting, native axis
Review, proposed-pose preview/return, exact Apply, unchanged actor selection and
source-qualified automatic resource refresh. Require stable IDs, changed record
hashes, updated assignment hashes, unchanged retirement/imported provenance and
one atomic command per Apply. Cover Undo/Redo, Save/Open and normal package output.
Check Edit/source-scene/capability guards, current project/source ownership and
pending/disposed contexts. Actor-library selection lifetime must remain unchanged.
Runtime appearance and timing remain separate deferred acceptance.


## Retained animation Asset Database workflow - 2026-10-05

Discover assigned, unassigned and retired captures in active/Project catalogs;
require stable authored identity, source scene, exact capture witnesses/counts and
honest active/runtime distinctions. Browse Animations and Authored assets; open
all three kinds, inspect provenance, captured model/actor navigation, and preview
saved frames in the normal model viewer. Retired inspection must never activate a
record or assign a native slot. Check captured-model edges and navigable registered
clip rows separately from active assignment native/bank evidence. Discovery and
preview must preserve document/history/files/mode/scene. Cover stale source, wrong
identity/model, extra/malformed HTTP and metadata fields, closed/pending dialogs,
changed project context and frame/channel bounds. Gameplay playback remains a
separate deferred acceptance requirement.


## Retained initial animation references - 2026-10-05

Require original decoded initial references to remain, with retained assignments
replacing only the effective inherited relationship. Check actor -> retained clip
-> captured model and inverse queries in active/Project scopes; unavailable scene
catalogs must not assert retained proof. Bind exact ledger/record/native bank and
assignment hashes, owner/model identities and current resolved native slot/selector.
Cover malformed hashes, cross-scene/canonical owners, wrong layers, extra fields,
selector/frame/channel bounds, shared model IDs and detached output. Standalone
retained navigation remains unavailable; the actor Inspector manages/previews it.
Clear must restore inheritance; Undo and Save/Open must restore retained evidence.
Queries in Edit and observation contexts must preserve document, history, files,
active scene and mode. Browser filters/provenance must not issue authoring, Build,
Save or game requests. This feature does not accept gameplay playback.


## Project script bookmark navigation - 2026-10-05

Cover all-scene and scene-filtered catalogs, token search including padded/unpadded
hex offsets and source hashes, empty catalogs, duplicate/invalid IDs, detached rows
and size/source bounds. Exercise same-scene and cross-scene actor/P2 open routes;
require exact original record qualification before selection focus. Changed source
must expose an error with no focused row or stale report/controls. Test changed
catalog/project keys, pending/busy dispatch and closed/disposed dialogs. Compare the
complete document, history, Authored files and Build key after a roundtrip. This
navigation changes active scene/selection context; it must issue no authoring,
history, Build or Save commands. Native map01/town01 actor/P2 and wrong-hash cases,
focused JavaScript guards and20 neighboring Python regressions passed. Screenshots
inspected; private proof: `local-output/sdk-20260909/project-script-bookmarks-20261005/`.
No game launch or new gameplay acceptance is needed for this navigation feature.


## Saved script bookmark regression coverage - 2026-10-05

Exercise original instruction and dialogue boundaries, actor and partition-two
owners, exact record/import hashes, stale review keys, bool/noninteger/out-of-range
PCs, unknown and ambiguous offsets, duplicate names, quota and Edit mode. Cover
create/rename/retarget/delete, no-op history, Undo/Redo, Save/Open without disc access,
project copy and reimport guards including deleted-record history. In the browser,
verify Recall changes only focus; pending script drafts, busy/stale/closed contexts
must prevent mutations. Compare native Build payloads with/without bookmark metadata.
Existing evidence:20 focused bookmark/view/copy cases, JavaScript source qualification,
Town01 browser CRUD/history/recall, partition-two persistence and paired normal Build
payload equality. Private proof: `local-output/sdk-20260909/script-bookmarks-final-20261005/`.
This feature needs no game launch. Broader runtime/gameplay acceptance stays deferred.


**Retail NPC actor-pool lower bound (2026-10-03):** Normal Review Build/Build now qualify the complete SCUS executable and seven retail function spans, derive the143-slot/216-byte actor pool, and reject unavoidable initial-placement overflow before MAN encoding. Source setup evidence establishes the anchor plus partition-1 loop; successful audit metadata keeps other scenery/channel/script demand unknown. Candidate features stay disabled and runtime allocation/gameplay unverified. See [pool check and evidence](legaia-npc-actor-pool.md).

Validation: six focused private-enabled Python checks and existing Node review guards pass. A bounded instruction harness executes the actual pool initializer/pop/failure path:143 distinct slots, then zero without memory changes. Six browser checks prove a normal one-draft package plus a real91-draft Town01 blocker (minimum144 nodes), disabled reviewed Build, unchanged authoring and540px layout. Independent full carrier readback preserves the earlier candidate MAN and fixed-span ownership. Package SHA256 `e8907db2b03619303d72cf3e09fbe2ac82bff7815534733d15c9337a00443c06`. Private proof: `local-output/sdk-20260909/npc-runtime-source-20261003/`. Helpers are closed; no game, install or disc export ran. Full runtime demand/acceptance remain deferred.

**Packet-group texture-binding copy (2026-10-02):** The source-binding picker now fills all textured primitives in a qualified target group in one draft action, with explicit target count. Other group/object drafts, group ABE, untextured rows, target UVs/geometry and source-owned bits remain separate. The complete resulting batch validates before draft replacement; over-budget groups reject atomically. Review, Proposed/Return, one Apply, history, persistence and Build reuse the existing material workflow. See [group copy](legaia-material-binding-picker.md#packet-group-copy-evidence-2026-10-02).

Validation: focused donor/material Node guards and seven actual browser workflows pass. Fresh effective-model hashes verify Undo/Redo. Independent complete TMD construction and packaged carrier readback match:14 target primitives,13 changed rows,26 CLUT/TPage word changes and39 additional bytes, preserving earlier edits and decoded neighbors. Package SHA256 `f1e9c622f00bf4b07fbee0ef1926ecd83872e8430125c94ebda325effcfd39c0`. Private proof: `local-output/sdk-20260909/material-group-binding-20261002/parent/`. Helpers are closed; no game, install or disc export ran. Native appearance/residency acceptance remains deferred.

**Imported model texture-binding picker (2026-10-02):** The material editor now browses active-scene AssetDB models and qualifies their Current source primitive bindings. Explicit Copy fills page/depth/indexed CLUT draft controls while retaining target UVs, geometry and blend flags. Review/Apply, Proposed/Return, history, persistence and normal Build reuse the existing source material command. See [binding picker](legaia-material-binding-picker.md).

Validation: three catalog Python cases, donor Node guards and the existing material lifecycle suite pass. Seven actual browser checks pass through one Apply and Build; a separate visual follow-up verifies UTF-8 labels and540px layout. Independent complete TMD construction/readback proves Current-to-Proposed bytes1102/1103/1106 only, retaining prior ABE byte1095; the entire carrier's neighboring decoded bytes stay unchanged. Package SHA256 `a952ee4f6443068d63f8ddc5b6f636aa31168d3625851d01fcc6a14d0e8a89a3`. Private proof: `local-output/sdk-20260909/material-binding-picker-20261002/parent/`. Helpers are closed. No game, install or disc export ran; UV suitability, live residency, palette animation and native blend appearance remain deferred.

**Assigned actor animation GLB interchange (2026-10-02):** Qualified appearance/initial-clip assignments now export and preview the assigned existing rigid pose. V2 sidecars bind the selected actor, imported clip contribution owner and inherited model witness; the export/review names ownership before Apply. Changes use the owner's existing AnimationChannels command, preserving the selected actor's original clip edits and assignments. Fresh witness/source checks and existing shared-axis conflict guards remain in force; unassigned v1 sidecars remain compatible. See [assigned GLB workflow](legaia-assigned-animation-glb.md).

Validation: four distinct private-retail Python workflow cases and the v1/v2 Node guard suite pass with no skips. Eight actual browser workflows pass through owner-labelled review, retained pose Return,540px controls, explicit Apply, Undo/Redo, Save/reload and normal Build. Independent complete ANM/MAN readback matches: town0b actor0019 retains clip0013 edits; witness0049 owns the clip0012 GLB change. Only ANM bytes8880/10336 and MAN byte9471 differ from retail. Package SHA256 `2d9eaec92f5076624af50f568c6494cd2f01b4b3b27b7f39becb60f2b3ad0aa7`. Private proof: `local-output/sdk-20260909/assigned-animation-glb-20261002/parent/`. No game, install or disc export ran, and helpers are closed. Native clip selection/timing and shared-user gameplay remain deferred.

**World source yaw rotation ring (2026-10-02):** World placements now offers an exclusive source-yaw ring with encoded-unit snapping, perspective-correct frozen-plane pointer conversion, continuous angle unwrapping and 0..4095 wrapping. Shared-record confirmation remains explicit. Temporary previews preserve positions and update every affected instance; Review and Apply use the existing source-qualified command, Undo, persistence, Build and export path. Current comparison gates hidden drafts and cancellation restores prior values/review. See [source yaw ring](legaia-worldmap-placement-yaw.md).

Validation: three focused Node suites and two private-retail Python source/package regressions pass with no skips. Seventeen browser checks pass, including both turn directions, wrapping, independent matrices and unchanged positions for all57 shared instances, cancellation, tool switching,540px controls, one Apply, Undo/Redo, Save/reload, normal Build and stale-source withdrawal. Independent full MAP readback matches X1280/Y256/Z256/yaw448; prior offsets persist and only the two yaw bytes additionally change. Package SHA256 `4a953cf8acfb12105dd121b7c3f6416f9469bfa00907ef4c2999d4e9bc9de6bf`. Private proof: `local-output/sdk-20260909/worldmap-placement-yaw-20261002/parent/`. No game, install or disc export ran; helpers are closed. Native runtime behavior remains deferred.

**World source viewport translation handles (2026-10-02):** World placements now offers source X/Y/Z pointer handles, 1/16/64/128-unit snapping and Frame anchor. Explicit shared scope is required. All affected instances and numeric offsets preview together; release retains a draft, Review qualifies it, and Apply alone records one command/Undo step. Cancellation restores prior draft/review state, and source/camera/layout changes invalidate frozen gestures. A dialog-close race was fixed so cancellation cannot clear another command's busy state. See [translation handles](legaia-worldmap-placement-gizmo.md).

Validation: two focused Node suites and fourteen Python regression cases pass with private input and no skips. Fifteen browser checks pass, including nonzero source/display X/Y/Z movement for all57 shared instances, cancellation, 540px layout, source invalidation, one Apply, Undo/Redo, Save/reload and normal Build. Independent complete MAP readback agrees exactly: record0477 is X1280/Y256/Z256/yaw1536, and only four retail source bytes differ. Package SHA256 `d15d8464e9486a9463dac0b5653e1005aadd9fa942c13e11ebf95fee8d28b6b7`. Private proof: `local-output/sdk-20260909/worldmap-placement-gizmo-20261002/parent/`. No game, install or disc export ran; owned helpers are closed. Native behavior and gameplay verification remain deferred.

**Current/Proposed world placement GLB export (2026-10-02):** World placements now downloads complete qualified kingdom scenes with applied record transforms or an exact reviewed proposal. Exports retain retail geometry, shared meshes, textures and ground, add source/current/exported MAP identities and per-instance retail/exported transform provenance, and preserve unknown runtime visibility/resting state. Proposal export does not Apply, Save or Build. The browser verifies representation, review identity, MAP hashes and binary digest, and rejects late or stale downloads. Existing World ground exports stay retail-source. See [authored world export](legaia-worldmap-placement-export.md).

Validation: six focused Python cases pass with private input and no skips, including unchanged legacy source exports. Independent all-three-kingdom MAP construction verifies every exported translation, yaw and record hash; geometry/image binaries remain identical to retail exports. Node guards validate actual private artifacts. Seven browser scenarios pass with no commands, game requests or page errors; Current and Proposed downloads match independent artifacts byte-for-byte, each with302 entities and57 changed source seeds. Saved project/import/Build files remain exact. The Current MAP hash matches the previously verified Build payload. Private proof: `local-output/sdk-20260909/worldmap-placement-export-20261002/`. No game, install or disc export ran.

**World source placement authoring (2026-10-02):** The World placements viewport now edits qualified shared object-record offsets and yaw for all three walk kingdoms. Source record selection and mesh picking, effective coordinates, shared-record scope, Current/Proposed comparison, frame/orbit, reviewed atomic Apply, Undo/Redo, Save/Open, Authored assets and normal Build are connected. Exact field masks preserve cells, anchors, model references, flags, other axes and opaque bytes. Disjoint MAP overlays compose; conflicting writes reject. Source spawn seeds remain separate from script-evaluated resting positions and visibility. See [world placement workflow](legaia-worldmap-placement-authoring.md).

Validation:17 focused Python cases pass with private source input and no skips, including all-three-kingdom source/package readback and ordinary Build regressions. Node source/review guards and independent transform arithmetic pass. Eight actual browser scenarios verify pending selection and Save/history guards, explicit shared scope, Proposed GPU pixels/matrices,540px controls, history/persistence, normal Build and actual GPU mesh selection. Independent browser-package readback matches all73,728 MAP bytes and changes only bytes15265/15275 against retail; shared record0477 affects57 seeds. No page errors, game requests, installs or disc exports ran. Private proof: `local-output/sdk-20260909/worldmap-placement-authoring-20261002/`. Gameplay acceptance remains deferred.

**Source NPC candidates in normal Build (2026-10-02):** Saved donor drafts now enter inclusive v2 Build review and normal package generation for qualified compressed MAN scenes whose complete candidate fits the original consumed stream. Two source-hashed overlays update that stream and its descriptor size word; carrier size, pointers, neighboring payloads, TOC and disc layout stay unchanged. Supported existing actor/P2 edits compose after append, while other asset overlays retain the normal pipeline. Streaming or oversized additions remain rejected. Packages identify source candidates and keep their feature disabled by default. Native allocation, spawning, scheduling and opaque script behavior remain unverified. See [NPC Build boundaries](legaia-npc-build-candidates.md).

Validation: eleven focused Python checks and sixteen ordinary Build regressions pass with private retail input and no skips; legacy and v2 Node review guards pass. Independent Town01 package readback verifies donor scripts, reached spawn-reference rebasing, existing placement/facing composition and counts `[36,53,39]` to `[36,54,39]`. Optimal LZS uses24,856 bytes within the original24,894-byte stream; decoded MAN grows45,338 to45,917 bytes. Four actual browser scenarios verify inclusive read-only review,540px controls, reviewed Build and unchanged authored/import files with no game requests or page errors. No game, install or disc export ran. Private proof: `local-output/sdk-20260909/npc-normal-build-20261002/`. This supersedes earlier blanket normal-Build draft rejection statements; broader gameplay acceptance remains deferred.

This is the post-feature acceptance plan, not a claim that every test exists.
The current buildout uses focused synthetic checks, retail import probes and
local browser validation. Larger automation follows connected product features.
See `FEATURE_MATRIX.md` and `legaia-release-parity.md` for actual current results.

## Latest integrated offline result — 2026-10-02

**World-map source GLB export (2026-10-02):** World ground inspection now connects to private GLB downloads for all resolved source placements plus terrain, terrain alone when the placement layer is hidden, or one selected source entity. Shared meshes, source transforms, embedded matched textures and source provenance use the existing scene exporter. Fresh source checks bind exports to the imported disc and current project; late responses after closing or changing sources cannot trigger downloads. Exported placement seeds retain unknown runtime resting positions and visibility. Exports create private artifacts without authored commands or Build/disc output. See [world-source export](legaia-worldmap-export.md).

Validation: 16 focused Python cases passed with private retail input and no skips; three Node guard suites and frontend syntax checks passed. Independent all-three-kingdom readback verifies source world corners, reflected winding, shared meshes, UVs, stored colors, embedded PNG pixels and provenance. Nine actual browser scenarios pass, including five downloaded artifacts, ground-only visibility scope, selected seed scope, 540px controls, cancelled late responses and stale-source withdrawal. Downloaded geometry binaries and normalized metadata match the independent exports. Blender 5.2.2 LTS imports the complete map01 scene with 302 entity roots, 303 mesh objects, 67 materials and 60 images; all local triangles match, and maximum world-coordinate float error is 0.0009765625 source unit. Saved project/import/Build files remain unchanged; no game, authoring command or disc export ran. Private proof: `local-output/sdk-20260909/worldmap-glb-20261002/`.

**Scenery group source-angle rotation (2026-10-02):** The existing anchor rotation workflow now accepts every integer source yaw delta from 0 through 4095, alongside its compatible quarter-turn controls. A frozen Q30 quarter-wave table and signed integer nearest-half-away rounding produce reviewed X/Z positions; cardinal turns remain exact. The editor independently checks the same arithmetic before accepting a report. Review, retained Proposed/Current inspection, atomic Apply, Undo/Redo, Save/Open and normal Build preserve source Y, other rotation axes, shared descriptors and unrelated components. Rounded positions can change distances slightly; this authoring convention does not establish retail GTE rounding or gameplay acceptance. See [group rotation workflow](legaia-scenery-group-rotation.md).

Validation: 19 focused Python cases passed with no skips; two Node guard suites and frontend syntax checks passed. All 4096 angles match between Python integers and JavaScript BigInt for six signed displacement pairs, with identical frozen tables. Twelve actual browser scenarios verify custom angle review, invalid-input rejection, retained Proposed/Current comparison, history, Save/reload, normal Build, cancellation and stale-state withdrawal; the 540px layout was visually inspected. Independent renderer matrices and reopened full 73,728-byte MAP package readback match the reviewed 45° proposal. Only bytes 171/256/260/267 change against the prior authored fixture; source Y, other axes, shared records, prior Collision and retail MAP remain intact. No game or disc export ran. Private proof: `local-output/sdk-20260909/scenery-group-angle-20261002/`.

**Source-bound GLB material editing (2026-10-02):** Fresh profile v6 adds
`_LEGAIA_SOURCE_MATERIAL` for full stored CLUT/TPage words and shared group ABE.
Exact integer primitive aliases and whole-group transparency aliases must agree.
Qualified masks preserve reserved CLUT bits, source ABR, other mode bits, row
commands and allocation. Untextured CLUT/TPage retain -1; group ABE remains
editable. Existing source positions, UV/RGB, normals and references compose;
legacy profiles retain their earlier field permissions. Review/Proposed
inspection/Apply/history/Save/Build use the normal model replacement workflow.
Shader assignments and texture images are separate; static associations may
remain partial. Retail blend/appearance acceptance remains deferred. See
[material GLB workflow](legaia-model-glb-materials.md).

Validation: 44 focused Python cases passed with the private retail disc (no
skips), two Node guard suites and frontend syntax checks. Actual Blender 5.2.2
no-op roundtrips are byte-exact; independent CLUT/group ABE, TPage and untextured
sentinel proofs change only bytes131/138, byte142 and byte299 respectively.
Twelve integrated browser checks cover fresh exports, no-op, reviewed source
fields, Proposed/Return, 540px layout, Apply/history/Save/stale withdrawal and
normal Build. Reopened package readback retains prior normal-reference/XYZ
bytes2940/3332 and adds only material bytes131/138, preserving neighboring data
and the 154,547-byte compressed capacity. No game was launched and no disc output written.
Private proof: `local-output/sdk-20260909/model-glb-materials-20261002/`.

**World-map source placement inspection (2026-10-02):** **World ground** now
opens a source scene with 301/272/236 sparse model placements in map01/map02/map03.
The hierarchy, mesh picking, Frame selected and Source model placements toggle
expose stable entity IDs, MAP cells, record hashes, dictionary slots and source
XYZ. Column-major source yaw/translation becomes a row-major renderer transform
with one display Y flip. The ground asset and source coordinates remain unchanged.
This is read-only; source changes withdraw geometry and pending-close cancels reads.
Runtime visibility, script-adjusted resting positions and animation remain
unverified. Model textures are partially resolved and missing associations stay
explicit. See [placement workflow](legaia-worldmap-placements.md).

Validation: eleven focused Python cases passed with the private retail disc
(no skips), plus ground and placement Node guards and frontend syntax checks.
Independent raw-source comparisons match every seed position, rotation, record
hash, model slot, loaded model topology and source-member hash in all kingdoms;
ground geometry remains unchanged. Nine integrated browser checks cover actual
rendering, hierarchy/coordinates, mesh picking, toggles, camera controls, 540px
layout, source withdrawal, pending-close and exact saved project/Build file hashes.
No game was launched or disc output written. Private proof:
`local-output/sdk-20260909/worldmap-placements-20261002/`.

**World-map walk-ground workspace (2026-10-02):** The editor's **World ground**
resource action now opens source-backed textured 3D ground for map01, map02 and
map03 through the shared scene renderer. The importer qualifies the overlapping
kingdom carriers, exact 0x12000 MAP footprint, slot-2 MAN floor LUT and slot-0
TIM atlas. Orbit/zoom, Frame ground, Top view, Wireframe and source details are
read-only; source changes withdraw retained geometry and closing pending reads
releases controls. Imported field selection, authored state, history and Build
files remain unchanged. Source Y-down coordinates flip only at the renderer.
Overview/MAPDSIP, script-managed resting transforms, sky/fog and runtime parity remain pending.
See [world-ground workflow](legaia-worldmap-geometry.md).

Validation: six focused Python cases passed with the private retail disc (no
skips), plus Node source/geometry/texture guards and frontend syntax checks.
Independent readback matches every ordered vertex, triangle, UV and visible-cell
selector in all three kingdoms. Visible cells are 16,251/16,381/16,374; source
texture coverage is 23/23, 17/18 and 15/16. Missing palettes stay explicit, without
fallback textures. Eight browser checks cover actual three-kingdom rendering,
camera controls, 540px layout, stale withdrawal, pending-close and unchanged
project files. No game was launched, no disc output written. Private proof:
`local-output/sdk-20260909/worldmap-geometry-20261002/`.

**Source-bound GLB normal-reference editing (2026-10-02):** Fresh profile v5
adds `_LEGAIA_SOURCE_NORMAL_INDEX` for selecting an existing normal within the
source object. Immutable corners retain packet ownership; flat references and
all raw XYZ aliases must agree. Unlit index -1 and XYZ sentinel remain explicit.
Changed references use `tmd-content-v3`; older content versions keep normal
references immutable. Review/Apply/history/Save/Open and normal Build compose
reference changes with earlier authored normal words. Material inspection,
source-bound JSON/TMD review and object transforms preserve the new references.
Counts, allocation, padding and unrelated source bytes remain fixed. Retail
lighting and gameplay parity remain deferred. See
[normal-reference workflow](legaia-model-glb-normal-references.md).

Validation: 42 focused Python tests passed with the private retail disc (no
skips), plus Node workflow and frontend syntax checks. Twelve integrated browser
checks cover actual Blender review/no-op, proposed inspection, Apply/history/
Save, 540px layout, stale rejection and Build. Independent flat/Gouraud rewiring
changes only byte2940/byte4284 respectively, retaining the earlier normal edit.
Integrated Build retains bytes2940 and3332, unchanged neighbors and the original
154,547-byte compressed capacity. Legacy content downgrades reject the changed
reference. No game was launched. Private proof:
`local-output/sdk-20260909/model-glb-normal-references-20261002/`.

**Source-bound GLB normal editing (2026-10-02):** Fresh model profile v4 adds
`_LEGAIA_SOURCE_NORMAL` raw signed-i16 XYZ for existing lit packet normal owners.
Shared flat/Gouraud aliases must agree after rounding. Retail axes remain
[x,y,z], without POSITION's Y flip or normalization; unlit corners retain the
out-of-domain [32768,32768,32768] sentinel. Display NORMAL is ignored. Normal
references, padding, allocation and unrelated bytes remain unchanged. Review,
Apply, undo/redo, Save/Open and normal Build use the existing model replacement
workflow. Legacy v1-v3 codec behavior remains; SDK editing requires a fresh v4
export. Retail normal-based lighting and gameplay acceptance remain pending.
See [normal workflow](legaia-model-glb-normals.md).

Validation: 27 focused Python tests passed with the private retail disc (no
skips), plus Node workflow and frontend syntax checks. Twelve browser checks
cover actual Blender no-op/edit review, proposed geometry, Apply/history/Save,
540px layout, stale rejection and normal Build. Independent Blender 5.2.2
readback changes only byte3332 for a shared flat normal and byte4640 for a
Gouraud normal. Integrated Build preserves all decoded neighbors and the
154,547-byte compressed capacity. No game was launched. Private proof:
`local-output/sdk-20260909/model-glb-normals-20261002/`.

**NPC facing composition and output review (2026-10-02):** Source script facing
edits now compose with appended NPC drafts in compressed and streaming MAN
carriers. Original record ownership is re-resolved after append; only the facing
nibble changes, upper flags remain intact, and donor clones retain retail facing.
The editor's **Review NPC output** prepares an in-memory archive and reports
source identities, relocated fields and allocation limits without writing a
package/disc, changing history or launching the game. Normal Build still rejects
NPC drafts; gameplay, scheduling and general allocation remain unverified.
See [draft facing workflow](legaia-draft-facing.md).

Validation: 16 focused Python tests passed with the private retail disc (no
skips), plus Node metadata guards and frontend syntax checks. Six integrated
browser checks cover actual two-scene review, exact metadata, 540px layout,
stale-input withdrawal, pending-close handling and unchanged saved files.
Independent Town0b/Dolk2 readback verifies four/one facing-byte changes, each
rebased by three bytes after append; donor copies and unrelated bytes are retained.
Private proof: `local-output/sdk-20260909/draft-facing-20261002/`.

**Source-bound GLB face rewiring (2026-10-02):** Model profile v3 adds existing
polygon vertex references to the external mesh workflow. Immutable source corner
IDs retain face ownership; qualified vertex IDs may select existing vertices in
the same object. Seam/quad reference and coordinate aliases must agree. Review
shows exact source/current/proposed references before ordinary Apply/history/
persistence/Build. Object, vector, polygon and packet capacities stay fixed;
new objects/polygons, normal tables and material allocation remain pending.
Legacy v1/v2 codec behavior is retained; SDK authoring requires a fresh v3 export.
See [face workflow](legaia-model-glb-faces.md).

Validation: 22 focused Python cases passed with the private retail disc (no
skips), plus the Node workflow and frontend syntax checks. Twelve browser checks
cover exact reference Review, regenerated proposed geometry, no-op and stale
rejection, 540px layout, Apply/history/Save and normal Build. Actual Blender 5.2.2
updates both aliases of one quad corner, vertex 17 to 0; independent readback
changes only byte434 (136 to 0). Build retains earlier RGB/material bytes300,
1095 and1102, all decoded neighbors and the 118,461-byte compressed capacity.
No game was launched; gameplay appearance and general allocation remain pending.
Private proof: `local-output/sdk-20260909/model-glb-faces-20261002/`.

**Raw RGB model GLB editing (2026-10-02):** The existing external model workflow
now imports qualified baked RGB through `_LEGAIA_SOURCE_RGB` in the raw 0..255
byte domain. Profile v2 binds each flat/shared or Gouraud/corner color to its
source packet; duplicate aliases must agree, and packets without stored RGB
retain explicit -1 sentinels. Review exposes exact fields and rounding error
before ordinary Apply/history/persistence/Build. Display `COLOR_0`, shader colors,
normals, references, material words and allocation remain outside this lane.
Fresh exports use v2; the codec retains legacy v1 positions/UV behavior. Existing
bindings require a fresh export for SDK Apply. See [RGB workflow](legaia-model-glb-rgb.md).

Validation: 18 focused Python cases passed with the private retail disc (no
skips), plus the Node workflow and frontend syntax checks. Twelve browser checks
cover no-op, exact RGB Review, proposed model, 540px layout, file invalidation,
Apply, Undo/Redo, Save, Build and stale-source rejection. Actual Blender 5.2.2
round trips flat and Gouraud edits exactly. The saved Dolk2 Build adds only byte
300 (24 to 25) to the two existing material bytes, preserving decoded neighbors
and the 118,461-byte compressed capacity. No game was launched; runtime lighting
and appearance remain deferred. Private proof: `local-output/sdk-20260909/model-glb-rgb-20261002/`.

**Coordinated scene animation:** Six focused Python cases and the Node lifecycle
suite pass. Actual Dolk2 integrated preparation loads 69 actors/15 shared tracks
and 46,015 frame vertices in Retail and Authored views. Independent Town01 source
proof covers 42 actors/22 tracks and 67,947 frame vertices. Sampled poses retain
source geometry, ordered object ranges and material mappings; authored frame zero
matches the composed shared bank and differs from Retail. Browser checks cover
multi-mesh sampling, unchanged canonical/placement/material/history, Play/Pause,
paused command rejection, exact Restore, narrow layout and representation guards.
No page/HTTP errors or game launches. Runtime timing/scheduling and live clip
identity remain unverified. Private evidence: scene-animation-20261002/parent
and research under local-output/sdk-20260909/.

**Source-qualified model materials:** 22 focused Python tests (nine new material
cases), three Node workflow suites and six real-browser checks pass. Checks cover
masked CLUT/TPage fields, shared group ABE, strict legacy reads, v2 material splits,
merges/reordering with retained rigid poses, source/draft/stale/no-op guards and
model/scene Return retention. Actual Dolk2 Apply, Undo/Redo, Save/Open and Build
preserve geometry and GLB bytes. Package readback changes only source bytes 1095
and 1102, retains the 118,461-byte compressed capacity and every decoded neighbor.
540px layout passes; page/HTTP errors and Run requests are zero. Runtime blend
state, texture residency and gameplay appearance remain unverified. Private
evidence: `local-output/sdk-20260909/model-material-20261002/parent/`.

**Source-bound texture PNG editing:** 12 focused Python cases pass with no skips:
4/8/16/24-bpp exact no-ops, duplicate indices, selected-row/pixel byte masks,
raw RGB nearest choices, deterministic palette reduction, binary alpha/STP,
PNG filters/indexed samples, bounded malformed/zlib/profile rejection, fresh
binding and read-only review/pixels, reviewed Apply, history, persistence and
HTTP envelopes. The Node suite covers exact Files/mode/context, export/download,
read-only pixels, immutable scene Return, stale/closed/late/busy guards and
Apply reply validation. Both frontend syntax checks and 11 browser checks pass,
including 540px layout and normal Save/Build, with zero page/HTTP errors or
game-launch requests. Independent Pillow verifies retail conversion and color
errors. Town01 package readback matches the exact reviewed TIM within its
33,312-byte allocation; other palettes, source metadata and neighbors remain
unchanged. Scene proposal affects 26 materials/10 instances and preserves all
geometry/placements. Private proof:
`local-output/sdk-20260909/texture-png-20261002/parent/final-evidence.json`.
Later gameplay acceptance must check texture appearance, palette consumers and
STP blending under matching runtime provenance. Large-image performance remains
unverified. See [workflow and limits](legaia-texture-png.md).

**Source-bound model GLB editing:** 14 focused Python cases pass with the private
disc and no skips: 24 packet families, exact alias/quad byte masks, indexed and
interleaved accessors, topology/bounds rejection, fresh binding, read-only review
and proposal, effective model composition, Apply/history/persistence and normal
Build readback. The Node suite covers immutable Files, stale/closed/late replies,
no-op and preview Return. Both frontend syntax checks and 12 browser checks pass,
including 540px layout and normal model rendering, with zero page/HTTP errors or
game launches. Actual Blender 5.2.2 receives a fresh SDK GLB and preserves source
bytes on re-export; its edit changes exactly one vertex X and one quad UV U.
Merge Vertices or lost attributes reject. RGB and normals are preserved.
The saved Dolk2 browser Build reconstructs the exact candidate within its source
capacity with unchanged decoded neighbors. Private proof:
`local-output/sdk-20260909/model-glb-20261002/parent/final-evidence.json`.
Later gameplay acceptance must check matching model/UV appearance and shared
instances. No immediate game verification is required. See [workflow](legaia-model-glb.md).

**Imported project Asset Database (2026-10-02):** The primary browser uses
source-qualified project inventories with retained shared memberships, scene
filters, field search, pagination and canonical cross-scene inspectors. The
Town01/Dolk2/map01 audit returns 3,637 identities and 3,703 memberships with
explicit partial coverage. It preserves populated source/material caches,
authored values, selection, Undo/Redo entries and saved files. Source freshness
ignores ordinary navigation and rejects authored drift. The focused backend,
HTTP dispatch checks total 18 passing Python tests. Two Node suites, both
changed-module syntax checks and 19 integrated browser checks passed. Private
evidence retains exact P2 owner/PC focus, canonical tool handoffs, authored
invalidation/Undo, stale action rejection and reviewed 540px layout. Page/HTTP
errors and game-launch requests were zero. This read-only inventory feature adds no
gameplay edit or new gameplay verification requirement. Complete format and
runtime coverage remain pending. See [workflow](legaia-project-assets.md).

**Source-qualified global landmark authoring (2026-10-02):** The world-map
workspace edits the 20 existing SCUS menu records with separate Retail,
Authored, Current and reviewed Proposed values. Existing name/discovery,
CDNAME destination and encoded X/Y fields have a duplicate-safe 2D diagram,
exact byte review, Apply/reset, Undo/Redo and Save/Open. Authored asset links and
normal Build reports reopen the source row. Normal Build emits a guarded
126-byte SCUS data overlay, with independent whole-executable reconstruction;
field placement composition retains both overlays and unchanged imports.
Experimental Export disc rejects this global component explicitly.

Name and discovery consumers are now qualified by retail static analysis.
Destination and X/Y meanings remain reference interpretations; drawing,
travel, discovery activation and gameplay are not verified. The table has 20
rows, terminator row 20 and two padding bytes before 16 immutable name slots.
See [landmark authoring workflow and evidence](legaia-worldmap-authoring.md).

Validation: 36 selected Python tests passed with the private retail disc and no
skips; two Node suites, both changed-module syntax checks and 16 browser
workflows passed. Browser page/HTTP errors and game-launch requests were zero.
The saved browser package independently reconstructs the executable with only
file byte 0x6429C changed 96-to97 (row 0 X), while fresh scene imports still match.
Review exposes field changes, byte offsets and the candidate hash; draft gates,
reset/history/persistence, 540px layout and Build-to-source navigation passed.
Private proof is in `local-output/sdk-20260909/worldmap-authoring-20261002/`.
The full SDK and gameplay acceptance remain incomplete.

**Source-qualified field branch authoring (2026-10-02):** The script workspace
now links a selectable source-flow diagram to disassembly and reviews existing
JMP, conditional, bounding-box, flag-word and ordinary system-flag destinations.
Retail, authored, current and proposed edges remain separate; encoded conditions
are not evaluated. Targets must be original instruction or atomic MES starts
through PC32767. Reviewed Apply/reset uses ordinary Undo/Redo and Save/Open;
normal Build, streaming export, appended-record composition and operand files/
bundles retain record layout and independently qualify changed flow. Other
authored operands survive branches that make source nodes unvisited.

Retail handler validation also corrects three existing decoder interpretations:
camera apply and FIELD43/44 continue, and flag-word targets use relative offsets.
Ordinary SYSFLAG forms cover50..7F; extended forms stop with an explicit reason.
The pinned Andrew reference remains unchanged. Town01 now has619 decoded dialogue
segments and1339 flag references; Dolk2 has629 segments and744 references.
See [field branch workflow and evidence](legaia-script-branches.md).

Validation:88 integrated Python regression cases passed with the private retail
disc and no skips, including compressed Town01 and raw Dolk2 normal packages.
Three HTTP cases reject18 malformed/foreign requests and stale Apply without
changing evidence or history. Four Node suites and15 browser workflows passed;
browser page/HTTP errors and game-launch requests were zero. The browser's
reviewed Town01 package independently reads back with only byte4791 changed
(PC31 target15-to11); its saved imports still match a fresh source import.
Dolk2 PC28 target63-to9 changes only bytes7481/7482. Real Town01 donor append
preserves that branch at rebased byte4794 in the prepared MAN; full rebuilt-disc
acceptance is deferred. Current/Proposed navigation, multiple pending choices,
reviewed Apply/reset, Undo/Redo, Save, no-op/stale gates, narrow layout and exact
Build-to-source navigation were checked. Private evidence remains in
`local-output/sdk-20260909/script-branches-20261002/`. Runtime branch activation,
story behavior and termination remain deferred; the full SDK remains incomplete.

**Model primitive content authoring (2026-10-02):** The integrated model
face/UV/baked-RGB workflow now spans source inspection, reviewed paired previews,
existing posed scene instances, atomic Apply, vector composition, Undo/Redo,
Save/Open, authored TMD export and normal Build audit navigation. Source packet
ownership, all24 flag layouts, bounded fields, stale/late requests, unchanged
opaque bytes and Vahn's actual idle-animation prefix are checked. Added objects,
packet/vector allocation, changed material bindings and runtime rendering
acceptance remain unfinished. See [model content contract](legaia-model-content.md).

Validation: 31 selected Python cases passed with the private retail disc enabled
and zero skips; 3 Node suites and 2 changed-module syntax checks passed. Sixteen
actual browser workflows passed with zero page/HTTP errors and zero game-launch
requests, including normal Build review/package/source navigation. Reviewed,
scene, Build and narrow-layout captures were inspected. Town01 model0000 changes
exactly source bytes48/52/62/64; independent package readback verifies the complete
304116-byte decoded container, 154518 encoded bytes within the 154547-byte source
capacity, and unchanged unused encoded tail. Imported metadata is unchanged and
Save/Open retains the exact versioned binding. Vahn idle retains its verified
12-to-10 object prefix and frame coordinates. Gameplay appearance/lighting/culling
remain deferred; no game was launched or package installed. Private evidence is
under `local-output/sdk-20260909/model-primitives-20261002/`.

**Visual transition graph workspace (2026-10-02):** Scene and Project
transitions now open a selectable node/arrow diagram, scene list, search,
imported-only filter, direct-reference focus, zoom/pan/Fit and paginated source
instructions. Parallel instructions remain independent records; arrow badges
group only equal source/destination pairs. Retail, Authored and Effective entry
bytes stay separate. Source-script navigation selects the exact owner and PC;
imported destinations use ordinary scene selection. Coverage, unavailable
catalogs and unresolved names remain explicit. Project-only freshness changes,
stale responses and pending-close/reopen cleanup and old-request isolation invalidate retained controls. The
canvas draws at most 80 scenes and 160 pairs; every matching instruction remains
accessible in 20-row pages. No gameplay route or story reachability is inferred.
See [transition graph workflow](legaia-project-transitions.md).

Validation: 26 selected retail-enabled Python cases passed with zero skips;
6 Node suites and 3 changed-module syntax checks passed. Thirteen actual browser
workflow checks passed with zero page/HTTP errors, zero authoring commands and
zero game-launch requests. The four-scene Town01/Dolk2/Town0b/map01 fixture has
17 nodes, 18 grouped pairs and 35 instructions from 319 scripts (195 partial,
zero unavailable). Graph, narrow-layout and entry-layer captures were inspected;
long arrows avoid intervening scene boxes and badges remain selectable above
crossing lines. Imported metadata and the saved project are unchanged. This
source-reference workspace is accepted offline; gameplay/runtime verification
remains deferred for the wider SDK. No game was launched or package installed.

**Reviewed primary trigger cells (2026-10-02):** Existing primary MAP kind-0
teleport and kind-1 binding rows now have an Edit trigger cell action. Retail,
Authored, Current and Proposed X/Z cells remain separate, with outline and scene
comparison, per-row retail reset, one-step Undo/Redo and Save/Open. Fresh source
and review keys qualify the complete retained binding; stable row identity stays
independent of coordinates. Only two lookup-coordinate bytes are writable.
Destinations, record/gate payloads, row order, footprints, elevation and all other
MAP bytes remain unchanged. A separate trigger key invalidates annotations
without reloading geometry. Normal Build composes triggers, regions, scenery and
collision walls in one exact MAP overlay, independently binding every trigger
byte to the requested cells. Build report links reopen the source resource.
Fallback rows remain read-only; unknown gates keep their unresolved behavior.
Moving a row can change first-match shadowing. Height, contact, activation and
playable behavior remain deferred. See [trigger cell workflow](legaia-trigger-cells.md).

Validation:50 selected retail-enabled Python cases verified without skips,
including the12 affected/neighbor cases rerun after repairs;6 Node suites and3
changed-module syntax checks passed. Thirteen actual browser workflow checks
passed with zero page/HTTP errors and zero game-launch requests. Visually
inspected review and viewport captures are readable. The retained Town01
kind-0/0000 fixture changes only MAP65554 from30 to31, preserving destination
bytes146/132. Fresh disc-span, ZIP and imported-metadata readbacks agree. The
package is built, not installed or played; full SDK/runtime scope remains incomplete.

**Source-facing instruction authoring and object-index correction (2026-10-02):**
The actor Inspector now opens source-qualified facing controls for simple
CAM_CFG and nonparked NPC_RUN instructions. Retail, Authored and Effective
sectors remain separate; drafts have a numeric compass preview, Apply/Clear,
Undo/Redo and Save/Open. Source-bound operand JSON and scene bundles include
ScriptFacing. Normal Build composes the exact low-nibble writes with other MAN
edits and checks the full byte audit and compressed capacity. Retail dispatch,
LUT reads and actor-facing stores were verified statically before implementation.
The shared Inspector also renders additional registered components through their
schema. Gate-0 object references now preserve unresolved flat MAN indices;
gate-1 remains explicitly P2-local. Initial/live actor heading, branch selection,
experimental NPC append export and gameplay acceptance remain unresolved.
See [source-facing workflow](legaia-script-facing.md).

Validation:56 focused retail-enabled Python tests passed without skips in70.133s;
7 Node checks and3 changed-module syntax checks passed. Nine actual browser
workflow checks passed with zero page/HTTP errors and zero game-launch requests;
a real P2 report independently validates/renders31 controls with explicit
extended-context uncertainty. Retained Town0b actor0019 packaging changes only
MAN byte9479 from0x81 to0x85, preserving the upper flag. Imports remain unchanged.
The package is not installed or played; full SDK/runtime scope is incomplete.

**Reviewed field region bounds (2026-10-02):** Primary MAP regions now have
an Edit region bounds action, four strict corner inputs, separate Retail /
Authored / Current / Proposed layers, and outline/viewport comparison. Apply
and per-row retail reset use one undo step; inherited/no-op values normalize
without dirtying the project. Source-qualified effective annotations leave the
imported spatial envelope intact, and a separate region key invalidates views
without reloading geometry. Save/Open and normal Build preserve the region
type, padding, source order and all bytes outside audited corners. Region edits
compose with scenery and collision walls in one MAP overlay. Browser review,
frame, comparison, Apply, history, persistence and scene cleanup passed with
zero page/HTTP errors and zero game-launch requests. The retained Town01
fixture changes only MAP byte66692 from58 to59; its package is built but not
installed or played. Height, activation and movement acceptance remain deferred.
See [region bounds workflow](legaia-region-bounds.md). The full SDK/runtime
objective remains incomplete.

Region milestone validation:54 retail-enabled Python tests passed with no skips in74.565s;42 Node checks and40 module syntax checks passed. Actual browser comparison passed10 workflow checks with zero page/HTTP errors and zero run requests. Independent package readback confirms one byte changes; imported scene hashes remain unchanged. No game launched or package installed.

**Field source cells and script links (2026-10-02):** Verified trigger and
region rows now appear in the scene hierarchy and shared Inspector, with
viewport outlines, framing and explicit source-cell picking. Trigger dispatch
uses `world >> 7`; region lookup uses `(world - 64) >> 7`, preserving the
64-unit difference. Display Y=0 remains an inspection plane with unknown
height. Coincident rows retain separate source identities. Gate-1 rows link to
unique bounded P2 scripts in Active/Project reference graphs with both record
hashes; object binds, unknown gates and missing/aliased targets stay unresolved.
Town01 supplies 99 trigger cells,14 region bounds and 51 eligible script links.
Read-only HTTP, source qualification, browser navigation/picking and stale-scene
cleanup passed. No game launched or package installed; contact/activation and
retail height acceptance remain deferred. See
[field source workspace](legaia-field-source-workspace.md). Full SDK/runtime
coverage is still incomplete.

Final validation:59 retail-enabled Python tests passed with no skips in84.629s;41 Node checks and39 module syntax checks passed. Actual browser frame/pick, overlapping rows, reference/script navigation, actor restoration and scene invalidation passed with zero page/HTTP errors. The saved baseline/import hashes remained unchanged; no package or game was launched.

**Central transition assets (2026-10-02):** Decoded scene-change instructions
now appear in the Asset Browser, shared Inspector and Active/Project dependency
graphs. Imported/authored/effective entry bytes and static destination arrival
coordinates remain distinct from unknown source triggers. A dedicated transition
key invalidates stale views without reloading geometry. Fresh serializer checks
qualify authored entries; partial catalog coverage with zero decoder stops no
longer blocks otherwise supported entries. Retail discovery found 35 transitions
across Town01, Dolk2, map01 and Town0b.55 retail-enabled Python tests passed
with no skips;39 Node checks and38 syntax checks passed. Browser editing,
history, persistence, source/destination navigation and reference scopes passed.
Reopened Build changes only Town01 MAN bytes28574 (96 to128) and28576 (4 to2).
No game launched; existing transition-arrival gameplay acceptance is deferred.
See [transition asset workflow](legaia-transition-assets.md). The full SDK and
runtime objective remains incomplete.

**Reusable initial-animation presets (2026-10-02):** Versioned v2 presets
capture a verified initial clip alone or with authored position/appearance.
Frozen witness proof survives later source-actor edits; full proposed components
are validated together before one single/group Apply. Omitted components and
imported channel ownership stay intact. Inherited clip matches normalize to
absence, including a true no-op on untouched targets. Metadata-only v2 files
retain fresh source/import/hash proof and independent library identity; legacy
v1 files/scopes remain supported. Proposed/Current scene comparison, Return,
Undo/Redo and Save/Open are connected.47 focused retail-enabled Python tests
passed in57.695s, plus8 HTTP/project compatibility tests in1.293s;37 Node files
and37 syntax checks passed. Actual browser capture/transfer/single/group scene
review/Apply/history/Save passed with zero page or unexpected HTTP errors.
Independent Town0b pure-clip MAN readback changes only9471,14→13; inheritance
reproduces baseline output. The saved combined fixture changes only19122,13→14,
and19123,119→150 (X15296→2944), retaining model0102/Z1472. Reopened Build
reproduces package SHA256 `2cc94474453d5a5bd8eaddb07808c6f3dbd10d089d126f9a8e8c4cb0dbd06389`.
No game launched; existing playback/script/gameplay acceptance remains deferred.
See [animated preset workflow](legaia-animated-actor-presets.md). The full SDK
and runtime objective remains incomplete.

**Central flag-reference assets (2026-10-02):** Source-scoped flag groups
now appear in Asset Database search, a shared Inspector, and Active/Project
script dependency graphs. The Inspector shows retail/authored/effective sites,
coverage and exact-PC navigation for P1/P2 owners. A dedicated operand-state
key invalidates stale annotations without changing geometry; project flag
keys now include authored operands. Fresh Town01/Dolk2/map01 sources yielded
899 groups/2,142 sites; source browsing preserves project/saved state.
43 focused retail-enabled Python tests passed in20.085s;36 Node files and36
syntax checks passed. Browser P1/P2 exact-PC navigation, operand layers,
Undo/Redo/Save/Clear, stale-view closure and Active/Project references passed
with no page or unexpected HTTP errors. Runtime variables, story names and
unseen paths remain unresolved. See [flag asset workflow](legaia-flag-assets.md). Gameplay remains
deferred; the full SDK/runtime objective is incomplete.

**Initial animation assignment (2026-10-02):** The actor Inspector now offers
source-verified same-model clip choices, explicit Review/Apply/Clear and witness
preview. A separate ActorAnimation component preserves imported channel ownership,
Undo/Redo and Save/Open. The authored scene and assigned GLB preview keep target
identity/position; normal and draft writers compose the final MAN header once.
Effective references and unconfirmed Live candidates keep animation witnesses
separate from appearance donors and invalidate stale observations. Incompatible
appearance/preset/revert changes reject atomically. Legacy v1 templates capture position/appearance; versioned v2 presets now
include the separate initial assignment. Global/zero/unknown/partial pairings remain
unsupported; scripts, timing and gameplay suitability remain unverified.
39 focused retail-enabled Python checks passed in55.598s, plus a22-check
compatibility pass in21.572s; all34 Node files and35 syntax checks passed. Seven raw MAN/appearance compatibility checks
also passed in47.334s without skips.
Actual browser Review/Preview/Apply/Clear, assigned-frame GLB export,
Undo/Redo/Save, exact scene placement and initial/effective reference edges passed
with zero page errors; malformed/stale HTTP rejected without history changes.
Visual review repaired a clipped Review button; final layout and screenshot
passed. Fresh Town0b package readback changes only MAN offset9471,14→13,
model0102/positions/imports/saved bytes unchanged. Record12 digest and exact
retail import were reverified; clearing reproduces baseline package bytes.
Draft composition preserves the appended retail donor clip and rebases the
existing header9471→9474. Saved private fixture/package/evidence:
`local-output/sdk-20260909/actor-animation-assignment-20261002/`.
See [initial assignment workflow](legaia-initial-animation-assignment.md).
No game launched or package installed. Manual checks are queued for later;
full SDK/runtime acceptance remains incomplete and the565 checkpoint predates
this feature.

**Shared model/clip reference navigation (2026-10-02):** Asset references
now links the eight supported shared field clips to their five global models in
both Active scene and Project scopes. These are explicit reference-pinned
associations, separate from initial/effective actor assignments. Edges retain
the pinned commit, model/clip identity, decoded counts and full source locator;
strict model provenance, record mapping and bounded metadata checks reject
inconsistent evidence. Missing models remain unresolved. The browser labels
actor playback unknown and supports model-to-clip and clip-to-model navigation.
31 focused retail-enabled Python checks passed in 24.333s; all 33 Node files and 34
syntax checks passed with hashes matched to final source. Fresh Town01/Dolk2/map01
discovery verified all 8 clips and 24 source-qualified edges in 33.826s, exact edge
hashes and untouched project/cache/saved bytes. Actual browser Active/Project
HTTP, three-scene navigation and the auxiliary loop passed with zero page errors
or authoring commands; screenshot inspected. Private evidence:
`local-output/sdk-20260909/shared-clip-references-20261001/`.
No game launched; this read-only feature needs no new gameplay gate. The
565-test checkpoint predates both reference workflows; full SDK/runtime
acceptance remains incomplete.

**Project-wide asset references (2026-10-01):** Asset Details → Inspect
asset references now offers Active scene and Project scopes. Project discovery
freshly verifies all imported scenes and assembles existing decoded relationships
through detached scene/catalog views, preserving project state and caches. Shared
stable IDs retain source memberships separately from navigable catalogs, with
scene-qualified edges and deterministic cross-scene navigation. Coverage exposes
source hashes, partial-catalog limitations and explicit unavailable reasons;
recorded relationships do not establish runtime residency or reachability.
Scope/Close cancellation and stale-source guards prevent late results. Strict
HTTP shapes and bounded graphs/metadata retain the existing active response.
Twenty focused retail-enabled Python tests passed in13.948s; all33 Node files
and34 syntax checks passed with hashes matched to final source. Fresh Town01,
Dolk2 and map01 discovery checked actor/script/dialogue/animation/world-map links,
12 shared-model material edges and exact source hashes; complete project/cache
and saved bytes stayed unchanged. This final retail check took21.566s. Per-call
import-hash reuse produces an identical report to the earlier repeated-hashing
implementation. Actual browser Active/Project HTTP responses, three-scene scope,
source navigation, pending Close and stale-source rejection passed with zero
page errors; screenshot inspected. Private evidence:
`local-output/sdk-20260909/project-asset-references-20261001/`.
No game launched. This read-only feature needs no new gameplay gate. The565
checkpoint predates it; full SDK/runtime acceptance remains incomplete.

**Integrated offline checkpoint (2026-10-01):** Full retail-enabled SDK
regression passed565 Python tests in250.658s (252.001s wall time), exit0 with no
skips, on unchanged clean source `43994eb25f5125da4378f2cb970b311931745bf9`.
All33 Node test files and34 editor syntax checks passed with captured hashes
freshly matched to source. This supersedes548 and includes viewport source-wall
editing, atomic mixed actor/scenery placements and their X/Z handles, saved
scene selections and visible placement rectangle selection, alongside earlier
SDK workflows. User-owned disc identity and466714416-byte length were freshly
verified. Browser and package readback evidence remains separate from this
regression. No game launched; runtime parity, genuine Live identity, gameplay
acceptance and full16-layer SDK completion remain unproven.

Private evidence under `local-output/sdk-20260909/`:
`sdk-regression-20261001-scene-placement.log/.json` and
`node-checks-20261001-scene-placement.json`. Python log SHA256:
`4a52fe3e8f7923fc173298f8c6f38b6fa460193ccf72eb6ced78177ff27a595f`.

**Placement rectangle selection (2026-10-01):** Box select placements now
selects visible imported actor and static-decoration meshes through one
depth-tested renderer ID pass. Drag replaces the selection; Ctrl/Command adds,
and an empty rectangle clears it. Hidden entities/layers, ground, NPC drafts and
placed scenery are excluded. Results are canonical and bounded to128, with
atomic rejection preserving the previous selection. Hierarchy and focused
Inspector stay synchronized; the selection feeds existing mixed placement
review and saved scene selections. Escape, camera, resize and stale source
cancel gestures without a project command. Eleven focused Python checks passed
in3.214s; all33 Node files and34 editor syntax checks passed. Actual2×-DPI
pointer replacement/addition, single-actor focus, empty selection, both layer
filters, cancellation and fresh review handoff passed with zero page errors;
screenshot inspected. Saved bytes/history stayed unchanged. Private evidence:
`local-output/sdk-20260909/scene-placement-box-20261001/`. No game launched.
This selection-only feature introduces no new gameplay gate. Historical548
predates it; the full SDK objective remains incomplete.

**Mixed placement viewport handles (2026-10-01):** Retained Proposed
actor/static-decoration groups now expose X/Z handles. Every drag snaps to a
relative 64-unit offset, holding each displayed height and rotation; release
freshly reviews the full source-bound mixed proposal without a project command.
Current has no handles. Rejected/pending drags keep the prior verified matrices
and inputs; Restore cancels pending review and ignores late responses. Escape,
camera, preview/source/representation changes and resize cancel stale gestures.
Thirty-one focused retail-enabled Python checks passed in 18.361s, all 32 Node
files and 33 syntax checks passed. Actual 2×-DPI top-view X/Z pointer drags,
retained review, rejection, cancellation, Current matrices, Apply/Undo/Redo/Save
and fresh Escape/camera/resize checks passed with zero page errors; screenshots
inspected. Normal two-overlay MAN/MAP package passed exact full73728-byte MAP ZIP
readback and independent actor/grid decode, preserving prior actor/scenery edits,
height/rotation, 17 collision edits, floor tiers and saved selection metadata.
Private evidence: `local-output/sdk-20260909/scene-placement-drag-20261001/`.
No game launched; gameplay remains deferred. Historical548 predates this feature.
See [Mixed placement workflow](legaia-scene-placement-groups.md).

**Saved scene placement selections (2026-10-01):** Named project-local
selections now retain 1–128 imported actors, static decorations or mixed members.
Create/Rename/Replace/Delete use strict source-bound commands and one-step
Undo/Redo. Metadata validation remains portable without a disc; scenery Create,
Replace and Recall freshly verify static MAP identities. Cross-scene Recall seeds
actor, scenery or mixed placement tools without editing game overrides. Changed
reimport is blocked under the library and its history. Thirty-eight focused Python
checks passed in 2.554s, all 32 Node files and 33 syntax checks passed. Actual
Town01/Dolk2 browser Create/Rename/Delete/history, Save/Open, cross-scene mixed
recall, single-decoration replacement/recall/Undo and pending source/recall Cancel
checks passed with zero page errors; screenshot inspected. Private saved-project
copy retains the library; normal package is byte-identical before/after selection
metadata (SHA256 `1503a2fb0aa1c141927efac65285390afa876028bfd7ddc46f44dd70c02302fe`).
Private evidence: `local-output/sdk-20260909/scene-selection-sets-20261001/`.
No game launched. This feature requires no new gameplay gate; it does not establish
runtime placement parity. Historical 548 checkpoint predates it.
See [Saved scene selections](legaia-scene-selections.md).

**Mixed scene placement groups (2026-10-01):** Select scene placements combines
imported actors and static decorations in one bounded selection. Move scene
placement group reviews 2–128 targets, including at least one of each kind, with
common X/Z offsets in 64-unit steps within ±16320. Proposed/Current inspection
retains the review and holds preview height; runtime height remains unknown.
Fresh full-source validation precedes one atomic Apply/Undo/Redo operation across
actor and Environment overrides, preserving unrelated components and edits.
NPC drafts and placed scenery are excluded. Forty-seven focused Python checks
passed (43 in 23.086s, four HTTP checks in 2.912s); all 31 Node files and 32 syntax
checks passed. Actual 2×-DPI retail hierarchy selection, Proposed/Current matrices,
held height/rotation, no-op/input withdrawal, one-step Undo for both owners,
Redo/Save and pending Cancel/late-response withdrawal passed with zero page errors.
Fresh browser representation guards also passed without writes; screenshots inspected.
The normal package contains both MAN and complete 73728-byte MAP overlays: exact ZIP
readback and independent MAN/grid coordinate decoding preserved opaque bytes,
unselected scenery, shared rotations, existing collision edits and floor tiers.
The previous 548-test checkpoint predates this change and remains unchanged.
No game launched. Gameplay remains deferred. See [Mixed placement workflow](legaia-scene-placement-groups.md).

**Viewport source-wall editing (2026-10-01):** Select wall rectangle loads
verified source collision data and picks canonical X/Z cells directly in the
scene. Dragging prepares inclusive bounds without a project command; release
opens the existing review. Proposed/Current/Retail wall layers can be inspected
on the labelled Y=0 reference plane, with retained Return/Restore and explicit
atomic Apply/Undo/Redo, Save/Open and normal Build. Camera/source/representation
changes, Escape and pending cancellation withdraw stale gestures or reviews.
Twenty-one focused retail-enabled Python tests passed in10.570s, all30 Node
files and31 syntax checks passed. Real2×-DPI top/perspective browser drags,
comparison layers, no-op/input withdrawal, cancellation and exact full73728-byte
MAP ZIP readback passed with zero page errors; screenshots inspected.
No game launched. This postdates548; gameplay and full acceptance remain open.
See [Wall rectangle workflow](legaia-collision-rectangles.md).

**Integrated offline checkpoint (2026-10-01):** Full retail-enabled discovery
passed548 Python tests in247.512s, exit0 with no skips, on unchanged clean source
`80d4ae765f820551759f181d8372478a49358b72`. All29 Node test files and30 editor
syntax checks passed with captured file hashes. This supersedes514 and integrates
saved-copy discovery, wall rectangles/spatial comparison, scenery groups/drags,
actor transform preview refresh and scenery alignment/distribution with the
previous SDK workflows. The user-owned disc SHA256 and466714416-byte length were
freshly verified. Browser/package evidence remains separate; no game launched.
Full16-layer SDK, runtime parity, genuine Live identity and gameplay acceptance
remain incomplete. This checkpoint predates the viewport wall workflow above.

Private evidence: `sdk-regression-20261001-scenery-layout.log/.json` and
`node-checks-20261001-scenery-layout.json` under `local-output/sdk-20260909/`.
Python log SHA256:
`a247306827edfc8672e0133478dbf1d0fd83ebf6e24536f014a414b4c153da2a`.

**Scenery alignment and distribution (2026-10-01):** Arrange scenery group
aligns2–128 selected static decorations to an anchor on X/Z or evenly distributes
them between fixed endpoints using integer half-up rounding and stable identity
ordering. Other axes, shared transforms, Y/rotation, outside edits and Collision
are preserved. Fresh review, textured Proposed/Current comparison, retained
Return/Restore, atomic Apply/Undo/Redo, Save/Open and normal Build are connected.
Fifty-three focused retail-enabled Python tests passed in17.726s, all29 Node tests
and30 syntax checks passed. Retail browser alignment/distribution, input withdrawal,
comparison matrices, no-op Apply and pending-close cancellation passed with zero
page errors; screenshots inspected. Complete73728-byte MAP ZIP matches the saved
binding and independently decoded descriptor coordinates. No game launched.
Included in548; runtime visibility/collision/lifecycle remain deferred.
See [Scenery groups](legaia-scenery-groups.md).

**Scenery group drag and actor preview refresh (2026-10-01):** Proposed
scenery inspection now has X/Z handles with integer movement and optional
16/64/256/1024 snapping. Release obtains a fresh source-bound review; Apply
remains one explicit undoable command. Rejected and cancelled pending drags
retain or restore the verified proposal without saving. Canvas focus now prevents
scroll displacement during pointer gestures. Imported actor transforms now
invalidate preview identity while retaining cached geometry, fixing stale actor
positions after edits and resampling source height where Y is unknown.
Forty-five focused retail-enabled Python tests passed in16.686s; all28 Node tests
and29 syntax checks passed. Retail browser group drags, rejection/cancellation,
Apply/Undo/Redo/Save, individual actor/scenery drags and exact full73728-byte MAP
ZIP readback passed with zero page errors; screenshots inspected. No game
launched. Included in548; gameplay/full acceptance remain deferred.
See [Scenery groups](legaia-scenery-groups.md).

**Static scenery group placement (2026-10-01):** Ctrl/Command-click static
decorations in the hierarchy or viewport, or Shift-select a hierarchy range,
then choose Move scenery group. Source-bound review supports2–128 instances,
common integer X/Z offsets, retained Proposed/Current textured scene inspection,
one atomic Apply, Undo/Redo, Save/Open and normal Build. Shared offsets/rotations,
Y, unselected instances, Collision and imported identities remain preserved.
Full merged descriptor capacity, signed range, source/metadata/selection guards
and exact zero-offset no-op behavior are checked. Twenty-one focused retail-
enabled Python tests passed in16.060s, all28 Node tests and29 syntax checks passed.
Retail browser two-wall workflow and full73728-byte ZIP MAP readback passed;
screenshots inspected and zero page errors. No game launched; gameplay deferred.
Postdates integrated514. See [Scenery groups](legaia-scenery-groups.md).

**Spatial wall rectangle comparison (2026-10-01):** Reviewed rectangles now
show all selected bits in a top-down Retail/Current/Proposed comparison with
canonical source X/Z bounds, quadrant placement and proposed-change outlines.
Layer switching is read-only; changed inputs withdraw the map and Apply.
Twenty-two focused retail-enabled Python tests passed in17.122s, including five
new synthetic HTTP contract tests; all27 Node tests and28 syntax checks passed.
A synthetic browser fixture checked16 bits, three layer counts, coordinate
bounds, no extra requests/writes and input withdrawal; zero page errors and
screenshot inspected. This is a source-grid diagram, not a terrain/live viewport.
Postdates integrated514. No game launched. See
[Wall rectangles](legaia-collision-rectangles.md).

Post-checkpoint feature: collision rectangle authoring passed17 retail-enabled
focused Python checks in14.410s,27 Node files and28 syntax checks. Multi-cell/
quadrant preservation, merged bounds, stale/context rejection, one-command history,
retail restoration/no-ops, Save/Open and normal package readback are covered.
Browser reviewed/applied16 town01 bits with no review writes, changed/reversed-input
withdrawal, Undo/Redo/Save, stale/extra API rejection and no-op disabled; zero errors,
compact screenshot inspected. Saved package ZIP matched the complete73728-byte
expected MAP with floor tiers preserved. No game launched; owned browser/server
stopped. Postdates514; see [Wall rectangles](legaia-collision-rectangles.md).

Post-checkpoint extension: saved editable-copy discovery passed28 focused Python
checks in4.058s,26 Node files/27 syntax checks. Fresh service/read-only listings,
edited names/metadata, incomplete/foreign/malformed receipts, scan/path/mode/source
guards, API fields and normal Open validation are covered. Retail browser checked
matching/edited/incomplete records, corruption rejection, dirty guard before Open,
Dolk2 X9536 reopen, closed pending list and Refresh with unchanged source bytes,
zero page errors and inspected screenshots. No game launched; owned browser/server
stopped. Postdates514; see [Project copies](legaia-project-copies.md).

Retail-enabled discovery passed **514 Python tests in365.743 seconds**, exit0,
no skips, on unchanged clean source `7a6459e4e29ad96f858d2a8c79eab25dabbc60f2`.
All26 Node test files and27 editor syntax checks passed on that source. This
supersedes498 and integrates saved Build comparison, raw MAN normal Build and
editable project copies with the earlier SDK workflows. The user-owned retail
disc SHA256 and466714416-byte length matched the expected source. No game launched.
Private evidence: `sdk-regression-20261001-project-copy.log/.json` and
`node-checks-20261001-project-copy.json` under `local-output/sdk-20260909/`.
Python log SHA256: `cde485238587c1200c630c4cc6306f4cbf35d7ecdb4892458df9f02b1dfe7434`.
Browser/package/rendered evidence remains separate. Native runtime parity, genuine
Live identity, gameplay and full16-layer acceptance remain incomplete.

Pre-checkpoint feature evidence: editable project copies have39 focused Python checks
passing in3.628s,26 Node files/27 syntax checks passing. Tests cover dirty-source
history/file preservation, copied templates/drafts/views/selections and referenced
TIM/TMD bytes, source metadata/file drift, size/path/mode/name guards, HTTP fields
and dirty project-open rejection. Browser copied unsaved Dolk2 X9536, blocked
dirty Open before dispatch, opened after Undo, saved independent X9600 and reopened
original X9472 with identical source bytes, zero page errors and inspected images.
No game launched; test browser/server stopped. Postdates integrated498, not a
replacement full-suite/runtime checkpoint. See [Project copies](legaia-project-copies.md).

Pre-checkpoint feature evidence: raw streamed MAN normal Build has27 retail-enabled focused
Python checks passing in79.901s, plus25 Node files/26 syntax checks. Tests cover
source offset/length, exact raw placement, no-op/clear baseline byte equality,
record/chunk structure, unaudited mutation/bad locator rejection before writes,
raw donor/dialogue/P2 transition/flag composition with raw ANM, reviewed/build audit
agreement and saved artifact verification. Existing compressed/header/texture/
animation package regressions passed. Browser mixed Town01/Dolk2 Review Build
and Build agree on ten changes/two overlays/68,930 bytes with no authored/persisted
mutation, page error or Run dispatch; screenshot inspected. Broader raw numeric
families/scenes and deferred gameplay require separate evidence. This postdates
integrated498. See [Raw MAN Build](legaia-raw-MAN-normal-build.md).

Post-checkpoint feature: saved Build comparison has 15 focused retail-enabled
Python checks, 25 Node files and 26 syntax checks passing. Coverage includes
different sources, ambiguous identities, exact record/detail/frame identity,
same-ID rejection, source/receipt drift, metadata bounds, real baseline/authored
package comparison and corrupted archive rejection. Retail browser verifies
one difference/eight identical records with no authoring or persistence changes,
same-ID client guard, malformed API rejection and corrupt-file recovery. Final
screenshot inspected after spacing/status fixes. This postdates integrated 498;
future acceptance should include larger mixed-scene audits and pending-request
context changes. See [Build comparison](legaia-build-comparison.md).

**Integrated SDK checkpoint after Build-history correction (2026-10-01):**
Retail-enabled discovery passed **498 Python tests in 368.664 seconds**,
exit0, no skips, on unchanged clean source `ba77695b6e4e86210a2d921e1e5d9935c706e611`.
All24 Node test files and26 editor module syntax checks passed on that source.
This supersedes the passing475 checkpoint and includes Project Settings,
dependency/material/effective-animation references, Build review, saved Build
history and its no-op package compatibility correction. The initial497-test
run at e49e09b0 failed four equality checks and one guard-order check; its evidence
is retained, and the unchanged regressions now pass in full discovery.
The user-owned disc SHA256 and466714416-byte length matched the expected source.
No game launched. Browser/package/rendered evidence remains separate, and native
runtime parity, genuine Live identity, gameplay and the full16-layer plan remain
incomplete. Private evidence: `sdk-regression-20261001-build-history-fixed.log/.json`
and `node-checks-20261001-build-history-fixed.json` under `local-output/sdk-20260909/`.
Log SHA256: `dd9141e0657fce546357327f9750709553de66284299018ba7353a218761ac28`.


The previous failed497-test discovery is retained as evidence. The corrected
full result above supersedes the historical passing result below.

**Historical integrated offline checkpoint (2026-10-01):** Retail-enabled
Python discovery passed **475 tests in 279.577 seconds**, exit0, no skips, on
unchanged clean committed source `9084e5454bd8e191f4f4b03e01f4c82497564619`.
All **20 Node test files** and **22 editor module syntax checks** passed on that
source. This supersedes the469-test checkpoint and includes script operand files
and atomic scene bundles, all12 catalog inspector types, bare scene URI search,
reviewed animation interpolation, and normal raw/compressed animation Build.
The final browser additionally verified observed authored-state changes withdraw
both interpolation Apply and review; baseline restored with zero page errors.
Independent user-owned disc SHA256 and466714416-byte length matched prior input.
No game launched. Native runtime parity, confirmed Live actor identity, gameplay
and the complete16-layer acceptance plan remain incomplete. Private metadata:
`local-output/sdk-20260909/sdk-regression-20261001-animation-build.log/.json`;
Node/syntax source hashes and results:
`local-output/sdk-20260909/node-checks-20261001-animation-build.json`.
Log SHA256: `2ceab6a68dee7a3088ff6faac10b73310931e1917b16cc0c4dcc206c4239791e`.

## Previous integrated checkpoint


**Previous integrated offline checkpoint (2026-10-01):** Retail-enabled
Python discovery passed **469 tests in 176.301 seconds**, exit 0, no skips, on
unchanged clean committed source `d948b2a0f27e77c2b60f17b490ca7d8878389646`.
All **17 Node checks** and **19 editor module syntax checks** passed on that
source. This supersedes the 463-test checkpoint and includes asset field search,
atomic group preset Apply, detached group scene inspection and SDK asset inspector
tools. The user-owned disc SHA256 and 466714416-byte length were independently
verified. Existing browser, package and saved-project evidence remains separate;
this does not prove native runtime parity, Live actor identity, gameplay or all
16 acceptance layers. No game launched. Private command/source/result metadata:
`local-output/sdk-20260909/sdk-regression-20261001-asset-inspectors.log/.json`;
Node/syntax file hashes and results:
`local-output/sdk-20260909/node-checks-20261001-asset-inspectors.json`.
Log SHA256: `eed72436dcc91f0631446e3786abeb42a58964fa8e8bfd967c68a33967da7de4`.

## Fixtures and execution policy

P0 protects memory, provenance, source bytes and basic boot; P1 covers primary
authoring workflows; P2 covers format breadth and diagnostics; P3 covers polish
and longer performance comparisons. Pure/synthetic tests run on Windows and
Linux without game files. Retail checks require `LEGAIA_DISC_BIN`, validate its
exact SHA-256 and skip clearly if absent. BIOS-dependent runs also require a
user-controlled BIOS path. Never download or commit those inputs.

Golden fixtures contain structural counts, stable IDs, digests and expected
diagnostic categories, not disc bytes, model/texture/dialogue payloads,
screenshots, savestates or cards. Generated evidence belongs under ignored
`local-output/`. Bounded quick checks should finish in under a minute; actual
boot/audio/transitions are separate 2–10 minute manual or environment-gated
runs. Long stress/performance captures are opt-in and record build provenance.

| Layer | Priority | Required assertions | Fixture / platform / approximate budget |
|---|---|---|---|
| 1. Pure logic | P0/P1 | Stable structural IDs, coordinate inverses, semantic claim ordering, finite authored values, no imported mutation, dependency identity | Synthetic Python; Windows/Linux; <10s |
| 2. Binary readers | P0 | Truncation, integer overflow, pointer alignment, bounds, malformed ISO/PROT/CDNAME/LZS/MAN/TMD/TIM, unsupported records fail with source context | Independently generated byte fixtures; Windows/Linux; <30s |
| 3. town01 golden | P1 | Exactly 52 actors, 119 models, 52/52 references; deterministic repeated import and stable identities | Metadata-only expectations plus `LEGAIA_DISC_BIN`; <30s |
| 4. Andrew parity | P1/P2 | Compare pinned-source interpretations and independently decoded model indices/geometry topology; document disagreements rather than bless identical bugs | Optional exact pinned checkout and local disc; no production dependency; <60s |
| 5. Retail import breadth | P2 | Multiple towns/fields; bounded catalog pagination; explicit unsupported scene taxonomy; no empty-success output | Env-gated disc, scene label list; <60s bounded batch |
| 6. Generic protocol | P0 | Capability negotiation, identity mismatch, malformed requests, region and byte budgets, non-RAM rejection, timeout, response-size limit, no memory writes | Compiled handlers and fake transport; Windows/Linux; <60s |
| 7. Layout profiles | P0 | Exact serial/text identity, confidence and evidence, safe prefix/range budgets, profile hash determinism, unsupported build rejection | Synthetic profile validation; no RAM dump; <10s |
| 8. Save/restore lifecycle | P0 | Repeated restore advances/invalidates guards and witnesses, stale native rejected, loaded RAM revalidated, frame rollback rejected, soft restart invalidates session | Compiled loader fixture plus env-gated save lifecycle; <60s / manual 5min |
| 9. Overlay replacement | P0 | Same address/different bytes reject stale static and dynamic ownership; matching bytes only reenable correct image; no 0899 in accepted inventory; split growth/shrink/restat | Executable synthetic CMake fixtures; Windows/Linux; <60s |
| 10. CD/XA/audio | P0/P1 | FIFO/IRQ visibility deadlines, seek refresh, audible continuity through FMV and battle loads, distinguish nonzero samples from acceptable sound | Source contract plus oracle/retail capture; manual 5–10min |
| 11. Windows/input | P0/P1 | Hidden/default startup, normal launcher, headless bounded check, debug port1/2 isolation, physical controller continuity, timed release and soft reset | MSVC Release and two-controller/manual check; 2–5min |
| 12. Scene transitions | P1 | Boundary observations invalidate old scene epoch, no retained stale actor selection/correlation, field-battle-field and world-map transitions | Synthetic boundary sequence plus retail route; <30s / manual 10min |
| 13. Actor traversal | P0 | Null, misalignment, out-of-region, loop, duplicate, maximum nodes/bytes/requests, partial/truncated reads, mutation during traversal, epoch changes | Safe 0x9C synthetic nodes and fake guarded transport; <30s |
| 14. Serialization/build | P0/P1 | Unchanged decode/encode preserves exact bytes; edited fields only change intended semantics; opaque bytes retained; source hash mismatch and compression capacity errors; package independently validates | Synthetic MAN/LZS plus env-gated private package; <60s |
| 15. Editor workflows | P1/P2 | Import/select/pick/drag/numeric edit/clear/undo/redo/save/reopen, dirty protection, narrow layout, model object preview, stale request rejection, separate imported/authored/live values | Browser against local Python service; synthetic scene and optional retail; 2–5min |
| 16. End-to-end modified game | P1 | Build one representable actor move, launch exact new executable with package, observe visibly modified placement, revert package restores retail; record audio and transition continuity | Private disc/package/runtime outputs; manual 5–10min |

## Acceptance details

Runtime identity must include executable content, runtime build and logical
session, not merely an executable filename. Observation freshness requires
matching lifecycle, requested execution witnesses and bounded page/region
guards before and after sampling. A nonzero frame counter alone is not a
valid scene observation. Never use restored runs as performance truth until
the restore and ownership layers pass with that exact build.

Model checks separate raw geometry, object-local shape, texture coordinates,
pixel decoding, palette interpretation, skeletal assembly and animation pose.
A successful file export or nonblank preview proves only the checked layer.
Unknown record flags and opcodes stay opaque until independent evidence exists.

Build acceptance has three distinct steps: serializer tests, runtime package
validation, and an actual modified-game run. An exported project or syntactically
valid manifest is insufficient for the final step. Nonrepresentable edits must
identify the entity, property and supported encoding rather than silently round.

The lightweight checks already implemented should remain small. Add new suites
at the listed risk boundaries when the corresponding feature is substantial;
do not generate implementation-mirroring tests merely to increase test counts.

## Additional completed targeted checks

Production snapshot tests now reject missing/duplicate/truncated known sections
before mutation, preserve MDEC FIFO contents on either allocation failure, and
resume a partially supplied MDEC command after restore. Raw and compressed
round trips, reordered sections and repeated loads pass. Unknown sections skip
within their encoded bounds; an unexpected commit-contract failure terminates
instead of returning to a partially restored machine.

The real savestate caller also rejects invalid incoming resume addresses before
guest mutation through both file and blob paths. Template acceptance now covers
capture/apply/undo/redo/save/reopen and an HTTP-level regression for the exact
Create/Apply/Delete payloads. Component tests alone had missed the Delete
route's inappropriate entity requirement; the former route fails this test.

The subsequent feature pass added executable snapshot-header rejection tests
(including omitted/truncated diagnostics), default-stack Windows mod-runtime
validation, TIM/material crops with retail provenance, strict v2 field-profile
rejection cases, conservative actor-candidate tests, and browser Build & Run /
Attach / Stop / upright textured-preview checks. These do not replace the
16-layer campaign above. Keep visible placement/revert, audible continuity,
full field-transition coverage and cold-versus-restored performance as separate
acceptance gates; a single matching MAN header is insufficient for them.

The next pass also completed a production CD controller regression that fails
against the previous unconditional XA data-ready behavior. It covers nine
mode/filter/mute/coding cases and immediate/pending/active DMA scheduling paths.
A no-input cold retail movie advanced from the former 17-frame stall to 1,337
decoded frames and movie-mode exit. This is acceptance of that reproduced stall;
a further no-input run also visibly reached the title menu after transition.
Other FMVs and audible quality require their own recorded results.

Party animation controls compare all six supported clips against unchanged
pinned reference transform functions (20,845 vertex cases). Shared textures
match an independent full-VRAM fingerprint and standalone palette crops while
preserving town01's existing catalog. Retail baseline builds also pass a real
disc serializer check: clear edits or set a retail-equivalent override, rebuild
to the same manifest-only package digest, and preserve the prior authored
package. Actual visible placement/revert remains a separate runtime check.

A single idle retail save/load also completed with paired three-by-ten-second
cold/restored windows: no sustained FPS/frame-period regression, recurrent
static-owner loss, CRC churn or new audio underruns. The nonrecurrent field VM
witness remained unavailable after lifecycle reset, so the full observer
profile correctly rejected; do not count that as observer-reacquisition
acceptance. Repeat the broader transition/restore campaign only against fresh
cold evidence, with current witness and scene guards.

Visible placement/revert acceptance now passes for town01 actor0052. The
authored savepoint appears beside Vahn at X4480/Z11904; the fresh retail build
has zero overlays, removes it from that location, and reports original
X9792/Z8512. Both runs use the same exact binary. Compare the same first-dialogue
screenshots; record that the retail guarded coordinate capture followed one
dialogue advance to reacquire a required VM execution witness.

Static GLB export checks now include binary/accessor/PNG roundtrips, path and
malformed-preview rejection, two real retail exports, Khronos validation and
Blender import/render. Editor HTTP checks reject client geometry/output paths
and invalid frame selection without writing exports or modifying project data.
The browser's selected idle frame2 also exported successfully and its actual
GLB passed Khronos validation. Animation channels and retail replacement remain
separate future features; static export acceptance does not imply them.

Central scene-preview acceptance now covers 51/52 town01 instances, 28 unique
geometries and 5,920 unique triangles. The complete request hashes the disc
once and decoded in 2.145 seconds in the recorded run. Focused tests cover
unchanged imported data, transform/undo cache reuse, returned-data isolation,
source-change rejection and HTTP rejection of client geometry/scene paths.
Parent browser inspection accepted a textured NPC's front/back, mesh-body
picking, X4544 to X4845 movement, imported-position tether, undo restoration,
and Models on/off. No browser warning/error was reported during that check.
Unknown height/facing, parked overlapping instances, script visibility and
exact PSX blending remain explicit limitations. NPC assembly additionally
passed an independent 5,028-vertex reference comparison and Blender render.

The searchable asset browser was checked with a model-reference query returning
one model and its three referring actors; category filtering isolates the model,
and an actor result selects the corresponding inspector. NPC frame stepping,
manual-rate playback/pause and selected-frame export pass in the browser. The
actual exported GLB embeds frame index4 and the selected actor/ANM provenance.
Unknown NPC timing remains null. HTTP checks reject client source bindings,
geometry, paths, invalid frame types and actors outside the active scene.

Script/dialogue UI acceptance includes actor0049's seven readable segments and
23 supported instructions, with an explicit four-byte opaque tail. Actor0001
shows a stop at0x6B for unsupported opcode0x29. Instruction rows expose encoded
successors and record offsets without claiming active runtime branches. Text
substitutions remain tokens. Bounded plain-text writing now passes project,
browser and package checks described in `legaia-sdk/dialogue-authoring.md`.
Gameplay display/revert, broader opcode coverage, relocation/control editing
and story-state evaluation still require their own evidence and campaign.

Central script-resource acceptance should cover metadata-only discovery,
script/dialogue category filtering, partial-decode status, per-PC flag/transition
references, parent-script navigation, actor selection and exact segment focus
in the authoring inspector. Source/project changes must discard stale resources.
Static references alone never pass live flag or transition-route acceptance.

The content-inspection milestone passed all 83 importer tests with private
retail input enabled and six focused HTTP/project tests. The donor-assignment
helper's seven tests establish bounded encoding, donor/channel checks,
unchanged opaque bytes and compressed-growth rejection. They do not establish
editable project integration or game behavior; those remain separate gates.

Authored TIM acceptance (2026-09-10): five writer tests cover raw retail and
synthetic compressed carriers, noops, capacity, aliases, truncation and immutable
headers; project tests cover history, persistence and tampered files. Twelve
build tests passed across textures, dialogue and assignment, including combined
guarded overlays and exact baseline restoration. Browser inspection verified
imported/effective pixels, Clear, Undo, Redo and Save. HTTP checks verified six
invalid requests leave state unchanged, original download byte identity, model
pixel propagation with unchanged geometry, and offline reopen. The native file
picker and in-game texture display/revert were not exercised.

Authored asset browser acceptance (2026-09-10) covers project-wide discovery
from an inactive scene, snapshot isolation, save/reopen and history removal/
restoration. Browser checks use town0c to open town01 actor and texture edits,
open a position template, refresh resources without duplicate rows, and inspect
authored metadata separately from source provenance. Eight focused project
tests passed; no runtime launch or new serializer behavior is claimed.

Field MAP workspace acceptance (2026-09-10): five focused foundation tests
include retail town01, biased wall lookup inversion, malformed table bounds
and overlap, source metadata and unchanged disc content. Five resource/project
checks passed, including stale source rejection and private preview separation.
Browser checks cover base-wall loading, collision/trigger/region inspectors,
toggling and refresh invalidation. Four invalid HTTP requests were rejected
without changing project state. This does not validate live collision or P2
transition execution.

Trigger-to-P2 inspection (2026-09-10): targeted importer checks cover variable
headers, all-partition bounds, section overlap, aliases, gate rejection and
fresh trigger resolution. Service checks cover changed-source rejection before
decoding and after inspection, plus private response separation. Retail checks
resolve town01 fallback trigger 0 to P2 record 38; a sweep covers all 51 eligible
references. No runtime trigger execution is claimed. Future acceptance needs
live dispatch-gate evidence before treating these references as reachable edges.

Build review (2026-09-10): focused report checks cover input metadata identity,
selection/template exclusions, audited world values, padded text and texture
hashes. Fourteen existing build tests pass with private retail input; the
combined report matches six changes in one scene, and no-op/cleared packages
are byte-identical to baseline. Browser acceptance covers the generated report,
reopening it, stale status after an edit and restored freshness after undo.
These checks establish build reporting, not gameplay execution.

Saved normal Build history (2026-10-01): 19 focused retail-enabled Python
checks include actual repeated packaging/receipt determinism, saved-project
reopen, authored-input drift distinct from package integrity, read-only file
verification, audit/manifest/payload/archive tampering, duplicate ZIP members,
missing/invalid receipts, reparse/path rejection and bounded immediate scans.
The focused set also retains normal Build review and raw/compressed animation
packaging regressions. All24 Node files and26 syntax checks passed; strict browser
contracts reject false gameplay/disc-integrity claims and malformed identities.
Fresh-server browser acceptance reopens a saved real nine-change report, verifies
package files, displays older-build receipt absence and rejects malformed routes.
No authoring/Build/Run request, persisted metadata change or page error occurred.
The corrected wide report screenshot was inspected. These checks postdate the
integrated475 checkpoint. Future acceptance should cover larger mixed-scene
histories, concurrent external filesystem changes and deliberate project context
switches during pending history requests; no atomic filesystem snapshot or
gameplay acceptance is implied. See [Build history](legaia-build-history.md).

Texture runtime acceptance (2026-09-10): one cold authored TIM run and one cold
zero-overlay baseline visibly show replacement and removal of the magenta
ground palette. Both processes exit zero without restore or RAM writes.
Manual early witness requests allow the baseline to pass the unchanged v2
observer. A separate bounded startup verifies automatic readiness preparation,
with all three PCs primed and scene verification still false. Twelve focused
service/profile/readiness tests cover identity rejection, missing/current reply
handling, malformed/partial priming and no fabricated scene acceptance.

A subsequent full cold New Game independently validated automatic preparation:
town01's unchanged v2 guard accepted 90 nodes and all three current witnesses,
without manual witness requests or restore. Both owned processes exited zero;
see `legaia-sdk/automatic-witness-field-acceptance.md`.

Live following (2026-09-10): the focused browserless harness executes the real
controller source with delayed responses to check epoch chaining, after-response
cadence, no overlap, command serialization, cancellation, one state refresh on
HTTP rejection, and no transport retry. Candidate checks cover finite positions,
display conversion, epoch mismatch and the 128-entry bound. Ten observer-service
tests pass, including rejection of a revoked token/backwards frame before actor
traversal and acceptance only after a new guarded capture. These are targeted
checks, not the complete cross-scene or repeated-restore campaign.

## Source-bound animation GLB workflow

Targeted checks cover GLB accessor/timeline guards, equivalent quaternion byte
preservation, source-nearest Euler/quantization, real Blender edit/re-export,
shared contribution ownership, stale review rejection, proposed pose inspection,
Undo/Redo, Save/Open and independent normal Build bank readback. Private retail
fixtures cover compressed Town01 and raw-stream Dolk2 animation banks. Browser
checks exercise the actual dialog and history workflow without any game request.
Gameplay clip selection and retail cadence remain deferred. See
[animation GLB workflow](legaia-animation-glb.md).

## Scenery yaw milestone — 2026-10-02

Scenery yaw milestone: ten focused Python cases (no skips), Node matrix/drag/scope guards, frontend syntax, twelve actual browser checks and one actor-handle regression passed. Browser cases cover individual/shared pointer drags, history, Save/Open, Escape/resize/source cancellation, Retail layer, narrow layout and normal Build. Resize assertions count command requests after cancellation to avoid async false positives. Independent package readback verifies exact bytes171/6987 and preservation of prior Collision/offset edits. Manual gameplay remains deferred for visibility, scripts and collision acceptance. See [workflow and evidence](legaia-scenery-rotation-gizmo.md).

## Scenery group rotation — 2026-10-02

Seven focused Python cases cover all quarter turns, source yaw wrapping/high words, axis/ownership preservation, turn0 metadata no-op, source/range/capacity rejection and strict HTTP review/atomic Apply/history/stale guards. Rotation-group and existing group Node guards pass. Twelve actual browser scenarios cover no-op, qualified preview, Current/Return, Apply/history/persistence, normal Build, changed input, pending-close and source withdrawal. Browser assertions read the actual preview Environment binding rather than a nonexistent state.overrides field. Independent full MAP ZIP comparison and expanded matrix arithmetic pass; a separate540px regression checks every label/select/button bound and visual review confirms wrapping. Gameplay visibility, collision and scripts remain deferred. See [workflow](legaia-scenery-group-rotation.md).

## Source-normal direction diagnostic — 2026-10-02

Source-normal milestone:43 focused Python cases (no skips), two Node guard suites and syntax checks passed. Coverage includes primitive layouts, normal references and vectors, normal-table structural bounds, authored composition, animation/partial poses and scene cache refresh. Independent all119-model raw comparisons passed. Ten integrated browser scenarios cover static coverage, normal/surface buffer and framebuffer invariants, Retail/Authored viewing, real vector Apply/history/Save,540px wrapping, animated disablement/playback, normal Build and independent GPU pixels/picking. Vector Apply uses /api/model-vector and closes its editor; the harness tracks that mutation endpoint and waits for updated source data. Disabled-option assertions inspect the actual DOM disabled property. Independent compressed package readback verifies three new normal bytes, preserved earlier edits and exact neighboring data. Gameplay/retail lighting and animated normal transforms remain deferred. See [workflow](legaia-model-source-normals.md).
