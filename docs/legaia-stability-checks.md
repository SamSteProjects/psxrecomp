# Fresh SDK Stability Checks

Diagnostics → **Run Fresh SDK Stability Checks…** executes three fixed groups:

- **Restore Ownership:** the real overlay loader with a synthetic library, checking restore entry and continuation.
- **Host Audio Reporting:** production output-health and pump-statistics fragments with synthetic host devices, including unavailable paths and lock ownership.
- **Precompile Inventory and Multi-Config Builds:** the production overlay generator and CMake staging logic, checking numeric part discovery, preserved neighbors, changed inventory/body and Release/Debug incremental builds.

These checks compile and execute small synthetic fixtures. They do not launch the game, attach to a runtime, modify a project, build a playable game or prove gameplay/release equivalence. The existing **Check SDK stability sources…** comparison remains a separate historical hash diagnostic.

The service snapshots fixed source/fixture files plus all runtime `.h` headers into a temporary private tree. Its downloadable JSON receipt includes every copied file's SHA-256 and size, resolved Python/compiler/CMake/Ninja paths and executable hashes, timestamps, per-group status/exit code/output, and the final source comparison. A pass requires all three groups to pass without skipped cases and the current source inventory to match the snapshot. Changed sources receive `source_changed`, not a current-source pass. Tool hashes describe the executables at job creation; system libraries and the host toolchain environment are not a hermetic toolchain proof.

Only one job can run per editor server. The start endpoint accepts an empty JSON object; no client-supplied commands, tool paths, source roots or project paths are accepted. Jobs run asynchronously, so the editor remains available. Each group has a 180-second deadline and 256 KiB output bound. Cancellation requires the exact current job ID and terminates the owned fixture/compiler process tree. Closing the dialog stops UI polling; it does not cancel the job. Reopening shows the same server's latest receipt. Server shutdown requests cancellation. Restarting the server clears its in-memory receipt, so save a receipt to retain it.

The source snapshot is intentionally limited to the dependencies of these three groups. This is not a broad runtime regression campaign. Normal audio playback, startup overflow, controller input, FMV, battle behavior, field coordinate parity and repeated cross-scene savestate performance still require their appropriate runtime/gameplay evidence.

## Verification — 2026-10-08

Evidence: `local-output/sdk-20260909/stability-checks-20261008/qualified/`; preceding attempts are retained in the parent directory. The first sandbox execution passed restore/audio but could not execute the installed Ninja through CMake; its failed receipt is retained. A fresh execution with tool access passed all three groups. The actual editor/HTTP workflow passed fresh execution, argument refusal, JSON download equality, explicit cancellation, wide/400 px layout and zero page errors. Source inventory contained 140 files; document/history/imports/dirty state stayed unchanged and helpers closed. Eight focused Python service/source diagnostic checks, two Node suites, two JavaScript syntax checks and three Python AST checks passed. Windows termination refusal is reported as failure, never clean cancellation; unexpected worker failures also withdraw running fixture states. No game, runtime attachment, install or disc export ran. Full SDK goal remains active; solo development and deferred gameplay verification continue.
