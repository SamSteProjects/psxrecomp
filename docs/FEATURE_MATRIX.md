# Legaia SDK feature matrix

Current scene-editor status (2026-09-12):

| Capability | Status and verified scope | Remaining work |
| --- | --- | --- |
| Authored NPC drafts | Stable UUIDs and donor references; create/edit/delete commands, undo/redo, Save/Open, dirty/build identity tracking. Browser-verified creation, management, hierarchy, donor-model rendering, framing, picking, main Inspector, X/Z gizmos with Undo/cancellation and serialized-candidate inspection. Same-scene batch drafts and existing actor X/Z edits compose into a verified logical archive prototype. | Descriptor and supported streaming MAN drafts now compose with supported actor/dialogue/transition/animation/model/texture and MAP overrides in experimental disc exports, with saved input snapshots and reopened archive verification. Complete script/scheduling and gameplay acceptance remain pending; see legaia-gameplay-verification-queue.md. |
| Scene discovery in import dialog | Verified local-disc catalog with name prefix, 16-block paging, placement counts and source carrier kind. Unsupported structural blocks keep their reasons. Browser Dolk selection and two disjoint catalog pages verified. Empty-project Dolk2 import, Save and independent disk reopen retained72 actors and the source path. Later shared-model fixes brought the browser preview to441/441 entities. | Placement discovery does not prove full model import, rendering or gameplay compatibility. |
| Authored asset discovery | Project-wide NPC drafts, actor edits, model and texture replacements, scene edits, scripts and templates are cataloged independently of resource refresh. Draft navigation opens its dedicated Inspector; catalog undo/save/reopen checks and saved-review browser navigation passed. | Broader cross-scene browser acceptance and unsupported asset families. |
| Native actor candidates | Source-bound donor append, reached spawn-index rewrites, physical container growth and browser-verified Inspector diagnostics. Logical PROT and experimental disc growth preserve downstream data; a donor11 image reopened with exact candidate MAN, 44 unchanged file hashes and 59215 internally verified regenerated sectors. Candidate Inspector placement and donor navigation passed browser checks. Retail candidate inspection creates no project entity or game actor. | Complete script/reference coverage, spawn scheduling, project commands/persistence, Build and gameplay acceptance. See [candidate implementation](legaia-native-actor-candidates.md). |
| Assembled field scene | Implemented and browser-validated for town01: 52 actors (51 renderable), 46 placed scenery objects, 162 decorations and one textured ground entity. | Complete retail scene parity, including ground holes and exact runtime terrain behavior. |
| Scene transparency preview | Decoded blend modes and STP gates rendered in separate opaque/blended WebGL passes. Four mode equations, opaque texels, transparent holes and picking passed GPU pixel checks; Dolk2 remains441/441. | Approximate instance ordering, no retail ordering-table reproduction; standalone model viewer now shares the same GPU path; runtime ordering remains unverified. Runtime acceptance deferred. |
| Boot texture coverage | Ordered boot UI bank underlays shared and scene texture catalogs. Town01 assembled preview improved279 ->287 matched materials, resolving all8 previously missing entries.23 focused texture/build checks passed. | Runtime residency, palette effects, transparency and full visual parity remain unverified. |
| Shared savepoint / auxiliary previews | F3/F4 reference clips decode with exact3/2 object bindings and30/15 frames. Shared field texture routing and browser savepoint scrubbing verified. Dolk2 now renders441/441 preview entities, including72 actors. | Unmatched materials, auxiliary role, scripted visibility, runtime scale and timing remain unverified. |
| Scene animation inspection | FUNCTIONAL / OFFLINE. Actor-assigned and shared reference clips can be isolated on one scene instance, scrubbed, played at a chosen rate, and restored. Browser playback/pause/wrap/restore checks passed with unchanged project state; shared savepoint loop uses the correct model route. | Runtime cadence, GTE rounding, actor height/facing and game-equivalent pose/visibility remain unverified. |
| Assembled scene GLB export | FUNCTIONAL / OFFLINE. Editor exports complete authored/retail source previews with shared geometry, instance transforms, private files and stale-source rejection. Actual map01 browser export313instances/38geometries passed GLB validation with zero errors/warnings. Independent glTF-Transform import matched all313world bounds within0.00001sourceunits. Dolk2 retail/authored exports retain441instances with exactly the saved actor0001 X change and440unchanged bounds. Selected actor, decoration and ground browser exports pass independent bounds checks. Authored draft export retains UUID/kind/world placement and is rejected in retail mode. Selected scenery/ground/draft GLBs validate with zero errors/warnings. | External rendered consumer acceptance and runtime visual parity. |
| Complete animation GLB export | FUNCTIONAL / OFFLINE. Frame snapshots and complete rigid-object clips have distinct editor actions. Explicit1..120fps export, STEP tracks, terminal hold, private files, source metadata and HTTP validation. Actual30-frame browser export passed Khronos validation (0errors/0warnings) and glTF-Transform4.5.0 import (10nodes/20channels). | Rendered animated playback in Blender/Unity; retail lighting/blend equivalence, skins and equipment behavior. |
| Partial-object animation poses | FUNCTIONAL / BOUNDED. Source-supported clips track leading model objects and omit untracked trailing objects without altering cached full geometry. Station0010(7/8objects) and Balden2/0015(1/10objects) pose/full-frame/export checks passed. | Balden2/0008 has6channels/4objects and remains unavailable; its correct runtime binding is unresolved. Fresh partial script inspection contains no decoded model selector, which does not exclude rebinding elsewhere. |
| Clipless multipart props | FUNCTIONAL / BOUNDED. Zero-initial-animation actors can draw raw objects with one actor transform, following the pinned reference play renderer. Station0007 now previews; unresolved nonzero-animation bindings still reject fallback. | Actual runtime draw/visibility acceptance and broader scene coverage. |
| Kingdom overworld scene preview | FUNCTIONAL / OFFLINE COVERAGE. Isolated saved imports: map01 has8actors/305environment instances/16,251terrain cells; map02 has7/276/16,381; map03 has19/244/16,374. All instances decoded as renderable within current budgets. All three browser previews verified: map01 313/313, map02 283/283, map03 263/263. map02/map03 perspective and orthographic captures visually inspected with zero page errors. | Dynamic water/visibility/encounters, world-map camera and retail gameplay parity. Source geometry support does not imply complete world-map behavior. |
| World-map landmark menu | FUNCTIONAL / READ-ONLY. Verified SCUS executable tables expose16 names and20 source placement records, discovery flag indices, destination IDs and menu pixels through the editor and searchable Asset Database. Exact CDNAME destination labels and catalog-to-landmark navigation are browser verified. Synthetic bounds/unknown-name tests and actual browser workflow passed. | Complete 3D world-map behavior, current discovery-state evaluation, menu authoring and gameplay acceptance. |
| Script model selectors | READ-ONLY / SOURCE-DECODED. SET_ACTOR_MODEL exposes signed/u16 selector and signed high-pool threshold, with extended context retained. Boundary tests pass. Searchable script-asset references link to source instructions; Dolk2 browser discovery verified10references across10scripts. | Runtime pool-base resolution, actual asset binding and execution remain unknown. |
| Script movement authoring | FOUNDATION / OFFLINE. Verified source-record X/Z serializer for MOVE_TO and NPC_RUN with stable owner/PC IDs, exact byte audits, immutable baselines and source-grid validation. Fresh Dolk2/town01 edits each changed one MAN byte and fit original payload spans. Project ScriptMovement commands, authored/effective layers, Undo/Redo, Save/Open and authored asset summaries now pass synthetic and fresh Dolk2 checks.  Server-verified actor/partition-2/trigger reports and strict edit/clear HTTP command shapes are connected; retail HTTP checks passed.  Inspector controls now pass browser Apply/Clear/Discard, grid validation, Undo/Redo and Save/reload; independent disk reopen retains X9408. | Retail/authored effective target overlays now pass browser coordinate comparison, unchanged-target checks and partial-report rejection without authored commands. Gameplay acceptance remains pending. Descriptor MAN Build now composes movement and other supported edits with byte-audit conflict checks; a town01 package independently decoded to exactly two requested changes. Append-aware source-owner rebasing now passes Dolk2/town01 exact-byte checks and retains donor copies. Streaming/appended MAN experimental disc integration now composes movement edits. A combined Dolk2/town01 export with an appended Dolk2 NPC passed rebuilt-PROT readback. Gameplay remains unverified. |
| Script movement targets | FUNCTIONAL / READ-ONLY. Viewport marker picking and a target selector reopen exact actor/partition-2 source instructions; overlapping hits require explicit choice. Actor and partition-2 script views now frame simultaneous target markers with explicit reference Y, source PCs/X/Z and unresolved contexts. Retail browser checks cover3actor and4partition-2 targets, Clear, height validation and source invalidation without authored commands. NPC_RUN and MOVE_TO expose decoded X/Z, raw operands and unknown Y; MOVE_TO is labeled a teleport target, and NPC_RUN retains parked status. Locate target fills the viewport locator and requires an explicit reference height; branch execution is not assumed. Script asset metadata includes searchable target coordinates and exact source-instruction links; retail Dolk2 browser discovery found14targets across9scripts. | Story-state execution, movement interpolation and runtime position verification. |
| Orthographic placement inspection | FUNCTIONAL / OFFLINE. Perspective and orthographic rendering/picking, matching overlay and move-plane projection, and Top (X/Z) camera shortcut. Eight math parity cases and actual map01 browser313/313 passed. | Runtime coordinate/visual comparison remains deferred. |
| Selection and inspection | Hierarchy, viewport picking, selection outlines, object framing and Actors/Scenery/Ground visibility layers work together. Source provenance remains separate from authored transforms. | Broader scene acceptance and extensible inspector coverage. |
| Shared scenery transforms | Writable numeric offsets/rotations, undo/redo, save/reopen, effective preview and guarded MAP packaging. Browser edit/save/undo accepted. | In-game visual/behavior acceptance; spawnable scenery remains shared-only. |
| Individual decorations | Writable cell-local transforms clone a descriptor into an unreferenced zero-filled slot while preserving grid flags. Retail checks verify distinct transforms for cells1833/2089 and unchanged unrelated bytes. | In-game rendered result and broader allocation/lifecycle acceptance. |
| Decoration and placed-scenery move handles | Browser-validated X/Z dragging, free X movement, Undo, origin-aligned64-unit Z snapping, unchanged shared counterpart and Save. | Placed scenery now has explicitly enabled shared X/Z handles. Dolk2 browser X/Z drag/Undo verified three shared instances and366 unchanged unrelated instances. Gameplay acceptance remains pending. Other transform tools remain open. |
| Preview performance | Transform changes reuse decoded geometry. Measured SDK service cold18.423s, clear0.386s, restore1.122s with identical geometry payloads and correct positions. | Browser/network performance; controls briefly disappear during refresh. |
| Playable scenery package | The saved gizmo edit built successfully. The same windowed runtime consumed all36 MAP sectors (73728 bytes), and four read-only RAM comparisons matched both descriptors and grid references. Normal title/prologue/field flow and movement reached. | User screenshot and explicit confirmation verify the visible wall gap in the manual run. Collision behavior and broader lifecycle acceptance remain unverified. |

