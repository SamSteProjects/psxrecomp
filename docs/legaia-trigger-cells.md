# Primary source trigger cells

The supported serializer changes the X/Z **lookup cell** of an existing primary
MAP kind 0 or kind 1 row. Retail source bytes remain immutable; authored edits
bind to the complete original `0x12000`-byte MAP SHA-256. Stable trigger identity
is the scene, primary table kind and original row index, independent of its cell.

In Edit mode, select an existing primary trigger in the hierarchy or source-cell
viewport, then choose **Edit trigger cell** in the shared Inspector. The dialog
shows the payload read-only, two integer cell inputs, separate Retail/Authored/
Current/Proposed layers and the matching world intervals. Review a proposal or
retail reset, inspect any layer in the scene, Return to the retained inputs, then
Apply once. Close/Restore discards the comparison. Ordinary Undo/Redo, Save/Open
and Build retain the authored cells; identical or inherited values create no
spurious history. This uses the user-owned retail source, without a running game.

`sdk.trigger_cells` exposes source-bound review, Apply and effective annotations.
The scene-owned `TriggerCells` component stores `{source_sha256, edits}` with no
retail payload. Fresh review keys reject changed project/source/inputs before a
single ordinary history command. Imported source spatial records remain intact;
a separate `scene_trigger_state_key` updates annotations and viewport cells.
Normal Build requalifies the complete original MAP and independently checks the
exact requested trigger audit before composing other MAP edits. Source report
links reopen the registered trigger tool; fallback IDs reject explicitly.

Validation covers50 selected Python cases with no skips (including12 affected
and neighbor cases rerun after repairs),6 Node suites and3 module syntax checks.
Thirteen actual browser checks passed with zero page/HTTP errors or run requests;
review and scene screenshots were visually inspected. The saved Town01 row0000
fixture changes only65554,30 to31; destination bytes146/132 remain unchanged.
Fresh original-disc span, full MAP diff, ZIP payload and imported metadata agree.
Private evidence is under `local-output/sdk-20260909/trigger-cells-20261002/`.
The package is uninstalled and unplayed; see the
[deferred gameplay queue](legaia-gameplay-verification-queue.md).

`importer.trigger_authoring.trigger_authoring_options(original, scene)` returns
metadata-only `source_sha256` and `records`. Each record has `trigger_id`,
`table_kind`, `record_index`, `byte_offset`, `byte_length: 4`, the complete row
`sha256`, existing `encoded` fields, and half-open one-tile `tile_bounds`.

`patch_field_triggers(original, expected_sha256, scene, edits)` accepts only
`{trigger_id, tile_x, tile_z}` edits with integer byte values 0..255. It returns
equal-size bytes and a per-changed-byte audit with `trigger_id`, `table_kind`,
`record_index`, `field`, `byte_offset`, before/after values and scope
`source-MAP-trigger-cell-only`. Empty or inherited edits return identical bytes.
Malformed shapes, stale hashes, duplicate IDs, unsupported/fallback IDs and
invalid source spans reject the complete proposal.

Only each selected row's first two bytes change. Kind 0 destination half-tiles,
kind 1 record/gate bytes, offsets/counts, source ordering, kind 2 elevation,
kind 3 regions, collision/object grids, descriptors and every other MAP byte
are preserved. All four known tables must fit the primary `0x2000` block and
have disjoint spans. The physical combined kind 0/1 maximum is 2043 rows.
The final whole-MAP diff must equal the exact byte audit.

Coincident cells remain separate rows. Lookup scans primary before fallback
and selects the first matching row within its kind; moving a row can change
which record shadows another. No rows are reordered, deduplicated, added,
removed or automatically rebound. Unknown kind 1 gates may move because the
generic lookup's X/Z fields are independently understood; their gate and
payload stay untouched and their behavior remains explicitly unknown.
Fallback rows are outside the primary MAP source span and are unsupported by
this serializer.

Trigger cells use `tile = world >> 7`, giving world intervals
`[tile*128, (tile+1)*128)` with no 64-unit bias. The reference dispatcher covers
tiles 0..127. Encoded source bytes outside that range remain representable
without an activation claim. Display Y=0 is an inspection plane; floor height,
walkability, object contact and actual script execution are not established.

Kind 0 is an intra-scene teleport lookup: its preserved destination bytes give
static world X `dest_x*64+64` and Z `(dest_z+1)*64`. Kind 1 gate 0 identifies an
object lookup key with an unresolved flat MAN record index; it is not a proven
player contact volume. Gate 1 identifies a P2-local source reference whose story
conditions and execution remain unobserved. This feature edits their lookup
coordinates, leaving those payloads intact.

Retail dispatch consults the crossed tile's object-cell bits `0x0600`. Scene
initialization also paints `0x0400` footprints from fallback kind 1 records.
Missing bits in the original on-disc object grid do not by themselves establish
that a source trigger cannot activate. This serializer does not paint or
simulate that grid, initialize scenes, evaluate story gates or infer activation.
Any authored primary row may still depend on its surrounding scene state.

Evidence remains pinned at `d6e64c68ede25813d35db20980da82a1a025549b`:

- `crates/engine-core/src/field_regions.rs`, blob
  `8f54e88895ecdf0ca3fe1fc5602ce583911c5feb`, lines84-128: kind 1 header,
  four-byte rows and X/Z-only first-match lookup; lines131-179: kind 0 fields
  and static destination arithmetic; lines233-239: object-cell trigger gate.
- `docs/subsystems/field-locomotion.md`, blob
  `220746dd6a415bfd61cc8982f18c9aae691279d4`, lines255-280: initialization
  footprint painting, all four strides, primary/fallback precedence, source
  trigger classes, flat object references and runtime restrictions.
- `crates/engine-core/src/scene/host/scene_entry.rs`, blob
  `0cf4e43f69fa6f5a547e2b3fd7696306c340fd0a`, lines1267-1304: unbiased trigger
  quantization, canonical dispatcher range, crossing order and gate 1 filter.

The reference is a read-only development oracle. No dependency, pin change or
runtime implementation is copied. The existing field MAP decoder qualifies
source table spans; this is an independent exact-byte writer.

Gameplay acceptance is deferred: verify the authored lookup cell at the intended
location, duplicate-row precedence, preserved teleport destination or binding,
scene initialization/activation, story conditions, object contact and floor
behavior in a user-controlled playable build. Offline byte agreement alone
does not prove any of those behaviors. No game launch is required to author,
review or build a qualified source-coordinate modification.
