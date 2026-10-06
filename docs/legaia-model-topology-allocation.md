# General model topology allocation work

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


## Shared-pack SDK preparation

`sdk.model_growth.prepare_model_growth` collects every authored model in each
explicit type-2 pack containing an addition binding. It verifies fresh imported
scene metadata and exact physical/descriptor/directory ownership, qualifies
retained base edits, replays addition ledgers and checks emitted bytes against
all saved model payloads. Ordinary shape/content/removal edits in the same pack
are carried as independently qualified bases with empty addition ledgers.
Imported model ownership can include native padding; remaining slot tails and
unselected members stay byte-exact. Preparation does not write project/history.

Requests target the existing PROT growth writer and report `deferred_model_ids`
for future Build composition. Those models must be excluded from legacy model
overlays when this is integrated, then combined with other authored carrier
patches before relocation. This preparation is not currently invoked by normal
Build; `build_ready` and `gameplay_verified` remain false. Bare/streaming carriers
are rejected rather than silently omitted.

The 23 focused tests and actual private Town01 proof cover additions over a
retained normal-reference/content base plus a neighboring shape edit, exact
whole-pack assembly, 112 untouched models, five unchanged compressed resources
and bounded archive reopening. Pack growth is 48 decoded bytes and eight carrier
bytes. No full Retail archive/BIN export or gameplay ran.
Private proof: `local-output/sdk-20260909/model-growth-preparation-20261003/parent/`.


## Compose patches before relocation

`importer.model_pack_composition.compose_model_pack_archive` accepts the source
archive hash, prepared resource requests and equal-length patch payloads with
original PROT-relative offsets and exact preimage hashes. It rejects header/TOC
writes, out-of-bounds or overlapping patches, malformed/duplicate resource
requests and changes to a selected pack's source. All patches apply before any
resource or archive growth; each relocation then uses the current archive and
its updated TOC. Final readback verifies every requested pack after all moves.
The per-step qualified carrier/archive transforms preserve other payload bytes,
including precomposed patches, while relocating resources and later entries.

Seventeen focused composition/preparation/archive/pack tests pass. New coverage
includes two growing carriers, two packs in one carrier, both supported header
locations, edits in retained resources and shifted archive neighbors, and
conflict/stale/ownership rejection. These are synthetic archive proofs, not a
Retail disc build or native gameplay acceptance. This module is not yet called
by normal Build; package and ISO metadata relocation integration remains required.
Output continues to report `build_ready=False` and `gameplay_verified=False`.


## Read relocated archives through ISO lookup

`importer.relocated_disc.RelocatedLogicalDisc` borrows an open source image and
verifies its complete original PROT hash before accepting a whole-sector, equal
or larger replacement. It uses `collect_metadata_relocation` to update PVD,
directories and endian path tables, supplies replacement PROT user sectors and
maps later logical LBAs back to their original source sectors. PROT is reopened
through ISO lookup to verify its extent and size. The audit describes source/
proposed sector counts and metadata sector preimage/candidate hashes. Closing
the view never closes the borrowed source. It does not expose raw CD sectors.

Seventeen focused tests include complete composition-to-ISO readback, shifted
metadata/payloads, same-size logical identity and invalid input rejection. These
are synthetic proofs with no physical disc export. The current runtime reads a
physical sector before applying ordinary overlays and obtains sector count from
that physical reader; insertion cannot be represented by ordinary overlays alone.
Normal Build packaging and runtime mapping/sector-count support must use the
verified logical mapping and remain unfinished. The view reports
`runtime_connected=False`, `build_ready=False` and `gameplay_verified=False`.


## Native sector mapping foundation

`runtime/include/disc_relocation.h` provides `PS1::DiscRelocation`. Qualified
activation supplies source sector count, PROT allocation, replacement user data
and relocated ISO metadata keyed by proposed LBA. The mapper validates extents,
no shrink, MSF address range and metadata ownership transactionally. Reads choose
replacement/metadata payloads or a shifted source callback, copying to the caller
only after success. Metadata addresses retain their old source LBA for future
raw-sector framing. Clear discards the active plan. The class does not perform
package hash/provenance or ISO metadata qualification; activation must do those.

A standalone native C++17 regression passes with warnings treated as errors,
covering every sector in the synthetic insertion, shifted tail/metadata, unchanged
buffers on failed reads and invalid configuration retaining the old valid plan.
The CMake `disc_relocation_test` target is registered; a full runtime suite was
not run. This mapper is not yet wired to ISOReader/CD controller or package
activation. Raw Mode 2 framing/error protection and normal Build packaging remain
required. Private executable lives under
`local-output/sdk-20260909/native-disc-relocation-20261003/parent/`.


## Native raw Mode 2 sectors

`runtime/include/cd_sector.h` supplies Form 1 EDC/P/Q regeneration and MSF address
relocation, cross-checked byte-for-byte against the existing Python codec.
`DiscRelocation::ReadRawSector` borrows raw source sectors, replaces user data for
PROT/metadata and rebuilds Form 1 protection. The final replacement PROT sector
uses original terminal framing; intermediate sectors use first-sector framing.
Metadata retains the original source LBA for framing. Shifted Mode 2 source
sectors change only their MSF header; XA/Form 2 payload/protection bytes stay
exact. Invalid framing and failed source reads leave caller buffers unchanged.
Activation must qualify uniform PROT stream framing/provenance before use.

Both native regressions pass with warnings treated as errors. Sixty-four varied
codec outputs match Python completely, including the highest supported address;
150,528 compared bytes have SHA256
`fbf8154320112dac223168df7ea5d1278882ded7de0952775c85b519f4801089`.
Mapping tests cover raw/user agreement, terminal/XA flags and malformed-frame
rejection. The CMake codec target is registered; full runtime suite not run.
Private proof: `local-output/sdk-20260909/native-raw-disc-relocation-20261003/parent/`.
ISOReader/CD controller wiring, package activation and normal Build integration
remain required. No game, installation or full-disc export ran.


## ISOReader installation and lifetime

`ISOReader::InstallDiscRelocation` validates the raw single-data-track source,
original ISO PROT extent/size and uniform Form 1 first/terminal framing before
installing a candidate mapping. Proposed PVD/root bounds are validated. ISO volume
size and physical sector count remain distinct: both grow by the insertion, even
when the original volume occupies fewer physical sectors. Hash/provenance and
complete ISO metadata qualification are the future activation layer's duties.

ReadSector, ReadRawSector and GetSectorCount use the installed mapping. File lookup
uses the relocated root. Virtual subchannel Q addresses use virtual bounds.
Clear restores the source root; Close/Open discard relocation. Duplicate active
installation rejects without changing the reader. CHD/multitrack/audio/SBI
configurations reject installation; their ordinary reader paths remain available.
The existing C CD wrappers already call these reader APIs, but package activation
and normal Build do not yet install plans.

The fresh native relocation regression and rebuilt SBI/CDDA regressions pass.
The relocation case includes source rejection, moved-root file lookup, exact
replacement/movie payloads, raw terminal/tail, bounds and lifetime. CMake target
registered; full runtime suite not run. MSVC reports existing libchdr/parser
warnings. Private builds: `local-output/sdk-20260909/iso-reader-relocation-20261003/parent/`.
No gameplay or full Retail disc export ran.


## Relocation payload contract

`importer.disc_relocation_package` defines binary v1 for feature package activation.
The existing legacy `derived_disc` channel rejects feature-style manifests.
This new codec is not a manifest declaration or an activation channel yet.

The 96-byte little-endian header (`<8s6I32s32s`) stores magic `PSXDRLOC`, version
1, original physical sector count, PROT starting LBA, original/proposed PROT
sector counts, metadata record count and original/proposed PROT SHA256 digests.
It is followed by complete proposed PROT user bytes. Each 2120-byte metadata
record stores `<II32s32s`: original/proposed LBA, source/candidate sector hashes,
then exactly 2048 candidate user bytes. Records sort by original LBA, exclude
PROT ownership and obey the insertion mapping. Payloads have exact lengths,
no shrink, MSF bounds, 1 GiB total/4096 metadata budgets and candidate readback.
The entire binary is bound to its expected SHA256 when decoded.

Activation must independently verify original PROT and metadata source hashes
against the committed source disc. Native parsing, strict feature manifest
ownership, conflict checks and activation are still required, followed by normal
Build packaging. Eight focused package/logical-disc/ISO tests pass; package tests
pass again after the preallocation guard. Output remains runtime/build/gameplay
unconnected. No game, helper, installation or full-disc export ran.


## Native payload qualification

`runtime/include/disc_relocation_package.h` decodes the exact binary v1 contract.
Parsing requires the whole-package expected SHA256 and stages the candidate
before assigning output. Header/extents, budgets, exact length, proposed PROT
hash and metadata ordering/ownership/candidate hashes are verified. The result
retains original PROT and metadata preimage digests with proposed payloads.

`VerifyDiscRelocationSource` must run against an unmodified reader bound to the
committed disc identity. It checks physical sector count, hashes original PROT
user sectors and checks every metadata preimage. Mutated parsed candidate
PROT/metadata is rejected too. This does not replace full ISO qualification,
feature/resolver conflict rules or package activation.

The standalone native regression passes with warnings treated as errors. A
Python-generated payload and source sectors verify natively with identical
replacement bytes and all five metadata source/proposed LBAs. Payload is 18,888
bytes, SHA256 `88ec8609e1e62340b14fee948057c78d678ecda9332bcdaf5409eea57c53b5b4`.
CMake target registered; full runtime suite not run. Private proof:
`local-output/sdk-20260909/native-relocation-package-20261003/parent/`.
No game/helper/installation/full-disc export ran. Normal Build integration and
activation remain unfinished.


## Feature manifest and conflict rules

Format 7 supports `[[disc_relocation]]` with exactly `feature`, `file` and
`sha256`. Ownership must name a declared feature; the package requires a target
with source-disc SHA256. File paths must be safe relative package assets and
payload hashes lowercase SHA256. The payload qualifies at manifest load and
again when its feature resolves enabled. Disabled features emit no relocation.
Channel pruning removes inaccessible owners and their relocation declarations.

Only one active relocation is permitted. Active ordinary disc writes, disc
user/raw overlays and legacy derived-disc providers conflict with relocation;
other authored carrier edits must be precomposed into the relocation payload.
Main-EXE operations retain their separate target. Resolved relocation package/
feature/payload hash joins the fingerprint; failed resolutions clear relocation
and other emitted operations. The existing 256 MiB loader limit is unchanged;
a fresh source metadata check reports PROT at 121,253,888 bytes.

Native relocation/complete package/runtime regressions pass. Runtime commit
currently rejects enabled relocation with an explicit unfinished-activation
error; it cannot silently boot stock while ignoring the selected feature.
Activation is the next required native step. SDK normal Build still emits format
6 overlays and does not emit relocation declarations yet. Private builds:
`local-output/sdk-20260909/mod-disc-relocation-20261003/parent/`.
CMake regression registered; full framework suite not run. Existing TOML/parser
warnings appear in native builds. No game, installation or full-disc export ran.


## Activation preflight before reader publication

`runtime/include/disc_relocation_activation.h` provides
`PrepareDiscRelocationReader` for a parsed payload and fresh unmodified reader
bound to the committed source identity. It verifies original PROT/metadata
preimages, inventories source file/directory identities and allocations within
budgets, then installs the candidate. Every reopened entry must retain type/size
and follow the expected extent shift; PROT gains its proposed size. Root mapping
and all directory child counts must match. Proposed PROT is streamed through the
installed reader and hashed without another full readback allocation. A failure
after installation clears relocation and restores the original reader root.

The native ISOReader regression passes for stale source rejection, wrong movie
extent rejection, hidden directory membership rejection/rollback and successful
PROT/movie readback, alongside previous mapping/lifetime cases. MSVC uses cached
libchdr plus native SHA256; existing library/parser warnings remain. Private
build/log: `local-output/sdk-20260909/iso-reader-relocation-20261003/parent/`.
Runtime publication/ownership/lifetime and path-table semantic qualification are
still required; runtime commit's explicit activation guard remains. Normal Build
is not connected. No game, installation or full Retail disc export ran.


## PVD and complete path-table semantics

Activation preflight snapshots the source PVD and every mandatory/optional path
table before installation. Tables are bounded to 1 MiB; both size copies and
mandatory pointers must agree. Records require complete headers, nonempty names,
no extended attributes and valid odd-name padding allocation. Source directory
extents must belong to the inventoried tree. Exact proposed extents are derived
using the insertion mapping; all other record bytes remain unchanged.

After installation, all four descriptor pointers, absent optional copies and
complete expected table bytes must match. The entire PVD must equal its source
transformation, allowing only volume-size, path-table-pointer and root-extent
updates. A mismatch rolls back to the original reader layout.

Fresh native regression passes with four source copies, wrong LE/BE extents,
padding/pointer/PVD mutations and rollback. Complete Python-generated payload/
Mode 2 fixture preflight also passes, including PROT and shifted nested movie
lookup. Fixtures: `local-output/sdk-20260909/relocation-path-table-preflight-20261003/parent/`.
Build/log: `local-output/sdk-20260909/iso-reader-relocation-20261003/parent/`.
Existing library/parser warnings remain; full runtime suite not run. Reader
publication/lifetime and normal Build integration remain required. Runtime commit
still refuses enabled relocation until activation is connected. No gameplay or
full Retail disc export ran.


## Runtime reader publication � 2026-10-03