Current coordinate/live-inspector additions:

- Actor preview elevation uses source terrain triangles where available, without changing imported or authored Y. In town01,25/52 actors resolve a source-ground sample; eight have nonzero heights. Actor0011 was visually checked on raised ground. The remaining27 still lack a matching displayed ground cell; this is not complete runtime elevation parity.
- The user reports that remaining NPCs occupy houses beside the outdoor map. Preserve their coordinates; absent displayed ground/interior geometry is not evidence of misplaced actors. Interior placement still needs independent comparison.
- Live candidate inspectors compare imported/effective/sampled guest XYZ, signed deltas, captured placement-header coordinates and header agreement. The table was exercised through guarded live sampling. Header/model compatibility does not establish identity, and runtime deltas are not a coordinate calibration.
- Frame live samples is browser-validated and restricted to accepted-epoch candidates in Live mode. Locate coordinates frames a separate camera-only reference marker; the captured1886/0/1740 point visually agrees with nearby ramp/path/rock landmarks.
- Same-scene refresh retains the previous preview with stale-value labels and disabled scenery editing. Browser acceptance covers retained inspector controls; a deferred-response check covers Undo cancelling a pending update.

The active scenery validation package moves decoration cell1833 by authored
MAP offset Z=-256, producing preview world Z2112 instead of1856. Cell2089 stays
at world Z2112. Package SHA-256:
`823dd770b419003b7d09a655bb9246d2f3f966bd719744be7b16d6acc1195dde`.
This is a partial scene-authoring workflow, not completion of the full SDK.
Detailed chronological evidence remains in `docs/internal/FAITHFUL_TIMING_PLAN.md`.

