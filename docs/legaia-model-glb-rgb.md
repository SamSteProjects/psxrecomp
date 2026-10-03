# Editing stored model RGB through Blender

Model authoring GLBs carry `_LEGAIA_SOURCE_RGB` as a custom float VEC3 attribute containing the stored byte values, from 0 to 255. This is separate from the display `COLOR_0` attribute. Display colors can include texture modulation and display conversion; changing them does not author retail RGB bytes.

Use the model inspector's authoring export, including its source binding. In Blender, import with **Merge Vertices disabled** and export GLB with **Custom Attributes enabled**. Preserve the source object metadata, `_LEGAIA_SOURCE_VERTEX`, `_LEGAIA_SOURCE_CORNER`, and `_LEGAIA_SOURCE_RGB`. Keep the existing topology and object transforms. Review the exported file in the model inspector before applying it, then Save and Build through the project workflow.

In Blender 5.2.2, the raw RGB attribute imports as a `FLOAT_VECTOR` on the `POINT` domain. It can be edited through `mesh.attributes`, rather than a paintable color layer. For example, the following changes the red byte of an existing flat primitive. Choose the object and primitive from the current source inspection; these example identities are not universal:

```python
obj = bpy.data.objects['object-0']
mesh = obj.data
corners = mesh.attributes['_LEGAIA_SOURCE_CORNER']
rgb = mesh.attributes['_LEGAIA_SOURCE_RGB']
primitive_index = 0
for index, entry in enumerate(corners.data):
    if round(entry.value) // 4 == primitive_index:
        value = list(rgb.data[index].vector)
        value[0] = 25
        rgb.data[index].vector = value
```

A flat primitive owns one RGB word shared by all its corners. Update every alias to the same byte value. A Gouraud primitive owns a separate RGB word for each source corner; filter on both the primitive identity and `round(entry.value) % 4` to select that corner, and update every duplicated alias of it. Quad triangulation and material seams can duplicate source corners. Conflicting aliases are rejected during review.

Some textured packets are lit from source normals and have no stored RGB word. Their raw attribute is the reserved sentinel `[-1, -1, -1]`. Preserve it; it does not mean black, and cannot be used to add a new color word. Existing stored values are quantized to source bytes during import. Review reports expose the resulting field changes. Geometry, UV, and raw RGB edits can coexist within the fixed source layout.

## Qualification and preservation

The packet layout is independently qualified against AndrewAltimit's read-only reference commit `d6e64c68ede25813d35db20980da82a1a025549b`, specifically `crates/tmd/src/descriptor.rs` and `crates/tmd/src/legaia_prims.rs`. Flat colors occupy the first three bytes of one word. Gouraud colors occupy the first three bytes of each corner word at a four-byte stride. The fourth byte belongs to the GPU command or padding and is retained. Lit textured rows 0 and 1 have no color block. Untextured rows 2 and 3 do store RGB even though the descriptor's texture-color discriminator is zero; the pinned primitive walker extracts their colors directly. Textured baked rows 4 and 5 place colors before the texture block.

Private actual-retail evidence for Dolk2 model `asset://dolk2/models/scene-tmd/0133` covers flat and Gouraud triangles and quads, both textured and untextured. A Blender 5.2.2 LTS round trip preserves all effective model bytes. Editing all three aliases of object 0, primitive 0's red channel from 24 to 25 changes exactly byte 300. The existing material override remains intact, as do every other byte, positions, UVs, normals, references, and packet commands. Private proof artifacts are under `local-output/sdk-20260909/model-glb-rgb-20261002/research/blender-proof/`; they are not distributable retail fixtures.

This verifies the interchange and byte ownership. Final in-game lighting and appearance still require deferred manual gameplay verification. Blender display shading does not establish runtime renderer parity.
