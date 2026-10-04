# General model topology allocation work

The new allocation reader reports qualified native packet/vector extents for
Retail and Current. In the model viewer, choose **Inspect native allocation**,
then select **Allocation layer** and **Model object**. **Stored packet groups**
expands the group counts, offsets and packet strides. The dialog is also backed
by `sdk.model_allocation.source`. It does not allocate or edit bytes.

Each object's report identifies group offsets, counts and packet strides; the
explicit terminal word; the primitive-stream boundary; and vector-array extents.
Bytes after the terminator remain uninterpreted. Compaction can leave old packet
bytes there, so neither their presence nor a zero value authorizes reuse.
Source qualification rejects aliased spans, missing terminators and mismatched
native primitive counts. The SDK source service additionally checks source
freshness and Edit mode and returns detached metadata within its report budget.

Fresh Town01 scene-TMD model0009 has four objects with Current primitive counts
65/11/9/18. Each stream reaches its vector boundary with zero tail bytes. The
Current and Retail model lengths are equal, and independent raw-header reads
agree with the report. The proof preserves all saved project bytes. Source SHA256:
`0c659a9ee764c57c83c176d52abc0ac8e392349dd27d3db8b9a96c786945cefe`.
Private evidence: `local-output/sdk-20260909/model-allocation-20261003/parent/`.

General face addition remains required. It needs an authored identity separate
from Retail primitive indices, an explicit topology binding, and packet packing
that preserves native group descriptors and footer ownership. Counts must change
in both group headers and object tables. Any moved vector/group offsets must be
rewritten consistently, and carrier neighbors must remain independently verified.
The current same-length content and Retail-removal bindings cannot represent that
change. Removal-derived spare space alone is not a general allocation solution.

The allocation Inspector is connected and source-qualified. A model-level packet
growth codec is now implemented. The next integration is a durable topology
binding and carrier relocation path. Review/Apply, history,
Save/Open, preview, GLB and normal Build need that same identity model. Native
appearance, pose/culling and shared-instance acceptance remain later gameplay
checks; successful source inspection is not evidence for those behaviors.


Inspector validation checks detached metadata, source hashes and identity,
stream/terminator/tail equations, group continuity/count sums, vector extents
and global span overlap. Retail and Current are checked independently, so the
read-only metadata model does not assume equal byte lengths for future relocation.
Stale or late requests cannot populate another source context. Closing aborts
inspection and releases its busy state. The HTTP endpoint accepts only model
identity and current source key; it offers no Apply or allocation command.

Six actual retail browser/HTTP checks verified all four Retail/Current objects,
packet-group disclosure,540px layout, source agreement and invalid requests.
Project files, authored state and history remained unchanged. Private UI proof:
`local-output/sdk-20260909/model-allocation-inspector-20261003/parent/`.


## Native packet-growth codec

`importer.model_face_addition.add_model_faces` accepts a verified source hash
and1..128 new authored face requests. Each names a canonical `face://authored/`
UUID, existing object/group and donor primitive, and typed fields including
vertex references. UV/RGB/normal fields use the existing source-qualified field
writer. Vertices and normals must already exist; arbitrary new vector/object/
group allocation is still unfinished. Donor formats preserve material and opaque
command bytes. A donor must belong to the chosen group.

New packets are inserted before that group's footer. Group and object primitive
counts update, active object-table offsets rebase relative to the12-byte header,
and existing source bytes retain their order. Unused vector pointer words stay
unchanged. The audit separates new UUID identities from retained source indices
and records Current primitive indices, packet hashes and pointer relocations.
Complete qualification recomputes the exact candidate and rejects unowned edits.
The4MiB source-model limit and native16-bit group count remain enforced.

Pinned evidence: unchanged Andrew `d6e64c68ede25813d35db20980da82a1a025549b`,
`docs/formats/tmd.md` and `crates/tmd/src/legaia_prims.rs`: relative object-table
pointers and group length `8 + (count + 1) * stride`, including the footer slot.
The codec preserves footer bytes rather than treating them as available space.