2026-09-10 animation authoring: sparse exact translation/rotation edits now
persist through commands, undo/redo and save/reopen. Browser controls show shared
clip users; imported and composed authored clips preview separately. The main
scene uses authored frame zero and invalidates geometry on override changes.
The package builder emits a guarded, equal-span scene ANM overlay with independent
LZS decoding; conflicting shared-axis writes and capacity overflow are rejected.
Browser acceptance covered Actor 0011 X=100, saved reopen, undo/redo and visible
imported/authored pose comparison. A private package combined that edit with the
wall override. Retail scene geometry showed exactly +100 X on affected vertices.
This remains **PARTIAL / runtime acceptance pending**: in-game animation playback remains unverified. Main-scene browser rendering
visibly showed the displaced head on the selected and another shared-clip actor. Imported/authored baked GLB exports
were parsed independently: 675 positions with only the intended +100 X delta,
and embedded authored source hashes/change evidence preserved. External viewer
acceptance of these new authored exports remains pending.
Arbitrary animation import, extra frames/channels, playback timing and skeletal
retargeting remain unsupported. Shared clip edits can affect other actors and
script-selected uses beyond the imported initial actor references.

2026-09-10 script path navigation: actor/dialogue and trigger script instruction
views share clickable decoded successors, incoming-edge navigation, highlighted
selection and local Back history. Undecoded targets stay non-clickable and retain
conditions/stop reasons. Browser acceptance followed actor0049 flag-set branch
0x18 -> 0x39, Back, and incoming edge0x16; actor0001 retained undecoded targets
and its unsupported0x29 stop. This navigates source evidence, not execution.

