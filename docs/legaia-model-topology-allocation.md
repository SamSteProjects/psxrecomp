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
(flags0x13, stride24), growing4704â†’4728 bytes. The new packet inserts at3160 and
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
A discovered browser raceâ€”`dialog.close()` changes open state before its close
handler runsâ€”is handled by checking actual dialog open state before accepting a
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


## Runtime reader publication — 2026-10-03

**Runtime relocation publication and C reader lifetime (2026-10-03):** Commit now stages a fresh reader, rechecks whole-source SHA256 before/after native preflight and publishes only after successful plan/state preparation. The opaque C disc handle acquires the prepared reader for the bound source path. Competing source paths reject; replacing an active relocation invalidates old handles. Closing one shared handle leaves the other live. Netplay clear and reinitialization remove relocation from retained readers and restore stock layout. Failed recommits preserve the published reader. This supersedes the earlier unfinished-activation checkpoints below; normal SDK Build still emits format 6 ordinary overlays and does not yet compose/package model growth.

Validation: fresh MSVC mod-runtime regression passes both its built-in public synthetic source/payload and the independently Python-generated synthetic fixture. Coverage includes 60-to-62 sector mapping, replacement user/raw terminal framing, shifted movie/tail reads, undersized/out-of-range output preservation, wrong source, changed payload, same-path changed source, failed-commit isolation, plan replacement, shared close, netplay clear and reinitialization. The C bridge is now linked into the CMake regression target. Existing compiler/parser warnings remain; the full runtime/game build was not run. Private build/log: `local-output/sdk-20260909/mod-disc-relocation-20261003/parent/`. No game, installation or full Retail disc export ran; gameplay remains deferred.

The normal Build path still needs to consume source-bound model-growth requests,
compose ordinary source-offset patches before growth, encode the relocation payload
and emit the format 7 feature package. This runtime checkpoint does not qualify a
Retail package or gameplay. Directory entry identity/type/extent/size/membership,
complete PVD and complete path-table bytes are checked; opaque directory-record
fields and parent-record byte transformations have not received independent full-byte
qualification.


## Normal Build package composition — 2026-10-03

**Normal Build relocation package composition (2026-10-03):** Normal SDK Build now gathers all saved models sharing a topology-growth pack, defers them from legacy shape overlays, composes ordinary PROT patches at original offsets before growth and emits one format 7 `disc_relocation` feature payload. Source-bound external Form 1 edits are composed into mapped sectors; overlap, stale hashes, PROT-boundary straddles, ISO metadata conflicts and native payload budgets reject. The existing format 6 path remains for builds without topology additions. Review computes/verifies proposed bytes without writing output; packing validates the emitted relocation asset, and repeated builds are deterministic.

Validation: 36 focused Python tests pass (3 Retail-gated cases skipped). New normal Build regression uses actual synthetic Mode 2 ISO sectors, saved addition/retained-shape bindings in one pack, original-offset patch composition, independent reopened model payload comparison, the real generic psxmod packer and archive readback. External edits crossing a sector boundary map correctly. A fresh MSVC native harness accepts/activates an SDK-emitted synthetic package, compares every proposed PROT/metadata sector through the C disc reader and restores stock count on netplay clear. Private proof: `local-output/sdk-20260909/model-growth-normal-build-20261003/parent/`. Existing native compiler/parser warnings remain. No Retail package/game launch, installation or full Retail ISO/BIN export ran; gameplay remains deferred.

Remaining integration: saved Build history verification and Build & Run still assume an overlay-only inventory/private size bound. Those consumers need relocation-aware inventory and runtime observation before this package is offered as a complete Build & Run workflow. This checkpoint supersedes the earlier claim that normal Build cannot emit growth packages; it does not complete the full SDK or prove Retail/gameplay acceptance.


## Saved Build verification and private run preparation — 2026-10-03

