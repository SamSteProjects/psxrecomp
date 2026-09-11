# Editing model shapes

Open a model in the asset browser and choose **Download shape OBJ**. The file
contains unposed object-local geometry in source units, with Y pointing down.
It is not an assembled character or a physical-metre representation.

The verified Blender 5.2.1 OBJ roundtrip uses these settings:

- Import: Forward Y, Up Z, scale 1; disable Split by Object, Split by Group,
  and mesh validation (`validate_meshes=False` in the Python operator).
- Keep vertex and face order, triangulation and vertex counts unchanged.
  Move existing vertices to integer source coordinates within -32768..32767.
  Do not merge vertices, subdivide, remesh or reorder faces.
- Export the selected mesh: Forward Y, Up Z, scale 1; disable Apply Modifiers,
  UVs, normals and materials. Do not apply object transforms to the geometry.

Choose the edited OBJ in the model inspector and **Apply shape**. Retail and
authored views remain separate. Save the project to retain the override, then
Build to package it. Clear Shape Override restores the source; undo/redo retains
history. The override affects uses of this model, rather than only one actor.

OBJ changes positions only. Source TMD normal vectors and material packets stay
unchanged, so substantial shape changes can have incorrect game lighting. The
same-layout TMD upload path also supports editing normal XYZ words. Neither path
supports new topology, new objects or material replacement.

Verified: one six-object town01 NPC model (130 vertices, 225 triangles) survived
Blender import/export with byte-identical TMD reconstruction. Moving one vertex
X by 20 in Blender changed exactly that coordinate on reimport. Party idle and
NPC authored-animation shape composition were checked separately through the
SDK. An isolated Edge browser also passed OBJ file selection, draft protection, discard, upload, authored preview and clear with no page errors. Gameplay acceptance remains pending.
