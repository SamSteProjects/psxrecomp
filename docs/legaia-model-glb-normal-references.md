# Reconnecting existing source normal references in Blender

Model authoring GLB profile v5 adds `_LEGAIA_SOURCE_NORMAL_INDEX`, a float scalar containing an existing normal table index within the source object. It works with `_LEGAIA_SOURCE_NORMAL`, which contains the raw signed-i16 XYZ value of that selected normal. `_LEGAIA_SOURCE_CORNER` retains ownership of the original packet corner. Existing normal table entries can be selected; no normals, packets, or table allocation are added.

Export the current model and source binding from the inspector. Import into Blender with **Merge Vertices disabled**, preserve source object metadata and custom attributes, and export GLB with **Custom Attributes enabled**. Review the source reference changes and proposed effective model, Apply through the inspector, inspect project history, Save and reopen, and use normal Build. Runtime lighting acceptance remains deferred to manual gameplay verification.

Change the raw normal index for the intended source corner and copy the target normal's raw XYZ value into `_LEGAIA_SOURCE_NORMAL`. Every alias choosing that normal must agree on its XYZ. Raw values stay in retail axes and magnitude: do not normalize them or apply the POSITION Y flip. Blender's display `NORMAL` attribute does not author either field.

Flat lit packets own one reference shared by all face corners. Update every corner and every duplicated triangle or seam alias of that face to the same existing normal index. Gouraud lit packets own one reference per source corner; update all aliases of the selected corner. Corners that already reference the target normal must agree with its proposed raw XYZ. Shared normal-table values remain shared after rewiring.

For example, this reconnects an existing flat quad to a known normal donor. Choose indices and raw values from the current inspection; this example belongs to the private qualification model:

```python
obj = bpy.data.objects['object-1']
mesh = obj.data
corners = mesh.attributes['_LEGAIA_SOURCE_CORNER']
indices = mesh.attributes['_LEGAIA_SOURCE_NORMAL_INDEX']
normals = mesh.attributes['_LEGAIA_SOURCE_NORMAL']
source_corner_ids = {4, 5, 6, 7}
for index, entry in enumerate(corners.data):
    if round(entry.value) in source_corner_ids:
        indices.data[index].value = 2
        normals.data[index].vector = (0, 0, -4096)
```

Unlit corners retain normal index `-1` and raw normal sentinel `[32768,32768,32768]`. They cannot acquire a new reference through this workflow. Existing lit indices must be integers inside the same object's normal table and fit the source u16 SVECTOR byte offset. Conflicting flat aliases, invalid table indices, malformed references, missing custom attributes, and source changes reject review.

## Source qualification and format boundary

The source normal table uses eight-byte SVECTOR records with signed-i16 XYZ and retained padding. Primitive normal references store a little-endian u16 **byte offset**, so source index `i` is serialized as `i * 8`. Independent retail observations qualify lit flat triangle references at packet byte 12, flat quad references at byte 20, Gouraud triangle references at byte 18, and Gouraud quad references at byte 20. Flat packets carry one reference; Gouraud packets carry one per source corner. Raw source references must be eight-byte aligned and resolve inside the existing normal count.

Reference evidence is pinned to AndrewAltimit's read-only commit `d6e64c68ede25813d35db20980da82a1a025549b`, its SVECTOR table definition, descriptor and primitive documentation, plus independent actual-retail packet walking. The reference repository is a research oracle, not a runtime dependency.

Normal-reference changes require the explicit `tmd-content-v3` model binding. Older shape, content-v1, and content-v2 bindings retain their earlier ownership rules and do not silently gain permission to change normal references. A fresh v5 authoring export is required for this workflow. Existing authored normal XYZ, RGB, UV, face-reference, and qualified material changes remain composed into the effective source baseline.

## Actual Blender byte evidence

Blender 5.2.2 LTS preserves all effective model bytes on unchanged v5 GLB round trips. Private Town01 model `asset://town01/models/scene-tmd/0009` evidence starts from an authored baseline with object 1, normal 0 changed to `[1,4096,0]`. Two isolated reference edits preserve that earlier change:

- Flat quad: object 1, primitive 1 selects normal 2 instead of normal 1. All six triangulation aliases change together, using donor XYZ `[0,0,-4096]`. Only byte 2940 changes from 8 to 16.
- Gouraud quad: object 3, primitive 16, corner 0 selects normal 17 instead of normal 16, using donor XYZ `[2106,1988,-2896]`. Only byte 4284 changes from 128 to 136.

Both results preserve every normal table byte, normal padding, the earlier normal XYZ edit, vertex vectors, face references, UV, RGB, material words, and packet command bytes. Proof GLBs, Blender source, source TMDs, bindings, independent packet identities, and candidate readbacks remain private under `local-output/sdk-20260909/model-glb-normal-references-20261002/research/`. No game was launched and no disc was exported. Exact source serialization does not establish visible retail lighting parity.
