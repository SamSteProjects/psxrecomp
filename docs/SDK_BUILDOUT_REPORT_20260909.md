# Legaia SDK buildout milestone — 2026-09-09

Verified stability fixes and a connected authoring workflow are implemented
on `codex/legaia-upstream-20260909`. The full modern SDK is not complete. This
record separates functioning features, demonstrated failures and remaining
product work; the detailed [feature matrix](FEATURE_MATRIX.md) and
[16-layer acceptance plan](TEST_PLAN.md) remain authoritative for scope.

## Current buildout status — updated 2026-10-01

Current buildout includes menu-label and source-bound text-file authoring, saved runtime node
review, indexed texture rectangle copying and model object
translation/rotation/scaling, instruction-to-operand navigation, flag/wait editing,
and isolated/shared model and texture proposals in the assembled scene. The dated
filename is retained for existing links. This section supersedes the historical milestone inventory and
old test counts below; those sections record what was proven at that time.

**Latest integrated offline checkpoint (2026-10-01):** Retail-enabled
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

**Reviewed animation interpolation and raw ANM Build (2026-10-01):**
The animation channel editor now blends a copied verified pose into the selected
effective pose across an existing frame range. Read-only review precedes one
Undo/Redo command; unrelated channels remain. Translation rounds to integers and
per-axis shortest-path rotation to16-unit PSX increments, with explicit tie rules.
Actual retail verification exposed normal Build assuming all ANM banks were
compressed. Normal Build now reuses the source-preserving patch service for raw
and compressed banks with preimage/carrier checks. Thirteen focused Python
checks passed with retail input, including both normal Build layouts and existing
streaming composition; all20 Node files and22 editor syntax checks passed.
Retail browser passed review, stale-range rejection, Apply/Save/Undo/Redo and zero
errors. Independent reopened package matched all114764 bank bytes, preserved
other payloads and four drafts. Screenshots inspected; baseline restored.
No game launched or disc installed. Gameplay remains deferred; this postdates
integrated469. See [animation interpolation](legaia-animation-interpolation.md).

**Asset navigation inspectors (2026-10-01):** Actors, imported scenes,
actor presets and world-map landmarks now use the shared SDK read-only property
and registered-action contract, bringing supported catalog inspector types to12.
Navigation retains original source and authored provenance; landmarks expose
menu coordinates and discovery indices without claiming live state or gameplay
reachability. Source/catalog/schema/capability, busy and closed guards apply.
Fixed bare `scene://` searches being misread as `scene:` filters; explicit field
filters remain supported. Eleven focused Python checks, all19 Node test files
and21 editor syntax checks passed. Retail browser verified all four new panels,
actor selection, cross-scene navigation, preset library and landmark menu/source
catalog navigation, zero author commands/errors and unchanged authored state.
Screenshot inspected. Private evidence:
`local-output/sdk-20260909/navigation-inspectors-20261001/`.
No game launched. These checks postdate the integrated469 checkpoint; gameplay
and the full SDK objective remain incomplete.

**Scene script operand bundles (2026-10-01):** The asset tools now export
and review authored numeric operands across actors and partition-two script
owners in the active scene. All owners stage before one atomic Apply/Undo/Redo;
actual shared-byte conflicts, invalid owners and changed review contexts reject.
Five focused Python checks, all 19 Node test files and 21 editor syntax checks
passed. Retail browser verified two owners/four entries, export, read-only review,
Save/Undo/Redo, invalid/stale/closed guards and zero page errors. Independent
reopen retained four drafts; detached no-draft normal builds changed only MAN
bytes 4808/4811/4816/28557, with all other content payloads unchanged. Screenshot
inspected and baseline restored. No game launched or disc installed; gameplay
remains deferred. This postdates the integrated 469-test checkpoint. See
[scene operand bundles](legaia-script-operand-bundles.md).

**Script file review refinement (2026-10-01):** File controls now bind to
the script owner's authored-state snapshot. An owner edit observed during review
withdraws Apply in the UI; the server's existing stale-key rejection remains.
Reviews show a readable operand/instruction/current/proposed table, with complete
source-bound details collapsed. All 18 Node checks and 20 editor syntax checks
passed. Final retail browser checked one-command flag/model-selector/move imports,
actual partition-two asset-to-script navigation, P2 Apply/Save/Undo/Redo, stale
review withdrawal and a closed pending response, zero page errors. Baseline
restored; screenshot inspected. Independent Save/Open retained four drafts.
Detached no-draft builds matched the complete 45338-byte MAN: mixed actor edits
changed only4808/4811/4816; the P2 flag changed only28557. Raw record-table/opcode
checks established offsets independently; every other content payload was
unchanged. Private evidence:
`local-output/sdk-20260909/script-operand-files-advanced-20261001/`.
No game launched or disc installed. Gameplay remains deferred; these checks
postdate the integrated469-test checkpoint.

**Script operand JSON workflow (2026-10-01):** The script inspector now
exports authored movement, flag, wait, model-selector and transition operand
metadata. A bounded source/owner-bound file review stages every entry through
existing verified commands; one atomic Apply supports Undo/Redo and Save/Open.
Supplied entries replace their authored fields; other entries/components remain.
Duplicate/nonfinite/extra/oversized files, wrong source/owner and stale reviews
reject without partial edits. No instruction bytes, dialogue, control-flow layout
or runtime state are transferred. Nineteen focused Python checks, all 18 Node
checks and 20 editor syntax checks passed. Retail browser verified export,
read-only review, Apply/Save/Undo/Redo, wrong-owner rejection and restored baseline,
zero page errors. Screenshot inspected. Independent reopen retained all four
NPC drafts; a detached no-draft normal Build matched the complete 45338-byte MAN
with only offset4811 changed for owner0003's selector240→239. Other content
payloads were unchanged. Package SHA256:
`e440d265be2a20a7008801e89c60eb1de8adc586ef3cac470e6ad22dc4aad53e`.
Normal Build still rejects drafts. Private evidence:
`local-output/sdk-20260909/script-operand-files-20261001/`. This postdates the
469-test integrated checkpoint; execution/gameplay remains deferred. No game
launched or disc installed. See [operand files](legaia-script-operand-files.md).

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

**SDK asset inspector tools (2026-10-01):** Asset Details now uses the
same SDK property/action contract as actor inspectors for eight catalog types:
models, textures, animations, scripts, dialogue, collision, triggers and regions.
SDK metadata supplies labels, read-only stable identity/source properties and
capability-bound tools; explicit type-specific handlers open the existing
verified workspaces. Details is now a consistent entry point, while asset-card
shortcuts remain. Changed source/catalog record/schema/capability, busy state and
closed dialogs block dispatch. Duplicate authored-open buttons are removed for
these types; authored details and source provenance remain separate. These are
inspector tool groups, not invented or persisted entity components. Eleven
focused Python checks, all 17 Node checks and 19 editor syntax checks passed.
Retail browser opened all eight Details panels through actual browser buttons,
loaded model/texture previews and opened the resource tools; busy/closed guards,
unchanged actors, zero author commands and zero page errors passed. Screenshot
inspected. Evidence: `local-output/sdk-20260909/asset-inspector-20261001/`.
This postdates the integrated 463-test checkpoint. Specialized editing forms,
other asset types, runtime identity and gameplay still need further work.
No game launched.

**Group preset scene inspection (2026-10-01):** The extension adds read-only Current/Proposed comparison in the assembled
3D scene for position, appearance and combined group presets. Return retains the
review for atomic Apply; Restore, changed selection and a closed pending request
discard it. Preview preserves the camera and unknown guest Y, and writes no
actor components. Markers and framing now use the active proposal's display
coordinates, matching its rendered meshes. Twelve focused Python checks, all 16 Node checks and 18 editor module syntax
checks passed. The final scene screenshot was inspected. All three scopes also passed the production
decoder against freshly verified retail-source scene responses. The retail browser
checked two changed actors, Current/Proposed/Return, Restore, late-response and
selection guards, Apply/Save/Undo/Redo, matching marker coordinates and unchanged
camera, with zero page errors. Independent normal Build readback matched the
entire 45338-byte MAN with only five expected donor/position bytes changed; all
other package payloads were preserved. Normal Build proof used a detached view
without drafts; projects containing drafts remain rejected. Private evidence:
`local-output/sdk-20260909/preset-batch-scene-20261001/`. These changes postdate
the integrated 463-test checkpoint. Gameplay and
runtime parity remain pending; no game was launched.

**Actor group presets (2026-10-01):** Position, appearance and combined
presets now review all 2–128 selected imported actors before one atomic Apply /
Undo/Redo command. Fresh source/target/donor compatibility, canonical membership,
stale-key rejection and no-op groups reuse existing commands on a detached
staging view. Absolute axes and possible overlaps are explicit; unrelated data
and unknown Y remain preserved. Eleven focused Python tests, all 15 Node checks
and 18 editor syntax checks passed. Retail browser group review/Apply/Save/Undo/
Redo passed without preview writes or page errors; screenshot inspected.
Independent Save/Open retained all four NPC drafts. A detached no-draft normal
Build package matched the complete 45338-byte town01 MAN with exactly target 0012
X changed from 3008 to 2944 at offset 8498. Package SHA256:
`a59e32eaf00f07971a0f36eb83ff10529eea908d34dd98404f07042bc6cf6567`.
Normal Build still rejects drafts; no game launched or disc installed. This
postdates the 463-test checkpoint; gameplay remains deferred. See
[group presets](legaia-actor-group-presets.md).

**Asset browser field search (2026-10-01):** Search now supports name,
stable ID, type, scene, model reference, recorded confidence and provenance
filters, quoted phrases and exclusions. Unknown fields and malformed/oversized
queries show errors without broadening results. Existing category and resource
scope remain; recorded confidence and model matches do not establish aggregate
certainty or runtime use. All 14 Node checks and 17 editor syntax checks passed.
Retail-source browser verified field combinations, imported/authored model users
against the SDK reference graph, phrases/exclusions, provenance, URI IDs, errors,
reset and actor navigation without authoring commands or actor changes, zero
errors. Screenshots inspected; narrow-panel controls now wrap. This postdates
the 463-test checkpoint. No game launched. See [asset search](legaia-asset-search.md).

