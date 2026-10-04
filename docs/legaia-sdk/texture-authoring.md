# Authored TIM replacement

**2026-10-04 — saved texture resize bindings and normal Build (service stage):**
Reviewed native image resizing now has project Apply, one-step Undo/Redo and
Save/Open. The versioned `tim-image-layout-v1` binding retains the Retail TIM
hash and exact authored image layout; ordinary uploads cannot change dimensions.
Review is read-only and binds the current source, encoded fill value and explicit
potential-overlap choice. The footprint census includes effective scene images,
flattened CLUTs (including the edited texture's CLUT) and known boot uploads.
Only overlap added by the new footprint is reported. This census does not prove
runtime residency, upload order or material suitability.

Normal Build merges resized and fixed-layout edits sharing a pack into one
qualified raw/compressed allocation. Source slots, unedited members, opaque
member tails and physical neighbors retain the native allocation guarantees.
Build audits identify image allocations separately from payload-only edits.
Effective texture/scene previews and palette, pixel and rectangle commands
understand saved allocations; pixels outside the Retail image have no Retail index.
Resizing withdraws an earlier GLB image receipt rather than retaining stale provenance.

Thirty-one focused construction checks passed, followed by thirteen targeted
checks after report guards and added-pixel editing were refined. Private Town01
raw and Dolk2 compressed projects passed Review/Apply, history, Save/Open,
read-only Build review and exact normal-Build readback, including a neighboring
payload edit in the same allocated pack. Town01 allocated one extra PROT sector;
Dolk2 retained physical capacity. Private evidence:
`local-output/sdk-20260909/texture-resize-project-20261004/parent/`.
No game, installed runtime change or physical disc export ran.

**Remaining before the complete resize workflow:** editor resize controls and
reviewed pixel/scene proposals, plus allocation-aware PNG/JSON/TIM-file comparison
reports. Those report paths explicitly reject saved resized bindings for now;
normal native TIM publication and Build work. The HTTP service endpoints are
available without advertising a finished editor capability. Runtime appearance,
UV coverage, upload overlap/residency and scene transitions remain deferred.
This is an implementation milestone, not completion of the SDK goal.

Format evidence uses Andrew's unchanged reference revision
`d6e64c68ede25813d35db20980da82a1a025549b`: `crates/tim/src/lib.rs`
(blob `99607f6265e223153cc47678bff1d65d59b0ea54`) and
`crates/prot/src/timpack.rs` (blob `f90c89f1aba8adf012395a6d752cef49a41d4960`).
Standalone pack offsets convert from words with a four-byte base; descriptor
pack offsets use their existing decoder convention. The writable path rejects
ambiguous members instead of sorting or deduplicating them into new identities.

Texture replacement keeps imported provenance and authored content separate.
The editor accepts a user-selected TIM file with the same source layout and
provides an original TIM download for external editing. Imported and effective
preview layers remain distinct. A replacement supplies actual image and palette
data; changing format, dimensions, VRAM rectangles or CLUT layout is unsupported.

Project metadata stores `texture_overrides`, mapping a structural texture ID to
`asset_sha256`, `byte_length`, `format` and `source_scene_id`. The authored file
lives at `Authored/Textures/<sha256>.tim` beneath the project. Input is bounded
to 1 MiB per file and 128 references per project. Content hashes and lengths
are checked on use, save and offline reopen. Paths are derived from validated
hashes and must resolve within the project. No client source locator or output
path is accepted.

Apply and Clear participate in Undo/Redo and dirty tracking. Clearing or undoing
a replacement retains the content file for history and recovery. The project
format omits the collection when empty, preserving existing baseline build
identity. Imported documents and the retail image are not modified.

Model and scene previews use effective scene TIM data while retaining retail
source locators. Shared party banks are separate and are not replaced through
scene texture IDs. Preview matching still does not reconstruct runtime upload
order, conditional resources, palette animation or PSX blend behavior.

The build combines compatible replacements within each source carrier, checks
exact source hashes and boundaries, and emits private guarded disc overlays.
Normal Build keeps fixed-span overlays when compression fits. If a compressed TIM
pack grows, it instead rebuilds the qualified entry-head descriptor carrier and
its unique physical PROT owner through the existing private relocation package.
Every TIM layout and decoded pack offset stays fixed. Following opaque bytes and
neighbor payloads are retained; later descriptor offsets and PROT starts are
rebased. Model, animation and texture resource growth can compose in one carrier.
Source hashes, bounded pack contents and exact final decoded readback are required;
ambiguous ownership or conflicting edits reject before publication.

**Review Build…** exposes relocation package size, PROT growth and rebuilt texture
pack count without creating a package. Normal **Build** uses the same qualified
pipeline. The legacy fixed-span export API still requires its original compressed
span. No new TIM allocation, resizing, VRAM relocation or runtime appearance is
established by carrier growth. See private evidence under
`local-output/sdk-20260909/texture-compression-growth-20261004/parent/`.

A cold authored/baseline pair now proves visible magenta palette replacement
and return to normal ground colors for `texture://town01/5/raw/0`. Both runs
used the same verified executable and no savestates. See
`texture-runtime-acceptance.md` for the precise scope. Other texture families,
conditional residency and palette/blend behavior still need runtime evidence.

## Image allocation codec stage — 2026-10-04

`texture_layout_allocation.resize_tim_image` constructs a resized native image at
the original VRAM origin, preserving mode and CLUT data. Widths must contain whole
native words (multiples of four pixels at 4 bpp, two at 8/24 bpp, one at 16 bpp).
New rows/columns receive an explicit encoded palette index, PSX word or RGB value;
the overlapping top-left region keeps exact encoded pixels. No sampling or UV
retargeting occurs. Palette headers/shape stay fixed; image bounds must fit VRAM.

`texture_pack_allocation.allocate_texture_pack` verifies each edited slot's source
TIM hash, preserves unedited TIMs and all opaque member tails, rebases word offsets
and audits added alignment padding. The shared resource composer accepts qualified
`texture-layout-pack` and `texture-layout-raw` requests. The raw codec retains
physical capacity for smaller images; compressed carriers update decoded size and
rebase following descriptor payloads. Both re-open exact output and preserve
physical neighbors. The legacy `texture-pack` path continues requiring fixed TIM
layouts unless an explicit allocation edit list is supplied.

This is native infrastructure, not a completed editor resize feature. Project
bindings, source-qualified Review/Apply, footprint/conflict reporting, subsequent
palette/PNG composition and normal Build collection remain to be connected.
Changing footprint can affect other uploads or material sampling even when the
serialized bytes are correct. No gameplay acceptance is claimed. Private read-only
Retail transformation evidence is in
`local-output/sdk-20260909/texture-layout-allocation-20261004/parent/`.

## Reviewed image allocation service

`POST /api/texture-resize-preview` takes exactly `asset_id`,
`expected_sha256` (effective TIM hash), `source_key` (current project scene source),
`width`, `height`, `fill_value` and `accept_potential_overlap` (a boolean).
Dimensions must consist of whole native VRAM words at the existing origin;
fill is an encoded palette index, PSX16 word or RGB24 value according to mode.
Review returns before/after layouts, native allocation evidence, bounded static
footprint findings and `review_key`. Existing encoded pixels are retained in the
top-left overlap; new pixels use the fill value and cropping removes outside pixels.
No resampling is performed. CLUT structure and payload are retained by resizing.

`POST /api/texture-resize` takes those same fields plus the exact current
`review_key`. A different source, choice, dimensions or fill requires a fresh
review. A no-op or unacknowledged new static overlap cannot Apply. Acknowledgment
records a reviewed authoring choice; it does not assert runtime safety.
Apply creates one ordinary project history command. Saving persists the new
binding and hash-addressed TIM. The complete editor resize UI is pending.

Native `set_texture_replacement(..., image_allocation=True)` is the internal
reviewed allocation publication path. The ordinary replacement HTTP endpoint
cannot select this policy. Following ordinary TIM payload edits must preserve
the current saved allocation. Clear override restores the Retail layer.
