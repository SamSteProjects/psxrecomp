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
