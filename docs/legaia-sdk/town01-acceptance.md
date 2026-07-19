# `town01` retail-disc acceptance

## Decision

**Accepted** for deterministic, metadata-only import of `town01` actor placements from the supported North American disc build. The real-disc integration test ran without skipping, two imports were byte-identical, the output passed schema and privacy review, Legaia Trace consumed the real output, and all 52 structural actor records agreed with Andrew's pinned parser after one documented representation normalization.

This acceptance does not cover model asset identity, scripts, dialogue, runtime layouts, TCP observation, RAM correlation or writes.

## Acceptance identity

| Item | Value |
|---|---|
| Date | 2026-07-18 |
| PSXRecomp repository | `SamSteProjects/psxrecomp` |
| Branch | `legaia-sdk-integration` |
| Acceptance baseline | `6a5d3ab42db126115585986cfba0aa093b4533d0` |
| Importer | `0.1.0`; implementation/test chain `d8c195e`, `532f4fd`, `81cad32` |
| Andrew reference | `AndrewAltimit/legend-of-legaia-re` at `d6e64c68ede25813d35db20980da82a1a025549b` |
| Disc build | North America, `SCUS-94254`; ISO marker `SCUS_942.54` |
| Image layout | Mode 2/2352, 198,433 sectors, 466,714,416 bytes |
| Whole-image identity | Exact match for the importer's published `SUPPORTED_DISC_SHA256`; the user path is not recorded here |
| Scene | `town01`; extraction-frame PROT range `[1, 10)`; MAN-bearing bundle entry `2` |

## Commands

The disc environment variable was set to the user's local legally obtained image. Its absolute value is intentionally omitted.

```powershell
python -m unittest discover integrations/legaia/tests -v

python integrations/legaia/tools/legaia_import.py `
  --disc $env:LEGAIA_DISC_BIN `
  --scene town01 `
  --output "C:\local-output\legaia-sdk-acceptance-20260718\town01-run1.json"

python integrations/legaia/tools/legaia_import.py `
  --disc $env:LEGAIA_DISC_BIN `
  --scene town01 `
  --output "C:\local-output\legaia-sdk-acceptance-20260718\town01-run2.json"

Get-FileHash -Algorithm SHA256 `
  "C:\local-output\legaia-sdk-acceptance-20260718\town01-run1.json", `
  "C:\local-output\legaia-sdk-acceptance-20260718\town01-run2.json"

cd integrations\legaia\inspector
npm run build
npx wrangler dev -c dist/server/wrangler.json --port 4175
npm test
npm run lint -- --ignore-pattern work
```

Andrew's checkout was verified at the pinned commit and used only as a temporary development oracle. It was not added to this repository or made a runtime dependency.

```powershell
cargo test -p legaia-engine-core `
  --test field_actor_placements_disc `
  man_actor_placements_decode_for_real_scenes `
  -- --exact --nocapture

cargo run -q -p legaia-engine-core --example town01_structural_parity
```

The second command used a temporary metadata-only example around Andrew's public `Scene::field_actor_placements` API. The example and temporary extracted-data junctions were removed after producing the local comparison CSV; Andrew's checkout was clean afterward. The comparison output remains outside PSXRecomp.

Schema validation used Python `jsonschema` against `integrations/legaia/schemas/town01-import.schema.json`; the importer's `validate_metadata_only` validator and an anchored absolute-path/string scan were also run on the real output.

## Test and import results

All 12 Legaia importer tests passed in 0.666 seconds. The exact tests were:

- `test_cdname_scene_resolution`
- `test_claim_serialization_round_trip`
- `test_deterministic_json`
- `test_duplicate_and_contradictory_claims`
- `test_metadata_only_output`
- `test_scene_table_and_lzs_use_synthetic_data`
- `test_stable_semantic_actor_id`
- `test_synthetic_man_actor_records`
- `test_synthetic_prot_table`
- `test_truncated_man_and_invalid_offsets`
- `test_unsupported_scene_and_disc`
- `test_town01_metadata_is_stable_and_bounded`

The last test was the retail-disc gated integration test. It ran and passed; it did not skip.

| Check | Result |
|---|---|
| Actor count | 52 |
| Semantic IDs | 52/52 unique; all matched `scene://town01/actors/man-p1/NNNN` |
| Actor ordering | Ascending MAN partition-1 record order, records 1 through 52 |
| Source bounds | Every `byte_offset + byte_length` remained within the 45,338-byte decoded MAN payload |
| Model references | Pool and index present on all 52 actors |
| Explicit unknowns | Y, rotation/facing and concrete asset-record identity unresolved on all 52 actors |
| Run 1 SHA-256 | `0d8fbe2a6464a149631c517005d1e13eec0c304f1735555866435453ba8133f0` |
| Run 2 SHA-256 | `0d8fbe2a6464a149631c517005d1e13eec0c304f1735555866435453ba8133f0` |
| Byte determinism | Pass; files were byte-identical |
| JSON Schema | Pass for both outputs |
| Metadata-only validator | Pass |
| Absolute local paths | None found |
| Binary/asset payloads | None found; no MAN/TMD/TIM/dialogue/scene/executable/sector bytes or blobs |

