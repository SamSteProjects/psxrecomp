# Combined native face/material model assignment

Status: native backend, HTTP, face-editor browser workflow and combined placed-scene comparison qualified.
Separate face-only and material editors remain available.

`POST /api/model-texture-assignment-preview` accepts exactly:

- `asset_id`: imported active-scene model identity.
- `primitive_edits`: 1 to 256 ordinary source-qualified face drafts (existing
  vertex connections, UV bytes, stored RGB and existing normal references).
- `material_edits`: 1 to 256 ordinary semantic material drafts (native page/depth,
  indexed palette coordinates or shared group semitransparency).
- `expected_sha256`: exact Current effective native model hash.
- `source_key`: exact Current editable scene source key.

The normal face/material codecs enforce their own source domains, duplicate
ownership and masks. Direct 16-bit bindings preserve Current CLUT; ABR/reserved
bits remain protected. Explicit group semitransparency affects its shared members.
Face topology, vectors, unknown bytes and packet capacities are unchanged.

Review independently constructs face-only and material-only candidates without
publishing either. Material edits are then applied to the face candidate. The
material audit must equal its independent Current audit, and a complete native
Current-to-final audit must equal the union. Retail/retained-topology comparison
and a source-bound `review_key` are regenerated from exact bytes and drafts.
Intermediate hashes are composition evidence; **Current** is always the actual
project model. HTTP adds the existing verified Current/Proposed texture previews.

`POST /api/model-texture-assignment-apply` requires the same fields plus the exact
`review_key`. It recomputes all qualification, rejects changed/stale/no-change
requests, and publishes only the final replacement. Existing additions/removals
and topology ledger replay stay with the ordinary writer. One model Undo restores
both field sets together. Save/Open, normal Build and independent package readback
use existing model content/ledger composition.

Texture creation, conversion and source retention remain separate explicit
operations. This transaction changes no TIM pixels or texture-slot metadata and
does not establish live VRAM residency, runtime ownership or gameplay correctness.

Verification: four focused real native codec/HTTP tests include group ABE,
unchanged readonly review, wrong/changed/stale/invalid/no-change rejection,
one-step history and stable authored face IDs with exact retained-ledger replay.
Private Town01 HTTP proof independently checked five-face UV/TPage bytes, one
combined model Undo, stale repeat rejection, offline Open and normal Build exact
model/TIM bytes with unchanged decoded neighbors:
`local-output/sdk-20260909/model-texture-assignment-20261004/parent/proof.json`.
The browser workflow now uses these routes directly. In the face editor:

1. Qualify the desired GLB faces, or choose selected-face/textured-group scope.
2. Choose target UVs from a Current scene texture and native page region.
3. Copy remapped UVs into draft using explicit Source/Target rectangles.
4. Stage texture binding for UV scope. This is a separate explicit draft action.
5. Preview faces to compare actual Current/final models and both native audits.
6. Apply reviewed faces to publish one model change. Discard texture binding draft
   retains face edits; Discard draft clears both sets.

Intermediate hashes are validated as separate composition evidence. They never
replace the displayed Current source. The frontend validates each contribution,
the exact audit union and topology comparison before enabling Apply, then checks
the Apply receipt against the accepted review. Changing either draft withdraws it.
A source change requires fresh Current qualification. Both unposed native previews
carry the model asset identity for the normal face comparison renderer.

A private Town01 browser proof passed five GLB-selected faces, native checker TIM
page selection, combined UV/page staging, readonly Review, draft invalidation and
combined Apply/Save/reload/Build review. Independent normal Build readback, model
Undo/Redo and offline Open also passed:
`local-output/sdk-20260909/model-texture-assignment-ui-20261004/parent/verified/proof.json`.
`POST /api/model-texture-assignment-scene-preview` takes the same draft/source
fields as Apply, including the accepted `review_key`, plus `entity_id` and the
explicit boolean `all_instances`. It regenerates the combined model and requires
that review key before composing the final native content through the ordinary
scene poses. Added topology uses a temporary content ledger replay against its
qualified base. No model replacement or history entry is published. Proposed UV
crops and native material bindings are refreshed from the verified texture catalog.

Inspect proposed faces in scene now supports the combined draft. The browser
checks its complete review metadata against the accepted model review, preserves
existing instance transforms, and supports Current/Proposed switching, isolation,
optional GLB face highlights and Return to face editor. Return retains the reviewed
combined Apply; any source/draft change still requires fresh Review.

Five native/HTTP tests and the private Town01 browser proof passed both posed shared
instances and readonly Current/Proposed/isolation/Return. A non-overlapping checker
texture is resolved explicitly by both changed material previews; an earlier
conflicting-address test remained ambiguous. Save/Open, Undo/Redo and normal Build
independent model/TIM readback passed:
`local-output/sdk-20260909/model-texture-assignment-scene-20261004/parent/qualified/proof.json`.
No game launched; live residency and gameplay verification remain open.


The face editor's **UV workspace** shows Current and Draft native byte outlines.
After Preview, each side displays its source-qualified static texture crop. Draft
corner dragging updates the existing UV fields and withdraws the review/Proposed
crop; Preview is required again before Apply or scene inspection. It preserves
other face/material drafts and authors no project state until the existing Apply.
Missing or ambiguous static evidence remains labelled. Numeric corner fields are
available for precise edits and coincident corners. Crops are bounded native page
pixels, not inferred full texture images or proof of runtime residency.


Clicking a visible native surface in either model comparison selects its existing
object/primitive and updates corner fields and the UV workspace. Both triangles
of a quad select the same face. This readonly selection is blocked by pending face
or material drafts; apply/discard them first. Dragging continues to orbit. Picking
uses the renderer's depth test and visible texture coverage, with complete native
face ownership checks. The model comparison uses the strict unposed adapter;
the main scene has a separate Current-qualified placed-surface navigation path.


**Outline selected native face (cyan)** displays the active face's boundary in
both model layers without replacing its texture/material fill. The quad diagonal
is omitted, and hidden boundary edges are deliberately shown as a selection
diagnostic. It is independent of the yellow GLB selection set and changes no
native data, draft or review identity. The caption identifies the active native
object/primitive; turning it off preserves selection and all editor state.


**Pick model face** in the main authored viewport is a one-shot navigation tool.
It resolves the frontmost visible entity before isolating its native triangle ID,
then requires a fresh primitive source matching the loaded project/scene key.
Each displayed object must be a complete native prefix with exact vertex starts,
counts, face triangulation and corner indices. Posed vertex positions do not become
native edits. Unsupported ownership is rejected; empty space leaves selection alone.
The selected entity is reflected in Hierarchy/Inspector before the existing model
face editor opens its Current object/primitive. Retail/live modes and pending scene
proposals are unavailable. Orbit drags never open the face editor.

Private verification covers overlapping instances, hidden/transparent fronts,
background and outside pixels, normal entity picking after restoration, and actual
Town01 scene navigation without model/history/source-key mutations. Existing UV,
material, scene comparison, Apply and normal Build verification also passed.
No game launched; this does not establish runtime coordinates or visibility.
