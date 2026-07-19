# Legaia SDK integration

This directory is the isolated home for a future Unity-like SDK/editor integration for *Legend of Legaia*. The long-term experience is to import a scene from a user-supplied disc, inspect and author actors/dialogue/triggers/cameras, validate changes against the live recompiled retail engine, and eventually build either a PS1-compatible patch or an extended native project.

## Separation of responsibilities

- **PSXRecomp** remains the low-level execution authority: recompiled original engine code, PS1 memory/hardware, overlays, stepping, instrumentation and native validation.
- **AndrewAltimit/legend-of-legaia-re** remains the independently maintained semantic/clean-room authority: disc and format parsers, scene/actor/script meaning, preview rendering, documentation and supported patching knowledge.
- **This integration** will own stable semantic IDs, provenance, imported/authored/live state separation, runtime correlation, project persistence and editor-facing contracts.

The clean-room repository is not copied here and is not linked into the PSXRecomp runtime. Phase 0 audited its latest `origin/main` commit `d6e64c68ede25813d35db20980da82a1a025549b` through a temporary external checkout. It is a pinned development reference and parity oracle, not a shipped dependency, submodule, required subprocess or second runtime. The SDK importer and project model will live here around the working recompiled engine; live inspection uses PSXRecomp’s existing JSON/TCP debug protocol.

## Why a dedicated branch

Work is isolated on `legaia-sdk-integration` so game-specific discovery cannot destabilize PSXRecomp’s actively debugged MIPS translation, BIOS, timing, hardware or overlay behavior. Any reusable generic protocol improvement must still be independently justified and tested. No Legaia title checks belong in generic runtime/hardware code.

## Current status

Implemented:

- repository and implementation audit;
- ownership/dependency architecture;
- semantic identity and provenance model;
- runtime bridge design and missing-command analysis;
- authored/imported/derived/live/generated project schema;
- read-only vertical-slice and test plan;
- risk register.

Not implemented:

- no PSXRecomp-side Legaia importer;
- no SDK code or editor UI;
- no scene or actor import in this repository;
- no runtime correlation profile;
- no TCP changes;
- no RAM writes, live reload or overrides;
- no dialogue editing, asset authoring or disc export.

## Proprietary data

Users must supply their own disc. Do not commit or distribute BIOS/game executable bytes, discs/sectors, extracted assets/dialogue, overlay captures, generated proprietary game code or runtime dumps containing game data. Disc-dependent tests must use `LEGAIA_DISC_BIN` and skip when it is unset. Before implementing any extraction/cache workflow, add explicit ignore rules for all local user-data, runtime and generated paths and verify them with `git check-ignore` plus a metadata-only repository scan.

PSXRecomp is under PolyForm Noncommercial 1.0.0; legend-of-legaia-re declares `MIT OR Unlicense`. Keep attribution and license boundaries intact and do not assume commercial redistribution rights.

## Smallest proof of concept

The smallest useful proof is a headless, read-only import of Rim Elm (`town01`) from a user disc using the existing Legaia RE path (`ProtIndex`, `Scene::load`, `build_field_scene`, `build_npc_catalog`). It should enumerate geometry and actors, select one NPC, assign a structural semantic ID, show source record/model/imported transform and only evidence-backed movement/interaction/flag/dialogue claims, then optionally compare that actor with a PSXRecomp runtime observation.

The exact next task is the schema plus metadata-only PSXRecomp-side Rim Elm importer spike. It will use Andrew's scene/NPC code and documentation as attributed reference material and a development parity oracle, without making Andrew's repository part of the shipped SDK. Generic runtime/editor changes remain a later boundary.

See `docs/legaia-sdk/` for the complete audit.