2026-09-10 correlation inspector: unconfirmed candidate cards show the matching
imported/effective appearance layer, donor when applicable, capture frame and
captured world position. Retained-capture browser verification displayed the
effective actor0049 candidate and removed it after clearing the appearance
override, requesting a new capture. This was not a fresh runtime observation.

2026-09-10 appearance gameplay acceptance: a cold appearance-only run replaced
town01 actor0049's child model103/animation15 with donor0015 model94/animation18.
The axe-carrying character appeared at the Genesis Tree, retained the original
dialogue and returned to field control after it closed. The guarded capture
accepted90nodes and observed the replacement header at placement4544/12096.
Correlation now compares imported and effective donor appearance separately,
retaining the target's local-count prefix and placement evidence. Replay of the
guarded capture yields an effective-only candidate for actor0049; it remains
unconfirmed. Changing authored appearance invalidates previous correlation.
This is bounded acceptance for this donor pair, not general script compatibility.
Clearing the override builds zero overlays; the subsequent matched-binary cold revert restored the child appearance and reached field control (see acceptance below).

2026-09-10 animation preview assignments: the animation asset picker now offers
separate Imported and Authored effective previews, plus combined labels when
unchanged. Browser verification opened actor0040's authored clip0012 (15 frames,
stepped to frame2) and original clip0008 (25 frames) through their respective
verified preview services. No runtime animation or gameplay equivalence claim.

2026-09-10 animation usage: animation asset details now expose imported and
effective actor links using verified catalog bindings and authored appearance
donors. Fresh retail metadata checks cover all 39 town01 bindings and an actual
supported actor0040 -> actor0046 donor assignment (clip0008 -> clip0012).
Same-model/different-animation handling also passes. Browser acceptance verified
the effective clip0012 link selects actor0040 with donor0046, then undo and
resource refresh restore Imported + Effective usage of clip0008. Runtime clip
state is not inferred.

2026-09-10 model usage: model details list project-wide imported and effective
initial actor assignments. Browser navigation from shared model 00f1 switched
town01 -> town0c actor0002 -> town01 actor0003 in a fresh two-scene project.
Authored donor relationships also pass save/open and undo tests. These links
do not claim scripted runtime residency or complete asset dependency coverage.

2026-09-10 initial flag reference browser acceptance: a source-verified scene index grouped 1,123
town01 encoded references into 418 script/context-qualified groups. Search,
source provenance and P1/P2 script navigation are integrated in the editor.
Matching operands across scripts are not asserted to be the same runtime flag;
live values, symbolic story names and flag editing remain unresolved.

Captured generic runtime-node flag words are separately visible after a guarded
scene observation, with epoch identity and explicit snapshot semantics. Browser
acceptance using the retained 90-node gameplay capture verified words/bit lists
and replacement by the unavailable state when no capture exists. This does not
bind nodes to source flag groups or observe local/global/system banks.

2026-09-10 dialogue gameplay acceptance: one actor-49 fixed text run visibly
rendered its authored replacement in a cold town01 run, then closed normally.
See `legaia-sdk/dialogue-authoring.md`. P2 gameplay remains unaccepted.

2026-09-10 scene-transition explorer: the active scene has a source-verified,
read-only reference graph with script provenance, encoded entry parameters,
partial/unavailable coverage counts, source-script navigation and navigation to
already imported destinations. Town01 exposes one encoded map01 reference from
P2[0] at PC 0x16. The browser verified its source-script link and disabled
destination navigation when map01 was not imported. This is not a runtime route
graph; unknown paths, partition-zero scripts and actual transition success
remain outside its evidence.

2026-09-10 dialogue workflow update: supported MAN partition-two text runs now
appear in project-wide Authored assets, including after save/open and without a
derived resource catalog. Selecting a saved script switches to its source scene
and reopens the shared dialogue workspace through fresh source verification.
Browser save/open/edit-clear acceptance passed for town01 P2[37]; the real HTTP
regression verifies matching trigger/direct provenance and rejects wrong-scene,
wrong-partition and absent-record requests. This extends the script and asset
browser rows below. P2 in-game text display remains unverified.