**Historical integrated offline checkpoint (2026-10-01, 463 tests):** The retail-enabled SDK
Python discovery suite passed **463 tests in 264.543 seconds**, exit 0, no skips,
on unchanged committed source `2ca0a1a4fa0044f55e9b0dc6d6c217b9e061f578`.
This supersedes the 457-test checkpoint and includes the later SDK animation/preset
inspector actions and saved scene views. All **13 Node checks** and **16 editor
module syntax checks** passed separately on the same source. The disc SHA-256
was independently verified against the recorded retail source. Browser, package,
saved-project and rendered acceptance retain their separate evidence; this suite
does not establish native runtime parity, Live actor identity or deferred gameplay.
No game was launched. Private command/source/result metadata and log:
`local-output/sdk-20260909/sdk-regression-20261001-scene-views.log/.json`;
Node/syntax hashes/results: `local-output/sdk-20260909/node-checks-20261001-scene-views.json`.
Log SHA-256: `5509fa89b90dd8f040c80c33bc7f75cb02cd7cf0e38ac100361772f009d16111`.

**Saved scene views (2026-10-01):** Named project-local camera bookmarks
retain projection, target/orbit/distance, authored/retail representation and scene
layers, bound to the imported scene hash. Recall supports cross-scene navigation
without actor edits or a history command; metadata create/rename/update/delete
support Undo/Redo and Save/Open. Stale source/review, invalid cameras and changed
source beneath saved views/history reject. Live and active proposal inspections
disable capture/recall. Camera targets are editor display coordinates, not proof
of retail height or runtime identity. Fourteen focused Python/HTTP checks and
Node validation/syntax passed. Retail-source browser checked exact display
recall, cross-scene navigation, rename/delete/Undo and unchanged actors, zero
page errors; screenshot inspected and button wrapping corrected. This postdates
the 457-test checkpoint. No game launched. See
[saved scene views](legaia-saved-scene-views.md).

**Historical runtime review comparison (2026-09-30):** Saved node reviews
now support a baseline/comparison table, coordinate sample differences, status
and text filters, complete decoded evidence, return navigation and metadata
export. Declared scene/epoch/profile mismatches reject; matching node keys remain
unconfirmed because v1 has no process or object-lifetime identity. Missing axes
and numeric overflow retain unknown deltas; file-only keys do not imply spawning
or removal. Node checks and synthetic browser comparison/filter/download/return,
context rejection and closed-read withdrawal passed, zero page errors or authoring
requests. Project/camera/runtime state was unchanged. Screenshot inspected. This
postdates the 441-test checkpoint; no real runtime capture or game launch occurred.
See [saved runtime reviews](legaia-runtime-node-review.md).

**SDK animation and preset actions (2026-09-30):** Four more actor tools
now consume SDK action descriptors and registered handlers: imported scene
animation preview, Edit-only channel authoring, eligible reference animation
preview and the preset library. The SDK supplies reference-clip eligibility as
detached view metadata without modifying imported components. Unsupported actions
are omitted; source/selection/busy/Edit guards remain in dispatch. Eight focused
Python/HTTP checks and Node action eligibility checks passed. Retail-source
browser opened all four existing tools, checked unsupported/busy guards and
confirmed no actor changes or authoring commands, zero errors; screenshot
inspected. Specialized tool forms and asset actions still use their existing
adapters. This postdates the457-test checkpoint. No game launched. See
[inspector contract](legaia-inspector-schema.md).

**Historical integrated offline checkpoint (2026-09-30, 457 tests):** The retail-enabled SDK
Python discovery suite passed **457 tests in 178.185 seconds**, exit0, no skips,
against unchanged committed source `3c8d8f46af7063f2993d49fe74ec02e6a0005639`.
This supersedes the 441-test checkpoint and includes the later draft repetition,
project transition discovery, SDK inspector services, combined actor preset
review/projection and preset file transfer/source protection. All12 Node checks
and10 module syntax checks passed separately on the same source, including the
inspector registry, model-user selection, historical review comparison and
combined preset scene guards. Browser, package, saved-project and rendered
acceptance retain their independent evidence. This does not establish native
runtime parity, real Live actor identity or deferred gameplay. No game launched.
Private command/source/result/hash metadata and log:
`local-output/sdk-20260909/sdk-regression-20260930-preset-files.log/.json`;
Node/syntax metadata: `local-output/sdk-20260909/node-checks-20260930-preset-files.json`.
Log SHA256: `d5095cd0f752881ce0fcd7212c6cfa09e5361719362b62356c20906759734732`.

**Actor preset file transfer (2026-09-30):** Position, appearance and
combined presets can export metadata-only JSON and import into a project with
the same freshly verified source import. Name/source/donor/schema review precedes
one independent library entry and Undo/Redo; actors remain unchanged. Duplicate
names, changed sources, stale reviews, extra/payload fields and bounded JSON
reject. Saved preset libraries now block changed-source reimport after reopen.
Nineteen focused Python/HTTP checks and retail-source browser export/review/import/history,
no-preview writes, size/closed-response rejection passed, zero errors; screenshot
inspected. Independent cross-project retail Save/reopen/re-export passed with
preserved components/hash and no actor/import edits. This postdates the 441-test
checkpoint. No game launched. See [preset files](legaia-actor-preset-files.md).

**Combined preset scene comparison (2026-09-30):** The combined preset
review can now inspect proposed position and initial donor appearance together
in the assembled scene. A freshly verified detached project projection preserves
current overrides/history. Proposed/Current retains the camera; Return reopens
the review for one Apply/Undo, while Restore discards the retained dialog.
Placement/display/matrix/authored-layer and donor/owner/unrelated-geometry checks
bind the scene response. Scene components, preset or selection changes withdraw
it, and scene export requires restoration. Fourteen focused Python tests and Node
preset/appearance projection checks passed. Retail-source browser comparison,
no-preview writes, camera, Return/Apply/Undo, Restore, closed delayed-response withdrawal and stale-target rejection
passed with zero page errors; screenshot inspected. This postdates the 441-test
checkpoint. No game launched; gameplay remains deferred. See
[combined actor presets](legaia-combined-actor-presets.md).

**Combined actor presets (2026-09-30):** Authored templates can capture
position axes and a verified appearance donor together. A source/target-bound
read-only review shows imported/authored/effective/proposed positions and donor;
Apply updates both components atomically in one Undo/Redo entry, retaining other
axes/components. Thirteen focused tests and retail browser capture/review/history/
Save/reload/stale rejection passed; screenshot inspected, zero page errors.
Independent disk reopen retained the preset and target edits. A detached no-draft
Build view matched every expected MAN byte, retaining earlier menus, selector,
placements and appearances; package SHA256:
`a59e32eaf00f07971a0f36eb83ff10529eea908d34dd98404f07042bc6cf6567`.
Normal Build rejects projects containing NPC drafts. Full experimental archive
readback also retained all four drafts and preset edits, SHA256:
`2f9437b5a0eda2ed4ae9eaf8bf810a6f2f9c0936942e1caae8c3c0a818e43381`.
No disc installed or game launched. Gameplay remains deferred; this feature
postdates the441-test checkpoint. See [combined actor presets](legaia-combined-actor-presets.md).

**Select effective model users (2026-09-30):** Model asset details now offer
scene-qualified selection of2–128 effective imported actor users for the existing
viewport/group tools. Retail-only assignments and NPC drafts remain separate.
Fresh SDK references, scene owners and effective assets are checked before
selection; changed or ambiguous usage rejects. No component/history command is
issued by selection. Node checks and retail browser exact membership for model0112
(actors0005/0011/0012), Dolk2-to-town01 navigation and stale-review rejection
passed, zero page errors. Screenshot inspected. A footer obstruction found during
the cross-scene check was fixed by reserving asset-list space and scrolling the
library tools. These are initial assignments; runtime script replacements remain
unobserved. No game launched. See [model-user selection](legaia-model-user-selection.md).

**SDK-driven component inspector (2026-09-30):** Project state now exposes
a versioned property contract for Transform, ModelRenderer, Animation,
ActorAppearance, RuntimeCorrelation and RetailMetadata. The editor consumes it
for layered number/reference controls, read-only properties and evidence details;
unregistered components receive escaped read-only SDK details. Transform commands
use a bounded registry adapter and ordinary ProjectService validation/history.
SDK authoring limits remain distinct from retail Build encoding, with unresolved
retail Y and project-only authored height explicit. Busy/Edit/selection/source
checks guard controls. Nine focused Python tests and Node renderer/command/
fallback/layer/detail checks passed. Retail browser X edit/Undo and project-only Y Build
issues passed, zero page errors. Retail layered appearance Clear/Undo preserved
imported/effective pairs; runtime unconfirmed state and provenance details passed,
zero errors, screenshot inspected. Six donor/model/script/candidate action buttons
now consume SDK action metadata and registered handlers, with capability/condition
filtering and Edit/busy/stale dispatch guards. Retail registered Clear/Undo and
loaded source-script inspection passed. Specialized forms, animation/template
actions and asset inspectors retain existing adapters; migration is incomplete.
This feature postdates the441-test checkpoint. No game launched. See
[inspector property contract](legaia-inspector-schema.md).

**Project-wide transitions (2026-09-30):** Project transitions now merges
source-qualified decoded scene-change references across1–64 imported scenes,
with separate source coverage, unavailable reasons and imported destinations.
Inspect source script navigates across scenes to its instruction; imported
destinations retain the existing scene navigation. Imported/authored/effective
entry operands remain separate. Five focused tests passed, including self-edge,
merged identity, unavailable source, no-write and stale-state checks. Retail
HTTP/browser discovery found3 references across town01/Dolk2,180 scripts,
88 partial,0 unavailable; cross-scene source navigation and strict request shape
passed with zero page errors. Screenshot inspected. This feature postdates the
441-test checkpoint. These references do not establish reachable gameplay routes,
complete exits or runtime scene connections. No game launched. See
[project transition guide](legaia-project-transitions.md).

**NPC draft repetition (2026-09-30):** Repeat draft previews a named series
of donor-bound NPC copies with a count and X/Z grid spacing. Proposed/Current
scene comparison and Return retain the review; Apply adds the copies in one
Undo/Redo entry. Eleven focused Python tests and Node projection checks passed.
Retail-source browser checks confirmed three copies at X2944/3008/3072, Z5440,
unchanged existing scene/assets, preserved donor pairs, no preview writes,
retained camera, Apply/Undo/Redo, Save/reload, atomic bounds and stale-source
rejection, and zero page errors. Screenshot inspected; independent disk reopen
retained all four drafts. Independent experimental PROT reopen decoded the final
MAN and verified four appended records' exact positions, initial model105 /
animation13 and script bytes equal to donor0011. Archive SHA256:
`b386fb186853a10e445030c3b7f3dc09d2dde1d3faa817acdc6fb6b7f711b262`.
This feature **postdates the 441-test integrated checkpoint**. Normal Build
rejects projects containing NPC drafts; experimental export retains its existing gates. Runtime spawning,
scheduling, collision and visibility remain unverified. No disc installed or game
launched. See [NPC repetition guide](legaia-npc-draft-repetition.md). Private
browser/disk/archive evidence: `local-output/sdk-20260909/draft-repeat-20260930/`.