**Runtime relocation publication and C reader lifetime (2026-10-03):** Commit now stages a fresh reader, rechecks whole-source SHA256 before/after native preflight and publishes only after successful plan/state preparation. The opaque C disc handle acquires the prepared reader for the bound source path. Competing source paths reject; replacing an active relocation invalidates old handles. Closing one shared handle leaves the other live. Netplay clear and reinitialization remove relocation from retained readers and restore stock layout. Failed recommits preserve the published reader. This supersedes the earlier unfinished-activation checkpoints below; normal SDK Build still emits format 6 ordinary overlays and does not yet compose/package model growth.

Validation: fresh MSVC mod-runtime regression passes both its built-in public synthetic source/payload and the independently Python-generated synthetic fixture. Coverage includes 60-to-62 sector mapping, replacement user/raw terminal framing, shifted movie/tail reads, undersized/out-of-range output preservation, wrong source, changed payload, same-path changed source, failed-commit isolation, plan replacement, shared close, netplay clear and reinitialization. The C bridge is now linked into the CMake regression target. Existing compiler/parser warnings remain; the full runtime/game build was not run. Private build/log: `local-output/sdk-20260909/mod-disc-relocation-20261003/parent/`. No game, installation or full Retail disc export ran; gameplay remains deferred.

The normal Build path still needs to consume source-bound model-growth requests,
compose ordinary source-offset patches before growth, encode the relocation payload
and emit the format 7 feature package. This runtime checkpoint does not qualify a
Retail package or gameplay. Directory entry identity/type/extent/size/membership,
complete PVD and complete path-table bytes are checked; opaque directory-record
fields and parent-record byte transformations have not received independent full-byte
qualification.


## Normal Build package composition � 2026-10-03

**Normal Build relocation package composition (2026-10-03):** Normal SDK Build now gathers all saved models sharing a topology-growth pack, defers them from legacy shape overlays, composes ordinary PROT patches at original offsets before growth and emits one format 7 `disc_relocation` feature payload. Source-bound external Form 1 edits are composed into mapped sectors; overlap, stale hashes, PROT-boundary straddles, ISO metadata conflicts and native payload budgets reject. The existing format 6 path remains for builds without topology additions. Review computes/verifies proposed bytes without writing output; packing validates the emitted relocation asset, and repeated builds are deterministic.

Validation: 36 focused Python tests pass (3 Retail-gated cases skipped). New normal Build regression uses actual synthetic Mode 2 ISO sectors, saved addition/retained-shape bindings in one pack, original-offset patch composition, independent reopened model payload comparison, the real generic psxmod packer and archive readback. External edits crossing a sector boundary map correctly. A fresh MSVC native harness accepts/activates an SDK-emitted synthetic package, compares every proposed PROT/metadata sector through the C disc reader and restores stock count on netplay clear. Private proof: `local-output/sdk-20260909/model-growth-normal-build-20261003/parent/`. Existing native compiler/parser warnings remain. No Retail package/game launch, installation or full Retail ISO/BIN export ran; gameplay remains deferred.

Remaining integration: saved Build history verification and Build & Run still assume an overlay-only inventory/private size bound. Those consumers need relocation-aware inventory and runtime observation before this package is offered as a complete Build & Run workflow. This checkpoint supersedes the earlier claim that normal Build cannot emit growth packages; it does not complete the full SDK or prove Retail/gameplay acceptance.


## Saved Build verification and private run preparation � 2026-10-03

**Relocation-aware saved Builds and run preparation (2026-10-03):** Saved Build verification and private run preparation now share an exact audited payload inventory. Format 7 relocation packages qualify their sole asset/hash/length and binary readback; composed source overlays remain audit inputs rather than separately installed assets. Output overlay counts describe emitted overlays. Private staging accepts the native 256 MiB relocation payload bound with bounded manifest overhead, rejects unexpected/mixed inventory and descriptor tampering before staging, and retains the feature selection plus expected payload hash/virtual sector count. Ordinary overlay packages keep the prior 64 MiB private bound.

Runtime `mod_status` now reports active relocation count, prepared reader activity, virtual sector count, reader acquisitions since plan reset and payload SHA256. SDK readiness requires the exact active relocation and at least one CD reader acquisition; older/missing observations, wrong hash/count, inactive readers and zero acquisitions reject readiness. This is process/plan identity preparation, not scene acceptance or sector-consumption proof.

Validation: 30 focused Python tests pass (3 Retail-gated skipped), including actual normal-Build history integrity/tamper checks, exact private staging without process launch, descriptor size/hash/path/budget rejection and readiness mismatch cases. Fresh MSVC native mod-runtime regression passes, proving status before/after handle acquisition and reset on netplay clear. The debug server passes GCC C11 syntax qualification with existing cached SDL3 headers; its actual status handler compiles independently with `-Wall -Wextra -Werror` and active/cleared JSON round trips parse correctly. Private protocol proof: `local-output/sdk-20260909/relocation-package-consumers-20261003/parent/`; runtime build/log: `local-output/sdk-20260909/mod-disc-relocation-20261003/parent/`. Existing native compiler/parser warnings remain. Full runtime/game build, Retail package activation and live Build & Run were not run. No game or runtime installation was performed; gameplay remains deferred.

Remaining: qualify the complete Retail model-growth package and rebuilt runtime without launching gameplay, then retain the gameplay queue for explicit user verification. The full SDK specification remains unfinished, including post-addition model authoring, scene/runtime parity, animation and script coverage. Earlier overlay-only-consumer checkpoints below are historical.


## Complete Retail package and raw-reader qualification � 2026-10-03

**Retail model-growth package and fresh runtime qualification (2026-10-03):** Normal Build now passes on an isolated saved Town01 project containing two authored faces over retained content-v3 model 9 plus an independent model 8 shape edit in the same pack. PROT grows from 121,253,888 to 121,255,936 bytes (one sector). Both saved payloads reopen exactly; all 112 unedited model slots and the original bytes of all five other resources are preserved. Only zero allocation padding is added after the final resource. Build leaves the project unchanged; reopening and saved Build integrity verification pass. Private run preparation accepts the 121,272,992-byte relocation payload and records its expected hash/count without starting a process.

Fresh MSVC isolated native activation passes against the original verified Retail BIN. It compares every proposed PROT byte and every relocation metadata sector through the C reader. All raw PROT sectors also match proposed user bytes, source-derived first/terminal subheaders, relocated addresses and regenerated EDC/ECC. Netplay clear restores the original reader count and clears relocation status. Payload SHA256: `467734a7805f5d4312bc79b922108a4b81d31d89e6490bfc98bed14b1d200ecb`; package ZIP: 72,034,628 bytes. Private artifacts/proof: `local-output/sdk-20260909/retail-model-growth-build-20261003/parent/`. No Retail disc image was exported; proprietary package/source material remains private and ignored.

The complete stability runtime target configures offline from cached dependencies, compiles and links successfully in Release with two build workers. Its revision stamp is `nightly-565-g3322686e`, and binary SHA256 is `f584a9c44f74c22b0ccf62596bfbca6a480c8f0f5d64c1855dc606b6cd2b805f`. Binary: `local-output/stability-20260909/build/Release/LegaiaStability.exe`. An initial MSBuild attempt rejected duplicate inherited PATH/Path names; normalizing environment names resolved it. Regenerating CMake also corrected a stale cached revision label. Existing compiler/parser warnings remain. The game binary was not executed: isolated reader activation is not live Build & Run, visual/editor parity or gameplay acceptance.

Gameplay remains queued for later user verification. Offline work can continue on post-addition model authoring and the remaining SDK specification; this qualification does not mark the goal complete or require immediate manual play.


## Typed content operations after addition � 2026-10-03

**Content authoring after face additions (2026-10-03):** Added a source-bound V2 face ledger that chains typed existing-layout content edits between addition batches. V1 ledgers remain readable. Each operation qualifies exact input/output hashes, ordered bounded byte preimages and complete typed model-content ownership; count/pointer/opaque changes reject. Stable source/authored face identities survive vector/normal, face vertex/UV/RGB, material and object edits, then further additions using an authored donor. Limits remain eight addition batches/128 authored faces, plus 64 total operations and 2 MiB finite ledger metadata.

Project model writes retain the original independently qualified base binding and append content operations. No-op writes preserve history. Current-topology TMD/OBJ/JSON preparation and object transforms can compose with additions; reports identify Current comparison rather than claiming a Retail topology comparison. Undo/Redo, Save/Open, export input snapshots, model-pack preparation/rebuild and normal relocation Build preserve the composed payload. Count-changing removal and GLB workflows are not covered by this checkpoint.

The face editor now accepts V4 explicit Retail/authored ownership maps, including gaps from added faces. Authored faces can be selected/edited; Reset to Retail is disabled when no Retail owner exists. Retained-face comparison still uses the actual Retail row. Ownership coverage, monotonic retained identities, authored UUID uniqueness/counts and row bounds reject malformed reports.

Validation: focused Python regression plus the Node face-editor source/draft/review/lifecycle suite pass. Coverage includes content between additions, edited authored donors, vector and normal edits, face UV/RGB/reference edits, material fields, object translation, history, Save/Open, retained-base snapshot bytes, pack readback and normal Build/archive readback with a V2 ledger. Stale/opaque/count changes, malformed runs/preimages/hashes and operation budget overflow reject without project/history mutation. Node coverage includes V4 ownership errors, authored selection, disabled Retail reset and Current draft discard. No Retail requalification, actual browser rendering or game launch ran in this checkpoint; earlier Retail V1/runtime qualification remains separate evidence. No immediate gameplay verification is required.

Remaining: topology-aware material/reference and GLB panels, post-addition removals/restoration, and new vector/object/group authoring still need independent ownership/integration work. The full SDK goal remains active.


## Material inspection on addition topology - 2026-10-03

**Material inspector after face additions (2026-10-03):** The material source now carries V3 explicit retained Retail face/group mappings and stable authored face identities. The panel accepts gaps from added faces, checks complete ownership coverage and UUID uniqueness, and keeps Retail reset available only for retained faces. Authored texture page/CLUT edits and shared packet-group ABE edits use the existing reviewed commands; all current group members, including authored faces, appear in the audit. Existing V1 sources and V2 removal mappings remain compatible.

V2 material reviews explicitly compare against Current addition topology, rather than reporting current offsets as Retail offsets. Review/Apply preserve the typed V2 face ledger, independently qualified retained base, stable identities, Undo/Redo and Save/Open. Tests cover retained removal bases, no-op review, stale source/hash/review-key rejection, actual HTTP source/review/apply envelopes and panel reset/discard/review lifecycle. The focused Python run passes 51 tests with one Retail-gated skip; all three Node material/donor/primitive suites pass; backend source/review data also qualifies in JavaScript after the HTTP asset identity decoration. Normal Build and pack-growth regressions remain passing. Gameplay appearance, live VRAM residency and hardware blending remain deferred; this checkpoint does not require immediate manual play.

This supersedes the earlier pending material-panel item. Reference/GLB panels, post-addition count-changing removal/restoration, new vectors/objects/groups and the remaining SDK/runtime specification still need work. The full goal remains active; no game was launched.

## Stored vector references on addition topology - 2026-10-03

**Stored vector-reference navigation after face additions (2026-10-03):** Normal and vertex user reports now expose V2 retained Retail mappings, stable authored face identities, complete Current face counts and separate Retail byte bounds. The reports qualify the independently retained base and full addition/content ledger before inspecting stored operands. Normal and vertex edits remain read-only in these reference panels; vector/content authoring stays in the existing reviewed tools.

Both panels accept retained index gaps, reject overlapping/duplicate/missing authored ownership, and show authored faces without inventing a Retail counterpart. Current and Retail links navigate to the actual Current face index; authored links carry their stable face identity. Stale selection/source changes withdraw the links. Earlier removals compose with later additions; baked-color faces still report no stored normal operands. Validation: 28 focused Python tests pass, including real HTTP reference endpoints, unchanged project/history, stale hash/key rejection, later vector edits, retained removal bases and normal operand absence. Three Node suites pass for legacy decoders, authored ownership/navigation and stale withdrawal. Four actual Python reports (normal/vertex, addition/removal base) qualify in JavaScript. No game or browser-rendering session ran; runtime visibility and normal shading remain deferred.

This supersedes the pending stored vector-reference panel item. GLB workflows, count-changing post-addition removal/restoration, new vectors/objects/groups and the broader SDK/runtime specification remain incomplete. Offline work can continue without immediate gameplay verification; the full goal remains active.

## GLB interchange on addition topology - 2026-10-03

**GLB interchange after face additions (2026-10-03):** The SDK now exports and imports the effective model after additions and typed content edits through the real GLB codec. A V3 sidecar binds the current model/profile to a freshly qualified stable topology fingerprint and authored face count. The fingerprint includes retained Retail mappings and authored identities, so changing stable identities invalidates an older sidecar even when model bytes remain identical. V1 ordinary and V2 removal sidecars remain supported.

V3 reviews explicitly audit Current addition topology; they do not mislabel current packet offsets as Retail changes. Position edits and authored-face RGB edits append typed content operations while retaining the independent base and addition ledger. Tests cover exact no-op export roundtrip, reviewed Apply, Undo/Redo, Save/Open, stale/forged bindings and review keys, retained removal bases, and actual HTTP export/review/import endpoints. The focused Python run completes 25 tests with three Retail-gated skips; both Node GLB suites pass, and four actual backend export/import reports qualify in JavaScript. No game, external DCC application or browser-rendering session ran; gameplay appearance remains deferred.