Independent Retail Town01 model0009 reconstruction adds a quad to object1/group0
(flags0x13, stride24), growing4704→4728 bytes. The new packet inserts at3160 and
uses vertex indices1/2/3/0; Current primitive index11. Candidate bytes agree with
independently rewritten headers/pointers. Removing the packet and restoring source
header words recovers the complete original, including vectors/footers/padding.
Private proof: `local-output/sdk-20260909/model-face-addition-20261003/parent/`.

This is a model-level codec foundation. It does not persist a project binding,
merge an existing removal/GLB identity ledger, allocate surrounding carrier space
or expose Review/Apply. Cross-operation authored UUID uniqueness is now implemented in the separate
model-only replay ledger below. SDK integration remains unfinished. No gameplay
or installation ran.


## Replayable face identity record

`importer.model_face_ledger` adds a detached JSON record using schema
`legaia.model-face-addition-ledger.v1`. The record binds the complete original
model hash and byte length. Its source face IDs are
`face://source/<source SHA256>/<object>/<source primitive>`; authored faces keep
canonical `face://authored/<UUIDv4>` identities. Source IDs identify only that
exact model, not a runtime actor or scene instance.

Each batch stores its input/proposed hashes and requests containing exactly
`face_id`, `donor_face_id` and typed `fields`. Replay resolves a donor from the
preceding model, including a previously authored face, and remaps all retained
identities after packet insertion. References to another new face in the same
batch reject; add that donor in a preceding batch. Duplicate authored IDs across
batches reject. Derived Current indices are recomputed rather than persisted as
authority. Candidate qualification compares every byte with complete replay.

Create with `create_face_ledger(original)`, append through
`append_face_ledger(original, ledger, requests)`, and reload through
`replay_face_ledger(original, ledger)`. Append returns candidate bytes, a detached
updated record and an audit. It does not mutate caller requests or prior records.
Both replay and append enforce eight batches and 128 total additions; these are
initial offline resource budgets. Codec typed-field and native byte/count limits
still apply.

Six ledger regressions cover deterministic JSON replay, multiple objects/groups,
shifted Current indices, authored-donor attribute inheritance, detached state,
source/schema/hash/byte tampering, cross-batch UUID collisions, missing donors and
batch/face budgets. Together with existing codec/topology checks, 28 cases pass.
Independent private Retail reconstruction serializes and reloads two quads in
Town01 model0009 object1/group0. Growth is 4,704 to 4,752 bytes; exact header/pointer
assembly matches, and removing both packets restores every source byte. Fresh
project reopen supplies the same source and all saved project hashes are unchanged.
Private proof: `local-output/sdk-20260909/model-face-ledger-20261003/parent/`.

The record is model-only and is not accepted by existing SDK asset override
bindings. It does not yet compose with Retail face removal/restoration, GLB edits,
new vectors/groups/objects or carrier relocation. Project history, Save/Open,
Review/Apply, scene preview and normal Build still need one coherent binding path.
No gameplay or installation ran.


## Model pack and scene-resource relocation codecs

`importer.model_pack_growth.grow_model_pack(source, source_hash, replacements)`
accepts exact `slot_index`/`ledger` pairs. It qualifies a canonical word-offset
TMD directory, derives each selected model's native extent, replays its ledger,
and preserves the member's trailing bytes separately. Later offsets rebase to
new word positions. All unselected slots remain byte-exact. Replacements compose
as one pack rather than sequential edits to stale offsets. Initial budgets are
240 slots, 32 selected slots and a 4 MiB decoded pack. Slots are explicit directory
identities; magic scanning does not establish relocation ownership.