No importer output, normalized comparison report, extracted retail data or proprietary bytes were added to Git.

## Confidence distribution

The 52 actors contain 364 claims:

| Confidence | Claims | Share |
|---|---:|---:|
| Confirmed | 260 | 71.43% |
| Unknown | 104 | 28.57% |
| Strongly inferred | 0 | 0% |
| Tentative | 0 | 0% |
| Contradictory | 0 | 0% |

Agreement with another implementation was not used to promote any unknown claim.

## Legaia Trace acceptance

The built inspector loaded `town01-run1.json` through its local file picker using the worker-backed local deployment configuration. It reported the expected scene, 52 actors, supported disc fingerprint and pinned reference commit.

- Search narrowed record `0052` to 1/52 results.
- The Unknown filter showed 52/52 records; Contradictory showed 0/52; All restored 52/52.
- Actor selection updated the selected source entity and showed its structural ID, X/Z, model pool/index, MAN record and decoded span.
- All 52 X/Z projection points rendered with finite percentage coordinates bounded from 10% through 90%; none contained `NaN`, infinity or a missing style coordinate.
- Y, rotation and concrete asset-record identity remained visibly unresolved.
- Source inspection and the inspector tests found no upload/network API, browser-storage API, authoring, save, export, connection or runtime-write path.
- `npm test` passed both inspector tests. Source lint passed with `npm run lint -- --ignore-pattern work`.

The unqualified `npm run lint` also traversed a pre-existing ignored `work/package-stage-v1` deployment artifact and failed on generated bundles. This is not a source lint failure and the artifact was not changed or deleted. A first `npm test` attempt was blocked by a cache lock from the local Wrangler acceptance server; after stopping only the server processes started for this pass, the documented test completed successfully.

On this Windows environment, `vinext start` served the initial HTML but returned 404 for its hashed client module. The worker-backed build (`wrangler dev` with `dist/server/wrangler.json`) served the same built application with its client assets and was the accepted interactive surface.

## Andrew parity

The normalized local report contains one row per MAN partition-1 record and uses the structural record index/source offset. No nearest-position matching or name-derived matching was used.

| Field | Classification | Result |
|---|---|---:|
| Scene identity | Match | 1/1 |
| PROT extraction range `[1, 10)` | Match | 1/1 |
| MAN carrier | Match | Exact actor source offsets and decoded ordering identify the same carrier |
| Actor count | Match | 52/52 |
| Actor ordering | Match | 52/52 |
| MAN record index | Match | 52/52 |
| MAN source offset | Match | 52/52 |
| Local prefix count | Match | 52/52 |
| X position | Match | 52/52 |
| Z position | Match | 52/52 |
| Placement tile X/Z | Match | 52/52 on each axis |
| Model index | Match | 52/52 |
| Animation-record ID | Match | 52/52 |
| Model pool | Representation difference | 52/52 normalized values agree |

The model-pool difference is representational: PSXRecomp emits `scene_tmd` or `global_special`; Andrew exposes `special_model: bool` derived from the same `model_index >= 0xF0` rule. After explicitly normalizing that rule, all 52 values agree. Andrew does not expose PSXRecomp's semantic actor ID or bounded record length in `ActorPlacement`; those are PSXRecomp provenance additions, not contradictions.

No ordering differences, missing actor records or genuine contradictions were found. No importer defect or synthetic regression test was required.

## Recommendation and remaining boundaries

The `town01` importer is accepted for its current metadata-only contract. A separately scoped model-asset-identity pass is now safe to begin because the carrier, record ordering, pool selection and indices have real-disc parity. It must keep concrete asset identity unknown until independently supported and must not export retail assets.

Live-runtime observation remains premature. It still requires a revisioned layout profile, a supported current-scene/epoch signal and an evidence-backed record-to-runtime correlation design. This acceptance does not authorize TCP changes, RAM reads/writes or generic runtime modifications.

The previously reported `test_reachable_discovery_codegen.py` failure against `build-msvc3` was not reproduced in this pass because it did not affect the importer. It remains a separate, pre-existing recompiler/stale-executable issue; no recompiler source or build directory was changed.
