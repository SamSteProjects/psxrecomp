# Debug observer prerequisite validation

Validation date: 2026-07-18. Branch: `legaia-sdk-integration`.

## Build environment

The desktop process contains duplicate case variants of `Path`. Enumerating the
PowerShell environment provider fails with a duplicate-key exception. Builds
were launched through a child process that created a new environment without
any case-insensitive `path` key and then supplied one canonical `Path` value.
The user's persistent environment was not changed.

The existing MSVC game build also required command-scoped workarounds for
pre-existing build issues:

- `/DNOMINMAX` for Windows header macro collisions;
- `/experimental:c11atomics` for the existing C atomics source;
- `/alternatename:?g_idle_skip_enabled@@3HA=g_idle_skip_enabled` for an existing
  C/C++ linkage mismatch;
- `/STACK:67108864` because the existing GCC-style MSVC stack option is ignored.

These flags were local build inputs only. None is part of the protocol changes.
The stale `psxrecomp-game` emitter binary was rebuilt first and its codegen hash
then matched the runtime tree.

## Results

- Every changed native C/C++ translation unit compiled with MSVC, including
  `debug_server.c`, `memory.c`, `overlay_loader.c`, and `sha256.c`.
- `beetle_debug_server.c` compiled independently with MSVC.
- A fresh local game runtime linked after the command-scoped workarounds.
- The DuckStation oracle patch was regenerated against pinned upstream
  `ffb33c281d196eb8ee0f559085ca285de7cdd51b` and reverse-applies cleanly.
- 44 synthetic observer-protocol tests passed.
- 21 revisioned Legaia layout-profile tests passed, including required-capability
  and protocol-major fail-closed checks.
- The static-overlay cache, overlay-init guard, decodable fallback, overlay
  codegen guard, CPS startup, and SHA-256 vector regressions passed.

Fresh live wire acceptance did not complete. The freshly linked local game
runtime exited with Windows status `0xC0000409` before port 4370 became
available, without producing a new crash report. This is separate from the
protocol compilation and synthetic results; no `protocol_info`,
`runtime_identity`, `executable_regions`, or live `read_regions` response is
claimed from that process. A BIOS-only runtime target also exposed pre-existing
missing `psx_game_address_in_text` and `psx_game_text_native_ok` link symbols.

No live performance or observer-interference measurement is claimed. The design
therefore retains the conservative 10 Hz polling guidance and existing TCP stall
telemetry requirement until a stable fresh runtime can complete wire acceptance.

`test_reachable_discovery_codegen.py` remains separately failing because an
invalid discovery mode does not fail closed. The freshly rebuilt recompiler was
used, so this is not attributable to a stale executable and was not modified as
part of the protocol work.

## 2026-07-19 live acceptance update

The startup blocker was corrected and a fresh `RelWithDebInfo` native runtime
completed live protocol negotiation, identity queries, bounded reads, and a
normal exit. See `docs/runtime-launch-acceptance.md` for the root cause, build
normalization, tests, and latency measurements.

Field-overlay acceptance remains blocked. Retail use exposed an advertised
128-record executable page that can exceed the 65,536-byte response cap, and
stable town01 samples did not report a source-matching native owner for the
field code. These are recorded in
`docs/legaia-sdk/field-overlay-0897-identity.md`; no layout-profile identity was
changed.

## 2026-07-19 protocol 1.2 catalog update

A fresh `RelWithDebInfo` runtime built from the current work opened port 4370,
negotiated `psxrecomp-debug` 1.2, and reached town01 through normal controller
input. The new catalog retrieved 116 image groups, 116 structural ranges, and
562 registrations with an eight-record hard maximum. Complete traversal took
15, 15, and 71 pages respectively and did not overflow the 65,536-byte response
cap. The catalog token remained stable throughout each traversal.

Ownership tokens changed between pages because writes advanced watched
generations on pages that intersect registered executable ranges. This no
longer invalidates or hides catalog paging: the client reports it separately.
Each individual bounded `read_regions` request retained equal before/after
frame and ownership stamps. Five-request median local latencies were 1.39 ms
for `protocol_info`, 2.00 ms for `runtime_identity`, 2.01 ms for one small
`read_regions`, and 11.12 ms for an eight-image catalog page. A complete
registration traversal took approximately 1.01 seconds and should remain an
epoch/transition diagnostic, not a polling loop.

The expected `0x801CE818` loaded-image base was absent. Current registrations
covering the known field function remained overlapping static structural
variants, not an authoritative overlay image, and none was a current
source-matching owner. Overlay 0897 remains unaccepted and the Legaia profile
remains unchanged.

Final rebuild verification found that the local game build cache had later
been reconfigured to a stale temporary PSXRecomp staging tree; that binary
truthfully reported protocol 1.1 and was rejected. The local game project was
reconfigured with `PSXRECOMP_ROOT` pointing at the current checkout and
`PSXRECOMP_GAME_EXECUTABLE` pointing at the preserved local recompiler, then
rebuilt under the same normalized child environment. The resulting fresh
binary reported protocol 1.2, the six native capabilities, both eight-record
limits, and `load_base: null` for a static structural variant. This correction
changed only the external local build cache, not repository files or user-wide
environment state.

## 2026-07-19 protocol 1.3 lifecycle update

A fresh normalized-environment `RelWithDebInfo` build compiled and linked the
generic lifecycle instrumentation. Native negotiation reported protocol 1.3,
the additive `executable_image_lifecycle` capability, an eight-record lifecycle
page maximum, and 4,096 retained events.

Four normal-flow launches were used while tightening the bounded model. The
accepted repeat reached `town01`, PROT `3`, and mode `3` with stable frame and
executable-state boundaries. Exact-owner queries repeatedly reported
`0x801CF754` as a current dirty-RAM interpreter observation with no native
registration and no image-instance parent. `0x801CE818` had no owner record.
The final bounded tables did not overflow; the event ring explicitly reported
older event history as truncated.

Five end-to-end Python CLI invocations averaged approximately 189 ms for the
one-record owner query and 150 ms for a small `read_regions` request. These
figures include Python process startup and are not wire-only latency; the prior
same-host wire measurements remain representative. Low-frequency queries did
not stop frame progression. Full lifecycle/catalog traversal remains an
epoch-change diagnostic, not a polling operation.
