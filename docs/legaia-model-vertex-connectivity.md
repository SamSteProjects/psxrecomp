# Vertex selections from Current topology

In **Move vertices in 3D**, choose **Selected vertex group**. **Select linked vertices** expands the current indices through the selected object's Current preview triangles. Multiple seed vertices can select multiple connected parts. **Invert group** selects the remaining object-local vertex indices.

These actions only change the local selection. They do not edit coordinates, normals, topology or project history. Geometry drafts must be discarded before changing the selection with these tools. **Save vertex group** persists the selection using the existing source-qualified group library, with its own history; Recall restores indices using Current coordinates. If inversion is empty, the existing selection is retained with an explicit status.

Connectivity follows shared vertex indices in decoded preview triangles. Coincident coordinates, shared normal rows and spatial proximity are not links. This is not a claim about runtime ownership or connections in opaque/nontriangulated primitives. Other objects stay outside the operation. Malformed object ranges or triangle references reject it. A result over4096 vertices rejects atomically, preserving the existing selection.

## Offline acceptance, 2026-10-06

Focused Node checks cover disconnected/coincident rows, multiple seeds, object-local index rebasing, inversion, immutable source metadata, invalid cross-object references and selection overflow. Existing vertex movement/scene-review guards remain green.

An actual Town01 Current model workflow expands a seed, checks repeat/no-op, inverts `[0,2]`, confirms local actions do not change SDK state, verifies geometry-draft locks, saves the exact group and recalls it. Group Undo/Redo and Save/Open preserve the indices. Wide/narrow layouts were inspected. Model/imported/authored geometry remains exact. Native package Builds before and after saving the group are byte-identical, SHA256 `c171e5e2a8a1e5a2c4c65595785f3b8a17e050e3e10ced471522e07663c6ee9d`; the Current model SHA256 stays `7508d0da0666dfc7c76901db77b414849ec009710aa05304f4da913f9667cdfe`.

Private evidence: `local-output/sdk-20260909/vertex-connectivity-20261006/`. No game, runtime attachment, installation or full-disc export ran; gameplay verification remains deferred. No serializer or authoring endpoint was added.
