# Legaia SDK feature matrix

Current scene-editor status (2026-10-01):

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

**Latest integrated offline checkpoint (2026-10-01):** Retail-enabled
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

| Capability | Status and verified scope | Remaining work |
| --- | --- | --- |
| Script operand JSON files | FUNCTIONAL / OFFLINE. Source-bound authored entries across five supported numeric operand families, reviewed all-or-nothing Apply, one Undo/Redo, Save/Open, exact MAN readback and retail browser workflow. | Same imported owner/source only; no instruction/control-flow/dialogue transfer or clearing of omitted entries. Actual execution and gameplay deferred. |
| SDK asset inspector tools | FUNCTIONAL / PARTIAL. Eight catalog record types share SDK property/action metadata and explicit type-specific registered tool handlers. Actual Details navigation, previews/resource tools and busy/closed guards passed retail browser checks without actor writes. | Specialized editing forms and other asset kinds retain existing adapters; runtime/gameplay acceptance remains deferred. |
| Actor group presets | FUNCTIONAL / OFFLINE. Position/appearance/combined preset review across2–128 active-scene imported actors, all-target source/compatibility validation, one atomic Apply/Undo/Redo and Save/Open. Focused tests, Node checks, retail browser and exact full MAN package readback passed. | Absolute saved axes may overlap targets; no instantiation or runtime/visibility/collision guarantees. Normal Build rejects projects containing drafts; gameplay deferred. |
| Asset browser field search | FUNCTIONAL / OFFLINE. Name/ID/type/scene/model/confidence/provenance filters, phrases and exclusions with bounded strict syntax; imported/authored model users match recorded references. Node and retail browser checks passed, no actor changes or authoring commands. | Active-scene resource scope and existing category limits remain; no aggregate confidence or runtime-use inference. |
| Actor group placement offsets | FUNCTIONAL / OFFLINE. Dedicated scene actor group selection, source/effective/proposed table, grid/bounds validation, atomic command and one-step Undo/Redo, persistence and existing Build serialization. 23 focused tests and retail browser/exact package checks passed. 3D Proposed/Current layers, Frame group, draft Return and Restore now pass 26 focused tests and exact retail browser transform/camera/no-write checks; source terrain preview height recalculated. Proposed group X/Z handles now pass relative 64-unit snap, browser pointer drags, cancellation, bounds rejection, Return and atomic Apply/Undo checks. Ctrl/Command-click imported actor group selection in the viewport/hierarchy, highlights, Frame/Clear and dialog seeding now pass real mesh/browser workflow checks. Depth-tested box selection and filtered hierarchy ranges now pass real 2x-DPI exact mesh/hidden/add/reverse/Escape/source and review-seeding checks; bounded strip readback and atomic selection merges pass Node checks. These UI checks postdate the 421-test Python checkpoint. | Mixed actor/scenery groups, Y/facing, NPC drafts and scenery groups remain separate work. Gameplay visibility/collision/script movement deferred. |
| Actor preset file transfer | FUNCTIONAL / OFFLINE. Metadata-only JSON export/import for position, appearance and combined scopes; exact imported-source hash and fresh disc/donor checks, reviewed unique name, independent library identity, one Undo/Redo and Save/Open. Retail browser and independent project transfer/re-export passed without actor/import edits. | Same retail source scene/import required; absolute positions, existing Apply compatibility and project-only height limits remain. No spawning or runtime/gameplay guarantees. |
| Combined actor presets | FUNCTIONAL / OFFLINE. Capture authored position axes plus a verified initial donor pair; read-only layered review, source/target/template key, atomic one-command Apply/Undo/Redo, Save/Open and normal supported serializers. Detached position+appearance scene comparison, Proposed/Current/Return/Restore and export/stale guards are connected. Fourteen focused tests and Node/browser scene checks passed, alongside prior disk, exact detached no-draft package MAN and full experimental archive readback. Postdates441 checkpoint. | Absolute axes only; source donor scene/compatibility gates remain. No instantiation, rig/retargeting or runtime script/collision/visibility guarantees. Normal Build rejects projects containing drafts; experimental archive retains them with existing gates. Gameplay deferred. |
| Effective model-user selection | FUNCTIONAL / OFFLINE. Model Used by details select2–128 effective imported actor users within one scene and seed normal group tools. Fresh SDK usage/owner/effective-asset guards; retail-only assignments and drafts excluded. Node checks and retail exact group/cross-scene/stale rejection passed; zero errors, screenshot inspected. Asset sidebar tool/list scrolling fixed after footer obstruction. | Initial assignments only; script-driven/runtime users and mixed draft/imported groups are not inferred. No component/history authorship by selection. |
| SDK component inspector contract | FUNCTIONAL / PARTIAL. Versioned SDK metadata drives Transform layers/number controls and ModelRenderer/Animation read-only properties, layered ActorAppearance references, RuntimeCorrelation status and RetailMetadata evidence details. Unregistered components use escaped read-only details. Bounded command adapter, authoring versus Build constraints, unknown retail Y and busy/Edit/source/selection guards. Nine focused Python tests, Node layer/detail checks and retail edit/Undo/Y diagnostics plus donor Clear/Undo/runtime/provenance checks passed. Screenshot inspected. Postdates441 checkpoint. | Six donor/model/script/candidate actions use SDK descriptors and registered handlers, with capability/condition and Edit/busy/stale guards verified by Node and retail Clear/Undo/source-script loading. Specialized forms and asset inspectors retain existing adapters; ten actor tools now use registered SDK actions; migration is incomplete. No runtime writable properties or arbitrary component editing inferred. |
| Project transition references | FUNCTIONAL / READ-ONLY. Source-qualified references across1–64 imported scenes; merged stable scene identities, source coverage/unavailable reasons, layered entry operands and cross-scene source-script/destination navigation. Five focused tests and retail HTTP/browser checks passed; three town01/Dolk2 references,180 scripts,88 partial, zero page errors. Screenshot inspected. Postdates441 checkpoint. | Unknown paths and controller records, complete exits, story-state evaluation, reachability and runtime connections remain unverified. No route inference or path finding. |
| NPC draft repetition | FUNCTIONAL / OFFLINE. Count and X/Z grid spacing, named donor-bound copies, detached scene comparison and Return, one Apply/Undo/Redo, persistence. Eleven focused Python tests, Node guards, retail browser checks, inspected screenshot and independent disk/archive reopen passed. Postdates the 441-test checkpoint. | Normal Build rejects projects containing NPC drafts. Experimental archive serialization proves exact appended placements/initial pairs/cloned script bytes; runtime spawning, scheduling, collision and visibility remain unverified. |
| Saved actor selections | FUNCTIONAL / OFFLINE. Named project-local groups of2–128 imported actors, bounded128 selections; source-scene/hash binding, canonical membership, UUID identity, strict Create/Rename/Replace/Delete commands, Undo/Redo and Save/Open. Cross-scene Recall seeds normal group tools without game-component/history changes. Fifteen focused Python tests, Node recall checks, retail browser workflow and independent disk/input-key checks passed. Python services included in441 checkpoint; browser/disk evidence separate. | Game parenting, mixed/scenery selections and prefab instantiation are separate work; saved selections do not encode those structures. |
| Actor group alignment/distribution | FUNCTIONAL / OFFLINE. Selected anchor alignment and endpoint-preserving nearest64-grid distribution for X/Z; stable source-ID tie ordering, insufficient-span rejection, layered review, no-write scene comparison and retained Return, one-command Apply/Undo, persistence and existing Build. Ten focused Python tests, Node group checks, town01 browser workflows and exact full MAN package readback passed. Python services included in441 checkpoint; browser/package evidence separate. | Rotation, mixed/scenery groups and Y/facing are not implemented here. Collision, visibility and script-driven gameplay remain deferred. |
| Actor group donor appearance | FUNCTIONAL / OFFLINE. Common source-verified initial donor pairs across 2–128 imported scene actors; detached layered and in-scene Proposed/Current preview with retained Return and Restore, atomic Apply and one-step Undo/Redo, persistence and existing Build serialization. Seventeen focused retail tests plus Node scene guards, town01 browser comparison and earlier exact package readback passed. Python services included in441 checkpoint; browser/package evidence separate. | Full rig/retargeting, runtime script/model-pool compatibility and gameplay acceptance remain unverified. No arbitrary model/animation pairing. |
| Authored component review | FUNCTIONAL / OFFLINE. Selected imported actor groups now support layered component review and source-bound atomic Revert with one group Undo; 15 focused tests and retail browser stale/inherited/closed-response checks passed. The441-test checkpoint includes its Python services; browser evidence remains separate. Source-bound per-component Revert in Authored Assets actor/P2/scene details, detached values, normal history/persistence and stale/replay guards. 25 focused tests plus retail town01 browser and independent disk reopen passed. | Model/texture replacements, NPC drafts and templates use their dedicated workflows. This does not establish gameplay acceptance of existing edits. |
| Project text search | FUNCTIONAL / OFFLINE. Imported-scene aggregate with detached views, full Dialogue/source guards, scene/text layer search and exact cross-scene edit navigation. Retail town01/Dolk2645-run workflow and late/stale guards passed without authored changes. | Unsupported/unvisited text, story reachability and gameplay remain unverified; explicit navigation changes active scene. |
| Scene text search | FUNCTIONAL / OFFLINE. Supported dialogue/menu runs across actor and P2 owners, separate text layers, filtering,25-run pages and exact editor navigation. Retail267-run workflow and source/text/late-response guards verified without writes. | Unsupported/unvisited text, controller records, full sentences/boxes, story reachability and gameplay acceptance remain unresolved. |
| Text glyph preview | FUNCTIONAL / OFFLINE. Source-bound retail font stencil and advances, separate retail/effective/unapplied draft canvases; retail pixel readback, invalid drafts, Discard and late-response guards verified without writes. | Full dialogue layout, controls/substitutions, runtime tint, pager behavior and gameplay acceptance remain unverified. |
| Field menu label authoring | FUNCTIONAL / OFFLINE. Existing Dialogue commands edit source-qualified, contiguous plain-glyph runs in reached two/three/four-choice pickers, with option/target/capacity Inspector metadata, history, persistence and audited Build. 54 focused retail-enabled tests, retail browser Apply/Clear/Discard/Undo/Redo/Save/reopen and independent package readback passed. Jump tables, controls and byte offsets are unchanged. | Pager execution, menu reachability, glyph layout and gameplay selection remain unverified. Ordinary dialogue stop checks remain in place; world-map menu authoring is separate and unavailable. |
| Authored NPC drafts | Stable UUIDs and donor references; create/edit/delete commands, undo/redo, Save/Open, dirty/build identity tracking. Browser-verified creation, management, hierarchy, donor-model rendering, framing, picking, main Inspector, X/Z gizmos with Undo/cancellation and serialized-candidate inspection. Same-scene batch drafts and existing actor X/Z edits compose into a verified logical archive prototype. | Descriptor and supported streaming MAN drafts now compose with supported actor/dialogue/transition/animation/model/texture and MAP overrides in experimental disc exports, with saved input snapshots and reopened archive verification. Complete script/scheduling and gameplay acceptance remain pending; see legaia-gameplay-verification-queue.md. |
| Scene discovery in import dialog | Verified local-disc catalog with name prefix, 16-block paging, placement counts and source carrier kind. Unsupported structural blocks keep their reasons. Browser Dolk selection and two disjoint catalog pages verified. Empty-project Dolk2 import, Save and independent disk reopen retained72 actors and the source path. Later shared-model fixes brought the browser preview to441/441 entities. | Placement discovery does not prove full model import, rendering or gameplay compatibility. |
| Authored asset discovery | Project-wide NPC drafts, actor edits, model and texture replacements, scene edits, scripts and templates are cataloged independently of resource refresh. Draft navigation opens its dedicated Inspector; catalog undo/save/reopen checks and saved-review browser navigation passed. | Broader cross-scene browser acceptance and unsupported asset families. |
| Native actor candidates | Source-bound donor append, reached spawn-index rewrites, physical container growth and browser-verified Inspector diagnostics. Logical PROT and experimental disc growth preserve downstream data; a donor11 image reopened with exact candidate MAN, 44 unchanged file hashes and 59215 internally verified regenerated sectors. Candidate Inspector placement and donor navigation passed browser checks. Retail candidate inspection creates no project entity or game actor. | Complete script/reference coverage, spawn scheduling, project commands/persistence, Build and gameplay acceptance. See [candidate implementation](legaia-native-actor-candidates.md). |
| Assembled field scene | Implemented and browser-validated for town01: 52 actors (51 renderable), 46 placed scenery objects, 162 decorations and one textured ground entity. | Complete retail scene parity, including ground holes and exact runtime terrain behavior. |
| Scene transparency preview | Decoded blend modes and STP gates rendered in separate opaque/blended WebGL passes. Four mode equations, opaque texels, transparent holes and picking passed GPU pixel checks; Dolk2 remains441/441. | Approximate instance ordering, no retail ordering-table reproduction; standalone model viewer now shares the same GPU path; runtime ordering remains unverified. Runtime acceptance deferred. |
| Boot texture coverage | Ordered boot UI bank underlays shared and scene texture catalogs. Town01 assembled preview improved279 ->287 matched materials, resolving all8 previously missing entries.23 focused texture/build checks passed. | Runtime residency, palette effects, transparency and full visual parity remain unverified. |
| Shared savepoint / auxiliary previews | F3/F4 reference clips decode with exact3/2 object bindings and30/15 frames. Shared field texture routing and browser savepoint scrubbing verified. Dolk2 now renders441/441 preview entities, including72 actors. | Unmatched materials, auxiliary role, scripted visibility, runtime scale and timing remain unverified. |
| Animation record replacement | FUNCTIONAL / EXISTING LAYOUT. Verified retail/effective download and ANM/BIN or source-bound complete-channel JSON import convert channel differences into actor contributions with Undo/Redo, Save/Open and shared conflict checks. Retail browser source equality, file upload and Undo passed. Shared imports reject conflicts atomically, preserve other contributors on clear, and pass Save/Open plus independent ZIP overlay readback. Headers/counts/opaque bytes remain fixed. Optional file preview shows bounded axis differences and validates shared conflicts without commands. Proposed files also open in the model viewer and isolated scene pose inspection with explicit unapplied labels, frame scrubbing and Restore. Retail service pose equality and browser inspection/no-command checks passed. | Arbitrary clip layouts, retargeting, general Blender/Unity import and gameplay acceptance. |
| Animation channel clipboard | FUNCTIONAL / OFFLINE AUTHORING. Copy verified retail or effective values to another frame draft or apply them across an inclusive range for the same rigid object. Retail browser range1..3, reversed-range rejection and two-step Undo restore passed. Actual town01 browser checks cover retail/effective copy, cross-object rejection, draft-switch guard, Discard, Apply and Undo; a fresh service read confirmed restored retail values and no contributors. | Runtime playback, arbitrary clip import and retargeting remain unverified or unsupported. |
| Scene animation inspection | FUNCTIONAL / OFFLINE. Actor-assigned and shared reference clips can be isolated on one scene instance, scrubbed, played at a chosen rate, and restored. Browser playback/pause/wrap/restore checks passed with unchanged project state; shared savepoint loop uses the correct model route. | Runtime cadence, GTE rounding, actor height/facing and game-equivalent pose/visibility remain unverified. |
| Assembled scene GLB export | FUNCTIONAL / OFFLINE. Editor exports complete authored/retail source previews with shared geometry, instance transforms, private files and stale-source rejection. Actual map01 browser export313instances/38geometries passed GLB validation with zero errors/warnings. Independent glTF-Transform import matched all313world bounds within0.00001sourceunits. Dolk2 retail/authored exports retain441instances with exactly the saved actor0001 X change and440unchanged bounds. Selected actor, decoration and ground browser exports pass independent bounds checks. Authored draft export retains UUID/kind/world placement and is rejected in retail mode. Selected scenery/ground/draft GLBs validate with zero errors/warnings. | External rendered consumer acceptance and runtime visual parity. |
| Complete animation GLB export | FUNCTIONAL / OFFLINE. Frame snapshots and complete rigid-object clips have distinct editor actions. Explicit1..120fps export, STEP tracks, terminal hold, private files, source metadata and HTTP validation. Actual30-frame browser export passed Khronos validation (0errors/0warnings) and glTF-Transform4.5.0 import (10nodes/20channels). | Blender5.2.2 independently rendered and evaluated Dolk2 actor0001:61 source-pose samples, STEP holds and terminal pose passed within0.000018 source units; saved scene reopened. Wider clips/Unity, retail lighting/blend equivalence, skins and equipment behavior remain unverified. |
| Partial-object animation poses | FUNCTIONAL / BOUNDED. Source-supported clips track leading model objects and omit untracked trailing objects without altering cached full geometry. Station0010(7/8objects) and Balden2/0015(1/10objects) pose/full-frame/export checks passed. | Balden2/0008 has6channels/4objects and remains unavailable; its correct runtime binding is unresolved. Fresh partial script inspection contains no decoded model selector, which does not exclude rebinding elsewhere. |
| Clipless multipart props | FUNCTIONAL / BOUNDED. Zero-initial-animation actors can draw raw objects with one actor transform, following the pinned reference play renderer. Station0007 now previews; unresolved nonzero-animation bindings still reject fallback. | Actual runtime draw/visibility acceptance and broader scene coverage. |
| Kingdom overworld scene preview | FUNCTIONAL / OFFLINE COVERAGE. Isolated saved imports: map01 has8actors/305environment instances/16,251terrain cells; map02 has7/276/16,381; map03 has19/244/16,374. All instances decoded as renderable within current budgets. All three browser previews verified: map01 313/313, map02 283/283, map03 263/263. map02/map03 perspective and orthographic captures visually inspected with zero page errors. | Dynamic water/visibility/encounters, world-map camera and retail gameplay parity. Source geometry support does not imply complete world-map behavior. |
| World-map landmark menu | FUNCTIONAL / READ-ONLY. Verified SCUS executable tables expose16 names and20 source placement records, discovery flag indices, destination IDs and menu pixels through the editor and searchable Asset Database. Exact CDNAME destination labels and catalog-to-landmark navigation are browser verified. Synthetic bounds/unknown-name tests and actual browser workflow passed. | Complete 3D world-map behavior, current discovery-state evaluation, menu authoring and gameplay acceptance. |
| Script model selectors | FUNCTIONAL / BOUNDED OFFLINE AUTHORING. Source-qualified signed16 SET_ACTOR_MODEL operand commands, source/effective layers, draft dispatch display, instruction-field navigation, history/persistence, descriptor package and experimental streaming/append serialization. Retail browser and exact town01/Dolk2 output readbacks passed. | Runtime pool-base/asset resolution, mesh restaging, animation pairing, story execution and gameplay remain unverified. Viewport does not simulate the opcode. |
| Script movement authoring | FOUNDATION / OFFLINE. Verified source-record X/Z serializer for MOVE_TO and NPC_RUN, plus NPC_RUN/EXEC_MOVE encoded move-selector bytes with unresolved behavior, with stable owner/PC IDs, exact byte audits, immutable baselines and source-grid validation. Fresh Dolk2/town01 edits each changed one MAN byte and fit original payload spans. Project ScriptMovement commands, authored/effective layers, Undo/Redo, Save/Open and authored asset summaries now pass synthetic and fresh Dolk2 checks.  Server-verified actor/partition-2/trigger reports and strict edit/clear HTTP command shapes are connected; retail HTTP checks passed.  Inspector controls now pass browser Apply/Clear/Discard, grid validation, Undo/Redo and Save/reload; independent disk reopen retains X9408. | Retail/authored effective target overlays now pass browser coordinate comparison, unchanged-target checks and partial-report rejection without authored commands. Gameplay acceptance remains pending. Descriptor MAN Build now composes movement and other supported edits with byte-audit conflict checks; a town01 package independently decoded to exactly two requested changes. Append-aware source-owner rebasing now passes Dolk2/town01 exact-byte checks and retains donor copies. Streaming/appended MAN experimental disc integration now composes movement edits. A combined Dolk2/town01 export with an appended Dolk2 NPC passed rebuilt-PROT readback. Gameplay remains unverified. |
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
| Model shape replacement | PARTIAL / AUTHORING | Same-layout source TMD vertex/normal XYZ replacement, content-addressed files, strict provenance, undo/redo, save/reopen, explicit authored preview/export and grouped compressed model overlays. All 119 town01 model layouts passed a coordinate edit; two models built into one verified overlay; party idle shape passed 15 frames. Browser authored view/export and OBJ file-picker upload/discard/clear verified. Complete source-bound vertex/normal JSON now supports imported/authored download, Apply shape, Undo/Redo and Save/Open. All119 town01 models round-trip exactly; a normal-only model0009 package passed exact independent member readback. Build reports expose scalar object/vector/axis changes and hash-checked authored-model navigation. Direct Edit model vectors now selects an object/kind/index, edits signed16 XYZ with inspected-hash validation, and supports Discard/Apply/Undo; retail normal edit/readback passed. The WebGL preview has no normal-based lighting. Ordered OBJ Blender roundtrip preserved source bytes; an edited vertex survived import. Party and NPC animation composition passed 15 frames, and separate-stream texture/animation combinations built. Scene visual checks, exact cross-family shared-container composition and gameplay remain pending. Arbitrary topology/material replacement is not supported. |
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
instruction navigation; at this checkpoint pager uncertainty prevented menu authoring. The September30 equal-span label writer preserves those unresolved controls without claiming execution.
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