**Historical integrated source checkpoint (2026-09-30, 441 tests):** the retail-enabled SDK discovery
suite passed **441 Python tests in 177.315 seconds**, exit0, no skips, against
unchanged committed source `e76b05fb1775802057e41c33a5a1e4e36301a093`. This includes
group donor appearance and its detached scene projection, actor alignment/
distribution, saved actor selections and all prior Python SDK services. It
supersedes the425-test source checkpoint below. All eight Node checks (font,
texture usage, script operands, rectangle picking, saved runtime review, actor
group scene/selection, group appearance scene and saved actor selection recall)
and five editor/renderer/group module syntax checks passed separately on the same
unchanged source. Browser/package/disk/rendered evidence remains independent;
this checkpoint does not establish deferred gameplay or native runtime parity.
No game launched. Private exact-command/source/result/hash metadata and log:
`local-output/sdk-20260909/sdk-regression-20260930-saved-selections.log/.json`.
Node evidence: `local-output/sdk-20260909/node-checks-20260930-saved-selections.json`.
Log SHA256: `d095c9718e9cb0269f99a5eeccf1f05b265051dee98984abdee197af6decbed2`.

**Saved actor selections (2026-09-30):** the viewport tool row now saves named
source-bound imported actor groups for later editing. Create, Rename, Replace
members and Delete use project commands/Undo/Redo; Save/Open retains UUID identity,
scene import hash and sorted actor IDs. Recall can navigate to another imported
scene and seed the existing placement/appearance/component tools. It changes no
actor component or command history. Stale reviews reject and refresh displayed
state; changed imports are blocked under selections or their history. Fifteen
focused Python tests passed in1.318s, plus Node recall binding checks. Retail
browser create/rename/history/member replacement/delete/Save/reload, Dolk2-to-town01
recall, placement-dialog seeding and stale rename checks passed, zero page errors.
A clipped Recall button found in the first browser run was fixed with a wrapping
dialog layout; final screenshot inspected. Independent retail disk reopen verified
saved membership/import identity and unchanged build/scene input keys. These are
editor selections, not game parenting/prefabs. No gameplay check is required for
selection metadata; authored game edits retain their existing deferred checks.
Its Python services are included in the441-test checkpoint above. No game launched.

**Actor group alignment/distribution (2026-09-30):** **Actor group placements**
now offers Align X/Z to a selected anchor and Distribute along X/Z, alongside
offsets. Alignment preserves its anchor; distribution preserves coordinate
endpoints and sorts ties by stable source ID. Interior coordinates round to the
nearest retail64-unit grid (ties upward), with adjacent gaps differing by at most
64. Insufficient span rejects before mutation. Retail/Authored/Effective/Proposed
review, no-write scene comparison/Return/Restore, atomic Apply/Undo, Save/Open and
existing Build serialization are connected. Only changed axis values are authored;
height, facing, source and unrelated components remain unchanged. Ten focused
Python tests, existing Node group checks and two retail browser workflows passed;
zero page errors. Town01 actor0013 distribution Z changed2880 to3648 while endpoint
actors0012/0011 remained1856/5440. Independent ZIP/LZS MAN readback matched every
expected byte, retaining donor assignments, earlier placements, three menus and
selector240. Screenshots inspected. No game launched or package installed; the
441-test full checkpoint includes its Python services. See
[group placement guide](legaia-actor-group-offset.md). Gameplay remains deferred.

**Actor group appearance scene comparison (2026-09-30):** reviewed donor
assignments now offer **Inspect group appearance in scene** before Apply.
A detached SDK projection resolves the verified initial model/animation pair at
both actors' existing placements. Proposed/Current switches preserve the camera;
Return retains the donor review, Restore discards the comparison, and export
requires restoration. Source or placement/group changes withdraw the comparison;
closed delayed responses cannot attach. Seventeen focused retail-enabled Python
tests passed in 7.010s, no skips; the new Node projection checks passed. Town01
actor0011/0012 browser comparison verified changed geometry, unchanged positions,
transforms and unrelated geometry/texture content, no inspection writes, retained
Return/Apply/Undo, Restore, source withdrawal and delayed-response discard. Zero
page errors; comparison screenshots inspected. Shared pose geometry may identify
a different first source actor after deduplication; only that attribution is
ignored when comparing unaffected geometry, retaining model/animation evidence.
No game launched or package installed. This feature postdates the425-test full
checkpoint; its Python services are now included in441. Private evidence: `local-output/sdk-20260909/group-appearance-scene-20260930/`.

**Actor group donor appearance (2026-09-30):** selected imported actors now
share a donor-backed initial model/animation assignment through Group appearance.
Discovery intersects freshly verified compatible pairs across every actor; source,
object-count and initial-animation restrictions remain explicit. Preview separates
Retail/Authored/Effective/Proposed data without writes. Apply revalidates the whole
group before one command/Undo entry, preserving other components. Sixteen focused
retail-enabled tests passed in 7.005s, no skips. Town01 actor0011/0012 had12 common
donors; browser discovery/preview/Apply/Undo/Redo/Save and stale last-member rejection
passed, zero page errors. Actor0001/0002 correctly had no supported pair. Screenshot
inspected. Independent saved-project/package MAN readback matched exact donor
assignments and retained positions, three menus and selector240. No game launched
or package installed. Its Python services are included in the441-test full checkpoint; see
[group appearance guide](legaia-actor-group-appearance.md). Gameplay is queued.

**Historical integrated source checkpoint (2026-09-30):** the retail-enabled SDK discovery
suite passed **425 Python tests in 172.910 seconds**, exit 0, no skips, against
unchanged `55f5db15ec610db8642e1e995c29a0b4c6855730`. This includes actor group component
review/revert and all earlier Python services, superseding the 421-test checkpoint
and historical lower counts below. All six Node checks and editor/group/renderer
syntax passed separately against the same source, including box/range guards.
Browser/package/rendered checks retain their independent evidence; this run does
not establish gameplay or runtime parity. No game launched. Private log/metadata:
`local-output/sdk-20260909/sdk-regression-20260930-group-components.log/.json`.
Log SHA256: `69e0a61d32f73d1b313b00b543b0199f8787519991430e17eff44e23c31be60c`.

**Actor group component review/revert (2026-09-30):** selected imported actor
groups now offer Review group components, showing each actor's authored settings
or retail inheritance. A source-bound review includes every selected actor,
including inherited members; Revert validates the whole group before removing
only the chosen component, with one Undo entry. Other components and imported
provenance are preserved. Fifteen focused group/component/history tests passed
in 1.771s with no skips. Retail town01 three-actor browser review, atomic Revert/
Undo, unrelated-component preservation, stale inherited-member rejection and
closed pending-response checks passed with zero page errors; screenshot inspected.
A private fixture was saved during preparation; no game or package installation.
The 425-test source checkpoint includes this backend addition; browser evidence
remains separate. See
[component review guide](legaia-authored-component-review.md).

**Actor box and hierarchy range selection (2026-09-30):** Box select actors
now draws a marquee and gathers visible mesh IDs from one depth-tested render,
read in bounded strips. Shift-click selects a range in the filtered hierarchy;
Ctrl/Command adds boxes or ranges to the existing group. Replace/add operations
retain the 128-actor bound. Escape preserves selection; source/camera changes
reject a pending box, and proposal inspection disables these selection tools.
Node range/merge and rectangle/high-DPI/strip/restoration checks passed. Actual
2x-DPI town01 browser ranges, exact mesh ID boxes, hidden actor exclusion,
reverse/add/empty boxes, Escape, source withdrawal and exact placement-review
seeding passed without selection-service or authoring requests/page errors.
Screenshots inspected; no Save or game launch. These UI checks are separate
from the earlier 421-test Python checkpoint. See
[group placement guide](legaia-actor-group-offset.md).

**Viewport/hierarchy actor group selection (2026-09-30):** Ctrl/Command-click
now toggles imported actors into a bounded 128-actor group, with cyan scene and
hierarchy highlights, Frame actor group, Clear group and Review group offset.
Review seeds the existing placement dialog; normal clicks retain focused-actor
inspection. Group selection is transient and sends no selection or authoring
requests. Single-actor handles are suppressed while any group is selected.
Node membership/bounds/immutability checks and real town01 hierarchy/visible-mesh
Ctrl-click, filtering, framing, seeded review, +64 X proposal drag, atomic Apply
and project-restoring Undo passed. Client source/mode guards were checked with
injected state changes; actual Live remains unavailable without a checked runtime.
Screenshot inspected; no game launched or project saved. These UI checks are
separate from the earlier 421-test Python checkpoint. See
[group placement guide](legaia-actor-group-offset.md).

**Actor group proposal drag handles (2026-09-30):** Proposed mode now offers
X/Z handles for the selected actor group, snapping relative movement to 64 units.
Release revalidates the whole proposal without authoring; Return shows the updated
offsets/table, and Apply remains one atomic command. Escape restores the prior
proposal, bounds failures reject the whole move, and Current authored mode has
no group handles. Node offset/immutability/bounds checks and actual retail town01
browser pointer drags (+256 X, +64 Z), cancellation, no-write preview, Return,
one-command Apply and project-restoring Undo passed with zero page errors.
Screenshot inspected. This UI addition was checked separately after the 421-test
Python checkpoint; no new full-suite result is claimed. No game launched. See
[group placement guide](legaia-actor-group-offset.md).

**Actor group 3D proposal comparison (2026-09-30):** reviewed group offsets
now inspect in the assembled viewport, with Proposed/Current authored layers,
Frame group, Return retaining the draft and Restore. Only proposed transforms
change; source terrain preview heights are recalculated, with unknown runtime
elevation explicit. Single-entity handles are disabled; group handles are described
above. GLB export requires Restore.
26 focused tests in 1.301s/no skips and Node guards passed. Retail town01 exact
actor transforms, unchanged geometry/unrelated transforms, camera comparison,
Return/Restore and source withdrawal passed with zero authoring requests/page
errors; screenshots inspected. Separate Return Apply/Undo and export rejection
passed. No game launched. The 421-test source checkpoint includes this addition; browser evidence remains separate. See
[group placement guide](legaia-actor-group-offset.md).

