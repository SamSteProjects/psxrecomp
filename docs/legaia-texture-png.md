# Source-bound texture PNG authoring

**2026-10-04 — resized-texture interchange and comparison reports connected:**
Saved image allocations now support current PNG export/reimport, PNG pixel
proposals and Apply, effective indexed JSON, and TIM/JSON file proposals.
Following payload edits preserve the saved dimensions and allocation binding.
Resized JSON uses `legaia.indexed-texture.v2` with both exact current TIM and
Retail source hashes; changing either hash, layout or current content requires
a fresh export. Existing fixed-layout JSON v1 remains supported.

Retail comparisons explicitly fit Retail pixels into the proposed dimensions,
preserve their top-left overlap, and zero-fill newly added pixels. Reports retain
the true Retail hash, identify the separate comparison baseline hash and count
added/removed pixels. Payload counts describe that baseline; they do not count
removed pixels as remaining source data or conceal a resize as a payload-only edit.
The PNG and file preview UI qualifies and labels this distinction. Current-to-
proposed payload counts remain exact and gate PNG Apply/no-op behavior.

Twenty-one focused Python checks and two Node suites passed. A private Town01
browser smoke passed resized PNG review, pixel inspection/Return, Apply, Save/
reload, JSON v2 file preview/Apply and Save. The saved result passed read-only
normal Build review and exact native texture readback from normal Build. The
new static comparison module was initially absent from the server allowlist;
that registration was corrected before the successful browser smoke.
Evidence: `local-output/sdk-20260909/texture-resize-interchange-20261004/parent/`.
No game, installed runtime change or physical disc export ran.

**Next:** editor resize controls and current-to-proposed resize pixel/scene
inspection using the reviewed allocation request. The resize service, history,
Save/Open, normal Build and following interchange paths are connected; the
complete editor resize workflow is still pending. Runtime appearance, UV coverage,
VRAM upload/residency and transition checks remain in the deferred gameplay queue.
The broader SDK goal remains active.

The SDK can export the current verified TIM texture as a PNG, accept an externally edited image, review the resulting TIM payload changes and apply them through ordinary project authoring. This edits an existing texture allocation: dimensions, bit depth, VRAM rectangles, TIM headers and palette count remain fixed. It does not add textures or establish their live upload, blending or gameplay behavior.

## Editor workflow

1. Open an imported texture, choose its palette and enter Edit mode. Select **Edit texture through PNG**.
2. Select **Prepare PNG export**. Download files for external editing, or select **Use prepared binding and STP** to fill both source inputs directly. This replaces the binding and STP files, clearing the STP input when the export has no plane, and keeps your selected edited PNG. The export represents the effective texture, including an existing authored replacement.
3. Edit the PNG externally without resizing it. Preserve binary alpha: every pixel must have alpha 0 or 255. Keep the binding JSON unchanged. An STP plane must contain only opaque black and opaque white at the same dimensions.
4. Choose the edited PNG, its binding JSON and optionally an STP plane. Choose **Use existing palette** or **Rebuild selected palette** for an indexed TIM. Direct-color TIMs use existing mode.
5. Select **Review selected files**. The review shows both retail-to-proposed and current-to-proposed changes, palette-word/index/image-byte counts, RGB error, STP changes and forced black/transparent rules. Review does not alter authored state or history.
6. Use **Inspect proposed pixels** to compare Current and Proposed. **Inspect in scene**, when available for the current scene preview, temporarily substitutes the reviewed texture and provides a return path. These previews use static source associations; they do not emulate PSX semi-transparent blending.
7. Select **Apply reviewed texture** to store the complete proposed TIM replacement. Ordinary Undo/Redo, Save/Open and the existing texture **Clear override** action apply. A no-op proposal cannot be applied.

Apply requires the exact reviewed files, palette mode, proposed hash and current project/scene/source context. Changing files or context invalidates the review. Export a fresh binding after authored texture content changes. An external editor that strips alpha, adds unsupported color metadata or resizes the image must be configured to produce a supported PNG before review can succeed.