September 30 regression checkpoint: retail-enabled Python SDK discovery passed
352 tests in 200.919 seconds at `1021bff1`, with no skips reported. Browser-only
viewport and path-query behavior retains separate focused verification. Runtime
acceptance remains deferred; no green suite is treated as gameplay parity.

September 30 palette editor: existing indexed scene TIM palette words now have
retail/effective inspection and source-bound Apply/reset/Discard within the
editor. A one-entry retail probe passed Undo/Redo, persistence, Build, exact
archive member readback and browser Apply/Undo. This does not establish runtime
palette effects, shared-bank authoring or full texture residency.

September 30 indexed image editing: source-qualified4/8-bpp pixel palette-index
inspection and Apply are available from bitmap Shift-click. Source hash guards,
packed-neighbor preservation, palette preservation and ordinary texture
history/persistence/Build checks passed. Runtime appearance remains unverified.

September 30 texture JSON interchange: source-bound complete indexed palette
and pixel arrays support retail/effective downloads and import through texture
replacement history/persistence/Build. All96 town01 indexed scene textures
round-trip exactly. Combined palette/pixel package and browser download/import/
Undo checks passed. Resizing, quantization and arbitrary format/layout changes
remain unsupported; runtime visual acceptance remains deferred.

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


September30 regression checkpoint at f8f135e4:383 retail-enabled Python SDK tests
passed in162.551s, exit0, no skips. Log:
local-output/sdk-20260909/sdk-regression-20260930-script-authoring.log.
Supersedes365-test checkpoint; browser/JavaScript and gameplay acceptance retain
separate evidence and are not established by Python discovery success.


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