This supersedes the pending existing-layout GLB composition item. GLB does not allocate further faces/vectors/objects/groups; count-changing post-addition removal/restoration and the broader SDK/runtime specification remain incomplete. Offline work can continue without immediate gameplay verification; the full goal remains active.

## Typed stable face removal replay - 2026-10-03

**Typed face-removal replay groundwork (2026-10-03):** The pure model ledger now supports V3 stable-identity removal operations after additions and content edits. Removal uses the independently qualified allocation-preserving face codec, checks operation pre/post hashes, compacts surviving Current face and group indices, and retains deleted identity records. Deleted authored IDs remain reserved and still count against the historical 128-face budget; deleted faces cannot be donors. Content edits and later additions retain V3. V1/V2 replay remains compatible.

Validation: 32 focused Python tests pass. New cases independently compare removal bytes with the existing codec, drop a complete packet group, edit vectors between removals, remove an authored face, add from a surviving remapped donor, serialize/replay, reject deleted ID reuse and donors, reject malformed/stale operation chains without input mutation, and enforce the shared 64-operation limit. Existing addition/content, GLB, reference, removal and normal Build regressions remain passing.

This is replay-layer groundwork, not a completed editor feature. Project reviewed removal commands, panel mappings when an authored-only group survives, restoration and end-to-end Build evidence for V3 removals still need integration. Existing editor commands do not create V3 removals yet. No game was launched; the full SDK goal remains active and offline work can continue.

## Reviewed project removals on ledger topology - 2026-10-03

**Reviewed project removal after additions (2026-10-03):** The project/HTTP removal command now resolves validated Current face selections to stable ledger identities and retains the original independent base plus the complete addition/content/removal ledger. Source reports expose active stable identities and deleted IDs; reviews identify the exact deleted IDs and replayed topology. Private replacement bindings remain internal. Reviewed hash, source key and current payload freshness gate publication; empty selections leave history unchanged.

Validation: 36 focused Python tests pass. New evidence covers retained and authored removals, HTTP source/review/Apply, wrong candidate and stale-repeat rejection without mutation, Undo/Redo, later vector edits, Save/Open, and normal Build using the real relocation packager with exact reopened model bytes after a retained-face removal. Earlier ledger, removal/restoration, addition/content, GLB, reference and normal Build tests remain passing. No game was launched.

This completes the backend command integration, not the browser feature. Browser V3 source/V2 review adapters, authored-only surviving group mappings, zero-active-authored GLB bindings and ledger restoration remain unfinished; old browser removal decoding rejects the new schema rather than guessing identities. Ledger restoration explicitly rejects until stable restoration ownership is implemented. The full goal remains active; no immediate gameplay verification is required.

## Browser stable-face removal adapter - 2026-10-03

**Browser removal adapter for stable ledger faces (2026-10-03):** The removal dialog now accepts V3 stable-identity sources and V2 removal reviews. It qualifies complete Current face coverage, source/authored identity domains, duplicate/deleted ownership, selected stable IDs, surviving group compaction, unchanged vectors and reviewed triangle counts. Stable deletion counts replace misleading Retail totals. Ledger restoration stays disabled, with source-appropriate help; ordinary Retail restoration remains supported.

Validation: the Node removal suite passes legacy removal/restoration plus authored deletion, authored-only surviving groups and identity/count tamper cases. Four actual backend retained/authored removal and no-op reports qualify in JavaScript. Eleven focused Python tests pass. Isolated headless Edge smoke tests use actual synthetic backend reports with mocked HTTP responses and the real scene renderer: both retained and authored cases load, render reviewed previews, switch Current/Proposed, withdraw Apply after selection edits, require a fresh review and submit the reviewed hash exactly once. A preview screenshot was inspected. This is browser integration evidence, not native gameplay or a full styled-editor visual acceptance run.

This supersedes the pending browser source/review adapter item. Other panels still need authored-only group and zero-active-authored handling; stable ledger restoration remains incomplete. No game was launched; offline work and the full SDK goal remain active.

## Panel ownership after stable removals - 2026-10-03

**Post-removal panel ownership and history counts (2026-10-03):** Material packet groups now derive their original Retail owner through the complete qualified donor chain, including deleted donors. Authored-only surviving groups retain the correct original group after compaction; the browser accepts these groups while retaining ordered group ownership, header/layout and retained-face checks. GLB V3 bindings accept zero active authored faces without discarding the stable topology fingerprint or ledger. The addition panel separates active faces from the historical creation budget, accepts recorded deleted donor provenance, rejects deleted ID reuse and checks that reviews preserve deleted identities.

Validation: 23 focused Python tests and all three Node material/GLB/addition suites pass. New cases cover authored-only material editing, subsequent additions from surviving authored donors, a second Retail group compacting to Current group 0, and GLB no-op roundtrips with zero active authored faces. Actual backend source/review data for material, GLB and addition workflows qualifies in JavaScript for both authored-only and zero-active-authored cases. Existing project/HTTP removal, history, typed content and ledger regressions remain passing. No new browser-rendering or native gameplay session ran.

This supersedes the pending authored-only group and zero-active-authored panel items. Stable ledger restoration, new vector/object/group allocation and the broader SDK/runtime specification remain incomplete. No immediate gameplay verification is required; the full goal stays active.

## Verified deletion preimages for restoration - 2026-10-03

**Replay-derived restoration packet sources (2026-10-03):** Added an opt-in capture API that recovers deleted face packets only after complete qualified ledger replay. Each detached record retains the exact packet, descriptor and opaque footer from the deletion preimage, its input hash/size/offset, stable face metadata, original group in the qualified ledger base and permanent ordering. Authored origins follow recorded donor chains across group compaction. No caller-provided raw packets are added to the ledger, and ordinary replay does not collect or retain these restoration copies.

Validation: 25 focused Python tests pass. New evidence compares independently sliced pre-deletion bytes with captured packet/descriptor/footer bytes after material edits, verifies original group 1 after Current group compaction to 0, checks source/authored permanent order, detached output and unchanged input ledgers, and rejects stale hashes, unknown identities and injected packet fields through full replay. Existing ledger, project/HTTP removal, post-removal panels, content/history and GLB tests remain passing.

This supplies verified restoration inputs, not a restoration command. Packet reinsertion/allocation, restoration replay operations, project/HTTP/browser integration and end-to-end Build qualification remain unfinished. No game or browser session ran; the full SDK goal stays active and offline work can continue.


**Deleted-face reinsertion codec (2026-10-03):** Added an internal source-bound codec that restores exact recorded source/authored packets into their original groups, keeps surviving packet bytes and current group settings, recovers absent-group descriptors and opaque footers, preserves stable ordering, grows primitive streams and rebases existing object table pointers. Bytes outside replaced streams are copied unchanged; unused table pointers remain unchanged. Complete native model qualification runs before return, with bounded allocation and unique deleted-identity selection.

Validation: 30 focused Python tests pass, including all 24 supported packet flag layouts, byte-exact packets/footer/terminal/suffix checks, complete group removal, an empty object with another supported object remaining, two-object pointer rebasing, surviving vertex and transparency edits, authored packet restoration, input immutability, malformed selections, tampered replay and allocation-budget rejection. Existing project/HTTP removal, content/history, panel and GLB regressions pass.

This completes internal packet reinsertion groundwork only. Restoration ledger operations, project/HTTP/browser publication and end-to-end restoration Build qualification remain pending. Removed allocation slack is preserved rather than reclaimed. No game was launched; no immediate gameplay verification is required and the full SDK goal remains active.


**Stable restoration replay ledger (2026-10-03):** V4 ledgers add a bounded `restore_faces` operation containing only stable identities and chained hashes. Replay recovers packet preimages in the same pass and reinserts them without recursive replay or caller-supplied packet bytes. Restored identities become active, leave the deleted set and may serve as later donors. Subsequent deletion captures a fresh preimage; historical authored identities and creation budgets remain reserved. Content and removal operations preserve V4. Older V1/V2/V3 ledgers remain supported and reject restoration operations.

Validation: 34 focused Python tests pass. New cases cover partial/full-group restoration, content and additions after restoration, deletion/restoration cycles, fresh deletion hashes, JSON roundtrips, forbidden identity reuse, nonrecursive replay, tampered operation fields/hashes and operation budgets. A synthetic fixture installs a qualified V4 binding and verifies existing project reads, later vertex-edit Undo/Redo, Save/Open and normal Build with exact packed-model readback. This is consumer/codec evidence, not a restoration project command or browser acceptance test.

Project/HTTP restoration command publication, source/review adapters and browser controls remain pending. The broad SDK/editor/runtime specification and deferred gameplay checks remain incomplete; no game was launched and offline work continues.


**Stable restoration project/HTTP/browser workflow (2026-10-03):** Added reviewed restoration of deleted source and authored faces in retained model ledgers. V4 source reports expose bounded deletion metadata and immutable group/order ownership; requests carry exact stable identities rather than stale Current indices or packet data. V2 restoration reviews qualify the selected identities, remaining deletions, reinserted order/groups, vector ownership, triangle counts and hash changes. Apply uses the existing transactional project path, preserving the qualified base binding and V4 ledger. The browser lists deleted face indices per object, maps them to stable IDs, renders Current/Proposed layers and withdraws Apply when selections change. Ordinary Retail restoration and V3 removal sources remain compatible.

Validation: 42 focused Python tests and the Node removal/restoration suite pass. Actual project commands cover reviewed hashes, read-only preview, Undo/Redo, later vertex edits, Save/Open and normal synthetic-disc Build with exact packed-model readback. HTTP tests cover authored restoration, stale source/model hashes, duplicate/unknown identities, injected packet fields, wrong reviewed hashes and repeat Apply rejection without history changes. Isolated headless Edge smoke checks using actual synthetic backend reports and the real renderer pass for both source and authored restoration, both preview layers, stale Apply withdrawal and exactly one reviewed-hash submission; a screenshot was inspected. HTTP responses in the browser smoke are fixture-backed; this is not full styled-editor or native gameplay acceptance.

This supersedes the pending restoration command and browser adapter items. Real Retail restoration package/native-reader qualification and deferred gameplay verification remain to be gathered; new vector/object/group allocation and the broader SDK/editor/runtime specification remain incomplete. No game was launched or controlled, and offline work remains active.


**Real Retail restoration package/native-reader qualification (2026-10-03):** In an isolated copy of the saved Town01 project, the actual reviewed commands removed and restored one retained face and one authored face. Both restored packets match the preceding model exactly and current vectors are unchanged. The model grew from 4,752 to 4,796 bytes because deletion slack is preserved. Its restored SHA-256 is `f647f23827e9a6562d28afdb85abbee7dbc4945bbb6601d13feb6aaa4df51aa6`.

Normal Build emitted a private format-7 package with one relocation payload, no overlays and one additional PROT sector. The payload is 121,272,992 bytes, SHA-256 `b38aa54ea37f4bf7df7982fed4d1a83d55cbc752fe3d4c4dd35b839f81e1340e`; the ZIP is 72,034,620 bytes. Exact restored and neighboring edited model readback passed; all 112 unedited model slots and the original five other resources were preserved, allowing only zero allocation padding. Build left project/history unchanged, Save/Open retained the restored model, saved Build integrity verified, and private RunService staging accepted the payload without creating a process.

A freshly compiled isolated MSVC harness using runtime sources at `d3017aed` passed native activation, every replacement PROT user-sector read, every replacement raw-sector payload/address/subheader/EDC/ECC check, all metadata-sector reads and netplay clearing back to stock count/state. Existing CRT and size-conversion compiler warnings remain; this is not a warning-free compile or a fresh full-game executable build. Private proof and scripts are under `local-output/sdk-20260909/retail-restoration-build-20261003/parent/`. The source disc hash remains `e6120a5d70716dd2f026a2da32d0171d52651971b52c4347a68541299f75258c`; no full Retail disc was exported and no game was launched or controlled.

This supplies the pending Retail restoration package/native-reader evidence. Runtime rendering/behavior still awaits deferred manual gameplay verification. New vectors, objects and groups, animation import/retarget and the remaining scene/runtime specification remain incomplete; the full goal stays active and offline work can continue.


**Native vector allocation codec (2026-10-03):** Added a source-bound allocator for appending vertex and normal SVECTOR rows to existing objects. It preserves all existing indices, vector padding, primitive packets, footers and opaque bytes while rebasing used table pointers and updating only requested vector counts. Previously unused vector tables receive an owned allocation at EOF rather than using their unused pointer. New rows contain explicit signed 16-bit XYZ and zero padding; no normal recomputation is implied. Requests reject duplicate table owners and are bounded to 4,096 new rows, 8,192 addressable rows per table and the existing 4 MiB model limit.

Validation: 26 focused Python tests pass. New evidence independently removes every insertion and restores only permitted header words to recover the complete original model byte-for-byte across four adjacent tables in two objects. Actual face packets use new vertices and normals without renumbering retained faces. The last addressable vertex (index 8,191) is accepted by the face codec, and another row is rejected. Empty normal-table allocation, exact zero-padded new rows, signed boundaries, hash/candidate tampering, duplicate/malformed requests and byte/row budgets are covered. Existing addition/removal/restoration ledger and reinsertion regressions pass.

This is internal allocation groundwork, not an editor vector-allocation command or retained-ledger operation. Ledger replay, project/HTTP/browser publication, GLB topology import and normal Build/native-reader qualification of new vector allocations remain pending. New objects/groups and the broader SDK/runtime specification remain incomplete. No game was launched; offline work and the full goal remain active.