**Actor group placement offsets (2026-09-30):** the editor toolbar now
previews and applies X/Z offsets to 2–128 imported active-scene actors. Retail,
Authored, Effective and Proposed positions stay separate. All source-grid/bounds
checks complete before one atomic command and one Undo entry. History protects
all group actors during reimport; stale source/project/actor states and replay
are rejected. 23 focused retail-enabled tests passed in 9.731s, no skips. Retail
town01 browser preview/no-write/bounds/Apply/Undo/Redo/Save and closed pending
response checks passed with zero page errors. Independent saved-project/package
MAN readback matched the four placement bytes while retaining prior menu and
selector edits. Screenshots inspected; no game launched or package installed.
The 421-test source checkpoint includes this feature; browser/package evidence remains separate. See the
[group placement guide](legaia-actor-group-offset.md).

**Authored component review (2026-09-30):** Authored Assets details now
show component-level review and source-bound Revert actions for actors, P2
scripts and scenes. Removing one component preserves the others and imported
evidence; Undo/Redo and Save/Open retain normal behavior. Stale reviewed values,
source/project identities and replay are rejected before mutation. 25 focused
tests passed in 1.334s with no skips. Retail town01 browser review/revert/history/
Save and stale rejection passed; independent disk reopen retained the selector
and three unrelated menu edits. Screenshot inspected, no page errors. No game
launched. The 421-test source checkpoint includes this feature; browser/package evidence remains separate. See the
[component review guide](legaia-authored-component-review.md).

**Script model-selector authoring (2026-09-30):** reached SET_ACTOR_MODEL
signed16 operands now use source-qualified commands, separate retail/authored/
effective layers, draft dispatch display, exact instruction-field navigation,
Undo/Redo, persistence, descriptor Build and experimental streaming/append output.
Runtime model-pool bases, actual assets and restaging remain unresolved; the
viewport does not execute the opcode. 34 focused retail-enabled tests passed in
35.413s with no skips, including five selector tests covering P2 ownership and
rebased extended actor-context rejection. Node binding/editor syntax and Dolk2 browser workflows passed; screenshots
inspected. Town01 package readback matched the exact MAN, retaining three menu
edits; Dolk2 rebuilt PROT contained the exact candidate. The 421-test source checkpoint
includes this feature; browser/package evidence remains separate. No game launched; gameplay deferred. See the
[model-selector guide](legaia-script-model-selectors.md).

**Project-wide text search (2026-09-30):** the same text search panel now
covers all imported scenes, retains scene coverage/reasons and opens the owning
scene before focusing the exact edit field. Discovery uses detached views and
checks imported/source and all dialogue-override identities. Retail town01/Dolk2
found645 supported runs across180 scripts (88 partial). Eleven focused tests and
editor syntax passed. Browser layer/scene search, cross-scene/return navigation,
stale aggregate and held-response close/reopen guards passed with unchanged
text/history and zero authoring requests/page errors. Screenshot inspected.
Explicit navigation changes Active scene; discovery leaves it unchanged.
Unknown/unvisited text remains excluded. The 405-test checkpoint includes this feature; gameplay remains deferred. See [text search guide](legaia-scene-text-search.md).

**Scene text search (2026-09-30):** source-qualified dialogue/menu runs
are searchable by text, owner and retail/effective/authored layers, with pages
and exact actor/partition-two edit-field navigation. Retail town01 discovery
found267 supported runs across91 scripts (60 partial), including eight P2 runs.
Nine focused Python tests and editor syntax passed. Browser filtering, paging,
field navigation, stale text-state and closed pending-response guards passed
with unchanged project state, zero authoring requests and page errors. Screenshot
inspected. Unknown/unvisited bytes and unsupported dialogue remain excluded;
coverage is explicit. The 405-test checkpoint includes this feature; gameplay deferred.
See the [scene text search guide](legaia-scene-text-search.md).

**Retail glyph preview (2026-09-30):** supported dialogue/menu forms show
Retail, Effective and padded unapplied Draft glyph stencils and source advances.
Nine focused Python tests, JavaScript font checks and editor syntax passed.
Retail browser pixel/advance readback, invalid drafts, Discard, held-response
close/reopen and malformed request rejection passed with unchanged project
state, zero authoring requests and page errors. Screenshot inspected. Controls,
substitutions, boxes, wrapping, pager behavior and runtime tint are not simulated.
The 405-test checkpoint includes this feature; gameplay remains deferred. See the
[glyph preview guide](legaia-text-glyph-preview.md).

**Renderer newline preservation fix (2026-09-30):** the plain-glyph
writer now excludes byte0x7C (`|`), which the pinned font renderer uses as a
newline even though MES emits it as a Glyph event. Source newline bytes split
editable runs and remain unchanged; form/API/text-file/Build writes reject new
pipe characters. Legacy saved projects open without rewriting their files;
invalid pipe edits have an unavailable effective value and can be cleared or
replaced. Clear/Undo and file-based null clearing retain normal history.
58 focused retail-enabled tests passed in29.566s with no skips, plus Node binding
checks and editor syntax. Retail browser rejection and legacy Inspector/Clear/
Undo passed with no page errors; legacy Build rejection created no output.
Synthetic dialogue/menu checks prove newline-byte preservation. The town01
52-actor read-only scan found no reached newline glyphs and no offered run
containing pipe; it is not wider retail preservation evidence. This fix follows
the397-test source checkpoint. No game launched; layout/gameplay remain deferred.

**Source-bound text JSON workflow (2026-09-30):** the script Inspector
exports supported dialogue/menu runs and previews external JSON before Apply.
Only each run's `text` is editable; null inherits retail. The file retains the
complete supported collection, verified MAN identity and current text-override
binding. All changes validate before one Undo entry; unrelated components stay
unchanged. Six focused text/project tests and editor/operand JavaScript checks
passed. Retail browser export/no-op/preview/immutable-field/stale-import,
two-run Apply/Undo/Redo/Save, oversized-file and closed pending-read guards
passed. Independent saved-project/package readback matched all three authored
label runs, including the prior override. Final preview screenshot and layout
bounds inspected. The 405-test source checkpoint includes this workflow; browser/package evidence remains separate.
See the [text-file guide](legaia-text-json-authoring.md). No game was launched;
menu reachability and display/selection remain deferred.

**Menu instruction-to-label navigation (2026-09-30):** decoded picker
choices now show separate retail/authored/effective glyph-run text and links to
the exact label forms. Owner, option, PCs, targets, capacity and source tokens
must match before a link is created. Duplicate or mismatched metadata is rejected.
The retail actor0001 browser exposed all30 supported label links, focused the
exact field and retained an unapplied draft. Stale source and withdrawn report
navigation were rejected; project/camera/service remained unchanged, with zero
authoring requests or page errors. Pure JavaScript checks cover multiple runs,
partition-two owners, detachment, bounds and ambiguity. Screenshot inspected.
This is separate browser/JavaScript evidence; gameplay remains deferred.

**Menu-label authoring (2026-09-30):** source-qualified plain-glyph runs
inside decoded two-, three- and four-option pickers now use the existing
Dialogue component and Apply/Clear/Discard, Undo/Redo, Save/Open and Build paths.
The Inspector identifies picker PC, option number, source capacity and encoded
choice target. Equal-span edits preserve jump entries, continuation bytes,
control/substitution tokens and record boundaries. Ordinary dialogue retains its
no-stop gate; conflicting or aliased menu spans remain unavailable. 54 focused
retail-enabled dialogue/script/resource tests passed in29.896s with no skips,
plus editor syntax and a retail browser workflow. A saved town01 actor0001
label package independently decoded to exactly the expected MAN. This is included in the current405-test source checkpoint; browser/package evidence remains separate. Menu story
reachability, glyph layout and runtime selection are unverified. See the
[menu-label guide](legaia-menu-label-authoring.md). No game was launched.

**Saved runtime node review (2026-09-30):** the Observed nodes panel can
export decoded metadata and reopen it later in Edit mode as a historical,
read-only Inspector. Positions/capture frames, uncertain fields, evidence and
unconfirmed candidate IDs are retained; raw prefixes and guard tokens are
excluded. Saved files never set Live state/correlation or change project/camera.
Serializer and synthetic browser download/reopen/filter/stale/file-read guards
passed with zero authoring requests or page errors. All17 fields from the actual
profile decoder on a synthetic prefix were accepted. See the [review guide](legaia-runtime-node-review.md).
No real runtime capture was performed; capture/gameplay acceptance remains deferred.

**Indexed texture rectangle copy (2026-09-30):** copy an existing 4/8-bpp
image region to another location in the same texture, with draft pixels and
source/destination bounds before Apply. Overlaps read the immutable pre-copy
indices; packed neighbors, palettes, headers and VRAM layout stay unchanged.
Retail texture29 browser checks passed draft/no-write, bounds and stale-hash
rejection, no-op/no-history, Apply, Undo/Redo, Discard, Save/reopen and Build.
Independent package readback matched all pixels/palettes and the saved33312-byte
TIM; three indices/image bytes changed, zero palette words.24 retail-enabled
focused tests passed with no skips. This feature is included in the current405-test source checkpoint; browser
and package evidence remain separate. Gameplay appearance remains deferred.

**Independent animation consumer review (2026-09-30):** Blender 5.2.2 rendered
and evaluated a fresh complete Dolk2 actor0001 GLB (30 frames, ten rigid objects,
three embedded textures). All61 source-decoded samples, including half-frame STEP
holds and terminal pose, matched within0.000018 source units;24 distinct geometry
snapshots establish motion. First/middle/last renders were visually inspected.
The saved Blender scene reopened with all meshes, animation actions and three
packed textures. A reusable offline review tool and [consumer review guide](legaia-glb-consumer-review.md)
are available. Acceptance is specific to this clip; wider clips/consumers, retail
cadence, lighting and gameplay remain unverified. No game was launched.

**Animation scene comparison (2026-09-30):** supported animation inspections now
switch between the inspected animation and Current authored scene, retaining the
selected frame and camera. Switching layers pauses playback; the current layer
disables scrubbing, playback and rate controls. Returning restores the inspected
frame and slider together. A retail actor0011 JSON proposal (15 frames) passed
exact layer/placement/base checks, playback pause, Return retaining the file,
Restore, stale-source withdrawal and unchanged project state, with zero authoring
requests or page errors. Screenshot inspected. This is separate browser evidence;
retail animation timing, playback and gameplay visibility remain deferred.

**Scene proposal comparison (2026-09-30):** model-transform, model-file and
texture proposals can switch between Proposed (not applied) and Current authored
scene while retaining the proposal and camera framing. Exact layer/restore and
unchanged project checks passed in retail browser runs for shared model0074
(11 instances), a JSON model-file proposal, and texture29 (19 geometries,
31 materials, 58 instances). Texture checks also verified unchanged camera and
withdrawal on a stale scene source. These are browser checks, separate from the
390-test Python checkpoint; game appearance and retail visibility remain deferred.

