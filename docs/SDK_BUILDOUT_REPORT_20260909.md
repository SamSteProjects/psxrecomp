# Legaia SDK buildout milestone — 2026-09-09

Verified stability fixes and a connected authoring workflow are implemented
on `codex/legaia-upstream-20260909`. The full modern SDK is not complete. This
record separates functioning features, demonstrated failures and remaining
product work; the detailed [feature matrix](FEATURE_MATRIX.md) and
[16-layer acceptance plan](TEST_PLAN.md) remain authoritative for scope.

## Current buildout status — updated 2026-09-30

Reviewed against committed source through `ea80fa35`, including model object
quarter-turn authoring, plus the current wait Inspector integration described
below. The dated filename is retained for
existing links. This section supersedes the historical milestone inventory and
old test counts below; those sections record what was proven at that time.

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
365-test regression checkpoint below predates this work, texture dependency
inspection and model object rotations; their later checks are recorded
separately. Manual gameplay verification remains deferred.

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

The latest retail-enabled SDK discovery suite passed **365 tests in138.866
seconds**, exit code0, with no skips. Log:
`local-output/sdk-20260909/sdk-regression-20260930-project-flags.log`. This run
includes EXEC_MOVE, texture palette/pixel/JSON/proposal/rectangle authoring,
texture Build audits and project-wide flag discovery. It supersedes the352-test
checkpoint at `1021bff1`. Viewport and editor interaction workflows retain
separate browser checks. A green suite does not establish gameplay or external
rendered animation acceptance.

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
