# Source-bound model GLB editing

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