**Object-transform proposal previews:** translation, rotation and uniform scale
can now be viewed before Apply, with proposed/current layers sharing camera
framing. Preview leaves project history and authored files unchanged. The 405-test Python discovery checkpoint covers these services; JavaScript and
browser checks retain their separate evidence. Gameplay acceptance
remains deferred.

**Supported flag operand authoring:** local, global and context flag-bit
serialization has focused source-preservation validation, including rebasing
source owners after an actor append. Fourteen focused flag/movement/project tests passed on
September 30. Source-qualified ScriptFlags project commands, authored summaries,
Undo/Redo and Save/Open are connected. A retail town01 actor0002 CFLAG_SET
bit2-to3 probe changed exactly one MAN byte and survived project reopening.
Ordinary Build and experimental compressed/raw-streaming exports now compose
these operands with audited source offsets. The script Inspector now supports
Apply, Clear and Discard with separate retail/authored/effective operands.
Independent package and rebuilt archive readbacks passed; see the update below. Special context side effects, unresolved
local widths, system flags and branch selectors remain unsupported. The
earlier365/383/390-test checkpoints have been superseded by the earlier392-test run
below. Browser checks for texture dependency inspection, model rotations and
script operand forms remain separately recorded. Manual gameplay verification remains deferred.

**Texture-file proposal preview:** TIM/JSON files can now be inspected before
Apply, with proposed pixels and separate retail/current payload comparisons.
Focused synthetic, retail service and browser checks passed without preview
state, history or authored-file changes. Gameplay appearance remains deferred.

- **Scene editor:** assembled textured field/world-map previews, hierarchy and
  picking, authored/retail comparison, orthographic views, coordinate location,
  actor and scenery transform handles, and inspection of supported animations.
  Full game-equivalent visibility, placement and live actor correlation remain
  unverified where the source evidence does not establish them.
- **Animation authoring:** source-bound channel editing, copy across frames and
  ranges, raw-record/JSON import and export, shared-clip conflict checks, Undo
  and persistence. Proposed files can be reviewed and posed in model/scene
  viewers without applying, then returned to the file form for explicit import.
  Supported full rigid clips export to GLB; retargeting and arbitrary clip
  layouts are still unsupported.
- **Model authoring:** same-layout TMD/OBJ/JSON replacement, complete vertex and
  normal JSON, file-change preview, direct vector Inspector editing, per-vector
  retail reset, and inspected-vertex camera location. Build audits show exact
  scalar changes and link to the matching model/vector with stale-hash checks.
  A model-view wireframe overlay exposes decoded triangle edges, including
  hidden edges; it follows preview vertex updates without authoring changes.
  Arbitrary topology/material replacement remains unsupported. Browser shaders
  do not calculate normal-based lighting.
- **Scene content:** supported dialogue, appearance, transitions, script movement,
  textures, collision and scenery edits use source-validated overrides. NPC
  drafts compose into experimental disc exports. General script/control-flow
  authoring, native spawn scheduling and story behavior remain incomplete.
- **Output and verification:** saved private projects, packages, hashes and
  independent archive/member readbacks are retained for later review. All119
  town01 models passed exact JSON round trips; a retail normal-only edit and a
  combined model/animation package passed offline readback checks.

The retail-enabled SDK discovery suite passed **421 tests in 172.966 seconds**,
exit code 0, with no skips, against unchanged committed source
`be7a5e42686119b2290643556a9827775cfb21c7`. This supersedes the 405-test
checkpoint at `cc41ded0` and includes model-selector authoring, authored component
review/revert, grouped placement commands/history and detached 3D proposal views,
along with earlier text/font/search services. Log and exact command, source,
result and hash metadata:
`local-output/sdk-20260909/sdk-regression-20260930-group-inspection.log/.json`.
Log SHA256: `4256992f5d0a3e1767a60056fbb625ce5c70b292f54373b7294743d3c7f2ef98`.
All five Node checks (font, texture usage, script operands, saved runtime review,
actor group scene coordinates) and editor/group-module syntax passed separately.
Browser workflows retain their independent pixel/render/navigation evidence;
a green suite does not establish gameplay, runtime parity or broader rendered
acceptance. Historical checkpoints below retain their dated evidence.

**Gameplay is deferred at the user's request.** These later changes did not
launch the game. Full runtime parity, normal lighting, wider scene/animation
playback, world-map behavior, MAPDSIP coverage and documented runtime acceptance
remain open. The full SDK goal is active, and offline work is not exhausted.

For current details use [SDK status](SDK_STATUS.md),
[feature coverage](FEATURE_MATRIX.md), and the
[deferred gameplay queue](legaia-gameplay-verification-queue.md).

## Historical September 9 milestone evidence

## Source and preservation

The starting revision was `56892d6216cf1ccf87d4a376c8e0feec67ac4182`, based on
upstream `1a64f611`. Recovery ref
`codex/recovery-legaia-stability-20260909` retains that starting point.
Changes are local commits in Recomp. No push or sibling-repository mutation was
performed. Existing generated game/BIOS sources were read by an isolated build;
they were not regenerated or edited. The sibling known-good binary is preserved.
Its mixed source/build provenance is documented in
[the release ledger](legaia-release-parity.md), rather than inferred from a tag.

Disc images, BIOS, decoded retail assets, screenshots, PCM, cards, snapshots,
private projects/packages and build outputs stay outside tracked source under
ignored local paths. Existing `.codex-remote-attachments/`,
`integrations/legaia/inspector/` and `legaia-release/` remain preserved, untracked
material. No proprietary payload was added to these commits.

## Implemented milestones

| Commit | Result |
|---|---|
| `189a2d24` | Static overlay inventory regeneration, restore ownership invalidation and independent controller-port injection. |
| `4d7e955f` | Integrated disc import, scene hierarchy, authoring project, undo/save/reopen and model inspection. |
| `aa3b22ab` | Exact unchanged MAN/LZS round trip and guarded private placement packages. |
| `bae00098` | Generic mod installer resolves assets at their final installed paths. |
| `be90a25d` | Guarded runtime observation and actual mod-sector consumption diagnostics. |
| `c8e69ccd` | Default-stack Windows hashing fix and diagnostic-independent snapshot identity rejection. |
| `a9507c7c` | Bounded TIM decoding and conservative material-address matching. |
| `f506ec8e` | Guarded MAN/model evidence and explicit, ambiguous live actor candidates. |
| `27cf180b` | Strict, versioned town01 field execution profile and live evidence record. |
| `ce747f44` | Private editor Build & Run, owned-process Attach/Stop and upright textured previews. |
| `d1b3b229` | Validate/prepare all snapshot sections before restore; safe partial-command MDEC capacity. |
| `5d8337da` | Remove unnecessary Windows directory rename in private run staging. |
| `946c76d8` | Reject invalid incoming savestate resume addresses before guest mutation. |
| `a9478f88` | Give runtime identity the compiled source-revision stamp. |
| `85fba8a5` | Reusable authored transform templates with provenance, undo/redo and persistence. |
| `cf3a51ae` | Validate actor requirements per HTTP command so template deletion works. |
| `58794999` | Route realtime XA away from CPU data-ready interrupts; fix reproduced 17-frame FMV stall. |
| `c8378677` | Six reference-scoped field-party idle/walk clips with assembled poses, stepping and playback. |
| `487e1716` | Build verified retail baselines after clearing or reverting authored placements. |
| `d4f01910` | Decode model-scoped shared party texture uploads with independent VRAM validation. |
| `0f98218c` | Export supported textured models and static poses as private, validated GLB files. |
| `392de27f` | Connect shared party textures and current-pose GLB export to the editor. |
| `29310f0d` | Verify scene-header ANM associations and assemble 39 town01 actor poses. |
| `c0aabe0d` | Render supported textured scene geometry with mesh picking, focus and authored transforms. |
| `4f865bb3` | Build source-verified scene payloads with bounded caching and request-scoped disc verification. |
| `082e164b` | Search SDK assets and inspect NPC clips, frame exports, scripts and inline dialogue in the editor. |
| `957acb85` | Expose actor-scoped animation/export and read-only script inspection APIs with strict request validation. |
| `27014048` | Add a bounded donor model/animation assignment serializer foundation. |
| `103eb9be` | Inspect verified MAN script paths and inline dialogue with explicit opaque boundaries. |

The earlier reapplied release fixes include CD/XA response visibility,
seek-position refresh, VBlank handling and Windows startup. Current frame
pacing and host timing match `release-full-fixes`. Both inspected manifests
contain the ten intended roles; 0899 is excluded and dynamic caching remains
disabled. MAPDSIP handler seeds do not establish full native coverage.

## Verified workflow and limits

The primary editor workflow imports a verified user-owned disc, lists scenes,
selects imported actors, edits authored transforms, undoes/redoes, saves/reopens,
inspects geometry/textures and builds a private package. The run controller
checks the actual child/listener identity, executable, BIOS, disc and enabled
mod plan; Stop exits the owned child normally. Imported, authored and Live
values remain separate, and failed observation clears transient candidates.

Retail town01 import resolves 52 actors and 119 models. All 29 actor-referenced
models decode. The 96-TIM catalog yields 38 uniquely matched textured material
crops, 26 untextured materials and eight explicitly unresolved materials among
72 references. A separate verified party bank resolves all eight used textured
materials for F0/F1/F2. Six idle/walk clips assemble ten rigid object channels,
with frame stepping and playback in the preview. General NPC/battle animation,
live equipment state, texture residency and animated palettes remain pending.

The central viewport now renders 51 of 52 town01 entities using 28 unique
geometries and 5,920 unique triangles. This includes 39 scene-header poses,
independently checked across 5,028 vertices, plus supported static models and
explicit reference party idle poses. One multipart savepoint remains a marker.
Mesh-body picking, focused textured NPC appearance, authored movement, imported
position tether, undo and model visibility toggle passed browser inspection.
The source-verified request hashes the image once and took 2.145 seconds in the
recorded run. Unknown height/facing and scripted placement/visibility remain
explicit; parked and overlapping instances are retained. Full asset-category
authoring remains outstanding.

NPC playback controls and selected-frame export are now connected: actor0049's
15-frame clip steps/plays/pauses at an explicitly chosen preview rate, and its
Frame5 browser export retains actor/ANM provenance. Search spans 119 models,
52 active-scene actors and one imported scene, including cross-reference and
provenance queries. The read-only script inspector presents seven dialogue
segments and 23 supported instructions for actor0049, preserving its opaque
tail; actor0001 explicitly stops on unsupported opcode0x29. This does not
implement dialogue writes, story-state evaluation or general script execution.

