# Check Recorded SDK Stability Source Inclusion

Open **Diagnostics**, then choose **Check SDK stability sources…**. The SDK
compares eight source/fixture files with the recorded checkpoint, showing each
relative path, expected/current SHA-256 and comparison status. **Refresh source
comparison** repeats those reads; **Save source comparison…** downloads the
complete metadata receipt and its check time.

The checkpoint covers five runtime/precompile files and three fixture sources:
host runtime/audio readiness and locked statistics, overlay restore ownership,
static-overlay discovery/staging and the associated focused regressions. Exact
paths and hashes are declared in the
[source manifest](../integrations/legaia/sdk/stability_sources_manifest.json).
Its basis revision is `6f51eaaeee47b305bc4e12b8c7a892be90043348`; recorded execution
evidence remains dated 2026-10-04. Release reference
`3ac7d410bf3da25f64a1e013ff8a99f7d3c694fa` is historical, not a newly observed
sibling checkout HEAD.

Reports classify matched, changed, missing, unreadable, unsafe, oversized or
unstable source reads. Relative paths and unique identities are validated;
resolved paths must remain inside the SDK checkout, and source reads are bounded
to 2 MiB. A missing/invalid manifest yields an unavailable report rather than a
passing comparison. No caller-supplied filesystem path is accepted by the GET
endpoint `/api/sdk-stability-sources`.

This is source inclusion only. The receipt explicitly sets test execution,
runtime binary verification and gameplay verification false. Matching hashes
do not prove compiler behavior, cold startup, FMV, audio quality, field restore
performance or complete release equivalence. The source audit does not launch
the game, rebuild it or modify a project. Legitimate source drift needs fresh
qualification and a corresponding ledger/manifest update; replacing expected
hashes alone is not new execution evidence.

The dialog owns its requests and bounded receipt. Closing, Escape or parent
disposal aborts synchronously; late responses cannot publish. A changed diagnostic
project context clears rows and withdraws Refresh/download. Saved receipts are
timestamped observations; source changes after that check require Refresh.

## Offline Checks Passed — 2026-10-07

Three Python tests passed actual eight-file inclusion and synthetic drift,
missing/oversized reads and invalid/duplicate manifest paths/identities. Node
checks passed report scope, hash/status/summary consistency, unavailable states,
detached data and refusal of fabricated execution/binary/gameplay claims. Both
changed JavaScript modules passed syntax checks; server/audit AST and whitespace
checks passed.

Actual private Town01 Diagnostics checks passed eight matching rows, Refresh,
receipt download and independent SHA-256 readback of every file. The 400 px
screenshot was inspected. Additional browser checks passed synchronous close
abort, ignored late completion and stale-context withdrawal. Project document,
history and file snapshots stayed unchanged; no page errors or authoring/Build/
Run requests occurred, and owned helpers terminated.

Private evidence:
`local-output/sdk-20260909/stability-source-diagnostic-20261007/qualified/`.
Earlier attempts retain an initialization timing assumption and the queued-close
abort issue corrected by synchronous disposal. No runtime fixture execution,
native Build, game, attachment, installation or disc export occurred. The full
SDK goal remains active and gameplay acceptance remains deferred.

Fresh execution is now available separately through [Fresh SDK Stability Checks](legaia-stability-checks.md). This historical comparison remains source inclusion only.
