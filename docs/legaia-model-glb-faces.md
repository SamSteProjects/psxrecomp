# Reconnecting existing model face corners in Blender

Model authoring GLB profile v3 allows an existing source face corner to reference another existing vertex in the same object. It preserves the number and identity of primitives, their triangle or quad shape, and the object and vertex allocation. It does not add or delete topology.

Export the model and its current binding from the model inspector. In Blender, import with **Merge Vertices disabled**, preserve source custom attributes and object metadata, and export with **Custom Attributes enabled**. Review the GLB in the inspector, inspect the proposed source reference changes and regenerated preview, then Apply, Save, and Build through the normal project workflow.

`_LEGAIA_SOURCE_CORNER` identifies the original primitive corner: `primitive_index * 4 + corner_index`. That ownership stays fixed. Change its `_LEGAIA_SOURCE_VERTEX` value to an existing source vertex ID within the same object, and move every alias of that corner to the target vertex's coordinates. Keep the target vertex's other aliases at those same coordinates. Positions sharing a source vertex must agree after source-coordinate quantization. UV and stored RGB remain owned by the source corner; they do not follow the newly referenced vertex.

For example, this reconnects one corner while copying coordinates from an existing target alias. The object and indices are examples; choose them from the current model inspection:

```python
obj = bpy.data.objects['object-0']
mesh = obj.data
vertices = mesh.attributes['_LEGAIA_SOURCE_VERTEX']
corners = mesh.attributes['_LEGAIA_SOURCE_CORNER']
primitive_index, corner_index, target_vertex = 9, 1, 0
target_point = next(i for i, entry in enumerate(vertices.data)
                    if round(entry.value) == target_vertex)
position = mesh.vertices[target_point].co.copy()
source_corner = primitive_index * 4 + corner_index
for i, entry in enumerate(corners.data):
    if round(entry.value) == source_corner:
        vertices.data[i].value = target_vertex
        mesh.vertices[i].co = position
```

Quad triangulation can expose the same source corner in two triangles. Update both aliases. Changing triangle winding, removing or duplicating corners, adding vertices, crossing object boundaries, or leaving conflicting aliases is unsupported. Review rejection protects the source layout; it does not establish that a proposed shape is visually appropriate. A distant target can stretch a face considerably.

## Source qualification and actual Blender evidence

AndrewAltimit's read-only reference commit `d6e64c68ede25813d35db20980da82a1a025549b` qualifies the packet layout in `crates/tmd/src/descriptor.rs` and `crates/tmd/src/legaia_prims.rs`. Primitive references are little-endian u16 byte offsets into an object's SVECTOR array. Each SVECTOR is eight bytes, so an existing source vertex ID is stored as `vertex_id * 8`. The packet's vertex-reference location is selected by its triangle/quad descriptor; normals, colors, texture blocks, GPU command/padding bytes, and primitive group headers have separate ownership.

Private Dolk2 model `asset://dolk2/models/scene-tmd/0133` evidence uses an effective baseline containing the previously authored RGB and material changes. Blender 5.2.2 LTS preserves all effective model bytes on an unchanged round trip. Reconnecting object 0, primitive 9, quad corner 1 from source vertex 17 to source vertex 0 updates both aliases and changes exactly byte 434 from 136 to 0. The stored u16 changes from `17 * 8` to `0 * 8`; its high byte remains zero. All other effective model bytes remain identical, including the vertex vectors, RGB, UV, material words, normal references, command bytes, and padding.

Private GLBs, Blender source, independently walked packet identities, candidate TMD, and proof JSON are retained under `local-output/sdk-20260909/model-glb-faces-20261002/research/`. Retail payloads are not committed fixtures. This establishes interchange and exact byte ownership. In-game geometry and lighting acceptance remain deferred to manual gameplay verification.