The next writable foundation can borrow an existing same-scene model/animation
pair for a compatible initial MAN header. Seven focused tests pass, including
actor5 borrowing actor40's pair with only two decoded bytes changed and an exact
compressed round trip. This helper is not yet connected to authored commands,
the editor or package builder, and its gameplay behavior remains unverified.

The final importer suite passes all 83 tests with private retail input enabled;
six focused HTTP/project tests also pass. Script fixtures retain retail text
hashes and structural expectations rather than dialogue payloads. The updated
main editor remains on port4388; the private acceptance editor was closed.

Authored templates transfer saved position axes to another imported actor,
preserving unspecified axes. The browser capture/apply/undo/redo/save workflow
and reopened project were checked with a synthetic two-actor fixture. This
does not implement native actor creation or model/animation presets.

Earlier cold field runs consumed all 24,894 patched bytes across 13 sectors
without a disc guard failure and rendered Rim Elm. The v2 profile accepted 90
nodes with strict executable, witness, scene, generation and epoch checks.
An actor candidate's MAN header contained authored X9984 versus imported X9920.
Its world position was parked; this does not establish visible actor placement,
confirmed identity or successful revert. See
[the field evidence](legaia-sdk/live-field-20260909.md).

Those early private builds had empty Release optimization flags. Subsequent
builds restore standard MSVC `/O2 /Ob2 /DNDEBUG` and `/GR /EHsc`; functional
captures from the earlier builds are not performance truth. Software rendering
is the tested backend. HLE is the current shipping tier; LLE/oracle parity is a
separate acceptance task.

The earlier optimized runtime contained the runtime changes through `a9478f88`:
SHA-256 `99d4e3b6742c864c3087a73c356f0d0de51bdc623accb0e1dd8e026052e94afa`.
The protocol now reports `nightly-16-ga9478f88-dirty`. The dirty suffix includes
in-progress documentation/editor work; the ignored final validation manifest
records exact runtime source hashes independently. Its new cold run reached
New Game, name selection and Rim Elm with the authored overlay fully consumed.
After name confirmation, the editor accepted all 90 actor prefixes (14,040
bytes; 94 requests; 1,114.530 ms total) and all 90 binding samples (2,670 bytes;
31 requests; 414.146 ms). They produced 82 candidate links, zero confirmed
identities. Actor0001's candidate header still carried X9984 and its world
position was parked. Stop exited normally and cleared the Live candidates.

The opening-FMV retry was subsequently reproduced without input or restore
and traced to erroneous CPU data-ready interrupts on XA-only sectors. The old
FIFO video header was copied again, causing retail chunk validation to discard
partial frames. Commit `58794999` fixes generic sector routing. The corrected
optimized executable has SHA-256
`148c66b1d509d4728d4ea3fcd24e7267776da5ee8104db72f27cfffed625ba6e`. Its
embedded configure-time label is stale; exact binary and source hashes are
recorded independently. Two no-input cold runs decoded 1,337 movie frames;
the later run visibly reached New Game / Continue and subsequently restarted
attract playback. Both exited normally. Other FMVs and audible quality remain
separate acceptance tasks. See the release ledger for root-cause evidence.

A new authored savepoint build moved town01 actor0052 from retail `(9792,8512)`
to `(4480,11904)`. Its short source script contains no own position override.
The cold game displayed the purple savepoint beside Vahn in the opening
Village Elder dialogue, and the guarded candidate carried both the edited MAN
header and world position `(4480,-128,11904)`. All 24,894 overlay bytes were
consumed without guard failure. This proves the chosen visible edit; generic
identity correlation remains conservatively classified as a candidate. A
fresh retail-baseline run completed revert acceptance: zero overlays and zero
modified bytes, no savepoint beside Vahn in the same first dialogue, and a
guarded candidate back at retail world `(9792,0,8512)`. That final coordinate
sample followed one dialogue advance to execute the required VM witness; the
guard was never weakened. Both private processes exited 0. The complete pair
is recorded in `local-output/sdk-20260909/visible-placement-revert-acceptance.json`.

## Focused validation

One retail idle save/restore comparison now passes on the fixed binary.
Three ten-second windows measured cold/restored median 59.85/60.02 FPS and
16.6897/16.6894 ms frame-period p95; static hits remained about 5,100/second.
Save/load completed, the same scene stayed visible, and settled windows added
no audio underruns or ownership-validation churn. A nonrecurrent VM witness
was cleared by restore and did not execute again, so the strict full Live
profile correctly remained unavailable. This bounded result does not establish
cross-scene or repeated-restore performance, nor observer reacquisition.

- All 62 importer/project/serialization/texture/animation/export tests passed with the local
  retail disc configured, including the retail-gated cases.
- Twelve observer/profile/correlation tests passed, including stale identity,
  wrong backend/hash, bounded reads, ambiguity and transient-layer clearing.
- Six focused project/template/HTTP tests passed. The exact Delete request
  failed before the route-validation fix and passes afterward; malformed
  actor commands still reject without changing project state.
- Production snapshot and savestate caller tests passed malformed and partial
  files, missing/duplicate sections, raw/zlib/reordered/repeated restoration,
  allocation failures, partial MDEC continuation, blob/file resume rejection
  and preservation of the live machine on ordinary failure.
- The actual mod runtime passed with the Windows default 1 MiB stack after the
  hashing-buffer fix; the previous implementation reproduced `0xC00000FD`.
- The isolated two-worker MSVC Release build passed. Browser checks covered
  authoring, textured preview, template application, private launch identity,
  guarded Live rejection and graceful owned-process Stop.

These focused results do not replace the comprehensive plan or manual audio,
physical-controller, battle and transition acceptance. The final private
manifest, screenshots, PCM and full guarded observations are retained under
`local-output/sdk-20260909/`; none is tracked source.

The editor now also exports the displayed party pose or a full supported raw
model through Export GLB into private project `Exports`. Vahn and tree outputs
pass Khronos validation with zero errors/warnings and import/render in Blender
5.2.1. The browser selected idle frame2 and produced a ten-object, 496-triangle,
four-texture export with explicit static-pose limits. All three party idle/walk
previews were visually checked with face/clothing textures and frame controls.
That initial checkpoint did not include animated GLB channels. As of 2026-09-12,
full rigid-object clips are available through Export full clip GLB with an
explicit chosen rate. A 30-frame actor export passed Khronos validation with
zero errors/warnings and independent glTF-Transform import (10 nodes, 20 channels).
Rendered animated playback in Blender/Unity remains unverified. Native replacement
and physical-meter scale are not established by these interchange exports.

## Historical remaining-work assessment

The reproduced STR/XA stall is fixed and reaches the title menu. Muscle Dome
relocation remains unresolved: the cited old change documents a repair but contains no
recovered implementation. A title-layer fix requires the failing lifecycle and
retail comparison, not a guessed runtime address patch.

At this milestone, the SDK proved a visible savepoint edit and fresh retail revert. The following was the remaining-work assessment then; use the current status above for later implementations. Full
posed scene rendering, general animation tools, asset replacement, native
entity/templates, dialogue encoding and editing,
script opcode/CFG tools, event flags, transitions and world-map authoring are
still incomplete. Unknown semantics remain explicit. Audio continuity,
field/battle/world-map transitions, physical controller behavior and
cross-scene/repeated restore performance also remain unaccepted.

September 30 viewport authoring connection: enable **Wireframe overlay** and
Shift-click a projected vertex in an unposed model to open its exact object,
index and source XYZ in the vector Inspector. Selection does not apply changes.
Plain clicks and orbit drags do not select. Picking includes hidden vertices;
posed/proposed animation geometry, pending shape files and Live mode cannot
use this authoring shortcut. Retail browser checks verified the selected vector
and no submitted edits; projection checks cover center, behind-camera and
offscreen points.

Whole-object shape authoring: the vector Inspector now offers **Translate all
vertices in this object** with explicit integer XYZ offsets in source units.
It preserves normals, other objects and topology; validates every resulting
signed16 coordinate and the inspected model hash before applying one undoable
replacement. Zero offsets submit no change. Retail service checks proved all
vertices, preservation and exact Undo/Redo; browser checks proved Apply/readback/
Undo and disabled zero/overflow offsets. Gameplay remains deferred.

Script workspace addition: **Find a decoded instruction path** accepts a selected
start and destination and shows one shortest encoded-successor route, with
condition labels and clickable instruction steps. Cycles terminate; unknown
targets are reported as boundaries. No-path results do not establish gameplay
unreachability. Queries do not execute scripts or alter project state. Synthetic
browser checks cover branching, cycles, same-node queries and undecoded targets;
a retail actor-script path was checked edge-by-edge against its decoded report.
General control-flow authoring and live execution remain incomplete.

Script operand authoring now includes the one-byte **NPC_RUN encoded move
selector** (0–255), with retail/authored/effective values, Apply/Clear/Discard,
Undo/Redo, Save/Open and existing audited Build composition. X/Z and depth stay
unchanged when only the selector is edited. Selector behavior is unresolved;
no animation or speed meaning is assigned. Seven focused tests passed (four
separate retail streaming tests skipped without their environment input). A
saved town01 probe changed selector 13 to 14, and independent package ZIP
readback found exactly one changed MAN byte. Browser Apply/Undo passed.

EXEC_MOVE operand authoring: fixed-width encoded move selectors now share the
ScriptMovement workflow with NPC_RUN. EXEC_MOVE exposes only its move-selector
byte, with no invented X/Z or scene marker. Source-verified field offsets drive
Build audits and appended-record rebasing. Eight focused tests passed, including
all256 selector bytes with ordinary/extended headers and rejection of X/Z edits.
Retail actor0003 PC0x12 selector9->10 passed Save/Open, Undo/Redo, browser
Apply11/Undo10 and independent ZIP decode with exactly MAN byte4816 changed.
This addition follows the352-test checkpoint and has focused checks; runtime
move-table identity and behavior remain unverified.

Indexed scene texture palette authoring: **Edit selected palette** exposes
retail/effective words, RGB5/STP bit interpretation, explicit Apply, retail
reset and draft Discard. Entry changes lock while a draft is pending. Edits
are bound to the inspected effective TIM hash and use ordinary texture
replacement Undo/Redo, Save/Open and Build. Four focused synthetic/build tests
passed (one retail test skipped without its environment input); a separate
retail workflow and browser Apply/readback/Undo passed. Actual ZIP member
readback proved the saved entry change affected only TIM byte22. Other palette
entries, image data and headers are preserved. Shared/conditional banks and
runtime palette/blend behavior remain outside the accepted authoring scope.

