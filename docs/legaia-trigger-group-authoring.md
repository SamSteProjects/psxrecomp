# Trigger cell group authoring

## Atomic trigger group authoring - 2026-10-04

The registered trigger Inspector now offers Move trigger cell group for existing
primary kind-0/1 source rows. Select1..128 cells and review an integer X/Z tile
offset from their Current coordinates, or return just those cells to Retail.
Retail/Current/Proposed coordinates and a source-byte audit appear before Apply.
Changing the selection or offset withdraws Apply, including late pending replies.
Closing aborts requests. The backend requalifies source and project identity and
publishes one ordinary TriggerCells history step. Unselected cell edits and other
components remain retained; payloads, row count and table order stay source-owned.
Out-of-range results reject the whole group. No rows, height or trigger semantics
are invented. New routes: /api/trigger-group-review and /api/trigger-group-apply.

11 focused Python checks passed with the private disc and no skips. Real vell HTTP
Apply, stale rejection, Save/Open and normal Build/ZIP readback composed two moved
cells with an existing script-binding edit: exactly the expected five bytes changed
and every gate byte was retained. Synthetic checks covered unselected edits, Undo,
Redo, Retail reset, no-op history and atomic bounds/source rejection. Focused new
and existing JavaScript checks passed for source/layer/offset/audit validation,
retained cells, busy controls, changed drafts and closed pending replies.

Fresh native browser acceptance passed for two-cell Review, draft invalidation,
one Apply and one Retail reset, unchanged SDK selection and retained script binding,
two Undo steps and zero page errors. Desktop and540px screenshots were inspected;
checkbox alignment was corrected and the workflow rerun. An earlier harness matched
the action in both sidebar and asset dialog; the accepted check scopes the dialog.
Evidence: `local-output/sdk-20260909/trigger-group-20261004/final/proof.json`.
No game launched or installed output changed. First-match shadowing, activation,
contact/height and script execution still require gameplay verification; the full
SDK goal remains active and solo.

Review request:
```json
{"scene_id":"scene://vell","trigger_ids":["trigger://vell/field-map/primary/kind-0/0000"],"delta":{"x":1,"z":0},"action":"translate"}
```

Apply uses exactly type `apply_trigger_group`, scene_id, trigger_ids, delta, action
and the returned review_key. Retail reset uses action `retail` with zero offsets.
Review is read-only. Its proposed MAP hash/audit covers the TriggerCells component;
normal Build separately composes the other authored components and validates the
combined output. The editor accepts only source-qualified rows from the current
catalog and exposes no runtime writes.
