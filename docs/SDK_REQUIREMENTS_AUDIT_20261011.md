# SDK Requirements Audit — 2026-10-11

The full SDK goal is **incomplete and active**. This audit compares the requested product areas with current implementation entry points and scoped evidence. It corrects older feature-matrix descriptions that predate delivered authoring work. Code presence, historical receipts and source inclusion are different evidence levels; none substitutes for whole-product gameplay acceptance.

Inspected implementation revision: `e7b99de012bbe91afef61be3a5aacbdd3559d1eb`. Current scoped workflow evidence includes `local-output/sdk-20260909/worldmap-animation-authoring-20261011/` native, client, editor and package proofs. Earlier subsystem receipts are referenced by their detailed guides and were not rerun here. The October 6 integrated campaign predates later changes; there is no fresh complete-suite claim.

| Specification Area | Current Implementation/Evidence | Remaining Requirement or Limit |
| --- | --- | --- |
| Working Release Fixes, Overlays, Precompile, Restore, Audio, Input | [Parity Ledger](legaia-release-parity.md); fresh eight-file source inclusion matches the retained receipt. | Fresh binary/sibling identity and full runtime equivalence are unproven. Cold audible startup, FMVs, repeated field/cross-scene restore, lifecycle/performance and toolchain gates remain separate. |
| Layered SDK Services and Stable Provenance | `sdk/project.py`, `sdk/server.py`, `sdk/project_assets.py`; immutable imports, derived source registrations, authored commands, Live evidence and Generated packages remain distinct. | Not every retail structure is understood. Architecture presence does not prove complete game-format coverage. |
| Retail Scene Import and Central Asset Database | [Project Assets](legaia-project-assets.md), [Batch Import](legaia-scene-import-batch.md); metadata index supports fifteen resource kinds and retained/authored identities. | Unsupported scenes/layouts remain explicit; memberships do not establish runtime residency or reachable content. |
| Scene/Entity/Component Editor and 3D Workspace | `editor/component-inspector.js`, `editor/scene-renderer.js`, `editor/hierarchy-navigation.js`; linked selection, inspectors, gizmos, camera/views and scene previews. | Whole-game placement, height/facing, scripted visibility and runtime visual parity remain partial. |
| Models and Textures | [Model GLB](legaia-model-glb.md), [Topology Allocation](legaia-model-topology-allocation.md), Current/native texture workflows. | Unsupported TMD/ETMD headers/packet modes and battle/equipment breadth remain an offline research frontier. Static skin/morph baking does not establish native animated skin support. |
| Animation Identity, Association, Preview and Replacement | [Field GLB](legaia-animation-glb.md), [World GLB](legaia-worldmap-animation-glb.md), [Native Channels](legaia-worldmap-animation-channels.md); field/shared/retained and registered World workflows. | Native cadence/activation, battle motion, equipment and unmatched model/clip relationships remain unresolved. |
| Actor/NPC Authoring | Donor-based NPC definitions, creation/groups/presets, reviewed scripts/appearance/arrivals, normal history/persistence/native package paths. | Native actor-pool bounds apply. Story behavior and authored gameplay need manual verification; this is not arbitrary actor/skeleton invention. |
| Dialogue, Scripts, Flags and Game State | [Branches](legaia-script-branches.md), [World Operands](legaia-world-script-animation-operands.md), [NPC Arrivals](legaia-npc-arrival-authoring.md); qualified operand families and separate layer/flow inspection. | Complete VM semantics, story-state evaluation, runtime flag banks and execution/reachability remain partial. |
| Collision, Regions and Transitions | Reviewed native field collision/region/trigger/arrival workflows; source/Current/Proposed viewport inspection and package evidence. | Runtime floors, actor blockers, collision behavior, travel and route activation remain unverified or unknown. |
| World Scene/Resource Authoring | [Placement Allocation](legaia-worldmap-placement-allocation.md), model/texture/script/channel tools and Current resource composition. | Runtime activation, complete MAPDSIP translation and broad playable parity remain open. Older statements that cell/model reassignment is absent are superseded by current implementations. |
| Audio Authoring | [Bank Authoring](legaia-audio-bank-authoring.md), [Sample Authoring](legaia-audio-sample-authoring.md), MIDI/SEQ and retained WAV workflows. | Offline audition and native bytes do not prove runtime music mapping, routing, residency, effects or audible game correctness. |
| Commands, History, Persistence and Build | Typed commands, freshness-bound Review/Apply, retained inputs, Save/Open, composed private native packages and saved reports. | Recent package evidence does not prove a current executable or installed, playable full mod. Rebuild/run/install/disc export are deferred. |
| Live Bridge, Traversal and Correlation | Retained profile/identity/execution-witness/epoch guards, bounded traversal and candidate correlation; historical narrow Live evidence. | Full transitions and restore reacquisition remain manual gates; candidates are not confirmed actors by list order or pointers alone. |
| Documentation, Final Report and Comprehensive Tests | Architecture, feature matrix, provenance, parity and test plan exist; this audit refreshes their current scope. | Final complete-game report/acceptance and a fresh post-buildout integrated campaign remain outstanding. Targeted checks cannot establish whole-product completion. |

## Fresh Source Inclusion Result

