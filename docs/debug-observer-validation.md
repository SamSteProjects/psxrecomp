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
