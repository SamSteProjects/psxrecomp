# World-map performance analysis

Status: reproducible read-only A/B harness implemented and accepted live. Missing static MAPDSIP coverage is not, by itself, claimed as the cause.

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
| Interpreter execution volume | dirty-RAM blocks/instructions plus phase share | strongly supported; map01 averaged about 198.2M interpreted instructions per 15 s versus 0.877M in town0c |
| Repeated decode cost | block/instruction deltas and native handoffs | decode cache hit/miss counters unavailable; no native handoffs were observed |
| Repeated overlay replacement | lifecycle-event, load, invalidation, revalidation deltas | not supported during stable intervals; all measured deltas were zero |
| Missing runtime-native/static coverage | native/interpreter dispatch and phase distribution | supported as an execution-mix difference, not yet as a complete MAPDSIP identity claim |
| Native registration mismatch | static variant/address misses and stale-blocked counters | no invalidation or stale-owner activity observed during stable intervals |
| CD/XA contribution | existing CD/XA diagnostics may be sampled separately; no causal claim here | unmeasured live |
| GPU/presentation contribution | headless/presented comparison is a separately launched, state-equivalent case | unmeasured live |
| Protocol overhead | idle versus 2 Hz polling comparison | harness-ready |
| Frame pacing | emulated frames versus wall time | harness-ready |

## Retail A/B result

The accepted run used the same fresh `RelWithDebInfo` build and presented-mode
configuration for every case, with 5 s warm-up, 15 s measurement, three
repetitions, idle controller state, and 2 Hz bounded scene polling. Detailed
metadata stayed outside the repository.

| Case | Mean FPS | Run standard deviation | Observer polls per run |
|---|---:|---:|---:|
| town0c idle | 59.9979 | 0.0012 | 0 |
| town0c polling | 59.9760 | 0.0378 | 30 |
| map01 idle | 59.2657 | 0.2673 | 0 |
| map01 polling | 59.6871 | 0.1018 | 30 |

Town polling differed from idle by -0.0365%. Map polling was +0.7110%, an
ordering/variance result rather than evidence that polling improves execution.
The stable map idle result was 1.2204% below town idle. More importantly, map01
averaged a 79.42% interpreter phase share versus 2.56% in town0c and about 226
times the interpreted instruction volume. Stable intervals recorded no overlay
loads, lifecycle events, invalidations, or revalidations. The evidence therefore
classifies the execution difference as **primarily interpreter execution
volume**. It does not prove which missing MAPDSIP coverage or decode mechanism
would be the correct optimization.

The live run exposed and corrected one harness defect: it requested nonexistent
`overlay_status` instead of the runtime's read-only `overlay_loader_status`.
Regression coverage now requires the real command. Dynamic overlay caching
remains disabled; the next performance investigation should profile broader
static coverage or interpreter/decode optimization without weakening stale-code
correctness.
