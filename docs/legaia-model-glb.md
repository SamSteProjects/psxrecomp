# Source-bound model GLB editing

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
existing import behavior. It transfers to **Map donors for all sections** and
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

Choose a GLB in **Import GLB mesh**, then **Map donors for all sections**. For
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
