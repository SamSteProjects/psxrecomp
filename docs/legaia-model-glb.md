# Source-bound model GLB editing

## Replace mapped objects with per-section native materials - 2026-10-06

**Map GLB section donors** now offers **Replace all existing geometry in mapped
donor objects**. Each selected section first allocates its own group using its
chosen Current triangle donor. Once every section is allocated, the transaction
retires exactly the original Current faces in those mapped native objects. Newly
imported sections survive, unmapped objects remain, and Apply publishes one Undo
entry. Multiple selected objects can be replaced together. Per-section group
replacement conflicts are rejected and disabled in this mode. Native identities,
original vector rows, tombstones and historical allocation budgets remain.

Batch Review, Apply and scene Review accept the strict optional `replace_objects`
boolean. True produces `legaia.model-mesh-batch-review.v2`, with exact
`replaced_object_indices`, `removed_face_ids` and a qualified final `retirement`
stage after all allocation steps. V1 remains supported. Review keys bind the
mode, selected donors, source sections and complete retirement. Editor validators
check the candidate chain, ownership, surviving native render packets and ledger
history; changing the checkbox withdraws Review and requires another Review.
Scene proposals compose qualified existing poses without publishing changes.

Validation: 14 focused Python cases (including Node report mutation checks),
actual browser upload/mapping/Review/Apply, mode-withdrawal checks and inspected
Current/Proposed captures at desktop and 540-pixel widths. A private retail
Town01 model0036 replaced object0's 7 groups / 163 faces with 2 mapped groups /
4 faces, while the other object's 14 packets remained byte-exact. Donors retained
distinct flags `0x15` / `0x25` and CLUTs 31424 / 31434: the lit section imported
normals, the unlit section imported RGB, and both imported UVs. One-step Undo/Redo,
Save/Open, source-project preservation and normal Build native readback passed.

Private Build `d67317911957cd29`; package SHA-256
`f359b62f382c0f1bdf7369926015fd9c39e33dc5fe4dbd58347854e2978c99a3`;
model SHA-256
`e3af801a20dd4191af9d6cf83e2b9566444b99da6d0219e3a00c94189b8748f1`.
Local evidence: `local-output/sdk-20260909/retail-mapped-object-mesh-20261006/`.
No game launch, mod installation or full-disc export occurred. Manual gameplay
acceptance remains queued. This maps existing native material bindings; arbitrary
new images, packet layouts and general animation import remain incomplete.

## Replace complete native object geometry from GLB - 2026-10-06

The mesh importer now offers **Replace donor object geometry** alongside append,
new-group and donor-group replacement. It imports the selected static GLB mesh
into independent groups, then retires every Current face in the selected native
TMD object as one published command. Other objects, object identity and existing
vector rows remain. Retired source/authored faces stay reserved and restorable;
all existing historical allocation budgets still apply. Preserving GLB primitives
creates separate new groups, all inheriting the selected triangle donor's layout
and material binding. This replaces a native object's geometry within a shared
model asset; it does not allocate arbitrary packet layouts, images or animation
channels, or replace every object in a multi-object model in one operation.

V8 Review explicitly identifies the object and complete retired face set. Its key
binds object replacement separately from group replacement, including when both
would yield identical model bytes. Strict booleans, mutually exclusive replacement
choices, independent-group requirements, typed topology/render qualification,
source freshness and reviewed Apply remain enforced. Scene proposals use the
same reviewed choice and compose existing qualified poses. V1-V7 review modes and
existing ledger schemas remain supported.

Twenty-five focused cases passed, including multi-group/copied-object retirement,
other-object ownership, restorability, wrong-mode and forged-review rejection,
one-step Undo/Redo, Save/Open, normal native Build, HTTP scene-review and existing
pose composition. A real browser upload/Review/Apply on a private retail Town01
project replaced model 0036 object 0's seven groups / 163 faces with two groups /
four faces. Object 1's 14 faces remained. Mode changes withdrew Review; desktop
and 540-pixel captures were inspected, including the rendered comparison. A
follow-up read-only browser review held all project files.

Retail normal Build `9014063760bfb107` passed integrity and native model readback.
Package SHA-256:
`1af6201e5b9f1b4c10c9703f6b3731467dd06437fcd9f787926febfdb701be0c`.
Decoded model SHA-256:
`0e5faa86128f2eb9aa1a1124ee5afe152058ef3771ed5c96353dfcaf38fd8380`.
Private evidence: `local-output/sdk-20260909/retail-object-mesh-20261006/`.
No game was launched, no mod was installed and no full-disc export was performed.
Manual rendered/gameplay acceptance remains queued; the larger SDK goal stays
active and solo.


## Retail 512-face delivery and packet allocation performance - 2026-10-06

The expanded mesh capacity now has a private retail normal-Build proof. Town01
model 0036 replaced one 44-face donor group with 512 triangles and 1,536 distinct
new vertices. All 133 retained packets remained byte-exact. The emitted compressed
pack verified all 114 model slots, including existing neighbor overrides, and
held the five other resource sections. Review stayed read-only; one-step Undo/Redo,
Save/Open, imported facts and the source reference project were preserved.

Build `e8d7fab1e309a97f` has package SHA-256
`e931e795d441b30b7b60e37411f6fac82f327aac1e7bc456ee7a17a5364b1fa2`.
Its decoded model SHA-256 is
`b6fe27e3864e721531c55337d387a366bc42b511f1b96755aa5dfc05567d5e59`.
A fresh normal Build with the optimized allocator produced the identical package
SHA-256, with current-input verification and project history held.
Private evidence is under
`local-output/sdk-20260909/retail-mesh-capacity-20261006/`.

Face/group allocation also no longer patches and requalifies an entire model
once per new face. It inspects the immutable source once, reuses the existing
typed operand writer on each bounded packet, and qualifies the complete assembled
model once. Public primitive authoring retains its existing source/candidate
qualification. Packet layout, material/footer ownership, normal/vertex domains,
source hashes and candidate validation remain enforced.

A direct 512-face retail comparison against revision `0963a9c2` produced identical
allocation bytes and audit: one measured allocation took 6.448 seconds before and
0.009 seconds after. Full saved model replay took 0.654 seconds. These are focused
serialization timings, not a gameplay or general editor performance claim.
Forty-three focused tests passed with retail primitive checks enabled, including
all 24 packet families and constant source/final qualification counts at 1 and
512 faces. No game was launched, no mod was installed, and no full-disc export
was performed. Manual rendered/gameplay/performance acceptance remains queued;
the broader SDK goal stays active and solo.


## Authored model capacity expanded to 512 faces - 2026-10-06

