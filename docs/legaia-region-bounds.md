# Reviewed field region bounds

Refresh scene resources, select an existing primary region in the hierarchy or
Asset Browser, then choose **Edit region bounds**. In Edit mode, change any of
`x0`, `z0`, `x1`, `z1` (integer source bytes0..255) and choose **Review bounds**.
Retail, Authored, Current and Proposed corner values remain separate. The
comparison diagram and world-bound table show the three effective rectangles.
Region type is an encoded read-only value; no behavior or height is inferred.

**Inspect retail/current/proposed bounds** temporarily returns to the viewport
and frames the chosen rectangle. The selected Inspector names the same layer
and exact X/Z intervals. **Return to region review** restores the review;
**Restore source cells**, Close, or a scene/source change discards the transient
comparison. **Apply region bounds** requalifies the review before one undoable
project change. **Review retail reset** proposes removing only that row's
edit. Matching retail and repeated values normalize to no change. Save/Open
retains authored metadata; normal Build writes the supported source corners.

The source-cell representation switch shows Retail source cells or Effective
region bounds. Imported source rows, hashes, order and `legaia.field-spatial.v1`
metadata stay immutable. Separate annotations provide authored/effective
geometry. Their region state key invalidates catalog/viewport state without
changing the scene geometry source key. Trigger cells use their existing raw
quantizer and are unchanged by this editor.

The primary MAP kind3 table has eight-byte rows:
`x0,z0,x1,z1,type,pad,pad,pad`. Source writes affect only the four corners of an
existing stable `region://<scene>/field-map/primary/<row>` identity. The table
parser qualifies all four known table spans, including unexposed kind2, rejects
aliases/overlap and checks the entire0x12000-byte MAP hash. Region type, opaque
padding, headers, counts, table order, triggers and other MAP bytes are preserved.
New rows, type changes, heights and runtime activation are unsupported.

Derived half-open bounds sort the X and Z corner pairs. Equal X extends the
maximum by2 tiles; equal Z extends the minimum downward by2 tiles. World bounds
are tile bounds times128 plus64, from `tile=(world-64)>>7`. Display Y=0 is a
reference plane with unknown height. Evidence remains pinned at
`d6e64c68ede25813d35db20980da82a1a025549b`,
`crates/engine-core/src/field_regions.rs`, blob
`8f54e88895ecdf0ca3fe1fc5602ce583911c5feb`, `RegionTable::parse/scan`.
The reference is a development oracle; no dependency or runtime was copied.

`POST /api/region-bounds-review` accepts exactly region ID, full corners or null,
and `set`/`clear`. `legaia.region-bounds-review.v1` retains whole-MAP and row
hashes, source extent, type, values/bounds layers, changed-corner count and a
review key. Apply accepts the exact reviewed input and key; it rechecks current
project/source evidence before `set_region_bounds`/`clear_region_bounds`.
`RegionBounds` is a scene-root authored component. Save/Open validates and
canonicalizes it. `region_bounds` annotations accompany field-map previews,
with a separate `scene_region_state_key`/`region_state_key` freshness check.

Build independently patches each authored MAP family against the original
source, rejects conflicting writes, then emits one equal-span overlay with a
complete changed-byte audit. Region changes use scope
`source-MAP-region-bounds-only` and identify the stable region row. Combining
region corners, collision wall bits and scenery placement preserves every byte
outside their combined audit.

The saved offline fixture is
`local-output/sdk-20260909/region-bounds-20261002/project/`. Town01 region0000
has source corners58,107,127,1 and type4 at byte66692. The fixture changes x0
from58 to59, moving the minimum X bound from7488 to7616 guest units. It preserves
all other source bytes. Source MAP SHA256:
`60ecaa14978708f8696d60c12f6e98a88cdb19c2e63c7cae8f1c967a1214eb3b`;
modified MAP SHA256:
`2fff22a4db31785a78fbcadd59ae2b1255ef43d3d23e6031f5091050b36f44b7`.
Package is in the same proof directory's `authored-build/`, with SHA256
`0c9a9fe907206e20d7ca3d71c44185661fecdcd5a542870461b31be51e57f803`.
It is built but not installed or played. Independent package readback, history,
persistence, stale evidence rejection and actual browser comparison are verified.
Private logs/screenshots are retained beside the fixture. Runtime activation,
region effects and movement comparison remain in the
[deferred gameplay queue](legaia-gameplay-verification-queue.md).

Region milestone validation:54 retail-enabled Python tests passed with no skips in74.565s;42 Node checks and40 module syntax checks passed. Actual browser comparison passed10 workflow checks with zero page/HTTP errors and zero run requests. Independent package readback confirms one byte changes; imported scene hashes remain unchanged. No game launched or package installed.
