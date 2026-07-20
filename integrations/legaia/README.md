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
- independent, read-only `town01` ISO/PROT/CDNAME/MAN metadata importer;
- deterministic actor identities, source claims, imported X/Z transforms and model pool/index references;
- synthetic unit coverage and an opt-in `LEGAIA_DISC_BIN` integration test;
- pinned interpretation/attribution manifest and metadata JSON schema.
- local-first Legaia Trace inspection surface for importer JSON, with actor search, X/Z projection, source spans and claim evidence;
- synthetic-only inspector preview and tests proving there are no upload, persistence, runtime-write or authoring paths.
- completed real-disc acceptance for the supported North American build: 52 deterministic `town01` actor records, schema/privacy validation, Legaia Trace consumption and full structural parity with Andrew's pinned parser. See `docs/legaia-sdk/town01-acceptance.md`.
- completed additive model-identity resolution: 114 scene-local and five global-special metadata-only model records, 52/52 resolved actor references, bounded source provenance and 119/119 structural parity rows. See `docs/legaia-sdk/model-asset-identity.md`.
- completed the first read-only SCUS-94254 field-runtime layout research pass: revisioned metadata-only profile/schema, multi-signal `town01` identity, observer-owned scene epochs, linked-node/collision-census distinction, bounded actor-field map, correlation-signal inventory and synthetic fail-closed validation. See `docs/legaia-sdk/runtime-layout-research.md`.
- completed generic observer foundations through protocol 1.4: safe runtime/executable identities, authoritative watched-generation reporting, native validity, backend-neutral execution-owner observations, bounded exact-instruction witnesses, frame-stamped `read_regions`, an eight-record executable catalog, and bounded image-lifecycle pages. These changes are generic and contain no Legaia addresses or traversal logic.
- accepted a three-witness field execution identity across fresh launches and natural field-scene replacements. This does not claim a canonical whole-overlay image. See `docs/legaia-sdk/field-execution-identity.md`.

Not implemented:

- no authored/editor UI, asset viewport or transform controls;
- no geometry, script, dialogue or authored scene import;
- no live runtime observer or imported-to-runtime actor correlation;
- no Legaia-specific TCP commands or runtime hooks;
- no RAM writes, live reload or overrides;
- no dialogue editing, asset authoring or disc export.

## Proprietary data

Users must supply their own disc. Do not commit or distribute BIOS/game executable bytes, discs/sectors, extracted assets/dialogue, overlay captures, generated proprietary game code or runtime dumps containing game data. Disc-dependent tests must use `LEGAIA_DISC_BIN` and skip when it is unset. Before implementing any extraction/cache workflow, add explicit ignore rules for all local user-data, runtime and generated paths and verify them with `git check-ignore` plus a metadata-only repository scan.

PSXRecomp is under PolyForm Noncommercial 1.0.0; legend-of-legaia-re declares `MIT OR Unlicense`. Keep attribution and license boundaries intact and do not assume commercial redistribution rights.

## Smallest proof of concept

The first proof is now a headless, read-only import of Rim Elm (`town01`) from a user disc. The independently implemented PSXRecomp-side path resolves ISO9660, PROT/CDNAME, the MAN-bearing scene bundle, actor placements and structural scene/global model pools, then emits deterministic metadata with stable actor/model IDs and evidence-backed claims. It does not emit geometry, decode scripts or require Legaia RE at runtime.

Run it with `python integrations/legaia/tools/legaia_import.py --disc "C:\path\to\Legend of Legaia.bin" --scene town01 --output "C:\local-output\imported-town01.json"`. See `docs/legaia-sdk/town01-importer.md` for the schema, confidence model, tests, attribution and data-handling rules.

The read-only scene/actor inspection surface is implemented under `integrations/legaia/inspector`; see `docs/legaia-sdk/town01-inspector.md`. The revisioned profile under `integrations/legaia/layouts` now selects the supported field runtime through three execution witnesses plus scene and boundary signals, without requiring a guessed whole-overlay range. A separately approved headless read-only observer is now the next safe phase. RAM writes, actor correlation and generic runtime title checks remain out of scope.

See `docs/legaia-sdk/` for the complete audit.