The model ledger and native face/group/object allocation paths now allow 512
historically allocated authored faces, including retired identities. The editor
uses one shared face-budget module for GLB bindings, mesh inventory, selected
section Review, primitive/material ownership and topology consumers. Existing
projects and smaller imports retain their schemas and replay behavior. Inventory
can qualify 128 source sections of up to 512 triangles each (65,536 total); one
selected import is still bounded to 512 triangles and the ledger's remaining
face budget. Native vector/address, group, model-byte and carrier-capacity checks
remain independent and unchanged.

A focused exact-limit proof replaced a synthetic Retail donor group with 512
triangles and 1,536 distinct vertices. Editor Review qualification, one-step
Undo/Redo, Save/Open replay and byte-for-byte normal Build package readback passed;
513 triangles rejected before changing the project. A 576-triangle file also
qualified as inventory: selecting 288 triangles passed HTTP Apply/history/Build,
while selecting both sections rejected. Another 47 focused Python tests and seven
JavaScript suites passed. These are synthetic-disc/native serialization proofs,
not a new retail gameplay or rendered 512-face acceptance claim.

No game was launched or controlled, and no full-disc export was performed.
Manual visual/performance verification remains queued. The SDK goal remains
active, with solo offline implementation continuing; arbitrary packet layouts,
new image allocation and general animated mesh retargeting remain incomplete.


## Connected triangle strips

For `TRIANGLE_STRIP` sources, repeated-index connector triangles are omitted before
native allocation. Their original positions in the strip still determine alternating
winding; indices are not compacted before triangulation. Inventory and selected-face
budgets report drawable triangles, so long connector sequences do not allocate faces
or vectors. Strip sources are limited to 16,384 indices and retain the existing
512 drawable triangles per section/transaction limit.

