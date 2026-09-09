# Shared field-party texture evidence

The independent importer implementation uses the existing reference pin
`d6e64c68ede25813d35db20980da82a1a025549b` of
`AndrewAltimit/legend-of-legaia-re`.

- `crates/asset/src/field_char_textures.rs` identifies PROT extraction entry
  874, LZS section 2, as an eight-member TIM pack loaded by `FUN_8001E890`
  through `FUN_800198E0`. Image rectangles are uploaded verbatim; CLUT blocks
  become horizontal strips of `width * height` words. Field uploads do not
  force the STP bit.
- `crates/asset/src/pack.rs` defines member offsets as four-byte word indices
  relative to the decoded pack start.
- `crates/asset/tests/field_char_textures_real.rs` pins the eight rectangles
  and the full reconstructed VRAM FNV-1a-64 digest `64615c6915ba9a80`. The
  reference reports correspondence to its live field VRAM captures; this
  importer did not perform a new live capture.

`load_asset_texture_catalog(disc, asset, scene_catalog)` revalidates the exact
global model source locator before selecting this catalog for F0/F1/F2. Other
assets retain the existing scene catalog after a source-disc identity check.
The shared uploads are not globally mixed into scene uploads. Every material
still requires unique word values at its actual TMD texture-page, CLUT and UV
coordinates; conflicting candidate values are rejected as ambiguous.

Retail verification used the read-only SCUS-94254 disc with SHA-256
`e6120a5d70716dd2f026a2da32d0171d52651971b52c4347a68541299f75258c`.
The independent full-VRAM reconstruction exactly matches the reference digest.
All used textured materials in the ten-object posed assemblies match uniquely:
Vahn four, Noa two, Gala two. Their used UV crops also match standalone TIM
palette decoding byte-for-byte. Their respective atlas members are 1, 2 and 3,
with image origins `(832,256)`, `(852,256)` and `(872,256)` and flat CLUT origins
`(0,478)`, `(64,478)` and `(128,478)`.

The 18 focused texture tests include malformed pack and source-locator rejection,
no forced STP, nonzero page-relative UVs, and preservation of town01's existing
96-entry scene catalog and its model-0088 material matches. Tests carry synthetic
bytes and numeric fingerprints only. Retail payloads and preview PNGs remain
under ignored `local-output/sdk-20260909/field-party-textures`.

This scope does not reconstruct live equipment swaps, conditional scene
residency, palette animation, texture windows, or PSX semitransparent blending.
The eight-member bank is interpreted only for the three evidenced field-party
models. Savepoint, auxiliary, battle, world-map and conditional PCH resource
associations remain outside this supported path.