Object-transform previews (2026-09-30): implemented before Apply in the model
vector Inspector for translation, rotation and scale. Source-bound proposed/current
geometry comparison, shared framing and draft/stale-response guards passed focused
model and retail browser checks without history or authored-file changes. Gameplay
acceptance remains deferred; the383-test checkpoint predates this feature.


Scene shape proposal inspection (2026-09-30): implemented for supported renderable
instances using their verified existing pose and scene placement. One-instance
isolation, Return to vector inputs and exact Restore passed focused and retail
browser checks without authored changes. Gameplay acceptance remains deferred;
383-test checkpoint predates this addition.


Model replacement file scene inspection (2026-09-30): TMD/OBJ/JSON proposals
can be inspected before Apply on a verified instance and pose, with exact Restore
and Return retaining the selected file. Retail browser/file-size/hash/state checks
passed without authored changes. Gameplay acceptance remains deferred;383-test
checkpoint predates this addition.


Shared model proposal impact (2026-09-30): all supported scene instances can be
previewed before Apply for transforms or replacement files, with distinct source
poses, preserved placements and explicit unavailable counts. Retail model0074
all11 placements, Restore/Return and unchanged state passed. Focused multi-pose
and browser checks passed; gameplay acceptance remains deferred.


Texture proposal scene inspection (2026-09-30): TIM/JSON proposals can be previewed
through the static image/CLUT material decoder before Apply, retaining geometry
and placement. Retail texture29 changed31 materials/19 geometries/58 instances;
Return/Restore, late-response withdrawal, unchanged project/authored-file hashes
and TIM readback passed.23 retail-enabled focused tests passed. Runtime texture
residency/gameplay appearance remain unverified;383-test checkpoint predates feature.