`grow_scene_model_pack` qualifies a source carrier hash, explicit nonempty type-2
resource descriptor and decoded pack hash. It reuses original compressed bytes
for no-op replay. For changes it verifies deterministic compression readback,
updates the descriptor's decoded byte count, and retains every later payload byte.
If the compressed stream exceeds its resource slot, `allow_growth=True` permits
four-byte-aligned insertion and rebases later descriptor offsets. The default
rejects that growth. Other resource types, decoded sizes and reserved header bytes
remain unchanged. Nonempty descriptors cannot point at the carrier's exclusive end.

Format evidence is read from pinned Andrew commit
`d6e64c68ede25813d35db20980da82a1a025549b`, `docs/formats/pack.md` and
`crates/asset/src/pack.rs`: pack offsets are words relative to the pack start and
slot order is retained. The reference checkout's current HEAD is not used as that
pin. Existing SDK `man_container` descriptor relocation and `prot_layout` physical
ownership readers supply the established resource/physical boundary conventions.

Six new pack/carrier regression cases plus the existing focused suites pass,
35 cases total. Tests independently assemble multiple grown members and headers,
force compressed-slot growth, verify every neighbor/tail and later descriptor,
exercise no-op source identity, and reject stale/duplicate/aliased/malformed input.

The private Town01 proof uses the **227,328-byte consecutive-start physical span**
for PROT entry 4, not its 458,752-byte overlapping read window. Section 0 is a
114-slot pack; slot 9 begins at decoded offset 20,832 and its original model spans
4,704 bytes. Two ledger additions produce 4,752 bytes. The complete decoded pack
grows 304,116 to 304,164 bytes and agrees with independent whole-pack assembly.
Every other slot is unchanged. The new compressed stream occupies 154,531 bytes
inside the original 154,547-byte slot, so this real carrier requires no byte or
sector growth. All other five compressed resource sections remain byte-exact and
all six sections decode. Forced relocation is covered separately with synthetic
sources; it is not claimed to have been required by this Retail edit.

Private proof: `local-output/sdk-20260909/model-pack-growth-20261003/parent/`.
These are native pack/resource codecs with `build_ready=False`. They do not yet
compose PROT physical allocation/TOC or ISO relocation, create project asset
bindings, integrate removal/GLB, or expose editor Review/Apply/history/normal Build.
No gameplay or installation ran. The next integration must use consecutive-start
physical ownership, preserve every archive neighbor, and read back after reopening.


## PROT physical allocation and reopened pack validation

`importer.model_pack_archive.rebuild_model_pack_entry` accepts the complete source
archive/hash, stable entry index, explicit model descriptor index, decoded pack
hash and slot/ledger replacements. It locates the owner's consecutive-start
physical span through `prot_layout`; the larger legacy read window is never used
as available capacity. The scene-resource writer operates only on that span.
After growth, the carrier is zero-aligned to sectors and `replace_physical_entry`
rewrites every later raw start, preserving end sentinels and terminal zero words.
The supported PROT header offsets remain 0 and 2,048 bytes.

The writer then creates a fresh `ProtArchive` over the result. Readable entry
identities must match; the relocated physical span must have the exact emitted
length/bytes. Its native directory reparses and the model resource decompresses
to the ledger-qualified pack hash. Every physical payload before and after the
target remains byte-exact. Failure at any boundary rejects the result; there is
no installation side effect. Audit includes both resource and archive relocation,
reopened-pack validation and whether ISO relocation is required. It deliberately
remains `build_ready=False` until integrated with SDK project/Build qualification.

Four new regressions, together with existing focused suites, pass 44 cases.
They cover both supported header offsets, moved later starts/end sentinels,
neighbor payload preservation, no-op whole-archive identity, source/model/type
rejection and a descriptor that attempts to borrow a following physical entry
through an overlapping read window.

