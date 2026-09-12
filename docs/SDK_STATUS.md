# Legaia SDK status — 2026-09-12

The SDK is functional for supported offline authoring workflows, but the full editor and runtime parity objective is incomplete. Gameplay verification is deferred at the user's request. No new game launch is needed to review the work below.

## Ready for offline review

- Scene workspace: source-based textured scenes, hierarchy selection, inspector, orthographic/top views, coordinate locator, authored/retail layers, and actor/decorative/shared-scenery X/Z handles. Shared scenery browser checks moved three instances while preserving366 unrelated instances and verified Undo on both axes.
- Script movement: verified MOVE_TO/NPC_RUN X/Z authoring, source/effective values, history and persistence, viewport targets with source-instruction navigation, and descriptor/streaming experimental output composition. Y, executed branches and actor identity remain unknown where evidence does not establish them.
- Animation: supported rigid clips can be previewed and exported. Channel edits and same-object retail/effective copy between frames use Apply/Undo/Discard. Browser checks cover late responses, invalid selections and cross-object rejection. Shared clip users are explicitly listed.
- Model shapes: existing-layout TMD and ordered-vertex OBJ replacements preserve source primitive/material data. Equivalent oriented face order and relative indices passed exact roundtrip and isolated vertex edits on119 town01 models. A saved OBJ project passed Undo/Redo, reopen and package build.
- Output: supported edits compose into private packages or experimental disc exports. Input snapshots, hashes and reopened archive checks support later review. Package descriptions list emitted edit families; output collisions are rejected instead of silently replacing existing builds.

## Validation scope

The last complete SDK discovery run passed344 tests in140.705 seconds at the earlier regression checkpoint. Later features have focused service, browser, source-byte and package checks; that full-suite result must not be represented as a test of every later change. Runtime and external Blender/Unity animated playback acceptance are separate.

Recent private evidence lives under `local-output/sdk-20260909/`, including `sdk-suite-recheck-20260912.log`, `shared-scenery-multiple-check.json`, `shared-scenery-multiple-z-check.json`, `obj-equivalent-retail-20260912/report.json`, `animation-channel-copy-check.json`, `animation-effective-copy-check.json`, and `animation-copy-request-order-check.json`. These files are local evidence, not redistributable fixtures.

## Deferred gameplay

Use [the verification queue](legaia-gameplay-verification-queue.md) for saved input projects, exact artifacts and manual checks. NPC append/spawn behavior, script execution, animation playback, modified collision and visual behavior require their stated checks. Successful serialization does not establish gameplay acceptance. The user's wall-gap confirmation is bounded to that prior edit.

## Major unfinished work

- Arbitrary model topology/material replacement, general animation import and retargeting.
- Complete script/control-flow authoring, unknown records and scheduling behavior.
- Confirmed runtime actor identity and complete Unity-style live scene parity.
- Complete world-map behavior and unresolved MAPDSIP coverage.
- Remaining release/runtime acceptance, including the latest audio-lock build and deferred lifecycle/performance checks.
- Independent rendered acceptance of complete exported animations and wider scene parity.

See [feature coverage](FEATURE_MATRIX.md), [release parity](legaia-release-parity.md), [architecture](ARCHITECTURE.md), and [test plan](TEST_PLAN.md). The goal remains active; this report does not claim all offline work is exhausted.