**Scene proposal comparison (2026-09-30):** model-transform, model-file and
texture proposals can switch between Proposed (not applied) and Current authored
scene while retaining the proposal and camera framing. Exact layer/restore and
unchanged project checks passed in retail browser runs for shared model0074
(11 instances), a JSON model-file proposal, and texture29 (19 geometries,
31 materials, 58 instances). Texture checks also verified unchanged camera and
withdrawal on a stale scene source. These are browser checks, separate from the
390-test Python checkpoint; game appearance and retail visibility remain deferred.

**Animation scene comparison (2026-09-30):** supported animation inspections now
switch between the inspected animation and Current authored scene, retaining the
selected frame and camera. Switching layers pauses playback; the current layer
disables scrubbing, playback and rate controls. Returning restores the inspected
frame and slider together. A retail actor0011 JSON proposal (15 frames) passed
exact layer/placement/base checks, playback pause, Return retaining the file,
Restore, stale-source withdrawal and unchanged project state, with zero authoring
requests or page errors. Screenshot inspected. This is separate browser evidence;
retail animation timing, playback and gameplay visibility remain deferred.

**Independent animation consumer review (2026-09-30):** Blender 5.2.2 rendered
and evaluated a fresh complete Dolk2 actor0001 GLB (30 frames, ten rigid objects,
three embedded textures). All61 source-decoded samples, including half-frame STEP
holds and terminal pose, matched within0.000018 source units;24 distinct geometry
snapshots establish motion. First/middle/last renders were visually inspected.
The saved Blender scene reopened with all meshes, animation actions and three
packed textures. A reusable offline review tool and [consumer review guide](legaia-glb-consumer-review.md)
are available. Acceptance is specific to this clip; wider clips/consumers, retail
cadence, lighting and gameplay remain unverified. No game was launched.

