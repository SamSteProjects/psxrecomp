# Assigning scene texture pages to model materials

In Edit mode, open a model, choose **Edit source material bindings**, select the
target object/group/primitive and expand **Choose a binding from a scene texture**.
**Browse scene textures** reads a freshly qualified active-scene catalog. Choose
a texture and an existing local palette index (zero for direct 16-bit textures),
then **Load texture page bindings**. These actions do not change authored state.
The page list uses the Current TIM, including saved image allocations, and shows
the exact inclusive native UV rectangle covered by each page region.

**Use texture page for selected primitive** copies its page column/row, depth and
indexed CLUT coordinates into the selected draft. **Use texture page for target
group** replaces binding drafts for all its textured primitives as an atomic
batch of at most 256 entries. Other groups, untextured faces, group ABE drafts,
UVs, geometry, normals, source ABR and reserved bits are retained. Direct 16-bit
bindings do not write the model's CLUT word.

Review materials, inspect the Proposed model or scene, Return, and explicitly
Apply. The ordinary material workflow binds the complete resulting model to the
Current scene source and exact effective hash. Apply is one model replacement
with Undo/Redo, Save/Open and normal Build. All model consumers share it.
Loading another texture/palette withdraws loaded binding choices; stale project,
scene, source or mode disables the picker. Copying a binding withdraws review.

Indexed palettes must be complete, aligned to 16 VRAM words and fit the existing
flattened CLUT strip. 24-bit TIMs do not supply native model texture-page bindings.
Large images are split into non-overlapping explicit page regions; assignment
chooses one page region rather than guessing UV wrapping. Use the separate
[UV rectangle editor](legaia-model-uv-rectangle.md) to place faces into that region.

This assigns existing scene texture addresses. It does not introduce a shader,
create a TIM slot, move an image/CLUT, allocate VRAM or infer a general imported
GLB image/material dependency. Static association can remain ambiguous or missing.
Runtime residency, palette animation, texture windows and final appearance remain
in the deferred gameplay queue.

## Offline evidence

Three Node suites and 15 focused Python cases passed. Private Town01 model
`scene-tmd/0009`, object 0 / group 0 (five primitives), was assigned page 12,0
and palette zero of resized `texture://town01/5/raw/0`. Model UVs stayed exact.
The native candidate SHA256 is
`ec156b1d0a825e7c9327d1a2097257e7421b7c81703693b6e2d1fbe8a3a09f3b`.
The texture SHA256 is
`c2b8570e6a8c03ed022462d01d7f3a7b6015a02773bc0acfce0f3693bf7f0482`.
Independent native word-mask construction, Review/scene Return, one model Apply,
Save/reload, runtime Undo/Redo and reopen passed. Normal Build folded the model
overlay into the relocated PROT archive alongside the resized raw texture pack;
exact record/member readback passed for both. Neighboring decoded model bytes
were unchanged. Source entry windows can span adjacent texture carriers, so the
readback qualifies the model section and texture pack rather than claiming its
whole enclosing source window is unchanged by the intentional texture resize.
Evidence: `local-output/sdk-20260909/material-texture-assignment-20261004/parent/`.
Proof browser/server are closed. Game launches: zero; gameplay remains deferred.
