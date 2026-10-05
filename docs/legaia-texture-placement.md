# Static native texture placement

The PNG-to-TIM draft dialog offers **Find static free coordinates** for a source
texture pack or an existing authored slot. Choose a PNG and native bit depth,
then query placement. A found result fills the image word coordinates and the
16-word-aligned palette coordinates. **Convert PNG** remains a separate action;
slot review and Apply retain their existing explicit workflow. The finder never
publishes files, changes project state, adds an Undo step or assigns materials.

`POST /api/texture-placement` accepts exactly `asset_id`, `source_key`,
`png_base64` and `bpp`. It requalifies the native pack, decodes the bounded PNG,
and excludes all known Current scene textures, authored slots and boot uploads.
Editing an authored slot excludes only that slot's current footprint. Creating
a slot retains its source anchor in the occupancy census. Image dimensions must
encode whole native words within 1024 by 512 VRAM; TIM content stays within the
existing one MiB authored budget.

The deterministic search prefers image origins from top to bottom, left to
right, and palette origins from bottom to top, left to right. Occupancy uses
exact word rectangles; proposed image and palette cannot overlap. Reports use
`legaia.texture-placement.v1`, include source/PNG/occupancy hashes and distinguish
`found`, `no_fit` and `search_budget_exhausted`. At most 8192 normalized rectangles
and one million image/palette pair checks are accepted. A budget-exhausted result
does not claim that no fit exists. Closed, stale or superseded editor requests
cannot populate coordinates or retain a prior converted draft.

Known uploads now share a corrected footprint helper with authored slot review.
GP0 A0 writes wrap X modulo 1024 and Y modulo 512 in `runtime/src/gpu.c`.
Consequently a vell boot upload at `(960,456)` with 256 words covers both
`[960,1024)` and `[0,192)`. The former rectangle-only census missed the wrapped
tail. Source uploads are now split into up to four bounded rectangles; unsupported
transfer dimensions reject rather than being silently clipped. Runtime code was
not changed.

Static placement does not establish runtime residency, upload order, texture
page/material compatibility or gameplay correctness. Pixel/STP conversion and
native material binding remain separately reviewed.

## Verification - 2026-10-04

Eight focused Python checks passed with the private disc and no skips, followed
by a dedicated wrapped-tail overlap regression. Placement and existing PNG
conversion JavaScript checks passed. A fresh native vell browser workflow filled
image `(0,0)` and palette `(320,511)` for an 8 by 8, 4-bit sample using 92 qualified
static rectangles. Independent existing footprint readback found zero overlaps;
separate PNG conversion verified its native header. Project document, history
and selection stayed unchanged, with zero page errors. Desktop and narrow
screenshots were inspected. The first browser harness waited for the wrong status
word; the corrected harness passed on a fresh project. No game launched or installed
build changed. Private evidence:
`local-output/sdk-20260909/texture-placement-20261004/final/proof.json`.