The private proof wraps a **fresh Retail Town01 227,328-byte physical carrier**
in a bounded synthetic PROT start table. That distinction matters: no full Retail
PROT or disc build is claimed. The two previously saved quads fit in place. A
third ledger batch adds 32 UV-varied quads, making 34 authored faces total and
forcing a 155,052-byte compressed pack stream against 154,547 bytes of original
capacity. Four-byte resource alignment adds 508 bytes; sector alignment then grows
the physical carrier to 229,376 bytes, one sector. Later starts update accordingly.
The reopened pack matches independent whole-pack assembly, all 113 other models
are preserved, other compressed resource bytes are unchanged, and both earlier
and later logical archive payloads remain byte-exact.

Private proof: `local-output/sdk-20260909/model-pack-archive-20261003/parent/`.
ISO relocation, persisted SDK asset bindings/history/Save/Open, removal and GLB
composition, editor Review/Apply/preview and normal Build remain unfinished.
No gameplay or installation ran. The next integration must carry this same
source/ledger/carrier qualification into the actual SDK project and Build path.


## Saved SDK face-addition binding

The SDK now accepts `tmd-face-addition-v1` through source-bound Python services
and `ProjectService.apply_model_face_additions`. Review and Apply both recompute
from the current Edit source key/effective model hash; Apply must match the
reviewed candidate hash. The binding contains ordinary model source/asset hashes,
byte length and scene identity, plus `base_binding` and the replayable `ledger`.
The candidate is stored in the existing content-addressed Authored/Models store.

`base_binding` is null for unchanged Retail or a retained, independently valid
same-source shape/content/material/normal-reference/face-removal binding. Nested
addition bases reject; successive additions append to one ledger instead. The
base's saved model bytes remain required, hash-qualified dependencies. Ledger
source-face IDs bind that exact effective base, not an inferred Retail/runtime
identity. This permits additions after existing edits/removal without discarding
them. Editing or restoring/removing/GLB importing *after* additions still needs
explicit ledger composition and remains unfinished.

Every model read and project Open verifies outer schema, Retail source, saved
candidate hash/length, retained base and exact complete ledger replay. Apply adds
one ordinary model-override session history entry and clears Redo. Session Undo/
Redo restores exact prior bindings. Save/Open retains bindings and owned bytes;
under the existing SDK convention Open clears session history, so history itself
is not claimed to persist across reopening.

Preview composition accepts addition/removal face-count changes while requiring
unchanged object identities and vertex ranges. It rebuilds triangle/material
arrays and continues to use existing verified rigid pose channels. No new object
or animation-channel relationship is inferred. Asset status identifies a
count-changing face addition. Existing-layout model edits and overlay Build reject
addition bindings explicitly; they cannot flatten or mis-export the ledger.

Four project regressions plus the focused native suites pass 48 cases, and 34
existing authoring/primitive/material/GLB regressions pass with private disc source,
82 total without skips. The private proof clones the previously saved Town01
project, retains its normal-reference/content base, reviews/applies a quad, tests
session history and composed preview, saves/reopens, then adds another face using
the authored donor and saves/reopens again. The final 4,752-byte model qualifies
exactly. No public project or game was modified. Private proof:
`local-output/sdk-20260909/model-face-addition-project-20261003/parent/`.

HTTP/editor source/Review/Apply actions, legacy edit/removal/GLB composition after
addition, and normal Build/ISO relocation remain unfinished. The persisted binding
is not yet installable through SDK Build. No gameplay or installation ran.


## HTTP source, Review, Apply and copied dependencies

The SDK exposes POST `/api/model-face-addition-source` with exactly `asset_id` and
`source_key`. Source now contains the native typed primitive/normal-reference
inspection as well as the replayed stable face ledger and decoded Current preview.
This supplies real donor field values and object-local vector domains for the
forthcoming editor. It does not infer donor identity from rendered triangles.