**Vector allocation replay ledger and Build consumers (2026-10-03):** V5 ledgers add a typed `allocate_vectors` operation with exact table requests and chained hashes. Stable face identities remain unchanged when vectors are appended; further face additions may use the new indices. Content, removal and restoration operations preserve V5, including allocation between full-group deletion and packet restoration. The replay-wide budget permits at most 4,096 allocated rows across all operations, in addition to existing native table, model byte, metadata and 64-operation limits. V1/V2/V3/V4 remain readable and reject the new operation.

Validation: 51 focused Python tests pass. New cases cover lit faces using new vertices/normals, later edits of a new row, exact packet deletion/restoration, full-group origin recovery, JSON replay, immutable requests/ledgers, malformed schemas/hashes/requests, operation limits and the real cumulative 4,096-row boundary. A synthetic fixture installs a qualified V5 binding and passes existing project reads, later new-row vector-edit Undo/Redo, Save/Open and normal Build with exact packed-model readback. The fixture does not invoke a vector-allocation project command or prove browser/scene-preview support.

Vector-allocation commands, project/HTTP/browser source/review controls, preview adaptation for enlarged vector tables, GLB topology import and Retail/native qualification remain pending. New objects/groups, animation import and the broader SDK/runtime specification remain incomplete. No game was launched; no immediate gameplay verification is required and the full goal remains active.


**Enlarged-vector model preview composition (2026-10-03):** Model previews now accept vector-count growth evidenced by a V5 binding already qualified by the project reader. The preview checks candidate hash/length, native ownership, bounded allocation requests and exact per-object growth. It updates object vertex ranges while retaining existing rigid channels, rebuilds candidate triangle/material data and applies the same channels to all frame vertices. Party-style prefixes continue to omit trailing equipment objects even when those objects grow. Current previews carrying an authored ledger must be an exact operation prefix of the proposed ledger; their existing allocations are subtracted so later allocations/content edits do not double-count growth.

Validation: 43 focused Python tests ran: 40 passed and three existing Retail-dependent cases were skipped. Four new cases cover complete unposed geometry, rotated/translated posed prefixes, frame transforms with independently checked new-row coordinates, later-object range shifts, new face indices, omitted equipment bounds, shared scene-instance immutability, successive V5 allocations/content previews and rejection of stale payload bindings, wrong counts/owners, invalid Current ledger ancestry and mismatched channels. Legacy shape/material/primitive/removal/addition preview regressions and vector replay/Build consumer tests remain passing. No browser or native session ran in this milestone.

This supplies preview composition for qualified bindings, not the vector-allocation project command or browser controls. Source/review/API/editor publication, other panels' new-vector ownership, GLB topology import and Retail/native qualification remain pending. The broader scene/animation/runtime specification stays incomplete; offline work and the full goal remain active.


**Reviewed vector-allocation project and HTTP commands (2026-10-03):** Added source inspection, read-only review and reviewed-hash Apply for new native vertex/normal rows. Source reports carry Current table counts, native limits, the remaining replay-wide row budget and stable topology. Reviews expose exact new row ranges/pointer relocations alongside Current/Proposed geometry, and independently compare direct allocation with complete V5 replay. Apply retains the independently qualified base and ledger through the existing immutable model asset/history mechanism. Face additions share that publication helper, which now rechecks the scene source immediately before history publication.

Validation: 63 focused Python tests pass without skips. Actual allocation commands cover read-only preview with unchanged asset files, wrong reviewed hashes, Undo/Redo, later new-normal editing, faces using newly allocated vertices, Save/Open and normal synthetic-disc Build with exact packed-model readback. A first allocation also wraps an ordinary independently qualified base. HTTP source/preview/Apply tests reject stale source/model hashes, extra fields, empty/malformed requests, duplicate table owners, boolean indices/coordinates, injected padding and repeated Apply without changing bindings/history. A source change after immutable asset preparation also prevents history publication. Existing face-addition, removal/restoration, GLB, vector replay and preview regressions remain passing.

This completes backend command publication, not editor/browser controls. Browser source/review adapters and controls, other panels' new-vector ownership, GLB topology import and Retail/native vector-allocation qualification remain pending. The broader SDK/editor/runtime specification remains incomplete; no game or browser session ran, and offline work stays active.


**Vector-allocation browser controls and review qualification (2026-10-03):** Added an Edit-mode model-editor action for appending object-local vertices or stored normals. The dialog accepts bounded signed XYZ triples, reports Current counts/new index ranges and remaining native/global budgets, renders Current/Proposed layers, invalidates review after input/context changes and submits only the reviewed hash. Browser adapters qualify stable face coverage, table/range/pointer ownership, exact requested new XYZ, preserved old vertices, rebased triangle references and unchanged face material/UV/color/normal content. The camera frames referenced geometry so distant unused new vectors do not shrink the visible mesh. The SDK advertises the capability and serves the module.

Validation: the Node vector-allocation suite and editor syntax check pass. Nineteen focused Python tests pass, including actual server module GET, API/history/Save/Open/Build, pose previews, replay and native allocation. Actual synthetic backend reports passed isolated headless Edge smoke checks for both vertex and normal allocation, both layers, changed-input Apply withdrawal and a single reviewed-hash submission. A screenshot was inspected; the smoke serves fixture-backed responses and is not a full styled-editor or live-runtime acceptance test. Browser pointer qualification also led to a native allocator fix: extending an existing table at EOF must precede allocating an empty table at the same EOF. A tight-layout regression confirms correct XYZ, table pointers and allocation order.

This supplies the pending allocation browser workflow. Other panels' new-vector ownership, GLB topology import and Retail/native qualification of allocated-vector packages remain pending, alongside new object/group allocation and the broader scene/animation/runtime specification. No game was launched or controlled; offline work and the full goal remain active.


**Allocated-vector reference inspection (2026-10-03):** Vertex and normal reference endpoints now emit V3 reports for V5 models, distinguishing retained Retail rows from appended Current rows with explicit vector counts/origin. Appended rows have null Retail coordinates and an empty Retail user list; the endpoint never reads an absent Retail row. Existing source rows retain both layers. Browser validation checks the origin/index/count relationship and absent-counterpart contract, keeps complete retained/authored face coverage and correct source/current byte bounds, labels allocated rows and disables their Retail layer. Current face links continue to carry stable authored IDs; stale inspections withdraw navigation.

Validation: 22 focused Python tests and three Node reference suites pass. New cases cover used/unused allocated vertices and normals, retained rows, retained-removal bases, read-only state, HTTP stale/bool/out-of-range rejection, and the first normal allocated into a zero-row Retail table. Node DOM fixtures verify the disabled Retail option, Current labels, authored navigation and stale withdrawal, with identity/count/null-coordinate tamper rejection. Twelve actual backend reports qualify in JavaScript across retained, allocated and unused rows with and without a retained-removal base. No new browser rendering or native session ran in this milestone.

This resolves reference-panel ownership for appended vectors. Primitive/material/GLB and other panels still need enlarged-table compatibility checks, followed by Retail/native allocated-vector package qualification. New object/group allocation, animation import and the broader scene/runtime specification remain incomplete. No game was launched or controlled; offline work and the full goal remain active.


**Allocated-vector editor compatibility (2026-10-03):** Primitive sources now emit V5 allocation ownership per object, derived from the qualified ledger and checked against Retail/Current table counts. The browser accepts enlarged tables only with matching growth, bounded native indices and unchanged retained/authored face ownership. Existing faces can reference appended vertices/normals; resetting a retained face restores its Retail references without removing allocated rows. The main vector editor labels rows without Retail counterparts and disables their Retail reset while retaining Current edit/discard behavior.

Validation: 34 focused Python tests ran, with 31 passing and three existing Retail-fixture skips. Actual synthetic V5 models with and without a retained-removal base passed primitive edit/reset and Undo/Redo, material editing, and real GLB no-op/export/import roundtrips editing an allocated vertex. Actual backend primitive/material/GLB sources and reviews qualify in their JavaScript adapters. Four Node suites pass, including mounted vector-handler regression checks for allocated vertices, the first normal in an empty Retail table, retained resets and invalid indices. Editor syntax and diff checks pass. No game was launched; this milestone does not establish live rendering or gameplay acceptance. Retail/native allocated-vector package qualification, topology allocation through GLB, new objects/groups and the broader SDK specification remain unfinished.


**Retail allocated-vector package qualification (2026-10-03):** An isolated copy of the Retail Town01 project appended two vertices and one normal to model 9, then added a donor-qualified face referencing vertices 71/72. The new stored normal remains unreferenced in this Retail case; synthetic lit-face tests separately cover references to allocated normals. The final model grew from 4,752 to 4,796 bytes (24 vector bytes plus a 20-byte face). Normal format-7 Build emitted one relocation payload and no overlays. Exact packed model readback includes the prior neighboring model-8 edit; all 112 unselected slots and five other scene resources remain byte exact, allowing only zero allocation padding. Build preserved authored state, saved project reopen passed, package integrity/current-input checks passed, and private RunService staging started no process.

A fresh isolated native harness compiled from current runtime sources at ce337cb8 activated the SDK-emitted package, read every replacement PROT user/raw sector, checked raw address/subheader/EDC/ECC framing, read all metadata patches and confirmed netplay clear restored the stock sector count and relocation state. PROT grew by one sector to 121,255,936 bytes; the 121,272,992-byte relocation payload has SHA256 `62e7f529e61af19246372bf2f970d75d97798cb41111adad2fdfe702eaf32280`. Private proof/scripts/source hashes are under `local-output/sdk-20260909/retail-vector-allocation-build-20261003/parent/`. No game executable was launched, no user runtime installation occurred, and no full Retail disc was exported. Native reader acceptance does not establish rendered geometry, lighting, animation or gameplay behavior. Those checks remain queued; broader SDK buildout continues solo.


**Reviewed standard GLB mesh append (2026-10-03):** Added a model-editor workflow that imports static GLB positions and triangle lists into the selected Current native triangle donor's object. Indexed and nonindexed geometry uses the existing bounded accessor reader, shares repeated source POSITION rows, reflects Y/reverses winding, rounds to signed native coordinates and rejects degenerate post-quantization faces. The command appends vertices and donor-layout faces through V5 replay, then publishes both allocations as one reviewed Undo step. Native donor UVs, baked RGB, normal references, packet flags and material bindings are retained; supported GLB display attributes are validated and explicitly excluded from import. No external resources are fetched.

The dialog offers file/donor selection, Current/Proposed rendering, orbit/zoom and a concise review summary. File/donor/context changes withdraw Apply. Apply is bound to the uploaded file hash, donor, source key and reviewed candidate; close/abort/busy handling retains ownership. The SDK serves the module and advertises the capability. One scene, one untransformed mesh node and triangle lists are accepted; skinned/animated/morph geometry, unknown attributes, nonidentity object transforms and quad-only donor models are rejected. New native objects/groups, imported normals/UV/colors/materials, general hierarchy and replacement topology remain unfinished. This is an append workflow, not complete arbitrary-model replacement.

Validation: 13 focused Python tests pass, including standard indexed/nonindexed axes/indices, malformed ownership/transforms, signed bounds and degenerate rounding, read-only review, one-step history, Save/Open, normal synthetic-disc Build with exact model readback, actual HTTP/module GET, changed-file review rejection and stale/repeated Apply. Actual backend reviews qualify in JavaScript before and after an append using a new authored donor, with vector/face/render-attribute/ownership tamper rejection. Isolated headless Edge rendered actual synthetic backend reports with the real scene renderer; both layers, changed-donor/stale-context withdrawal and a single exact reviewed Apply passed, and the screenshot was inspected. The browser smoke uses fixture-backed HTTP responses, not the complete styled editor/server session. Private evidence is under `local-output/sdk-20260909/mesh-append-browser-20261003/parent/`. Retail/native qualification of this GLB workflow and gameplay appearance remain pending. No game was launched or controlled, and the broader SDK goal remains active with solo implementation.


**GLB append normal allocation (2026-10-03):** Standard GLB NORMAL attributes now decode alongside appended positions/triangles. Referenced directions must be finite and nonzero; the importer normalizes them, reflects Y and rounds them to signed Q12 components. Lit Gouraud donors retain per-corner directions. Lit flat donors require equal converted corner directions rather than averaging away an unrepresentable layout. New stored normals are deduplicated and allocated with vertices in the same V5 operation; new face references bind their exact appended native indices. Missing-normal faces retain donor references, and unlit donors allocate no normal rows. V2 geometry/review metadata records normal conversion, allocation ranges, per-face references and imported-face counts; the browser independently checks those relationships. Donor labels now distinguish Lit Flat, Lit Gouraud and Unlit, and the review summary displays imported normal/face counts.

Validation: 14 focused Python tests pass. Actual lit fixtures verify converted stored XYZ words, complete per-corner indices, combined one-step Undo/Redo, Save/Open and normal synthetic-disc Build with exact packed-model readback. Cases cover flat equality/rejection, mixed primitives with missing normals, unlit inheritance, zero directions, standard indexed/nonindexed geometry, HTTP/review identity and existing allocated-row editing. Actual Gouraud/flat/unlit backend reviews qualify in JavaScript and reject zero/changed directions, counts, indices and allocation ownership. An isolated headless Edge smoke rendered the V2 lit report with the real scene renderer, verified both layers, donor/context review withdrawal and one reviewed Apply; the screenshot was inspected. Private fixture-backed browser evidence is under `local-output/sdk-20260909/mesh-append-normals-browser-20261003/parent/`. This supersedes inherited-only normals for compatible mesh appends. Imported UVs/colors/materials, native object/group creation, replacement topology and the broader SDK specification remain unfinished. No live lighting or gameplay acceptance is claimed; Retail/native GLB workflow qualification and gameplay checks remain queued. No game was launched or controlled, and solo offline work remains active.


