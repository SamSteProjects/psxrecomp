# Legaia SDK feature matrix

Status recorded during the 2026-09-09 buildout. FUNCTIONAL means the named
workflow runs within its stated bounds; it does not mean the entire subsystem
is complete. Runtime fixes from the preceding milestone are committed as
`189a2d24994dab0443d053fa2e60bc2867553920`.

| Subsystem | Status | Implemented evidence / remaining acceptance |
|---|---|---|
| Release parity | PARTIAL | Stability/source audit in `legaia-release-parity.md`; Windows build, rendered title/opening story and bounded process/audio samples passed. Field gameplay, FMV continuity and audible quality remain unaccepted. |
| Overlay precompilation | FUNCTIONAL | Build-time split discovery; growth/shrink/body edits and helper isolation checked with compiled fixtures. Ten intended retail roles; MAPDSIP completeness not claimed. |
| Restore ownership | FUNCTIONAL | Explicit native invalidation and lazy-cache reset; repeated restore fixtures pass. Restored retail performance remains a separate gate. |
| Disc / scene import | FUNCTIONAL | Exact SCUS-94254 disc identity, ISO/PROT/CDNAME/LZS/MAN readers; town01 52 actors/119 models/52 resolved and town0c 44/115/44. Unsupported bundle layouts fail explicitly. |
| Asset database | FOUNDATION | Disc-scoped structural model IDs, source records and dependencies field. Rich dependency graph, textures, replacement assets and animation catalog pending. |
| Model preview | PARTIAL | All 29 town01 referenced models decode; individual object triangles visibly render in the editor. Skeletal pose, ETMD breadth and texture association need separate acceptance. |
| Scene model | FUNCTIONAL | Imported actor entities and evidenced Transform/ModelRenderer/Animation/RetailMetadata components. Triggers/collision/dialogue/scripts remain unresolved. |
| Project authoring | FUNCTIONAL | XYZ overrides, selection, undo/redo, dirty state, content-addressed imported evidence, digest-checked save/reopen. Heading/model/animation editing and templates pending. |
| Editor | PARTIAL | Browser-verified selection/edit/clear/undo/redo/save/reopen and actual model preview; responsive workspace tabs, placement markers and transform handles. Real posed scene rendering remains pending. |
| Live bridge | PARTIAL | Generic identity/guard/witness/read-regions protocol ported; live executable identity and capability negotiation pass. Field observation correctly rejects missing witnesses at title; accepted retail field traversal remains pending. |
| Correlation | FOUNDATION | Structural imported identities and epoch-scoped runtime nodes exist separately. No guessed list-order mapping; matching engine pending. |
| Scripts/dialogue/flags | FOUNDATION | Unknown fields retained with provenance. Decoders, editor tools and bounded round-trip serializers pending. |
| Transitions/world map | FOUNDATION | Prior observation vocabulary retained. Transition graph, MAPDSIP coverage and world-map authoring pending. |
| Build and Run | PARTIAL | Representable X/Z edits serialize to hash-guarded streaming disc overlays in a private .psxmod. Retail one-byte edit round trip, package parser/installer and enabled runtime boot pass. Actual patched-sector consumption and visible authored actor placement require further acceptance. |

The primary acceptance path is import -> hierarchy/viewport -> select -> edit ->
undo/redo -> save -> reopen with original retail evidence unchanged. The later
build acceptance must prove the authored edit in a running game, including
revert, rather than treating an exported metadata file as a playable build.