Status recorded during the 2026-09-09 buildout. FUNCTIONAL means the named
workflow runs within its stated bounds; it does not mean the entire subsystem
is complete. Runtime fixes from the preceding milestone are committed as
`189a2d24994dab0443d053fa2e60bc2867553920`.

| Subsystem | Status | Implemented evidence / remaining acceptance |
|---|---|---|
| Release parity | PARTIAL | Stability/source audit in `legaia-release-parity.md`; Windows build, rendered title/opening story/town01 arrival and bounded process/audio samples passed. The reproduced opening-FMV stall is fixed; a no-input cold run reaches the title menu. Other FMVs, full field gameplay and audible quality remain unaccepted. |
| Overlay precompilation | FUNCTIONAL | Build-time split discovery; growth/shrink/body edits and helper isolation checked with seven-variant executable fixtures under Visual Studio/MSVC, Ninja/GCC and NMake/GCC. GNU Make remains unaccepted. Ten intended retail roles; MAPDSIP completeness not claimed. |
| Restore ownership | FUNCTIONAL / BOUNDED LIVE VALIDATION | Explicit native invalidation and lazy-cache reset; repeated restore fixtures pass. One idle retail restore retained 59.85/60.02 FPS cold/restored and recurrent static ownership. Later checks on binary `61d99eac...` completed three title loads, New Game input, story-to-title restore and restart. Repeated field/cross-scene overlay restoration and full Live-profile reacquisition remain separate gates. |
| Snapshot integrity | FUNCTIONAL / BOUNDED | Header identity rejects independently of diagnostic storage. All known sections validate and prepare before commit; corrupt input and MDEC allocation failure preserve guest state. Executable raw/zlib/reordered/repeated/partial-command regressions pass. Retail scheduler restoration is a separate gate. |
| Disc / scene import | FUNCTIONAL | Exact SCUS-94254 disc identity, ISO/PROT/CDNAME/LZS/MAN readers; town01 52 actors/119 models/52 resolved and town0c 44/115/44. Unsupported bundle layouts fail explicitly. |
| Asset database | PARTIAL / READ-ONLY | Searchable models, actors and scenes, plus source-verified discovery of 96 textures, 14 referenced animations, 52 actor scripts, 39 partition-two scripts, 522 dialogue segments, one collision grid, 99 triggers and 14 regions in town01. Derived resource registration is separate from immutable imports and authored state. Project-wide Authored assets links actor edits, TIM replacements and position templates to their editors, including cross-scene navigation without a derived catalog refresh. Content-addressed TIM replacement registration is supported; broader replacement families remain pending. |
| Model preview | PARTIAL | All 29 town01 actor-referenced models decode. Browser-verified object-local geometry and matched textures; F0/F1/F2 idle/walk and supported scene-header NPC poses have stepping and playback. Runtime equipment, battle animation and ETMD breadth remain pending. |
| Model shape replacement | PARTIAL / AUTHORING | Same-layout source TMD vertex/normal XYZ replacement, content-addressed files, strict provenance, undo/redo, save/reopen, explicit authored preview/export and grouped compressed model overlays. All 119 town01 model layouts passed a coordinate edit; two models built into one verified overlay; party idle shape passed 15 frames. Browser authored view/export and OBJ file-picker upload/discard/clear verified. Ordered OBJ Blender roundtrip preserved source bytes; an edited vertex survived import. Party and NPC animation composition passed 15 frames, and separate-stream texture/animation combinations built. Scene visual checks, exact cross-family shared-container composition and gameplay remain pending. Arbitrary topology/material replacement is not supported. |
| Model export | FUNCTIONAL / STATIC AND RIGID CLIPS | Editor exports full supported models, baked frames, and complete rigid-object clips into private project Exports. Full clips use explicitly selected timing and preserve active object/channel identity; validator and independent-import checks passed. Earlier static Vahn/tree exports were imported/rendered in Blender; animated Blender/Unity playback remains unverified. No physical scale or native replacement claim. |
| Textures | PARTIAL / AUTHORING | Bounded 4/8/16/24-bit TIM decoding; town01 has 96 searchable TIM assets with direct image inspection and local palette selection. Material association resolves 38 unique crops, 26 untextured and 8 unresolved among 72 materials. The separate shared-party bank resolves all eight used F0/F1/F2 materials. Matching-layout TIM replacements support image/palette edits, imported/effective previews, history, persistence and guarded builds. One cold authored/baseline pair proves visible palette replacement and removal for town01 TIM 5/raw/0. Broader residency, blend and animated palettes remain unverified. |
| Animations | PARTIAL / AUTHORING | Eight supported shared clips (party idle/walk, savepoint and auxiliary loop) plus verified scene-header NPC clips. Resource provenance, individual and isolated in-scene stepping/playback, rigid full-clip export, partial-object posing and bounded channel authoring are implemented. Model/clip reference association is distinct from initial or live actor state. Runtime cadence, equipment, battle animation, unmatched bindings and authored gameplay acceptance remain pending. |
| Scene model | FUNCTIONAL | Imported actor entities and evidenced Transform/ModelRenderer/Animation/RetailMetadata components. Authored Dialogue runs bind to verified record-relative source spans. Source-base collision, trigger and region resources are available separately; live collision and general script bindings remain unresolved. |
| Model/animation assignment | FUNCTIONAL / WRITABLE | Verified same-scene donor pairs connect to project commands, undo/redo, save/open, scene preview, posed export and bounded mod builds. Combined appearance/position edits serialize one composed buffer; clearing edits restores baseline package bytes. One cold town01 actor0049/donor0015 pair visibly changed appearance while retaining dialogue and field control. A matched-binary cold revert restored the child appearance and field control; broader script compatibility remains unverified. |
| Project authoring | FUNCTIONAL | XYZ, supported donor-appearance and bounded dialogue overrides, selection, undo/redo, dirty state, content-addressed imported evidence and digest-checked save/reopen. Transform templates capture/apply supported axes. Native actor creation, heading and arbitrary model/animation replacement remain pending. |
| Editor | PARTIAL | Verified selection/edit/clear/undo/redo/save/reopen, textured object preview, private Build & Run, attach and graceful Stop. Central WebGL scene preview renders 51/52 town01 entities with mesh picking, focus, transform updates and marker fallback. Opt-in Live follow chains guarded captures, stops on failure, and displays separate selected-actor candidate markers; browser restart/Stop/Edit/runtime-stop checks pass. Scripted placement/visibility, retail height/facing and broader editing tools remain pending. |
| Live bridge | PARTIAL / LIVE-VALIDATED | Cold town01 v2 capture accepted 90 nodes under executable/witness/scene/epoch guards. Early exact-PC preparation now runs during compatible discovery and owned launch readiness; a fresh cold New Game with automatic preparation passed the unchanged v2 guard with 90 nodes and all three witnesses current. One same-scene restore recovered all three witnesses and 90 nodes after normal dialogue input, without sustained slowdown in the measured window. Late attachment cannot recover unrecorded entry execution. Archived v1 remains strict; repeated/cross-scene restore and town0c/transition acceptance remain pending. |
| Correlation | PARTIAL / READ-ONLY | Guarded MAN-header/model evidence yields explicit candidates and ambiguity. Actor0052 authored header and world position match `(4480,11904)`, with a visible savepoint beside Vahn. Generic bindings remain candidates; they are not promoted to confirmed identity. |
| Scripts/dialogue/flags | PARTIAL / BOUNDED TEXT WRITING | Actor inspector decodes supported bounded MAN instruction paths and inline dialogue, with explicit substitution tokens, flag operands, successors, opaque bytes and stop reasons. The asset browser links script/dialogue resources to their actor inspector and records 1,183 source-qualified flag references across P1/P2. Bounded flag-word branches expose five additional read-only P2[4] dialogue segments; its unresolved graph still rejects authoring. Town01 actor0049 shows 23 instructions/seven dialogue segments; actor0001 stops at unsupported0x29. Supported plain-text runs have Apply/Clear, undo/redo, save/open and guarded build serialization; P2[36]/[37] each expose one supported ten-byte run; broader partial graphs remain read-only. No script execution, story-state evaluation, control editing or text relocation. One actor-49 authored message is cold-gameplay accepted; P2 display remains unaccepted. |
| Collision and field regions | PARTIAL / SOURCE WALL AUTHORING | Field MAP source grid supplies 4,228 blocked subcells in town01, displayed as bounded ground-plane outlines. Source/project changes clear overlays. Exact wall bits support commands, undo/redo, persistence and composition with scenery in one MAP overlay; retail/effective previews and browser single-cell Apply/Undo are verified. Floor tiers, script paints and actor blockers remain unmodified; in-game movement acceptance is pending. Fourteen region records expose encoded tile bounds; no floor height, runtime actor blockers or script paints are inferred. |
| Transitions/world map | FOUNDATION | Prior observation vocabulary retained. Script resources expose encoded named scene-change references when decoded; one occurs in the cataloged town01 P2 paths; reachability is not established. Field MAP discovery adds 99 town01 trigger records: 11 local teleports, 37 object bindings and 51 fallback P2 references. Eligible gate-1 triggers open bounded P2 script inspection with Back navigation; all 51 town01 references resolve, with unsupported paths explicitly partial. All 39 P2 scripts and their bounded decoded dialogue segments are directly browsable. Opening P2[3] exposes eight segments before a known halt with unresolved trailing ownership; opening text remains read-only. These do not establish named or reachable scene edges. Reachable transition graphs, MAPDSIP coverage and world-map authoring remain pending. |
| Build and Run | FUNCTIONAL / PARTIAL ACCEPTANCE | Supported X/Z, donor appearance and bounded text edits build into guarded private .psxmod packages; clearing edits builds a verified zero-overlay retail baseline. A reopenable build report lists audited changes and validation, with stale status after authored edits. Editor-owned Windows launch verifies executable/BIOS/disc/mod identity; Attach and Stop pass. Cold game consumed 24894 patched bytes over13sectors and rendered town01. A moved savepoint visibly appears at its authored location; a fresh zero-overlay retail run removes it there and restores its original world coordinates. |