## Embedded PNG source from GLB

Instead of choosing an externally saved edited PNG, choose **GLB PNG source**,
select **Embedded GLB PNG**, and select **Use embedded PNG**. The editor places
those exact extracted bytes in **Edited texture PNG**, displays GLB and PNG SHA-256
identities, and reads them through the same fixed-dimension/native-binding checks.
Use **Prepare PNG export** and **Use prepared binding and STP** for this native
texture, or upload its exported binding JSON and optional STP plane manually. Then
Review and inspect before explicit Apply. Changing the GLB source or
image selection withdraws any accepted review. Extraction itself changes no native
asset, saved project file or history entry.

The GLB must contain its JSON/BIN data in one file, no larger than 32 MiB, with
1–64 image slots. Embedded `image/png` slots must own a plain bounded buffer view;
each PNG is limited to 8 MiB and 2,097,152 pixels, and the server validates its PNG
structure, CRC and supported pixel layout. Image indices and both source hashes are
rechecked on extraction. URI images, JPEG and image extensions are excluded without
network access. Malformed embedded PNG slots reject the source instead of silently
substituting another image.

This is image-byte extraction, not GLB material import. The source image need not
be assigned to a GLB mesh. GLB texture bindings, UV sets, samplers, factors, shaders
and material extensions are not transferred. No texture is newly allocated or
automatically assigned to native primitives. After handoff, Review/Apply binds the
PNG hash and current native texture context; saved authoring does not retain a GLB
material relationship. Native image dimensions, palette capacity and existing TIM
allocation remain fixed.

### Saved GLB source receipt

For a PNG adopted through **Use embedded PNG**, every review/preview/Apply request
includes the selected GLB source. The server freshly re-extracts the image, verifies
both hashes and requires exact equality with the PNG input. The review key includes
its source receipt. Changing or omitting this provenance requires another review;
a manually chosen PNG follows the ordinary PNG path without a GLB receipt.

Apply saves the GLB hash, input PNG hash, image index and image name alongside the
TIM reference. Undo/Redo and Save/Open retain it. The texture Inspector displays
these fields after reopening, and Build includes them in its texture audit while
emitting the same native TIM payload. Subsequent native edits and ordinary texture
replacements clear the receipt; Undo restores its previous value.

New GLB-image Applies also retain the original bounded GLB as
`Authored/TextureSources/<glb-sha256>.glb`. Its embedded PNG can be extracted again
without reconstructing it from quantized TIM pixels. The receipt records the retained
file size, and reads verify its exact bytes and selected image. Project reopen,
Build and input snapshots reject missing or changed retained sources. Project copies
carry these sources under the same byte/file limits as other editable inputs.

Select **Download retained GLB source** in the texture Inspector to recover that
file. The server and browser verify its receipt and hash; then edit externally and
import the image again with a fresh native binding. Source retention is part of the
normal Apply history step. Undo/Redo preserves access to its immutable content;
ordinary replacement clears the active reference, while unreferenced files remain.

Older receipts without a retained byte length remain readable and display their
hashes, but the source download stays disabled. Those historical receipts identify
an input whose bytes were not archived. The new retained source does not assign a
GLB material or establish live residency. Original external STP files and external
GLB dependencies are not separately archived; keep them if needed for re-editing.

## PNG alpha and the PSX STP bit