Indexed texture pixel authoring: Shift-click the bitmap to inspect a pixel
and edit its encoded palette index. Retail/effective values and the inspected
palette colour word remain explicit. Apply/reset/Discard uses source-hash-bound
texture replacement history, persistence and Build. Four-bpp edits preserve the
other nibble; eight-bpp edits preserve neighboring pixels. Five focused tests
passed (one environment-gated retail test skipped), with exhaustive index
values at row/packed-byte boundaries. Separate retail checks passed authored
palette preservation, stale rejection, Undo/Redo, Save/Open, Build and exact
ZIP member readback. Browser Shift-click, range rejection, Discard, Apply and
Undo passed after correcting fractional canvas-edge rounding. Runtime residency
and visible/material/palette behavior remain deferred.

Indexed texture interchange: retail/effective JSON downloads and source-bound
JSON replacement now expose complete ordered CLUT words and pixel-index rows.
Existing TIM headers, bit depth, dimensions and array counts remain fixed;
duplicate keys, stale source hashes, unsupported formats and invalid values
reject before replacement. Effective JSON retains the retail source hash.
All96 indexed town01 scene textures round-tripped exactly; seven focused tests
passed (one environment-gated retail test skipped). Separate retail/browser
checks passed combined palette/pixel import, Undo/Redo, Save/Open, download/
upload and actual ZIP member readback. Existing TIM upload remains available;
file reads now reject changed texture/file contexts before submitting. No
quantization, resizing, shared-bank authoring or runtime acceptance is claimed.

Texture-file proposal preview: selected TIM/JSON files render without applying,
with palette-word, pixel-index and image-byte counts against both retail and
current authored data. Details are capped at256 changes while counts remain
complete. Return retains the file for explicit Apply. Source/layout validation
and changed-context guards precede display; Build capacity and runtime appearance
remain separate gates. Nine focused tests passed with one environment-gated
retail test skipped. Separate retail service and browser checks proved preview
leaves state/history/authored files unchanged, and Apply/Undo restores the exact
previous texture. Screenshot inspected; game not launched.

Texture Build reports now retain bounded palette-word/pixel-index/image-byte
audits with complete change counts. Changed pixel links open the effective
texture pixel editor only when its replacement hash matches the report;
older reports without payload details remain readable. Synthetic report tests
and a retail package readback verified the combined palette/pixel diagnostic
at TIM bytes22/544. This reports emitted payload edits, not runtime residency.
Browser checks passed report details, unchanged project state during pixel
navigation, and stale replacement hash rejection after a later edit.

Indexed texture rectangle fill: the editor previews an unapplied rectangle
using an existing encoded palette index, validates complete image bounds and
uses an inspected effective TIM hash. Apply creates one ordinary texture
replacement command; no-op fills create no history entry. Four-bit packed
neighbors, outside pixels and all palette words are preserved. Nine focused
tests passed with one retail environment-gated test skipped. Separate retail
checks passed stale rejection, Undo/Redo, Save/Open and actual ZIP readback;
browser draft/no-command, edge rejection, Discard, Apply and Undo passed.
This edits indices for every palette using the image; resizing, quantization,
shared-bank authoring and runtime appearance remain outside verified scope.

Project-wide flag references: imported scenes are freshly verified and scanned
without changing authored state or active selection. Scene/script-qualified
operand groups remain separate even when encoded bank/index values match;
partial/unavailable coverage stays explicit. Browser search includes scene
names, and source-instruction links navigate to the matching scene/script.
A three-scene town01/Dolk2/map01 retail probe found2142 references in899groups
across230scripts (128partial). Service state stayed unchanged. Browser coverage,
search and cross-scene instruction navigation passed with unchanged command
history; scene navigation uses the existing saved-view dirty tracking. Discovery
is bounded to64imported scenes,32768groups and262144references. Current runtime
values, shared variable identity and story names remain unresolved.

Scene texture dependency inspection: **Inspect scene texture uses** derives
static image/CLUT source contributors from the current verified scene preview,
keeps partial candidates separate from address matches, reports unresolved
materials/unavailable instances, and offers model/instance/material search plus
viewport Locate actions. Source keys guard navigation; inspection adds no
project edits/history. Focused Node checks cover shared/draft instances, CLUT
contributors, unresolved candidates, untextured exclusion, detached results and
bounds. Retail browser checks passed actor0005 navigation for texture25, and
texture29 fanout of31material matches/19geometries/58instances, scenery Locate,
empty search and stale-source rejection. Screenshot inspected. This addition
follows the365-test Python checkpoint; runtime residency/conditional visibility
and cross-scene dependencies remain unverified.

Model object quarter-turn authoring: rotate existing object vertices and normals
around their source-local origin by−90°, +90° or180° on source X/Y/Z. Exact
signed permutations preserve vector lengths, padding, topology and other objects;
signed16 overflow and stale effective hashes reject atomically. The vector draft
must be applied/discarded first. Three focused tests passed, including inverse/
four-turn restoration, all axes and invalid ranges. Separate multipart retail
checks passed object1 vertex/normal transforms, other-object preservation, stale
rejection, Undo/Redo, Save/Open and independent decompression of the actual ZIP
member. Browser draft guard, Discard, Apply, readback and exact Undo passed.
This addition follows the365-test checkpoint; gameplay shape/lighting/animation
compatibility remains deferred. Browser lighting does not use normal vectors.


Flag output integration (2026-09-30): ordinary Build now emits source-qualified
flag operands with independent audit checks for source/hash/owner/offset, upper
bits, requested bit, overlaps and unaudited changes. Build reports distinguish
flag.bit from raw operand bytes and name the source instruction. Experimental
compressed and raw-streaming exports rebase existing owners after NPC append;
flag changes participate in scene export audits. Thirteen selected tests passed
with the private retail disc and no skips (27.267s); sixteen focused project,
serializer and merge tests also passed. Retail ZIP readback changed only MAN
byte4772. Compressed town01 append reopened bit3 at rebased byte4775; raw dolk2
append composed bit24-to25 with dialogue and transition edits. Private package:
local-output/sdk-20260909/flag-authoring-project-20260930/Builds/flag-output-verified,
SHA256 adeeb217b679908845e4e9e260e31b3d22cccceb3fc0f63ab33fd502459c99bf.
Earlier foundation notes describing Build rejection are superseded by this
integration. Editor Apply remains pending; story meaning, execution, runtime
values and gameplay acceptance remain unverified. No game launched or package
installed. The365-test checkpoint predates this addition.


Flag operand Inspector (2026-09-30): supported source-qualified L/G/C flag
SET/CLEAR/TEST operands now expose retail, authored and effective bit indices
through script inspection APIs and editor forms. Apply/Clear use ordinary project
commands; Discard retains authored state. Numeric bounds and special context
SET8/CLEAR10 checks disable Apply; unapplied drafts block project history/save
controls. Unsupported scripts retain read-only reports and clearable unresolved
overrides. Failed refresh removes authoring controls. Flag Build report navigation
opens the source instruction. Six focused retail HTTP/project/merge tests passed;
HTTP checks include unexpected fields, invalid values and special context bits.
Browser checks passed layers, special-bit guard, pending draft guard, Discard,
Apply, Undo, Clear and restoration with no page errors; screenshot inspected.
Private evidence: flag-authoring-project-20260930/flag-browser-check.json and
flag-editor.png under local-output/sdk-20260909. Earlier pending-Apply notes are
superseded. Supported operand editing is connected through project persistence
and output; wider flag/control-flow authoring and gameplay acceptance remain
incomplete. No game launched. Temporary browser/server stopped.


Authored flag reference layers (2026-09-30): scene/project flag browsers now show
retail, authored and effective operands for source-qualified flag edits. Groups
keep their retail identity/index; matching effective indices never merge scripts,
scenes or unresolved contexts. Search includes effective operands. Authored
annotations pass the source serializer first; missing/stale source or unmatched
catalog identities reject, and project-wide discovery rejects state changes
during collection. No runtime values or execution are inferred. Twelve focused
flag/reference/project tests passed. Retail scene/project discovery retained
1249references with one authored operand (town01 actor0002 CFLAG_SET2-to3).
Browser layer display, retail grouping and exact instruction navigation passed
without page errors; screenshot inspected. Private evidence:
local-output/sdk-20260909/flag-authoring-project-20260930/flag-reference-browser-check.json
and flag-reference-layers.png. No edits/history were created by discovery;
temporary browser/server stopped. Gameplay remains deferred. The365-test
checkpoint predates this work.


In progress — script wait authoring (2026-09-30): WAIT_FRAMES inspection now
exposes its u16 target as duration_ticks, host_frame_delta units, signed16
accumulator width and explicitly unknown seconds/execution. Source-qualified
wait serialization changes only the two-byte target and preserves dispatch,
control layout and opaque bytes; source owners rebase after actor append.
Authored targets are restricted to0..32767 because the pinned reference uses a
signed16 saturating accumulator; larger retail targets remain unavailable.
Thirty-eight retail-enabled wait/inspection/catalog tests passed in2.226s.
Retail town01 has four eligible actor waits; actor0044 PC0x019F16-to17 changed
only decoded MAN byte24483. Dolk2 has no eligible actor waits under these source
coverage rules. Private evidence: local-output/sdk-20260909/wait-authoring-20260930/town01-wait-check.json.
Project commands, Inspector Apply and output composition remain pending; this is
serializer groundwork, not a finished editor workflow or gameplay acceptance.
Reference checkout HEAD has advanced to574ee5f603ed3ca9bd95c796711e595d9c2ad8a8;
WAIT handler evidence was read directly with git show from the unchanged SDK pin
d6e64c68ede25813d35db20980da82a1a025549b, step.rs opcode0x4A.
No reference checkout mutation or game launch occurred. The365-test checkpoint
predates this addition.


Wait project/output integration (2026-09-30): ScriptWaits commands now preserve
retail/authored/effective ticks, ordinary Undo/Redo, Clear, authored summaries
and Save/Open. Ordinary Build independently checks exact two-byte spans, requested
values, source identity and overlap/unaudited bytes. Reports expose wait.duration_ticks
and source instruction IDs. Experimental compressed/raw-streaming exporters
compose/rebase waits and include them in scene audits; new wait coverage in the
raw-streaming route has not yet received a retail wait probe. Fifteen selected
retail-enabled tests passed in27.113s without skips. A focused merge check also
passed after adding explicit high-byte and second-byte overlap cases. Retail
town01 actor0044 wait16-to17 composed with actor0002 flag2-to3; saved project,
Undo/Redo, package ZIP/decompression and appended archive readbacks passed.
The two changed decoded MAN offsets were4772 and24483; append rebased the wait
to24486. Private project: local-output/sdk-20260909/wait-authoring-project-20260930.
Package under Builds/89f66b995f838276 has SHA256
148ab35c0b9146cab17359b9a870ab054c95aa98c415a7b26be199992da50971.
Earlier pending project/output notes are superseded. Inspector Apply is next;
seconds, execution, actual timing behavior and gameplay acceptance remain
unverified. No game launched or package installed. The365-test checkpoint
predates this work.


