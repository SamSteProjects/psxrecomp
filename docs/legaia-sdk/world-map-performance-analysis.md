# World-map performance analysis

Status: reproducible read-only A/B harness implemented. No claim that missing static MAPDSIP coverage is the slowdown cause is made here.

## Current path and known limits

`map01` is identified by the active-scene signal at `0x80084548`. The existing field profile's `town0c` witnesses are not reused to label map01 code: that would be a false executable-ownership claim. The runtime's existing execution diagnostics classify static-native, cached-native, runtime-native, and dirty-RAM interpreter ownership; exact execution witnesses intentionally cover only single fetched instructions, not invented function or decoded-block ranges.

The checked-in integration has no authoritative, complete MAPDSIP image identity, no checked-in MAPDSIP static registration manifest, and no tracked generated MAPDSIP code. The local Legaia build metadata explicitly generates static captures only for PROT entries 0897, 0898, 0899, 0900, 0967, 0970, 0971, 0972, 0975, 0976, and 0980; MAPDSIP is not among them. Therefore the exact MAPDSIP grouping, all fragments, and static coverage cannot be promoted from inference. Existing world-map handler seeds are evidence of individual reachable entry points, not proof of a complete overlay. The generic interpreter fallback remains the correctness path.

Dynamic overlay caching remains **disabled**. It was disabled after stale same-address replacement failures; it is not a harmless performance switch. Enabling it is deferred unless generation invalidation, live image identity, same-address replacement regression coverage, and a separately reviewed opt-in A/B all demonstrate correctness and benefit.

## Harness

`integrations/legaia/tools/legaia_benchmark.py` uses only pre-existing read-only protocol requests. The title-owned target file `integrations/legaia/benchmarks/scus94254-na-world-map-v1.json` supplies the scene signal definitions; generic code contains no Legaia addresses.

The harness records process/runtime/executable identity, configuration, verified target signals, warm-up and measurement wall time, emulated-frame delta, effective FPS, derived mean frame time, variance across repetitions, observer request count, dispatch deltas, interpreter block/instruction deltas, overlay lifecycle/counter deltas, generation-validation counters, and sampled backend wall-time shares. It deliberately omits raw RAM, code bytes, paths, and per-instruction traces. Runtime counters are process-scoped monotonic counters compared as start/end deltas; the harness does not reset or alter the runtime. CPU utilisation is reported unavailable unless an external, independently approved collector is added.

Suggested equivalent cases, each from a fresh process where practical and each using normal retail debug-menu navigation:

```powershell
# settled town control, server available but no observer polling
python integrations/legaia/tools/legaia_benchmark.py --case-id town0c-idle --target town0c-field-control --poll-hz 0 --warmup-seconds 5 --measurement-seconds 15 --repetitions 3 --output <metadata-output>

# settled map01, server available but no observer polling
python integrations/legaia/tools/legaia_benchmark.py --case-id map01-idle --target map01-world-map --poll-hz 0 --warmup-seconds 5 --measurement-seconds 15 --repetitions 3 --output <metadata-output>

# identical map01 state with a bounded 2 Hz scene observer
python integrations/legaia/tools/legaia_benchmark.py --case-id map01-poll2hz --target map01-world-map --poll-hz 2 --warmup-seconds 5 --measurement-seconds 15 --repetitions 3 --output <metadata-output>
```

The normal retail debug menu may be used to warp; debugger RAM writes, save-state injection, cache toggles, and input injection are not benchmark navigation methods.

## Hypotheses and required evidence

| Hypothesis | Evidence the harness supplies | Current status |
|---|---|---|
| Interpreter execution volume | dirty-RAM blocks/instructions plus phase share | unmeasured live |
| Repeated decode cost | block/instruction deltas and native handoffs | unmeasured live |
| Repeated overlay replacement | lifecycle-event, load, invalidation, revalidation deltas | unmeasured live |
| Missing runtime-native/static coverage | native/interpreter dispatch and phase distribution | unmeasured live |
| Native registration mismatch | static variant/address misses and stale-blocked counters | unmeasured live |
| CD/XA contribution | existing CD/XA diagnostics may be sampled separately; no causal claim here | unmeasured live |
| GPU/presentation contribution | headless/presented comparison is a separately launched, state-equivalent case | unmeasured live |
| Protocol overhead | idle versus 2 Hz polling comparison | harness-ready |
| Frame pacing | emulated frames versus wall time | harness-ready |

The current implementation was synthetically exercised with both target states, idle and 2 Hz polling, repeated aggregation, failed target rejection, bounded counter deltas, and privacy checks. A live benchmark result must be produced only while the verified target is stable; no synthetic result is presented as a retail performance measurement.

The fresh runtime probe used for this change remained in the normal boot/menu
state. It was deliberately not navigated by injection or RAM modification, so it
produced no live town0c or map01 benchmark sample. The table above consequently
remains unmeasured live.
