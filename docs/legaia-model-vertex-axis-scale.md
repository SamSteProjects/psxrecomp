# Selected vertex per-axis scaling

Move model geometry now offers Uniform (the default) or Per axis scaling for
selected vertex groups. Per axis accepts independent X/Y/Z integer percentages
from 1 through 1000. A value of 100 leaves that axis unchanged. The pivot is the
object-local origin or the selected group's bounds center. Source Y points down.

The exact half-unit center is retained through calculation. Each result rounds
to the nearest signed16 native word, halfway away from zero. Overflow on any
selected coordinate rejects the entire operation. Zero, reflection, fractional
percentages, malformed arrays, duplicate/out-of-range indices and stale source
hashes reject. Uniform scaling retains its existing request schema and results.

Scaling starts from Current geometry and affects only selected XYZ words.
Normals, padding, face topology, materials, allocated-row ownership and Retail
provenance remain unchanged. It does not recalculate lighting normals, alter
actor placement or retarget a skeleton. Other supported tools can edit normals
separately. This is authored geometry arithmetic, not an inferred game scale field.

Stage group scale creates a local draft. Draft/Current/Retail previews and
single/all-instance scene comparison use the same candidate. Editing controls
and project history remain locked until the draft is applied or discarded.
Explicit Apply uses the normal model replacement command and history; Save/Open
and the native Build pipeline retain the result. Scene comparison checks the
exact operation, three percentages, selected indices, pivot and candidate bytes.

The codec entry point is `scale_shape_vertices_axes`; the project command is
`scale_model_vertices_axes`. The exact HTTP route is
`/api/model-vertices-axis-scaling`. Scene review uses operation
`vertex_axis_scaling` with values `{indices, percents, pivot}`.

## Offline acceptance, 2026-10-07

Sixteen focused Python checks, five client suites and two syntax checks passed.
Coverage includes independent axes, odd/negative pivots, uniform compatibility,
subset/normal/topology preservation, exact review identity, malformed/overflow/
stale requests, no-op history and allocated-row ownership.

On a private Town01 project, vertices 0-2 of scene model 0000 were scaled by
150/75/125 percent around their bounds center. The editor passed default/mode
visibility, identity and invalid scale, staging, discard, Draft/Current/Retail,
single/all-instance scene review and return, Apply, Undo/Redo and wide/400 px
layout checks. Browser page errors and game launch requests stayed empty.

Independent raw native-word calculations matched the authored model. Only eleven
selected XYZ byte offsets changed. Imported state remained exact; Undo restored
the complete prior project document. Save/Open retained the edit. Both directory
and ZIP native output decompressed to the exact expected complete MAN section.
Model SHA-256: `100b9e273c2f329c2ad07d1f5facbe09d7b8470f46d31b6897b5eb9f278f2219`.
Build: `f4e01a7d44332334`; package SHA-256:
`23e8b5a8b620d569cff12281790789086fdd8254d934e1e51f9104c4b038a6f3`.

The first browser check caught an incorrect control assignment that disabled
Stage when Per axis was selected. The assignment was repaired and the complete
workflow rerun successfully; failed evidence is retained. A visual-only harness
setup failure is retained separately. Private evidence is under
`local-output/sdk-20260909/vertex-axis-scale-20261007/`.

No runtime source change, game launch, runtime attachment, mod install, full-disc
export or full test campaign occurred. Native readback proves delivery of bytes;
gameplay appearance remains deferred. Development stays solo; the SDK goal is active.