**Indexed texture rectangle copy (2026-09-30):** copy an existing 4/8-bpp
image region to another location in the same texture, with draft pixels and
source/destination bounds before Apply. Overlaps read the immutable pre-copy
indices; packed neighbors, palettes, headers and VRAM layout stay unchanged.
Retail texture29 browser checks passed draft/no-write, bounds and stale-hash
rejection, no-op/no-history, Apply, Undo/Redo, Discard, Save/reopen and Build.
Independent package readback matched all pixels/palettes and the saved33312-byte
TIM; three indices/image bytes changed, zero palette words.24 retail-enabled
focused tests passed with no skips. The390-test checkpoint predates this feature;
gameplay appearance remains deferred.

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

**Saved runtime node review (2026-09-30):** the Observed nodes panel can
export decoded metadata and reopen it later in Edit mode as a historical,
read-only Inspector. Positions/capture frames, uncertain fields, evidence and
unconfirmed candidate IDs are retained; raw prefixes and guard tokens are
excluded. Saved files never set Live state/correlation or change project/camera.
Serializer and synthetic browser download/reopen/filter/stale/file-read guards
passed with zero authoring requests or page errors. All17 fields from the actual
profile decoder on a synthetic prefix were accepted. See the [review guide](legaia-runtime-node-review.md).
No real runtime capture was performed; capture/gameplay acceptance remains deferred.


