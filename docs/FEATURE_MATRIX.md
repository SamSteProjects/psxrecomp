# Legaia SDK feature matrix

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
Clearing the override builds zero overlays; a new cold revert run remains pending.

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
| Asset database | PARTIAL / READ-ONLY | Searchable models, actors and scenes, plus source-verified discovery of 96 textures, 14 referenced animations, 52 actor scripts, 39 partition-two scripts, 426 dialogue segments, one collision grid, 99 triggers and 14 regions in town01. Derived resource registration is separate from immutable imports and authored state. Project-wide Authored assets links actor edits, TIM replacements and position templates to their editors, including cross-scene navigation without a derived catalog refresh. Content-addressed TIM replacement registration is supported; broader replacement families remain pending. |
| Model preview | PARTIAL | All 29 town01 actor-referenced models decode. Browser-verified object-local geometry and matched textures; F0/F1/F2 idle/walk and supported scene-header NPC poses have stepping and playback. Runtime equipment, battle animation and ETMD breadth remain pending. |
| Model export | FUNCTIONAL / STATIC | Editor Export GLB writes a full supported model or current baked pose to private project Exports. Embedded textures, provenance and axis conversion; Vahn and tree pass Khronos validation and Blender import/render. No animation channels, replacement importer or physical scale claim. |
| Textures | PARTIAL / AUTHORING | Bounded 4/8/16/24-bit TIM decoding; town01 has 96 searchable TIM assets with direct image inspection and local palette selection. Material association resolves 38 unique crops, 26 untextured and 8 unresolved among 72 materials. The separate shared-party bank resolves all eight used F0/F1/F2 materials. Matching-layout TIM replacements support image/palette edits, imported/effective previews, history, persistence and guarded builds. One cold authored/baseline pair proves visible palette replacement and removal for town01 TIM 5/raw/0. Broader residency, blend and animated palettes remain unverified. |
| Animations | PARTIAL / READ-ONLY | Six field-party clips plus scene-header NPC clips with stepping, playback and posed export. The resource browser lists 14 unique town01 animations through 39 verified actor bindings; 13 unavailable associations stay explicit. Independent party comparison covers 20,845 vertices. Runtime timing, equipment and battle animation remain pending. |
| Scene model | FUNCTIONAL | Imported actor entities and evidenced Transform/ModelRenderer/Animation/RetailMetadata components. Authored Dialogue runs bind to verified record-relative source spans. Source-base collision, trigger and region resources are available separately; live collision and general script bindings remain unresolved. |
| Model/animation assignment | FUNCTIONAL / WRITABLE | Verified same-scene donor pairs connect to project commands, undo/redo, save/open, scene preview, posed export and bounded mod builds. Combined appearance/position edits serialize one composed buffer; clearing edits restores baseline package bytes. One cold town01 actor0049/donor0015 pair visibly changed appearance while retaining dialogue and field control. Broader script compatibility and a cold appearance-revert run remain unverified. |
| Project authoring | FUNCTIONAL | XYZ, supported donor-appearance and bounded dialogue overrides, selection, undo/redo, dirty state, content-addressed imported evidence and digest-checked save/reopen. Transform templates capture/apply supported axes. Native actor creation, heading and arbitrary model/animation replacement remain pending. |
| Editor | PARTIAL | Verified selection/edit/clear/undo/redo/save/reopen, textured object preview, private Build & Run, attach and graceful Stop. Central WebGL scene preview renders 51/52 town01 entities with mesh picking, focus, transform updates and marker fallback. Opt-in Live follow chains guarded captures, stops on failure, and displays separate selected-actor candidate markers; browser restart/Stop/Edit/runtime-stop checks pass. Scripted placement/visibility, retail height/facing and broader editing tools remain pending. |
| Live bridge | PARTIAL / LIVE-VALIDATED | Cold town01 v2 capture accepted 90 nodes under executable/witness/scene/epoch guards. Early exact-PC preparation now runs during compatible discovery and owned launch readiness; a fresh cold New Game with automatic preparation passed the unchanged v2 guard with 90 nodes and all three witnesses current. One same-scene restore recovered all three witnesses and 90 nodes after normal dialogue input, without sustained slowdown in the measured window. Late attachment cannot recover unrecorded entry execution. Archived v1 remains strict; repeated/cross-scene restore and town0c/transition acceptance remain pending. |
| Correlation | PARTIAL / READ-ONLY | Guarded MAN-header/model evidence yields explicit candidates and ambiguity. Actor0052 authored header and world position match `(4480,11904)`, with a visible savepoint beside Vahn. Generic bindings remain candidates; they are not promoted to confirmed identity. |
| Scripts/dialogue/flags | PARTIAL / BOUNDED TEXT WRITING | Actor inspector decodes supported bounded MAN instruction paths and inline dialogue, with explicit substitution tokens, flag operands, successors, opaque bytes and stop reasons. The asset browser links script/dialogue resources to their actor inspector and records 1,145 source-qualified flag references across P1/P2. Bounded flag-word branches expose five additional read-only P2[4] dialogue segments; its unresolved graph still rejects authoring. Town01 actor0049 shows 23 instructions/seven dialogue segments; actor0001 stops at unsupported0x29. Supported plain-text runs have Apply/Clear, undo/redo, save/open and guarded build serialization; P2[36]/[37] each expose one supported ten-byte run; broader partial graphs remain read-only. No script execution, story-state evaluation, control editing or text relocation. One actor-49 authored message is cold-gameplay accepted; P2 display remains unaccepted. |
| Collision and field regions | PARTIAL / READ-ONLY | Field MAP source grid supplies 4,228 blocked subcells in town01, displayed as bounded ground-plane outlines. Source/project changes clear overlays. Fourteen region records expose encoded tile bounds; no floor height, runtime actor blockers or script paints are inferred. |
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
