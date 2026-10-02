# Legaia SDK validation plan

This is the post-feature acceptance plan, not a claim that every test exists.
The current buildout uses focused synthetic checks, retail import probes and
local browser validation. Larger automation follows connected product features.
See `FEATURE_MATRIX.md` and `legaia-release-parity.md` for actual current results.

## Latest integrated offline result — 2026-10-01

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