PNG uses unassociated alpha; RGB channels are not multiplied by alpha. Its general format allows partial transparency, but this TIM workflow accepts only binary alpha. See the primary [PNG specification, alpha representation](https://www.w3.org/TR/png-3/#6AlphaRepresentation).

The TIM conversion is different from PNG opacity:

| Source word | Exported RGBA | STP plane |
| --- | --- | --- |
| `0x0000` | `[0, 0, 0, 0]` | black / 0 |
| `0x8000` | `[0, 0, 0, 255]` | white / 1 |
| Other word with bit 15 clear | Expanded RGB, alpha 255 | black / 0 |
| Other word with bit 15 set | Expanded RGB, alpha 255 | white / 1 |

An STP-set colored pixel still exports opaque PNG alpha. STP cannot be recovered from PNG opacity alone, and STP does not prove that a primitive uses semi-transparent blending.

Without an STP file, the importer preserves current per-pixel STP except when transparent pixels require word zero or opaque black requires word `0x8000`. Review counts these forced changes. An explicit STP file rejects a transparent pixel with STP1 or an opaque black pixel with STP0. For direct 16-bpp and rebuilt palettes, colors that round to RGB5 black also require STP1. Existing-palette near-black samples retain their STP class and select a compatible existing entry. Direct 24-bpp requires opaque alpha and STP0.

The source-word conversion is pinned to Andrew's commit `d6e64c68ede25813d35db20980da82a1a025549b`, `crates/tim/src/lib.rs` lines 161–174, blob `99607f6265e223153cc47678bff1d65d59b0ea54`. It expands each five-bit channel as `(v << 3) | (v >> 2)` and makes only word zero transparent. The SDK interprets these numeric samples directly; it does not claim a measured retail display color space.

## Palette modes and quantization

**Use existing palette** preserves every palette word. It selects the nearest existing entry by squared RGB8 distance within the requested binary-alpha/STP class. Equal-distance choices prefer the pixel's original index, then the lowest entry index. A palette without a compatible class cannot represent that request and is rejected. Direct 16-bpp rounds each RGB8 channel to the nearest expanded five-bit sample, with lower-sample ties. Direct 24-bpp writes RGB bytes directly.

**Rebuild selected palette** quantizes requested words into the existing 16-entry or 256-entry capacity. If all requested words fit, it keeps them exactly. Otherwise, deterministic weighted median-cut in RGB5 reduces colors while keeping transparent zero and the two opaque STP classes separate. Each representative is an actual requested word nearest its weighted centroid. Existing matching slots remain; surplus duplicate slots are reclaimed only when needed, from the highest index while retaining the lowest existing representative slot. New words, sorted by numeric value, fill the lowest free slots. Unallocated slots and other CLUT rows remain unchanged. Pixel assignment then uses the same compatible RGB8-distance and original-index tie rules.

An unchanged visible image with unchanged STP returns the original TIM bytes in either mode. Duplicate palette words, original indices and unused palette entries survive this no-op path.

The review reports maximum channel error and RMS error in RGB8 units, plus the number of pixels with RGB error. Invisible transparent RGB is excluded. Error reporting is numeric; it does not predict hardware blending or perceptual appearance.

**Every palette shares the same packed image-index plane.** Preserving another CLUT row's bytes does not preserve its rendered image when indices change. Inspect other palettes before applying an edit to a multi-palette TIM. Rebuilding only the selected palette can still change shared indices.

## Source, files and Build

The binding records the asset, scene, retail TIM hash, effective TIM hash, project source key and exact palette/layout profile. The server freshly regenerates that binding and rereads the current effective TIM for review and Apply. The service validates retail-to-proposed and current-to-proposed payloads through the existing texture authoring writer; a client cannot authorize a different source allocation through JSON metadata.

The codec accepts bounded noninterlaced PNGs: eight-bit RGB/RGBA/gray/gray-alpha, or indexed PNG with 1/2/4/8-bit indices and a valid palette/transparency table. PNG signature, chunk structure/order/CRC, filters and bounded zlib output are checked. Animated PNG, interlace, sixteen-bit channels, unknown critical chunks, malformed/trailing data, ICC and HDR color metadata are rejected. Standard sRGB metadata is allowed; gamma and chromaticity metadata must match the supported sRGB values. The supported subset is narrower than the [general PNG format](https://www.w3.org/TR/png-3/).

Each image or STP PNG is limited to 8 MiB and 2,097,152 pixels. A source or proposed TIM is limited to 1 MiB. The browser binding JSON limit is 128 KiB. Dimensions must match exactly, and no header, VRAM rectangle or palette allocation is resized.

Maximum-size images with many unique colors can take substantial CPU time during palette matching or reduction. The color-choice cache is bounded to 65,536 entries; no maximum-load performance acceptance is claimed.

After Apply and Save, normal Build uses the existing texture overlay path. A standalone TIM keeps its original allocation; a compressed descriptor texture is rewritten inside its existing pack, with exact replacement readback, preimage guards and compressed-span fit checks. A payload that cannot fit is rejected rather than relocated. The Build report identifies source texture changes. Building a package does not launch or verify gameplay. See [existing texture authoring and carrier limits](legaia-sdk/texture-authoring.md).

## Independent offline evidence

Private proof files are under `local-output/sdk-20260909/texture-png-20261002/research/`; retail payloads and images stay there. `pillow_roundtrip.py` uses the already installed Pillow 12.1.0 to encode/decode PNGs independently, then checks source TIM block structure, packed nibbles and output colors with a separate little-endian readback. Pillow is not a shipped SDK dependency.

The two-palette retail fixture is `texture://dolk2/69/0/17`: 64×64, 4 bpp, 2,144 bytes, SHA-256 `e14119e241fcb40a21af31ea4fcca3f3d149e0cf47868fe6e57f7b7ed0cf5cad`. Both palettes round-trip byte-for-byte in existing/rebuild modes, with and without an explicit STP plane. Palette 0 contains 2,463 transparent pixels and 225 STP-set pixels.

An exact existing-palette edit at `(22,15)` changes index 8 to 0, only TIM byte 587 from `0x28` to `0x20`. The adjacent packed nibble and all palette bytes remain unchanged. The same index edit changes one pixel under palette 1. A separate rebuild replaces palette word 8 from 7,529 to 31, recoloring 88 pixels with unchanged indices and unchanged second-palette bytes. An over-capacity image additionally checks deterministic reduction, independently computed RGB error and preservation of other palette/header bytes.

A second retail fixture, `texture://dolk2/69/0/4`, has original palette entries `0x0000` and `0x8000`. Its original image uses the transparent entry; its opaque-black entry is unused. A reviewed PNG edit selects that original black entry with one exact packed-nibble change and one forced-black STP count. Separate synthetic direct-color fixtures check the word/alpha/STP corner cases and rejection of partial alpha or explicit black/STP0 conflict.

These proofs establish offline source conversion and payload preservation. A bounded search of the first 100 Dolk2 scene models did not establish an actual material use for the selected two-palette fixture. No live residency, palette animation, hardware blend result or gameplay appearance is inferred from this evidence. No game was launched.

## Recover an older original GLB source

For an older image receipt without retained bytes, open its texture Inspector in
Edit mode and choose **Retain original GLB source**. Select the exact original GLB
file and choose **Review original source**, then **Retain reviewed source**. Save
the project. **Download retained GLB source** now recovers those exact bytes.

This is one undoable receipt upgrade. It leaves the TIM unchanged, so an identical
PNG does not need a no-op texture Apply. Review checks the saved file/image hashes
and image identity; it does not recompute the earlier palette/STP import recipe.
A changed file or project context requires a fresh review. Already retained
receipts use Download directly; arbitrary replacement sources are rejected.

## Compressed carrier growth in normal Build

A layout-compatible PNG/TIM edit can increase compressed pack size. Normal Build
now relocates a qualified compressed texture carrier when needed, preserving all
TIM layouts, decoded pack member offsets and following opaque data. Review Build
shows resource relocation size and rebuilt texture pack count. The private package
uses the existing relocated-disc reader; source disc bytes stay unchanged.

Existing dimensions, bit depth and VRAM rectangles remain fixed. New textures,
resizing and runtime upload/rendering acceptance are still outside this workflow.
Legacy fixed-span texture export retains its capacity limit.
