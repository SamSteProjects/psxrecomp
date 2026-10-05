# Reviewed model UV rectangle retargeting

## 2026-10-04: Combined face and texture-page browser workflow

The face editor now explicitly stages a qualified Current texture page/depth and
indexed palette binding for its selected face, textured group or GLB-selected
faces. Choosing a UV target alone still changes only the rectangle controls.
Preview faces validates independent face/material audits, their exact native union
and Current/final identities; Apply publishes both drafts as one model Undo.
Discard binding keeps face drafts. Discard draft clears both; source changes
withdraw the review and require fresh qualification. The actual Current/final model
comparison is available before Apply. Combined placed-scene proposal comparison
remains pending, so that scene action is disabled while a binding draft is staged.

Four native codec/HTTP tests now also exercise the browser decoder against actual
Current and retained-authored-face reports. Existing face/material/picker Node
checks passed. Private Town01 browser verification passed GLB five-face selection,
qualified native page choice, UV draft staging, readonly combined Review,
review invalidation and one combined Apply, plus Undo/Redo, Save/offline Open and
normal Build exact model/TIM readback with unchanged decoded neighbors:
`local-output/sdk-20260909/model-texture-assignment-ui-20261004/parent/verified/proof.json`.
No game launched; runtime texture residency and gameplay verification remain open.
The earlier API-only browser-pending note below is superseded by this milestone.


## 2026-10-04: Combined native face/material Review and Apply API

Implemented the backend/HTTP composition needed to apply UV/face fields and native
page/palette/shared-blend drafts as one model replacement. Both drafts independently
qualify the actual same Current model. Material edits are composed onto the face
candidate; their audit must match the independent material-only candidate. The final
native audit must equal both disjoint field audits. No intermediate override is
published or represented as Current. Review includes Current/final previews, exact
intermediate/final hashes and a source-bound review key. Apply regenerates everything
and uses the ordinary replacement writer for one Undo entry and retained topology
ledgers. This API does not add texture slots, allocate topology or infer addresses.

Four focused Python tests passed real native codecs, exact readonly HTTP Review,
wrong/stale/changed/invalid/no-change rejection, group blend plus UV/page composition,
one-step Undo/Redo and existing authored face stable IDs with exact ledger replay.
A private Town01 HTTP test composed five faces onto an authored 128x128 16-bit TIM
region. Independent packet readback confirmed UV and TPage bytes only; wrong review
and stale repeated Apply rejected. Save/Open, Undo/Redo and normal Build exact model
and TIM readback passed with unchanged decoded neighbors. Evidence:
`local-output/sdk-20260909/model-texture-assignment-20261004/parent/proof.json`.

**Next:** browser combined-draft controls and a combined review UI. Existing separate
face/material editors remain available. This milestone proves the combined API, not
completion of the combined browser workflow. See
[API contract](legaia-model-texture-assignment.md). No game launched; gameplay remains
deferred and the broader SDK goal remains active.

## 2026-10-04: Native texture page regions feed explicit UV target controls

The face editor now offers **Choose target UVs from a scene texture** inside
**Retarget a UV rectangle**. Browse the source-qualified Current texture catalog,
choose a Retail or authored texture and explicit palette index, then load its
native page regions. **Use texture page UV rectangle** fills only the Target U/V
controls from the selected inclusive native byte rectangle. It invalidates earlier
face review but changes no face draft or project. Source rectangle and remap scope
(single face, packet group or qualified GLB face set) remain explicit. Copy into
draft, Preview and Apply retain the ordinary face workflow.

The picker reuses native texture source/depth/page/palette qualification and Current
source-key checks. Native page offsets and partial/multiple page regions are retained;
image dimensions alone and GLB shader UVs do not define the target. Regions with
zero U/V spans cannot be used and explain that restriction. Changing texture or
palette withdraws earlier page evidence. Close/stale-context abort and busy ownership
follow the existing child-picker pattern. Native TPage, CLUT, blend, pixels and
geometry are unchanged by this UV helper; material assignment remains separate.