The primary acceptance path is import -> hierarchy/viewport -> select -> edit ->
undo/redo -> save -> reopen with original retail evidence unchanged. The later
build acceptance must prove the authored edit in a running game, including
revert, rather than treating an exported metadata file as a playable build.

The scene preview additionally assembles 39 town01 actors from their verified
MAN header animation IDs and type-5 ANM bank. Independent comparison covers
5,028 frame-zero vertices. This extends the party-only animation foundation;
NPC clip frame stepping, manual-rate playback and selected-pose GLB export are
connected to the actor inspector. Runtime clip selection/timing and battle
animation remain pending. Ten zero-ID actors do not acquire invented poses; supported
single-object models can render statically, while the multipart savepoint stays
a marker. Two party instances use explicitly labelled reference idle poses.

2026-09-10 reference navigation acceptance: transition and flag operations open
and select their exact decoded PC in the shared script workspace. Browser checks
cover actor0049 flags and partition-two script0 SCENE_CHANGE0x16/CFLAG_SET0xC.
This is source navigation, not branch execution or runtime flag identity proof.

2026-09-10 transform tooling: X/Z gizmos support optional origin-aligned snapping
at16/64/256/1024 scene units and coordinate feedback. Each completed drag emits
one existing undoable transform command; cancellation discards the preview.
Snap settings are session controls, not authored retail properties. Heading
and native actor creation remain unsupported.