**GLB append UV import (2026-10-03):** Standard TEXCOORD_0 arrays now decode per triangle with the same winding conversion as positions/normals. For textured donors, the importer derives the Current UV rectangle of all packets sharing the selected CLUT/TPage binding and maps normalized mesh UVs into that explicit region. Conversion follows the existing texel-center convention, clamps half-texel crop edges and reports integer rounding error. Imported UVs are written into each new native packet while donor materials, palette/page words, colors and packet flags remain unchanged. Missing UVs retain donor values; untextured packets ignore mesh UVs. Coordinates outside 0..1 are rejected for textured imports rather than inferring wrapping/sampler state. V3 geometry/review reports expose region, converted values, imported-face count and rounding; the browser independently verifies the binding, conversion and proposed triangle UVs. The review summary identifies the target region and texel rounding.

Validation: 17 focused Python tests pass. A combined positions/normals/UV import verifies literal native UV coordinates, normal references, unchanged material words, read-only review, one-step Undo/Redo, Save/Open and normal synthetic-disc Build with exact packed-model readback. Cases cover missing-UV primitives, untextured donors, rejected wrapping with unchanged history/files, and browser rejection of changed regions, binding words, counts, packet UVs and proposed render coordinates. Existing mesh/normal allocation and allocated-row editor checks remain passing. Isolated headless Edge rendered actual V3 synthetic backend geometry with an explicitly synthetic checkerboard texture; both layers, changed-donor/stale-context withdrawal and one reviewed Apply passed, and the screenshot was inspected. Private evidence is under `local-output/sdk-20260909/mesh-append-uv-browser-20261003/parent/`. The checkerboard is a crop-mapping smoke, not Retail texture association or gameplay acceptance. This supersedes inherited-only UVs for compatible appends. New images/materials, baked-color import, native object/group creation, replacement topology and the broader SDK specification remain incomplete. Retail/native GLB workflow and gameplay checks stay queued; no game was launched or controlled and solo offline work remains active.


**GLB append baked color import (2026-10-03):** Standard COLOR_0 arrays now decode per imported triangle, including FLOAT and explicitly normalized unsigned byte/ushort RGB/RGBA accessors. Normalization is an opt-in shared-reader path, leaving existing fixed-layout GLB readers' defaults intact; buffer ownership also rejects boolean buffer IDs. Unlit native packets import colors with explicit native semantics: textured colors map linear modulation to neutral 128, while untextured colors invert the established export's linear/sRGB conversion into display-referred byte RGB. Gouraud donors preserve per-corner colors; flat donors require equal converted corners. Missing colors inherit the donor, lit packets ignore mesh colors, and nonopaque per-corner alpha is rejected for baked RGB. Native material, palette/page, command and packet-layout ownership remains unchanged. V4 review metadata exposes conversion mode, exact RGB fields and rounding; the browser independently qualifies those fields and proposed render colors. Donor labels distinguish Unlit Flat/Gouraud, and the review summary reports baked-color face count.

Validation: 26 focused Python tests pass, including existing fixed-layout GLB codec checks. Combined positions/UV/color commands verify literal packet RGB, UVs and unchanged materials, read-only review, one-step Undo/Redo, Save/Open and normal synthetic-disc Build with exact model readback. Additional cases cover normalized byte/ushort data, missing normalization, color domains, flat/untextured/lit ownership, missing-color primitives and rejected alpha with unchanged history/files. Actual textured, untextured-flat and lit backend reviews qualify in JavaScript and reject changed modes/counts/rounding, RGB fields and proposed colors. Isolated headless Edge rendered actual V4 synthetic backend reports with Gouraud RGB gradients; both layers, donor/context review withdrawal and one reviewed Apply passed, and the screenshot was inspected. Private evidence is under `local-output/sdk-20260909/mesh-append-color-browser-20261003/parent/`. This supersedes inherited-only colors for compatible unlit appends. Standard textured colors do not import amplification above neutral 128; native RGB editing remains separate. New mesh images/materials, native object/group creation, replacement topology, animation import and the broader SDK specification remain unfinished. Retail/native GLB workflow and gameplay appearance remain queued. No game was launched or controlled; solo offline work and the full goal remain active.


**Retail GLB append package and native reader qualification (2026-10-03):** A private Retail Town01 project imported four GLB vertices and two triangles into model 0009, including normalized UVs and baked textured RGB. Review left project/history/files unchanged; Apply published one Undo step, Undo/Redo restored exact bytes, and Save/Open retained the result. Native packet readback confirms imported vertex references, UVs and RGB while preserving donor material words. Model size grew from 4,752 to 4,824 bytes (72 bytes); final model SHA-256 is `3c76b154c754938e6ab030d9e25a8e1895f7ca5d811db603c695af415619c7d1`. Normal Build preserved the prior model 0008 edit, all 112 unselected model slots and five other scene resources, with only allocation padding permitted. Saved Build integrity and private staging passed without changing project state.

The sole relocation payload is 121,272,992 bytes, SHA-256 `114ff9deadf54bcb41807a685ed76060196a728ffb2dd341192b848f9064554a`; proposed PROT is 121,255,936 bytes with one extra sector. A freshly compiled native reader harness at SDK revision `d9720e39` activated that emitted package against the unchanged Retail source, checked every replacement PROT user sector and raw sector (address, subheader, EDC/ECC), read all patched metadata, and cleared relocation state/sector count for netplay. Source disc SHA-256 remains `e6120a5d70716dd2f026a2da32d0171d52651971b52c4347a68541299f75258c`. Private proof, source hashes and harness are under `local-output/sdk-20260909/retail-glb-append-build-20261003/parent/`.

This qualifies the positions/UV/baked-color append through Retail packaging and the native reader. The selected donor is unlit, so NORMAL was explicitly ignored and no new normals were stored; lit normal allocation retains synthetic test coverage, not this Retail/native proof. Gameplay appearance, full-scene parity, new native objects/groups, mesh replacement/images/material allocation, animation import and the broader SDK specification remain unfinished. No game was launched or controlled, no full Retail disc was exported, and solo offline work remains active.


**GLB triangle strip/fan append (2026-10-03):** Static mesh append now accepts glTF TRIANGLES, TRIANGLE_STRIP and TRIANGLE_FAN primitives (modes 4/5/6). Strips alternate source winding; fans retain their anchor before the existing Y reflection and winding reversal. Every expanded corner retains its matching normal, UV and color. Indexed and nonindexed inputs produce the same typed triangle append operations and use the existing review/history/native donor gates. Expanded face count is bounded at 128 across all primitives; unsupported modes, incomplete inputs, out-of-range indices and triangles degenerate after native quantization are rejected. Degenerate strip connectors are not silently discarded.

Validation: 29 focused Python tests pass, including fixed-layout GLB regressions and three new mode cases. Independently specified odd/even strip and fan corners verify native position/normal/UV/color associations. Both modes exercise actual reviewed Apply, one-step Undo/Redo, Save/Open, normal synthetic-disc Build with exact model readback, and JavaScript qualification/tamper rejection using actual backend reports. No separate rendered browser smoke or Retail/native strip/fan run is claimed; the prior Retail/native proof covers triangle-list GLB input. The existing editor accepts the unchanged triangle review schema. New native groups/objects, replacement meshes/materials/images, animation import, full-scene parity and the broader SDK specification remain incomplete. Gameplay appearance remains deferred; no game was launched or controlled and solo offline work remains active.


**Native packet-group allocation foundation (2026-10-03):** Added a bounded codec that creates new native primitive groups at an object's explicit terminator. Each request owns a UUID group identity and typed UUID face identities, selects a qualified same-object donor group, and supplies donor packet vertex/UV/RGB/normal-reference fields. The codec inherits descriptor bytes and opaque footer exactly, sets the new group count, preserves all retained packets and unowned bytes, updates object primitive counts and rebases used vertex/normal/primitive pointers. Unused pointers remain unchanged. Several new groups and several objects can grow in one candidate; later allocation may use a newly created group as donor. Qualification recomputes the entire candidate from source bytes and typed requests. Limits are 64 groups and 128 faces per operation plus the existing model-byte budget.

Validation: 20 focused Python cases ran, 18 passed and two existing Retail-dependent primitive tests were skipped. Four new allocation cases exercise all 24 supported native flag variants across multiple objects/groups; exact descriptors, opaque footers, retained packets and complete unowned-byte reconstruction; typed Gouraud UV/RGB and lit normal indices; repeated allocation and existing face extension of a new group; unused pointers; identity/owner/donor/field/count/budget errors; immutable requests and exact candidate tamper rejection. No Retail/native package, browser or game check ran for new-group allocation.

This is allocation infrastructure, not a published authoring workflow. Stable replay-ledger group ownership, removal/restoration composition, project command/history/persistence/Build integration and editor review controls remain next; users cannot yet create groups through the editor. Donor-layout inheritance does not invent new packet families or create native objects. Mesh replacement/images/material allocation, animation import, scene/runtime parity and the full SDK specification remain unfinished. Gameplay stays deferred and solo offline work remains active.


**Stable native-group replay and Build consumers (2026-10-03):** V6 ledgers now carry typed `allocate_groups` operations using stable group and donor-face identities. Replay resolves all packet donors in the selected Current group, qualifies allocation through the native codec and chains exact input/output hashes. New group origins are permanent per-object ordinals after the base groups; they survive Current compaction, later face additions, full-group deletion, intervening new allocation and restoration. Authored group/face identities remain reserved after deletion. The audit exposes historical group count, allocation count and stable group IDs with explicit Current index or null when absent. V6 preserves prior vector/content/removal/restoration operations and enforces cumulative 64-group, 128-face, eight-addition-batch and 64-operation budgets. Earlier versions cannot replay group allocation.

Existing enlarged-vector primitive sources, reference-user inspection and rigid pose preview recognize V6 vector ownership. An internal qualified binding passes existing project reads, later vector-edit and primitive-edit history, Save/Open and normal synthetic-disc Build with exact packed model bytes. The group fixture installs the binding internally; it does not exercise a new-group project command or UI. Current V5 previews transitioning to V6 retain pose channels, appended vertex rows and complete new triangle data without mutating shared inputs.

Validation: 35 focused Python tests pass. New cases cover stable roots and ordering through deletion/intervening allocation/restoration, mixed V5/V6 vectors and lit references, content edits, tombstones, donor ownership, version/hash/schema rejection, cumulative limits, JSON replay, persistence/Build and pose composition. Actual V6 primitive source/review reports also pass the JavaScript adapters; new-group reference users have no invented Retail vector coordinates. Material-group ownership compatibility, new-group project/API/review controls and broader browser workflow remain unfinished, as do native objects, mesh replacement/images/material allocation, animation import and full-scene/runtime parity. No Retail/native V6 package, rendered browser smoke or gameplay acceptance is claimed; no game was launched or controlled. Solo offline work and the full goal remain active.


**Authored-group material ownership and editor compatibility (2026-10-03):** Material source V4 represents each allocated Current group with a null Retail group mapping and a stable authored group ID. V6 replay records the inherited creation flags/mode, allowing protected descriptor comparison without assigning a donor's Retail identity to the new group. Ordinary face extensions inherit the authored ownership; deletion removes the active group entry and restoration recovers its stable ID. Retained groups keep their existing Retail mappings. Material Review/Apply continues to audit against Current topology, including exact shared-group membership. The browser adapter qualifies all authored-group IDs, complete null-owner mappings, packet ownership and protected descriptor bits. The material panel renders absent Retail values explicitly, disables and guards Retail reset for authored groups, and keeps Current texture-binding and shared semitransparency authoring available.

Validation: 33 focused Python tests ran, 31 passed and two existing Retail-dependent tests were skipped. Three new cases verify literal source ownership, reviewed primitive/group material changes, no mutation during Review, stale-review rejection, one-step history, Save/Open, removed-base composition, deletion/restoration and fixed-layout GLB no-op export/import on V6 topology. Actual V4 source/review reports pass JavaScript and reject changed IDs, flags/mode, Retail mappings, missing/duplicate group owners, incomplete face ownership and changed shared-group audit membership. The normal synthetic Build fixture now includes an authored-group material edit and reopens exact final packed-model bytes. Existing Node material workflow and syntax checks pass.

An isolated headless Edge smoke mounted the real material panel against actual synthetic backend reports with fixture HTTP responses. It rendered the authored group with absent Retail values, guarded disabled Reset, reviewed group semitransparency, withdrew Apply on stale context and sent exactly one reviewed Apply. The screenshot was inspected; no page errors occurred. Private evidence is under `local-output/sdk-20260909/authored-group-material-browser-20261003/parent/`. This is panel/adapter evidence, not full styled-editor or Retail texture/rendering acceptance. New-group creation project/API/review controls, Retail/native V6 package qualification, native objects, replacement meshes/images/material allocation, animation import and full-scene/runtime parity remain unfinished. No game was launched or controlled; solo offline work and the full goal remain active.


**Reviewed group-allocation project command and HTTP path (2026-10-03):** Added group-allocation source/review APIs and an actual project command that recomputes the reviewed candidate, retains the independently qualified base binding and publishes one immutable model override/Undo step. Review keys bind stable group/face IDs, donor identities, typed fields, source key, Current hash and proposed bytes; changing an identity while leaving candidate bytes identical still invalidates Apply. Source reports expose Current native donors, complete geometry/topology and remaining group/face/batch/operation budgets. Review supplies exact allocation spans, descriptor/footer/packet hashes, pointer relocation audit and Current/Proposed native geometry. The server accepts only exact model/source/request/review fields and exposes the group-allocation capability. Review and source leave project/history/files unchanged; late source publication gates remain active.