Wait target Inspector (2026-09-30): source-qualified WAIT_FRAMES forms now show
retail, authored and effective host ticks with Apply, Clear and Discard. Targets
remain0..32767; seconds and actual timing/execution are unresolved. Ordinary
script Undo/Redo and Save obey pending draft guards. Actor, partition-two and
trigger script routes expose authoring metadata without suppressing read-only
inspection when authoring is unavailable. HTTP commands reject extra fields,
invalid tick values and malformed identities. Build report links can open the
source wait instruction. Six targeted retail-enabled HTTP/project/merge/serializer
tests passed in7.768s. Browser layer/bounds/pending-draft/Discard/Apply/Clear/Undo
checks passed and restored the saved17-tick diagnostic; zero page errors and
screenshot inspected. Initial copied browser assertion had an encoding mismatch;
corrected test text, no application change required. Evidence retained under
local-output/sdk-20260909/wait-authoring-project-20260930/wait-browser-check.json
and wait-editor.png. Earlier pending-Apply notes are superseded. Supported wait
editing is connected through project and output; wider script/control-flow and
runtime timing acceptance remain incomplete. Temporary browser/server stopped;
no game launched or package installed. The365-test checkpoint predates this work.


Instruction operand navigation (2026-09-30): decoded instruction rows now display
retail/authored/effective values for verified movement, flag and wait targets,
with Open operand editor links that focus the matching form. Encoded source
operands and graph successors remain retail evidence. A reusable client metadata
adapter requires exact PC/mnemonic/context/retail values and consistent effective
layers; mismatches, duplicate PCs and oversized metadata withdraw links. It does
not simulate execution or mutate reports. Focused Node checks passed flags,
coordinate/selector movement, waits, bounds, ambiguity, context/value rejection
and source detachment. Retail browser flag/wait rows and exact input focus passed
with no project/history changes or page errors; screenshots inspected. Evidence:
local-output/sdk-20260909/wait-authoring-project-20260930/instruction-operands-browser-check.json
and instruction-flag-layers.png/instruction-wait-layers.png. Temporary browser
and server stopped; no game launch. This JavaScript addition follows the383-test
Python checkpoint and retains separate browser validation.


Model object uniform scaling (2026-09-30): Scale whole object in the vector
Inspector edits source-local vertices by an integer percent1..1000, with positive
uniform scaling, nearest-integer rounding and halves away from zero. Normals,
vector padding, topology/materials and other objects remain unchanged. Signed16
overflow, stale inspected hashes, invalid percentages/objects and pending vector
drafts reject before applying.100% is a no-op without history. Ordinary model
replacement supplies Undo/Redo, Save/Open and Build. Five focused scale/rotation/
JSON tests passed. Retail model0009 object1 at150% composed with its existing
rotation/normal override; normal/other-object preservation, history, reopening
and actual ZIP carrier decompression matched the replacement. Browser invalid/
draft guards, Discard,125% Apply, readback and exact Undo passed, no page errors;
screenshot inspected. Initial readback harness selected a scene-specific carrier;
corrected to the recorded shared model carrier, without rebuilding/replacing it.
Private project: local-output/sdk-20260909/model-scale-project-20260930; package
under Builds/e7728cba624de600 has SHA256
9d16d794517133d474921f7e001f9dd1929cc43f51df2ff8c33aca89f09aa3cb.
No game or package installation. Gameplay shape/animation/collision compatibility
remains deferred. The383-test checkpoint predates this addition.


Model-object transform previews (2026-09-30): the vector Inspector has explicit
Preview buttons for translation, quarter-turn rotation and uniform scaling, with
an orbit/zoom canvas and Proposed/Inspected current layers under shared framing.
The server binds previews to the inspected effective SHA and uses the same
serializers as Apply, including a shared translation serializer. Invalid fields,
stale hashes, overflow and vector drafts reject previews. Input changes, dialog
close and delayed responses withdraw proposals; comparison-layer changes retain
geometry. Seven focused model tests passed. Retail model0009 object1 previews
matched exact Apply-operation bytes for all three transforms while project state
and authored-file hashes stayed unchanged. Browser checks passed all transforms,
layer comparison, draft/input guards, close/reopen and delayed-response withdrawal
with zero page errors; scale/rotation screenshots inspected. An initial browser
failure exposed comparison-select input events clearing the preview; fixed and
rerun successfully. Private evidence: local-output/sdk-20260909/model-scale-project-20260930/
object-preview-service-check.json, object-preview-browser-check.json and
object-preview-{translation,rotation,scale}.png. Temporary server/browser stopped.
No game launch, package installation or gameplay claim. The383-test checkpoint
predates this addition; full SDK goal remains incomplete.


Scene model-object proposal inspection (2026-09-30): a validated translation,
rotation or scale proposal can be inspected on one renderable instance in the
authored assembled scene. The endpoint resolves the existing source-bound pose
and applies local coordinates through its supported transforms, preserving
instance placement and source geometry. It rejects stale scene keys, wrong
asset/instance bindings and unsupported pose layouts. Proposed geometry is isolated
from shared instances and marked not applied. Restore recovers the exact scene;
Return to model vectors retains the input parameters for explicit Apply or discard.
Animation playback controls are hidden for static shape inspection and restored
when entering animation inspection. Ten focused model/pose tests passed. Retail
browser verification used environment://town01/field-map/cells/05913, model0009,
animation4/frame0; scene matrices, other instances, base scene and project state
were preserved, with exact Return/Restore and zero page errors. Stale scene keys
and unknown instances rejected without project changes. Screenshot inspected.
Private evidence: local-output/sdk-20260909/model-scale-project-20260930/
scene-shape-browser-check.json and scene-shape-preview.png. Browser/server stopped;
no game launched or package installed. Gameplay placement/visibility remains
unverified. The383-test checkpoint predates this feature; full SDK remains incomplete.


Proposed model-file scene inspection (2026-09-30): TMD, OBJ and JSON replacement
files can now be inspected on a selected supported scene instance before Apply.
The endpoint revalidates the file, inspected proposed TMD hash, active scene source
key and asset/instance binding, then uses the same pose-preserving scene proposal
service as object transforms. The selected file remains pending during inspection;
Return to model file and Restore recover the exact scene and retain it for explicit
Apply or Discard. New model contexts clear retained draft metadata. No proposal
creates authored files, commands or history. Nine focused model/file/pose tests
passed. Retail browser checks passed all three formats, one-instance isolation,
scene matrices/base/project preservation, Return/Restore file retention, discard
and stale hash/source/instance/base64 rejection with zero page errors. Screenshot
inspected. A43090-byte JSON proposal passed the upload route with exact proposed
hash and unchanged project state/authored-file hashes. Private evidence under
local-output/sdk-20260909/model-scale-project-20260930/model-file-scene-browser-check.json,
model-file-scene-large-check.json and model-file-scene-preview.png. Temporary
browser/server stopped; no game or package installation. Gameplay placement and
visibility remain unverified;383-test checkpoint predates this addition.


Shared model proposal impact (2026-09-30): object-transform and model-file scene
inspection now offer All supported model instances. Each instance retains its
existing placement and pose; proposed geometries are grouped by the source scene
geometry key rather than duplicated per placement. Nonrenderable matching instances
are reported as unavailable and remain unchanged. Unsupported renderable pose
bindings reject the proposal. The client verifies instance/source-geometry bindings,
isolates proposal assets from the immutable base and frames affected instance bounds.
Restore and Return retain the existing authoring workflow. Ten focused file/model/
pose checks passed, including two distinct synthetic pose geometries, repeated
placements and unavailable instances. Retail browser town01 model0074 previewed
all11 supported placements using one geometry; placements, unrelated entities,
base scene/project state and exact Return/Restore passed with zero page errors.
The JSON file all-instance selector and strict boolean scope rejection also passed
on model0009. Private evidence: local-output/sdk-20260909/model-scale-project-20260930/
shared-shape-browser-check.json, shared-shape-preview.png and
shared-file-scene-browser-check.json. Initial camera framing included unrelated
scene bounds; adjusted to affected instances and rechecked. Screenshot inspected
for proposal controls; scene occlusion and retail visibility remain approximate.
Temporary browser/server stopped. No game or package
installation.383-test checkpoint predates this addition; gameplay acceptance
remains deferred and the full SDK remains incomplete.


Proposed texture files in the scene (2026-09-30): validated TIM/JSON proposals can
now be inspected before Apply across their decoded scene materials. A private
in-memory catalog substitutes the proposed TIM alongside current authored texture
bindings, then uses the existing static VRAM image/CLUT decoder for model and ground
materials. Separate field-party banks retain their established scope. Geometry,
topology, poses and placement remain source-owned; the renderer only substitutes
texture payloads. Changed material/instance counts and unavailable geometries are
explicit; the16MiB scene texture budget still applies. Candidate hash and scene key
are revalidated. Closing the proposal withdraws delayed replies. Restore/Return
recover the exact scene while retaining the selected file for explicit Apply or
Discard.23 focused retail-enabled texture tests passed with no skips, including
prepared-ground catalog substitution without source mutation. Retail texture29
JSON browser probe changed31 materials across19 geometries/58 instances; vertices,
topology, poses, matrices, base/project state, exact Restore/Return, retained file,
discard and stale hash/source/base64 rejection passed with zero page errors.
A held response after closing the proposal did not change the scene. TIM readback
matched the candidate hash and same31 materials/58 instances. All11 authored-file
hashes remained unchanged. Screenshot inspected for proposal controls; visual
occlusion remains approximate. Evidence under local-output/sdk-20260909/model-scale-project-20260930/
texture-scene-browser-check.json, texture-scene-tim-check.json,
texture-scene-authored-check.json and texture-scene-proposal.png. Temporary browser/
server stopped; no game/package installation. Runtime VRAM residency and gameplay
appearance remain unverified;383-test checkpoint predates this addition.


Historical regression checkpoint (2026-09-30): all390 Python discovery tests passed
in163.243s against05e93405, exit0, retail disc supplied, no skips. Owned process
continued to terminal completion without restart; no application repairs required.
Texture usage/operand layer Node checks and editor syntax passed. Evidence:
local-output/sdk-20260909/sdk-regression-20260930-scene-proposals.log and matching
.json metadata/hash. This supersedes the383-test checkpoint and historical
predates notes for current Python services. Browser workflows remain separate;
no game launched, runtime parity/gameplay acceptance still deferred.