2026-09-10 snapping workflow accepted in browser: actor0049 Z12096 ->12288,
Undo/Redo, Save/Open existing and Build. Package reports one placement change,
24894 overlay bytes and passed provenance/opaque/LZS validation. Browser errors
were empty. This snapped edit has not been run in the game.

2026-09-10 actor template extension: separate `authored-appearance-v1` presets
capture authored donor pairs and apply through the existing same-scene verified
appearance command. Position presets remain `authored-position-v1`; one preset
never silently captures the other component. Browser capture/clear/apply/save/
build and independent reopen passed for town01 actor49 donor15. Presets reuse
existing actors; they do not instantiate NPCs or supply missing script state.

2026-09-10 build-report navigation: audited actor owners link directly from
package changes to their source scene and selected actor. A private retail
build containing model103->94, animation15->18 and Z12096->12288 passed fresh
import, unchanged opaque-byte and LZS validation. Browser navigation from
town0c to town01 actor0049 displayed authored Z12288 without browser errors.
Dialogue-run focusing is handler-checked but not separately browser-accepted.
This report workflow does not constitute a new gameplay run.

2026-09-10 partition-two report navigation accepted in browser: a one-run
Greetings. -> Greetings! build for town01 P2[36] passed package validation.
From town0c, the report link opened script36 and focused authored run0x11.
This supersedes the handler-only navigation limit for that P2 path, while
in-game display of the P2 edit remains unaccepted.

2026-09-10 texture report navigation accepted in browser: a source-verified
TIM payload edit built with33312 overlay bytes. Its report link switched from
town0c to town01 and opened the effective256x256,4bpp,16-palette texture with
the matching replacement hash. Browser errors were empty; no new gameplay
validation is implied.

2026-09-10 placement feedback: Transform Inspector shows build issues derived
from the actual X/Z serializer and identifies authored Y as project-only.
Synthetic browser checks cover invalid X125/Y0, Undo clearing warnings and
supported X128 without warnings. These warnings do not replace build-time
source verification or establish unsupported heading/height serialization.


2026-09-10 script position presentation: actor and trigger instruction tables
show immediate unchanged-axis semantics separately from timed movement operands.
Extended target contexts remain explicitly unresolved. Encoded operands stay
inspectable, and no live movement or runtime actor identity is inferred. Syntax
and focused DOM behavior checks pass; browser layout acceptance is pending.