The shared browser face-source adapter now recognizes V6 allocated groups. It qualifies historical group counts, stable UUID/root/Current ownership, complete active authored face lists, inherited flags and donor provenance across separate groups. Missing/conflicting allocation records reject; existing source groups retain their original provenance rules. This supports donor inspection after creation rather than treating an authored group's template as its Retail group identity.

Validation: 29 focused Python tests pass, including four new command cases, native group replay/Build consumers, authored materials and mesh append regressions. Actual command checks cover read-only review/files, same-byte changed-ID rejection, one-step Undo/Redo, Save/Open with retained topology, normal synthetic Build with exact packed-model bytes, independent base wrapping and stale publication. HTTP source/review/apply cases cover exact fields, malformed/stale requests, review-key rejection and repeated Apply. Actual post-creation face sources qualify in JavaScript and reject changed allocation ownership; existing Node face workflow/lifecycle tests and syntax checks pass. The creation dialog, its independent review adapter and editor action remain next; the API is implemented but no new-group creation UI is exposed yet. Retail/native V6 package and gameplay checks remain deferred. New objects, mesh replacement/images/material allocation, animation import, full-scene/runtime parity and the broader SDK specification remain unfinished. No game was launched or controlled; solo offline work and the full goal remain active.


**Packet-group creation editor workflow (2026-10-03):** The Edit model panel now exposes Create packet group. Its dialog selects a qualified Current donor, edits typed vertex/normal indices, UVs and RGB where supported, and reviews complete Current/Proposed native geometry before Apply. This initial UI creates one group with one triangle or quad using existing vector rows; Add model face can extend it afterward. The API supports multi-group/multi-face requests. Capability, pending shape edits, busy state, selected asset and project context gate the action. Input changes invalidate review, context changes dispose the dialog, requests abort on close, and Apply sends the bound review key as one project history step.

The independent browser adapter checks source budgets, packet-group coverage/stride/footer ownership, stored normal vectors and table pointers; review checks typed packet geometry, stable retained/new identities, exact insertion at the owner's terminator, nonoverlapping growth and pointer rebasing (including preserved unused table pointers). No new native objects, packet families, vector rows, images, animations or arbitrary replacement hierarchy are created.

Validation: 21 focused Python tests pass across project/API, native group allocation/replay/Build and authored materials. New checks qualify actual reports for all 24 supported packet flag variants across two objects, multi-group/multi-face requests and reject forged geometry, pointers, spans, identity and budgets. The real server serves the new JavaScript module. Existing Node face workflow/lifecycle checks and editor/module syntax checks pass. An isolated headless Edge smoke against actual synthetic backend reports renders both preview layers, invalidates changed fields, withdraws stale context, sends one reviewed Apply and releases busy state without page errors; screenshots were inspected. Private evidence: `local-output/sdk-20260909/group-creation-browser-20261003/parent/`. Browser fixture styling is not full styled-app acceptance. Retail/native V6 package qualification and manual gameplay remain pending. The broader SDK goal remains active; no game was launched or controlled.


**Retail V6 group-allocation package and native reader qualification (2026-10-04):** A private copy of the prior Retail GLB append project now applies a new two-face packet group in Town01 model 9 using an authored Current donor and existing imported vectors. Review remained read-only, Apply retained the independent base binding, V5 history replayed into V6, Undo/Redo was one step and Save/Open recovered exact final bytes. The model grows from 4,824 to 4,892 bytes, SHA-256 `d8f9fc5fc13544d8be6ebe88f9411b2283cb9323f13e7a5260f46c675d370e6b`. Actual Retail source/review reports qualify in the browser adapter.

Normal Build produced one format-7 relocation payload (121,272,992 bytes; SHA-256 `fd1af83a98d6203b1f27034d4b0a45133e1de1481d33f87428036694531dc55a`) and no duplicate overlays. PROT is 121,255,936 bytes, one sector larger than source. Build integrity/current inputs and unchanged authored project state passed. The prior neighboring model-8 edit remains exact; 112 untouched model slots and five other scene resources remain byte-exact, with only qualified padding. A fresh native reader harness compiled against runtime revision `c53d8b26` (executable SHA-256 `9ce3ccf8fae140e7253dc99ea1ab596c2a39ba3258ee852618713d7129a0bdd5`) activated private staging and read every emitted PROT user/raw sector, verifying raw addresses/subheaders/EDC/ECC, all metadata patches and netplay clear. Harness compile emitted existing CRT/conversion warnings. Retail source hash remains `e6120a5d70716dd2f026a2da32d0171d52651971b52c4347a68541299f75258c`.

Private evidence: `local-output/sdk-20260909/retail-group-allocation-build-20261003/parent/` (`proof.json`, source/review reports, qualifier scripts, fresh harness and staging). This qualifies package/reader delivery, not game rendering, collision or camera behavior. No game process, user-runtime installation or full Retail disc export occurred. Manual group visibility/gameplay checks remain deferred; new native objects, arbitrary replacement hierarchy/images/material allocation, animation import and full-scene/runtime parity remain unfinished. The full SDK goal remains active.


**Native object-allocation codec foundation (2026-10-04):** Added a pure byte codec for allocating up to 64 independent objects from qualified Current native donors, subject to the 1,024-object and 4 MiB model limits. Requests carry distinct authored object UUIDs and exact donor indices. The object table expands without changing retained object indices; existing used pointers rebase, unused pointers stay exact and the entire original post-table byte suffix remains intact. Each appended object independently copies its donor's complete qualified primitive allocation (including descriptor/footer/opaque tail), signed vector rows/pads and opaque object metadata. New allocations align to four bytes; counts/pointers/native spans and source/proposed hashes are audited. Exact candidate recomputation rejects any unowned mutation. Donors require a nonempty qualified vertex table; no rig, pose, scene hierarchy or animation ownership is inferred.

Validation: three targeted cases pass across all 24 supported packet flag variants, multiple objects/groups, repeated and newly allocated donors, unowned source tails, absent normal tables, header/size/request/hash gates and independent new-object packet edits; four existing native-group codec cases also pass. This is byte-codec groundwork only. Stable object/face/group ledger provenance, project Review/Apply/history/Build integration, existing editor consumers and creation controls are not connected yet, so no object-creation capability is exposed. No Retail object package or gameplay acceptance is claimed; the full SDK goal remains active and the game stays closed.


**V7 object provenance, reviewed project command and synthetic Build (2026-10-04):** Object allocation now has a stable ledger operation. Each clone references a stable Current object ID and supplies new UUIDs covering every donor group and face in native order. Replay qualifies the independent byte codec, records donor ancestry for each authored object/face and retains source object indices. New objects and their copied groups have permanent roots; face deletion/restoration, additional groups/faces, vector allocation and typed content edits preserve V7 and stable ownership. IDs remain reserved after face deletion. Copied native vectors, groups and faces count against cumulative 4,096-vector, 64-group, 128-face, eight-batch and 64-operation limits, alongside the 64-authored-object limit. Empty native groups reject in this ledger workflow; a group-free object with a qualified nonempty vertex table can be represented.

The SDK object source/review adapter exposes Current stable object donors, complete native previews, remaining budgets and exact allocation spans/pointer audit. The actual project command binds all object/group/face identities and donor choices into its review key, independently recomputes the candidate, retains the existing base binding and publishes one immutable override/Undo step through the existing late source gate. Same candidate bytes with changed identity cannot reuse the review. Source/Review remain read-only. V7 bindings Save/Open and build through the normal synthetic relocation path with exact packed-model bytes, without changing authored state during Build.

Validation: 25 focused Python cases pass across object codec/provenance/project command and existing V6 group/material/Build paths. New coverage checks deterministic JSON replay, cloned authored objects as later donors, full-group deletion followed by new allocation and restoration, independent content/vector edits, schema/hash/identity/coverage/budget rejection, unchanged Review files/history, one-step Undo/Redo, Save/Open, exact normal synthetic Build and stale publication. Group review now shares reserved-group extraction with object operations. Object-creation HTTP/editor controls, V7 authored-object inspection/material/vector/pose consumer ownership and Retail/native object-package evidence are still pending. No object-creation capability is exposed yet; no rig/scene hierarchy or animation channels are inferred. No game was launched or controlled; the broader SDK goal remains active.


**Authored-object packet/vector inspection and edit compatibility (2026-10-04):** Primitive source V6 now carries complete stable object mappings on V7 models. Retained objects keep their original Retail index; cloned objects have a null Retail counterpart and explicit stable donor-object ancestry. Face mappings cover every Current object: authored objects have an empty Retail face map and complete authored face IDs. Vector growth includes all independently copied rows, and qualification checks its total against complete V7 replay. Packet Review/Apply can edit an authored object's existing vertex/normal/UV/RGB fields and retain V7, identities and one-step history.

Stored vertex/normal reference sources V4 carry the same object ownership. Copied objects have zero Retail vector count, null Retail coordinates, empty Retail users and complete Current authored face references. The browser adapters qualify stable object ID syntax, source indices, donor-before-clone ancestry, complete mappings, native counts and authored face coverage; they reject invented Retail ownership, self donors, changed identities and forged growth. Existing reference panels disable the absent Retail layer and navigate using the authored face identity.

Validation: 12 focused Python cases pass across V7 object inspection/project commands and earlier allocated-vector/editor/group Build consumers. Actual V7 source and complete packet-review reports qualify in JavaScript; forged object/face/vector ownership rejects. Existing Node primitive, vertex/normal and post-addition reference suites pass. The real HTTP server serves the shared object-ownership adapter. A headless Edge smoke mounts the real reference panels against actual synthetic reports, verifies disabled Retail layers, authored-face navigation and stale-context withdrawal with no page errors; its screenshot was inspected. Private evidence: `local-output/sdk-20260909/authored-object-references-20261004/parent/`. Fixture styling is not full styled-editor acceptance. Material/GLB/pose/shape consumer ownership, object-creation HTTP/editor controls and Retail/native object package qualification remain next. No game was launched or controlled; the full SDK goal remains active.


**Authored-object materials, GLB editing and explicit preview pose scope (2026-10-04):** Material source V5 now carries stable V7 object mappings. Groups copied into a new object receive authored ownership with no Retail object/group/face counterpart; later face extensions preserve that ownership. Source/review browser adapters qualify the object ancestry and complete authored group/face membership while retaining protected descriptor bits. Existing material Review/Apply supports inherited texture selectors and shared group semitransparency on these objects, retains V7 and stable IDs, and preserves one-step history and Save/Open. Retail reset stays disabled and guarded.

The V7 shape-preview composer now handles expanded native object tables. It qualifies candidate/hash/ledger continuation and retained vertex spans, preserves only evidenced original pose channels and explicitly labels all remaining objects as unposed. Copied objects never receive a donor's pose/bone channel; a forged channel extending into a new object rejects. Known source pose prefixes and frame bounds are retained while full Current geometry is displayed. This unlocks fixed-layout Current GLB export/import on V7: unchanged files round-trip, and edits to a copied object's exported native vertex rows publish through existing typed content/history handling without inventing a new hierarchy or rig.

Validation: 18 focused Python cases pass across authored-object material/GLB/preview, earlier authored-group/material/vector consumers and object project Build paths. Actual material source/review reports qualify in JavaScript and reject invented Retail owners, self donors, missing group owners and changed protected flags. Targeted pose checks cover unposed geometry, retained pose prefixes, frames, later Current continuation and forged channel/hash/ledger rejection. Existing Node material workflow checks pass. A headless Edge smoke mounted the real material panel against actual synthetic reports, rendered inherited fields with absent Retail values, guarded disabled Reset, withdrew stale Review and sent one reviewed Apply with no page errors. Screenshot inspected; private evidence: `local-output/sdk-20260909/authored-object-material-browser-20261004/parent/`. Fixture styling is not full styled-editor or game rendering acceptance.

Object-creation HTTP/editor controls, remaining animation/scene consumer integration and Retail/native object-package qualification are still pending. General replacement meshes, image/material allocation, animation import and full-scene/runtime parity remain unfinished. No game was launched or controlled; gameplay stays queued and the full SDK goal remains active.


**Object-allocation HTTP source/review/apply and shared donor compatibility (2026-10-04):** Added exact-field HTTP routes for object allocation source, preview and reviewed Apply. They require a model, current source key/hash, bounded stable requests and the reviewed identity key. Source reports now include each Current object's native table offsets, opaque metadata, complete packet-group counts/order and hashes for primitive allocation and padded vertex/normal tables. Review remains read-only; Apply uses the actual project command and late source gate, publishing one immutable override/history step. No object-creation capability or button is exposed yet.

The shared face donor adapter now qualifies V7 object ancestry and permits cross-object donors only through the copied object's explicit stable donor-object relationship and authored group ownership. Source objects remain bound to the ledger base hash/index; copied objects cannot acquire source face identities. Self donors and forged object history reject. This allows existing face/group donor inspection after object creation rather than rejecting legitimate copied provenance.

