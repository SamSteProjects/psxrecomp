# Editing source model material words through Blender

Model authoring GLB profile v6 carries `_LEGAIA_SOURCE_MATERIAL` as a custom float VEC3 containing `[CLUT, TPage, ABE]`. CLUT and TPage are complete stored u16 source words; ABE is the source primitive group's integer 0 or 1. Source corner identities establish ownership. Blender shader settings, reassigned materials, images, and display shading do not author these fields.

Export the current model and source binding from the inspector. Import into Blender with **Merge Vertices disabled**, retain source metadata and custom attributes, and export with **Custom Attributes enabled**. Review the exact source-field changes and regenerated effective preview, Apply through the model inspector, inspect history, Save and reopen, and Build through the normal project workflow. Export again after project changes.

Blender 5.2.2 imports the raw material attribute as a `FLOAT_VECTOR` on the `POINT` domain. Edit it through `mesh.attributes`. CLUT and TPage belong to one source primitive, so every corner and duplicated alias of that primitive must agree. ABE belongs to the entire source group: every primitive, corner, and duplicated alias in that group must agree, even if Blender splits it across display materials.

For example, choose the object, primitive, group members, and complete source words from current source inspection. This example updates one source CLUT column and turns on ABE for its five-primitive group:

```python
obj = bpy.data.objects['object-0']
mesh = obj.data
corners = mesh.attributes['_LEGAIA_SOURCE_CORNER']
materials = mesh.attributes['_LEGAIA_SOURCE_MATERIAL']
group_primitives = {0, 1, 2, 3, 4}
for index, entry in enumerate(corners.data):
    primitive = round(entry.value) // 4
    value = list(materials.data[index].vector)
    if primitive == 0:
        value[0] = 31362
    if primitive in group_primitives:
        value[2] = 1
    materials.data[index].vector = value
```

These identities and values are specific to the private qualification model. A CLUT column is the low six bits; retain the other bits when choosing a new column. Untextured primitives retain CLUT/TPage sentinel `[-1,-1]`; their ABE group value can still be source-owned. The sentinel cannot add a texture block. Raw material values must be exact integers, with ABE exactly 0 or 1. Missing attributes, stale bindings, conflicting aliases, and unsupported changes reject review.

## Writable bits and retained source data

Existing source material authoring qualifies CLUT mask `0x7FFF`, TPage mask `0x019F`, and group mode ABE mask `0x02`. CLUT retains its high reserved bit. TPage permits page column, page row, and supported texture depth while retaining ABR bits `0x0060` and all other reserved bits. Supported texture depths are 4, 8, and 16 bits. A CLUT change requires an indexed target depth; direct 16-bit and reserved target depths retain their source CLUT. The source ABE write changes only group mode bit 1, preserving packet command bytes and every other mode flag.

AndrewAltimit's read-only reference commit `d6e64c68ede25813d35db20980da82a1a025549b` qualifies texture-block CLUT at `+2`, TPage at `+6`, and source group ABE. Existing retail consumer evidence establishes that caller state can replace encoded ABR, so the GLB workflow does not author it or infer final runtime blend mode. Existing qualified material bindings remain the authority; v6 extends external interchange rather than granting shader assignments new source ownership.

Earlier GLB profiles retain their earlier field permissions. Preserve fresh v6 attributes for material edits. Content bindings retain their explicit format boundaries: source material changes require the qualified material-capable format, and an existing normal-reference edit continues to require `tmd-content-v3`. Prior positions, face references, UV, RGB, raw normal XYZ, normal references, and material changes compose through the same effective model.

## Private actual Blender evidence

The qualification fixture uses Town01 model `asset://town01/models/scene-tmd/0009` with earlier authored normal XYZ and normal-reference changes retained. Its object 0, primitive 0 stores CLUT 31361 and TPage 26; group 0 contains five primitives and stores mode 37, with ABE off. The primary external edit chooses CLUT 31362 and group ABE on, retaining TPage and every unrelated source field.

Actual Blender 5.2.2 LTS no-op v6 round trips preserve every effective model byte. The raw material attribute survives as a POINT-domain FLOAT_VECTOR. The primary edit updates all three primitive CLUT aliases and all fifteen group ABE aliases, changing exactly byte 131 from 37 to 39 and byte 138 from 129 to 130. Earlier normal-reference byte 2940 and normal XYZ byte 3332 remain authored and unchanged.

Separate Blender readbacks verify TPage column 26 to 27 changes only byte 142, while retaining the same earlier normal edits. An untextured Dolk2 model `asset://dolk2/models/scene-tmd/0133` retains its `[-1,-1]` CLUT/TPage sentinels; toggling ABE for its nine-primitive group changes only byte 299 from mode 33 to 35. No texture block is created. Every other source byte, including RGB, references, SVECTOR padding, row commands, and reserved material bits, remains unchanged in each isolated proof.

Private GLBs, Blender source, current bindings, independent packet offsets, source candidates, and readback proofs are retained under `local-output/sdk-20260909/model-glb-materials-20261002/research/`. Texture association can become missing or partial when selectors change; the effective preview reports that source result. An edited shader appearance is not proof of source bytes or runtime blend behavior. Final in-game appearance remains deferred to manual gameplay verification. No game or disc export is used for these proofs.

Central validation passed 44 focused Python cases, two Node guard suites and
12 integrated browser checks. The saved project reopened with the exact
Blender candidate; normal Build package readback retained bytes2940/3332 and
added only bytes131/138. All decoded neighboring bytes and the original
154,547-byte compressed capacity remain unchanged. Parent screenshots and
package proof are under the private milestone `parent/` folder.
