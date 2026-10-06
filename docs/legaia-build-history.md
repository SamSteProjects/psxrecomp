# Saved normal Build history

Choose **Build history** to review packages saved in the current project's
`Builds` directory, including after closing and reopening the editor. No game
or runtime connection is required.

A successful normal Build now writes `build-receipt.json` after packing and
checking its package. The receipt records the authored-input identity, source
disc hash, audit/manifest/archive hashes, package identity and byte length.
It contains no extracted payloads or gameplay acceptance claim. Identical
inputs produce the same receipt and package; filesystem timestamps are not
used as build identity. Build directory/version identity follows serialized
audit bytes. No-op authored overrides therefore retain byte-identical baseline
packages. The first `build-receipt.json` is preserved; each input context also
gets an immutable `input-receipts/<authored-key>.json`. History looks up the exact
current key without scanning nested folders and validates that receipt against
the same package artifact identity. Receipts from the first snapshot-based
identity implementation remain readable; new packages use content identity.

The history list checks receipt structure and its audit hash. Its input match
compares recorded authored metadata to current project inputs. This comparison
includes project root and disc path; copying a project can therefore change it.
It does not recheck either the disc or package files. A receipt is local recorded
provenance, not a signed authenticity certificate or a saved editable project.
No builder source revision is recorded or inferred.

**Verify saved files and open report** independently checks the audit, manifest,
source package payload files, complete archive hash and exact ZIP member inventory,
lengths and payload hashes. Manifest package/disc/overlay identities must match
the receipt and audit. Successful verification opens the saved change report.
This is an integrity observation at verification time, not a claim against later
external file mutation. The original source disc is not read by this operation.
Gameplay remains unverified.

Older or unfinished folders without a completion receipt show input match and
integrity as unavailable. The editor does not fabricate receipts for them.
Rebuild from the intended current project inputs to record a new receipt.
Custom CLI output paths outside the project are not scanned.

The service scans only immediate project `Builds` entries, at most 4096 entries
and 256 matching Build identities, in identity order. Truncated coverage is
explicit; it does not claim these are the newest builds. Symlink/reparse paths
are rejected through the shared output guard. Metadata is limited to eight MiB,
archives/expanded audited payload totals to 512 MiB, individual overlays to
64 MiB, and overlay inventories to 4096 entries. The dialog displays the first
256 audited changes and identifies that limit.

The routes are read-only `POST /api/builds` with `{}` and
`POST /api/builds/verify` with a saved `id` only. Browser requests guard project
context and abort on dialog close. No install, delete, launch or authored-change
action is part of this workflow.

Validation on 2026-10-01: 19 retail-enabled Python checks covering receipt
determinism, reopen/input comparison, read-only verification, payload/manifest/
audit/archive corruption, duplicate ZIP members, legacy/invalid receipts, path/
reparse rejection, bounded scans and existing review/raw/compressed animation
Build behavior. All 24 Node test files and 26 module syntax checks passed.
A fresh server/browser reopened a real nine-change package report with its
24,894-byte overlay, verified files, labeled a retained older Build, and rejected
malformed API requests. Persisted metadata/authored entities stayed unchanged;
no Build, Run or authoring command was dispatched by the history workflow.
The first screenshot exposed clipped columns; the dialog was widened, browser
checks repeated and the final screenshot inspected. Private evidence is under
`local-output/sdk-20260909/build-history-20261001/`; no retail payload is tracked.

This feature postdates the integrated 475-test checkpoint. Full SDK/runtime
completion and the separate manual gameplay queue remain open.

Compatibility correction (2026-10-01): full discovery at `e49e09b0` ran 497
tests with no skips but found four package-equality failures and one stale-source
validation-order error. Those failures were not accepted as a checkpoint. Build
now retains content identity plus separate immutable input receipts, and stale
retail validation occurs before snapshot metadata hashing. All29 focused checks
covering the five failing workflows passed; an additional six-check history set
passed, including exact binding and rejection of conflicting current-input
receipts. Fresh retail-enabled discovery on `ba77695b6e4e86210a2d921e1e5d9935c706e611` subsequently passed all498 tests; all24 Node files and26 syntax checks also passed. Browser verification after the correction retained the nine-change report and explicit incomplete entry, with unchanged authored metadata and no game launch. The corrected wide screenshot was inspected.

## Inspect one asset's emitted Build records

Open an asset's Details and choose **Inspect saved Build records...**. The dialog
lists completed project-local receipts in identity order; this is not a newest-first
claim. Invalid/incomplete entries remain available in the general Build history,
and bounded-scan coverage is explicit. Choose a Build and **Verify saved package**.
Only after the existing SDK verification service checks its receipt, audit,
manifest, payload files and ZIP does the dialog show matching records.

**Exact audit asset ID** means the selected stable ID equals a report row's
`asset_id`. **Include exact audit owner matches** additionally shows rows whose
`owner_id` equals the selected ID, labeled **Exact audit owner ID**. It does not
infer an ownership graph or treat a source script/scene membership as a matching
asset. Toggle owner matching to inspect direct IDs alone. Before/After, scene,
field, scope and full emitted record details retain SDK values. Results have
128-row Previous/Next pages; paging does not truncate the matched inventory or
nested model-coordinate, texture or composition ledgers.

The dialog shows archive/source-disc hashes and whether the saved receipt matches
current authored inputs. Package integrity and current-input match remain separate.
Fresh server inputs are checked after list/verification responses. If project,
source membership, asset record or inputs change, reopen the asset Details.
Changing Build selection withdraws prior records. Closing cancels requests and
removes the dialog; detached paging callbacks cannot alter replacement results.

A missing match means only that the exact ID is not recorded in that audit.
Unchanged native content may not have an edit record, shared IDs retain independent
source memberships, and runtime consumers remain unverified. This is generated
audit evidence, not a native asset preview or gameplay acceptance. The dialog does
not create a Build, author, save a project, install output or launch the game.
Project templates retain their existing project-only workflow.