Every source index is validated even when it participates only in connectors.
A section with no drawable triangles rejects. Distinct-index triangles that become
collinear or collapse after native rounding still reject, as do existing malformed
triangle lists/fans. Non-indexed duplicate positions are not inferred as connectors.
The source GLB hash continues to bind the exact reviewed bytes, including connectors.
The [Khronos glTF specification](https://registry.khronos.org/glTF/specs/2.0/glTF-2.0.html)
recommends avoiding degenerate geometry; this compatibility path does not generate it.

## Import a subset from a larger source scene

File inventory qualifies static sections independently from one parsed GLB.
It may list up to 128 sections, each containing at most 512 triangles, with a
maximum total of 65,536 triangles. Every listed section must still qualify;
unsupported or malformed sections reject the file. This inventory does not imply
that all listed geometry can be written into one native transaction.

Each single or mapped mesh import retains its 512-triangle transaction limit.
When a source scene exceeds it, choose one **Source mesh section** or open
**Map section donors** and select a fitting subset. **Review mesh import** remains
disabled for an oversized all-section choice while the picker and mapping dialog
remain available. The batch dialog shows selected triangles against the 512
limit and blocks Review and Select all if the combined choice is too large.
At most 16 sections may be selected in one donor mapping, subject to that same
triangle limit. Existing native object/vector/group budgets also still apply.

The native service freshly qualifies the source and selected geometry before
Apply; it rejects an oversized transaction even if called directly through HTTP.
Review/Apply, scene inspection, source-unit scale, UV choices, one-step history,
persistence and normal Build retain their existing ownership requirements.
Large inventories reuse parsed source data, but maximum-size performance has not
been accepted or benchmarked.

## Choose the sections to import

Open **Map section donors** and check **Import this section** for each section
needed in the native model. The dialog shows the selected count and retains each
source primitive ID; gaps in the IDs do not renumber the source. Select 1–16 rows.
Unchecked rows keep their donor, UV and replacement choices with controls disabled,
and contribute no native vertices, normals, faces, groups or replacement removals.
**Clear selection** unchecks every row. **Select all sections** is available when
the complete inventory fits the 16-section transaction budget.

Inventories with at most 16 sections start fully selected, preserving the prior
all-section workflow. Larger inventories start with none selected and require
explicit choices. The source scene remains bounded to individually qualified sections;
skipping a section does not bypass malformed source geometry or increase those
bounds. This feature selects within a qualified file rather than repairing it.

Selection changes invalidate Review. **Review selected sections** reports both
selected and skipped IDs; scene inspection and Return retain the selection.
**Apply reviewed sections** writes all selected donor mappings in one history
entry. Skipped native donor groups stay unchanged even if their unchecked row
retains a replacement choice. Per-row UVs, fixed source scale, static scene scope,
material RGB choice and source/hash checks retain their existing requirements.

API `mappings` may contain a subset of existing primitive indices, in strictly
increasing order with no duplicates. Reports expose `selected_primitive_indices`
and `skipped_primitive_indices`. Apply binds the complete selection to Review,
even when alternate sections would produce identical native bytes.

## Set the source unit scale

Set **Native units per GLB unit** before Review. The default 1 preserves the
existing native-unit workflow. Choose a smaller factor to shrink a model or a
larger factor to enlarge it. The factor multiplies positions after the complete
source node hierarchy is baked, including node translations, then native Y
reflection and integer rounding apply. It scales around the source scene origin;
it does not recenter or reposition the geometry. Unit normals, UV coordinates,
RGB and source winding keep their existing conversion.

The finite positive range is 0.000001 through 1000000. Native signed coordinate,
vector/face budgets and nondegenerate-triangle checks still apply. Smaller values
can bring oversized source coordinates within range; very small values can make
triangles degenerate after rounding and therefore reject qualification.

Changing the field immediately withdraws Review. Leaving the field requalifies
the chosen scene at the new scale and retains its UV and section choices. A file
that failed coordinate qualification remains loaded so the factor can be changed
and retried. Choose the factor before opening **Map section donors**;
that dialog displays and uses one fixed factor for every section. Scene inspection
and Return retain it. Scale is bound to Review and Apply even when native rounding
produces the same bytes. API callers may pass optional `source_scale` in file
inventory, single import or batch requests; omitted values retain 1.

This is an authored source-unit choice. It does not establish runtime actor/model
coordinate parity or infer game placement units from a GLB.

## Choose a static scene in a mixed file

A GLB may contain static and animated scenes. Choose a source scene whose entire
node hierarchy is static and unskinned. A channel targeting any selected node,
including a parent or a node shared between scenes, rejects this mesh workflow.
A separate animated instance of the same mesh can remain outside the selection.
Selected skin, morph and node-extension data retain their existing rejection.
The geometry-independent catalog keeps other source scenes selectable after an
animated default scene fails qualification.

Animation target ownership follows the standard node/property relationships in
the [Khronos glTF animation specification](https://registry.khronos.org/glTF/specs/2.0/glTF-2.0.html#animations).
This bounded mesh workflow requires explicit existing integer target nodes and
standard translation/rotation/scale/weights paths. Missing targets and animation,
channel or target extensions reject instead of inferring activity. The source
may have at most 64 animation clips, 64 skin records and 256 total animation
channels; sampler references must resolve within each bounded clip.

The dialogs report excluded clip/skin counts. Only activity ownership metadata
is qualified; excluded sampler values, skin payloads and their animation behavior
are not decoded or validated as playable assets. No pose is sampled or baked.
Review binds the exact file, chosen scene and static scope, and retains the normal
native donor, source hash, Undo/Redo, persistence and Build gates. This does not
add animated mesh import or skin retargeting.

## Compare while mapping donors

**Map GLB section donors** shows the mapping controls beside the mesh comparison
on desktop windows. Scroll the section list to reach additional mappings while
keeping the review actions visible. After Review, switch between Current and
Proposed; drag the preview to orbit, use the wheel or +/− to zoom, or use arrow
keys to orbit. Narrow windows stack the controls and comparison in a scrollable
dialog. Scene inspection and Return retain the mapping choices and review.

## Choose the source UV channel

**Source UV channel** lists the selected scene's available channels, with UV0 as
the default. Static imports accept consecutive `TEXCOORD_0` through `TEXCOORD_7`.
Choose a channel before Review. Its values map into each native donor's Current
texture region using the existing bounded texel conversion. Normalized unsigned
byte/short UV accessors decode to their normalized values; float UVs remain valid.
The native donor still supplies its texture page/CLUT and material binding.

The choice applies to the selected section(s) and carries into **Map donors for
all sections**, scene inspection and Return. Changing channel requires another
Review. Changing source scene resets it to UV0. If a section has no selected UV
channel, its donor UVs remain; untextured donors ignore UVs. Reviews report the
textured-face count that consumes the selected values. Other source UV channels
are listed as ignored. A channel choice remains bound to the review key even when
it produces identical native bytes.

Source material `texCoord` assignments are not inferred. For sections needing
different source UV channels, choose the channel in each row of **Map donors for
all sections**. The complete mapping still applies as one reviewed transaction.
The initial file/import UV choice seeds every row; **UV channel for all sections**
resets them together. Changing a row requires another Review, and scene inspection
and Return retain all row choices. Source images, sampler wrapping and new native
texture allocation remain unsupported. Selected coordinates must fit 0..1 when
consumed by a textured donor. Standard UV channel/accessor semantics follow the
[Khronos glTF specification](https://registry.khronos.org/glTF/specs/2.0/glTF-2.0.html#meshes).

## Choose a source scene

The scene picker loads from a separate file catalog before native geometry is
qualified. If the default scene cannot import (for example, its transform has
zero scale), its error is shown while the picker remains available. Select another
scene without replacing the GLB. The same SHA qualifies its native geometry afresh.
The catalog lists names/roots and explicitly makes no geometry qualification claim;
Review/Apply stay disabled until native section inventory succeeds. Selected-scene
inventory must match the original file catalog.

A static GLB can contain up to 64 source scenes. After choosing the file, use
**Source GLB scene** to choose its named scene. The initial selection follows the
file's default scene; if omitted, the first scene is shown. Scene labels remain
source descriptions and do not rename SDK scenes or assets. Only the selected
scene's roots and descendants become mesh sections. Shared source nodes may appear
in different source scenes; each import follows that selected scene's declared
root order and existing transform rules.

Changing scene reloads its sections, resets primitive selection and invalidates
Review. Empty source scenes show no sections and disable mesh Review/Apply; choose
another scene from the same file. File bytes and SHA stay unchanged. **Map donors
for all sections** carries the selected scene into its review, scene inspection
and Return. A new scene choice requires a new review key even if native model
bytes happen to match. Batch Apply remains one Undo entry, and normal Build emits
the selected native geometry.

This imports static geometry into native donor objects. It does not create an SDK
scene or infer actor placement, skinning or animation channels. Source-scene
semantics follow the [Khronos glTF specification](https://registry.khronos.org/glTF/specs/2.0/glTF-2.0.html#scenes).

## Optional material RGB factors

Enable **Bake opaque material RGB factors (unlit donors only)** to multiply each
section's standard `pbrMetallicRoughness.baseColorFactor` RGB by linear vertex
`COLOR_0`. Missing vertex colors are white. The option starts off, preserving the
existing import behavior. It transfers to **Map section donors** and
remains selected after scene inspection and Return. Changing it invalidates Review.
Review displays each source factor and the number of unlit faces that consume RGB.
Lit packets ignore the result, even though the choice still binds the review key.

Textured unlit donors use modulation RGB with neutral 128; untextured unlit donors
use linear-to-sRGB display conversion. Flat donors still require identical corner
colors. Native material and texture bindings remain. Source images, metallic and
roughness shading are not imported. Baking requires OPAQUE mode, factor alpha 1,
opaque vertex alpha and standard materials without extensions. Unsupported alpha
is rejected rather than translated to native blend flags.

The browser checks the original corner colors, section factors and exact linear
multiplication before accepting the existing native color conversion. Batch Apply
is one Undo entry; Save/Open and normal Build retain exact native packet RGB.
This construction evidence does not establish in-game appearance.

Factor semantics follow the [Khronos glTF specification](https://registry.khronos.org/glTF/specs/2.0/glTF-2.0.html#materials).

## Static child hierarchies

Static GLB import now accepts transform-only group nodes and child mesh nodes.
The selected source scene's roots and each node's children are traversed in declared,
depth-first order. Section labels retain the source Node/Mesh and **Path** from
root to mesh. Duplicate children, cycles, multiple parents and roots that also
have parents reject before geometry decoding. An empty selected scene rejects.

Global matrices compose parent-global with child-local, following the
[Khronos glTF node transform convention](https://registry.khronos.org/glTF/specs/2.0/glTF-2.0.html#transformations).
Positions and normals are baked from the composed matrix. Nonuniform parent scale
plus child rotation can produce global shear; its full inverse transpose is
retained. Local matrix inputs must still decompose into TRS without shear, and
all local/composed values retain finite/bounds/nonsingularity qualification.

Section selection, multi-donor Review, scene inspection, atomic Apply/history,
Save/Open and normal Build use the same composed candidate and ancestry evidence.
This transfers static geometry into chosen existing native objects. It does not
create game scene parenting, animation channels or rigs. Skinning, morphs,
animated nodes and new images/material allocation remain unsupported; gameplay
acceptance is deferred. Existing64-node/mesh and128-section bounds remain, with
at most16 sections in one donor-mapping batch.

## Multiple static mesh nodes

The static GLB importer accepts multiple independent root mesh nodes in its sole
scene. The file's root order followed by each mesh's primitive order defines the
section list. Each section shows its Node/Mesh identity, triangle count and material
label. Nodes sharing one mesh remain independent instances; shared position
accessors are not merged across node identities. Each node's static transform is
baked before native rounding.

Select a source section for one donor transaction, or use **Map donors for all
sections** to assign every section to native triangle donors as one Undo step.
Review and scene inspection retain the full source binding. Save/Open and normal
Build deliver the composed native model ledger. Importing nodes does not create
native objects, scene entities or animation channels; those remain determined by
the chosen existing donors.

The source is limited to one scene, at most 64 declared nodes/meshes and 128 source
sections; native geometry budgets remain authoritative and batch mapping admits
at most 16 sections. Only scene roots are instantiated; unused resources do not
become geometry. Duplicate/invalid roots and child hierarchy fields reject.
Skinning, morphs, animation and new material/image allocation remain unsupported.
Gameplay acceptance is deferred.

## Static object transforms

Static GLB mesh import now accepts the sole node's TRS or affine column-major
matrix. The importer bakes translation, rotation and scale before signed native
coordinate rounding. Normals use the inverse transpose; mirrored transforms
adjust triangle order together with the SDK's Y reflection. UV/color/normal
corners stay attached to their source vertices. The original GLB hash and computed
transform evidence remain bound into Review, including section selection and
multi-donor batch imports.

Transform components must be finite and bounded by 1e9; scale columns must be
nonzero with length at least 1e-9. Quaternion length must be within 1e-5 of unity;
it is normalized within that tolerance. Matrices must be affine and decomposable
into TRS without shear. Singular/sheared matrices, matrix plus TRS, coordinate
overflow and triangles degenerate after rounding reject before Apply. Input units
still map directly to native source units; no automatic meter/unit calibration,
node hierarchy, multiple meshes, skinning or animation is inferred.

Transform order and quaternion/matrix conventions follow the
[Khronos glTF 2.0 specification](https://registry.khronos.org/glTF/specs/2.0/glTF-2.0.html#transformations).
The node transform changes imported mesh geometry; it does not move a scene entity
or create native animation channels. Save/Open and normal Build retain the baked
native candidate. Gameplay remains unverified.

## Map donors for all sections

Choose a GLB in **Import GLB mesh**, then **Map section donors**. For
1–16 source primitives, choose a native triangle donor per section. Each section
creates an independent packet group in that donor's object. Optional **Replace
the existing donor group** retires that group; a group used by another section
cannot also be replaced in the batch.

**Review all sections** composes the complete candidate without writing files or
history. Current/Proposed comparison and **Inspect mapped mesh in scene** show the
combined proposal. Return retains the mappings. Changing a donor or replacement
choice requires a fresh Review. **Apply all reviewed sections** publishes one
Undo step; Save/Open and normal Build retain the complete native ledger.

GLB material names identify sections. The chosen native donor supplies packet
layout and material/texture bindings. New textures/images, arbitrary material
allocation and rig/channel creation remain unsupported. Existing native vector,
face, group, operation and metadata budgets still apply. Gameplay is unverified.

## Import a source primitive

In **Import GLB mesh**, choose a file, then select **All GLB primitives** or a
single **Source mesh section**. The list shows each source primitive ordinal,
triangle count and material name/slot. Choose the native triangle donor and packet
group mode, then Review. The proposal summary identifies the selected section;
changing it requires another Review. Scene inspection and Return retain the choice.
Apply uses one Undo entry. Save/Open and normal Build deliver the resulting native
model ledger, as with whole-mesh imports.

A section can be imported with its own chosen native donor in a separate reviewed
transaction. Source material names are labels; GLB textures/images and arbitrary
material allocation are still unsupported. Other source primitives are omitted
from a selected-section transaction; existing native geometry follows the chosen
Append/New/Replace group mode. All-file inventory remains bounded by the current
static GLB importer limits. This is offline authoring; gameplay is not verified.

The model GLB workflow imports existing object-local vertex positions, UV
coordinates, qualified baked RGB, existing vertex/normal references, stored
normal XYZ and qualified material fields into the SDK's normal model replacement path. It complements
animation GLB editing: mesh edits change the model asset, while animation edits
change rigid pose channels. Actor placement and source mesh coordinates remain
separate. Shared model edits can affect several recorded instances.

GLB container, mesh accessor and custom attribute semantics follow the
[Khronos glTF 2.0 specification](https://registry.khronos.org/glTF/specs/2.0/glTF-2.0.html).
Source packet ownership follows the pinned Andrew reference and existing
[primitive authoring qualification](legaia-model-content.md).

1. In **Edit** mode, choose an imported model and open **Edit model through GLB**.
   Choose the asset's exact source scene when navigating from project inventory.
2. Use **Prepare GLB export**, then download both **GLB** and **binding JSON**.
   The export describes the current effective, unposed model, including existing
   authored model changes. Keep the binding JSON unchanged with its GLB.
3. Import the GLB into Blender with **Merge Vertices disabled**
   (`merge_vertices=False`). Edit existing mesh positions or UVs. Keep node
   identities, object layout, original triangle connectivity and custom source
   attributes. Do not add, delete, weld, dissolve or replace geometry.
4. Export glTF Binary (`.glb`) with **Custom Attributes enabled**
   (`export_attributes=True`) and **Custom Properties enabled**
   (`export_extras=True`). Retain UV export and the existing coordinate conversion.
   Keep the model unposed and avoid object hierarchy or transform changes.
5. Back in the SDK, select the edited GLB and its original binding JSON, then
   **Review selected files**. Review lists changes from Current separately from
   all changes relative to Retail, plus source/current/proposed hashes and
   quantization diagnostics. Existing authored RGB, normal, face-reference or
   other supported model edits remain part of Current.
6. Use **Inspect proposed model** to inspect the qualified candidate through
   the existing model preview. **Apply reviewed model** requires that exact
   reviewed pair and unchanged source context. Selecting another file or changing
   project/model context invalidates review. A no-op import has nothing to Apply.
7. Use ordinary **Undo/Redo**, **Save/Open** and normal **Build** for the resulting
   model replacement. The existing serializer preserves source container
   capacities and audits changed fields. Build evidence does not establish
   gameplay or runtime rendering acceptance.

Export a fresh GLB/binding pair after source or project changes. The SDK
regenerates the authoritative profile from freshly verified current bytes;
client-provided GLB extras and binding fields do not establish source ownership.
The binding identifies the model, imported scene, retail hash, effective hash,
project source key and source profile. A stale or foreign pair rejects before
authoring. Review and proposed inspection do not change history or saved files.

The transport retains `_LEGAIA_SOURCE_VERTEX` and `_LEGAIA_SOURCE_CORNER` as
custom numeric attributes. Node `source_object` metadata identifies the source
object. A vertex ID is an object-local source ordinal; a corner ID is
`primitive_index * 4 + source_corner_index`. IDs must remain exact integers.
The importer validates source-qualified corner topology instead of matching by
position, nearest neighbor, vertex order or material name.

GLB render vertices can split one source vertex into several points for UV or
color seams. Every copy of one source position must agree. Retail quads are
represented by their existing two triangles; duplicated source corners must
also agree on UV values. Editing only one seam copy creates conflicting values
and rejects rather than silently averaging them. Blender's Merge Vertices option
can discard differing custom corner attributes even when it retains geometry,
so it is outside the supported workflow.

Coordinates retain source units, with the SDK's established Y reflection for
glTF display; physical meter scale is unknown. Positions quantize to signed
16-bit source values, and UVs to existing byte values. Review reports rounding
error. Source field ranges and fixed layout still apply after quantization.
Rounding uses the nearest integer with half ties to even. UV endpoint excursions
within `1e-4` byte units account for float32 conversion; larger raw overflow
rejects. Quantized component counts refer to unique source components and
ignore numerical errors of `1e-5` units or less; maximum error remains visible.
The source profile supplies UV conversion for the represented material; an
unmatched texture is not evidence that its source UVs can be guessed from a
different image.

`COLOR_0`, shader/material assignments and image pixels are not imported.
Fresh profile v6 accepts explicit source material words through
`_LEGAIA_SOURCE_MATERIAL`; see [material GLB editing](legaia-model-glb-materials.md). Use the profile v2 raw `_LEGAIA_SOURCE_RGB` attribute to edit existing baked RGB
(see [RGB workflow](legaia-model-glb-rgb.md)); display color remains separate.
Packet counts, vector padding, source allocation and opaque bytes stay unchanged.
Existing normal words and references use the source-bound profiles documented
in [normal editing](legaia-model-glb-normals.md) and
[normal references](legaia-model-glb-normal-references.md). Blender may
generate render normals, but those are not identities for TMD normal-table
entries. Use the existing model face/color editor or texture authoring workflow
for their supported source fields. This lane does not add objects, topology,
materials, textures, skinning or runtime lighting support.

The service accepts a GLB up to 32 MiB and a bounded binding JSON up to 128 KiB
in the browser workflow. Export, Review, proposed inspection and Apply use the
`/api/model-glb-export`, `/api/model-glb-preview`,
`/api/model-glb-pose-preview` and `/api/model-glb-import` routes. Review binds the
GLB hash and proposed TMD hash to the exact current source. Apply revalidates
that result and uses the ordinary model replacement command.

Private interoperability evidence is under
`local-output/sdk-20260909/model-glb-20261002/research/`. Blender **5.2.2 LTS**
(`d13f752e3b9c`) imported and re-exported retail Dolk2 model 0133 with 10 objects,
167 source vertices, 190 source primitives, 91 quads and 281 rendered triangles.
The identity attributes and source material extras survived with merging off
and attribute export on. All 661 source corners and their original oriented
triangle multiplicities remained qualified. Position error was zero; maximum
UV error was approximately `2.98e-8` in normalized coordinates.

The no-op Blender export reconstructed the identical 6,672-byte source TMD with
zero audit changes. An independent edit moved source vertex 27's X by one unit
across ten split points and changed primitive 50/corner 2's U by one byte across
both quad triangles. The existing writer reported exactly those two fields and
preserved every other byte. This fixture has no source normals, so it does not
prove a normal-authoring inverse.

Negative probes established the restrictions: enabling Merge Vertices lost 494
source corner identities; disabling Custom Attributes removed both IDs.
Top-level GLB document extras were lost on re-export, while node extras survived.
Display `COLOR_0` changed by as much as `0.3125` in linear space on the unchanged
mixed-material fixture, which is why this lane preserves effective RGB.
The successful probes used a private Blender user-resource directory; no game,
installation, reference modification or user project write was involved.

Parent integration also passed 14 focused Python cases with the private disc,
the Node workflow suite, both frontend syntax checks and 12 browser checks.
The browser downloads a freshly qualified pair, reviews the actual Blender
no-op/edit, renders the proposed model, retains exact selected Files on Return,
rejects stale/no-op Apply, applies one ordinary command and exercises Undo/Redo,
Save and normal Build. The review fits 540px with internal scrolling. Page/HTTP
errors and game-launch requests were zero.

A fresh production SDK export independently passed the same actual Blender
roundtrip. Reopening the saved browser project and decompressing its package
reconstructs the exact two-field candidate, with unchanged neighboring decoded
bytes and the original 118,461-byte compressed span. Parent proof and the saved
project/package are under `local-output/sdk-20260909/model-glb-20261002/parent/`.
The candidate SHA-256 is
`186b8176a298302d6834b584a3eb57ddc6c2b9ff5bc2fbd852f92fc95fa1da84`.
These tiny edits establish byte integrity; they do not establish perceptible
gameplay appearance. Later manual acceptance must use matching source/build
provenance and check model/UV rendering and shared instances. Arbitrary topology,
general material replacement, runtime lighting and full SDK parity remain pending.

Profile v2 RGB support and later flat/Gouraud Blender, browser and Build evidence
are documented in [the RGB workflow](legaia-model-glb-rgb.md). The original
positions/UV milestone below remains historical evidence for its own source.

Fresh profile v3 also supports [existing face rewiring](legaia-model-glb-faces.md).
Fresh profiles v4/v5 add existing normal words and references, and v6 adds
qualified CLUT/TPage/group ABE words. New polygons and source allocation remain
outside GLB import. Earlier position/UV and RGB milestones retain their dated evidence.

## Face-removal bindings

Models with `tmd-face-removal-v1` overrides now use `legaia.model-glb-binding.v2` sidecars and `legaia.model-glb-review.v2` reviews. Each carries the exact sorted removed Retail identities. Export and import profiles bind the reduced Current packet layout, while final candidate qualification uses actual Retail bytes and that removal set. The review includes every removed Retail face exactly once and permits only supported typed Current fields as pending edits. V1 bindings remain valid for models without removal. Export again after any source/removal change; GLB topology insertion/allocation remains unsupported. Apply uses the ordinary model override/history/Build path and retains prior material/reference edits. Native gameplay appearance remains deferred.

## Frame imported geometry

Both the single-donor importer and Map GLB section donors expose **Camera
framing** after Review. **Shared visible geometry** keeps Current and Proposed
at one common scale. **Visible geometry in this layer** frames only vertices
referenced by its rendered triangles, making replacements easier to inspect
when retired geometry leaves unused native vectors. **All stored vertices in
this layer** includes those unused rows. **Frame mesh** resets zoom without
resetting orbit. Switching layers or framing preserves the reviewed candidate;
these camera controls do not author coordinates, change native bounds or add
history entries. Other surviving objects remain part of the visible model frame.

## Position imported vertices with a native origin

Set **Native origin offset** X/Y/Z in the GLB import dialog before Review or Map
section donors. The origin is added in native model units after baked GLB node
transforms, unit scaling and `[x,-y,z]` conversion. Native Y increases downward.
Changing an offset withdraws Review and rechecks source geometry, retaining the
chosen source section and UV channel. The mapped-section dialog displays and
uses the same origin for every selected section; change it in the import dialog
before mapping. Review reports the exact chosen XYZ offset. Apply stores the
resulting native vector coordinates with the ordinary topology command/ledger.

Offsets may be fractional; positions round after translation. Each component
must be finite and within -32768..32767, and final positions must fit that range.
Rounding can collapse a triangle, which rejects Review. Offsets do not move scene
entities or change normals, UVs, colors, winding or node-transform provenance.
All instances of the shared model inherit its imported geometry. Zero preserves
older behavior. The API's optional `source_offset` is a three-number XYZ array,
bound through inventory, Review, scene Review and Apply. Different nonzero
offsets require fresh Review even if their rounded native candidates match.

## Orient imported geometry

Set **Native import rotation (degrees)** X/Y/Z before Review or Map section
donors. Angles use native model axes (Y increases downward), rotating X, then Y,
then Z with active right-handed matrices. Conversion order is baked GLB node
transform, unit scale, `[x,-y,z]`, native rotation, native origin offset, and
integer rounding. Positions rotate around the native origin; offset is added
afterward. Normal directions rotate with the mesh before Q12 conversion. UVs,
colors and oriented winding retain their existing source interpretation.

Angles may be fractional and must be finite within -360..360 degrees. Final
coordinates still must fit signed native storage; collapsed rounded triangles
reject. Changing angles withdraws Review and refreshes inventory, retaining
selected section/UV choices. Map section donors uses one common orientation
chosen in the import dialog. The optional API `source_rotation` is an XYZ array
bound through inventory, Review, scene Review and Apply. A full turn still needs
its own Review key, even if bytes match zero rotation. Zero preserves earlier
behavior. Rotation changes shared static model geometry, not actor facing,
animation channels or retail node provenance.

## Recovering original mesh inputs

After a reviewed single or mapped import, reopen **Import GLB mesh** and choose
**Retained mesh sources**. Each Current receipt offers its original GLB and an
import-settings JSON download. The settings include scale, native XYZ rotation
and origin, source scene/section/UV choices and donor/replacement options.
Historical donor IDs are evidence of that import, not automatically reusable
Current donors. Reimport requires choosing valid Current donors and Review.

The project retains hash-named originals in `Authored/Models/Sources` and binds
receipts to native ledger spans. Save/Open and later native edits preserve the
inputs. Undo removes the Current receipt; Redo restores it using retained bytes.
Missing/changed GLBs or recipes fail qualification and Build. Retained originals
are project sources, not runtime package assets. Older imports have no retained
original unless they were applied again through this workflow.

## Retained mesh and texture sources - 2026-10-06

Editable copies and saved export input snapshots now include original GLBs
referenced by Current model import receipts. Hash-named files under
`Authored/Models/Sources` are qualified and copied with the native TMD and ledger.
Shared originals appear once in the captured inventory. Retained texture PNGs
and GLBs are also accepted by the editor copy inventory and saved-copy discovery.
The existing 512-file/256-MiB copy limits include these inputs.

Open the copied project, choose **Import GLB mesh > Retained mesh sources**, and
download the same original GLBs and settings. Missing or changed sources reject
copy review/creation before a completed copy is published. Unreferenced files
and inputs reachable only through excluded Undo/Redo history are not copied.
Review and Copy still preserve the original project's metadata, dirty state and
history. Retained original inputs remain project sources, not runtime Build
assets. Older snapshots created without mesh sources are not repaired implicitly.

The same capture routine serves export input snapshots and editable recovery
copies. Synthetic snapshot/recovery checks do not generate a retail disc export.


## Renamed or reordered source object nodes

The fixed-layout **Edit model through GLB** workflow now accepts readable node
names and reordered node/mesh indices when exported
`extras.source_object.object_index` tags are preserved. Source tags identify
native objects; readable names do not create semantic object identities.
Unnamed tagged nodes also work. If a tag is absent, preserve its canonical
`object-N` name. A canonical name that contradicts a tag rejects, as do malformed,
duplicate or out-of-range tags. Renaming untagged nodes remains unqualified.

Retain all source vertex/corner/normal/material attributes, their repeated aliases,
the source scene and existing native layout. Static rigid transforms and parent groups are now baked as described below; this
does not allocate geometry. Use a fresh binding, Review,
Inspect proposed model, close to Return, then Apply. GLB image-to-native-face
selection uses the same object resolver after qualifying the complete unchanged
native model. The ordinary command, Undo/Redo, Save/Open and Build paths apply.


## Bake static rigid object transforms and parent groups

Fixed-layout **Edit model through GLB** now accepts static translation/rotation
TRS and affine rigid matrices on source objects and their parent groups. Matrices
and TRS cannot be mixed on a node. The selected source scene must contain every
node and each existing native object exactly once; up to 1024 nodes are allowed.
Preserve source-object identities and all source corner/vector attributes.

Parent-first composition bakes each represented POSITION into native object
coordinates. Stored normal attributes are raw native XYZ words: the importer
converts them to GLB axes, rotates them by the composed orientation, then converts
back and quantizes without normalization. Translation does not change normals.
Unlit sentinel attributes, unrepresented native vector slots, padding, packet
layout and opaque bytes remain intact. Display NORMAL remains ignored. Aliased
corners must agree after transformation and source-domain quantization.

Local matrix shear, perspective, skinning, morphs, animation, cycles,
multiple-parent trees, detached nodes and unowned meshes reject. Rotating lit
objects with an old profile that cannot author stored normals rejects; unlit
legacy objects and translation-only imports retain their supported field scope.
Use Review, inspect the proposed model, close to Return, then Apply. Undo/Redo,
Save/Open and normal Build use the existing native replacement pipeline. These
are geometry edits and do not move scene instances or establish retail lighting.


## Bake positive uniform model scale

Fixed-layout GLB editing accepts positive uniform scale on source object nodes
and their parent groups, through `scale: [s,s,s]` or a uniformly scaled affine
matrix. Local scales and every composed ancestor scale must stay in
`1/1024..1024`. This bounds the interchange transform; represented native vectors
must also fit their existing signed-i16 domains after quantization.

Scale composes with rotation and translation in glTF order. A parent scale
multiplies child translations as well as mesh positions; a node's own scale does
not multiply its own translation. Raw stored normal magnitudes are preserved;
only composed rotation affects them. Fractional position results round through
the existing reviewed quantization diagnostics. Unused native vectors, packet
layout, padding, image/material fields and unlit sentinels remain unchanged.

Uniform matrix decomposition uses the existing rigid orientation checks with
float32 tolerance. Zero TRS scales, local matrix shear, perspective,
matrix-plus-TRS and excessive composed scales reject. Positive nonuniform scale
is supported as described below.
Animation GLB imports retain their existing unit-scale requirement. Scene
placements are separate authored values. Use a fresh binding and the ordinary
Review/Pose/Return/Apply, Undo/Redo, Save/Open and normal Build workflow; gameplay
appearance remains deferred.


## Bake positive nonuniform model scale

Source object and parent TRS scales may now differ across X/Y/Z. A local affine
matrix may likewise contain positive nonuniform axis scale and rotation; it must
still decompose into TRS. The importer composes full linear matrices, so a rotated
child under a scaled parent retains the resulting composite shear. Shear in an
individual local matrix remains rejected under the
[glTF node transform rules](https://registry.khronos.org/glTF/specs/2.0/glTF-2.0.html#transformations).

Positions receive the complete composed matrix and translation. Raw stored normals
receive its inverse-transpose direction, restored to their original vector
magnitude before signed-i16 quantization. Zero normals stay zero. Uniform-only
hierarchies retain the earlier rotation path and exact source behavior. The
native/GLB Y conversion, unlit sentinels, shared source aliases and unused vector
preservation remain in force. The viewport still does not prove retail lighting.

Each positive local axis is bounded 1/1024..1024. Every composed node transform
must have singular scales in that same range. A bounded one-sided Jacobi
measurement works directly on matrix columns, preserving small-axis precision
without forming squared normal equations. Reciprocal/cross-axis cancellation is
accepted when the actual composed transform stays bounded; out-of-range
intermediate ancestors still reject. Only floating-point boundary noise is
allowed (64 ulps of the largest measured scale). Native integer-domain and
quantization checks remain separate. Zero scales, perspective, local matrix shear, animation
and skinning remain unsupported. Legacy lit profiles without stored-normal
editing reject nonuniform transforms; unlit legacy geometry remains supported.

Use fresh binding, Review/Pose/Return/Apply, Undo/Redo, Save/Open and normal Build.
These edits change native model geometry, not scene-instance placement or native
animation formats. Gameplay appearance and lighting verification remain deferred.


## Explicit external model object mapping

When an external tool removes source-object extras and renames object nodes,
enter GLB node indices in native object order in the model GLB dialog. For two
native objects whose nodes are 3 and 1, enter `3, 1`. The node inventory lists
indices, display names and mesh/group status. Blank uses preserved tags or
canonical `object-N` names, or an existing binding mapping.

The optional binding field `external_object_nodes` is an ordered list with one
distinct integer node index per existing native object, within 0..1023. Include
empty native objects as well as mesh objects. Mapped nodes must be reachable in
the selected scene, and every mesh node must be owned. Preserved source tags and
canonical names must agree with the chosen mapping; the mapping cannot override
conflicting provenance. Source corner/vertex attributes, topology, aliases,
materials, capacities and transform bounds still qualify the entire native TMD.
This supports external organization of the existing layout, not arbitrary meshes
without source attributes, allocation, skeletal retargeting or skinning.

Review seals the complete mapping choice alongside GLB content, regenerated
source profile and proposed native bytes. Changing only the mapping invalidates
Review even when candidate bytes are identical. The dialog withdraws Review when
mapping text or files change, retains the chosen mapping through proposed-model
inspection and Return, and requires explicit Apply. Material-face selection uses
the same mapping after an exact native no-op qualification. Use normal Undo/Redo,
Save/Open and Build; gameplay rendering and lighting remain deferred.


## Recover original model GLB imports

After a successful Apply, open the model's GLB dialog and choose **Recover model
inputs**. Download the original uploaded GLB, its original binding JSON (including
explicit object mapping) and its import receipt. Downloads check the original
file's SHA-256 and byte length. Retained source inputs survive subsequent native
model edits; they describe the historical import, not the current model.

Native content and input metadata share one Undo/Redo step. Save/Open, project
copies and Build input snapshots retain registered sources. The project supports
32 model import receipts and 64 MiB of distinct original GLBs, with a 32 MiB limit
per GLB. Receipt metadata removal is available through Review and explicit Remove in the
retained model inputs dialog. It creates one Undo/Redo step and preserves the
authored model and original GLB file. Review must be repeated if project or receipt
state changes. Shared blobs release registered budget only after their last
receipt is removed. Physical orphan cleanup remains open. The Project model
inputs button provides recovery and reviewed removal across all recorded scenes,
with scene filters and search by model identity or hash. It does not require
selecting the original scene/model. Downloads verify the saved GLB before
returning its original binding or receipt; export a fresh binding for a new Apply.
Files may remain as unregistered cache entries after Undo or a failed publication.

An old binding is intentionally stale after edits. Recover original inputs for
external editing, export a fresh binding from Current, preserve source attributes
and choose the mapping appropriate to that GLB, then Review again. No receipt
silently replays changes or authorizes native/runtime writes. Gameplay rendering
and lighting acceptance remain deferred.


From Project model inputs, choose Open model in source scene to inspect the current
model. This verifies the saved receipt, opens its imported scene and checks that
the model is still present. Authored geometry is shown when a native override exists;
otherwise the inspector shows Retail. Use Edit model through GLB and Prepare GLB
export to obtain a fresh binding before editing again. Navigation preserves receipts
and authoring history; explicit export creates normal files under Exports. Finish
or discard pending model edits before navigating to another source model.


Use Compare current native model on a saved input to check whether its historical
native result still matches the model currently in the project. The SDK verifies
the Retail disc and native model bytes in that receipt's source scene, even when
another scene is open. The result labels current Retail or authored content and
shows its hash/size. A difference means the current native model no longer matches
that historical result. A match proves byte equality only; use a fresh export and
Review for a new edit. Comparison does not change project state or create an Undo
step. The matching retail disc is required for comparison, while saved input
recovery remains available separately.


## Bake mirrored model transforms - 2026-10-06

Export Current through Edit model through GLB, retain the fresh binding and source
attributes, and apply signed nonzero node scale or a static reflected matrix in
your external editor. Parent groups, renamed source-tagged objects and explicit
object mapping retain their usual ownership rules. Review selected files, inspect
the proposed model, return and explicitly Apply. Undo/Redo, Save/Open and normal
Build include the result and retain the original GLB input receipt.

The current v6 profile supports mirrors by baking the full composed transform
and reversing the native face corners when its determinant is negative. This
follows the [glTF transform/winding rule](https://registry.khronos.org/glTF/specs/2.0/glTF-2.0.html#instantiation).
The native implementation exchanges corners 1 and 2 for triangles and quads,
retaining the quad diagonal. UVs, Gouraud RGB and normal-reference words follow
their vertex corner; flat fields and all material/command/padding bytes keep their
owners. Normal directions use signed inverse-transpose transformation with their
original source magnitude restored before integer rounding. This magnitude policy
belongs to the native SDK and is separate from glTF display normals.

An even number of reflections that cancels in the final transform does not reverse
native winding. Each local scale magnitude and composed singular scale remains
within 1/1024..1024. Zero/singular transforms, overflow, local matrix shear,
skinning and animation reject. Older profiles cannot import a reflected object;
export again using Current. Keep source triangle identities and their original
GLB index winding; the SDK applies determinant-based native winding correction.
Do not reverse the GLB source indices yourself. This creates a reviewed native
replacement without allocating new objects, vectors or packets. Gameplay rendering
and lighting acceptance remains deferred.


## Recover verified native-mesh import settings - 2026-10-06

Open an authored model from the resource browser, choose Import GLB mesh, then
Retained mesh sources after its source has loaded. Download original GLB, Download
import settings JSON and Download import receipt each freshly qualify the saved
native import and source file. The settings file contains the original single or
batch recipe, including source scene/section choices, orientation, scale, origin,
UV channel and donor choices. The receipt also contains source and native-ledger
hashes. A missing/changed file or changed Current context rejects the download.
Closing recovery cancels pending requests; no later file is published from that
closed panel. Settings are historical evidence. Choose Current donors and perform
a fresh Review before a new Apply; downloading them does not change project state.

## 2026-10-06: recovered mesh settings become editable drafts

`Import GLB mesh` now accepts the bounded JSON downloaded by `Retained mesh sources` after a GLB is chosen. Single settings restore scene/section, unit scale, XYZ origin/rotation, UV channel, color choice and packet-group mode. Batch settings open the section donor editor with saved section selection, per-section UVs and group/object replacement choices. Both paths request a fresh SDK inventory of the selected GLB before publishing controls, clear any previous Review, and require fresh Review plus explicit Apply. Unavailable Current triangle donors remain unselected; no donor is substituted. Unknown fields, invalid bounds, missing sections/scenes/UVs and conflicting mappings reject.

Validation: new Node settings decoder/qualification checks and the existing recovery/download Node checks passed; all five Python mesh source retention/history/HTTP tests passed. Actual browser checks restored both saved recipes, rejected malformed settings without changing draft choices, required missing-donor reselection, and completed fresh single and mapped Reviews. No Apply, project/history/file mutation, game launch, runtime attach or installation occurred. Wide and narrow screenshots inspected. Evidence: `local-output/sdk-20260909/mesh-settings-draft-20261006/proof.json`. Gameplay acceptance remains deferred; the full SDK goal is incomplete.

## 2026-10-06: project-wide retained mesh input library

The editor now offers `Project mesh inputs` alongside the model and animation input libraries. It finds retained native mesh import GLBs and their historical single/batch recipes across source scenes, filters by scene/model/hash/import kind, recovers original GLB/settings/receipts and opens the Current model in its source scene. The SDK reconstructs each model's retained ledger inputs within a verified disc operation. Complete project/import/native context seals the library key; downloads verify fresh membership, exact receipt, byte length and independently hashed GLB. Navigation requalifies before and after changing scenes. This is read-only recovery: settings remain editable input requiring fresh Review and explicit Apply. The library supports at most 128 receipts and 64 MiB of distinct registered GLBs and refuses larger catalogs without truncation.

Validation: three new Python library checks plus five existing mesh retention checks passed, including HTTP exact-field rejection, stale project/key/mode, corrupt input, late context mutation, global budgets and no project/history/file changes. Node library decoding/filtering, exact recovery, hash-time context and qualified scene navigation passed. Actual browser proof started in `town0c`, recovered all six artifacts from two `town01` imports, filtered single/batch inputs, opened the source scene's exact authored model and verified its native SHA-256. No page errors; wide/narrow library and Current model screenshots inspected. Original and private project files, native receipts and Undo history stayed unchanged; scene selection changed as requested. Evidence: `local-output/sdk-20260909/mesh-input-library-20261006/proof.json`. No native Apply, Build, game launch, runtime attach or installation occurred. Gameplay acceptance and the full SDK goal remain open.

## 2026-10-06: Current native mesh import comparison

`Project mesh inputs` now compares each historical receipt with the complete Current native model and reports how many faces introduced by that import are active or retired. The reader requalifies the library and retained input, replays exact before/after ledger spans, checks the historical candidate hash and Current replay bytes, and seals receipt/root/mode/import/native/disc context before returning. The UI validates exact response fields and hash/count consistency. A whole-model difference can reflect later edits or imports; active face identities do not assert unchanged face content or gameplay acceptance. Comparison requests are read-only and require no active source scene change.

Validation: five focused Python checks passed (three library regressions and two comparison workflows), with the two comparison checks rerun after the final model-byte bound. Exact match, later-import difference with all original faces active, one-face retirement, Undo restoration, HTTP exact fields/stale receipt/root/key and context drift reject paths passed. Node library/comparison validation, hash truth, bounded face totals and no-write claim checks passed. Actual retail-backed browser comparison ran from another scene and matched complete SDK responses and displayed counts for a single import (1 of 2 active, 1 retired) and batch import (4 of 4 active). Independent baseline showed the batch's exact native match, and Undo restored it after private fixture retirement. Comparison reads preserved project document/history/files; original project untouched. Wide/narrow screenshots inspected. Evidence: `local-output/sdk-20260909/mesh-native-comparison-20261006/proof.json`. The private fixture used a qualified native face retirement and Undo to exercise lifetime reporting; no Build, game launch, runtime attach or installation occurred. Full SDK and gameplay acceptance remain incomplete.
