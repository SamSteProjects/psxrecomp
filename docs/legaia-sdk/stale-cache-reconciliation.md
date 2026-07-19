# Stale-cache runtime fix reconciliation

Date: 2026-07-18

This note records the read-only branch audit performed before changing runtime
or debug-protocol code on `legaia-sdk-integration`.

## Baseline and branch inventory

- Current branch: `legaia-sdk-integration`
- Audited HEAD: `788eedfc61cc4f7a597a6c2e861edbe85fb05e77`
- Relevant source branch: `codex/legaia-recompile-fixes`
- Source branch HEAD: `7ead3a0`
- Merge base: `3ebddf408b28bdbea425ac86be584f52a708ce29`
- Divergence at audit time: 18 commits only on `legaia-sdk-integration`; 9
  commits only on `codex/legaia-recompile-fixes`
- The matching remote-tracking branch is
  `origin/codex/legaia-recompile-fixes`.

The source branch contains broad overlay-runtime and Legaia experiments. It
must not be merged wholesale into the SDK branch.

## Identified source fix

The stale static-overlay cache fix is commit
`bb2ec29ef6a6e8ef9aca73c5d2915a7c7e289fe3` (`Fix Legaia overlay cache and
add debug tooling`) on `codex/legaia-recompile-fixes`.

The complete source commit changes these files:

- `recompiler/src/full_function_emitter.cpp`
- `runtime/include/crash_trace.h`
- `runtime/runtime.cmake`
- `runtime/src/crash_trace.c`
- `runtime/src/debug_server.c`
- `runtime/src/main.cpp`
- `runtime/src/overlay_loader.c`

Only the seven-line `runtime/src/overlay_loader.c` change is the stale-cache
correction. The remainder is unrelated debug tooling and Legaia behavior, so a
whole-commit cherry-pick would violate the scoped-integration policy.

### Original failure mode

`psx_overlay_static_code_matches` cached a successful CRC verdict using the
watched-page generation sum, but it did not first register the static variant's
source pages with `overlay_watch_set_range`. An overlay loaded by CD, DMA, or
ordinary guest stores could therefore replace code at the same guest address
and length while the generation sum remained zero. Dispatch could continue to
accept the cached native/static variant for the old bytes.

The source fix registers every validated static code range before reading its
generation sum. Subsequent writes advance the existing authoritative page
generation and force the CRC verdict to be recomputed. Unchanged bytes retain
the cached verdict.

This is a generic PSXRecomp runtime correctness fix. It is not keyed to Legend
of Legaia, SCUS-94254, a debugger write path, or a particular overlay address.

## Classification of related history

| Commit | Classification on `legaia-sdk-integration` | Reason |
| --- | --- | --- |
| `478e235` | Superseded architecture, historical evidence present | Earlier eager registration-lifetime invalidation is in ancestry; the current runtime uses lazy generation-gated validation. |
| `7793bf5` | Already present exactly | Supplies the generic watched-page generation mechanism used by dynamic candidates. |
| `b39387e` | Already present exactly, incomplete for static variants | Adds exact native/static dispatch and the static CRC cache, but omits static page registration. |
| `bb2ec29` | Missing and still applicable | Adds the omitted registration before the static cache reads generation state. |
| `9bd056a`, `4d50c22` | Already present | Fail-closed native-entry guards are separate dispatch safety checks. |
| `1f6713b`, `1010c58`, `966902f` | Already present | Content/codegen, build-flavor, and namespace cache identities prevent incompatible compiled-object reuse, but do not replace live-RAM invalidation. |
| `29d6acf` | Unrelated prerequisite | Guards later index traversal during overlay shutdown; it does not address stale source bytes. |
| `5b7e69b` | Unsafe and unnecessary to integrate here | Removes the SLJIT tier as part of a much broader overlay architecture change. |

## Integration decision and evidence

Reimplement the single `overlay_loader.c` hunk from `bb2ec29` with attribution,
rather than cherry-picking the mixed-purpose commit. Preserve the existing
page-generation authority in `runtime/src/memory.c`; do not add a second
generation system.

Evidence supporting the decision:

- `git log -S overlay_watch_set_range` identifies `bb2ec29` as the only commit
  that registers static match ranges.
- Current dynamic candidate registration already watches all executable source
  ranges.
- Current static matching reads `overlay_watch_pagegen_sum` without registering
  those ranges.
- `overlay_watch_set_range` and the ordinary memory-write paths share the
  generic watched-page bitmap and monotonic generation counters.
- The source commit contains no regression test for this exact static-cache
  failure, so a synthetic behavioral regression must be added separately.

Future `executable_regions` protocol reporting should expose this same live
registration/generation truth. It must distinguish immutable compiled-source
identity from hashes of current guest RAM and must never preserve native
ownership after these generations invalidate a registration.