POST `/api/model-face-addition-preview` accepts exactly `asset_id`, `source_key`,
`expected_sha256` and `requests`. POST `/api/model-face-addition` additionally
requires `proposed_sha256`. Envelopes require nonempty bounded string asset IDs,
canonical lowercase 64-character source/hash strings, and 1..128 requests. Native
UUID/donor/typed-field validation remains in complete replay. Source requests have
the existing 32 KiB limit; Review/Apply have a 256 KiB limit. Over-limit declared
bodies reject before decoding or source work. Apply returns normal current state
with `model_face_addition` capability; the UI dialog is not yet connected.

Project input snapshots now include an addition's retained base file as a verified
owned dependency. Candidate read qualifies both levels; the base is independently
read again before capture. Existing duplicate-file identity and byte/file budgets
apply to that dependency. Project copy can therefore reopen and qualify an
addition over existing content edits rather than referencing an omitted base file.
No recursive addition dependency chain is accepted by the binding schema.

Three new HTTP/snapshot regressions plus the project/copy/history and existing
GLB HTTP suites pass 24 cases without skips. Cases exercise exact envelope/body
limits, review without mutation, mismatched candidate and stale repeat rejection,
qualified Apply/history, base dependency inclusion, budget accounting and tampered
base rejection. A real private Town01 server proof validates normal source/Review/
Apply state, then creates a project copy through the existing copy API. The copy
contains both required model hashes, reopens and qualifies the same 4,776-byte
candidate. Source authoring/history is unchanged by copying. Helpers close.
Private proof: `local-output/sdk-20260909/model-face-addition-http-20261003/parent/`.

Editor Review/Apply dialog, normal relocated Build/ISO integration and subsequent
legacy edits/removal/GLB composition remain unfinished. No game or installation ran.


## Model viewer Add face dialog

The model viewer now offers **Add model face** in Edit mode. Choose an existing
stable donor, then enter its triangle/quad vertex indices. UV pairs, baked RGB and
lit normal indices appear only when supported by that donor. Initial values come
from qualified Current native fields; material/command layout remains inherited.
The form creates one canonical authored UUID and reviews one face at a time.
Repeated dialog openings can use previously authored donors.

Review is tied to the exact typed request, model hashes and project/scene/asset
source context. The SDK now echoes the detached request in its review report.
The dialog checks complete stable owner coverage, typed domains, retained owner
remapping, expected added identity/counts and unchanged preview vector ownership.
Edits and donor changes clear Review. Current/Proposed complete-model wireframe
comparison supports drag/arrow-key orbit and scroll/plus/minus zoom. Camera changes
do not alter the accepted request. Apply sends only that reviewed request/hash,
updates normal state/history and refreshes the authored model viewport.

Close aborts inspection/review, releases owned busy state and disposes renderer/
resize resources. During Apply the Close button and Escape are held until outcome.
A discovered browser race—`dialog.close()` changes open state before its close
handler runs—is handled by checking actual dialog open state before accepting a
response. A late response cannot populate a closed dialog or release another
operation's busy state. Project/scene/asset/source/mode changes discard the dialog.
Corrupt or mismatched source/review data cannot enable Apply.

Seven focused Python cases and addition/removal/allocation Node suites pass,
plus editor/module syntax checks. Node regressions include the close-before-event
race, stale/late responses, owned busy release, mode and malformed-source guards.
Eight actual private Town01 browser checks validate typed lit quad fields,
read-only Review, edit invalidation, Current/Proposed layers, 540px layout, orbit/
zoom, Apply/history/view refresh, authored donor reopening and lifecycle guards.
Review leaves saved files and history unchanged. Apply changes only the private
clone's authored model state. No page errors or command/Save/Build/Run requests
occur. Narrow screenshot inspected; owned browser/server helpers close.
Private proof: `local-output/sdk-20260909/model-face-addition-editor-20261003/parent/`.

The dialog states that Build support is still being connected. General new vector/
object/group allocation, legacy edits/removal/GLB composition after addition and
normal relocated Build/ISO export remain unfinished. No gameplay or installation
ran; this is not native appearance/culling/pose acceptance.
