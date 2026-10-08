# Selected vertex per-axis scaling

Move model geometry now offers Uniform (the default) or Per axis scaling for
selected vertex groups. Per axis accepts independent X/Y/Z integer percentages
from 1 through 1000. A value of 100 leaves that axis unchanged. The pivot is the
object-local origin, the selected group's bounds center or explicit source XYZ. Source Y points down.

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

## Explicit Source Scale Pivot

In **Move model geometry**, select **Selected vertex group**, enter the indices and choose Uniform or Per axis scaling. Under **Pivot**, choose **Explicit source XYZ** and enter Pivot X/Y/Z as signed16 integers (-32768 through 32767). These are object-local source coordinates with positive Y down, rather than scene or actor coordinates. Choose **Stage group scale**, inspect Draft/Current/Retail and the single/all-instance scene comparison, then Apply or Discard. Editing the group, percentages or pivot is locked while a draft is pending. The original origin/center choices and Uniform default remain available.

The existing `pivot` request field accepts either `origin`, `center` or an exact three-integer XYZ array. No new command, project schema or runtime scale property is introduced. Uniform and per-axis scaling share the same native word arithmetic, retain half-unit bounds-center precision and round nearest with ties away from zero. Selected coordinate overflow, malformed/boolean/fractional/out-of-range pivots and stale hashes reject before publishing a replacement. Only selected vertex XYZ words change; normal words, padding, topology, material data, other objects, allocated row ownership and imported provenance remain fixed. Scaling a group does not recalculate normals or alter actor placement.

Offline checks passed on 2026-10-08: eight focused Python cases, two Node suites, JavaScript syntax and Python AST checks passed. New coverage includes independently literal expected uniform/per-axis bytes around (10,-20,30), untouched bytes, invalid pivot arrays and overflow refusal, extreme-pivot 100% no-op, allocation ownership, HTTP source/scene Review/Apply and history. The movement Node suite retains its existing origin/center behavior checks.

A private native Town01 editor workflow used model0000, object0, vertices0/1/2, percentages150/75/125 and explicit pivot (10,-20,30). Draft/Discard, invalid percentage refusal, source layers, single/all-instance scene Review/Return, one Apply, Undo/Redo and Save/independent Open passed. The browser produced no page errors or game-launch requests; desktop and 400 px captures were inspected without horizontal overflow. Independent source-table arithmetic matched the entire candidate model, and all thirteen changed byte offsets belonged to the selected XYZ spans. Normal/padding/topology bytes stayed exact. A private data-package Build passed complete containing-section readback from both directory and ZIP, with package SHA-256 `9dac9f73697fa86b56ea4f3ddd0f56eb3708f24829c5def5c013f915dc28f21b`. Final Undo/Save restored the original project document, model and imported evidence with one legitimate Redo entry. Source/reference assets were not modified.

Evidence: `local-output/sdk-20260909/vertex-explicit-scale-pivot-20261008/` (`browser.json`, `native-proof.json`, `cleanup.json`, screenshots and private package). The initial browser locator matched both the pivot selector and its new coordinate controls; changing it to an exact selector preceded the passing run. No game, runtime attachment, native recompilation, installation or disc export ran. Lighting/appearance in gameplay remains deferred; the full SDK goal remains active and solo work continues.

## Current Vertex Pivot

In Selected vertex group scope, choose **Explicit source XYZ** under the scale or rotation Pivot selector. Enter an object-local index under **Current pivot vertex**, then choose **Use vertex as scale pivot** or **Use vertex as rotation pivot**. The fields receive an independent copy of that Current vertex's signed16 XYZ. The anchor can be outside the group being transformed. This copies coordinates; it does not create a persistent vertex binding. Copy again if Current geometry changes.

Picking a pivot leaves geometry, project history and source identity unchanged. Stage a scale or rotation separately, inspect its scene proposal and Apply or Discard. The existing group/draft/source/Edit/busy guards disable copying during an operation or stale context. Indices must belong to the currently selected object's complete Current table, including supported retained allocation rows; malformed/empty/fractional/boolean/out-of-range indices or unsigned/invalid coordinates refuse. Object indices and full table spans are checked. Neither Retail-layer coordinates nor live/scene positions are substituted for Current source words.

Offline checks passed on 2026-10-08: four focused Node suites and JavaScript syntax passed. The new helper suite checks detached words, object-local ownership, signed16 bounds, complete table spans, invalid rows and exact scale/rotation results using an anchor outside the transformed group. The existing movement, explicit-rotation and axis-scale suites passed.

A private native Town01 editor check copied Current model0000/object0 vertex2 XYZ (448,0,192) into both scale and rotation pivots without a mutation request or project source-key change. An invalid negative pivot index disabled copying. The browser then staged/discarded a quarter turn and applied a Y45-degree custom rotation to vertices0/1 around that copied point. Draft/Discard, Current/Retail layers, single/all-instance scene comparison, Apply, Undo/Redo and Save/independent Open passed. Independent complete-model comparison matched all bytes, with changes at only five selected XYZ byte offsets; anchor vertex2, normals, padding and topology remained exact. Scale pivot copying was checked in the browser; scale arithmetic is separately covered by the focused suites, rather than claiming a second native scale Apply in this run.

Desktop and 400 px captures were inspected without horizontal overflow or browser page errors. A private data-package Build passed complete containing-section readback from both directory and ZIP, package SHA-256 `bb04abd2e4e2d6a62b42d54f4e20d4dcb9d097a9b65a3fa7f508be52b610e315`. Original private project/model/imports were restored by final Undo/Save, with one legitimate Redo entry. Evidence: `local-output/sdk-20260909/vertex-current-pivot-pick-20261008/`. No game, runtime attachment, native recompilation, installation or disc export ran. Gameplay appearance remains deferred; the full SDK goal is active and solo work continues.
