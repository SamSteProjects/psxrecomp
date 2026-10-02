# Existing-layout model content authoring

The model viewer provides **Edit faces, UVs and colors** beside the existing
vertex/normal tools. Select an imported model, object and source primitive.
Edit its object-local vertex references, textured UV byte pairs, or stored RGB
values; lit packets have no authored RGB field. Flat packets store one color
word and Gouraud packets store one per corner. Retail values and Current values
remain separate. Reset to Retail copies only that primitive into a draft.

Preview renders Current and Proposed geometry with the same camera and supports
textures, wireframe, orbit and zoom. The inspected proposal changes no project
history or saved asset. Apply rechecks the current model hash, the complete scene
source key and the candidate hash; changing the draft invalidates its review.
A reviewed proposal can also be inspected across supported instances in the
current authored scene, retaining each instance's existing placement and pose.
Return restores the current scene and the retained face draft.

Apply creates one normal model command. Undo/Redo, Save/Open, Clear shape override,
normal Build review and normal Build use the same source-bound content. Build
reports contain object/group/primitive/corner identities and exact changed source
field values; their links reopen the current face inspector. Download authored
TMD retains both vector and primitive edits. Existing OBJ authoring still requires
its ordered oriented triangulation; shape JSON edits only vertices/normals and
preserves current primitive fields. Whole-object vector operations also preserve
face/UV/color edits. Import a TMD to replace all supported content at once.

## Packet and container contract

The importer supports Legaia relative-pointer TMD header `0x80000002`, flags zero.
Source evidence is pinned to Andrew commit
`d6e64c68ede25813d35db20980da82a1a025549b`,
`crates/tmd/src/legaia_prims.rs` (blob
`75a3b860484e5142bae6457369b593d0d930898c`),
`crates/tmd/src/descriptor.rs` (blob
`7e6afe79b675aaf2c30bf194874686b49f22b4be`) and
`docs/formats/tmd.md` (blob
`ed67864c57ab4653a326ed277303c34b8fbbf90a`).

| Source flags | Packet family | Vertex offset, triangle / quad | Texture block | RGB words |
| --- | --- | --- | --- | --- |
| 0x10–13 | Lit FT | 14 / 12 | 0 | none |
| 0x14–17 | Lit GT | 12 / 12 | 0 | none |
| 0x18–1B | Untextured F | 4 / 4 | absent | one |
| 0x1C–1F | Untextured G | 12 / 16 | absent | per corner |
| 0x20–23 | Baked FT | 14 / 16 | 4 | one |
| 0x24–27 | Baked GT | 22 / 28 | corner count × 4 | per corner |

Offsets are decimal bytes within each payload. Vertex indices encode as
`index × 8` and must fit the source object and unsigned16 offset. UV pairs use
texture offsets **0, 4, 8, 10**: the fourth corner occupies bytes10/11, not12/13.
RGB writes exclude each four-byte word's command/padding byte. The object table,
all nonempty vector tables and complete primitive intervals must be disjoint.
Explicit terminators and declared primitive counts must agree. Every candidate
is decoded again and every changed byte must belong to an audited supported field.

Legacy `tmd-shape` bindings retain XYZ-only validation. New primitive changes use
`tmd-content-v1`; both persist private content-addressed TMD files, retaining the
retail hash and scene source identity. Headers, object/group/packet counts and
strides, normal references, CLUT/page words, GPU modes, footer slots, terminators,
vector padding and opaque bytes stay source-owned. Object-to-animation channels
remain unchanged. Pose composition replaces candidate triangles/colors/UVs while
retaining the verified object prefix, transforms and frame streams. Texture crops
are rebuilt from candidate UV bounds and fixed material keys.

Normal Build composes model members sharing a decoded source container before
one LZS encode. Decoded size and original compressed span remain fixed; independent
decompression checks the complete composed container and capacity overflow rejects.
Supported containers are raw PROT entries, decoded LZS sections and decoded TMD
pack slots. No disc, runtime or reference checkout is modified by inspection.

## Remaining scope

Added/deleted objects or packets, new vector capacity, changed material bindings,
allocator/relocation work, arbitrary mesh conversion, anatomical retargeting,
unknown packet forms and bit-exact runtime lighting/culling are unfinished. The
preview shader does not reproduce retail lighting. Gameplay appearance and model
animation acceptance remain deferred. This workflow is one part of the full SDK;
it does not establish full scene/live-runtime parity or release acceptance.

Private validation evidence is retained under
`local-output/sdk-20260909/model-primitives-20261002/` and excluded from Git.

Validation: 31 selected Python cases passed with the private retail disc enabled
and zero skips; 3 Node suites and 2 changed-module syntax checks passed. Sixteen
actual browser workflows passed with zero page/HTTP errors and zero game-launch
requests, including normal Build review/package/source navigation. Reviewed,
scene, Build and narrow-layout captures were inspected. Town01 model0000 changes
exactly source bytes48/52/62/64; independent package readback verifies the complete
304116-byte decoded container, 154518 encoded bytes within the 154547-byte source
capacity, and unchanged unused encoded tail. Imported metadata is unchanged and
Save/Open retains the exact versioned binding. Vahn idle retains its verified
12-to-10 object prefix and frame coordinates. Gameplay appearance/lighting/culling
remain deferred; no game was launched or package installed. Private evidence is
under `local-output/sdk-20260909/model-primitives-20261002/`.
