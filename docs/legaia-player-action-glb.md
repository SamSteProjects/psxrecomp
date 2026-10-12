# PLAYER Action GLB Import

Offline checks passed — 2026-10-11. Existing-layout PLAYER motion GLB import now reaches editor Review/Proposed/Apply, retained-input validation, history/persistence, Current sampling and private native package delivery. Gameplay timing, activation and playable behavior remain unverified.

## Native Conversion

`importer/player_animation_glb.py::import_player_action_glb` consumes an exact Current PLAYER file hash, existing action identity/hash, selected equipment, an embedded GLB and explicit 1..120 Interchange FPS. The shared bounded glTF parser, rigid hierarchy sampler and STEP/LINEAR tracks supply scene-space poses at float32 native-frame-index/FPS times. The source frame/part counts remain fixed, endpoints hold, and no action allocation or runtime timing evidence is inferred.

Fresh native assembly owns the object-to-part mapping. Every native part must be represented. Equipment attachment objects that alias a body part must agree in sampled translation and orientation; conflicting tracks refuse instead of overwriting one another. The importer uses one Y reflection and source-biased Rz*Ry*Rx Euler quantization at full twelve-bit precision, with a 0.15-degree angular bound. Signed translations reject raw overflow before rounding. Existing field/World rotation precision stays at sixteen PSX units by default.

The normal PLAYER native channel codec applies sparse edits and enforces compressed record0 capacity. Headers, descriptor tables, model pools, other action bytes and unused allocation suffix remain protected. No-op imports keep the complete original compressed physical file. Meshes and textures do not author native model pools through this converter; skin/morph channels remain unsupported.

## Focused Evidence

All 38 supported retail actions across four source files and 605 frames round-trip through GLB with exact original file bytes. All 1210 attachment/body alias samples agree. Four modified imports preserve signed translation and non-multiple-of-sixteen native rotation values, with unchanged unselected decoded action bytes and protected physical ranges. Four attachment-only conflicts refuse. Invalid boolean/string/nonfinite/out-of-range rates reject. Full-precision source equivalence and gimbal-neighborhood checks pass alongside thirteen existing shared animation/clip checks.

Private evidence: `local-output/sdk-20260909/player-native-model-authoring-20261011/glb-action-import-proof.json`. Tests: `test_player_animation_glb.py`, `test_animation_glb.py`, `test_animation_clip_export.py`. Proprietary source data and derived files stay private.

## Review, Retained Inputs And Native Delivery

The editor exposes PLAYER Motion GLB and Interchange FPS inside Native PLAYER Action Channels after Current model/action inspection. Review converts the selected existing action; Preview Proposed PLAYER Action samples the unsaved native result in the current model viewport and timeline. Apply Reviewed PLAYER Action uses the exact fresh Review identity and creates one normal history step. Source/selection/file/rate changes withdraw the reviewed operation. No-op imports cannot Apply.

Exact routes `/api/player-action-glb-review` and `/api/player-action-glb-apply` bind project/source/catalog, equipment, action, inspected Current file/action hashes, complete GLB bytes, FPS and optional file-animation/node mapping. The normal native canonical ledger remains the saved Current truth. Fresh Apply regenerates the import and compares the complete receipt seal; old or altered inputs refuse before publishing state.

The latest imported GLB for each owned action is retained byte-exact at `Authored/PLAYER/ActionInputs/{sha256}.glb`. Its pre-import native baseline stays in the immutable ActionSources cache. Saved metadata records complete hashes/sizes, sampling/mapping choices and replay-receipt digest. Open and subsequent Current/Build validation check those files and independently replay the original import. Later numeric edits preserve this historical import evidence while changing the canonical channel ledger; the retained GLB is not silently presented as the final action after later edits. Undo/Redo retains files needed by historical states. Removing the entire action owner withdraws its active import metadata. Inputs are limited to 4 MiB per GLB and a combined 64 MiB active GLB/baseline project budget.

Focused HTTP/service checks pass unsaved Review, stale Apply refusal, one-step Apply, exact retained bytes, Undo/Redo, Save/Open, Current pose, later numeric edits retaining provenance and native package delivery. Tampering retained GLB bytes blocks Open. Client verification replays the reported sparse edits against the independently decoded Current action bytes and rejects eight altered input/receipt/proposed envelopes; it does not independently implement a second glTF hierarchy sampler. Eight existing Project/World checks pass. Private evidence: `local-output/sdk-20260909/player-native-model-authoring-20261011/glb-action-workflow-cases.json`.

Actual muted Edge editor passes edited GLB Review, unsaved Proposed preview/export gating, one-step Apply alongside an authored native model, Current action/pose witnesses, Undo/Redo and Save/Open. Wide/400-pixel captures were inspected; no page errors, commands or scene navigation occurred. Private evidence: `local-output/sdk-20260909/player-native-model-authoring-20261011/action-glb-browser-proof.json`. The native workflow remains existing-layout rigid motion: new actions, anatomical skin/retargeting and verified runtime timing are not supplied. A private data-package Build ran; no recomp compilation, installation, game, runtime attachment or disc export ran. Full SDK goal remains active.