Historical regression checkpoint (2026-09-30):392 retail-enabled Python tests passed
in159.893s, no skips, source1eafc313; supersedes390 at05e93405. Texture usage,
script operand and runtime-review JavaScript checks and editor syntax passed.
Private log/metadata: sdk-regression-20260930-runtime-review.log/.json under
local-output/sdk-20260909. This covers accumulated SDK services and new rectangle
copy preservation/rejection; browser and gameplay acceptance remain separate.

2026-09-30 menu-label authoring: see [the guide](legaia-menu-label-authoring.md).
This addition follows the392-test source checkpoint and has54 focused retail-enabled
tests plus separate browser/package readback evidence. No new full-suite claim
or gameplay acceptance.

2026-09-30 field menu navigation: source-bound retail/authored/effective label
runs appear beside decoded picker choices, with exact-form links. Pure JS
checks reject owner/PC/option/target/token mismatches, duplicates and excessive
collections; multiple runs and partition-two identities are supported. Retail
browser checks found30 links, preserved an unapplied draft and unchanged
project/camera/service, and rejected stale source or withdrawn report navigation.
No authoring requests or page errors; screenshot inspected. This follows the
392-test checkpoint and retains separate JavaScript/browser evidence.

2026-09-30 source-bound text files: connected script/dialogue workspace exports
complete supported run snapshots (including menu labels), previews proposed
changes, and applies atomically through one history entry. Immutable metadata,
MAN/owner/current text-state binding, 1MiB file limit and equal-span serializer
checks guard imports. Null clears a run override; other components survive.
Six focused project/text tests, Node operand checks and syntax passed. Retail
browser download/no-op/preview/rejection/Apply/Undo/Redo/Save/late-read checks
and independent package readback passed. See [text JSON guide](legaia-text-json-authoring.md).
Full392-test checkpoint predates this addition; no gameplay acceptance.