Validation: 14 focused Python cases pass across object HTTP/project commands, V7 primitive/vector consumers, group commands and authored-object material/GLB paths. HTTP cases cover read-only project/files/history, extra fields, malformed/bounded requests, stale source/hash, bad review keys and repeated Apply. Actual V7 face and group sources qualify in JavaScript; forged source indices, self ancestry, object budgets and face self-donors reject. Native source group coverage is checked. Existing Node face workflow/lifecycle and syntax checks pass. The independent object review adapter and Current/Proposed creation dialog are next; Retail/native object package, remaining animation/scene integration and gameplay remain deferred. No game was launched or controlled; solo offline work and the full SDK goal remain active.


**Native object creation editor (2026-10-04):** The model editor now exposes Create native object in Edit mode with a bound disc. It copies one complete qualified Current donor into independent native primitive, vertex and normal allocations, including authored V7 donors. The independent browser adapter qualifies stable ancestry, complete packet/group order, signed vectors, geometry/bounds, table expansion and pointer rebasing, copied-span hashes, opaque metadata and cumulative allocation/history budgets before enabling Apply. Current/Proposed orbit/zoom comparison is available. Donor changes invalidate Review; closed or changed project/scene/source/model contexts withdraw the dialog; Apply requires the exact reviewed request/key and uses one existing project Undo step.

Validation: 17 focused Python cases pass across object byte/ledger/project/HTTP, browser qualification, authored consumers/materials and preview paths. The browser qualifier now exercises both multiple initial clones and cloning an authored V7 donor, rejecting forged geometry, pointers, spans, counts and stable ancestry. Headless Edge mounted the real dialog against actual synthetic backend source/review reports: Current/Proposed rendered, donor changes invalidated Review, stale context withdrew the dialog, one reviewed Apply was sent, busy state released and no page errors occurred. Screenshot inspected. Private evidence: `local-output/sdk-20260909/object-creation-browser-20261004/parent/`. Fixture styling does not establish full styled-editor or gameplay rendering acceptance.

Copies start at the same object-local coordinates and inherit Current material settings; they have no newly assigned pose/animation channel. Arbitrary object layouts, rig creation and scene-instance creation are outside this command. Retail/native V7 object-package qualification and remaining animation/scene consumers are next offline work; manual game rendering, pose/lifecycle and scene parity remain deferred. No game was launched or controlled. Solo work and the full SDK goal remain active.


**Retail V7 object package and native reader proof (2026-10-04):** In a fresh private copy of the prior Retail V6 group/vector project, Town01 model 9 now has one complete lit native object clone (donor object 1: 13 faces, 18 vertices and 11 normals). V7 retains the prior authored face/group/vector history, original object indices, stable clone ownership and base binding. Review is read-only; Apply is one Undo step, with Undo/Redo and Save/Open confirmed. Model bytes grew 4,892 to 5,500 (+608), SHA-256 `fd79db3d2b265c017f133e78f8de46194316e33884eb7de1fd955a42baeba4f5`. Actual Retail source/review reports also passed independent JavaScript geometry/identity/allocation qualification.

Normal Build emitted one format-7 PSXDRLOC payload, 121,272,992 bytes, SHA-256 `97cdf08171b04a5aa3b52293fe2d0ae8d6c90c341e0febf234c2479ebf90a58c`, with no duplicate model overlays. PROT is 121,255,936 bytes (+one sector from Retail). Packed readback matches the full V7 model and retained model 8 edit; 112 unselected model slots and five other scene resources remain byte-exact (qualified carrier padding only). Saved Build integrity/current inputs and unchanged authored state during Build passed. The bound disc hash remains `e6120a5d70716dd2f026a2da32d0171d52651971b52c4347a68541299f75258c`.

A fresh MSVC native reader harness at `c5277f3d` activated only private staging, read every relocated PROT user/raw sector and metadata patch, independently qualified Mode2 address/subheaders/EDC/ECC, and restored vanilla reader state through netplay clear. Evidence: `local-output/sdk-20260909/retail-object-allocation-build-20261004/parent/proof.json`. No full Retail disc export, user-runtime installation or game launch/control occurred. This establishes emitted-package/native-reader delivery, not in-game object rendering, animation/pose assignment or scene parity. Those manual checks remain queued; remaining animation/scene consumers and broader SDK work remain active and solo.


**V7 coordinated scene animation and normal scope (2026-10-04):** Fixed the scene sampler's assumption that every Current native object has an animation channel. V7 shape previews retain only the evidenced existing channel prefix; scene tracks now qualify and expose that prefix plus explicit unposed native object indices and vector boundary. Every scoped frame must reproduce the original channels and retain all unposed vectors exactly, even when normal preview is omitted by its budget. Canonical scene scope, frame ownership, PSX rotation words and full mesh/material mappings remain qualified. Missing scope, invented clone channels and moved unposed vectors reject.

Normal sampling rotates evidenced objects only and retains unposed native object normals in object-local coordinates. The browser independently qualifies scope/ranges, constant unposed vertex suffix, exact normal scope and channel count. Scene source coverage visibly lists existing channel count and unposed indices. Existing all-channel tracks retain their format and behavior; no new animation/bone channel, hierarchy, record or game schedule is allocated.

Validation: 11 focused Python cases pass across scene sampling, actual V7 shape composition and the new scope integration. A complete synthetic lit object clone feeds the real sampler and JavaScript decoder; posed geometry moves while copied vectors/normals stay fixed. Forged scope/channel/rotation/vector changes reject, including with normal budget zero. Existing Node scene-controller and rigid-normal renderer checks pass. Headless Edge mounted the real scene controller and renderer against the actual synthetic report, displayed scope, scrubbed the track, retained cloned vectors/normals, restored baseline and released busy state with no page errors. Screenshot inspected; private evidence: `local-output/sdk-20260909/scene-animation-object-scope-20261004/parent/`. This is a focused synthetic integration/render check, not full styled-editor, Retail clip, or gameplay acceptance.

Remaining animation/scene consumers, general animation allocation/import/retargeting, full-scene/runtime parity and other SDK buildout requirements remain unfinished. Game rendering, pose/lifecycle and coordinate checks remain deferred. No game was launched or controlled; the full goal remains active and solo.


**Individual V7 model normal diagnostic compatibility (2026-10-04):** Fixed the model viewer's shared normal sampler to accept the V7 shape composer's explicit pose marker and unposed-object indices, as well as the scene sampler's structured scope. Both forms qualify through the same bounded prefix/range checks. Cloned objects retain source-local normal vectors while only evidenced existing channels rotate. Unknown scope, non-trailing exclusions and invented clone channels reject; no channel is inferred from a donor.

The actual V7 model-preview/scene-report integration first reproduced the rejection, then passed after the adapter repair: frame normals from both views match exactly. Four focused Python cases and the existing Node rigid-normal renderer checks pass. This is a model/scene adapter compatibility check; no additional Retail or gameplay rendering claim is made. No game was launched or controlled. Manual verification remains queued and the full SDK goal remains active, solo.


**Retail actor V7 model/scene animation evidence (2026-10-04):** A fresh private project copy now qualifies the complete authored-object preview path against Town01 actor `scene://town01/actors/man-p1/0005`, model `asset://town01/models/scene-tmd/0112` and its verified MAN-associated clip `animation://town01/scene-anm/0056`. A complete Current donor object 2 clone expands six native objects to seven. All six original rigid channels and 30 frames remain evidenced; object 6 has no assigned channel. The raw clone suffix begins at vertex 128 and stays unchanged through the entire clip.

The actual EditorServer coordinated scene service admitted 22 tracks and 42 animated instances, explicitly reported ten static/unavailable instances, and retained unchanged project/history during sampling. The browser decoder qualified the full 68,217 frame-vertex report. Every frame's model-view normal sample exactly matches the scene-view sample; original Retail animation changes while the cloned object's vertices and normals remain static. Evidence: `local-output/sdk-20260909/retail-actor-object-animation-20261004/parent/proof.json`. No substitute synthetic clip was used for this milestone.

This establishes offline Retail clip/model/scene consumer compatibility. It does not establish rendered Retail browser acceptance, a new game animation channel, the scene's initial pose matching current gameplay, or in-game rendering/lifecycle. No game launch/control, user-runtime installation or full disc export occurred. Manual checks remain deferred; broader SDK allocation/interchange, scene/live parity and other specification requirements remain active and solo.


**GLB import into an independent native group — project/API (2026-10-04):** Mesh append now supports an explicit boolean `new_group` option in the ordinary source-qualified Review/Apply API. It allocates imported vertex/normal rows and one complete native packet group atomically in the selected Current donor object, preserving retained faces/groups and the existing GLB POSITION/NORMAL/UV/RGB conversions. The donor supplies the qualified packet layout, descriptor mode, material binding and opaque footer; imported faces receive stable identities in their independent group. The original append-to-donor-group behavior remains the default.

New-group reports use review V5 and carry the exact group request. The review key binds that mode and stable group/face requests in addition to the file, source, geometry and donor, so a review from one mode cannot authorize the other. Apply re-prepares the candidate and publishes one immutable project/history step. Existing cumulative face/vector/group/history bounds remain enforced through ordinary ledger replay. Imports into a copied V7 object retain stable object ownership and V7 rather than acquiring a Retail counterpart.

Validation: three focused new-group cases pass: read-only review/files/history, distinct mode hashes/keys, wrong-mode Apply rejection, retained packet fields, full new-group membership, one-step Undo/Redo, Save/Open, exact normal synthetic-disc Build, HTTP strict boolean/malformed/repeated Apply and copied-object V7 continuation. Four existing mesh-append cases passed during integration. Browser V5 qualification and a visible mode selector are the next implementation step; this milestone does not claim those controls are exposed. Retail/native delivery for this exact new mode and gameplay remain deferred. No game was launched or controlled. The full SDK goal remains active, solo.


**GLB independent-group browser workflow (2026-10-04):** The mesh import dialog now offers Append to donor group or Create independent group. The chosen mode is captured in Review, checked against V4/V5 report scope and submitted with the exact review key at Apply. Changing mode invalidates Review and hides comparison; pending/busy and stale project/scene/source/model contexts block Apply. The summary states whether imported faces share the donor's material group or form a separate group. Both modes retain the existing Current/Proposed orbit/zoom comparison and file/context lifecycle.

The mesh-specific source API includes qualified complete native group descriptors/footer hashes, raw normal vectors and next stable group-origin boundaries, including empty/deleted group history. Browser V5 qualification checks exact new group/face requests, stable identity reservation, retained group membership, group mode/flags, origin/current indices, V7 object ownership, ledger/budget increments and face ordering. It independently reconstructs complete Proposed packet geometry, normals and bounds from the Current donor plus imported attributes. Neither Review nor preview assigns a new object/pose/animation channel.

Validation: eight focused mesh/new-group Python cases pass; the actual browser qualifier covers repeated allocation, an authored V7 object and lit Gouraud normal import, rejecting forged mode/identity/index/ledger/normal/geometry/bounds fields. The actual new source HTTP route is checked. Headless Edge mounted the real dialog/renderer against actual synthetic backend reports: uploaded a GLB, reviewed both modes, rendered Current/Proposed layers, invalidated a mode change, blocked stale Apply and sent one reviewed new-group Apply with busy released and no page errors. Screenshot inspected; private evidence: `local-output/sdk-20260909/glb-native-group-import-20261004/parent/browser-proof.json`. Fixture styling is not full styled-editor acceptance. Exact Retail/native delivery for this mode and gameplay remain deferred; broader SDK requirements remain active, solo. No game was launched or controlled.


**Retail GLB independent-group package/native qualification (2026-10-04):** A fresh private copy of the Retail V7 object project now qualifies independent-group mesh import on Town01 model 36. Its native object 1 supplies a supported lit Gouraud triangle layout; a complete copy receives a new group with two GLB triangles, four new vertices, three Q12 stored normal rows and imported UVs. The actual source/review reports pass browser qualification, including complete reconstructed geometry, normal references/vectors, group ownership and bounds. The earlier model 8/model 9 edits remain part of the same project.

Mesh Review is read-only and Apply is one Undo step after the separate object-copy command. Undo/Redo, stable V7/base binding, Save/Open and unchanged authored state during Build pass. The mesh step grows the copied model from 12,172 to 12,308 bytes (+136), SHA-256 `c0b9b7cff8f34eabab923b4f6e0ed046f295a971d249b4bde0658834687bf517`. Normal Build emits one format-7 relocation payload, 121,272,992 bytes, SHA-256 `4a902b38602c59dd00d950314167ed96b1911660fb024180fcc00b8360fec3a4`; PROT is 121,255,936 bytes (+one sector from Retail), with no duplicate model overlays. Packed readback reproduces all three authored models while 111 unselected model slots and five other scene resources remain byte-exact (qualified carrier padding only). Saved Build integrity/current inputs pass; the bound Retail disc hash remains `e6120a5d70716dd2f026a2da32d0171d52651971b52c4347a68541299f75258c`.

A fresh MSVC native harness at `d0a60379` activates private staging and verifies every relocated PROT user/raw sector, metadata patch, Mode2 address/subheaders/EDC/ECC and vanilla reader restoration through netplay clear. Evidence: `local-output/sdk-20260909/retail-glb-group-build-20261004/parent/proof.json`. This establishes exact emitted-package/native-reader delivery for lit normal/UV imports into a separate group on an authored object; it does not establish in-game rendering, material appearance or object lifecycle. No user-runtime installation, game launch/control or full Retail disc export occurred. Manual checks stay deferred; arbitrary new layouts, texture/image/material allocation, general animation allocation/interchange and full-scene/live parity remain unfinished. Solo work and the full SDK goal remain active.