All five recorded runtime/precompile sources and three fixtures match their expected SHA-256 values. Fresh receipt: `local-output/sdk-20260909/requirements-audit-20261011/stability-source-inclusion.json`. The audit explicitly reports `execution_repeated=false`, `runtime_binary_verified=false` and `gameplay_verified=false`. No missing patch or drift was found in **this recorded set**; this does not audit every runtime file or a current sibling release checkout.

## Battle Discovery Checkpoint — 2026-10-11

[Battle Character Resource Discovery](legaia-battle-character-resources.md) now supplies source-qualified importer/services for five existing-format model bodies and six complete TIMs, with a seventh partial record. Four retail-enabled source/HTTP checks pass. Project-browser global registration and source-only model/TIM editor inspection now pass offline checks; battle assembly/animation remain incomplete; this does not broaden gameplay acceptance.

## Next Development Frontier

Offline implementation is still possible. The next high-value research area is provenance-qualified discovery of battle/extended model and animation formats, which current decoders explicitly leave unsupported. Establish pinned reference and retail layout evidence before registering new assets or extending codecs. Full runtime timing, visibility, audible output and cross-scene restore remain gameplay-dependent gates and are deferred under the user's current instructions.

No native compilation, game launch/attach, installation, disc export or broad test campaign ran for this audit. No proprietary payload is part of the documentation change.


## PLAYER Editor And Delivery Checkpoint — 2026-10-11

The earlier Battle Discovery checkpoint above is historical. Current PLAYER coverage now includes four physically bounded equipment sources, stored action identities, selected static textures, native tagged GLB Review/Apply, retained input replay, Current inspection, Undo/Redo, Save/Open, package Build, Current interchange and local action scrubbing/playback. [PLAYER Battle Assembly](legaia-player-battle-assembly.md) records the scoped evidence and limits. Package delivery was verified in local commit `b68756dfd`; Current action/interchange integration was verified in `5d17f0d34`. The latest local playback evidence covers eight Retail/Current receipts, sixteen native reference poses, exact source spans and actual editor transport behavior. These do not qualify native action authoring, runtime timing/activation or broad gameplay parity.

This advances the animation and model/equipment rows without closing their remaining runtime and unknown-format requirements. Further offline work remains possible in native animation replacement and extended battle-format discovery. No game-dependent gate is marked complete; no fresh binary or full-suite claim is added.


## Native PLAYER Action Workflow Checkpoint — 2026-10-11

[Native Action Editor And Build](legaia-player-battle-assembly.md#native-action-editor-and-build) now covers numeric existing-layout PLAYER channels through fresh Review, unsaved Proposed pose, Apply/history/persistence, authored Current sampling/export and composed native package readback. Separate model and action projection ownership prevents record0/pool replacement conflicts. This advances eventual animation replacement for the bounded nine-byte PLAYER format; it does not close action allocation/interchange import, unknown extended formats, native cadence/activation or gameplay requirements. Runtime/release gates remain deferred.


## PLAYER Motion Interchange Checkpoint — 2026-10-11

[PLAYER Action GLB Import](legaia-player-action-glb.md) now extends existing-layout motion replacement through editor Review/Proposed/Apply, retained GLB/native-baseline replay, history/persistence, Current sampling and private package delivery. This supersedes earlier statements that PLAYER action interchange import is absent. The native converter round-trips 38 supported actions/605 frames and preserves full twelve-bit rotation precision; attachment aliases cannot disagree. Actual muted Edge editor and scoped source/client/package checks pass. New action allocation, anatomical skin/retargeting, runtime activation/cadence and playable acceptance remain open. No current executable/full regression or gameplay claim is added; the full goal remains incomplete and active.


## Shared Texture Input Assets Checkpoint — 2026-10-12

[Shared PNG Input Assets](legaia-field-texture-authoring.md#shared-png-input-assets) advances the Asset Database and texture workflow requirements: active original images/masks now have stable historical identities, source-qualified metadata, matching native references and read-only inspector recovery/navigation. Native replay, package readback, client refusal checks and actual editor recovery pass at the documented scope. Retail, historical input and final Current pixels remain distinct. This closes the active shared-input registration gap recorded in the earlier texture checkpoints; it does not establish archive-library management, growing layout allocation, native blending, runtime appearance or playable delivery. Full objective remains incomplete and active, with gameplay-dependent gates deferred.


## Monster Archive Checkpoint — 2026-10-12

[Monster Archive Discovery](legaia-monster-archive.md) advances global battle/extended-resource coverage with 186 source-qualified object-local models and stored record provenance from PROT 867. Discovery, Asset Database registration, read-only 3D inspection and bounded source/client/browser checks pass. This is FUNCTIONAL / READ-ONLY / OFFLINE for the documented source workflow. Monster texture relocation/rendering, assembly, animation, interchange, native authoring/delivery and gameplay parity remain partial or unimplemented. Stored stats are distinct from live battle values. No runtime gate is closed; the full SDK objective remains incomplete and active.


## Monster Pool Texture Checkpoint — 2026-10-12

[Monster Source Pool Textures](legaia-monster-archive.md#source-pool-texture-inspection) advances source model/texture coverage with exact pool qualification, 186 Texture registrations, fifteen-palette inspection and independently replayed source-local material crops. The documented native/client/editor workflow is FUNCTIONAL / READ-ONLY / OFFLINE. Nine material UV ranges remain unavailable beyond their own source page; runtime placement/blending, assembly, animation, authoring/delivery and playable acceptance remain open. The full objective is incomplete and active.
