# Static VRAM upload inspection

**Find static free coordinates** now displays a qualified VRAM map before PNG
conversion. The map represents 1024 native words by 512 rows, with a 64-word/row
reference grid. Current images are blue, palettes gold and boot uploads grey;
the proposed image/palette use green/pink outlines. An 8-pixel image may occupy
only two native words at 4-bit depth. These are upload footprints, not a rendered
texture atlas or evidence of simultaneous runtime residency.

Click the map to inspect a word. Arrow keys move inspection one word at a time
within VRAM bounds. The Inspector below lists source asset IDs, upload kinds and
half-open rectangle bounds for that word, with a maximum of 32 displayed rows.
The full qualified census remains available to picking. At a reduced display
size, one screen pixel can represent multiple words; keyboard movement permits
exact word inspection. Empty words are labelled as having no known static upload,
without claiming runtime availability. Map interaction changes no project data,
selection or history.

`POST /api/texture-upload-map` accepts exactly `asset_id` and `source_key`.
It uses the placement finder's shared native-pack qualification and normalized
Current upload census. Its `legaia.texture-upload-map.v1` report includes source,
scene, selected/excluded asset, coverage, dimensions, rectangle count, occupancy
hash and source-owned rectangles. Editing a saved authored slot excludes only that
slot. Creating a new slot retains the anchor. Maximum census size is 8192 rows.
Source changes reject before publication.

The editor independently hashes the complete sorted rectangle list and requires
it to match the accepted placement's occupancy hash, source context, count and
coverage. Out-of-bounds rectangles, unknown upload kinds, owner contradictions,
stale sources and unsupported report fields reject. Placement and map requests
share the existing abort/generation/busy lifecycle. Closing aborts pending requests;
changed inputs and conversion remove the temporary map. No project file is published.

## Verification - 2026-10-04

Four focused placement/map Python checks passed with private retail input and no
skips. They cover read-only HTTP, stale/extra-field rejection, census hash equality,
native vell wrapped-tail coverage and the existing overlap witness. Focused map,
placement and existing conversion JavaScript checks passed, including detached
results, altered occupancy bytes, invalid owners/kinds, bounds and half-open picking.

A fresh native vell styled-editor workflow passed map rendering, mouse/keyboard
inspection at row456 in the boot upload's wrapped `[0,192)` tail, separate native
PNG conversion, map removal and close while a map response was pending. Project
document, history and SDK selection remained unchanged; zero page errors. Desktop
and narrow screenshots were inspected. Browser checks found and fixed missing
static-module serving and canvas-border coordinate handling. An intermediate
subpixel assertion was refined to allow screen-pixel quantization followed by
exact keyboard movement; failed attempts remain preserved. Private evidence:
`local-output/sdk-20260909/texture-upload-map-20261004/final-verified/proof.json`.

No game launched or installed output changed. Upload order, runtime residency,
material/page compatibility and appearance remain separate gameplay acceptance.