Focused checks passed detached target coordinates, a direct-color native offset,
indexed multi-page regions with explicit palette qualification, malformed/degenerate
rectangles and wrong source metadata rejection. Existing texture-binding and face
editor Node suites passed. A private Town01 browser loaded an authored 128x128
16-bit TIM at native X=640,Y=32 and received UV [0,32,127,159]. Use filled Target
controls without authoring; Copy/Preview produced exact five-face UV-only changes.
Clipping rejection retained prior drafts. Apply/Save/reload, Undo/Redo, offline Open
and normal Build exact TMD/TIM readback passed, with neighboring decoded model bytes
unchanged. Evidence:
`local-output/sdk-20260909/uv-target-texture-region-20261004/parent/proof.json`.
The picker screenshot was inspected. No game launched; gameplay remains deferred.

## 2026-10-04: Qualified native face highlights in placed scene context

The model face editor now carries a qualified GLB face highlight into **Inspect
proposed faces in scene**. Keep **Highlight GLB face selection (yellow)** enabled
after the readonly model inspection. Both Current and Proposed scene inspection
layers show the selected native surfaces in their existing placed/posed context,
with explicit display-only captions. Shared pose groups retain their source
vertices, geometry keys and instance placement matrices. Other scene assets stay
unchanged. **Isolate inspected instances** is available for shared face proposals;
**Return to face editor** restores the original scene and retains the face review.
A no-change face Preview can inspect the selection in scene without enabling Apply.

Highlights are detached display copies. Scene/project keys, exact effective model
identity, complete native face ownership, triangle/quad counts and geometry-owner
matching are checked before display. Missing/duplicate Current geometry and foreign
proposal geometry reject inspection. Existing source revalidation, review hashes,
Apply/Save/Build and stale-context restoration remain authoritative. This feature
does not infer runtime ownership or prove editor/gameplay coordinate parity.

Verification: focused Node checks covered shared posed geometry, unchanged vertices,
triangles, placements, review hashes and unrelated scene assets, plus stale/foreign
and missing/duplicate geometry rejection. The existing primitive editor suite passed.
A private Town01 browser showed five selected faces in the full placed scene, switched
Current/Proposed, isolated the supported instance and returned with no project/history
change and Apply disabled for the no-change review. It then completed UV staging,
review invalidation, Apply/Save/reload, Undo/Redo, offline Open and exact normal Build
model/TIM readback with unchanged decoded neighbors. Screenshots were inspected.
Evidence: `local-output/sdk-20260909/model-face-scene-selection-20261004/parent/proof.json`.
No game launched; later gameplay verification remains separate.

## 2026-10-04: Readonly GLB native face highlight

After qualifying a GLB material/image face set in the face editor, **Inspect GLB
face selection** opens the ordinary Current/Proposed comparison without requiring
an authored UV change. **Highlight GLB face selection (yellow)** recolors only the
qualified native triangles in a detached display copy. The full model supplies
context, and framing uses the selected surfaces in both views. Turning highlight
off restores the selected-object comparison; the display toggle changes no draft,
material, model bytes or project history. Normal-direction colors and the yellow
selection diagnostic are mutually exclusive. Textures and wireframe remain usable.

The ownership mapping verifies Current object vertex counts, contiguous preview
triangle spans, native triangle/quad counts and complete face membership. A quad
maps to both decoded triangles. Selections across objects retain their independent
local face identities. Stale, duplicate, ambiguous or mismatched layout evidence
is rejected. This is model-local inspection, not live scene/runtime correlation.

Focused Node checks passed triangle/quad ownership, cross-object identities,
unchanged geometry and original previews, isolated display colors, and rejection
of stale/ambiguous/layout-mismatched selections. The existing primitive editor
suite passed. Private Town01 browser evidence verified five native faces/five
triangles in yellow before editing: Preview reported zero native changes and
Apply remained disabled. Highlight/normal-direction toggles preserved project
state. The UV editing workflow then passed review invalidation, Apply/Save/reload,
Undo/Redo, offline Open and exact normal Build model/TIM readback with unchanged
decoded neighbors. Evidence:
`local-output/sdk-20260909/model-face-selection-view-20261004/parent/qualified/visual/proof.json`.
No game launched; gameplay validation remains queued separately.

## 2026-10-04: UV rectangles for GLB-selected native faces

