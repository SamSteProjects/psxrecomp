# Legaia SDK feature matrix

Status recorded during the 2026-09-09 buildout. FUNCTIONAL means the named
workflow runs within its stated bounds; it does not mean the entire subsystem
is complete. Runtime fixes from the preceding milestone are committed as
`189a2d24994dab0443d053fa2e60bc2867553920`.

| Subsystem | Status | Implemented evidence / remaining acceptance |
|---|---|---|
| Release parity | PARTIAL | Stability/source audit in `legaia-release-parity.md`; Windows build, rendered title/opening story/town01 arrival and bounded process/audio samples passed. The reproduced opening-FMV stall is fixed; a no-input cold run reaches the title menu. Other FMVs, full field gameplay and audible quality remain unaccepted. |
| Overlay precompilation | FUNCTIONAL | Build-time split discovery; growth/shrink/body edits and helper isolation checked with compiled fixtures. Ten intended retail roles; MAPDSIP completeness not claimed. |
| Restore ownership | FUNCTIONAL / BOUNDED LIVE VALIDATION | Explicit native invalidation and lazy-cache reset; repeated restore fixtures pass. One idle retail restore retained 59.85/60.02 FPS cold/restored and recurrent static ownership. Cross-scene/repeated retail restoration and full Live-profile reacquisition remain separate gates. |
| Snapshot integrity | FUNCTIONAL / BOUNDED | Header identity rejects independently of diagnostic storage. All known sections validate and prepare before commit; corrupt input and MDEC allocation failure preserve guest state. Executable raw/zlib/reordered/repeated/partial-command regressions pass. Retail scheduler restoration is a separate gate. |
| Disc / scene import | FUNCTIONAL | Exact SCUS-94254 disc identity, ISO/PROT/CDNAME/LZS/MAN readers; town01 52 actors/119 models/52 resolved and town0c 44/115/44. Unsupported bundle layouts fail explicitly. |
| Asset database | FOUNDATION | Disc-scoped structural model IDs and provenance; texture catalog supplies static address-based material dependencies. Central animation/replacement asset catalog remains pending. |
| Model preview | PARTIAL | All 29 town01 actor-referenced models decode. Browser-verified upright object-local geometry with matched textures; F0/F1/F2 idle/walk rigid posed previews have stepping and playback; general NPC/battle animation and ETMD breadth remain pending. |
| Model export | FUNCTIONAL / STATIC | Editor Export GLB writes a full supported model or current baked pose to private project Exports. Embedded textures, provenance and axis conversion; Vahn and tree pass Khronos validation and Blender import/render. No animation channels, replacement importer or physical scale claim. |
| Textures | FUNCTIONAL / READ-ONLY | Bounded 4/8/16/24-bit TIM decoding; town01 96 TIMs, 38 uniquely matched textured material crops, 26 untextured and 8 unresolved among 72 materials. The separate shared-party bank uniquely resolves all eight used F0/F1/F2 textured materials against pinned upload evidence. Runtime residency, blend and animated palettes are not reconstructed. |
| Animations | PARTIAL / READ-ONLY | Six field-party idle/walk clips, stable provenance, ten rigid object channels, frame stepping and playback. Independent pinned transform comparison covers 20,845 posed vertices. Reference-derived 30 Hz is not a live timing measurement; equipment and general NPC/battle animation remain pending. |
| Scene model | FUNCTIONAL | Imported actor entities and evidenced Transform/ModelRenderer/Animation/RetailMetadata components. Triggers/collision/dialogue/scripts remain unresolved. |
| Project authoring | FUNCTIONAL | XYZ overrides, selection, undo/redo, dirty state, content-addressed imported evidence, digest-checked save/reopen. Authored transform templates capture/apply supported axes with provenance and undo/redo; native actor creation and heading/model/animation editing remain pending. |
| Editor | PARTIAL | Verified selection/edit/clear/undo/redo/save/reopen, textured object preview, private Build & Run, attach and graceful Stop. Central WebGL scene preview renders 51/52 town01 entities with mesh picking, focus, transform updates and marker fallback. Scripted placement/visibility, retail height/facing and broader editing tools remain pending. |
| Live bridge | PARTIAL / LIVE-VALIDATED | Cold town01 v2 capture accepted 90 nodes under executable/witness/scene/epoch guards. Archived v1 remains strict; title rejects and town0c/transition acceptance remains pending. |
| Correlation | PARTIAL / READ-ONLY | Guarded MAN-header/model evidence yields explicit candidates and ambiguity. Actor0052 authored header and world position match `(4480,11904)`, with a visible savepoint beside Vahn. Generic bindings remain candidates; they are not promoted to confirmed identity. |
| Scripts/dialogue/flags | FOUNDATION | Unknown fields retained with provenance. Decoders, editor tools and bounded round-trip serializers pending. |
| Transitions/world map | FOUNDATION | Prior observation vocabulary retained. Transition graph, MAPDSIP coverage and world-map authoring pending. |
| Build and Run | FUNCTIONAL / PARTIAL ACCEPTANCE | Supported X/Z edits build into guarded private .psxmod packages; clearing edits builds a verified zero-overlay retail baseline. Editor-owned Windows launch verifies executable/BIOS/disc/mod identity; Attach and Stop pass. Cold game consumed 24894 patched bytes over13sectors and rendered town01. A moved savepoint visibly appears at its authored location; a fresh zero-overlay retail run removes it there and restores its original world coordinates. |

The primary acceptance path is import -> hierarchy/viewport -> select -> edit ->
undo/redo -> save -> reopen with original retail evidence unchanged. The later
build acceptance must prove the authored edit in a running game, including
revert, rather than treating an exported metadata file as a playable build.

The scene preview additionally assembles 39 town01 actors from their verified
MAN header animation IDs and type-5 ANM bank. Independent comparison covers
5,028 frame-zero vertices. This extends the party-only animation foundation;
NPC clip playback controls, runtime clip selection/timing and battle animation
remain pending. Ten zero-ID actors do not acquire invented poses; supported
single-object models can render statically, while the multipart savepoint stays
a marker. Two party instances use explicitly labelled reference idle poses.
