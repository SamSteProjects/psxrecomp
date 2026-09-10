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
| Asset database | PARTIAL / READ-ONLY | Searchable models, actors and scenes, plus source-verified discovery of 96 textures, 14 referenced animations, 52 actor scripts and 344 dialogue segments in town01 (678 total records). Derived resource registration is separate from immutable imports and authored state. Project-wide Authored assets links actor edits, TIM replacements and position templates to their editors, including cross-scene navigation without a derived catalog refresh. Content-addressed TIM replacement registration is supported; broader replacement families remain pending. |
| Model preview | PARTIAL | All 29 town01 actor-referenced models decode. Browser-verified object-local geometry and matched textures; F0/F1/F2 idle/walk and supported scene-header NPC poses have stepping and playback. Runtime equipment, battle animation and ETMD breadth remain pending. |
| Model export | FUNCTIONAL / STATIC | Editor Export GLB writes a full supported model or current baked pose to private project Exports. Embedded textures, provenance and axis conversion; Vahn and tree pass Khronos validation and Blender import/render. No animation channels, replacement importer or physical scale claim. |
| Textures | PARTIAL / AUTHORING | Bounded 4/8/16/24-bit TIM decoding; town01 has 96 searchable TIM assets with direct image inspection and local palette selection. Material association resolves 38 unique crops, 26 untextured and 8 unresolved among 72 materials. The separate shared-party bank resolves all eight used F0/F1/F2 materials. Matching-layout TIM replacements support image/palette edits, imported/effective previews, history, persistence and guarded builds. Runtime replacement display, residency, blend and animated palettes remain unverified. |
| Animations | PARTIAL / READ-ONLY | Six field-party clips plus scene-header NPC clips with stepping, playback and posed export. The resource browser lists 14 unique town01 animations through 39 verified actor bindings; 13 unavailable associations stay explicit. Independent party comparison covers 20,845 vertices. Runtime timing, equipment and battle animation remain pending. |
| Scene model | FUNCTIONAL | Imported actor entities and evidenced Transform/ModelRenderer/Animation/RetailMetadata components. Authored Dialogue runs bind to verified record-relative source spans. Triggers/collision and general script bindings remain unresolved. |
| Model/animation assignment | FUNCTIONAL / WRITABLE | Verified same-scene donor pairs connect to project commands, undo/redo, save/open, scene preview, posed export and bounded mod builds. Combined appearance/position edits serialize one composed buffer; clearing edits restores baseline package bytes. Script compatibility and gameplay appearance remain unverified. |
| Project authoring | FUNCTIONAL | XYZ, supported donor-appearance and bounded dialogue overrides, selection, undo/redo, dirty state, content-addressed imported evidence and digest-checked save/reopen. Transform templates capture/apply supported axes. Native actor creation, heading and arbitrary model/animation replacement remain pending. |
| Editor | PARTIAL | Verified selection/edit/clear/undo/redo/save/reopen, textured object preview, private Build & Run, attach and graceful Stop. Central WebGL scene preview renders 51/52 town01 entities with mesh picking, focus, transform updates and marker fallback. Scripted placement/visibility, retail height/facing and broader editing tools remain pending. |
| Live bridge | PARTIAL / LIVE-VALIDATED | Cold town01 v2 capture accepted 90 nodes under executable/witness/scene/epoch guards. Archived v1 remains strict; title rejects and town0c/transition acceptance remains pending. |
| Correlation | PARTIAL / READ-ONLY | Guarded MAN-header/model evidence yields explicit candidates and ambiguity. Actor0052 authored header and world position match `(4480,11904)`, with a visible savepoint beside Vahn. Generic bindings remain candidates; they are not promoted to confirmed identity. |
| Scripts/dialogue/flags | PARTIAL / BOUNDED TEXT WRITING | Actor inspector decodes supported bounded MAN instruction paths and inline dialogue, with explicit substitution tokens, flag operands, successors, opaque bytes and stop reasons. The asset browser links script/dialogue resources to their actor inspector and records 380 source-qualified flag references. Town01 actor0049 shows 23 instructions/seven dialogue segments; actor0001 stops at unsupported0x29. Supported plain-text runs have Apply/Clear, undo/redo, save/open and guarded build serialization; town01 exposes 154 runs across 16 actors. No script execution, story-state evaluation, control editing or text relocation. Gameplay text display remains unaccepted. |
| Transitions/world map | FOUNDATION | Prior observation vocabulary retained. Script resources expose encoded named scene-change references when decoded; none occur in the supported town01 paths. Reachable transition graphs, MAPDSIP coverage and world-map authoring remain pending. |
| Build and Run | FUNCTIONAL / PARTIAL ACCEPTANCE | Supported X/Z, donor appearance and bounded text edits build into guarded private .psxmod packages; clearing edits builds a verified zero-overlay retail baseline. Editor-owned Windows launch verifies executable/BIOS/disc/mod identity; Attach and Stop pass. Cold game consumed 24894 patched bytes over13sectors and rendered town01. A moved savepoint visibly appears at its authored location; a fresh zero-overlay retail run removes it there and restores its original world coordinates. |

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
