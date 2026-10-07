# Grow and shrink Current vertex groups

In Move model geometry, choose Selected vertex group. Grow group adds exactly
one ring of neighbors from the selected object's Current preview triangles.
Pressing it again adds the next ring. Shrink group removes selected vertices
that have an unselected neighbor. These complement Select linked vertices,
which traverses an entire connected component, and Invert group.

The tools change the local selection only. They do not alter coordinates,
normals, topology or project history. Use the existing movement tools to stage
geometry changes, and Save vertex group to retain the selection. Saved groups
use existing source qualification, normal history and Save/Open.

Neighbors follow shared object-local vertex indices in decoded Current preview
triangles, including their triangulation edges. Coincident positions, shared
normals, spatial proximity and opaque primitive structures are not inferred
connections. Other objects stay outside the operation. The entire selected
object's triangle range is validated before a result is produced. Malformed
or cross-object references reject; a Grow result above 4096 vertices rejects
atomically. Dirty geometry, active drags, pending requests and stale sources
retain the existing selection locks.

Shrink erodes a selected/unselected boundary rather than open mesh edges.
A fully selected connected component and an isolated vertex therefore remain
selected. If Shrink would produce an empty group, the editor retains the current
selection and explains why. No-op actions leave selection and history unchanged.

## Offline acceptance, 2026-10-07

Five affected client suites and two syntax checks passed. Focused checks cover
exactly one ring, repeated growth, selection-boundary erosion, object-local index
rebasing, isolated/full-component behavior, immutable inputs, malformed topology
and overflow rejection. Existing movement, grid, linked/inverse and marquee
guards remain green.

An actual Town01 Current model workflow selected vertex 0, grew to
`[0,1,2,3,4,20,22]`, then to fourteen vertices. Shrinking the first ring yielded
`[0,2]`; shrinking the single seed retained it with an empty-result explanation.
Each local action left the SDK state exact. A geometry draft disabled both tools.
Saving the first ring added one history entry; explicitly selecting the newly
saved group and Recall restored its exact indices. Undo/Redo and Save/Open
preserved the library and model data. The initial private check accidentally
recalled a pre-existing group; its evidence is retained with the corrected check.

Wide and 400 px layouts were inspected without overflow, page errors or game
requests. Current model SHA-256 remained
`7508d0da0666dfc7c76901db77b414849ec009710aa05304f4da913f9667cdfe`.
Normal private native packages before/after group Save were byte-identical,
SHA-256 `c171e5e2a8a1e5a2c4c65595785f3b8a17e050e3e10ced471522e07663c6ee9d`.

Private evidence: `local-output/sdk-20260909/vertex-selection-rings-20261007/`
contains focused checks, the real editor workflow, screenshots, group/model
proof, native packages and private project. No new serializer or authoring API,
game launch, runtime attachment, install or full-disc export was introduced.
No full regression campaign was repeated. Gameplay verification remains deferred;
development stays solo and the full SDK goal stays active.
