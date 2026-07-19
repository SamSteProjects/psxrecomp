# Native runtime launch acceptance

Acceptance date: 2026-07-19. Branch: `legaia-sdk-integration`. Startup fix:
`0576b58`. Regression guard: `65412fd`.

## Result

The fresh MSVC `RelWithDebInfo` runtime now starts reliably, reaches `main`,
loads the configured BIOS and SCUS-94254 disc, opens TCP port 4370, answers
protocol 1.1, remains responsive after queries, and exits with status zero after
the existing `quit` command is submitted. The runtime-launch gate passed.

The later field-overlay identity gate did not pass. No profile identity was
changed; see `docs/legaia-sdk/field-overlay-0897-identity.md`.

## Failure evidence and correction

The original PDB-bearing build exited before the first diagnostic marker with
Windows status `0xC0000409`. Windows Error Reporting classified it as `BEX64`
in `ucrtbase.dll` at offset `0x11858`, with fail-fast subcode `5`
(`FAST_FAIL_INVALID_ARG`). The archived WER report contained metadata but no
retained dump, so it did not provide a complete native stack.

The first operation in `main` was `setvbuf(stdout, nullptr, _IOLBF, 0)`. A
separate MSVC `/Zi /Od` reproducer containing only that call exited with the
same status and subcode. This identifies the failing source call formerly at
`runtime/src/main.cpp:2813`; it was before game loading and before debug-server
initialization. Windows now uses `_IONBF`, which preserves immediate startup
diagnostics without invoking the UCRT invalid-parameter path. Other platforms
retain line buffering. No security check was disabled and no exception was
swallowed.

## Build-workaround audit

The desktop environment exposes both `Path` and `PATH`. Each configure/build
was run in a child environment that removed every case-insensitive path key and
added one canonical `Path`; no persistent environment was changed.

- `NOMINMAX` is now a target-scoped MSVC definition.
- `/experimental:c11atomics` is now a target-scoped MSVC option. A
  `COMPILE_LANGUAGE` expression was tested and rejected because the Visual
  Studio generator omitted it; the option is accepted by both MSVC front ends.
- `g_idle_skip_enabled` now uses the existing `psx_cycles.h` C-linkage
  declaration. The `/alternatename` linker alias is no longer needed.
- The existing `/STACK:67108864,67108864` target setting was retained. PE
  inspection confirmed a 64 MiB reserve and commit; it did not cause this
  failure. No command-line stack override was used in the accepted build.
- Existing `/GS-`, `/guard:cf-`, and `/GUARD:NO` settings predate this pass and
  were not changed or used to mask the failure.

The accepted build used no `CL` or `LINK` environment override:

```text
cmake -S <local-game-project> -B <local-game-build>
cmake --build <local-game-build> --config RelWithDebInfo --target psx-runtime -- /m:2 /p:BuildProjectReferences=false
```

The launch was:

```text
LegaiaRecomp.exe --game <local-game-config> --headless --no-launcher --debug-port 4370
```

The local executable timestamp, SHA-256, PDB, stdout, stderr, and WER metadata
were inspected but are not committed. No BIOS, disc, executable, dump, PDB, or
absolute user path is stored here.

## Live protocol observations

The fresh native runtime reported `psxrecomp-debug` 1.1 and the sorted native
capabilities `executable_regions`, `read_ram`, `read_regions`,
`runtime_identity`, and `watched_page_generation`. The SCUS serial, BIOS
identity, and main executable source identity were present and stable after
excluding expected request ID and frame changes. Responses exposed no host
paths or executable bytes.

Five two-region reads preserved request order and returned stable frame and
executable-state boundary stamps. Invalid RAM, overflow, per-region limit, and
aggregate-limit requests failed closed. Approximate local latencies were:

| Command | Minimum | Average | Maximum |
|---|---:|---:|---:|
| `protocol_info` | 1.35 ms | 1.84 ms | 2.10 ms |
| `runtime_identity` | 0.52 ms | 1.56 ms | 2.10 ms |
| `executable_regions` (main only) | 2.92 ms | 3.72 ms | 5.15 ms |
| small `read_regions` | 0.42 ms | 1.76 ms | 2.21 ms |

Frame progression continued during the low-frequency sample. Port readiness
was observed in under one second on the final run, although an earlier query
during boot was boundedly dropped before the emulation thread was ready. A
future observer should retry negotiation with backoff.

The I/O thread can return `emu busy or frozen` for `quit` before the main thread
consumes the queued request. In every acceptance run the request was later
consumed and the process exited with status zero. This response/consumption
distinction remains an observability issue; it did not require force termination.

Use identity negotiation once, small `read_regions` polling at no more than
10 Hz, and `executable_regions` only at startup or transition suspicion. Do not
poll full live hashes at frame rate.

