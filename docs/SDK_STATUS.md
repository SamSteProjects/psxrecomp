# Legaia SDK status — 2026-09-30

The SDK is functional for supported offline authoring workflows, but the full editor and runtime parity objective is incomplete. Gameplay verification is deferred at the user's request. No new game launch is needed to review the work below.

## Ready for offline review

- Scene workspace: source-based textured scenes, hierarchy selection, inspector, orthographic/top views, coordinate locator, authored/retail layers, and actor/decorative/shared-scenery X/Z handles. Shared scenery browser checks moved three instances while preserving366 unrelated instances and verified Undo on both axes.
- Script movement: verified MOVE_TO/NPC_RUN X/Z authoring, source/effective values, history and persistence, viewport targets with source-instruction navigation, and descriptor/streaming experimental output composition. Y, executed branches and actor identity remain unknown where evidence does not establish them.
- Animation: supported rigid clips can be previewed and exported. Channel edits and same-object retail/effective copy across frames/ranges use Apply/Undo/Discard. Existing-layout raw-record and readable channel-JSON download/import support retail/effective values. Raw-record checks pass shared-conflict, clear, persistence and package readback checks. Browser checks cover late responses, invalid selections and cross-object rejection. Shared clip users are explicitly listed. Proposed files can be inspected without applying them in both the model and scene viewers, restored, and returned to the same file form for explicit import.
- Model shapes: a diagnostic wireframe overlay displays all decoded triangle edges in the model viewer, including hidden edges. Focused WebGL and retail browser checks cover toggle, buffer reuse, vertex updates, picking and no project writes. Direct vector Inspector editing, per-vector retail reset, inspected-vertex camera location and exact-vector audit navigation are connected with focused browser checks. Existing-layout TMD, ordered-vertex OBJ and source-bound vertex/normal JSON replacements preserve source primitive/material data. Model build reports show scalar audits and navigate only to hash-matching authored previews. Normal-only edits are not visualized as lighting: the WebGL shader uses colors/textures without normal-based lighting. Equivalent oriented face order and relative indices passed exact roundtrip and isolated vertex edits on119 town01 models. A saved OBJ project passed Undo/Redo, reopen and package build.
- Textures: indexed scene palette-word and pixel-index editing, retail/effective JSON downloads and source-bound complete palette/pixel JSON imports are connected to texture Undo/Redo, Save/Open and Build. All96 town01 indexed textures round-tripped exactly. Source layout and other packed pixels are preserved; gameplay appearance remains unverified.
- Output: supported edits compose into private packages or experimental disc exports. Input snapshots, hashes and reopened archive checks support later review. Package descriptions list emitted edit families; output collisions are rejected instead of silently replacing existing builds.

## Validation scope

The retail-enabled SDK discovery run passed **365 tests in138.866 seconds**,
exit code0, with no skips. Log:
`local-output/sdk-20260909/sdk-regression-20260930-project-flags.log`. It includes
the recent movement-selector and texture authoring/interchange/preview/audit
features and project-wide flag service. The movement HTTP test now selects its
intended decoded MOVE_TO target rather than assuming the first record still
contains coordinates; earlier EXEC_MOVE records remain selector-only. Browser
interaction, rendering and runtime acceptance remain separate checks.

Recent private evidence lives under `local-output/sdk-20260909/`, including `sdk-suite-recheck-20260912.log`, `shared-scenery-multiple-check.json`, `shared-scenery-multiple-z-check.json`, `obj-equivalent-retail-20260912/report.json`, `animation-channel-copy-check.json`, `animation-effective-copy-check.json`, and `animation-copy-request-order-check.json`. These files are local evidence, not redistributable fixtures.

## Deferred gameplay

Use [the verification queue](legaia-gameplay-verification-queue.md) for saved input projects, exact artifacts and manual checks. NPC append/spawn behavior, script execution, animation playback, modified collision and visual behavior require their stated checks. Successful serialization does not establish gameplay acceptance. The user's wall-gap confirmation is bounded to that prior edit.

## Major unfinished work

- Arbitrary model topology/material replacement, general animation import and retargeting.
- Complete script/control-flow authoring, unknown records and scheduling behavior.
- Confirmed runtime actor identity and complete Unity-style live scene parity.
- Complete world-map behavior and unresolved MAPDSIP coverage.
- Remaining release/runtime acceptance, including the latest audio-lock build and deferred lifecycle/performance checks.
- Independent rendered acceptance of complete exported animations and wider scene parity.

See [feature coverage](FEATURE_MATRIX.md), [release parity](legaia-release-parity.md), [architecture](ARCHITECTURE.md), and [test plan](TEST_PLAN.md). The goal remains active; this report does not claim all offline work is exhausted.


Recent model interchange addition: source-bound complete vertex/normal JSON is
connected to model downloads, Apply shape, Undo/Redo and Save/Open. All119 town01
models round-tripped exactly. A retail normal-only model0009 probe preserved all
other TMD bytes and passed independent package-member readback. Browser checks
cover model0000 vertex upload, authored JSON download and Undo; they do not prove
runtime normal lighting. Saved probes are listed in the gameplay queue.

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


Flag operand authoring foundation (2026-09-30): source-qualified ScriptFlags
commands preserve separate retail/authored/effective values, support Undo/Redo,
clear offline and Save/Open, and validate reached L/G/C flag SET/CLEAR/TEST
operands against immutable source records. Upper operand bits and dispatch/layout
remain unchanged; local width and context side-effect cases are unavailable.
Fourteen focused tests passed. Retail town01 actor0002 CFLAG_SET bit2-to3 changed
only decoded MAN byte4772; project history and reopening passed. Private project:
local-output/sdk-20260909/flag-authoring-project-20260930. Editor Apply and Build
composition remain pending. Build explicitly rejects ScriptFlags instead of
silently dropping them. This is foundation work, not a completed authoring
workflow or gameplay acceptance; the365-test checkpoint predates it.


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
