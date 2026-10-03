# Editing stored model normals through Blender

Model authoring GLB profile v4 carries `_LEGAIA_SOURCE_NORMAL` as a custom float VEC3 attribute containing the original signed-i16 normal XYZ values. These are raw retail object-local axes and magnitudes. They are not normalized and do not receive the POSITION attribute's Y flip. The display `NORMAL` attribute is ignored during authoring import.

Export the model and current source binding from the inspector. Import into Blender with **Merge Vertices disabled**, retain source object metadata and custom attributes, then export GLB with **Custom Attributes enabled**. Review the resulting source normal changes, Apply through the model inspector, verify history and the effective model, Save and reopen the project, and Build through the normal project pipeline. A refreshed export is required after project changes.

In Blender 5.2.2, the raw attribute survives as a `FLOAT_VECTOR` on the `POINT` domain. Edit it through `mesh.attributes`. A source normal can belong to several face corners, and quad triangulation or seams can duplicate each corner again. Every alias of the same source normal must agree after signed-i16 quantization. The binding and source inspection establish ownership; vertex positions do not identify normal ownership.

For example, this changes one known flat quad's shared normal. Choose the object, source primitive, and raw values from the current inspection; these example identifiers are specific to the private qualification model:

```python
obj = bpy.data.objects['object-1']
mesh = obj.data
corners = mesh.attributes['_LEGAIA_SOURCE_CORNER']
normals = mesh.attributes['_LEGAIA_SOURCE_NORMAL']
source_corner_ids = {0, 1, 2, 3}
for index, entry in enumerate(corners.data):
    if round(entry.value) in source_corner_ids:
        normals.data[index].vector = (1, 4096, 0)
```

For a normal referenced by other primitives, include all of their source corner IDs too. For Gouraud packets, different source corners can reference different normal table entries. Copying or painting Blender shading normals does not change the raw authoring attribute. A zero source normal is a valid stored value and must not be confused with an unavailable normal.

Unlit corners carry the out-of-domain sentinel `[32768, 32768, 32768]`. Preserve it exactly. It is not a normal vector and does not authorize adding a normal table or a reference. Writable values range from -32768 through 32767. Existing normal references, counts, table allocation, and the fourth SVECTOR padding word remain unchanged. Conflicting aliases or malformed references reject review.

## Independent source qualification

AndrewAltimit's read-only reference commit `d6e64c68ede25813d35db20980da82a1a025549b` identifies vertex and normal tables as eight-byte SVECTORs containing signed-i16 XYZ and padding in `crates/tmd/src/lib.rs`. Its descriptor and primitive documentation distinguish flat and Gouraud lit packet layouts. Private raw retail evidence independently confirms normal references are **SVECTOR byte offsets**, requiring eight-byte alignment and division by eight before selecting the normal table entry; they are not ordinal indices.

| Lit packet family | Normal-reference byte offset within packet | Ownership |
|---|---:|---|
| Flat textured triangle | 12, before vertices | One reference shared by all corners |
| Flat textured quad | 20, after vertices | One reference shared by all corners |
| Gouraud textured triangle | 18, after vertices | One reference per source corner |
| Gouraud textured quad | 20, after vertices | One reference per source corner |

Actual source models qualify all four families: Town01 model 0009 contains flat and Gouraud quads, Town01 model 0036 contains Gouraud triangles, and Dolk2 model 0012 contains flat triangles. For example, model 0009's object 3 has 24 normals and stored references 128, 136, 144, and 152. Those values are outside the ordinal count but resolve correctly as byte offsets to normal entries 16 through 19.

## Actual Blender byte evidence

Blender 5.2.2 LTS preserves all model bytes on unchanged GLB round trips. Two isolated edits to Town01 model `asset://town01/models/scene-tmd/0009` verify exact write ownership:

- Object 1, flat shared normal 0: `[0,4096,0] → [1,4096,0]`. All six triangulation aliases agree; only byte 3332 changes from 0 to 1.
- Object 3, Gouraud normal 16: `[2978,2811,0] → [2979,2811,0]`. Only byte 4640 changes from 162 to 163.

Every other byte remains identical, including normal references, SVECTOR padding, vertices, face references, UV, RGB, material words, and packet commands. Private GLBs, source TMDs, Blender source, raw packet observations, and proof JSON remain under `local-output/sdk-20260909/model-glb-normals-20261002/research/`. Retail payloads are not committed fixtures.

This verifies source serialization and external interchange. The editor and Blender display normals do not establish parity with retail lighting, and visible in-game lighting remains deferred to manual gameplay verification. No game or disc export was used for this evidence.
