# Saved normal Build history

Choose **Build history** to review packages saved in the current project's
`Builds` directory, including after closing and reopening the editor. No game
or runtime connection is required.

A successful normal Build now writes `build-receipt.json` after packing and
checking its package. The receipt records the authored-input identity, source
disc hash, audit/manifest/archive hashes, package identity and byte length.
It contains no extracted payloads or gameplay acceptance claim. Identical
inputs produce the same receipt and package; filesystem timestamps are not
used as build identity. Build directory/version identity combines audit bytes
and the authored-input key, so distinct input snapshots can retain separate
receipts even when their serialized changes are identical.

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
