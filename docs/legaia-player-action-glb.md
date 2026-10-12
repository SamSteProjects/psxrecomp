# PLAYER Action GLB Import

In progress — 2026-10-11. This workflow is under construction. The native converter is implemented and checked; editor Review/Proposed/Apply, retained GLB inputs and full persistence/Build integration are not yet delivered.

## Native Conversion

`importer/player_animation_glb.py::import_player_action_glb` consumes an exact Current PLAYER file hash, existing action identity/hash, selected equipment, an embedded GLB and explicit 1..120 Interchange FPS. The shared bounded glTF parser, rigid hierarchy sampler and STEP/LINEAR tracks supply scene-space poses at float32 native-frame-index/FPS times. The source frame/part counts remain fixed, endpoints hold, and no action allocation or runtime timing evidence is inferred.

Fresh native assembly owns the object-to-part mapping. Every native part must be represented. Equipment attachment objects that alias a body part must agree in sampled translation and orientation; conflicting tracks refuse instead of overwriting one another. The importer uses one Y reflection and source-biased Rz*Ry*Rx Euler quantization at full twelve-bit precision, with a 0.15-degree angular bound. Signed translations reject raw overflow before rounding. Existing field/World rotation precision stays at sixteen PSX units by default.

The normal PLAYER native channel codec applies sparse edits and enforces compressed record0 capacity. Headers, descriptor tables, model pools, other action bytes and unused allocation suffix remain protected. No-op imports keep the complete original compressed physical file. Meshes and textures do not author native model pools through this converter; skin/morph channels remain unsupported.

## Focused Evidence

All 38 supported retail actions across four source files and 605 frames round-trip through GLB with exact original file bytes. All 1210 attachment/body alias samples agree. Four modified imports preserve signed translation and non-multiple-of-sixteen native rotation values, with unchanged unselected decoded action bytes and protected physical ranges. Four attachment-only conflicts refuse. Invalid boolean/string/nonfinite/out-of-range rates reject. Full-precision source equivalence and gimbal-neighborhood checks pass alongside thirteen existing shared animation/clip checks.

Private evidence: `local-output/sdk-20260909/player-native-model-authoring-20261011/glb-action-import-proof.json`. Tests: `test_player_animation_glb.py`, `test_animation_glb.py`, `test_animation_clip_export.py`. Proprietary source data and derived files stay private.

## Remaining Workflow

Integrate fresh Current inspection and model/action ownership with a source-bound GLB review receipt, proposed playback, exact Apply seal, retained immutable GLB inputs, normal history and Save/Open, then verify Current and composed package Build. Authoring remains incomplete until those editor steps are implemented and checked. Native cadence/activation and playable behavior require later gameplay verification.

No Build, recomp compilation, install, game or attachment ran. Full SDK goal remains active.