2026-09-10 dialogue menu browser acceptance: a fresh town01 project opened
actor0001's source-verified four-option picker at0x6B. The shared instruction
table displays all labels/encoded targets and unresolved continuation, with no
writable runs. Visual inspection found expanded raw data obscured the choices;
menu raw operands now default collapsed and all four choices fit in the selected
row. Reload verification passed with no browser errors. No runtime menu claim.


Script catalog menu discovery now records menu count, source PC/span, option
count and source hash without retaining labels or raw bytes. Script resource
details expose links to the exact menu instruction through fresh private source
inspection, for actor and P2 owners. Older catalogs request refresh rather than
claiming zero menus. Six catalog tests (retail enabled) and JS syntax pass;
browser acceptance of these new resource links remains pending.


The menu resource link now has browser acceptance: fresh town01 catalog refresh,
Scripts category/search0001, actor0001 resource details showed one four-option
menu; its link opened source verification and selected DIALOGUE_PICKER0x6B with
all choices and the read-only guard intact. Browser errors were empty. This
accepts the actor resource path; the P2 resource link has not yet had a separate
browser run.


Flag-word branch catalog integration adds11 town01 references using the pinned
host's context/local/global bank mapping. The scene flag browser consumes these
through its existing source-reference path. Local indices above15 remain
bank-width-unresolved, and no live flag values are inferred. Seven catalog tests
pass with retail input; a browser check specific to these new references is pending.


Menu-choice paths now follow each evidenced entry-relative target without
inventing a post-menu fallthrough. Compared with the prior decoder, town01 adds
113 dialogue IDs and withdraws17 from P2[20] when a newly reached boundary
conflict invalidates that graph: net522 dialogue segments/613 script-dialogue
assets,1183 flag references,60 partial scripts. Choice successors use existing
instruction navigation; pager uncertainty continues to prevent menu authoring.
The new successor links await browser acceptance.


Menu successor browser acceptance: actor0001 choice1 followed0x6B ->0xC4
SYSFLAG_SET and Back returned to the picker. This exposed misleading 'Not decoded'
labels for already decoded dialogue targets. The shared path table now includes
dialogue nodes with encoded continuations and escaped text. Reload verification
followed choice0 to0xD6 DIALOGUE_SEGMENT and Back to0x6B, with no browser errors.
Read-only script guards remain intact; these links do not execute game choices.


Decoded script paths now support case-insensitive local search across text,
instruction names, operands and hexadecimal offsets, with Previous/Next and
Enter/Shift-Enter navigation. Search excludes opaque bytes and does not write
catalog text or project state. Browser acceptance found all seven actor0001
pickers, navigated0x6B ->0x10C ->0x6B, and verified no-results disables both
buttons without changing selection. Browser errors empty; JS syntax passes.


2026-09-10 cold appearance-revert acceptance: set/clear donor commands produced a
zero-overlay baseline, launched with exactly the earlier appearance-tested
2be69467... binary. Normal cold title/FMV/story/name/elder flow reached town01
field control. Screenshots show the original child where the prior donor run
showed the axe-worker. Guarded v2 observation accepted90nodes; actor0049 has an
imported+effective structural candidate with original placement4544/12096.
That binding remains unconfirmed. Mod status reports zero writes, overlays and
copied bytes, guard false; runtime and editor exited0. Evidence stays private in
appearance-revert-live. This accepts removal for one pair on the matched binary,
not arbitrary donor compatibility or newer-binary field acceptance.


2026-09-10 transition entry authoring: verified P1/P2 named-transition spans now
support encoded entry bytes and exact X/Z arrival coordinates/facing sectors,
with source ownership checks, project history, offline persistence, script
inspector controls, authored graph layers and audited MAN packaging. Retail
PROT897 instruction bytes and the executable facing table support the static
arrival interpretation; live arrival and destination terrain height remain
unverified. Browser Apply/Clear and competing-draft protection passed. A private
combined transition/dialogue package survived save/reopen, decoded to exactly
three intended changed bytes, and returned to the exact baseline package hash
when both overrides were cleared. This does not complete reachable world-map
routes, destination-name editing, MAPDSIP coverage or live scene acceptance.

2026-09-10 ramp inspection: the collision resource now exposes source kind-2
elevation records in primary/fallback order, with signed coarse steps, four
subcell Y adjustments and per-record provenance. The editor provides a read-only
table. These are adjustments to the corner-height mean, conditional on the
object-cell0800 flag; no complete floor surface is inferred. Six focused tests
passed including private retail records for two cold-run visibility tiles.
Inspector JavaScript syntax and browser layout checks passed. The235-row retail
table supports filtering by table, row or tile-coordinate tokens; matching and
empty results were checked in the browser, including the two investigated tiles.
