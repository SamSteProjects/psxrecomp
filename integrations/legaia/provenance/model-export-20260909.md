# Private model GLB export

`importer/export.py` independently writes GLB 2.0 from the existing verified
model/texture/animation preview schemas. It does not read or modify source discs.
The layout follows the [Khronos glTF 2.0 specification](https://registry.khronos.org/glTF/specs/2.0/glTF-2.0.html).
No external exporter code or retail fixture is included in the module.

The input format evidence retains reference pin
`d6e64c68ede25813d35db20980da82a1a025549b`; see the adjacent animation and
field-party texture notes for exact Andrew reference paths. The export carries
the model source locator, reference commit, stable asset identity, raw object
metadata and, when selected, animation identity/frame/object transforms in
glTF `extras`. Original preview arrays are not changed.

The supported output is either object-local source geometry or one explicitly
selected baked animation pose. Each object becomes a node/mesh, and material
groups use expanded triangle corners so per-corner colors and UV seams survive.
The axis conversion is exactly `[x,-y,z]`, with reversed triangle winding.
Source numeric units are retained: no unsupported physical meter scale is
guessed. Consumers can rescale the model deliberately.

Uniquely matched material crops become embedded RGBA PNGs, sampled with nearest
filtering and clamped UVs. Coordinates include a half-texel center offset and
retain the decoded image's top-left origin. Materials use `KHR_materials_unlit`,
double-sided geometry, and alpha masking for transparent palette zero.
Untextured display RGB is converted to glTF linear `COLOR_0`; textured vertex
modulation uses neutral 128, clamped to the valid 0..1 accessor range. Above-128
modulation and PSX semitransparency are reported explicitly. This does not claim
GTE lighting, PSX blending, texture-window or animated-palette fidelity.

`encode_model_glb(preview, frame_index=None)` returns `(bytes, audit)`.
`write_model_export(preview, output_root, frame_index=None)` returns
`{path, filename, audit}`, writes a unique new file, rejects symlink/reparse
ancestors and never overwrites an existing file. The SDK should provide its
private project `Exports` directory and freshly verified preview data, without
accepting client-supplied geometry or output paths. Local filesystem redirection
by another process between validation and file creation is not a transaction
guarantee; the application controls this private output directory.

Validation on the read-only SCUS-94254 disc, SHA-256
`e6120a5d70716dd2f026a2da32d0171d52651971b52c4347a68541299f75258c`:

- F0 Vahn idle frame 0: 10 objects, 496 triangles, four embedded textures.
- Town01 scene model 0088: one object, 328 triangles, two embedded textures.
- Khronos `gltf-validator` 2.0.0-dev.3.10: both outputs have zero errors and zero
  warnings. Vahn has four informational non-power-of-two image notices; the
  nearest/clamp sampler does not require mipmaps.
- Blender 5.2.1 LTS successfully imported both GLBs with the expected object,
  triangle and image counts. Private rendered previews were inspected: Vahn is
  upright with coherent face/body textures, and the tree has foliage and bark.
  Blender's unrelated extension-cache write was denied by the sandbox; import
  and render completed successfully.
- Six focused executable Python tests cover binary alignment and accessor
  roundtrip, finite float32 bounds, PNG CRC/pixel roundtrip, winding/UV conversion,
  static pose selection, malformed inputs, exclusive output creation and path
  rejection, plus both actual retail exports.

Private GLBs, validator JSON, Blender reports and rendered PNGs reside under
ignored `local-output/sdk-20260909/exports`. No retail bytes are tracked. Static
pose export supplies no animated glTF channels or invented joint hierarchy.