**Topology-changing GLB group replacement — project/API (2026-10-04):** Mesh import now supports an explicit `replace_group` boolean together with `new_group`. It imports the reviewed GLB into a qualified independent group, then retires exactly the complete Current donor group's stable faces in the same published project command. Original vector rows remain; the replacement appends its own vertices/compatible normals and retains donor layout/material inheritance and existing UV/RGB conversions. This changes group topology rather than accumulating visible old faces. It does not replace an entire multi-group object or allocate an arbitrary packet layout.

Review V6 reports the exact retired IDs and Current object/group selection. The key binds replacement mode and removal ownership as well as the imported group requests, file and proposed bytes. Applying an append/new-group review as replacement, or a replacement review as append/new-group, rejects. Three ledger operations (vector allocation, group allocation, face retirement) publish as one Undo step. Cumulative allocated identities/budgets are retained, retired faces stay reserved/restorable, group origin remains stable, and Current native indices rebase after the old group is removed. Copied-object replacement retains V7 and explicit authored group ownership.

Validation: three focused replacement cases pass: read-only Review/files/history, exact donor-face retirement and topology count change, wrong-mode key rejection, one-step Undo/Redo, Save/Open, exact normal synthetic-disc Build, stable no-Retail ownership mapping, ordinary retired-face restoration, strict HTTP boolean/independent-group requirements and stale/repeated Apply rejection. A copied V7 group's retired ownership is explicit and its resulting Current source passes the existing browser source qualifier. Existing four new-group cases passed during integration. Replacement V6 review qualification and the visible mode selector remain next; full material panel, Retail/native delivery for replacement and gameplay are not claimed by this milestone. No game was launched or controlled; broader SDK work remains active and solo.


**GLB donor-group replacement — browser workflow (2026-10-04):** The mesh import dialog now exposes Replace donor group alongside both append modes. Its V6 qualifier independently checks exact retired stable face IDs, Current group selection, surviving face and group index rebasing, allocated-group tombstones, three-operation budgets, imported face donor ownership and full typed packet reconstruction. Replacement reconstructs native material ordering rather than assuming append-only material indices. Original vector rows remain stored, and retired identities stay restorable. Mode changes and stale project context invalidate Apply; the reviewed request carries both exact booleans.

Validation: 12 focused Python/Node tests pass across replacement, independent-group and legacy append. Replacement reports qualify for original, retained authored, retired authored and copied V7 group cases; forged retirement, selection, donor ownership, operation counts, vector/triangle data and allocated group ordinals reject, as does the wrong review mode. A private headless Edge check exercised the actual dialog/renderer with a GLB replacing two faces with three: Current/Proposed render, upload, mode invalidation, stale Apply rejection, exactly one reviewed Apply and busy release passed with no page errors. Proposed screenshot inspected. Evidence: ignored `local-output/sdk-20260909/glb-group-replacement-20261004/parent/browser-proof.json`. This browser check does not verify Retail replacement delivery, the material editing panel or gameplay. Those remain deferred; the broader SDK goal stays active and solo.


**Retail GLB donor-group replacement — package/native evidence (2026-10-04):** A fresh private copy of the existing Retail V7 project replaces Town01 model 36's copied object 2 group 0. Exactly four stable authored faces retire and two lit Gouraud GLB faces import with four new vertices, three compatible stored normals and UVs. Other groups remain, native group ordinals rebase, the retired allocated group retains its tombstone, and the copied object retains its stable identity. Both actual V6 source/review reports and the resulting V5 material source pass browser qualification, including explicit absence of Retail counterparts for the copied object/groups.

Read-only Review, one-step Undo/Redo, unchanged base binding, Save/Open and saved Build integrity/current inputs pass. The model changes from 12,308 to 12,444 bytes; original vectors remain stored even when their faces retire. Final model SHA-256 `8c91f56ec5ab0306e41cd8df934d450567235f3fa0f830972e003b5571c48e05`. The normal format-7 Build emits one relocation payload (121,272,992 bytes, SHA-256 `77a1f4ce47f838e2958bc5cb72ae2d9ff0590e156b67b846f45923e80b639265`), with no duplicate overlays. Packed readback exactly reproduces all three authored models, preserves 111 unselected model slots and five other resources (qualified carrier padding only), and retains the matching Retail source hash. PROT remains 121,255,936 bytes, one sector above Retail.

A fresh native harness built at `2fde4087` activates only private staging and checks complete relocated PROT user/raw reads, metadata readback, Mode2 address/subheaders/EDC/ECC and vanilla restoration on netplay clear. Evidence: ignored `local-output/sdk-20260909/retail-glb-replacement-build-20261004/parent/proof.json` and `browser-qualification.json`. Two fixture assumptions were corrected while preserving prior attempts: object face totals are not selected-group totals, and copied object ownership is represented by `retail_index: null`. No user-runtime installation, game launch/control or full Retail disc export occurred. In-game appearance, collision/lifecycle and material editing after replacement remain deferred manual/workflow checks. Arbitrary packet layouts, texture/image/material allocation, animation interchange/allocation and full-scene/live parity remain unfinished. The full SDK goal stays active and solo.


**Reviewed GLB mesh inspection in the scene (2026-10-04):** Mesh import now offers Inspect reviewed mesh in scene before Apply. The new endpoint regenerates the candidate from the exact file, donor, Current hash and group mode, then checks both reviewed key and proposed hash. It composes the full prepared topology ledger into existing scene pose groups rather than treating allocated geometry as a same-layout file. Shared supported placements retain their source geometry grouping, pose and matrices; unavailable instances are reported. Textures are freshly qualified through the existing scene proposal path. The editor supports Current/Proposed comparison, affected-instance framing, Return to mesh import and Restore while retaining the uploaded file and accepted review.

Validation: 18 focused tests pass across scene proposal, replacement, both append modes and object preview. Scene composition covers all three modes on original and copied V7 objects; copied objects retain explicit unposed ownership. HTTP rejects forged review/proposed hashes, wrong group mode, invalid scope, unavailable selection and extra fields. Successful inspection preserves the scene, project document/history and authored files. A private headless Edge dialog/renderer check passed scene review retention, Return/Restore, mode invalidation, stale Apply, one reviewed Apply and delayed callback disposal with no page errors; it exposed and fixed a queued-close event that could dispose an already reopened dialog. Both changed editor modules pass syntax checks. Evidence: ignored `local-output/sdk-20260909/glb-scene-inspection-20261004/parent/browser-proof.json`. This bounded browser check exercises the dialog lifecycle with an injected scene callback; full Retail scene endpoint/render integration remains next and is not claimed. No game was launched or controlled. Manual gameplay stays deferred; the broader SDK goal remains active and solo.


**Retail GLB scene inspection and temporary isolation (2026-10-04):** The full editor now qualifies the reviewed GLB replacement through the actual Retail HTTP scene endpoint on private Town01 model 36. Its two supported placements share one proposed geometry, retain all placement matrices/display positions, and return to the exact base scene. Both Return to mesh import and Restore retain the uploaded file and accepted review; project state remains unchanged and no Apply is sent. This extends the earlier injected-callback dialog check to the actual editor, scene service, texture-qualified proposal and renderer.

The first screenshot showed unrelated scenery obscuring the inspected geometry. Mesh scene inspection therefore adds a reversible Isolate inspected instances control. It filters only viewport visibility, applies equally to Current and Proposed, and clears on Return/Restore/disposal without editing scene visibility or placements. The Retail browser check confirms 259 unrelated instances hidden, the two selected instances visible, and the full base restored with no page errors. Isolated Current/Proposed screenshots inspected; geometry remains positioned in the scene rather than recentered into a separate object viewer. Evidence: ignored `local-output/sdk-20260909/retail-glb-scene-inspection-20261004/parent/browser-proof.json`, `isolation-browser-proof.json` and `retail-isolated-proposed.png`. Editor syntax and diff checks pass. The owned private server/browser are stopped. This establishes Retail static scene inspection for this replacement; it does not establish game appearance, collision/lifecycle or general animation/coordinate/runtime parity. No game launch/control, user-runtime installation or full Retail disc export occurred. Manual gameplay stays deferred, and the full SDK goal remains active and solo.


**GLB primitive boundaries — native project/API allocation (2026-10-04):** Mesh import now supports exact boolean `preserve_primitives` when independent groups are selected. Geometry V5 records the contiguous source primitive index, first triangle, triangle count and source triangle mode. One native group is allocated for each GLB primitive, in source order, while shared POSITION accessor rows remain shared. Each group owns its corresponding stable added faces and inherits the selected donor layout/material. Mixed missing UV/normal/color attributes retain the established per-face donor behavior. GLB material/image allocation remains unfinished and is not implied by preserving boundaries.

Review V7 binds this choice and the primitive ranges in addition to the exact file, donor, group requests and proposed bytes. It supports append and donor-group replacement; replacement still retires only the selected Current group. Vector allocation and the complete multi-group request publish atomically, with optional retirement, as one Undo step. Cumulative face/vector/group/batch/operation budgets and copied V7 object ownership remain enforced. Existing default imports and review schemas remain unchanged. The scene proposal endpoint carries the choice through candidate regeneration and review matching.

Validation: four new cases pass for shared vertices/contiguous ranges, per-primitive UV absence, strict choice and group bounds, read-only Review/files/history, wrong-mode Apply rejection, distinct stable group ownership, one Undo/Redo, Save/Open, exact synthetic normal Build model readback, strict HTTP preview/scene/Apply/stale rejection and copied V7 group tombstones/scene continuation. All 18 focused primitive-group/scene/replacement/new-group/legacy append tests pass together. This milestone implements native/project/API support; browser V7 qualification and a visible preservation control are next. Retail multi-group package/native delivery and gameplay are not claimed. No game was launched or controlled. Manual gameplay stays deferred and the full SDK goal remains active and solo.


**GLB primitive boundaries — browser workflow (2026-10-04):** Mesh import now exposes Preserve GLB primitives as separate groups for independent-group append and donor-group replacement. The choice is disabled and cleared when appending into an existing group. Review, Apply and scene inspection carry the exact choice; changing it invalidates the review. The summary reports the primitive/native group count and explicit donor layout/material inheritance.

The V7 browser qualifier checks contiguous complete primitive ranges, source ordering, bounded mode/counts, distinct stable group requests and each range's exact faces. It independently reconstructs allocated group counts/origins/Current ordinals, face group membership, retained group rebasing/tombstones, full typed packet render output and vector/normal ownership. Retired stable face IDs are also reserved when qualifying new identities. Default V1–V6 review paths continue to pass.

Validation: 19 focused Python/Node tests pass across primitive preservation, scene proposal, replacement, independent-group and legacy append. Actual SDK reports qualify for append/replacement, copied V7 ownership, and mixed imported/inherited stored normals. Forged ranges, ordering, identities, group counters/origins, face membership, render UVs and preservation choice reject. A private headless Edge dialog/renderer check passes GLB upload, Current/Proposed render, primitive-toggle/mode invalidation, disabled existing-group choice, retained scene review, Return/Restore callback, stale Apply, one reviewed Apply, delayed scene disposal and busy release with no page errors. Proposed screenshot inspected. Evidence: ignored `local-output/sdk-20260909/glb-primitive-groups-20261004/parent/browser-proof.json`. The scene callback in this bounded check is injected; full Retail multi-group scene/package/native delivery remains next. No game was launched or controlled. GLB material/image allocation, arbitrary packet layouts, animation interchange/allocation and full-scene/live parity remain unfinished. Gameplay stays deferred and the full SDK goal remains active and solo.


**Retail GLB primitive groups — scene/package/native evidence (2026-10-04):** A private copy of the Retail V7 project replaces Town01 model 36 copied object 2 group 0 with two separate groups from two GLB primitives. Four selected authored faces retire and four imported faces preserve their source ranges/order with shared position rows. The first group imports three stored normal directions and UVs; the second omits those attributes and inherits donor references/values. Other groups remain, Current ordinals rebase and the retired group retains its stable tombstone. Actual V7 source/review and V5 material-source browser qualifiers pass.

Read-only Review, one-step Undo/Redo, unchanged base binding, Save/Open, unchanged project during Build and saved Build integrity/current inputs pass. The model changes from 12,308 to 12,524 bytes, SHA-256 `73eb1a978275de8ea3b7014f21ebde1b27ed117122c069ade695973f3ebd2d1f`. The normal format-7 Build emits one relocation payload (121,272,992 bytes, SHA-256 `383a0f2077f29bed03fcc6ad07497ba445b3575fbbb95fa21d52bb0c0243152b`), with no duplicate overlays. Packed readback matches all three authored models, preserves 111 unselected slots and five other resources (qualified padding only), and keeps PROT 121,255,936 bytes, one sector above Retail.

A fresh native harness at `dd5eaa87` qualifies complete user/raw reads, metadata, Mode2 address/subheaders/EDC/ECC and vanilla restoration on netplay clear. The full Retail editor then inspects exactly the same candidate model hash on both supported placements through the real HTTP endpoint and renderer. Shared geometry, all placement matrices/display positions, isolated Current/Proposed views, Return/Restore, retained file/review and exact base restoration pass with unchanged project state and no page errors; screenshot inspected. Evidence: ignored `local-output/sdk-20260909/retail-glb-primitive-groups-20261004/parent/proof.json` and `local-output/sdk-20260909/retail-glb-primitive-scene-20261004/parent/isolation-browser-proof.json`. Private server/browser stopped. No game launch/control, user-runtime installation or full Retail disc export occurred. Gameplay appearance/collision/lifecycle remain deferred; GLB material/image allocation, arbitrary packet layouts, animation interchange/allocation and full-scene/live parity remain unfinished. The full SDK goal stays active and solo.