2026-09-30 renderer newline fix: plain-glyph authoring excludes pipe0x7C, a
font-renderer newline despite the MES Glyph event. Source bytes split editable
runs and are preserved; all write paths reject introducing them. Legacy project
readback preserves prior files/overrides and exposes an invalid effective value;
Clear/Undo or supported replacement resolves the edit.58 focused retail-enabled
tests (29.566s, no skips), Node/syntax and retail browser rejection/legacy review
passed. Synthetic spans establish byte preservation; town01 scan found no
reached newline glyphs. This follows397-test checkpoint; gameplay deferred.

### Saved scene views — 2026-10-01

Source-bound project camera bookmarks with cross-scene recall, representation and
scene layers; metadata CRUD, Undo/Redo and Save/Open. Camera targets remain editor
display coordinates. Fourteen focused Python/HTTP checks, Node validation/syntax
and retail-source browser recall/history passed; no gameplay or live-identity
claim. Postdates the integrated 457-test checkpoint. See
[saved scene views](legaia-saved-scene-views.md).

### Integrated offline source checkpoint — 2026-10-01

Retail-enabled Python discovery: **463 tests**, 264.543 seconds, exit 0, no
skips; source `2ca0a1a4fa0044f55e9b0dc6d6c217b9e061f578` unchanged throughout.
All 13 Node checks and all 16 editor-module syntax checks passed on that source.
Includes SDK animation/preset actions and saved scene views; supersedes the
457-test checkpoint. This covers offline services and UI guards, with separate
browser/package/rendered evidence. Native runtime and gameplay remain deferred.
Private evidence: `local-output/sdk-20260909/sdk-regression-20261001-scene-views.log/.json`
and `node-checks-20261001-scene-views.json`. No game launched.