**Relocation-aware saved Builds and run preparation (2026-10-03):** Saved Build verification and private run preparation now share an exact audited payload inventory. Format 7 relocation packages qualify their sole asset/hash/length and binary readback; composed source overlays remain audit inputs rather than separately installed assets. Output overlay counts describe emitted overlays. Private staging accepts the native 256 MiB relocation payload bound with bounded manifest overhead, rejects unexpected/mixed inventory and descriptor tampering before staging, and retains the feature selection plus expected payload hash/virtual sector count. Ordinary overlay packages keep the prior 64 MiB private bound.

Runtime `mod_status` now reports active relocation count, prepared reader activity, virtual sector count, reader acquisitions since plan reset and payload SHA256. SDK readiness requires the exact active relocation and at least one CD reader acquisition; older/missing observations, wrong hash/count, inactive readers and zero acquisitions reject readiness. This is process/plan identity preparation, not scene acceptance or sector-consumption proof.

Validation: 30 focused Python tests pass (3 Retail-gated skipped), including actual normal-Build history integrity/tamper checks, exact private staging without process launch, descriptor size/hash/path/budget rejection and readiness mismatch cases. Fresh MSVC native mod-runtime regression passes, proving status before/after handle acquisition and reset on netplay clear. The debug server passes GCC C11 syntax qualification with existing cached SDL3 headers; its actual status handler compiles independently with `-Wall -Wextra -Werror` and active/cleared JSON round trips parse correctly. Private protocol proof: `local-output/sdk-20260909/relocation-package-consumers-20261003/parent/`; runtime build/log: `local-output/sdk-20260909/mod-disc-relocation-20261003/parent/`. Existing native compiler/parser warnings remain. Full runtime/game build, Retail package activation and live Build & Run were not run. No game or runtime installation was performed; gameplay remains deferred.

Remaining: qualify the complete Retail model-growth package and rebuilt runtime without launching gameplay, then retain the gameplay queue for explicit user verification. The full SDK specification remains unfinished, including post-addition model authoring, scene/runtime parity, animation and script coverage. Earlier overlay-only-consumer checkpoints below are historical.


## Complete Retail package and raw-reader qualification — 2026-10-03

**Retail model-growth package and fresh runtime qualification (2026-10-03):** Normal Build now passes on an isolated saved Town01 project containing two authored faces over retained content-v3 model 9 plus an independent model 8 shape edit in the same pack. PROT grows from 121,253,888 to 121,255,936 bytes (one sector). Both saved payloads reopen exactly; all 112 unedited model slots and the original bytes of all five other resources are preserved. Only zero allocation padding is added after the final resource. Build leaves the project unchanged; reopening and saved Build integrity verification pass. Private run preparation accepts the 121,272,992-byte relocation payload and records its expected hash/count without starting a process.

Fresh MSVC isolated native activation passes against the original verified Retail BIN. It compares every proposed PROT byte and every relocation metadata sector through the C reader. All raw PROT sectors also match proposed user bytes, source-derived first/terminal subheaders, relocated addresses and regenerated EDC/ECC. Netplay clear restores the original reader count and clears relocation status. Payload SHA256: `467734a7805f5d4312bc79b922108a4b81d31d89e6490bfc98bed14b1d200ecb`; package ZIP: 72,034,628 bytes. Private artifacts/proof: `local-output/sdk-20260909/retail-model-growth-build-20261003/parent/`. No Retail disc image was exported; proprietary package/source material remains private and ignored.

The complete stability runtime target configures offline from cached dependencies, compiles and links successfully in Release with two build workers. Its revision stamp is `nightly-565-g3322686e`, and binary SHA256 is `f584a9c44f74c22b0ccf62596bfbca6a480c8f0f5d64c1855dc606b6cd2b805f`. Binary: `local-output/stability-20260909/build/Release/LegaiaStability.exe`. An initial MSBuild attempt rejected duplicate inherited PATH/Path names; normalizing environment names resolved it. Regenerating CMake also corrected a stale cached revision label. Existing compiler/parser warnings remain. The game binary was not executed: isolated reader activation is not live Build & Run, visual/editor parity or gameplay acceptance.

Gameplay remains queued for later user verification. Offline work can continue on post-addition model authoring and the remaining SDK specification; this qualification does not mark the goal complete or require immediate manual play.


## Typed content operations after addition — 2026-10-03

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
