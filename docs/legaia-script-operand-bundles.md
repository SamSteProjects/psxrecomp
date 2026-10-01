# Scene script operand bundles

In Edit mode, open **Script operand bundles…** in the asset tools. Download
exports the active scene's authored numeric operands across imported actors and
partition-two script owners. Select a bundle JSON file to review each owner's
current and proposed authored fields, then **Apply reviewed bundle** publishes
all changes as one Undo/Redo command. Save/Open preserves the ordinary authored
components. Review and export do not modify authored state.

The bundle uses `legaia.script-operand-bundle.v1` with exact `schema_version`,
`scene_id`, `source_import_sha256`, and `owners` fields. Each owner contains
`owner_id` and `components`, using the existing [single-owner operand file](legaia-script-operand-files.md)
structures. Limits are 64 KiB UTF-8 JSON, 128 unique owners and 256 instruction
entries total. Supported families are movement, flags, waits, model selectors
and transitions, subject to their existing source instruction and numeric bounds.

All owners must belong to the active imported scene and its verified retail
source. Supplied entries replace their complete authored fields; omitted owners,
entries and components remain unchanged. Empty bundles and unchanged proposals
add no history. Bundles do not append instructions, transfer dialogue, clear
omitted entries, transplant owners, or change control-flow layout.

The service stages every owner before publication and compares actual audited
serialized byte writes against all existing numeric edits in the scene. Different
values for a shared byte reject the entire bundle. Explicit no-op fields produce
no writes. This checks byte composition, not runtime behavior or general semantic
compatibility. Apply re-verifies the source and binds to the complete authored
override snapshot; changed files or project overrides invalidate its review key.
The editor also withdraws stale or closed reviews before dispatch.

## Verification — 2026-10-01

Five focused Python checks passed, including duplicate/bounds rejection,
failure on the last owner without partial edits, conflicting byte writes,
one-command persistence/history, no-op and stale-key handling. All 19 Node
test files and 21 editor JavaScript syntax checks passed.

The retail browser checked export, read-only two-owner/four-entry review,
one Apply, Save/Undo/Redo, invalid last-owner rejection, stale withdrawal and
closed pending-response withdrawal. No page errors; baseline restored and
review screenshot inspected. Independent reopen preserved all four NPC drafts.
Detached no-draft normal builds matched all 45338 MAN bytes against the expected
result, changing only offsets 4808, 4811, 4816 and 28557; every other content
payload was unchanged. Package SHA256:
`f5b7bd9f3dc18d154fdffef09ec87205f702111e8d61b3cc9501624ef0f2922c`.

Private evidence is under
`local-output/sdk-20260909/script-operand-bundles-20261001/`.
Normal Build still rejects projects containing drafts; the verification detached
them only in memory. No game launched or disc installed. Gameplay is deferred.
These focused checks postdate the integrated 469-test checkpoint and do not
replace it or establish full SDK completion.