The face editor now offers **Select UV faces from GLB image** inside **Retarget
a UV rectangle**. Qualify an exact Current SDK model GLB and fresh binding JSON,
then choose a material/channel/image. This reuses the native roundtrip and complete
source-corner ownership checks. Choosing the face set selects the new **Qualified
GLB material faces** scope; explicit Source/Target byte rectangles still determine
the UV mapping. Copy stages all selected UVs before publishing any draft. Preview
faces and explicit Apply retain the existing model replacement workflow.

Selections may span packet groups and objects. Draft identity now includes both
object and local primitive index. Existing vertex/RGB/normal-reference drafts and
other face drafts are preserved. The combined draft limit is 256, including the
visible primitive. Current source UVs are mapped afresh; no image dimensions,
texture-page address, GLB shader UVs, clipping or wrapping is inferred. Split
material quads, untextured faces and stale bindings remain ineligible. After Apply,
the face selector is withdrawn until a fresh Current export is qualified.

Focused checks passed cross-object duplicate local indices, preservation of other
drafts, source ownership and atomic failure. The real GLB codec tests passed the
face-editor source adapter; existing UV and model-primitive Node suites passed.
Private Town01 browser evidence passed five-face qualification, UV-only packet
changes, clipping rejection with earlier drafts retained, review invalidation,
Apply/Save/reload and normal Build review. Parent verification passed Undo/Redo,
offline Open, stale binding rejection and exact normal Build model/TIM readback,
with neighboring decoded model bytes unchanged. Evidence:
`local-output/sdk-20260909/model-glb-uv-selection-20261004/parent/qualified/proof.json`.
The first private browser harness expected the face editor to close after Apply;
it was corrected to verify refreshed Current source on a fresh private project.
No game launched; gameplay and live texture residency remain deferred.

Open a model in Edit mode, choose **Edit faces, UVs and colors**, select a
textured primitive and expand **Retarget a UV rectangle**. Choose inclusive
Source and Target U/V endpoints in native byte coordinates (0–255). Source
endpoints must ascend and both rectangles must have nonzero spans. Reversed
target endpoints mirror that axis. Mapping rounds to the nearest byte, with
half ties toward the larger value. This is a coordinate mapping rather than
an image resampler.

Choose the selected primitive or every textured primitive in its packet group,
then **Copy remapped UVs into draft**. Every selected Current corner must lie
inside the source rectangle. No clipping, wrapping, texture address, image size
or material assignment is inferred. More than 256 textured faces rejects the
whole operation; untextured neighbors are excluded. Copy always maps Current
source UVs, replacing earlier UV drafts. The selected vertex/RGB/normal-reference
draft is retained; other group faces retain all their Current non-UV fields.

Use **Preview faces** for the exact source-qualified byte audit and Current /
Proposed model views. **Inspect proposed faces in scene** and **Return to face
editor** preserve the reviewed batch. Changing a rectangle choice or scope
withdraws the old review. Copy again to change the face draft, then Preview.
**Apply reviewed faces** applies the batch as one ordinary model replacement.
All consumers of that model share the edit. Save, reopen, Undo/Redo and normal
Build use the existing project path. Discard or Reset clears neighboring UV
batch drafts; Reset copies Retail values into the selected primitive only.

Retargeting does not resize TIMs or rewrite CLUT/TPage/ABE. Use Resize image and
the source material editor for those separate explicit choices. Runtime
texture windows, VRAM residency, palette animation and final visual suitability
remain deferred gameplay checks. General imported image/material assignment,
new TIM slots and automatic atlas allocation remain unfinished.

## Offline evidence

Two Node guard/lifecycle suites and 17 focused Python cases passed. The private
Town01 fixture remapped object 0 / group 0 of model `scene-tmd/0009`: five faces,
27 changed UV bytes, candidate SHA256
`5066c91047b78013af5c260db03ee1544cf02a562d596ed01d956f91ff1be87d`.
Independent byte construction, reviewed scene Return, one Apply, Undo/Redo,
Save/reopen and exact normal Build carrier readback passed. Neighboring decoded
bytes and source compressed capacity remain unchanged. Visual inspection passed.
Evidence: `local-output/sdk-20260909/model-uv-rectangle-20261004/parent/`.
The proof browser and server closed; game launches: zero. Gameplay suitability
is deferred.
