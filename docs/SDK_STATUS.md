# Legaia SDK status — 2026-10-06

## Verified model-source derivation cache - 2026-10-06

**Implemented offline inspection performance:** model source reads share a bounded
in-memory service for previously qualified scene metadata and immutable retail
TMD bytes. A new operation still verifies the full supported disc hash before
using cached derivations. Keys include scene identity, exact imported-document
hash and verified disc digest. The service retains at most eight scene
qualifications and 32 models/32 MiB; it never caches authored model files or
retained GLB bytes. Qualification/decoder failures clear its derived entries.
Project staging/Build-review deepcopies receive fresh independent service state.

Retained-source reconstruction reuses the already verified Retail bytes inside
its detached view, with imported-evidence checks before/after reconstruction.
GLB bytes, native ledger spans and exact reconstructed results still qualify on
every model read. Nested verified disc scopes now also check their file stamp
on exit, preventing early cache publication after a nested read changes input.

In the private retail Town01 model 0036 comparison, retained-model read was
**8.44s before / 1.54s after**, with exact native bytes.
Warm original-model reads were approximately0.45s and still verified the disc.
These are local measurements, not general scene-loading/runtime guarantees.
Evidence: `local-output/sdk-20260909/model-source-cache-20261006/proof.json`.
Twenty-one focused cases passed, including the separately retail-enabled GLB
HTTP workflow. Checks cover full hash rejection after same-size/same-mtime input
mutation, exit drift, imported metadata drift, eviction/bounds, independent
staging caches, source reconstruction and existing authoring/copy workflows.
Actual editor GLB/receipt downloads and read-only normal Build review passed;
all reference project files and history were held. No game launch, package
installation or full-disc export. The full SDK goal remains active/incomplete.


## Retained source inputs in editable project copies - 2026-10-06

**Implemented offline workflow:** Copy project and saved export input snapshots
now carry the original GLBs referenced by Current mesh import receipts. Sources
are qualified and included in the inventory/file hashes; shared originals are
deduplicated. Missing/changed inputs reject before copy creation. Unreferenced
files and excluded Undo/Redo dependencies stay excluded. Copy byte/file limits
include retained inputs. The editor and saved-copy discovery now also accept
retained texture PNGs, fixing rejection of otherwise valid texture-source copies.

Validation: **26 focused Python cases plus the project-copy Node checks** passed.
Checks cover copied native qualification, original GLB recovery, shared-input
deduplication, snapshot recovery, texture PNG/STP source recovery, corruption,
source preservation, bounds, and editor inventory/path guards. Private retail
Town01 proof used the actual Copy project, saved-copy list, Open copy and mesh
source download controls at wide/narrow widths. Both GLBs and JSON receipts
matched. Original files/history and the separate source reference were held.
Copied-project normal Build **6dc800e2b077da1a**, package SHA-256
`1f3be0e69bbf76e36e52a9394e2613e1460587ba8982ead81c67f72991fe3c9a`, verified Current inputs and
matched native model 0036 bytes in the package. Evidence:
`local-output/sdk-20260909/mesh-source-project-copy-20261006/proof.json`.

No game launch, installation or full-disc export. Export input recovery was
checked with synthetic saved-snapshot metadata. Older snapshots lacking mesh
sources are not repaired implicitly. Gameplay acceptance remains queued and the
full SDK goal remains active/incomplete.


## Retained GLB mesh sources and import receipts - 2026-10-06

Reviewed single and mapped mesh Apply now retain original GLB bytes under
`Authored/Models/Sources/<sha256>.glb`, plus exact import settings in the native
model binding. Each receipt identifies its append-only native ledger span,
input/result hashes and GLB hash. Reading a saved model checks the source bytes
and reconstructs the original import against the preceding ledger prefix;
missing or changed sources and inconsistent recipes reject. Legacy bindings
without receipts remain supported; their original files cannot be recovered.

**Import GLB mesh > Retained mesh sources** lists Current imports, shows settings,
and downloads original GLBs or JSON receipts. Recovery is read-only and guarded
by Current model context. Settings describe historical donors; a new import
still requires fresh donor selection and Review. Native vector/content edits
and face removal preserve receipts. Undo/Redo follows the binding in the same
single command; retained files remain available for Redo. No implicit cleanup.

Limits: 32 receipts per model, 32 MiB per original GLB, 64 MiB of distinct source
bytes per model, alongside the existing stricter native operation/geometry
budgets. Source GLBs stay in the project and are not distributed in Build.

Validation: **26 focused regression cases** across source retention, rotation,
single/mapped imports, scene node ownership and object/group replacement. The
private retail Town01 model 0036 proof retained two imports, checked original
GLB/receipt downloads in the actual editor at wide/narrow widths, held all
project files/history during recovery, and passed Undo/Redo and Save/Open.
Normal Build **39fb8fd720902191**, package SHA-256
`4f94303104d773eb22fe26e8843de0932b7fe2b67703b2c57321ca44a8189b96`,
has verified Current inputs and native package readback. Evidence:
`local-output/sdk-20260909/model-mesh-sources-20261006/proof.json`.

No game launch, installation or full-disc export. Gameplay acceptance remains
queued; this source recovery feature needs no immediate gameplay verification.
The full SDK goal remains incomplete.


## Native import orientation in GLB authoring - 2026-10-06

The GLB importer now exposes **Native import rotation (degrees)** for X/Y/Z.
Active right-handed rotations apply in X, then Y, then Z order (`Rz Ry Rx`)
after node transforms, unit scaling and GLB Y reflection, before origin offset
and integer rounding. Normal directions use the same rotation before normalized
Q12 conversion. UVs, colors and winding retain their source conversion. This
orients static imported geometry inside the shared native model; actor facing,
scene placement and animation channels remain separate.

Inventory, Review, scene Review and Apply accept optional `source_rotation` XYZ
degrees. Values must be finite numbers in -360..360. Missing/zero rotations
preserve earlier reports/behavior. Nonzero rotation metadata is bound throughout
the candidate chain and Review keys, even for a full turn yielding identical
native bytes. Editing an angle withdraws Review and rechecks source inventory,
retaining section/UV choices. Map section donors inherits the chosen rotation
and origin for all selected sections. Native coordinate/normal and topology
budgets remain enforced. Oversized numeric rotation/offset/scale inputs now
reject cleanly before floating-point conversion can overflow.

Validation: 21 focused regression cases passed, including Node report guards;
the affected 11 cases were rechecked after the numeric-guard adjustment. Checks
cover native axes, rotation order, node/scale/offset composition, rotated normals,
limits, distinct Review keys for identical bytes, read-only posed scene Review,
atomic history and native Build. Actual browser angle editing/reinventory,
single-donor Review, stale Review withdrawal and mapped Apply passed. Private
Town01 model0036 used rotation `[90,0,90]` and offset `[1500,256,-1000]` across
three sections/two objects, retiring 177 faces and importing 6. Undo/Redo,
Save/Open, reference-project preservation and exact native Build readback passed.
Rotation controls and desktop/540-pixel comparison captures were inspected.

Private Build `2d06d44bda9966bb`; package SHA-256
`b2a234864b5e973cff5d0a7347eea0e0209310ea452436fcc3e50eddb9430b56`;
model SHA-256
`1f62042c41586d80a362e00eab55cd1929243eff76d416890d4505183cfcc7df`.
Evidence: `local-output/sdk-20260909/model-mesh-rotation-20261006/`.
No game launch, mod installation or full-disc export occurred. Gameplay acceptance
remains deferred. Arbitrary images/layouts, general animation import and the
broader SDK specification remain incomplete; the goal remains active.

## Native origin offsets in GLB import - 2026-10-06

The GLB importer now exposes explicit **Native origin offset** X/Y/Z controls.
Offsets apply after node-hierarchy transforms, unit scaling and Y reflection,
before native integer rounding. They move imported vertices inside the shared
model; they do not move actor placements, rotate normals or change UVs. Native
Y increases downward. Map section donors inherits one common chosen origin for
all selected sections. Existing append, group/object replacement and preserved
source-section modes compose with this origin.

Inventory, Review, scene Review and Apply accept optional `source_offset` XYZ.
Components must be finite numbers from -32768 through 32767; final rounded
coordinates still must fit signed native storage and nondegenerate triangles.
Missing/zero offsets preserve existing reports and behavior. Nonzero origin
metadata is present in inventory/geometry/reports and bound to Review keys,
including identical rounded candidates. Changing an input withdraws Review and
refreshes source inventory while retaining UV/section choices. Normal Build
serializes the shifted authored vectors through the existing model ledger.

Validation passed 19 focused Python cases, including Node report guards. Actual
browser input/reinventory, single-donor Review, origin-withdrawal and mapped
Review/Apply passed without page errors. Private retail Town01 model0036 mapped
three sections into two objects at `[1500,256,-1000]`, retired 177 original faces,
and imported 6 faces with normals/UVs unchanged. One-step Undo/Redo, Save/Open,
reference-project preservation and exact native normal-Build readback passed.
Desktop and 540-pixel captures were inspected.

Private Build `05d29e44e4b276ed`; package SHA-256
`ce8275cd30f033178cce644431ef8ccda873485c41e24668f62ac352f146dd1e`;
model SHA-256
`081f0f637d0b2cc3f0b10ee41fa6205b31eeaa9988298cbffb6af156e467c1d2`.
Evidence: `local-output/sdk-20260909/model-mesh-offset-20261006/`.
No game launch, mod installation or full-disc export occurred. Gameplay acceptance
remains queued; arbitrary images/layouts and general animation import remain
incomplete. The full SDK goal remains active.

## Visible geometry framing for GLB comparisons - 2026-10-06

Single-donor and mapped-section GLB dialogs now expose **Camera framing** and
**Frame mesh**. The default shared frame covers visible triangles in both
Current and Proposed at the same scale. Active-layer visible framing ignores
unused vertex rows, including rows retained after object/group retirement.
Stored-vertex framing remains available to inspect their full native extent.
Frame mesh resets zoom while retaining orbit. These are display controls: they
preserve Review, native coordinates/bounds, authored geometry and history.

Validation passed 13 focused Python workflow/scene cases and two Node suites for
framing and existing scene cameras. Actual retail HTTP Reviews exercised both
dialogs, all three frame modes, shared layer switching, zoom reset, and inspected
desktop / 540-pixel captures. In the mapped Town01 model0036 proposal, retiring
177 faces across two objects changed the useful visible radius to 70.7107 from
the stored-vector radius 429.2534; the retained native vectors remain untouched.
Camera actions issued no API requests, Apply was not used, and all private
project-file hashes, document state and Undo history remained unchanged.

Evidence: `local-output/sdk-20260909/model-visible-frame-20261006/proof.json`
and `validated/` captures/reports. No game launch, mod installation or new Build
was required for this camera-only change. Gameplay acceptance remains deferred;
the complete SDK goal remains active and incomplete.

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


## NPC-owned transition arrival serialization foundation - 2026-10-06

A native serializer now supports independently owned arrival bytes for qualified
SCENE_CHANGE instructions in appended NPC records. It uses the existing transition
adapter and the shared final-allocation guard, which now accepts the adapter's
transition target collection. Typed partial/full requests alter only encoded
entry X, Z and direction bytes. Destination names, full opcode/context/argument
preimages, untouched arrival bytes and layout remain bound to the retail donor,
even for no-op requests. Branch composition must follow operand serialization.

Validation: 24 focused native transition and NPC selector/branch/wait/flag checks
pass. Coverage includes ordinary/extended dispatch, two independent final clones,
partial/full byte edits, retained waits, no-op preimages, malformed values, changed
names/arguments/context, foreign ownership and forged allocation rejection.

Retail eligibility remains unresolved: a fresh source-qualified scan found no
eligible actor-owned named transitions in Town01, Dolk2, Town0b or map01. This does
not establish absence of runtime transitions. The first Town01 clone-proof attempt
stopped at that eligibility assertion; no retail clone proof is claimed. The scan
preserved project documents, histories and all file hashes. Evidence:
`local-output/sdk-20260909/npc-transitions-native-20261006/discovery.json`.

This is a native foundation with synthetic ownership/composition evidence, not a
completed retail editor workflow. Project review, editor, Build, presets and saved
comparison remain pending; a qualified actor donor or supported script-binding
extension is needed before a retail vertical workflow can be proven. No game
launch or full-disc export occurred. Gameplay acceptance is deferred and the full
SDK goal remains active; other offline SDK work remains available.

## Portable NPC model-selector presets v9 - 2026-10-06

NPC presets now freeze and transfer signed SET_ACTOR_MODEL operands alongside
all seven earlier edit families. Capture, export, import review and placement
freshly qualify selector ownership/instructions; complete branch composition
includes the frozen selectors, including instructions skipped by changed edges.
Metadata-only v9 stores stable source IDs and typed signed16 values, without
model payloads or an inferred runtime model binding. Earlier v1-v8 envelopes and
size bounds remain supported; selector-bearing files cannot claim an older schema.
Import adds a library entry only. New instances require separate reviewed placement.

Validation: 20 focused Python checks and both Node preset suites pass. Checks
cover freezing, branch/movement/facing/wait retention, skipped-body composition,
invalid signed values, extra/foreign fields, missing native targets, forged saved
preset placement, atomic history and Save/Open. Actual browser capture/download,
upload, review withdrawal, library Undo/Redo, Save/reload and detached scene
placement pass. The 1211-byte v9 file and 540px review were inspected.

Recipient Build `13dd8005234017a7` independently reopens selector0 at PC12; its
entire NPC record matches the expected donor clone, placement and selector word.
Source NPC drafts and recipient imports remain unchanged. Package SHA256:
`f26852879064a47e1d8fb8d272bba54a8bc6930a1eaca1089df04f8d4ea5b58d`.
Evidence: `local-output/sdk-20260909/npc-model-selectors-presets-20261006/proof.json`.

This supersedes the earlier NPC selector-preset capture restriction. No game
launch or full-disc export occurred. Runtime pool identity, restaging, pairing
and story execution remain unverified; manual gameplay acceptance stays deferred
and the full SDK goal active/incomplete.

## Saved NPC model-selector explanations - 2026-10-06

Saved-build comparison now explains NPC-owned SET_ACTOR_MODEL selector words.
Native qualification binds the typed signed16 request, original donor/PC/opcode,
extended context, source hash and separate retail/generated offsets to the exact
receipt and emitted bytes. Browser decoding independently verifies MENU_CTRL
sub-op0x50, signed word encoding, source metadata, instruction width and held
dispatch. Retained selectors still qualify when a changed branch skips their
original instruction. Source-identical requests receive no authored change span.

Validation: 17 focused Python checks with private retail input and the Node
comparison suite pass. Signed boundaries, ordinary/extended forms, no-ops,
skipped-body composition, forged requests/receipts and duplicate spans are covered.
A fresh read-only Town01 Build `47211a52e78d1b75` comparison labels one selector
byte out of three changed bytes; two stay unexplained. The 540px table was visually
inspected. Streaming Build `a283762d47e6985f` qualifies the requested -1 word and
correctly leaves the source-identical 240 request unlabelled. The private helper's
initial assumption that both requests changed bytes was corrected using each
retail preimage. Both project documents, histories and every file hash stay held.
Evidence:
`local-output/sdk-20260909/npc-model-selectors-script-comparison-20261006/proof.json`.

Portable NPC model-selector presets remain pending. No new Build, game launch or
full-disc export occurred. Runtime pool identity, restaging, pairing and story
execution remain unknown; manual acceptance is deferred and the SDK goal active.

## NPC model selectors through editor and normal Build - 2026-10-05

Independent NPC SET_ACTOR_MODEL signed selectors now connect source inspection,
complete reviewed entries, Apply/Clear, Undo/Redo, Save/Open, root Inspector and
Asset Details. Normal compressed and streaming Builds compose selector words
before NPC branches. Branch review includes selectors in its complete frozen
composition, retaining original operands when a changed edge skips them.
Repetition qualifies and retains entries. Preset capture explicitly rejects
selector-bearing NPCs until portable interchange is connected; saved authored
comparison for this family also remains pending.

Validation: 24 focused Python checks with private retail input and the Node source,
review and opener contract pass. Checks include stale review, typed fields,
HTTP rejection, history/persistence, repetition and a changed branch skipping a
retained selector. Actual Town01 browser Review/Apply/Clear, changed-input
withdrawal, Undo/Redo and Save/reload pass; the 540px dialog was visually inspected.
Build `47211a52e78d1b75` reopens selector0 at PC12, preserving every other record
byte against its baseline Build. Package SHA256:
`f12191b0735f0c0de979219c6f145e121e09a2870cb2bbba236373ce2f886293`.
Streaming Rayman Build `a283762d47e6985f` reopens two independent NPC selectors
240/-1 at PC12 with only their word bytes changed. Package SHA256:
`7319c7612354b6cf878a31c33d69ec745968a98de51dbfeb3df59d8d304aa3ab`.
Evidence: `local-output/sdk-20260909/npc-model-selectors-editor-20261005/proof.json`
and `local-output/sdk-20260909/npc-model-selectors-streaming-20261005/proof.json`.

Selectors are encoded script operands, not resolved model assets. Runtime pool
identity, pairing, restaging and story execution remain unverified. No game launch
or full-disc export occurred. Manual acceptance stays deferred; the SDK goal stays
active/incomplete.

## NPC-owned script model selector foundation - 2026-10-05

Appended NPC scripts now have independent native SET_ACTOR_MODEL selector-word
serialization using the existing source-qualified MENU_CTRL 0x50 adapter. The
shared final-allocation guard binds each unique clone to its immutable donor.
Signed16 values preserve encoded meaning, opcode, sub-op, extended context and
all other bytes. No-op requests still verify full instruction/word preimages.
This changes script operands; runtime model-pool resolution and mesh restaging
are not inferred, and the viewport does not simulate this instruction.

Validation: 10 focused native/model-selector/wait Python checks pass. Ordinary and
extended forms, signed boundaries, two independent clones, final offsets, retained
wait operands, no-op preimages, invalid types/owners and forged allocations reject
or retain bytes as required. A fresh retail Town01 actor0003 two-clone proof sets
PC12 to selectors240/-1, preserving the retail donor, complete MAN layout, every
unrelated byte, project document, Undo/Redo history and all project file hashes.
Evidence: `local-output/sdk-20260909/npc-model-selectors-native-20261005/proof.json`.

Project commands, editor review, normal Build, portable presets and saved authored
comparison are still pending for NPC-owned model selectors. The existing imported
actor workflow is unchanged. No game launch or full-disc export occurred; runtime
model identity, pairing, restaging and story execution remain unverified. The full
SDK goal remains active and manual gameplay verification remains deferred.

## Portable NPC branch presets v8 - 2026-10-05

NPC presets now freeze independent branch destinations with all six earlier edit
families. Capture, export, import review and new-instance placement qualify the
complete frozen script composition against the retail donor. Metadata-only v8
stores stable branch IDs and typed target PCs; original boundaries, conditions,
selectors and dispatch remain native-qualified. Earlier v1-v7 envelopes and bounds
remain available. Branch-bearing files cannot use an older schema. Import creates
only a library entry; reviewed placement creates an independent undoable NPC.

Validation: 19 focused Python checks with private retail input and both Node
preset suites pass. Coverage includes freezing after source edits, all earlier
families, skipped-body composition, atomic history, Save/Open, invalid/interior
PCs, forged ownership/fields and freshly qualified stored-template placement.
Actual browser capture/download/upload, changed-review withdrawal, library
Undo/Redo, Save/reload, detached scene inspection and new-instance Apply pass.
The 2583-byte v8 file and 540px import review were inspected.

Recipient normal Build `ee559898bc7a73de` independently reopens branch PC14 target11,
flag bit0, facing sector0, wait11, movement X3200/Z5696/MOVE_ID10, appearance105/13
and text `Wait NPC`. Source drafts and recipient imports stay unchanged. Package
SHA256: `3a1ee99cfc40358682941c2afc850393303255f64b6e39f309072d47a0a24f71`.
Evidence: `local-output/sdk-20260909/npc-branches-presets-20261005/proof.json`.

This supersedes the earlier branch-preset capture restriction. No game launch or
full-disc export occurred. Runtime activation, story reachability, scheduling and
termination remain unverified; manual acceptance is deferred and the goal active.

## Saved NPC branch explanations - 2026-10-05

Saved-build comparison now explains source-qualified NPC branch destination words
alongside appearance, dialogue, waits, movement, facing and flag bits. Native
qualification binds original instruction boundaries and the final graph to the
saved receipt. Browser decoding independently checks all eight supported branch
word families, exact dispatch, targets, original boundaries and held selectors.
Edits retained in instructions skipped by a changed branch still qualify: facing
and flag checks use a private copy with original branch words restored, while the
comparison always displays exact saved bytes. No project data is changed.

Validation: 11 focused Python checks with private retail input and the Node
comparison suite pass, including skipped-body edits and forged receipt rejection.
A fresh saved Town01 Build `6e6a47c3f7d988fe` comparison renders all seven edit
families and accounts for 30 of 33 changed bytes; three stay unexplained. The 540px
comparison was visually inspected. Streaming Build `0dc504a3a5d7cf6f` independently
qualifies both NPC branch spans. Both projects, Undo/Redo history and every project
file hash remain unchanged. Evidence:
`local-output/sdk-20260909/npc-branches-script-comparison-20261005/proof.json`.

Portable branch presets remain pending. No game launch, new Build or full-disc
export occurred; branch activation, story reachability and termination remain
unverified. Manual gameplay acceptance stays deferred and the SDK goal is active.

## NPC branch authoring through editor and normal Build - 2026-10-05

NPC branch destinations now connect source-qualified review to the root Inspector
and Asset Details, reviewed commands, Undo/Redo, Save/Open and both normal Build
carrier paths. Review composes existing own dialogue/movement/facing/flags/waits
before qualifying the proposed graph. Build composes branch destinations after all
six existing NPC edit families, retaining original instruction spans even when
changed edges skip them. Conditions, selectors and extended dispatch stay held.
Repetition qualifies and retains branches. Branch-bearing preset capture rejects
until portable interchange is connected; saved authored-span explanations are also
pending. See [NPC branch workflow](legaia-npc-branches.md).

Validation: 19 focused Python checks pass with retail input enabled; the Node
source/review/opener contract suite passes. Actual browser Review/Apply/Clear,
changed-input withdrawal, Undo/Redo and Save/reload pass. A module export mismatch
found by the first browser probe was corrected and the opener export is now
checked. The saved 540px dialog top and bottom were visually inspected without
project/history/file mutation. Private Town01 Build `6e6a47c3f7d988fe` reopens
branch PC14 with target11 and changes only its destination word against the
verified six-family baseline. Package SHA256:
`df94104dd232c590cf6a1fc99633ff58b34b8c3a6a2919dd8aa0e9b61fa92636`.
Streaming Rayman Build `0dc504a3a5d7cf6f` reopens two NPC branches at PC12 with
targets9/10, with only branch-word changes and all six prior families retained.
Package SHA256: `7d3ea68002c864c4580f3fb3d2ce60abb802af573f9499d5b90a1f585104c18d`.
Evidence: `local-output/sdk-20260909/npc-branches-editor-20261005/proof.json`
and `local-output/sdk-20260909/npc-branches-streaming-20261005/proof.json`.

No game launch or full-disc export occurred. Branch activation, story reachability
and termination remain unknown. Manual acceptance stays deferred and the full SDK
goal remains active/incomplete.

## NPC-owned branch destination serialization foundation - 2026-10-05

Appended NPC records now have a native branch-word serializer using the existing
source-qualified BranchAuthoringContext. It resolves final clone allocations,
qualifies each clone against immutable donor graph anchors and composes complete
branch requests together. Original opcodes, dispatch contexts, branch conditions,
selectors, word preimages and record boundaries stay held. Targets must be reached
source instruction or atomic message starts; opaque/interior targets reject.
Original source spans remain retained when edited edges make them unreachable.
Branch composition belongs after other qualified NPC operand edits.

Validation: 13 focused Python checks pass with the retail fixture enabled.
Synthetic cases cover ordinary/extended supported family words, two independent
clones, final offsets, no-op preimages, invalid types/owners and changed conditions
or selectors. A fresh retail Town01 donor0040 two-clone proof changes the qualified
SYSFLAG_TEST at PC14 to source boundaries11/12, preserving appearance, waits,
movement, flags, the source donor, MAN structure, every unrelated byte and project
files/history. Evidence:
`local-output/sdk-20260909/npc-branches-native-20261005/proof.json`.

This is a serialization foundation. Project review/history, editor controls,
normal Build, portable presets and saved-script explanations are not yet connected.
Branch activation, termination and story reachability remain unknown. No game
launch or full-disc export occurred. Manual acceptance stays deferred and the full
SDK goal remains active/incomplete.

## Portable NPC presets retain qualified flag-bit overrides - 2026-10-05

NPC preset capture now freezes source-qualified flag entries alongside appearance,
dialogue, waits, movement and facing. Flag-bearing exports use metadata-only
`legaia.npc-preset-file.v7` with the existing 512 KiB bound; v1-v6 retain their
previous schema selection and limits. Export/import and reviewed placement freshly
qualify donor operands. The browser checks exact owner/PC namespaces and typed
entries, preserves the complete reviewed draft and shows flag counts. The temporary
flag-bearing capture rejection is removed. Runtime flag identity and story meaning
remain unknown. See [NPC flag workflow](legaia-npc-flags.md).

Validation: 18 focused Python checks and two Node suites pass. Tests cover frozen
capture, independent library import without NPC creation, history/persistence,
older-format rejection, malformed entries, special side-effect exclusions and
fresh placement requalification. Actual retail browser capture/download/upload,
Review withdrawal, library Apply/Undo/Redo, Save/reload and Review/Inspect/Apply new
instance all pass. Existing entities/imports and the source NPC stay held. The
540px import review was visually inspected. Recipient NPC
`authored-actor://4df9310b-5efd-5626-be23-39aa19404402` retains bit0, sector0,
wait11, own text, model105/animation13 and own movement X3200/Z5696/move10 at
placement X3200/Z5824. Normal Build `248da4af5e7947dd` independently reopens all
six families and preserved upper bits. Package SHA256:
`0092b428d9d6ed60852905fa54a917adc6c0e98fe5de4220f10d4a026346e495`.
Evidence: `local-output/sdk-20260909/npc-flags-presets-20261005/proof.json`.

No game launch or full-disc export occurred. Manual runtime acceptance stays
deferred and the full SDK goal remains active/incomplete.

## Source-qualified saved NPC flag explanations - 2026-10-05

Saved-script comparison now labels NPC-owned flag-bit index bytes alongside
appearance, dialogue, waits, movement and facing. Each explanation is bound to the
current NPC's typed request, source donor/PC/opcode/context, exact native source
change, final record allocation and saved before/after bytes. Both records must
qualify the supported instruction; widths and special side effects stay excluded.
Upper bits, extended dispatch, no-op receipts, stale/forged metadata and overlap
are checked independently. Other differences remain unexplained. This does not
assert runtime flag identity, story meaning or behavioral equivalence.

Validation: 13 focused Python checks and the Node comparison suite pass, including
all nine operations in ordinary/extended forms, forged receipts, typed values,
upper bits and dispatch. Existing saved Town01 Build `9ad4a9c1b39b7fda` explains
28 of31 changed bytes across all six authored families, leaving three unexplained.
Streaming Build `ee3148f1c5861326` independently qualifies one flag span in each of
two NPC records. Actual read-only browser comparison renders all six labels; its
540px table was visually inspected. Project documents, history and all file hashes
stay unchanged for both projects. Evidence:
`local-output/sdk-20260909/npc-flags-script-comparison-20261005/proof.json`.

No new Build, game launch or full-disc export was needed. Flag-bearing portable
presets remain to be connected. Manual gameplay acceptance stays deferred and the
full SDK goal remains active/incomplete.

## NPC-owned flag authoring through editor and normal Build - 2026-10-05

NPC flags now connect source-qualified inspection and review to the root Inspector
and Asset Details, reviewed project commands, Undo/Redo, Save/Open and both normal
Build carrier paths. Complete entries belong to the NPC's recorded donor; stale
reviews, foreign owners, invalid bit indices and unsupported side-effect selectors
reject. Input changes withdraw browser proposals. Repetition qualifies and retains
flags. Preset capture currently rejects flag-bearing NPCs to prevent losing their
entries; portable preset integration and saved-script authored-span explanations
remain pending. See [NPC flag workflow](legaia-npc-flags.md).

Validation: 22 focused Python checks pass with the private retail fixture enabled;
two Node suites pass. A later added stale-position review regression also passes.
The actual browser verifies Review/Apply/Clear, changed-input withdrawal,
Undo/Redo and Save/reload; the 540px dialog was visually inspected. Private Town01
Build `9ad4a9c1b39b7fda` independently reopens with bit0; its record differs from
the verified prior five-family record by exactly one operand byte. Package SHA256:
`11c66953be270113d45838106195c8a1bdacd307cc499751c59bee36294c68b1`.
Private streaming Rayman Build `ee3148f1c5861326` independently reopens two NPCs
with indices3/4 and exactly one changed byte per record against their verified
baseline. Package SHA256:
`032ff923b60c8299c500c0ea5ee9521ccfe48889781aa7166d9b81f61689d6b6`.
Upper bits, the five existing own script families, placement, imports and other
draft fields stay held. Evidence: `local-output/sdk-20260909/npc-flags-editor-20261005/proof.json`
and `local-output/sdk-20260909/npc-flags-streaming-20261005/proof.json`.

No game launch or full-disc export occurred. Runtime variable identity, story
meaning and gameplay effects remain unknown; manual acceptance stays deferred.
The full SDK goal remains active/incomplete.

## NPC-owned flag operand serialization foundation - 2026-10-05

Appended NPC records now have a native serializer for source-qualified LFLAG,
GFLAG and CFLAG SET/CLEAR/TEST bit indices. It resolves final record allocations,
requires each donor-qualified instruction and operand preimage, preserves the
upper three operand bits and extended dispatch context, and changes only the
requested low five bits. Existing width and special side-effect exclusions remain
in force. No-op requests still require an exact preimage. Unsupported paths,
foreign owners, duplicate requests and invalid typed values reject.

Validation: 14 focused Python checks pass, including all nine supported operations
with ordinary and extended dispatch. A fresh private retail Town01 proof appends
two donor0040 clones, composes independent appearance, waits and movement, then
sets separate flag-bit indices 3 and 4. Exactly two bytes change; the source donor,
MAN layout, upper bits, all unrelated bytes, project files and history stay held.
Evidence: `local-output/sdk-20260909/npc-flags-native-20261005/proof.json`.

At this earlier checkpoint it was a serialization foundation; the newer
checkpoint above connects editor/project/normal Build. Presets and saved-script explanations also remain to be connected.
Runtime variable identity, story meaning and gameplay effects are not asserted.
No game launch or full-disc export occurred. Manual gameplay acceptance remains
deferred and the full SDK goal remains active/incomplete.

## Keep dense source scenes previewable with authored NPCs - 2026-10-05

The Rayman viewport failure was a combined entity-budget mismatch, not an endless
decode. Its supported source scene occupies 512 actor/scenery entries plus one
derived ground mesh; two authored NPCs raised the total to 515 and the old final
512-entry check rejected the whole preview after decoding. Scene preview now keeps
separate allowances for 512 source entries, one terrain instance and 128 independent
NPC drafts, with an explicit combined ceiling of 641 entries. A 129th active-scene draft
rejects before geometry decoding. Existing geometry/triangle/texture budgets stay
held. Shared scene constants align animation, NPC repetition/group/appearance,
preset proposal and texture-usage decoders with the supported total. The separate
world-source scene graph keeps its own existing budget.

Validation: 16 focused Python checks and nine Node suites pass. The synthetic
boundary includes all 512 source entries, ground and 128 NPCs with unchanged project
history/imports and exact source identity retention; 129 drafts reject. Actual retail
Rayman browser preview now reaches readiness in 9896 ms (one measured cold load),
with 515 entities, 514 rendered instances, 93 geometries, 15971 triangles and 5533230
texture bytes. Environment/terrain/animation errors are null. Frame All and the
NPC Focus control pass, including changed camera target and closer distance.
Overview, focused NPCs and 540px scene screenshots were visually inspected.
Project/imports/history and existing file hashes stay unchanged. Evidence:
`local-output/sdk-20260909/rayman-preview-loading-20261005/proof.json`.
A separately profiled server preview takes about 23 seconds with profiler overhead;
the earlier 60-second readiness failure is resolved by the capacity fix.

No Build/Save/authoring command, game launch or full-disc export occurred.
One unsupported scenery instance remains a source marker. Unknown NPC height,
initial heading and live placement are still explicit preview conventions; rendered
models do not establish gameplay alignment. Manual runtime acceptance stays deferred
and the full SDK goal remains active/incomplete.

## Streaming NPC readback and saved-inspector receipt fix - 2026-10-05

A fresh normal Build of the retail streaming `rayman` scene now has independent
readback proof for two NPC clones carrying appearance, dialogue, waits, movement
and NPC_RUN facing. The check found and fixed a saved-inspector bug: streaming
receipts use `actor_changes` for allocations, while compressed receipts use `actor`.
The inspector now selects the exact family from the qualified carrier schema and
rejects unknown/ambiguous receipts or missing/unbounded allocation rows. Output
DTOs remain unchanged; compressed saved inspection is also reverified.

Validation: 20 focused Python checks pass; one optional private Town01-fixture
check skips. Saved streaming Build `e5ec43a38c122f65` independently reopens record92
with sector0/wait12/X3264 and record93 with sector7/wait11/X3200. Both retain Z5696
movement, appearance model90/animation22, own padded text, placement Z5760 and upper
facing flags. The entire emitted MAN equals a separately reconstructed post-append
baseline plus intended clone edits and terminal zero padding; all other record bytes
stay held. Project/imports/history stay fixed. Package SHA256:
`04a1befcb91bfbe3c54002b02ab04123eef33537b3079cd4c27cb29e782b704f`.
Read-only browser comparison labels all five families, and the 540px table was
visually inspected. Browser project files/history stay unchanged. Evidence:
`local-output/sdk-20260909/npc-owned-streaming-20261005/proof.json`.
This closes the separate retail streaming check for NPC-owned facing and movement
and supplies retail streaming evidence for own waits/text/appearance together.

The first browser probe exceeded its 60-second full-scene viewport readiness
window. The script comparison was then verified after project readiness, separately
from scene rendering. Rayman preview loading was subsequently diagnosed as an entity-budget mismatch
and resolved in the newer checkpoint above. This earlier checkpoint did not verify
its full rendered scene. No game or full-disc export
ran. Runtime allocation/scheduling, branch execution and visible facing still need
later gameplay acceptance. The full SDK goal remains active/incomplete.

## Explain NPC-owned facing in saved script comparison - 2026-10-05

The retail-donor/generated-NPC comparison now labels **Own script facing sector**
for exact source-qualified authored bytes. Receipt rows must match the native
facing serializer, retail donor/PC/context/hash, current owned sector, final clone
allocation and separate source/generated offsets. The generated target must remain
supported after own movement. Typed sectors, full upper flags, opcode/dispatch and
CAM_CFG mode stay bound. No-op or duplicate/overlapping spans, parked targets and
forged/stale receipt rows reject. The browser independently checks raw ordinary and
extended CAM_CFG/NPC_RUN forms and the exact owned nibble. Other bytes remain
unexplained; labels establish no branch execution or runtime heading.

Validation: 39 focused Python checks and the Node comparison suite pass with the
retail disc enabled. Read-only actual browser inspection of saved Build
`2ef03e22f5a78f7b` accounts for 27 of 30 changed bytes across appearance, dialogue,
waits, movement and facing; three remain unexplained. The 540px comparison table
was visually inspected. Project document/history and all existing project file
hashes stayed fixed. Evidence:
`local-output/sdk-20260909/npc-facing-script-comparison-20261005/proof.json`.
No Build/Save/authoring command or game launch occurred. The separate own-facing
retail streaming package check is now verified above; later gameplay remains open.
The full SDK goal remains active/incomplete.

## Transfer NPC-owned facing presets - 2026-10-05

NPC preset capture now freezes supported own facing sectors alongside appearance,
dialogue, waits and movement. Facing-bearing exports use **legaia.npc-preset-file.v6**;
v1-v5 retain their existing formats and bounds. V6 contains bounded source-bound
metadata only. Export/import and instance placement freshly qualify the facing
against the same donor and its own movement-composed record; parked targets reject.
The import/placement dialogs show facing counts and require separate reviewed Apply.
Frozen presets stay independent of later source NPC edits. History and Save/Open
retain exact facing metadata without changing existing actors or imported scenes.

Validation: 37 focused Python checks and two Node suites pass. Actual editor
capture/download/upload, reviewed library import, changed-input withdrawal,
Undo/Redo, Save/reload and reviewed detached-scene placement passed. The 540px
import dialog was visually inspected. Recipient normal Build `2ef03e22f5a78f7b`
was independently reopened: sector0 and upper flags, X3200/Z5696/selector10,
wait11, own text and model105/animation13 all survived. Placement was X3200/Z5824;
source NPCs/imports stayed fixed. Package SHA256:
`8a4c6fb933dce117e9796c2a2ad35944ada8db6f7eab37aaac2cfc6dbdc65524`.
Evidence: `local-output/sdk-20260909/npc-facing-presets-20261005/proof.json`.
No game launched. Visible facing, dispatch and branch execution still need later
gameplay acceptance. Facing explanations in saved-script comparison are now supported, as recorded
above. The separate own-facing retail streaming package check is now verified above.
The full SDK goal remains active/incomplete.

## Independently author NPC script facing - 2026-10-05

NPC Inspector and registered Asset Details now offer **Edit NPC script facing**.
Source-qualified CAM_CFG/NPC_RUN targets expose an own sector0..7 override with
retail sector, preserved upper flags and unresolved dispatch context. Review
changes withdraw Apply. Apply/Clear use one history step; Undo/Redo and Save/Open
retain facing with appearance, dialogue, waits, movement, name and placement.
Script donor changes require clearing the retained facing binding first.

Facing qualifies the NPC's own movement-composed record. Parked NPC_RUN targets
are unavailable, and movement review rejects parking a target with an owned facing
override. Normal compressed/streaming MAN composition applies facing after movement,
uses final clone allocation and records npc_facing_changes. Repetition qualifies and
retains own facing. Preset capture and v6 transfer now retain facing; see the latest
checkpoints above. Saved-script facing explanations are also now supported.

Validation: 45 focused Python checks and two Node suites pass. Actual root editor
Review/Apply/withdrawal/Clear/history/persistence and the inspected 540px dialog
passed. Normal Build `a27a96074d841507` independently reopened sector0 with preserved
upper flags, own X3200/Z5696/selector10 movement, wait11, text and model105/animation13.
Placement, imports and existing preset metadata stayed fixed. Package SHA256:
`582f053dd091e1234eaabf2383620fef902b74f5852608b85f5641f924fdb910`.
Evidence: `local-output/sdk-20260909/npc-facing-editor-20261005/proof.json`.
This earlier package check covers compressed MAN; streaming readback is now
verified in the newer rayman checkpoint above. Source operands establish no
initial/live Transform heading, dispatch identity or execution. No game launched;
gameplay stays deferred and the full SDK goal is active/incomplete.

## NPC-owned facing serializer foundation - 2026-10-05

Added source-qualified facing serialization for uniquely allocated NPC clones.
Simple CAM_CFG and nonparked NPC_RUN targets accept sector0..7 only. Requests bind
a draft, its retail script donor and supported instruction ID. The shared allocation
guard verifies final record indices, extent, local/script entry ownership and aliases.
Dispatch/opcode, CAM_CFG mode and full operand preimages remain source-bound,
including no-op requests. Only the low facing nibble changes; upper flags stay held.

Facing composes with independently authored NPC_RUN movement X/Z/selectors and
wait/appearance edits. A composed parked NPC_RUN target rejects facing authoring.
Unknown/conflicting paths, nondirection LUT slots, halt-acquire CAM_CFG mode, wrong
owners/fields/types, stale flags/context, aliased records and duplicate writes reject.
The adapter emits exact source/final byte offsets and hashes, and asserts no runtime
dispatch, initial Transform heading or gameplay behavior.

Validation: 17 focused Python checks pass with the retail disc enabled. Synthetic
cases cover both opcode families, ordinary/extended contexts, all eight sectors,
two final clones, no-op/stale and unsupported targets, aliases and composition.
A fresh town01 donor0040 check composed own movement, waits and initial appearance,
then wrote sector0/7 to two clones. Exactly two facing bytes changed; upper flags,
all other candidate bytes, MAN layout and source donor records stayed fixed relative
to the post-append/composition baseline. Project document, history and existing file
hashes stayed unchanged. Evidence:
`local-output/sdk-20260909/npc-facing-native-20261005/proof.json`.
Project commands, editor controls and normal Build integration have now landed;
see the latest checkpoints above, including v6 preset transfer. No Build, export or game launch
occurred. Manual gameplay remains deferred; the full SDK goal is active/incomplete.

## Inspect NPC-owned movement targets in the scene - 2026-10-05

The NPC movement editor now offers retail donor, current NPC and reviewed proposal
scene target layers. Enter an explicit reference Y and choose **Show NPC script
targets**. The existing viewport target overlay frames qualified MOVE_TO/NPC_RUN
X/Z markers with source PCs. Selector-only EXEC_MOVE has no scene position.
Script Y, dispatch identity, branch execution and live actor position stay unknown;
markers never move NPC placement or scene geometry.

Target selection/Inspect returns to the retained movement editor at that instruction,
including unapplied inputs and reviewed Apply. Changed inputs invalidate a proposal
overlay. Clear, stale source state or overlay replacement dispose the hidden editor;
ordinary imported-script overlays keep their existing behavior. Inspector and Asset
Details use the same NPC movement editor entry.

Validation: 18 focused Python checks and two Node suites pass. Actual browser
verified three markers, explicit/invalid height guards, current X3200/Z5696,
reviewed X3264/Z5696 and retail X13888/Z5056, return-to-editor review retention,
input withdrawal and Clear cleanup. The scene overlay and 540px scrollable controls
were visually inspected. Project document, history and all existing file hashes
remained unchanged; only source/review preview requests ran. Evidence:
`local-output/sdk-20260909/npc-movement-target-scene-20261005/proof.json`.
No Build/Save/authoring command or game launch occurred. Reference Y is a display
choice, not a recovered script height or gameplay alignment claim. Manual gameplay
remains deferred and the full SDK goal stays active/incomplete.

## Preserve NPC-owned edits through repetition - 2026-10-05

Line/grid and selected-arrangement repetition retain each source NPC's own
appearance, dialogue, wait targets and script movement in independent copies.
The single-NPC browser decoder now compares each complete proposed draft with
its source; omitted, substituted or extra fields reject. UUID uniqueness and
placement remain checked. Spacing changes placement only, never script targets.

Repetition now freshly qualifies retained source operands/appearance witnesses
before review and Apply. The single review binds the complete project source key,
checks freshness after qualification, and rejects direct Live-mode review.
Line/grid review algorithms advance to v2; saved NPC identities are unchanged.
A library or other project change withdraws a prior review rather than replaying it.
Arrangement copies use the same source qualification with atomic batch history.

Validation: 30 focused Python checks and two Node suites pass. Actual editor review,
detached scene comparison, input withdrawal, Apply/Undo/Redo and Save/reload passed
for a four-family NPC. Existing scene entities, the original NPC and imports stayed
fixed; the 540px scrollable dialog was inspected. Normal compressed MAN Build
`0be50da61dbc2529` reopened both independently allocated records with retained
appearance/dialogue/wait/movement edits. Positions differ at X3200 vs X3264,
Z5760; script targets remain X3200/Z5696 with selector10 and own wait11.
Package SHA256: `c021d76f28f93bc257c3e0b25386df826b3544b9dc17d6cbb12e4ef3e6ad1e80`.
Evidence: `local-output/sdk-20260909/npc-owned-repetition-20261005/proof.json`.
No game launched. This proves editor metadata and emitted bytes, not runtime
allocation, scheduling or movement behavior. Gameplay stays deferred; the full
SDK goal remains active/incomplete.

## Explain NPC movement edits in saved-script comparison - 2026-10-05

The saved normal Build comparison now labels source-qualified NPC movement
operand bytes alongside appearance, dialogue and waits. Each movement audit row
must match its recorded script donor, reached supported instruction, PC, field,
dispatch context, source hash and exact requested before/after bytes. Final record
allocation and source/generated relative offsets must match. Missing audit rows
or other bytes receive no explanation; invalid rows reject the comparison.
The browser independently checks raw ordinary/extended opcodes, operand offsets,
current authored values and exact byte encoding before rendering X/Z/selector
labels. Bounded span counts accommodate all supported operand families.

Validation: 23 focused Python checks and the Node comparison suite pass, including
MOVE_TO/NPC_RUN/EXEC_MOVE, ordinary/extended contexts, missing bindings, forged
owners/fields/context/offsets, byte substitutions, overlap and collection bounds.
Actual saved Build `4725587333eecfe2` yielded 29 changed bytes: 26 accounted for by
qualified appearance/dialogue/wait/movement spans and three remaining unexplained.
The real editor comparison and inspected 540px table passed without authoring,
Build/Save or Run calls. Project document, history and all existing file hashes
remained unchanged. Evidence:
`local-output/sdk-20260909/npc-movement-script-comparison-20261005/proof.json`.
This explains exact authored bytes only; it proves no runtime dispatch, movement
behavior or branch execution. No game launched; gameplay stays deferred and the
full SDK goal remains active/incomplete.

## Movement-bearing NPC presets - 2026-10-05

NPC preset capture now freezes supported own script movement together with
appearance, dialogue and waits. Export uses **legaia.npc-preset-file.v5** when
movement is present, with the existing 512 KiB metadata bound. Formats v1-v4
remain supported. Capture, export/import and reviewed placement freshly qualify
the donor-owned instruction targets and operand fields; malformed owners, types,
grid coordinates, missing targets and unsupported opcode fields reject. Frozen
metadata stays independent of subsequent source-draft edits. Import adds only a
library entry; a separate reviewed placement creates the NPC.

The library/import summary reports movement target counts. Review changes withdraw
Apply, and exact reviewed placement metadata must retain all supported edit families.
Script movement coordinates remain separate from the chosen NPC placement.

Validation: 35 focused Python checks passed, one existing optional check skipped,
and two Node suites passed. The actual editor captured/downloaded/uploaded a v5
preset, reviewed an independent library import, exercised Undo/Redo and Save/reload,
and reviewed/inspected/applied an independent instance. Existing entities and source
draft/import metadata stayed fixed. The 540px import dialog was visually inspected.
Normal compressed MAN Build `4725587333eecfe2` was independently reopened: emitted
NPC movement X3200/Z5696/selector10, own wait11, own text and model105/animation13
all survived transfer. Chosen placement X3200/Z5760 remained independent.
Package SHA256: `48a4564f2c96a8224f1413583f8732262a74c05d3ed2565f211a97272f001ed8`.
Evidence: `local-output/sdk-20260909/npc-movement-presets-20261005/proof.json`.
The private readback helper initially expected a hex field instead of an audit byte;
corrected readback passed against the existing Build without rerunning gameplay.
No game was launched. Runtime dispatch/selector behavior and streaming retail
package acceptance remain unverified; gameplay is deferred. The full SDK goal is
active/incomplete.

## Independently author NPC script movement - 2026-10-05

NPC Inspector and registered Asset Details now offer **Edit NPC script movement**.
The source-qualified picker groups reached instructions and exposes only their
supported X/Z and encoded move-selector fields. Each field has a retail value and
an independent own-override checkbox. Review preserves unselected operands; input
changes withdraw Apply. Apply/Clear use one NPC history step. Undo/Redo and
Save/Open retain script donor, appearance, dialogue, waits, name and placement.
Changing script donor requires clearing retained movement first.

The editor labels encoded dispatch context as unresolved. Script targets remain
separate from placement/live coordinates; selector meaning, Y, depth, branch
execution and runtime behavior are not inferred. Native serialization composes
NPC movement before other supported edits against final allocated record IDs.
Normal compressed/streaming MAN paths record npc_movement_changes separately.
Movement-bearing NPC preset capture/transfer/placement is now supported; see the
latest v5 checkpoint above.

Validation: 40 focused Python checks and two Node suites pass. Actual root editor
source loading, field Review/Apply, withdrawal, Clear, Undo/Redo and Save/reload
passed; the 540px grouped dialog was inspected. Normal Build `f58172af849a0417`
independently reopened the emitted NPC record with X3200/Z5696/move selector 10,
retained 11-tick wait, own dialogue and model105/animation13. Imports and authored
placement remained fixed. Package SHA256:
`46cca87024e38f696ab6749d2b151e1792e2abc8d4ec1fce620b02bb07567c08`.
Evidence: `local-output/sdk-20260909/npc-movement-editor-20261005/proof.json`.
The actual package check covers compressed MAN; streaming integration has not yet
received a separate retail package check for NPC movement. Saved-script comparison
now explains qualified movement operands; other unqualified changes stay unexplained. No game was launched.
Gameplay remains deferred and the full SDK goal stays active/incomplete.

## NPC-owned movement operand serializer - 2026-10-05

Added native serialization for source-qualified movement operands in allocated
NPC scripts: MOVE_TO/NPC_RUN encoded X/Z and NPC_RUN/EXEC_MOVE move selectors.
Requests name a draft, its retail script donor and stable supported instruction
IDs. Final clone indices, local/script entry ownership, exact extent and alias
checks are now shared with NPC wait serialization. Source-stopped paths, wrong
owners, unsupported fields, stale opcode/dispatch/operand preimages and overlapping
writes reject. Source-identical requests also qualify current preimages.

Only requested fixed-width operand bytes may change. NPC_RUN depth, extended
context, Y, placement, opaque bytes and unrelated candidate content remain held.
Script targets are not current NPC transforms or live actor coordinates; selector
meanings and runtime dispatch remain unresolved. Bounds remain 128 allocated drafts
and 1024 requested targets with a 4 MiB MAN candidate.

Validation: 18 focused Python checks pass across movement/waits/appearance/dialogue.
Ordinary/extended MOVE_TO/NPC_RUN/EXEC_MOVE, two clones, final offsets, no-op,
wrong values/fields/donors, aliases and stopped paths are covered. A fresh retail
actor0040 two-clone candidate composes independent X/Z and selector edits with own
waits and initial appearance. Exactly six movement bytes changed; layout, waits,
all unrelated candidate bytes and every project file/history entry remain held.
The existing retail NPC wait probe passed again after sharing allocation guards.
Evidence: `local-output/sdk-20260909/npc-movement-native-20261005/proof.json`.
Project commands, persistence, editor controls, presets and normal Build integration
remain next. No game was launched; runtime movement remains deferred. The full SDK
goal stays active/incomplete.

## Explain NPC authored edits in saved-script comparison - 2026-10-05

Retail donor/generated NPC comparison now labels exact bytes accounted for by
saved initial-appearance, own-dialogue and own-wait audit spans. Each span binds
the emitted allocation, separate retail/generated offsets, exact before/after
bytes and the current NPC authored field. Overlapping or inconsistent spans,
wrong owners, preimages, values or allocations reject. Source/header bounds and
receipt integrity are rechecked. The browser independently verifies the same
span bytes and authored bindings before displaying the explanations.

Unaccounted changes remain **Other record change - unexplained**. They are not
classified as authored edits or presumed to be harmless append rebasing. Counts
report only changed bytes within qualified spans. Existing header/tail byte
comparison, opaque-path limits and runtime uncertainty remain intact. The whole
workflow is read-only and the bounded/paged comparison table remains available.

Validation: 19 focused Python checks and the Node comparison contract pass.
Actual retail saved Build `a61cd16b02574b72` contains 26 changed bytes: 23 accounted
for by initial appearance, own dialogue and own wait; 3 remain unexplained. The
real server/dialog rendered all categories, the 540px screenshot was inspected,
and every project file/history entry remained unchanged. No command, Save, Build
or Run was called. Evidence:
`local-output/sdk-20260909/npc-authored-script-comparison-20261005/proof.json`.
No game was launched. Gameplay equivalence remains unverified and the full SDK
goal stays active/incomplete.

## Preserve NPC-owned waits in reusable presets - 2026-10-05

NPC preset capture now freezes supported own wait targets together with own
dialogue and independent initial appearance. Capturing, portable transfer and
reviewed placement freshly qualify the wait operands against the recorded script
donor. Changing the source draft later does not change the captured definition.
Library import creates an independent preset identity; placement remains a separate
reviewed command. Inspector library/import summaries show the owned wait count.
The preceding temporary rejection of wait-bearing capture is superseded.

Wait-bearing presets use portable format **legaia.npc-preset-file.v4**, bounded
at 512 KiB. V1 donor-only, v2 text and v3 appearance formats retain their formats and
bounds. Exact donor-owned wait IDs and duration_ticks integers 0..32767 are required;
older formats cannot carry wait bindings. Presets contain metadata, not retail
script/model payloads or live state. Undo/Redo and Save/Open retain all bindings.

Validation: 19 focused Python checks and two Node suites pass, including frozen
capture, v4 transfer/placement, wrong types/owners and older-format rejection.
Actual browser capture/download/upload, reviewed library import with input
withdrawal, Undo/Redo, Save/reload and scene-reviewed placement passed across two
private projects. The 540px review was visually checked. Normal recipient Build
`a61cd16b02574b72` independently read back own wait 11 ticks, model105/animation13
and complete own dialogue. Package SHA256:
`006d1deec3bfce5982734a2844e2ef647975c15ce50befe3af72bff4adf26889`.
Evidence: `local-output/sdk-20260909/npc-waits-presets-20261005/proof.json`.
No game was launched; runtime timing, residency and script compatibility remain
deferred. The full SDK goal stays active/incomplete.

## Independently author NPC wait targets - 2026-10-05

NPC Inspector and registered Asset Details now offer **Edit NPC wait targets**.
The source-qualified picker separates retail targets from optional NPC-owned
WAIT_FRAMES overrides and accepts integer duration_ticks 0..32767. Review binds the
full current project/draft; input changes withdraw Apply, and stale reviews reject.
Apply/Clear make one existing NPC history step. Undo/Redo and Save/Open retain
script donor, own appearance, own dialogue, name and placement. Changing the script
donor with retained waits requires clearing them first. Asset summaries label own
wait targets separately; no runtime timing, seconds or reachability is asserted.

Normal compressed/streaming MAN composition now uses the native clone adapter
against final allocated record identities. The saved package records a separate
npc_wait_changes audit. NPC preset capture currently rejects wait-bearing drafts
explicitly, preventing silent omission; preset capture/transfer/placement support
is still next.

Offline validation: 36 focused Python checks and two Node contracts pass.
The actual root editor passed source loading, reviewed Apply, input withdrawal,
Clear, Undo/Redo and Save/reload. The 540px dialog screenshot was inspected.
Normal Build `5e3865fd5768fd42` independently reopened the emitted NPC script with an
exact 11-tick operand, model105/animation13 and complete own dialogue. Other drafts
and imports stayed fixed. Package SHA256:
`e3ab5e46486e9869c807360b6f3192b24f3b0ecbdea78ba2600c0e889948e54b`.
Evidence: `local-output/sdk-20260909/npc-waits-editor-20261005/proof.json`.
This actual package check covers the compressed MAN route; streaming composition
is integrated but has not received a separate retail package check for own waits.
No game was launched. Runtime timing acceptance remains deferred and the full
SDK goal remains active/incomplete.

## NPC-owned wait operand native adapter - 2026-10-05

Added a source-qualified serializer for independent WAIT_FRAMES operands on
allocated NPC scripts. Requests bind a draft, recorded retail script donor and
supported stable wait IDs with integer duration_ticks 0..32767. The adapter resolves
final record indices after all appends, verifies extent/local entry ownership,
rejects aliases/retail targets, requalifies current instruction layout and checks
exact operand preimages. Only selected two-byte targets can change. Limits are
128 drafts and1024 targets per candidate. Seconds and runtime scheduling are not
inferred; unknown/stopped source paths remain unsupported.

Nine focused checks pass across NPC waits, existing wait/appearance/dialogue
adapters. Coverage includes two independent clones, ordinary/extended waits,
boundaries, source-identical no-op, stale preimages, final offsets, aliases,
malformed ownership/values and decoder stops. Fresh town01 discovery qualifies
waits for actors0040/0044/0046. A retail two-clone candidate from actor0040 holds
independent11/22-tick targets, composed with the existing model/animation appearance
patch. Layout, all non-wait candidate bytes, donor candidate record and every
project file/history entry remain unchanged. Append's supported spawn-reference
rebasing is already part of the pre-wait candidate baseline; this is not a claim
that append preserves raw retail records byte-for-byte.
Evidence: `local-output/sdk-20260909/npc-waits-native-20261005/proof.json`.
Project commands, persistence, presets, editor controls and normal Build integration
remain next. No game was launched; runtime timing acceptance stays deferred.
The full SDK goal remains active and incomplete.

## Review NPC appearance in the placed scene - 2026-10-05

The NPC appearance picker now offers **Inspect NPC appearance in scene** after
Review. It renders a detached Proposed scene at the selected NPC's existing
placement, with Current/Proposed switching and Return to NPC appearance. Return
retains the reviewed choice; changing the choice withdraws inspection and Apply.
The SDK requalifies the witness and review before creating the detached view.
Project metadata, retail imports, script donor, own dialogue and history remain
unchanged. Scene identity, retained placement/script/evidence, unrelated entities
and model/geometry ownership are checked before displaying the proposal.

Offline validation: 11 focused Python checks and the Node appearance contracts
pass. Actual retail HTTP rejects stale reviews and unsupported fields. The full
editor passed clear-override model92-to-model105 comparison, both layer switches,
return-to-review and changed-choice withdrawal without command, Save, Build or
Run calls. The scene screenshot was inspected. Evidence: proposal-proof.json and
appearance-proposal-scene.png under
`local-output/sdk-20260909/npc-appearance-editor-20261005/`.
This is a visual authoring preview; runtime compatibility remains unverified.
No game was launched. Gameplay acceptance stays deferred and the full goal active.

## Independently author an NPC initial appearance - 2026-10-05

NPC Inspector and registered Asset Details now offer **Choose NPC initial
appearance**. The reviewed picker uses freshly source-qualified retail witnesses
for existing local model/animation pairs. Apply changes one authored binding,
retaining the script donor, own dialogue, name and placement. Changing the picker
withdraws Apply. Clear restores the script donor's initial pair. Undo/Redo and
Save/Open preserve the independent binding; changing script donor while bindings
are retained requires clearing them first.

Scene preview, asset/model references, model navigation and animation inspection
follow the appearance witness; retail script inspection continues to follow the
script donor. Frame inspection still targets the authored NPC placement. Normal
compressed/streaming MAN composition uses the native adapter from the preceding
checkpoint to patch final allocated header offsets only. Saved Build inspection
now qualifies the emitted pair against its recorded appearance witness.

NPC presets capture both supported own appearance and dialogue. Portable format
v3 binds the appearance witness to the script donor and owning import, retaining
the 512 KiB authored metadata bound. V1 donor-only and v2 text-only files retain
their existing formats/bounds. Transfer and placement reverify compatible pairs;
no retail script/model payload or runtime state is copied into the preset.

Offline evidence: 42 focused Python checks and five Node contracts pass. Actual
Inspector/Asset Details review, withdrawal, Apply, Undo/Redo, Save/reload, scene
and model reference checks passed; the 540px layout was inspected. Normal Build
`47edfdee85c4fdb2` contains exact model92/animation9 and the complete authored glyph
span, preserving script donor0012 and other drafts/imports. Retail witness0040
animation inspection and frame1 scene placement passed without history changes.
V3 capture/export and synthetic cross-project transfer/instantiation preserve both
bindings. Evidence is under `local-output/sdk-20260909/npc-appearance-editor-20261005/`.
No game was launched. Initial assignment does not prove script compatibility,
residency, eventual appearance or gameplay; those checks remain deferred.

## Independent NPC appearance native adapter - 2026-10-05

Added a source-qualified native adapter that keeps an NPC's script donor separate
from its initial model/animation witness. Requests identify an allocated draft and
a retail witness record; native numbers and bytes are not supplied by clients.
The existing MAN assignment validator checks local bank membership, compatible
object/channel counts and donor ownership. Only the selected clone's two initial
header bytes can change. Final record identities resolve offsets after all appends;
intermediate allocation offsets are not reused. Retail records, aliases, ambiguous
allocations, unsupported pairs and changed header preimages reject.

Focused synthetic checks cover two clones, later table growth, exact byte scope,
repeat/preimage rejection, malformed ownership, aliases and incompatible channels.
A retail town01 candidate changed model105/animation13 to qualified model92/
animation9 from donor0040 while retaining script donor0012 and authored dialogue.
Exactly two header bytes changed; all other bytes and the second clone remained
unchanged. Project state/history/files were preserved. Evidence is under
`local-output/sdk-20260909/npc-appearance-native-20261005/`.

This is native foundation work, not yet an editor feature or normal Build input.
Next: integrate an independent appearance binding into project commands, scene
preview/asset/animation references, persistence, presets and normal Build, then
verify the complete editor workflow. Runtime compatibility and gameplay remain
unverified; no game was launched. The full SDK goal remains active.

## Retain NPC dialogue in reusable presets - 2026-10-05

Capturing an NPC preset now freezes its supported own dialogue with the retail
donor, name and native-grid placement defaults. Later edits or deletion of the
capture NPC do not change the preset. Reviewed placement deep-copies those edits
into an independent new NPC, where normal dialogue authoring and Build apply.
Capture, transfer and placement reverify the text runs through the existing
source-qualified equal-span serializer; unknown/aliased runs, controls, oversized
text and a mismatched donor reject. Runtime state and other script edits remain
outside this snapshot.

NPC preset JSON v2 carries only source-bound preset metadata and user-authored
text edits, with a 512 KiB file bound. Donor-only NPC v1 and ordinary actor preset
files retain their 8 KiB bound and original format. A version/content mismatch
rejects. The editor displays the owned-run count and verifies that placement
retains the exact captured text. No retail script bytes or native packets are
included in the portable file.

Offline evidence: 16 focused Python checks and the NPC preset/file browser
contracts pass. A real two-project browser workflow captured text, downloaded
and uploaded v2 JSON, reviewed/imported a new library identity, passed Undo/Redo
and Save/reload, then reviewed scene placement and created an independent NPC.
Existing source drafts/imports and recipient scene entities remained unchanged.
The inspected 540px layout is readable. Normal Build `2e2e86485096975f` reads
back the complete authored glyph span including space padding. Evidence is under
`local-output/sdk-20260909/npc-dialogue-presets-20261005/`. No game was launched;
manual spawning, reachability and dialogue-layout acceptance remain deferred.

## Author dialogue independently for an NPC - 2026-10-05

NPC Inspector and registered Asset Details now offer **Edit NPC dialogue**.
The workspace freshly verifies the retail donor's supported plain-glyph runs,
shows retail and authored text separately, and reviews a complete NPC-local edit
set before Apply. Checked runs override this NPC only; unchecking restores retail
text. Shorter replacements are space-padded, longer text and control/substitution
edits reject. Existing decoder gates for unknown stops, aliases and menu ownership
remain intact. Static paths do not establish runtime dialogue reachability.

One reviewed command updates the authored NPC draft with one Undo step. Undo/Redo,
Save/Open, draft copies and authored-input freshness retain the NPC-local text.
Changing donor while text is retained rejects with an explicit clear-first message;
text-run identities cannot silently migrate to another donor. NPC presets still
capture donor/placement definitions; text presets remain a separate future feature.

Normal Build patches only the audited appended record, after allocation and before
other scene composition, using freshly verified source glyph preimages and bounded
equal-span offsets. Compressed and streaming MAN paths share the same adapter.
Retail donor records, other NPCs, record extents, controls and section layout remain
unchanged by these text edits. Build audits expose the NPC-owned text spans.

Offline evidence: 41 focused Python checks and four Node contract suites pass. Real editor
Review/Apply/Undo/Redo/Save workflows and inspected 540px layouts passed in private
format6 fixed-span and format7 relocated projects. Normal packages independently
read back exact NPC text; complete generated donor records match their prior
Builds exactly. Asset Details reopening shows the persisted own text; its action
row now wraps to keep buttons inside the dialog. Both source/generated
comparisons show 26 changed bytes including placement headers. Evidence is under
`local-output/sdk-20260909/npc-dialogue-20261005/`. No game was launched; spawning,
reachability, text layout and runtime behavior remain deferred manual acceptance.

## Compare saved NPC records with retail donors - 2026-10-05

The generated NPC script workspace now offers **Compare generated record with
retail donor**. Both records are freshly inspected against the current project,
verified source disc and intact saved Build receipt. The dialog compares exact
bytes at the same relative record offsets and retains separate retail and
generated MAN offsets, record hashes, lengths and script-entry offsets.

Changes before both script entries are labelled record header; other changes
are labelled script or remaining record bytes. Missing bytes are explicit, and
large differences are paginated in groups of 128. Script tails include opaque
and unvisited data. Matching bytes establish neither instruction equivalence
nor runtime spawning, scheduling or execution. Closing returns to the generated
record workspace with the selected NPC retained. Stale inputs and inconsistent
comparison counts, bytes, scopes or identities reject before rendering.

Offline evidence: focused Python and Node comparison, generated-record and
retail-source checks pass. Real browser comparison passed format6 fixed-span
and format7 relocated packages, including inspected 540px layouts. Both have
2 changed header bytes and 507 identical common bytes; their script tails match.
Retail MAN offset 8487 remains distinct from generated offsets 44648 and 44720.
Project history, authored inputs and every preexisting file remained unchanged;
no Save, Build or game launch occurred. Evidence is under
`local-output/sdk-20260909/npc-script-comparison-20261005/`. Manual gameplay
verification remains deferred; this milestone is read-only package evidence.

## Inspect NPC scripts emitted in saved Builds - 2026-10-05

NPC Inspector and Asset Details now offer **Inspect saved Build script...**.
Choose an intact saved package matching current authored inputs. The SDK verifies
the receipt/audit/manifest/archive and user-owned source disc, reconstructs the
emitted PROT from verified fixed-span overlays or relocation data, then reads the
actual generated MAN record by the audited NPC allocation index. Final table
spans are parsed from emitted bytes, never copied from intermediate append offsets.

The read-only workspace exposes generated dialogue, instruction navigation and
raw/record evidence with Build-scoped script identities. Retail donor inspection
remains separate. Stale inputs, wrong NPC/record/package identities, changed
payloads, ambiguous overlay spans and invalid record bounds reject. Package and
source-disc integrity do not establish runtime spawning, scheduling or execution.
The former **Inspect serialized candidate** label is corrected to **Inspect donor
append prototype**; prototype text now directs complete-project readiness to
Review Build rather than claiming that normal NPC Build is unavailable.

Offline evidence: 21 focused Python checks and Node generated/donor/Asset/NPC
Inspector contracts pass. Actual browser workflows passed both Inspector entries,
generated/retail separation, path navigation and inspected 540px layouts for a
format6 fixed-span package and a format7 relocated package. Stale-input receipts
reject. Final bounded payload reads and record/hash guards accept both actual
package responses. Generated offsets are44648 and 44720 respectively. Project,
history, Build input identity and preexisting files are unchanged. No new Build,
Save, game launch, install or disc export occurred. Evidence:
`local-output/sdk-20260909/npc-saved-build-script-20261005/` (`proof.json`,
`final-readback.json`, `fixed-540.png`, `relocated-540.png`). Gameplay remains deferred.

## NPC retail donor script inspection - 2026-10-05

Authored NPCs now expose **Inspect retail donor script...** in the NPC Inspector
and a registered **Inspect retail donor script** action in Asset Details. The SDK
qualifies the active draft/donor and freshly verifies the imported donor against
the user-owned disc. The read-only workspace shows decoded dialogue, searchable
instruction paths, flow overview, successor navigation, source spans, raw record
and explicit decoder stops. Unknown paths and branch reachability stay unknown.

The report captures full project source identity and exact draft/donor provenance;
stale or forged bindings and authoring/generated claims reject. Source offsets
belong to the imported donor, not allocated NPC code or a live actor. This view
adds no NPC script authoring or runtime execution claim. Donor authoring remains
separate from this retail-only inspection.

Offline: 20 focused Python checks and donor-script, Asset Inspector and NPC
Inspector Node contracts pass. The private retail browser passed both entry points,
exact source response, instruction navigation and retained NPC selection. The
540px layout was inspected. Donor0012 has 25 decoded instructions and16 dialogue
segments; its record SHA-256 is
`5063e5eb8bfd400fba142b0eabee28f50c46b900aa319ebdf86fd0b4eea73a65`.
Project document, Undo/Redo history, normal Build input identity and preexisting
files stayed unchanged. No commands, Save, Build, game launch, install or disc
export occurred. Evidence: `local-output/sdk-20260909/npc-donor-script-20261005/`
(`proof.json`, `browser.log`, `donor-script-540.png`). Gameplay remains deferred.
See [NPC donor script workflow](legaia-npc-donor-scripts.md).

## Copy selected NPC arrangements - 2026-10-05

**Repeat draft...** now offers **Copy selected NPC arrangement** when the current
or recalled selection contains at least two same-scene NPC drafts. Mixed selection
members outside the NPC group are excluded with a count. Copy the arrangement in
a line or rectangular grid: each member keeps its own retail donor and receives
the same native-grid offset per repetition, preserving relative X/Z positions.
Copies receive independent stable IDs and bounded member-derived names. They are
independent NPC drafts; no parenting, prefab inheritance or runtime spawning is
asserted. The project-wide 128-draft limit and native coordinate bounds apply.

Review creates no project changes. Detached scene inspection retains original
entities and each copied member's model binding, with Current/Proposed/Return.
Source/input changes withdraw the review. Apply adds all copies in one Undo step;
Redo and Save/Open preserve them through the existing normal Build pipeline.

Offline: 13 focused Python checks and Node proposal/scene contracts pass. A private
retail browser copied two differently bound NPCs, checked held originals, exact
relative placement and member-specific geometry, then Apply/Undo/Redo/reload.
The 540px review was inspected. Normal format-7 Build independently decoded the
complete candidate MAN and all nine appended records: new record57 is X3392/Z5632,
model105/animation13; record58 is X3072/Z5632, model111/animation56. Current saved
receipt and preserved project/history/preexisting files pass. Evidence lives in
`local-output/sdk-20260909/npc-arrangement-repeat-20261005/` (`project-verified-2`,
`proof.json`, `normal-build-proof.json`, `arrangement-540.png`). Package SHA-256:
`88fe43534bacd8dfe12a5d9a9e02d3b56f0d2fc834e636cc2397880056c2f6ab`.
Gameplay spawning, scheduling, scripts, collision and visibility remain deferred.
No game launch, install or disc export occurred.

## Reviewed NPC group retail donor assignment - 2026-10-05

The NPC Inspector now offers **Assign NPC group donor...** for 2 through 128
same-scene drafts. Current or recalled scene selections seed the dialog; mixed
selections retain only NPC members with an exclusion note. Choose an imported
retail donor, review the exact membership, then inspect the detached proposed
scene with Current/Proposed comparison and Return before Apply. Identity, name
and X/Z stay fixed; imported actors and unselected scene content stay unchanged.

This changes inherited native model, initial animation, scripts and related actor
data. It is donor reuse, not arbitrary model/animation assignment. Source changes,
input changes and malformed proposals reject or withdraw Apply. One Apply creates
one Undo step; Redo and Save/Open preserve the reviewed donor bindings.

Offline evidence: eight focused Python cases and the Node proposal guards pass.
The actual private browser passed Review without mutation, detached scene model
bindings, Current/Proposed/Return, input withdrawal, Apply, Undo/Redo and reload.
The final read-only check passed the tightened guards and an inspected 540px
layout. Normal Build independently decoded the complete format-7 compressed MAN:
selected records 53/54 retained X/Z 2944/5568 and 3136/5568 while changing donor
model/animation from 105/13 to 111/56. All five unselected appended records retained
105/13 and their positions. Saved receipt freshness and project preservation pass.
Evidence: `local-output/sdk-20260909/npc-donor-group-20261005/` (`proof.json`,
`normal-build-proof.json`, `ui-final.log`, `donor-group-540.png`). Package SHA-256:
`e936966c4e152a74f4fe35c1ffd722b499c888d79e3316e3ef9eac486117a58c`.
Gameplay visibility, spawning, scheduling and inherited script behavior remain
unverified. No game launch, install or disc export occurred.

## Repair saved selections after NPC deletion - 2026-10-05

Saved selections containing deleted NPCs now support **Replace with current
placements**. Select available placements in the saved scene, then replace the
membership. The set keeps its stable identity and name; one Undo restores its
previous members, including missing NPC references. The dialog identifies
unavailable NPCs and explains the repair path. Recall still rejects missing NPCs.

Replacement proves the original import and MAP binding before dropping members,
including removal of all scenery. New membership must be available in the owning
scene. Stale keys, source drift, empty/invalid replacements or a project change
during source proof reject before publication. Repair changes editor metadata only.

Validation: 16 focused scene/actor selection Python cases and both Node selection
suites passed. Checks cover source drift, stale keys, unavailable replacements,
metadata Undo/Redo, persistence and unchanged Build identity. Actual private Town01
browser checks passed the missing-member note, rejected Recall, same-ID/name repair,
Undo/Redo, Save/reload, disk reopen and successful repaired NPC focus. The 540px
message was inspected; no page errors occurred. Imports, game overrides, NPC data
and Build input identity stayed unchanged. Evidence:
`local-output/sdk-20260909/npc-selection-repair-20261005/proof.json`.
No game launch, Build, installation or full-disc export ran for this metadata-only
repair. Gameplay remains deferred; the full SDK goal stays active and work stays solo.
See [Saved scene selections](legaia-scene-selections.md).

## Saved NPC selections feed group authoring - 2026-10-05

Opening **Move NPC draft group...** now checks the NPC members of the current
scene placement selection, including recalled saved selections. A focused draft
remains the default when no NPC group is selected. The dialog copies membership
and qualifies every selected NPC against the active scene before opening.
Unavailable, wrong-scene, duplicate or oversized selections reject with a visible
error. Existing checkbox/search controls still let the user change membership.

For mixed selections, the NPC tool includes only NPC members and reports how many
other placements it excludes. Use mixed scene placements to edit all kinds together.
This closes the saved-selection-to-authoring handoff for offset/layout/removal review;
selection alone does not change project or game data. The existing review source
binding, detached scene proposal, atomic command history and serializer remain.

Validation: 16 focused SDK group/selection cases, the expanded group and saved
selection Node checks, and editor syntax passed. Actual private Town01 browser
checks covered focused default membership, saving/reloading/recalling an NPC pair,
exact checked members and review targets, preview without mutation, Apply/Undo/Redo,
unchanged unselected drafts, explicit mixed-selection scope, Save/reload and disk
reopen. The 540px dialog was inspected; no page errors occurred. Normal format 7
Build readback matched the complete prepared MAN and all seven appended NPC rows,
including the edited pair with donor model/animation preserved. Saved package
verification matches current inputs; Build preserves project/history/preexisting
files. Package SHA256:
`cafe9311747208ea97b8dbc54cb50e7a772397aaaeb1189761b8444011550cc4`.
Evidence: `local-output/sdk-20260909/npc-selection-group-handoff-20261005/proof.json`
and `normal-build-proof.json`. No game launch, installation or full-disc export ran.
Gameplay remains deferred; the full SDK goal remains active and work stays solo.

## Native-grid NPC group rotation, scale and reflection - 2026-10-05

The NPC group Inspector tool now adds position rotation (-90/+90/180 degrees),
spacing scale (1-1000 integer percent), and X/Z coordinate reflection about a
selected NPC anchor. It operates on 2-128 existing NPC drafts in the active Edit
scene. Rotation uses exact X/Z quarter-turn permutations; scale rounds final
coordinates to the native 64-unit grid with half steps away from zero. Reflection
changes one coordinate. The selected anchor stays fixed. These layouts change
positions, preserving model geometry, facing, donor bindings and other metadata.
Rounded placements can coincide; inspect Current/Proposed before Apply.

Exact typed layout requests, a distinct native-layout review-key binding, complete
source snapshots and full bounds validation qualify the whole group. Invalid,
stale or out-of-bounds proposals publish nothing. The existing detached scene
preview and atomic Apply/Undo/Redo work unchanged; no-ops retain redo history.
Offset, alignment, distribution and removal remain compatible.

Validation: 16 focused Python cases and group/repetition/mixed-NPC Node checks passed.
Actual private Town01 browser checks covered all three rotations, scale and both
reflection axes, fixed anchor, input withdrawal, Current/Proposed/Return, exact
renderer matrices, unchanged geometry/unselected entities and preview without
mutation. One reflection passed atomic Apply/Undo/Redo, Save/reload and disk reopen;
the 540px dialog was inspected, with no page errors. Normal format 7 Build readback
matched the complete prepared MAN and all seven appended NPC positions, model 105
and animation 13. Saved package verification matched current inputs; Build preserved
project/history/preexisting files. Package SHA256:
`b3185a16a71aea60a3ffba163d1f0131f021daeab4168751fb07f0ac72eab560`.
Evidence: `local-output/sdk-20260909/npc-native-layout-20261005/proof.json` and
`normal-build-proof.json`. No game launch, installation or full-disc export ran.
Gameplay remains deferred; the full SDK goal stays active and work stays solo.
See [NPC draft group workflow](legaia-npc-draft-groups.md).

## Saved scene selections include NPC drafts - 2026-10-05

**Saved scene selections** now stores 1-128 scene placements including authored
NPC drafts, imported actors and static decorations. Save an individual NPC from
its Inspector focus or capture a mixed selection. Recall focuses the NPC Inspector
for a single draft and restores mixed membership for the placement tool, including
when switching from another imported scene. Saved sets retain identities, so NPC
moves and renames do not restore old transforms or duplicate actors.

NPC-only sets require no MAP hash. Scenery membership retains fresh MAP source
proof, and NPC members must be available in the owning scene for Create/Replace/
Recall. Deleted NPC references remain portable metadata: Save/Open, Rename and
Delete still work, while Recall reports the unavailable member. Undoing deletion
restores recall. Existing source-bound actor/scenery sets remain compatible.

Validation: 17 focused Python cases, scene/actor selection Node checks and editor
syntax passed. Actual private Town01 browser checks passed mixed and NPC-only Save,
library Undo/Redo, Save/reload, NPC Inspector focus, cross-scene mixed recall, opening
the recalled mixed placement dialog, missing-NPC rejection and deletion Undo.
The 540px dialog was inspected; no page errors occurred. Imports, NPC content,
game overrides and Build input identity remained unchanged by selection metadata.
Evidence: `local-output/sdk-20260909/npc-saved-selections-20261005/proof.json`.
No game launch, Build, installation or full-disc export ran for this metadata-only
feature. Gameplay remains deferred and the full SDK goal remains active. Work is solo.
See [Saved scene selections](legaia-scene-selections.md).

## NPC drafts in mixed scene placement groups — 2026-10-05

**Scene tools → Select scene placements → Move scene placement group** now accepts
2–128 members spanning at least two of imported actors, authored NPC drafts and
static decorations. Shared offsets, alignment, distribution, spacing scale, position
rotation and coordinate reflection use the existing review workflow. NPCs keep native
64-unit X/Z coordinates and may be layout anchors. Their donor, name and other
metadata stay unchanged. Current/Proposed inspection holds source preview height.

NPC-inclusive reviews use version 2 and bind the full Current draft snapshot. NPC
Retail placement is absent and shown as **Authored only**; Retail reset is disabled
and rejected for the entire group. Existing actor/scenery version 1 reviews remain.
Apply validates the whole proposal before changing overrides and NPC drafts, then
records one combined Undo step. No-op operations preserve history and redo. Saved
selection sets and runtime placement semantics are separate work.

Validation: 31 focused Python cases, new NPC source/DTO guards, legacy mixed-placement
Node checks and editor syntax passed. Actual private Town01 browser checks covered
three-kind selection, hierarchy membership, exact proposals with held height, review
without mutation, Current/Proposed inspection, atomic Apply/Undo/Redo and Save/reopen.
The 540px review was inspected; no page errors occurred. Normal Build emitted a
format 6 package whose complete native MAN and MAP carriers match preparation.
Readback confirmed imported actor record 12 at X/Z 3840/1920 and appended NPC record
53 at 3008/5696 with donor model 105 and animation 13. The decoded-size patch and
saved receipt match current inputs; Build preserved project/history/preexisting files.
Package SHA256: `e728785c95c6e58f925b3873b785c21b93396e6c711bb9c64f2f465182b61361`.
Evidence: `local-output/sdk-20260909/mixed-npc-placement-20261005/proof.json` and
`normal-build-proof.json`. No game launch, installation or full-disc export ran.
Gameplay remains deferred; the full SDK goal remains active. Work continues solo.
See [Mixed scene placements](legaia-scene-placement-groups.md).

## NPC preset file transfer — 2026-10-05

NPC presets now use metadata-only `legaia.npc-preset-file.v1` JSON in the shared
preset export/import workflow. The editor downloads `npc-preset.json`, reviews an
independent named library import, then places a new NPC through the separate
reviewed placement workflow. File/schema scope, exact source/components, capture
provenance, matching import hashes and the 8 KiB limit are checked. Export/import
freshly verify the owning retail scene against the project user's disc. Unknown
payload fields, changed sources and stale library reviews reject. Imported-actor
preset application remains separate.

Actual private two-project browser acceptance verifies download/upload, a new
library identity with retained provenance/defaults, changed-name review withdrawal,
library Undo/Redo, Save/reload and disk reopen, then detached scene inspection and
placement without the original capture draft. Source project document/history and
all file bytes stay unchanged; recipient imports and existing scene entities stay
unchanged. The 946-byte exported file contains metadata only. The 540px import
review is visually inspected with no page errors. Focused NPC/template-file Python
and Node checks and existing animation-preset regression checks pass.

The recipient's private normal format-6 Build uses the compressed reserved-span
route. Native MAN bytes exactly match preparation; descriptor decoded size and
new record 53 read back at X 2944 / Z 5632, model index 105, animation ID 13. Saved
receipt verification matches current inputs. Package SHA-256:
`5f3f409de8ac2e613f18602bb1771312bca52b00c2d2caf1dbcfd9adf3d3b5c6`.
Evidence: `local-output/sdk-20260909/npc-preset-transfer-20261005/proof.json`,
`normal-build-proof.json` and `transfer-review-540.png`. No game, install or full-disc
export occurred. Prefab inheritance, cross-scene remapping and runtime gameplay
acceptance remain unsupported or deferred. See [NPC presets](NPC_PRESETS.md).

## Reusable NPC draft presets — 2026-10-05

The preset library now supports a separate `npc-draft-preset-v1` scope. Select an
NPC draft and choose **NPC presets…** to capture its retail donor, authored name
and native X/Z defaults with owning scene, import hash and original draft provenance.
Review a new named instance at a chosen 64-unit-grid placement, compare the detached
scene with Current, then Apply. Capture and placement each have their own Undo step;
rename, delete, Save and reopen use the existing project template library. A preset
survives deletion of its original draft. Imported-actor template Apply rejects this
scope; cross-scene, stale, Live-mode and invalid placement requests fail closed.

Focused Python/Node checks and an actual private browser pass capture, changed-input
review withdrawal, exactly one scene addition, preservation of existing entities,
Apply, atomic Undo/Redo, Save/reload and disk reopen. Narrow review actions wrap
within the 540px viewport. A private normal format-7 Build contains all seven authored
NPC rows; the preset instance reads back from native MAN at X 3008 / Z 5632. Complete
native MAN bytes match preparation and saved receipt verification matches current
inputs. Package SHA-256:
`18ea1110520c28bdb321499dc8f466f868512be03b982736eddc8429c1e43adc`.
Evidence: `local-output/sdk-20260909/npc-presets-20261005/proof.json`,
`normal-build-proof.json` and `preset-review-540.png`.

This is project-local donor/placement reuse, not prefab inheritance or an authored
script/appearance snapshot. Shared asset edits remain project-wide. See the NPC
preset transfer milestone for file interchange; cross-scene remapping remains
unsupported. Runtime spawning,
scheduling, collision and visibility remain deferred to manual gameplay; no game,
install or full-disc export was performed. See [NPC presets](NPC_PRESETS.md).

## NPC animation frames at authored scene placement — 2026-10-05

**Inspect animation in scene** now targets the selected NPC draft when entered
through its donor animation Inspector. The donor remains the verified animation
source; the NPC becomes the explicit display target. Existing imported-actor
inspection retains its prior target selection. A dedicated adapter qualifies the
current scene source, unique authored entity, recorded donor/model and authored
X/Z placement before accepting an NPC target. Wrong source, model, donor, duplicate
entity or changed placement rejects the inspection.

The existing isolated geometry workflow changes only the target's display geometry
key. Authored/source position, sampled elevation, display position and model-to-scene
transform remain intact. NPC selection and framing synchronize with the inspection;
the scene bar uses its authored name. Frame changes retain the same NPC geometry
instance. Restore returns the qualified Current scene. This is display-only pose
inspection, not animation assignment, runtime playback or gameplay acceptance.

Focused NPC Inspector Node checks pass source/target/placement rejection. Actual
private browser with shared authored channels and a different authored donor
appearance verifies exact frame vertices, unchanged donor/all other entities,
retained authored transform, NPC selection, frame advancement and restoration.
The 540px viewport is visually inspected with no page errors. Project document,
history and every project file byte remain unchanged. Evidence:
`local-output/sdk-20260909/npc-animation-scene-target-20261005/proof.json` and
`npc-scene-540.png`. No Build, game launch, install or disc export occurred.

## NPC animation Inspector matches shared authored preview — 2026-10-05

The NPC animation button previously opened the imported donor clip even when the
Authored viewport showed shared authored animation channels. It now uses a
qualified SDK draft model reference and the current NPC pose kind: imported pose
opens the retail donor clip; authored pose opens shared authored channels. Labels
identify the representation. Unsupported/missing poses have no fallback action;
pending refresh, busy state and detached scene proposals cannot arm navigation.
The click rechecks source context and binding before opening the model dialog.

The retail donor model and clip owner remain explicit. The donor's authored
appearance is separate. `ModelRenderer.asset_id` already retained the retail
model; inspection corrected the initial suspected wrong-model diagnosis. This
change fixes the animation representation mismatch and strengthens binding checks,
without claiming an NPC runtime animation identity or an established idle stance.

Focused NPC Inspector and Asset Inspector Node checks pass source/pose coherence,
imported/authored channel choice, unknowns and mismatched donor/model rejection.
Actual private browser uses a verified donor appearance override (0105 to 0092)
and a native shared channel edit in `animation://town01/scene-anm/0012`. It opens
model 0105 with the correct donor owner and authored representation; its first
frame differs from the retail response. The 540px dialog passes with no page errors.
Project document, history and all file bytes remain unchanged during inspection.
Evidence: `local-output/sdk-20260909/npc-donor-animation-binding-20261005/proof.json`.
No Build, game launch, install or disc export occurred. Gameplay stays deferred.

## NPC recorded donor-model inspection — 2026-10-05

Authored NPC records and central project inventory entries now expose the SDK's
existing `draft_initial_model_assignment` reference. It retains source draft/name,
owning scene, model asset ID, retail donor ID and `runtime_binding=not_asserted`.
Unresolved donor model references remain null. The draft assignment uses the retail
donor independently of that donor's authored appearance.

NPC Asset Details shows **Recorded donor model** as a read-only SDK reference and
provides **Inspect recorded donor model** when model preview capability and a
coherent assignment are present. The adapter qualifies source/name/scene/donor,
assignment kind and layer before registering navigation; the editor checks the
current SDK reference again before opening the imported model view. The project
inventory adapter also rejects inconsistent model bindings. There is no runtime
residency/pose claim or property-writing action.

Validation: 22 focused Python Inspector/inventory cases pass, including retail
donor separation and explicit unknowns. Asset Inspector and project inventory Node
checks pass binding, malformed-reference, capability and unresolved-action checks.
Actual private browser matches SDK fields in active/project scopes and opens the
exact recorded model response; 540px layout passes, with no page errors. Document,
Undo/Redo and all project file bytes remain unchanged. Evidence:
`local-output/sdk-20260909/npc-donor-model-navigation-20261005/proof.json`.
No Build, game launch, install or disc export was performed. Gameplay stays deferred.

## Reviewed NPC draft group removal — 2026-10-05

The NPC group tool now offers **Remove selected NPC drafts** alongside offset,
alignment and distribution. Review retains exact selected draft metadata and a
full-project source-bound key. Its detached scene proposal removes those authored
instances while preserving every imported and unselected entity. Changing the
operation withdraws Apply. **Remove reviewed drafts** issues `delete_actor_drafts`
and creates one atomic Undo entry; Undo restores stable identities and all metadata.
Only two through 128 existing drafts in the active Edit scene are eligible.
Malformed requests, wrong command types, missing drafts and stale reviews reject
before mutation. Imported donor actors remain unchanged.

Focused SDK group/repetition checks (eleven Python cases) and Node report/scene
qualification pass. Actual private browser verifies review without mutation,
detached removal, operation invalidation, Apply, exact Undo/Redo, save/reload and
independent disk reopen; 540px layout passes with no page errors. A private normal format-7 Build passes current-input saved package verification.
Its final decompressed native MAN matches the prepared candidate and contains
exactly the four remaining appended NPC rows, with both removed identities absent.
Package SHA-256: `e1026d3eb4f83f54970f58b475c157177258f71a05c5b2d5672631dae16b90ef`.
Build leaves the project document/history and preexisting file bytes unchanged.
Evidence is under
`local-output/sdk-20260909/npc-draft-removal-20261005/`. Gameplay remains unverified;
no game launch, install or disc export was performed.

## NPC drafts in the central project Asset Database — 2026-10-05

The SDK project inventory now registers each validated NPC draft as an explicitly
`authored` actor entry. Its stable authored UUID, exact name, donor binding and
X/Z placement remain project metadata. The single owning-scene membership carries
that import's hash as context; it has no retail source record or decoded-catalog
key. Imported/catalog records cannot supply authored NPC identities. Existing
source freshness and asset/membership/metadata budgets cover these entries.

The browser retains imported and authored distinctions, filters by owning scene,
and opens the typed NPC Asset Details and Inspector through existing selection.
The membership control says **Authored NPC owning scene** and explains that its
import hash is context, not a retail origin. Project scope is labeled **Project
resources**. This does not establish runtime residency, spawning or visibility.

Focused validation: nine SDK inventory cases plus two HTTP cases pass; Node
checks cover authored membership, donor/scene/coordinate coherence, source
substitution rejection and scene filtering. Actual private browser checks verify
indexed NPC membership, exact SDK fields, selection and the 540px layout, with no
page errors or project/document/history/file changes. Evidence is under
`local-output/sdk-20260909/npc-project-assets-20261005/`. No Build, game launch,
install or disc export was needed. Manual gameplay verification remains deferred.

## Authored NPC Asset Details — 2026-10-05

NPC draft cards in active-scene and project scopes now use the SDK-owned
`AssetNpcDraft` descriptor. It presents the authored identity, name, project scene,
retail donor binding and authored X/Z coordinates with Project/Authored state
badges. Imported actor cards retain their existing descriptor. The separate
`authored_asset_inspectors` mapping preserves imported asset contracts.

The adapter rejects inconsistent draft identities, scene/name/donor records and
invalid native-grid coordinates before mounting the descriptor. Its only registered
action, **Select NPC draft**, uses existing scene navigation and opens the draft
Inspector. This exposes current SDK authored records; it does not add imported
Asset Database memberships or establish runtime spawning/visibility.

Validation: twelve Python Inspector schema cases and the expanded Node asset
Inspector checks pass. Actual private browser checks match every SDK property in
both scopes, select the correct NPC Inspector and pass at 540px with no page errors.
Project document, Undo/Redo and all project file bytes remain unchanged. Evidence:
`local-output/sdk-20260909/npc-draft-asset-inspector-20261005/proof.json` and
`asset-540.png`. No Build, game launch, install or disc export was performed;
manual gameplay verification remains deferred.

## SDK-owned NPC draft Inspector display — 2026-10-05

NPC drafts now use SDK Inspector contracts for identity, authored X/Z placement
and preview snapshot metadata. `NpcDraftIdentity`, `NpcDraftTransform` and
`NpcDraftPreview` own labels, paths, units, state badges, source details and notes.
A dedicated read-only adapter renders them through the shared component renderer;
existing name/donor/position, frame/delete, repetition and group controls retain
their specialized command adapters.

Authored placement stays separate from source-preview X/Z, unresolved placement
Y and derived terrain elevation. Preview model/pose/geometry metadata retain SDK
meaning; missing fields do not fall back to authored values or donor data. Pending
refresh is explicit. During a detached viewport proposal, the Inspector identifies
its retained source snapshot and does not relabel source coordinates as proposed.
Retail view has no NPC draft preview, so those values remain unavailable; returning
to Authored restores the qualified snapshot. Donor retail metadata is source detail,
not the new draft's retail placement or an established runtime identity.

Validation: 11 Python Inspector schema cases, new NPC/previous environment Node
render checks and both editor module syntax checks pass. Actual private browser
matches every schema-defined property to SDK source values, verifies unresolved Y
versus terrain sample, retained authoring controls, controlled pending/proposal
labels, Retail missing-preview behavior and Authored return. The540px Inspector
is inspected with no page errors. Project document, history and every saved file
remain unchanged; no Command/Save/Build/Run, game, install or disc export occurs.
Proof: `local-output/sdk-20260909/npc-draft-inspector-schema-20261005/proof.json`.
This adds display contracts; authored commands, package serialization and runtime
capabilities are unchanged. See [Inspector schema](legaia-inspector-schema.md).

## NPC draft group alignment/distribution and normal package — 2026-10-05

**Move NPC draft group → Placement operation** now aligns X/Z to a selected
anchor or distributes along either axis. Alignment preserves the other axis.
Distribution orders by Current coordinate then stable ID, retains endpoints and
rounds intermediate positions to the nearest64-unit placement, with half steps
rounding upward. Groups need at least one native interval per gap; insufficient
span rejects. Already-correct layouts are inspectable no-ops with Apply disabled.

SDK review and `layout_actor_drafts` use the existing atomic batch Undo/persistence
workflow and a distinct `draft-group-layout.v1` algorithm. Offset request keys and
behavior remain. Selection, operation and anchor changes withdraw accepted review.
The editor independently recomputes every native proposal and changed count;
detached scene qualification retains the group tool's donor/model/source guards.
No spawn, collision or script semantics are introduced.

Validation: 10 focused Python group/repetition cases, expanded Node offset/layout
contracts and module syntax pass. Actual private HTTP/browser verifies rounded
spacing/endpoints, selected-anchor alignment, unchanged other axes, operation-change
withdrawal, detached scene, atomic distribution Undo/Redo, both applied layouts,
Save/reload and independent disk reopen. The540px layout is inspected; no page
errors. Private normal Build review accepts all six drafts, saved package verification
matches current inputs, and decoded final MAN equals preparation byte-for-byte.
All six appended coordinates match authored state. Normal package uses the existing
format7 compressed NPC growth relocation route; project document/history and
preexisting files stay unchanged during Build. Package SHA256:
`d6dc02e375d60518fd862fa22bdf32ff017ae5e9c4e92d58f31193290dcd3ad9`.
Evidence: `local-output/sdk-20260909/npc-draft-layout-20261005/{proof,normal-build-proof}.json`.
No game, install or full-disc export; gameplay acceptance remains deferred.
See [group layouts](legaia-npc-draft-groups.md#alignment-and-distribution).

## Reviewed NPC draft group movement — 2026-10-05

Selected authored NPC drafts now expose **Move NPC draft group...**. Search by
name/stable ID, select visible matches or individual members, then review a shared
X/Z offset on the existing retail64-unit grid. At least two active-scene drafts
are required. Every result must fit64..16384; zero delta remains inspectable but
has no Apply or history change. Names, donor bindings, imported actors/scenery
and unselected drafts remain unchanged.

The SDK owns review/validation and atomic `offset_actor_drafts` command dispatch.
A full project/source snapshot binds `draft-group-offset.v1`; Apply revalidates all
members before one existing batch Undo entry. Detached Proposed/Current scene
inspection qualifies exact selected positions, source elevation/display/model
transforms, donor metadata/assets and unchanged unselected entities. Save/Open
preserves the group positions. No retail structures or spawn semantics are added.
See [NPC draft groups](legaia-npc-draft-groups.md).

Validation: eight focused Python group/repetition cases, new Node report/scene
qualification checks, existing repetition Node checks and module syntax pass.
Private actual HTTP/browser checks pass subset movement, search/visible selection,
read-only review/scene comparison, zero-delta and bounds rejection, Apply/Undo/
Redo/Save/reload and independent disk reopen. The first selection fixture matched
all shared-prefix names; corrected ID search passed. Narrow actions/table layout
was repaired and a read-only browser recheck preserves all project/history/files.
The final540px screenshot is inspected, with no page errors. Native prepared PROT
reopen matches all six draft positions, including only the two selected movements;
MAN/PROT hashes match the preparation audit and project files remain unchanged.
A copied native helper initially pointed at the prior grid fixture; corrected
fixture preparation/readback passes. No normal Build, game, install or disc export.
Evidence: `local-output/sdk-20260909/npc-draft-group-20261005/{proof,native-proof}.json`.

## Rectangular NPC draft repetition — 2026-10-05

**Repeat draft → Rectangular grid** now reviews independent donor-bound copies
across columns, then rows. The original occupies cell zero; copy count excludes
it. X step spaces columns and Z step spaces rows, using the existing 64-unit
placement grid and bounds. Columns must be 2..copy-count-plus-one; zero column
spacing rejects, and rows require nonzero Z spacing when another row is used.
Negative spacing is supported when every resulting position remains valid.

Grid review uses a distinct algorithm/key while existing line requests, positions
and deterministic identities remain unchanged. Pattern/column/spacing edits clear
the accepted report. Detached scene inspection uses the exact reviewed grid;
Apply revalidates source/draft state and creates one existing batch Undo entry.
Copies stay individually editable and persist through Save/Open. No new retail
structure, serializer, runtime spawning or gameplay capability is inferred.

Validation: 12 focused Python repetition/review cases, expanded Node coordinate
checks and module syntax pass. Real private browser checks cover grid/line review,
negative row spacing, invalid zero row spacing, pattern-change withdrawal, exact
proposal scene coordinates, atomic Apply/Undo/Redo/Save/reload and independent
disk reopen. The 540px controls are inspected, with no page errors. Native prepared
PROT readback matches all six appended positions (original plus five copies),
59 partition-one records and one growth sector; input project files stay unchanged
during native preparation/readback. The first fixtures crossed retail bounds and
the first readback used a logical alias offset; corrected checks pass. No normal
Build, game launch, install or full-disc export occurs. Evidence:
`local-output/sdk-20260909/npc-grid-repetition-20261005/{proof,native-proof}.json`.

## Current NPC Build scope in repetition/review — 2026-10-05

NPC repetition and experimental archive review now share the normal builder's
current scope note: qualified compressed candidates use fixed spans or capacity-
growth relocation, and qualified raw streaming candidates use relocation. Source,
allocation, composition and actor-pool gates remain. Repetition now displays all
bounded SDK notes below its review table instead of silently omitting them;
malformed/unbounded notes reject the report and keep Apply unavailable.

Experimental review explicitly reports `normal_build_assessment: not_assessed_here`.
Its legacy `normal_build_ready:false` remains and grants no readiness claim; use
**Review Build** for normal-package readiness of the complete authored project.
The repetition guide is corrected and the 2026-10-01 raw-MAN fixed-span restrictions
are labeled historical, preserving their original evidence. No new serializer,
command, review-key algorithm or gameplay capability is introduced.

Validation: 10 focused Python repetition/review/HTTP cases, both existing Node
contracts and module syntax pass. The actual SDK response matches visible browser
scope notes; malformed notes withdraw Apply. The 540px dialog is inspected, close
cleans up, and project document/history/files remain unchanged. No Build or game
runs during this check. Evidence:
`local-output/sdk-20260909/npc-build-scope-notes-20261005/proof.json`.

## General Build history fresh-input and receipt qualification — 2026-10-05

General **Build history** now qualifies fresh `/api/state` after list, verification
and comparison responses, before displaying their results. A changed server
project path or authored-input key rejects even when the editor's cached state
has not refreshed. Closed dialogs abort and reject late responses.

Explicit package verification also binds its returned receipt to the selected
history entry: archive/source-disc hashes, build kind and report count must agree,
and `matches_current_inputs` must equal the receipt/input-key comparison. General
and asset-specific Build inspection share this validator. A mismatch withdraws
report rows instead of presenting stale current-input or package claims. List summaries
identify the input match when listed, so an old snapshot is not a fresh claim. Metadata
input match, package integrity, unchecked source disc and unverified gameplay
remain distinct; no native Build or authoring path changes.

Validation: expanded general/asset Build-history Node contracts and module
syntax pass. Actual browser verifies the existing private saved package, then
controlled fresh-server input mismatch withdraws verification rows and rejects
listing before rendering entries. A changed returned archive receipt hash rejects
against its selected history entry despite current server inputs. Close cleanup,
540px failure layout and zero page errors pass; project document, history and all
files stay unchanged. No new Build, authoring, Save, Run, installation or full-disc
export occurs. Evidence:
`local-output/sdk-20260909/build-history-freshness-20261005/proof.json`.
Runtime/source-disc acceptance stays deferred, work remains solo and the full SDK
goal remains active.

## Asset Database → verified saved Build records — 2026-10-05

**Asset Details → Inspect saved Build records...** connects a selected stable asset
ID to saved normal-Build completion receipts. Choose a completed Build in explicit
identity order and verify its receipt, audit, manifest, payload files and ZIP before
viewing matching emitted audit records. The SDK's existing Build-history service
owns file verification; this adds no alternative Build or authoring path.

Exact audit asset-ID matches and optional exact owner-ID matches are labeled
separately. All matching rows remain available in 128-row pages, with full audit
details including native model coordinate ledgers. Current-input match is separate
from artifact integrity. Receipt hashes/kind/count and current input identity are
qualified against the selected history entry; fresh server state is checked before
presenting verification. Source, asset membership, input/Build selection changes
withdraw results. Pending controls and detached paging callbacks are guarded.

Absence from an audit does not prove unused/deleted/native-absent content. A shared
ID does not prove the selected source membership was emitted. Source-disc integrity
and gameplay remain unverified; templates are project metadata and retain their
own workflow. The dialog issues no authoring, project Save, Build or Run operation.

Validation: six focused Python Build-history integrity cases, new asset-record
matching and existing Build-history Node contracts, plus module syntax pass.
A private normal Town01 Build completes and verifies through the SDK service;
actual Asset Details → saved Build → verification retains the full 130-word model
coordinate ledger. Controlled detached DTO checks cover all 301 rows across pages,
stale server-input withdrawal and inert removed page callbacks. The 540px layout
is inspected. Browser inspection leaves the project document, history and every
file unchanged, with no page errors or authoring/Save/Build/Run requests. The first
harness attempt read hidden detail text incorrectly; corrected readback passes.
Private package SHA256:
`22df98883fdf40a9bbb33c02662de555ab7de4cf2523742bf89b9377c130dce9`.
Evidence: `local-output/sdk-20260909/asset-build-records-20261005/proof.json`.
No game, installation or full-disc export ran. Full SDK/runtime acceptance remains
unproven and the goal active; work stays solo.

## Shared scenery Inspector section controls — 2026-10-05

Scenery now uses the same session-only component collapse and keyboard navigation
as actors. SDK placement, Retail/Current transforms and evidence, plus existing
shared/individual transform and shared-record sections, have accessible toggle
headers. Collapse/Expand visible components is available without an actor filter.
Left/Right collapse/expand; Up/Down and Home/End move between visible headers.

Layout choices are retained across scenery in the same project session. A
same-instance rerender restores header focus; changing selection does not carry
that focus. Collapsing preserves the existing form nodes, values and handlers
and submits no command. Replacing an Inspector still follows existing form
rerender behavior. Source/representation/selection guards and DOM ownership make
removed section/tool callbacks inert, including same-instance rerenders. Actor
filter placement and layout controls retain their established behavior.

Validation: three focused Node Inspector checks and module syntax pass. Actual
private Town01 browser verifies all seven scenery sections, header keyboard
navigation, collapse/expand all, unchanged unsubmitted input values, same-instance
layout/focus restoration, detached callback rejection, layout across scenery,
actor filter/layout regression and controller project isolation. The 540px
Inspector screenshot is inspected and every header fits. Project document,
Undo/Redo and files remain unchanged; no page errors or authoring/Save/Build/Run
requests. Evidence:
`local-output/sdk-20260909/scenery-inspector-sections-20261005/proof.json`.
No gameplay, installation or full-disc export ran; the full SDK goal remains active
and deferred gameplay gates are unchanged. Work remains solo.

## SDK-driven scenery Inspector — 2026-10-05

The scenery Inspector now renders **Environment placement**, **Retail transform**,
**Current preview transform** and **Source and bindings** from SDK component
metadata. Identity/model/pose, six retail and six preview coordinate/angle values,
MAP hash and source indices retain their SDK paths and property-state labels.
Source records and decoder evidence remain separately expandable. Missing values
stay unknown; stale preview snapshots show an explicit refresh-pending warning.

This replaces the hard-coded scenery identity/transform/source display and makes
Retail versus Current placement visible per axis. Frame and the existing shared/
individual source-qualified transform adapters remain. The new descriptors are
strictly read only and grant no commands or runtime writes. Preview values follow
the displayed Retail/Authored representation; they are not sampled gameplay state.

Validation: 12 focused Python inspector-schema/environment-project cases, the
scenery adapter Node check and module syntax pass. Private Town01 browser checks
all four real SDK sections, every displayed property, separate Retail/Current
values, Current GPU translation, retained source controls and Frame, the full
panel's pending-refresh warning and Retail/Authored reload with reselection.
The 540px Inspector-tab screenshot is inspected. Project document, Undo/Redo and
all project files stay unchanged; no page errors or authoring/Save/Build/Run
requests. Earlier harness attempts are retained (heading whitespace, narrow-tab
visibility, quoting and representation-selection assumptions); the final fresh
fixture passes. Evidence:
`local-output/sdk-20260909/environment-inspector-schema-20261005/proof.json`.
No gameplay, installation or full-disc export ran. The SDK goal remains active;
manual runtime placement/collision acceptance stays deferred and work remains solo.

## Save selected Asset Database evidence — 2026-10-05

**Asset Details → Save asset evidence…** downloads the complete selected catalog
record as `legaia.asset-record-evidence.v1` JSON. Imported source metadata, authored
settings and every retained project source membership preserve their original
fields; the chosen membership remains explicit. Export is metadata evidence, not
an editable interchange file, native payload or Build package.

The button qualifies bounded JSON metadata, uses a 32 MiB UTF-8 budget and checks
both the current editor record/context and fresh `/api/state` inputs before
saving. Changed sources, membership, project inputs or closed details reject.
Pending and busy clicks cannot start a second export. No command, history, Save,
Build or game operation is issued. Source keys do not establish native payload
integrity or runtime use; gameplay remains unverified.

Validation: focused export and existing asset-inspector Node checks, nine Python
inspector-schema cases and module syntax pass. Private Town01 browser downloads
from active and project scopes match the complete selected source/authored record;
project membership is retained, the 540px screenshot is inspected and a forged
fresh-server source key blocks export. Project document, Undo/Redo and every
project file remain unchanged; no page errors or authoring/Save/Build/Run requests.
The first browser attempt exposed a missing static module route, fixed before
passing the fresh-fixture run. Evidence:
`local-output/sdk-20260909/asset-record-evidence-20261005/proof.json`.
Gameplay, installation and full-disc export remain deferred. Work stays solo;
the full SDK goal remains active.

## Mirror mixed scene placement coordinates — 2026-10-05

**Move scene placement group → Mirror X/Z coordinates about anchor** reflects the
selected coordinate across its value at a selected imported actor/static-decoration
anchor: `proposed_axis = 2 * anchor_axis - Current_axis`. Final actor coordinates round
to 64 units with half steps away from zero; scenery retains integer precision. Off-grid
scenery anchors are supported and stay fixed. The other coordinate stays unchanged;
only changed actor axes become overrides. This reflects positions without mirroring
models, changing facing/object rotation, creating parenting or recomputing collision.

Exact typed `{kind, axis, anchor_entity_id}` requests use a distinct native-mirror
review algorithm binding. Review qualifies selection, source and full native proposals;
Current/Proposed inspection and Return author nothing. Input/source changes withdraw
review. Actor bounds and complete MAP offset/allocation checks reject atomically. Apply
records one Undo step through existing commands; no-ops preserve history and redo.
Shared descriptors, unselected instances, heights and unrelated components remain.

Validation: 28 focused Python layout/group/HTTP cases, expanded mixed-placement Node
checks and module syntax pass, including both axes, off-grid anchor, half rounding,
unchanged-axis metadata, invalid/stale requests, no-op/history, offset overflow and
forged/safe-arithmetic guards. Actual private Town01 browser checks X and Z reflection,
fixed off-grid anchor, Current/Proposed GPU matrices, held height/rotation, withdrawal/
Return and one Apply at 540px. Undo/Redo, Save/Open and normal Build pass with full MAP
directory/ZIP and independent MAN coordinate/opaque-byte readback. Package SHA256:
`41922554d2e88a1b07fcfd9482853c1a924286f1aab763e7e1b2650a6e451b9b`.
Evidence: `local-output/sdk-20260909/mixed-placement-mirror-20261005/proof.json`.
No game, installation or full-disc export ran. Runtime/script-driven placement and
collision acceptance stay deferred; the full SDK goal remains active and work stays solo.

## Rotate mixed placements at native coordinate precision — 2026-10-05

**Move scene placement group → Rotate positions -90°/+90°/180° in X/Z** accepts a
selected imported actor or static-decoration anchor at its native integer position.
Scenery anchors can lie between actor grid points. Signed quarter-turn permutations
rotate Current distances around that fixed anchor; final actor positions round to
64-unit coordinates with half steps away from zero, while scenery retains integer
precision. The anchor stays fixed. Rounding can bring placements together; use the
Retail/Current/Proposed review. This supersedes initial grid-only position rotation.

The SDK and browser qualify exact operation/selection/source and full native proposals.
Rotation has a distinct `native-coordinate-rotation.v1` review-key binding; old algorithm
tokens reject. Actor source-coordinate limits, signed scenery offsets, full MAP allocation,
atomic Apply/Undo and Save/Open remain. Heights, facing, object rotations, unselected
placements, shared edits and collision resources stay unchanged. Rotation changes
positions, not geometry, parenting or runtime placement semantics.

Validation: 25 focused Python layout/group/HTTP cases, expanded mixed-placement Node
checks and module syntax pass. Cover all signed quarter turns, integer/off-grid anchors,
positive half rounding, actor bounds, scenery overflow, no-op/history, source withdrawal,
old-token rejection and forged/safe-arithmetic guards. Actual private Town01 browser
checks all three turns about an off-grid decoration, Current/Proposed GPU matrices,
height/rotation preservation, operation withdrawal/Return and one Apply at 540px.
Undo/Redo, Save/Open and normal Build pass with full MAP directory/ZIP and independent
MAN coordinate/opaque-byte readback. Package SHA256:
`e36c50f5dedac90d3a3625f19f1094526eeb3a45738513854884c152b10b11e1`.
Evidence: `local-output/sdk-20260909/mixed-placement-native-rotation-20261005/proof.json`.
No game, installation or full-disc export ran; gameplay remains deferred and the full
SDK goal stays active. Implementation remains solo.

## Saved scene visibility and grid — 2026-10-05

**Saved scene views** now retain manually hidden imported actors/static decorations/
ground, an optional isolated instance and the grid switch, alongside camera,
representation and layers. **Recall scene view** restores the focused inspection;
**Restore scene** still preserves manually hidden instances. Model filters, proposal
previews, runtime observations and new NPC draft visibility are outside this metadata.

Visibility uses canonically sorted source-bound IDs (up to 32768 hidden instances)
and a MAP hash when environment instances are retained. Save/replace verifies the
source MAP and static cell membership. Portable Open validates typed metadata without
requiring a disc; recall checks current preview membership, isolated renderability and
MAP identity after scene/representation loading. Active group/collision proposals
withdraw the tool. Old views without visibility/grid keep their former recall semantics.
These fields use existing command/history/persistence and change no game components,
imported facts, normal-Build inputs or scene-preview source keys.

Validation: nine focused Python view cases, expanded scene-view and camera Node suites,
and both editor-module syntax checks pass. Cover typed/canonical metadata, native static
membership, MAP mismatch/atomic rejection, source drift, legacy projects, Undo/Redo and
Save/Open. Actual private Town01 browser saves a hidden actor and isolated decoration,
recalls camera/grid/isolation, restores manual hiding, checks metadata Undo/Redo and
Save/Open, and retains isolation across Retail-to-Authored preview reload at 540px.
Screenshot inspected; no page errors. Imported/authored game data and Build/preview
keys remain unchanged. Evidence:
`local-output/sdk-20260909/saved-scene-visibility-20261005/proof.json`.
No package, game, installation or full-disc export ran. Gameplay verification remains
deferred; the full SDK goal stays active and implementation remains solo.

## Save the complete pre-Build review — 2026-10-05

**Review Build → Save full Build review…** downloads the complete accepted v1/v2
review as JSON, including source identity, scope, blockers, native/other change
records, relocation and serialization provenance, limitations and unverified runtime
status. It preserves rows beyond the 256-row display limit and all coordinate pages.
Blocked reviews, including an absent serialization assessment, can be saved without
claiming readiness. This is review metadata, not a package or an imported authoring file.

The download revalidates the accepted response and current authored-input identity,
uses a bounded source-key filename and a 32 MiB UTF-8 budget. Pending, busy, stale and
closed contexts cannot export. Download and Build/Close actions wrap at narrow widths.
No new SDK command, authored state, history entry or package output is introduced.

Validation: expanded ordinary Build-review Node suite, NPC review suite and module
syntax pass, covering 301 top-level rows, native/other ledgers, blocked/null assessment,
v2 coverage, stale/no-output claims and multibyte overflow. Actual private Town01
browser downloads at desktop and 540px equal the full accepted retail response,
including all 130 native records. Pending disable, mounted UI stale-source rejection,
close disposal, narrow action bounds and unchanged document/history/all fixture files
pass with no page errors. The 540px screenshot is inspected.
Evidence: `local-output/sdk-20260909/build-review-download-20261005/proof.json`.
No game, installation, package or full-disc export ran; gameplay acceptance remains
deferred and the full SDK goal stays active.

## Review native model coordinate changes before Build — 2026-10-05

**Review Build → Native coordinate audit** exposes qualified vertex/normal records:
object and vector index, axis, model byte offset, and signed before/after values.
Details render lazily with 128 coordinates per page. Primitive, material, removal
and allocation records remain separate records in the full audit; they are not
interpreted as coordinates. The existing first-256 top-level change-row limit stays.
Reports without a native ledger do not acquire invented coordinate changes.

Existing-layout shape/content and face-removal ledgers now survive model-pack
relocation into both Build audit and report. Topology-addition bindings retain their
existing relocation evidence without a fabricated coordinate ledger. The browser
validates hashes, signed values, indices and unique aligned offsets before exposing
review; paging is guarded by the current authored-input identity. Recorded offsets
are model-layout offsets, not an assertion of a retail file address.

Validation: nine focused Python Build-review/growth/normal-Build cases, both ordinary
and NPC Build-review Node suites, and module syntax pass. Synthetic normal packages
retain independently checked native ledgers and deterministic relocation behavior.
Actual private Town01 review exposes 130 exact native changes over two pages for a
model-pack-content relocation, with correct paging bounds, readable 540px layout,
no browser errors and unchanged project/history/all fixture files. Independent native
word and source/candidate hash readback passes. Review creates no package.
Evidence: `local-output/sdk-20260909/build-review-model-coordinates-20261005/proof.json`.
No game, installation or full-disc export ran. Gameplay acceptance remains deferred;
the full SDK goal stays active.

## Distribute selected model vertices along a source axis — 2026-10-05

**Move model geometry → Selected vertex group → Distribute group X/Y/Z** stages even
spacing between the selected Current axis endpoints. Select 2–4096 unique object-local
rows. Ordering uses axis coordinate then native vertex index; integer spacing rounds
half steps toward the positive axis. Endpoints and other coordinates stay fixed.
Two rows or an already evenly spaced group produce no draft change. Normal words,
primitive topology, ownership and unselected rows remain unchanged; no normal or
collision recomputation is implied.

Distribution is a distinct SDK operation with exact `{indices, axis}` values and an
inspected Current model hash. The local draft locks conflicting selection/movement,
supports Discard and Retail/Current/Draft comparison, and reaches single/all-instance
Current/Proposed scene inspection with Return/Restore. The parent workspace qualifies
its full geometry and exact operation values and labels the distribution axis. Apply
uses the normal model override/history path; Save/Open and Build consume the result.

Validation: six focused Python distribution/alignment cases, expanded vertex-movement
Node checks and both changed editor-module syntax checks pass. Coverage includes signed
extremes, stable coordinate/index ties, stale/invalid requests, appended vector ownership,
immutable source, no-op and forged scene-review replies. Actual private Town01 browser
checks draft locks, no-op/Discard, Current/Draft, single/all-instance scene comparison,
Return/Restore, 540px Apply and Undo/Redo without page errors. Save/Open and normal Build
pass; complete decoded carrier readback in the package directory and ZIP preserves all
neighbors. This retail edit changes only model byte1524. Package SHA256:
`59be7c6edc144766f4d51844f08d7004e8085df59e557a4b1ab38a44807d1ca8`.
Evidence: `local-output/sdk-20260909/vertex-distribution-20261005/proof.json`.
No game, installation or full-disc export ran. Gameplay appearance remains deferred;
the full SDK goal stays active.

## Scale mixed placements at native coordinate precision — 2026-10-05

**Move scene placement group → Scale spacing at native precision** scales selected
imported actor and static-decoration X/Z distances around a selected placement anchor.
Enter an integer percentage from 1 through 1000. Current coordinates must be integers;
decorations and decoration anchors can lie between actor grid points. Final actor
coordinates round to their native 64-unit spacing, decorations to native integer units,
with half steps away from zero. The anchor stays fixed and 100 percent is a no-op.
Rounding can bring placements together; review Retail/Current/Proposed before applying.
This replaces the initial grid-only spacing scale; scenery no longer snaps to actor
precision and rounding applies to final coordinates rather than relative distances.

Current/Proposed scene inspection changes no authored data. Changed inputs withdraw the
review. Apply rechecks project/source, selection, exact operation and full proposal,
then records one atomic Undo step. The scale arithmetic has a distinct review-key
algorithm binding. Actor coordinate bounds and scenery signed-offset limits remain.
Height, facing, object rotations, shared descriptor edits and unselected placements
stay unchanged. Scaling changes spacing, not geometry or collision resources.

Validation: 18 focused Python layout/group cases, expanded Node qualification and module
syntax checks pass, covering native signed half rounding, off-grid anchor, 100-percent
identity, actor bounds, scenery offset overflow and atomic rejection. Actual private
Town01 browser checks exercise 50/100/175 percent, fixed off-grid decoration anchor,
Current/Proposed GPU matrices, withdrawal/Return, one Apply and all action bounds at
540px. Undo/Redo, Save/Open and normal Build pass; independent MAN actor decoding and
complete MAP directory/ZIP readback preserve opaque/unselected bytes. Package SHA256:
`2178e97c3548ff3c392d371f8e7869038c50408cdb9f765b1b31418663b2d373`.
Evidence: `local-output/sdk-20260909/mixed-placement-native-scale-20261005/proof.json`.
No game, installation or full-disc export ran; gameplay appearance remains deferred.
The full SDK goal stays active.

## Save complete asset-reference reports — 2026-10-05

Asset references now offers **Save full reference report** in Active and Project scopes.
The downloaded JSON preserves every accepted incoming/outgoing relationship, source
binding, node, coverage limit and diagnostic; display filters never trim the snapshot.
Export rechecks the exact root asset, source key and scope, limits formatted UTF-8 JSON
to 32 MiB and uses a bounded safe filename. Pending discovery, a busy editor or changed
source context cannot start an export. Closing disposes the reference dialog as before.

The snapshot records known references, not runtime residency, execution or gameplay
reachability. It does not edit authored data or replace a live source refresh; there is
no report import command. Focused Node tests cover complete Active/Project readback,
identity/source/scope rejection, immutable inputs, filenames and the byte budget.
Private retail browser checks cover actual downloads in both scopes, pending disable,
zero-match filters retaining the full report, decoder readback and the reachable 540px
button. Project/scene/selection, document/history and saved files remain unchanged;
no authoring, Save, Build or Run occurs. Evidence:
`local-output/sdk-20260909/asset-reference-download-20261005/proof.json`.
Manual gameplay acceptance remains deferred; the full SDK goal is still active.

## Project asset provenance search across retained memberships — 2026-10-05

Field-specific asset search now covers all retained project membership records. `name:`
includes each variant's recorded name; `scene:` includes its source entry alias;
`provenance:` includes source records, claims, RetailMetadata and explicit scene/import
SHA256/catalog-key bindings. Bare and field searches now consistently find a shared asset
by another retained membership's verified source hash. Confidence/model searches retain
their existing recorded-value behavior. Positive and excluded terms use the same full
record coverage; no confidence, name or source fact is invented.

Search does not choose, merge or activate variants. Details/activation retain one exact
chosen source record with the existing source-context/catalog qualification. Combined
terms match recorded asset metadata across memberships; they do not assert that all terms
came from one binding. Use the membership selector to choose a source. Active records
without project memberships retain their existing field behavior. Search help is updated.

Validation: both expanded asset-search/project-assets Node suites, eight focused Python
project-source cases and both modified editor-module syntax checks pass. A fresh private
three-scene retail browser reproduced the old field-search miss against the prior module,
then found the shared world-map placement using a nonchosen Map01 import/catalog hash.
Exclusion, unchanged chosen Dolk2 variant, real Details membership and 540px search passed
with no page errors. Document/history, scene/selection and all saved files stayed
unchanged; no authoring, Save, Build or Run requests. Screenshot inspected. Two incorrect
Details selectors in the harness were corrected from actual card markup; failed attempts
are preserved. Private proof:
`local-output/sdk-20260909/project-provenance-search-20261005/proof.json`.
No game ran; the full SDK goal remains unfinished and active, with solo work continuing.


## Inspector property-category filtering — 2026-10-05

The actor Inspector now offers **Property category** alongside text search and **Authored
only**. Options come from the SDK property-state labels already rendered in the current
component sections, coalescing multiple authored workflows under Authored. Filtering
shows whole components containing the selected category, preserving their values and
actions. It does not infer unknown values, authorship or live identity. Authored only
continues to use exact SDK authored-component IDs, so an empty declared Authored layer
is not treated as an override. Search, category and authored membership compose.

Category selection is remembered across actor rerenders in the editor session. Reset
filter clears all three controls. A selected category absent from the next entity stays
available and yields no matching components. Collapse/expand and header navigation
continue to operate only on visible components. This modifies display state only;
project data, commands, Undo/Redo, persistence and Build remain unchanged.

Validation: three focused Node suites and filter-module syntax pass. Actual private
retail browser checks compare visible component IDs with declared categories, combine
search/actual authored membership, exercise zero results, two-actor retention, Reset,
asset navigation, 540px layout and collapse/keyboard restoration with no page errors.
Project document/history, final scene/selection and every saved file stayed unchanged;
no authoring, Save, Build or Run requests. Screenshot inspected. The first harness
attempt navigated before selection readiness; explicit ready/identity waits corrected
it, with failed evidence preserved. Private proof:
`local-output/sdk-20260909/inspector-property-category-20261005/proof.json`.
No game ran; manual gameplay stays deferred and full SDK buildout continues solo.


## SDK property-state labels in the Inspector — 2026-10-05

The shared component/asset property renderer now displays SDK-declared property states:
Retail, Authored, Effective, Derived, Reference, Source, Project, Live observed,
Unresolved, Evidence and Editor. A detached `property_states` presentation catalog owns
labels and explanatory notes. Appearance/initial-animation layers and Transform columns
have explicit declared states; precise authored donor/source-workflow states stay intact.
Transform separately shows Retail Y as Unresolved and its Build representation as
Unsupported in a full-width row. Empty/false values, source details and reference labels
remain exact. Property-state labels describe ownership/evidence category; an empty
Authored value is still inherited, and a Live observed category does not confirm a live
sample or actor association. Unknown/malformed state declarations display Unclassified.

This is display metadata, not a command/capability registry. Existing Edit/busy/source
checks, property commands, action eligibility and read-only/live-write boundaries remain.
All existing generic component/asset consumers receive the labels without new special
binary-format knowledge or authored data. Specialized editors retain their own adapters.

Validation: nine focused Python schema tests, both component Inspector/reference Node
suites and module syntax pass. Actual private retail browser checks cover all displayed
labels/notes against SDK declarations, authored X/Y values, separate unsupported height,
model-reference asset navigation, 540px layout and collapse/keyboard restoration without
page errors. Document, Undo/Redo, source scene, selection and every saved file stayed
unchanged; no command, Save, Build or Run requests. Screenshots inspected; initial Y-label
wrapping was corrected and prior attempts preserved. Private evidence:
`local-output/sdk-20260909/inspector-property-states-20261005/proof.json`.
No game ran; no manual gameplay gate is added. Full SDK/live parity remains unfinished
and solo work continues.


## Mixed actor/scenery position rotation — 2026-10-05

The scene placement group workspace now rotates selected imported actors and static
scenery positions by -90, +90 or 180 degrees around a selected actor or decoration.
Both anchor coordinates must lie on the 64-unit actor grid. +90 maps relative
(X,Z) to (-Z,X); -90 maps to (Z,-X); 180 negates both. The anchor remains fixed.
Exact integer arithmetic avoids trigonometric rounding. Every proposed actor position
must satisfy native placement bounds/grid; scenery must satisfy signed MAP offsets
and complete merged descriptor allocation. This changes X/Z positions only: authored
height, actor facing, scenery rotations, shared edits, unselected instances, unrelated
components and collision stay intact. No inferred parenting or terrain height is added.

Review qualifies the exact operation, selected source identities and complete proposal.
Operation/anchor changes withdraw Review. Current/Proposed scene comparison holds height
and rotations; Return retains the review. Layout mode has no shared-offset drag handles.
Explicit Apply recomputes the source-bound candidate and records one atomic Undo/Redo
step across actor Transform and scene Environment owners. Coincident no-ops preserve
history/redo. Save/Open and normal Build use the existing MAN/MAP serializers.

Validation: 13 focused Python cases pass (three new rotation cases plus ten existing
layout/reset/offset checks), the expanded Node suite and editor syntax check pass.
A private retail browser exercised all three turns around a decoration, operation
withdrawal, exact Current/Proposed GPU matrices, Return and one reviewed Apply without
page errors. Pre-Apply saved files/document stayed unchanged. Atomic history, persistence,
unselected actor/scenery preservation, full MAP directory/ZIP readback, independently
parsed MAN actor coordinates/opaque bytes and ZIP integrity passed. Screenshot inspected.
Private evidence: `local-output/sdk-20260909/mixed-placement-rotation-20261005/proof.json`.
Package SHA256: `86a37e8ee0ec8c82f8853ce6e49d6ffc4f02a28da65916122db97334aa4cce7b`.
No game, installation or full-disc export ran. Gameplay remains deferred; the full SDK
goal is unfinished and work continues solo.


## Mixed group Reset X/Z to Retail - 2026-10-05

The mixed placement dialog now offers Reset X/Z to Retail for the selected imported
actors and static decorations. It proposes exact source positions, clears selected
actor X/Z overrides (including redundant overrides already equal to Retail), and prunes
empty actor Transform/component containers. Height, facing and other components remain.
Scenery resets merge per-instance source positions while preserving shared transforms,
Y/rotation and unselected edits; a shared authored transform may require an explicit
selected-cell compensation rather than clearing the shared record for every instance.

The readonly review carries the exact Current authored actor axes to be cleared, qualified
against the editor's source-bound actor components. Native-position change counts and
metadata-only clearing remain separate; the dialog reports both. Existing operation/source
qualification, scene Current/Proposed comparison, Return, no-op, atomic Apply, Undo/Redo,
Save/Open and normal Build remain intact. Reset can recover off-grid integer actor X/Z
because it validates the Retail candidate rather than requiring the invalid Current value
to encode. This does not reset height, facing, other actor properties, entire Environment
state or runtime gameplay. See [reset](legaia-scene-placement-groups.md#reset-xz-to-retail).

Verification: two new synthetic reset cases and eight neighboring mixed-group/layout
cases passed, plus Node reset/arithmetic/witness guards and JS syntax. The actual private
retail browser reviewed three exact source placements, qualified authored-axis clearing,
compared Proposed/Current GPU matrices with height/rotation held, returned and applied
one command. One history step, unchanged files before Apply, Undo/Redo and Save/Open
passed. Unselected actor and scenery edits were preserved. Normal Build directory/ZIP
full MAP readback, independently decoded MAN source actor positions and opaque-byte
preservation, ZIP integrity and SHA passed. Evidence: ignored
`local-output/sdk-20260909/mixed-placement-reset-20261005/proof.json`, audit and screenshots.
The first private fixture used the public two-decoration minimum for its single unselected
cell check; it was corrected to the existing internal minimum-one scope. No game launched
or installed. Gameplay checks remain deferred; the full SDK goal stays active and solo.

## Mixed actor/scenery alignment and distribution - 2026-10-05

The mixed scene placement dialog now supports aligning source X/Z to a selected actor
or static-decoration anchor and distributing a mixed group along either axis. Groups
retain 2..128 imported actors/decorations with at least one of each. Alignment requires
an anchor on the 64-unit actor grid; distribution requires grid-aligned selected coordinates,
preserves endpoints, uses nearest grid spacing with upward half ties, and orders equal
positions by stable ID. Off-grid inputs reject explicitly rather than silently snapping.

The existing complete actor/MAP qualification and merge paths validate every candidate
before publication, retaining unrelated components, axes, shared transforms and instance
edits. Review is readonly and source-qualified. Retail/Current/Proposed tables, scene
comparison and Return retain the reviewed operation. Changing mode/anchor withdraws it.
Layout inspection holds preview height and rotations; shared-offset drag handles are
restricted to offset mode. One Apply writes actor Transform and Environment changes as
one history step, with no-op suppression, Undo/Redo, Save/Open and normal Build. Runtime
height, collision, activation and gameplay suitability remain unverified. See
[mixed layouts](legaia-scene-placement-groups.md#alignment-and-distribution).

Verification: two focused synthetic layout checks and six existing mixed-offset checks
passed, along with Node source/arithmetic/review guards and two JS syntax checks. Actual
private-retail browser evidence covers distribution preview, decoration-anchor alignment,
mode withdrawal, exact Proposed/Current GPU matrices, retained height/rotation, Return
and one Apply. Document/files stayed unchanged before Apply; one history step, Undo/Redo
and Save/Open passed. Normal Build directory/ZIP full MAP readback, independent MAN actor
coordinate decoding with opaque-byte preservation, package SHA and ZIP integrity passed.
The initial browser harness matched a nested summary as well as Scene tools; its selector
was corrected and the failed attempt preserved. Evidence: ignored
`local-output/sdk-20260909/mixed-placement-layout-20261005/proof.json` and screenshots.
No game was launched or installed. Gameplay checks remain deferred; the full SDK goal
is active and incomplete, with solo implementation continuing.

## Retained animation assignment-user navigation - 2026-10-05

Retained animation assets now list their authored initial-assignment users by stable
actor identity. Select assigned actor navigates through the existing selection service,
frames the actor and synchronizes Hierarchy/Inspector. Capture actor navigation stays
separate. Unassigned and retired clips show an explicit empty state. This is authored
initial-selection evidence, not script-driven residency or observed runtime playback.

The list qualifies every registered user against the current scene's exact retained
record/hash/model component and effective initial-animation identity. Missing, duplicate,
extra or changed users reject navigation. Current project/scene/source, busy and pending
preview guards remain active. Pending Preview locks the selector; closing aborts the
request. The Inspector wraps its action row and bounds its width/scroll area so all
actions remain reachable at desktop and 540px widths. No authoring command or serializer
is introduced. See
[assignment users](legaia-retained-animation-assets.md#navigate-to-assigned-actors).

Verification: the Node metadata/action workflow and two focused Python catalog checks
passed, along with JS syntax. The actual private-retail browser exercised a clip with
two users, distinct capture/target actor navigation, empty active/retired states,
Hierarchy/Inspector synchronization, 540px action reachability and pending-preview
close/locks without page errors.
Document, history, mode, active scene and every saved file remained unchanged; there were
no authoring, Save, Build or game requests. Evidence: ignored
`local-output/sdk-20260909/retained-assignment-users-20261005/proof.json` and `users.png`.
The first browser attempt exposed the overflowing action row; it was fixed and the failed
attempt preserved. Gameplay acceptance remains deferred; the full SDK goal stays active
and solo.

## Selected model vertex group rotation - 2026-10-05

The movement workspace now stages -90, +90 and 180 degree turns of 1..4096 selected
object-local vertices about source X/Y/Z. Positive source Y points down. Pivot choices
are object-local origin or the selected bounds center. Exact doubled pivot coordinates
and signed permutations avoid trigonometric drift; final signed16 words round to nearest,
with half ties away from zero. Overflow rejects the entire candidate. Stored normals,
unselected rows, padding, packet topology and allocation ownership remain unchanged.
This edits geometry only; it does not reconstruct lighting normals or actor transforms.

Draft transforms lock selection, offsets, picking and history. Discard restores Current;
Retail/Current/Draft and exact source-qualified placed-scene Current/Proposed comparisons
retain the draft through Return/Restore, including all instances. Apply creates one
normal model replacement history step. Unchanged native words produce no command.
Undo/Redo, Save/Open and the normal Build serializer reuse the existing workflow.
See [group rotation](legaia-model-vertex-movement.md#selected-group-rotation).

Verification: four focused synthetic Python rotation checks (including HTTP and allocated
rows), six existing scaling/alignment checks, Node geometry/review checks and two JS syntax
checks passed. A private actual-retail browser exercise verified no-op, staging, Discard,
locks, comparison, Return/Restore, all-instance inspection, one Apply and Undo/Redo; native
Save/Open and independent Build directory/ZIP full-section readback also passed. Only
selected XYZ bytes changed. Evidence: ignored
`local-output/sdk-20260909/vertex-rotation-20261005/` (`proof.json`, screenshots and audit).
No game was launched or installed. Gameplay appearance and lighting remain deferred;
the full SDK goal is still active and incomplete.

## Selected model vertex group scaling - 2026-10-05

The model movement workspace now stages positive uniform scaling of 1..4096 selected
object-local vertices at an integer percent1..1000. Pivot choices are object-local
origin or the selected group's bounds center. The center retains exact half-unit
coordinates; both browser and native writer round final words to nearest signed16,
with ties away from zero. Overflow rejects the candidate atomically. Unselected rows,
stored normals, topology and native ownership remain unchanged; normals are not rebuilt.

The shared staged-transform state locks selection/offsets/picking/history while a scale
is pending. Discard restores Current. Retail/Current/Draft and qualified placed-scene
Current/Proposed comparison retain the draft through Return/Restore, including all
instances. Exact operation/percent/pivot/selection/source witnesses qualify scene Review.
Apply routes through the existing source-bound model replacement command, project
history and normal Build serializer. A 100% or otherwise unchanged native result creates
no history entry. Allocated selected rows retain their ownership and count. Actor
placement and supported pose are separate. Gameplay appearance remains deferred.
See [group scaling](legaia-model-vertex-movement.md#selected-group-scaling).

Verification: 6 focused synthetic Python checks, the Node geometry workflow checks
and 2 JavaScript syntax checks passed. The actual headless retail editor exercised
100% no-op, Stage/Discard, draft locks, Retail/Current/Draft, exact placed-scene Review,
Return/Restore and all-instance inspection, then one Apply, source refresh, Undo/Redo
and Save/Open. Before Apply, document and authored files remained unchanged. Normal
private Build passed independent directory/ZIP decompression to the complete expected
scene section. Only nine bytes inside the selected XYZ words changed; unselected rows,
opaque padding, normals and packets were byte-identical. Package SHA/ZIP integrity
matched. Scene screenshot inspected. The initial browser attempt found a missing
root scene label/qualification path; it was fixed and the failed attempt preserved.
No game launched or installed. Evidence:
`local-output/sdk-20260909/vertex-scaling-20261005/proof.json`.

## Assign retained assets to the selected actor - 2026-10-05

An active retained animation asset now offers Assign to selected actor in Edit mode
with the authoring/assignment capabilities. The exact inspected clip opens a dedicated
initial-assignment view with the selected imported actor ID shown explicitly. Capture
actor and target actor remain separate identities. The fresh library row must match
the inspected asset before actions enable. Target selection changes invalidate this
view through the existing actor-owned lifetime; project/scene/mode/source guards remain.

Review uses the existing source-qualified native assignment service to verify captured
model/channel compatibility and current selector resolution. Unsupported retargeting
reports a blocker without mutating an actor. Preview shows the reviewed target initial
pose and returns to Review. Apply writes one atomic ActorAllocatedAnimation override,
preserving the retained ledger/capture and other actors. The catalog refreshes assignment
references after Apply. This view exposes neither lifecycle changes nor assignment Clear;
use the existing actor Inspector for Clear. Retired assets cannot start assignment.
Save/Open, Undo/Redo and normal private Build remain the existing workflow. No runtime
write or gameplay suitability is inferred. See
[asset-to-actor assignment](legaia-retained-animation-assets.md#assign-to-the-selected-actor).

Verification: 4 retail-enabled Python tests, 3 Node workflow checks and 3 JavaScript
syntax checks passed. The actual headless editor hid retired assignment, rejected an
incompatible model, then reviewed/previewed/applied the captured actor-0011 clip to
selected actor0012 through one exact command. The target pose screenshot was inspected;
asset assignment metadata refreshed. Imports, ledger/capture hashes and capture actor
overrides were unchanged. Undo/Redo and Save/Open passed. A second readonly browser
check changed target selection and verified disposal with no command or document,
history or file changes. Normal private Build passed native bank/initial-header/
relocation readback plus ZIP/SHA checks. No game launched or installed. Evidence:
`local-output/sdk-20260909/retained-asset-assignment-20261005/proof.json`.

## Retained asset retirement and restoration - 2026-10-05

Manage retained lifecycle now opens a single-clip lifecycle Inspector directly from
an authored animation asset. Its fresh library row must match the inspected capture
identity, hash, owners, source model, counts and active status before controls become
available. The actor library keeps its existing multi-clip and assignment workflow;
the asset lifecycle view exposes no actor-assignment actions and their handlers reject
assignment. Opening or previewing the asset does not select its capture actor.

Review retirement/restoration is readonly. Apply uses the existing activation command
and exact review/source key, then refreshes the asset catalog through the guarded
post-command path. Clip identity and captured bytes persist. Existing authored initial
references block retirement until cleared in the actor Inspector. Source/project/scene/
mode changes invalidate the view; Undo/Redo, Save/Open and normal Build remain the
existing workflow. No new serializer or runtime write is introduced. Gameplay
acceptance remains deferred. See [asset lifecycle](legaia-retained-animation-assets.md#direct-retained-lifecycle).

Verification: 3 retail-enabled Python tests, 2 Node workflow checks and 3 JavaScript
syntax checks passed. The actual headless editor verified exact single-asset scope,
blocked assigned retirement, readonly saved-pose Preview/Return and lifecycle Review,
then retired an unassigned clip and restored a retired clip through exactly two Apply
commands. Actor selection, retail imports, every captured record hash and the complete
initial-assignment component were unchanged; asset status refreshed automatically.
Undo/Redo and Save/Open passed. Normal private Build passed native bank, initial header
and relocation readback plus ZIP/SHA integrity checks. Restoration screenshot inspected.
No game launched or installed. Evidence:
`local-output/sdk-20260909/retained-asset-lifecycle-20261005/proof.json`.

## Direct retained asset GLB interchange - 2026-10-05

A retained animation asset now offers Edit retained GLB in Edit mode when native
animation authoring is available. The asset opens the existing captured-clip GLB
workflow directly: prepare export, download the GLB and source binding, select
externally edited files, Review, inspect the proposed pose, and Apply. Capture actor
selection is not required. The actor-library route keeps its actor-owned lifetime;
the asset route follows the project, scene, Edit mode and source revision.

Exports use an explicit caller-selected FPS; retail timing is not inferred. Existing
strict binding, native quantization, frame mapping and revision limits remain in
force. Apply preserves the clip UUID, updates authored initial references atomically,
and keeps a retired clip retired. Both direct editing routes share a guarded catalog
refresh after Apply, so the asset's displayed source witnesses update. Save/Open,
Undo/Redo and normal Build continue through the existing command and serializer.
Game appearance/playback verification remains deferred. See
[asset GLB workflow](legaia-retained-animation-assets.md#direct-glb-interchange).

Verification: 3 retail-enabled Python tests, 2 Node workflow checks and 2 JavaScript
syntax checks passed. The actual headless editor completed export and byte-verified
GLB/binding downloads, external channel replacement, Review, proposed-pose Preview
and exactly two Apply commands for assigned and retired assets. Capture actor
selection and retail imports were unchanged; assigned reference hashes updated and
retirement persisted. Undo/Redo, Save/Open and normal private Build passed, including
native bank/initial-assignment/relocation readback and package ZIP/SHA verification.
Both proposed screenshots were inspected. No game was launched or installed.
Evidence: `local-output/sdk-20260909/retained-asset-glb-20261005/proof.json`.

## Direct retained animation asset editing - 2026-10-05

Retained asset inspection now offers Edit retained content in Edit mode with the
animation authoring capability. It routes a detached verified capture row to the
existing retained-content editor. Asset ownership is independent of actor selection;
project/scene/mode/source freshness remains enforced by the reviewed editor. Actor
library editing keeps its selection-bound lifetime. No serializer or new animation
format is introduced by this entry point.

Review and proposed-pose preview stay readonly. Apply uses the existing atomic
command, preserving the clip UUID while updating its record hash and every authored
initial reference together. Retired content can be edited without restoration.
After successful asset-based Apply, a deferred source/busy/mode guard refreshes the
resource catalog so the same asset exposes fresh witnesses. Save/Open and normal
private Build remain the existing project workflow; runtime appearance/timing and
playback acceptance remain deferred. See [direct editing workflow](legaia-retained-animation-assets.md#direct-content-editing).


Verification: 6 retail-enabled Python tests, 2 Node checks and 2 JavaScript syntax
checks passed. The actual headless editor edited both assigned and retired assets
through Review, proposed-pose Preview and Apply; actor selection and retail imports
were preserved, with exactly two atomic commands. Undo/Redo and Save/Open round trips
passed. The normal private Build passed native bank, initial assignment and relocation
readback; package ZIP integrity and SHA-256 matched its receipt. No game was launched
or installed. Evidence: `local-output/sdk-20260909/retained-asset-edit-20261005/proof.json`.

## Retained animations in the Asset Database - 2026-10-05

Refresh scene resources now registers active and retired saved clips as authored
animation assets, with stable scene/UUID identities. Animations and Authored assets
show the records and badge; Project discovery includes their source memberships.
A dedicated readonly asset Inspector discloses status, frames/channels, authored
initial-assignment counts and original/captured source witnesses. Preview reconstructs
saved content through the existing decoder and opens the normal model viewer with
Current geometry. Captured model and actor navigation remain separate actions.
Retired preview does not reactivate the clip or assign a generated/native slot.

Registered retained clips are now navigable from reference inspection. Every
retained record has an authored captured-model edge with source hashes, owners,
counts and active status; active actor assignments preserve their separately
verified native selector/bank edges. Runtime playback/timing are unresolved.
Discovery/preview also work in a readonly observation view without changing the
original mode. Exact-source, malformed/extra-field and disposed-dialog guards
remain explicit. See [retained asset workflow](legaia-retained-animation-assets.md).
Validation: 42 focused/neighboring Python checks, four JavaScript workflow/contract
suites and three syntax checks passed. Native HTTP discovery, actor/clip/model
references, all three clip previews, Project membership, malformed/stale requests
and readonly observation mode passed. The actual browser verified animation/authored
categories, all three inspectors and model viewers, captured-model navigation,
actor reference -> registered clip metadata navigation and stale-source rejection.
Complete document/history/files/mode/scene were unchanged. Zero page errors or
authoring/Build/Save/game requests; screenshots inspected. Private evidence:
`local-output/sdk-20260909/retained-assets-20261005/proof.json`. Initial browser
harness assumptions about responsive-only tabs, total authored counts and collapsed
provenance text were corrected; prior attempts are preserved. No game launched.

The earlier retained-reference navigation limitation is superseded when the
verified scene catalog registers the clip. Full SDK goal remains active; gameplay
acceptance remains deferred.


## Retained initial animation reference correction - 2026-10-05

Actor reference inspection now keeps the original decoded initial clip while a
retained assignment replaces the effective inherited clip relationship. Stable
retained UUID nodes connect the assigned actor to its captured model in active
scene and Project scopes. Fresh readonly assignment Review qualifies ledger,
record, bank, model/channel-owner and exact component hashes, plus the current
native slot/selector and frame/channel counts. Unavailable derived catalogs do
not assert retained proof. Runtime playback remains unresolved.

Retained clips currently lack standalone navigable AssetDB records; their row
navigation stays disabled. Use the actor Inspector to Manage/Preview them.
Recorded provenance, layer filters and identity/hash search remain available.
See [retained reference workflow](legaia-allocated-animation-references.md).

Focused Python/JavaScript checks cover suppression of only the inherited effective
edge, original/inverse links, shared-model identities, exact evidence and native
bounds, detached results and unchanged observation-mode metadata. Native HTTP
checks cover active/Project actor/clip/model graphs, current native Review agreement,
Clear/Undo, Save/Open and unchanged project document/history/files for queries.
All 28 focused/neighboring Python checks and both JavaScript reference suites passed.
The native browser verified active/Project scopes, retained disabled navigation,
identity search, layer separation and Recorded provenance, with zero page errors
or authoring/Build/Save/game requests. Screenshot inspected. Private evidence:
`local-output/sdk-20260909/allocated-references-20261005/proof.json`.
The graph change introduces no gameplay verification gate; existing gameplay
acceptance is deferred and the full SDK goal remains active.


## Project-wide source script bookmark navigation - 2026-10-05

Script bookmarks now opens a project-wide catalog beside the resource tools.
Search covers names, scene/owner identity, padded/unpadded hex offsets, mnemonics
and original record hashes; a scene selector narrows imported memberships. Cards
show original record/import witnesses and retain the existing stable bookmark IDs.
Empty, stale and pending contexts are explicit; Refresh rebinds the current list.

Open bookmarked instruction navigates to the imported scene, selects an actor owner
where applicable, and opens actor/partition-two inspection. The newly inspected
original owner, record hash, unique decoded PC and mnemonic qualify before focus.
A verified-bookmark label identifies the requested original boundary. Mismatched
source rejects before any row is focused. Pending edits/animation, stale/busy lists
and changed bookmark/project guards prevent unintended navigation. No instruction
or bookmark command is issued. Active scene/selection use normal editor navigation;
a scene change can mark the active-scene setting dirty.

Native map01 -> town01 actor0044 -> town01 partition-two0015 -> map01 actor0001
passed search/scope/source witness browsing, exact owner selection and saved-PC focus.
A deliberately mismatched record hash rejected before focus with no stale evidence.
Complete project document/history/Authored files and Build input key were unchanged
on return. Zero command/history/Build/Save requests, page errors or game launches.
Catalog/source/search JavaScript guards and20 neighboring bookmark/view/copy Python
regressions passed. Screenshots inspected. Private evidence:
`local-output/sdk-20260909/project-script-bookmarks-20261005/proof.json`.
See [project-wide workflow](legaia-script-bookmarks.md#project-wide-navigation).
No new gameplay gate; full SDK goal remains active.


## Source-qualified saved script bookmarks - 2026-10-05

The Script and dialogue workspace now saves named original decoded instruction/
dialogue boundaries as project navigation metadata. Stable UUIDs bind owner, imported
scene witness, record SHA256, record-relative PC and mnemonic. Save/Update freshly
verify imports and use the read-only inspector, without inheriting byte-serializer
write restrictions. Up to256 records, names unique per script, exact bounded metadata.
Recall requires the newly inspected original record and unique boundary; it only
focuses a row. It does not infer execution, authored reachability or runtime PCs.

Save/Rename/Update offset/Delete use ordinary commands, history and dirty tracking.
Save/Open and project copy preserve records; Open validates portable metadata without
a disc. Reimport cannot reinterpret records or their history. Pending script drafts
lock mutations/history; source, busy and disposed-context guards remain explicit.
Bookmarks stay separate from game overrides and Build inputs. See
[script bookmark workflow](legaia-script-bookmarks.md).

Native Town01 actor0044 browser CRUD, retarget, read-only recall, Undo/Redo and Save
passed. A partition-two bookmark passed source qualification and Save/Open. Project
copy retained metadata. Paired normal Builds with/without the library emitted an
identical native asset payload. Complete imports, overrides and Authored files stayed
unchanged. Reopened read-only layout/recall retained the complete document/files;
screenshot inspected. Twenty focused bookmark/view/copy Python tests and JavaScript boundary/
source guards passed; zero page errors or game launches. Private evidence:
`local-output/sdk-20260909/script-bookmarks-final-20261005/proof.json`.
No new gameplay gate; existing gameplay acceptance remains deferred. Full goal active.


## Collapsible actor component Inspector - 2026-10-05

Actor component headers now collapse or expand their existing contents. Left/Right
collapse/expand; Up/Down and Home/End move focus among visible component headers.
Enter/Space use normal button activation. Collapse/Expand visible components work
with the existing search and authored-only filters, leaving filtered sections' layout
choices intact. Header focus restores after a same-actor Inspector rerender; it is
not transferred to another actor. Component layout is shared across actors within
one project/editor session and resets on project changes. Reloading starts expanded.

This is display state only: imported, authored, effective and live fields remain
separate. Hidden inputs/actions retain their existing DOM nodes, values and handlers.
No commands, authored metadata, native assets, Build or runtime behavior changed.
Scene-resource/NPC draft Inspectors retain their existing specialized layouts.

Native Town01 browser checks passed collapse/expand, keyboard focus, actor changes,
filtered bulk controls, retained input nodes, same-scope rerender focus, stale dispatch
and project/scope reset. Complete project document and Authored files were unchanged;
zero mutation requests, page errors or game launches. Eight focused SDK Inspector
schema tests and existing component/filter JavaScript checks passed. Screenshots
inspected. Evidence: `local-output/sdk-20260909/inspector-sections-20261005/proof.json`.
No new gameplay gate; existing package appearance and stability checks stay deferred.
The full SDK goal remains active. See [Inspector component layout](legaia-inspector-sections.md).


## Selected vertex plane alignment - 2026-10-05

Selected vertex group scope now offers Align group X/Y/Z at the selected rows'
minimum, maximum or bounds-centre source coordinate. Centre is (min+max)/2 rounded
to the nearest signed16 integer with half ties away from zero, including negative
centres. This changes one axis of selected rows only. Other coordinates, vertices,
objects, normals, faces/material words and allocation ownership remain unchanged.
No actor transform or pose channel changes; native positive Y still points down.

Alignment stages a local Draft. Current/Retail comparisons and one/all-instance
placed-scene inspection retain it through Return/Restore. Nonuniform alignment hides
translation handles and locks XYZ offsets, membership, library and history until
Apply/Discard. Explicit Apply uses /api/model-vertices-alignment and one normal
model override/history step. Already-flat selections make no draft/history change.
Raw and scene previews share the exact source-qualified candidate; keys, native
ownership, complete geometry, axis/anchor/membership and stale replies are checked.

Native Town01 model0000 object0 rows[0,1,2] aligned on the centre Y plane passed
no-op/Discard, draft locks, Current/Draft, placed scene comparison, all-instance mode,
Return/Restore, Apply, Undo/Redo and Save/Open. Complete document/Authored files
unchanged before Apply; candidate matches independent exact-axis reconstruction.
Full Retail-section normal Build directory/ZIP readback passed; only model offsets
1518/1526/1527/1534/1535 change. Seven focused alignment/group/allocated-object checks
and JavaScript geometry/rounding/review guards passed; screenshots inspected, zero
page errors/game launches. Allocated-row content replay retains source ownership.
Evidence: `local-output/sdk-20260909/vertex-alignment-20261005/proof.json`.
Package SHA256: `b56e76531495b9a39f9e2831f5f0727461551f185cebd14e479dcf228bd077d4`.
Appearance and scene/save-load stability remain on the deferred queue. Goal active.

## Reusable saved model vertex groups - 2026-10-05

Selected vertex group scope now has a project-local library: Save, Recall, Rename,
Update membership and Delete. Up to128 named groups retain stable UUIDs, model/scene
identity, object-local indices and source provenance. Names are unique per model.
Save/Open and project copy preserve them. Create/rename/update/delete use ordinary
project commands, dirty tracking and Undo/Redo; selection metadata never edits game
geometry. Recall is read-only and fills the local group at zero offsets. Dirty,
invalid offsets, gizmo/marquee gestures, pending requests and changed context lock library actions.

Retail rows bind to the original model hash and retain ownership across coordinate
and compatible content edits. Allocated rows/objects additionally bind to the typed
vector/object allocation fingerprint. This fingerprint is deliberately strict:
another allocation invalidates recall for allocated selections until explicitly
updated against Current. It never silently substitutes a reused index. Group validation on Open checks
portable metadata without disc access; recall requalifies Current row bounds, source,
scene key and the saved review key. Reimport cannot reinterpret selections/history.
The source import, authored geometry, pose and selection metadata stay separate.

Native Town01 model0000 passed create, local recall, rename, membership update,
delete/Undo/Redo, Save/Open, then recalled rows1/2 and applied X16 to exactly those
rows. Recall still worked after the coordinate edit. All first-phase model content,
imported records, scene overrides and Authored files stayed unchanged; metadata and
geometry used separate history entries. Recall snapshots are read-only. Screenshots
inspected, zero page errors/game launches. Paired normal Builds with/without the
library emitted identical native payloads.25 focused project/library/copy/view/
selection checks plus JavaScript exact-recall guards passed. Private evidence:
`local-output/sdk-20260909/saved-vertex-groups-20261005/proof.json`.
No new gameplay acceptance gate; existing movement output remains queued. Goal active.

## Marquee selection for model vertex groups - 2026-10-05

In Selected vertex group scope, Shift-drag a rectangle to replace membership;
Ctrl+Shift-drag (or Meta+Shift) adds to it. The visible dashed overlay does not orbit
the camera. Selection uses all projected object-local rows, including hidden rows
and rows beyond the point-marker drawing cap. Reversed rectangles and viewport
clipping are supported. Empty/very small rectangles retain membership; exceeding
4096 unique vertices rejects without changing it. The group status shows a count.

Marquee selection is local and requires zero valid offsets, picking enabled and
Current/Draft geometry. Retail and dirty/invalid drafts cannot select. Controls and
handles lock during the gesture. Escape, pointer cancellation/capture loss, blur,
wheel input, viewport resize and changed source/draft/camera cancel without committing
membership. Source context and viewport dimensions are requalified before release.
Closing the workspace releases pointer capture and the blur listener.

Native Town01 model0000 selected the expected27 rows, passed additive membership,
Escape/blur/resize and Retail/dirty-draft guards, then applied X16 to exactly those
rows through the existing one-step group command. Other vertices, normals and
native topology stayed exact; Undo/Redo and Save/Open passed. Complete document and
authored files unchanged before Apply and in the final read-only visual check.
Changed draft cancels the live rectangle; overlay screenshot inspected. Pure checks
cover boundaries, reversed/clipped rectangles, hidden/deep rows, immutable inputs,
add/replace, uniqueness, drawing-cap independence and4096 overflow. Static module
routing was fixed after the initial native404; final native checks have zero errors.
Evidence: `local-output/sdk-20260909/vertex-marquee-final-20261005/proof.json`.
No Build/runtime behavior changes or game launches. Existing group movement output
remains on the deferred gameplay queue. The full SDK goal stays active.

## Selected vertex group movement - 2026-10-05

Move model geometry now supports a selected group of 1..4096 unique existing
object-local vertex indices. Enter comma-separated indices or click points to
toggle membership before moving. XYZ handles and numeric signed16 offsets move
the group from Current, with a bounds-centred handle, snap and Escape cancellation.
Dirty/invalid offsets lock membership and history; Discard restores zero offsets.
Retail/Current/Draft layers retain the selection/draft. Unselected vertices,
other objects, normals, topology and material words remain unchanged.

The exact same qualified candidate drives read-only object/scene previews and
/api/model-vertices-translation Apply. Index ownership, uniqueness, source hashes,
scene keys, complete geometry and resulting signed16 bounds are checked. Apply
creates one project history step; zero offsets create none. One/all-instance scene
inspection retains the group on Return/Restore. No actor placement or pose edit.

Native Town01 model0000 object0 group[0,2] offset[16,-8,32] passed point toggling,
gizmo drag/Escape, invalid draft locks, scene Current/Proposed, all-instance mode,
Apply, Undo/Redo and Save/Open. Complete document/authored files unchanged before
Apply and throughout the separate interaction check. Full Retail-section directory
and ZIP readback matches the exact two-row candidate; only eight model bytes change.
Eight focused API/content/object/allocated-object checks and JavaScript guards pass.
Screenshots inspected; zero page errors/game launches. Private evidence:
`local-output/sdk-20260909/vertex-group-20261005/proof.json`.
Package SHA256: `bd600024ab3ef57fd9905667eeff3497125ae5700e5e278a01a3c6deddc85f4f`.
Game appearance remains deferred in the gameplay queue. The full SDK goal is active.

## Retail comparison and vertex reset in the movement workspace - 2026-10-05

Move model geometry now offers Retail, Current and Draft layers. Retail loads the
independently decoded imported geometry, including its original face topology;
Current retains all authored changes. Layer switching retains the local draft and
camera. Retail comparison hides handles and disables picking. Original object-local
row identity is retained; appended vectors and copied objects have no Retail counterpart.

Reset draft vertex to Retail copies only that original signed16 XYZ into the local
draft. Explicit Apply uses the existing hash-qualified vector command and creates
one ordinary history step. Whole-object reset is unavailable. Source qualification
rejects malformed coordinates, ownership and face ranges; baseline reads write no
project/history/authored files. Added source data remains under the existing response
budget.

Native Town01 model0000 object0 vertex0 reset from Current352/-32/241 to
Retail320/-32/241 passed comparison, draft retention/locks, Apply, refreshed baseline,
Undo/Redo and Save/Open. The complete project document and authored files were
unchanged before Apply; only that vector changed, with vertex1's authored368/0/145
retained. Zero page errors and game launches. Screenshots inspected. Focused source
HTTP/history and JavaScript baseline/ownership/malformed-data checks passed.
Evidence: `local-output/sdk-20260909/retail-movement-20261005/proof.json`.
No new gameplay verification gate or package is required for this editor workflow;
in-game appearance remains on the existing manual queue. The SDK goal stays active.

## Inspect individual vertex drafts in the placed scene - 2026-10-05

Selected vertex scope now supports the same placed scene inspection as Entire
object. Inspect movement draft in scene qualifies the exact object-local vertex
index, signed16 XYZ, Current/native geometry, material words, bounds and source
hash before requesting one supported instance or all shared model instances.
The earlier object-only restriction is superseded. Placement and supported pose
remain source-owned; no actor transform or pose channel is authored.

The SDK now exposes read-only /api/model-vector-preview and
/api/model-vector-scene-preview. Preview and existing Apply share the same native
candidate preparation, preserving Current authored faces/materials and topology.
Preview emits no command/history/file write. Exact HTTP envelopes, scene source
keys, vector owner/kind/index/values and candidate identity are checked. Numeric
bounds, source changes and stale replies reject; recomputed bounds match native
geometry and known texture/blend display enrichment stays separate.

Native Town01 model0000 object0 vertex1 draft368/-16/32 passed single/all-instance
rendering, Current/Proposed comparison, Return/Restore retention and late changed-
draft rejection. The complete project document/history/authored state remained
unchanged, with zero writes and page errors. Screenshots inspected. Two focused
API/candidate checks, three content/history/retained-topology checks, four existing
allocated-vector pose checks and JavaScript geometry/review guards passed.
Evidence: `local-output/sdk-20260909/vertex-scene-20261005/proof.json`.
No game launched. This read-only integration adds no gameplay verification gate;
actual appearance remains on the existing package queue. The SDK goal stays active.


## Inspect object movement drafts in the placed scene - 2026-10-05

The 3D geometry movement workspace now offers a source-qualified Scene instance
selector and Inspect object draft in scene for Entire object translation. Choose
one supported instance or all instances of the shared model. It first qualifies
the normal object proposal against exact local Current/Proposed native geometry,
bounds, material words, source hash and owner, then requests the existing placed
scene proposal. Known HTTP texture/blend enrichment stays separate from raw geometry;
JSON key order has no semantic meaning. No project command or Apply is implicit.

The scene retains qualified placement and supported pose and exposes ordinary
Current/Proposed comparison, isolation, Return to movement draft and Restore.
Both return paths keep exact offset/scope/instance choices. Source, scene, draft
and late-response guards prevent stale handoff; Close withdraws an owned inspection.
The action disables for single-vertex scope, invalid/no-op offsets, loading or an
unavailable authored scene/model instance. Single-vertex scene handoff remains
future integration, while its existing object-local editing remains supported.

A native Town01 model0000 draft64/-16/32 passed single/all-instance scene rendering,
Current/Proposed comparison, Return/Restore retention and rejection of a reply after
the draft changed. The complete project document, history and authored asset state
remain unchanged; zero authoring requests and zero page errors. Screenshots inspected.
Focused geometry/review guards and4 existing object/pose checks passed. Evidence:
`local-output/sdk-20260909/movement-scene-final-check-20261005/proof.json`.
No game launched. This read-only workflow adds no new gameplay-verification gate;
actual model appearance/pose remains on the existing deferred package queue.
The full SDK goal stays active and solo.


## Whole-object movement and compressed-content delivery - 2026-10-05

The model geometry movement workspace now offers Selected vertex and Entire object
scopes. Object scope moves every existing vertex in the selected native object,
including hidden rows, with XYZ offsets from Current and a bounds-centred gizmo.
Normals, topology and other objects stay fixed. This edits object-local geometry;
it does not change actor placement or assign a pose. Dragging remains local until
Apply. Dirty/invalid drafts lock scope, object and history; Current comparison,
snap, Escape cancellation, retained Apply and ordinary Undo/Redo remain available.
Every candidate vertex must fit signed16. Offset controls use signed16 source units.

Native Town01 model0000 object0 passed a208/-16/32 translation across50 vertices,
draft-only drag, Escape, overflow rejection, scope locks, one Undo step, Save/Open
and retained Undo/Redo with zero page errors. The real Build initially exceeded the
original compressed span by17 bytes. Normal Build now relocates qualified TMD packs
when composed content cannot fit, reusing the existing pack/archive/native reader
path. A typed capacity error selects this path; other qualification errors propagate.
All authored members sharing the pack compose together. Fitting fixed-layout edits
keep ordinary overlays. Noncanonical/unowned packs still reject.

Full independently reconstructed section readback matches Build directory and ZIP.
The native reader passed complete logical/raw-sector framing, metadata and vanilla
clear checks. Focused source/gizmo, content/history and relocation checks passed.
Evidence: `local-output/sdk-20260909/object-move-20261005/proof.json`.
Package SHA-256: `ae41e80b50649ef9f52a0d15c1c07c2f8106ead48f1075d5ed399fe4eb438bf2`.
No game launched or user runtime installed. Appearance/pose/scene lifecycle remains
in the deferred gameplay queue. The full SDK goal remains active and solo.


## Retained vertex editing and project history - 2026-10-05

The vertex movement workspace remains open after Apply. It requalifies the new
Current source and retains the camera and selected existing row, allowing another
vertex edit without reopening. Ordinary project Undo/Redo is available through
explicit toolbar controls and non-input Ctrl-Z/Shift-Ctrl-Z shortcuts. Dirty/invalid
drafts block history. Native input text undo stays local to the input. Changed
project/scene/mode rejects continuation. A published change with a failed source
refresh disables editing until Close/reopen; stale geometry is withdrawn.

Native Town01 model0000 checks passed two retained edits, fresh source after each,
camera retention, button/keyboard Undo/Redo, draft locks, two ordinary history steps
and Save/Open. Injected refresh failure blocked editing, and Close/reopen recovered.
Final source-failure/recovery evidence is recorded alongside the
workflow at `local-output/sdk-20260909/vertex-session-final-20261005/`. Full normal
Build directory and ZIP section readback matches independent Retail reconstruction,
with only model bytes1516 and1524 changed. Other vectors/normals/topology stay fixed.
No game launched; appearance remains deferred. The SDK goal remains active and solo.


## Pick vertices in the model movement viewport - 2026-10-05

Move vertices in3D now opens directly from the model shape panel. The movement
viewport displays bounded projected point markers and selects the exact existing
object-local vertex by click, using screen distance then depth/index ties. Picking
includes hidden vertices; it does not establish visible-surface ownership. Current
and Draft retain the same camera. Dirty or invalid drafts lock selection until
Discard; orbit drags do not pick. Numeric object/index controls remain available.
The transparent point overlay preserves the visible mesh; marker drawing is capped
at1024 plus the selected point, while picking considers all qualified projected rows.

Native Town01 model0000 checks selected exact rows1 and2, verified dirty/invalid
locks, pick toggle, Current-layer selection, orbit exclusion and close cleanup.
The complete project document/history stayed unchanged; zero authoring requests
or browser errors. Final screenshot inspected. Focused nearest/depth/index/bounds
Node checks passed. Evidence: `local-output/sdk-20260909/vertex-picking-final-20261005/`.
This browsing addition needs no immediate gameplay check; the previous vertex edit
package stays in the manual queue. The full SDK goal remains active and solo.


## Direct model vertex movement - 2026-10-05

The vector Inspector now opens a Current/Draft geometry viewport for an existing
vertex. X/Y/Z handles and numeric input use signed16 object-local source units;
positive Y points down and snap steps are1/16/64. Dragging stays local, Escape/camera/
viewport/context changes cancel unfinished movement, and Current remains separately
inspectable. Apply uses the existing native-hash guarded vector command as one Undo
step. Other vectors, normals, objects and topology stay fixed. Closed dialogs release
renderer, observer and shared gizmo listeners. This is unposed geometry authoring.

Native Town01 model0000 vertex0 moved320/-32/241 to464/-32/241. Styled browser,
Current/Draft comparison, snap16, Escape, overflow rejection, one Apply, Save/Open
and Undo/Redo passed with zero page errors. Seven focused Python checks and Node
source/geometry guards passed. Normal Build directory and ZIP full-section readback
match independent Retail reconstruction, changing only model byte1516. Evidence:
`local-output/sdk-20260909/vertex-move-20261005/proof.json`. No game launched; model
appearance remains in the manual queue. Details: `docs/legaia-model-vertex-movement.md`.
The broader SDK goal remains active and solo.


## Transition graph to exact source entry - 2026-10-04

Scene and Project transitions now open the exact transition Inspector from each
instruction row. Cross-scene navigation refreshes source resources and qualifies
stable identity, owner/PC, full provenance, reference and Current entry layers
against the retained graph. Project/source/Current changes reject. The Inspector
then leads into the existing destination arrival comparison and authoring workflow.
This source navigation creates no authored change; graph reachability stays unknown.

Native Town01/map01 project and scene graph round trips passed with the complete
project document/history unchanged, zero authoring requests and zero browser errors.
Screenshots inspected; eight focused Python graph checks and Node source/Current
qualification guards passed. No game launched; no immediate gameplay check is needed
for this navigation feature. Details: `docs/legaia-transition-graph-entry-navigation.md`.
The full SDK goal remains active and solo.


## Arrival draft X/Z handles - 2026-10-04

The destination viewport now has opt-in Move arrival draft handles. Raw guest X/Z
axes use the same scene transform and camera as the geometry, snap to 64 units and
reject points outside 64..16384. Facing remains unchanged; reference Y is never
authored. Purple Draft is distinct from green reviewed Proposed. Dragging sends no
Review or authoring request and creates no history; explicit Review and Apply retain
the normal source-qualified serializer and one-step Undo workflow. Escape, camera,
viewport, focus, move-mode and source-context changes cancel an unfinished drag.
Cancellation restores the previous local draft/review only while its source remains
current. Numeric controls remain available. Marker labels avoid each other.

Focused grid/provenance guards and native Town01-to-map01 editor checks passed:
draft-only movement, X/Z handles without Y, facing preservation, Escape/camera
cancellation, restored reviewed Apply, refreshed Current, Save/Open and Undo/Redo.
Normal Build directory and delivered ZIP MAN readback match the complete expected
native output. Evidence: `local-output/sdk-20260909/arrival-gizmo-final-20261004/`.
No game was launched; arrival execution remains queued for later manual verification.
This completes the arrival drag control, not the full SDK buildout.


## Reviewed arrival authoring in the destination viewport - 2026-10-04

The arrival comparison now authors the existing source transition through destination
viewport controls. Enter grid X/Z and facing sector, Review the green Proposed marker
beside Retail/Current and inspect the exact source byte audit, then Apply that reviewed
request. Draft changes withdraw Apply; Discard restores Current. Source/project/destination
changes invalidate the review. Apply revalidates all inputs, preserves upper direction
bits and unrequested operands, invokes the normal transition command and refreshes the
Current marker. Reference Y remains an inspection plane and is never authored.

Review independently qualifies the exact target byte audit against its Retail source
record/PC and requested encoded operands. It retains all other source entry edits and
does not change the active scene or publish overrides. Already saved entries report no
authored change. No destination names, instruction lengths, branch bytes or source trigger
positions are changed. No transform-drag tool or runtime execution is claimed.

Five focused Python checks and JavaScript review/source-byte/proposed-coordinate guards
passed. Native Town01 -> map01 browser Review/Apply passed on destination geometry,
including stale-draft withdrawal, one Undo step, refreshed Current, Save/Open and Undo/Redo.
Desktop Proposed and narrow saved screenshots were inspected with zero browser errors.
Normal private Build and independent full MAN/ZIP readback matched exactly two source-byte
changes, at28574 and28576. A fresh native report additionally qualified zero Current delta
with two retained Retail-to-Current source byte changes. Gameplay remains deferred; no
game launch or runtime installation occurred. Private evidence:
`local-output/sdk-20260909/transition-arrival-authoring-20261004/verified/proof.json`.
See [arrival authoring](legaia-transition-arrival-authoring.md).


## Transition arrival viewport comparison - 2026-10-04

Transition source resources now offer **Compare arrival in destination scene** when
the named destination is already imported and Edit-mode preview is available. The
service requalifies the source transition and destination import, records source and
destination preview keys and a project-state key, and preserves Retail/Current entry
layers. The main viewport opens the destination and shows blue Retail and gold Current
arrival markers, encoded-facing labels, Frame, Return and Clear controls. Reference Y
is editable for inspection and explicitly unknown; arrival markers are never presented
as source triggers or observed runtime positions. Scene/project/source-key changes
withdraw the overlay. Controls remain beside the viewport outside the Scene tools drawer.

This native browser pass also fixed a real Inspector handoff bug: flag and transition
dialog guards referenced a lookup local to Asset Details. They now use the shared asset
catalog, retaining their exact resource snapshots and context guards.

Ten focused Python checks passed with private-disc coverage and no skips, alongside
JavaScript transition/arrival guards and editor syntax checks. Native Town01 -> map01
showed Retail arrival (12352,3264), facing2048/4096 and Current (128,3264), facing1024/4096
against loaded destination geometry. Desktop/narrow screenshots were inspected; reference
Y, framing, Return, Clear, and flag/transition dialog actions passed with zero page errors.
Authored data and Undo/Redo history stayed unchanged. Navigation changes the existing
saved active-scene view state, so dirty status may change; it does not create an authored
override. No gameplay or game launch occurred. Prior failed harness/layout attempts remain
preserved. Private proof:
`local-output/sdk-20260909/transition-arrival-viewport-20261004/final-verified/proof.json`.
See [transition arrival preview](legaia-transition-arrival-preview.md).


## Current flag operand references - 2026-10-04

The reference browser now shows a separate Effective / Current relationship for
saved ScriptFlags operands, alongside the unchanged Retail encoded reference.
Each Current edge records the exact source instruction and operand ID, Retail and
Current indices, source-record hash and authored component hash. Source-group asset
IDs keep their Retail bank/index grouping; this does not create shared runtime flag
identities or infer values, story meaning or execution. Unedited sites inherit Retail
and do not receive duplicate Current edges. Stale annotations and mismatched source
records are rejected. Both active-scene and project queries use the same evidence.

Twenty-eight focused Python checks passed with the private disc enabled and no skips;
JavaScript qualification and existing reference/filter guards passed. Native dolk2
CFLAG_SET 24 -> 25 verified preserved Retail edges, Current inverse/project queries,
Save/Open, Undo/Redo and styled desktop/narrow browser display with exact script
navigation. Inspection left project data, history, dirty state and selection unchanged;
no browser errors or game launches occurred. Gameplay behavior remains deferred.
Private evidence: `local-output/sdk-20260909/current-flag-references-20261004/accepted/proof.json`.
See [Current flag reference contract](legaia-current-flag-references.md).


## Trigger group viewport comparison - 2026-10-04

## Searchable reference browser - 2026-10-04

Reference inspection now filters exact recorded layers and relationship directions,
and searches neighbor IDs/labels/types, relation labels and provenance with bounded
plain-text terms. Visible/total counts distinguish no matches from absent recorded
relationships. Coverage, diagnostics and source proof remain unchanged. Filtering
uses the accepted snapshot without requests; scope changes requalify while retaining
filters. Close is beside the title, and controls use a responsive grid. Qualified
navigation identity and stale/closed request rejection remain intact.

Focused JavaScript filter and existing source/proof/project-navigation checks passed.
A copied native vell project verified Current and Retail/source filtering, outgoing
rows, authored-slot ID search, counts, no-match recovery, scope retention and exact
Inspector navigation. Filter changes issued no reference requests; project document,
selection and history stayed unchanged, with zero page errors. Desktop/narrow
screenshots were inspected. No backend, serializer, installed output or game changed.
Details: [reference browser filters](legaia-reference-browser-filters.md).
Evidence: `local-output/sdk-20260909/reference-filters-20261004/final/proof.json`.
The full goal remains active and solo; gameplay stays deferred.

## Guarded Current material reference reuse - 2026-10-04

Repeated active/project-wide reference inspection now reuses up to two bounded,
source-keyed Current material metadata censuses. Retail verification still precedes
reuse, and existing owned-content readers requalify model/base bindings and effective
texture/slot/source-recipe files. Same-size tampering cannot return a cached result.
Changed bindings invalidate; returned metadata is detached; caches stay out of project
persistence. Project-wide resource registration remains isolated while material caches
are shared only behind fresh snapshot verification. Current and combined metadata
budgets remain eight MiB, with existing project query budgets retained.

Twenty-one focused Python checks passed with private retail input and no skips. A
copied native vell authored project confirmed one Current decode across four initial
model/slot queries, model/TIM tamper rejection, restored input recovery, changed-binding
invalidation, warm HTTP/project-wide reuse and continued Retail checks. The styled
browser retained both reference layers and authored-slot consumers, with project,
selection/history unchanged and zero page errors. Screenshots inspected. Initial
local timing was about4.4s cold versus1.6s warm; this is fixture evidence, not a general
performance claim. No game, installed output or runtime code changed.
Details: [guarded reference reuse](legaia-current-material-cache.md).
Evidence: `local-output/sdk-20260909/current-material-cache-20261004/final/proof.json`.
Full goal remains active and solo; gameplay stays deferred.

## Current material-to-texture reference graph - 2026-10-04

The Asset Database now displays separate Retail and Current static material links.
Current discovery qualifies saved model edits and effective scene textures, including
new TIM slots, while retaining immutable imported links/cache. Authored slots expose
Current model consumers in active and project-wide queries. Model roots offer separate
Retail/Current diagnostics; missing, ambiguous and unsupported matches stay explicit.
Source/catalog/import, Retail/Current model and authored-state hashes qualify Current
edges. Reference freshness now includes model/texture overrides and texture additions.
No reference view mutates project state, selection or history. These are static address
matches, with runtime binding not asserted; live residency/appearance stay deferred.

Twenty focused Python checks passed with private retail input and no skips, plus the
reference/project-navigation JavaScript checks and new Current proof/diagnostic guards.
A fresh native vell project assigned a new TIM slot to Model0000 through existing
reviewed material authoring. Retail semantic evidence, Current/inverse/project queries,
Save/Open and Undo/Redo passed. The styled editor displayed both link layers and the
new slot's Current consumer, with project document/history/selection unchanged and
zero page errors. Desktop/narrow screenshots were inspected. No runtime, serializer,
installed build or game was changed. Full goal remains active and solo.
Details: [Current material references](legaia-current-material-references.md).
Evidence: `local-output/sdk-20260909/effective-material-references-20261004/accepted/proof.json`.

## Static VRAM upload map - 2026-10-04

Find static free coordinates now displays Current image, palette and boot-upload
footprints in a1024-word by512-row VRAM map, with proposed image/palette outlines.
Click or use arrow keys to inspect exact word ownership and half-open bounds.
The new read-only /api/texture-upload-map route shares native source qualification,
normalized wrapped rectangles and authored-slot exclusion with placement search.
The editor hashes the complete bounded census and requires exact agreement with
the placement source, coverage, count and occupancy hash before rendering.
Stale/closed requests cannot publish a map; conversion removes temporary geometry.
Map inspection changes neither selection nor authored data/history. Static coverage
is explicitly distinct from runtime residency and material compatibility.

Four focused Python checks passed with private retail input and no skips; map,
placement and existing conversion JavaScript checks passed. A fresh native vell
styled-editor workflow verified92 footprints, wrapped-tail mouse/keyboard picking,
separate conversion and closing a pending map. Project document, history and SDK
selection stayed unchanged, with zero page errors. Desktop and narrow screenshots
were inspected. Static module serving and border coordinate handling were corrected
from browser evidence; screen-pixel quantization was accommodated in the harness
before exact keyboard checks. No game launched or installed output changed.
Details: [static VRAM upload inspection](legaia-texture-upload-map.md).
Evidence: `local-output/sdk-20260909/texture-upload-map-20261004/final-verified/proof.json`.
The full SDK goal remains active and solo; gameplay acceptance stays deferred.

## Static texture placement finder - 2026-10-04

The PNG-to-TIM dialog now offers Find static free coordinates. Its read-only,
source-bound query considers known Current scene textures, authored slots and
boot uploads, fills image/palette coordinates, and keeps conversion, slot review
and Apply separate. Existing authored-slot edits exclude only their own Current
footprint. Deterministic bounded search distinguishes a fit, no fit and budget
exhaustion. Static placement does not prove runtime residency or material use.

The shared overlap census now accounts for GP0 upload wrapping across X=1024
and Y=512, matching local runtime GPU writes. Real vell boot uploads at X=960
with width256 previously lost their wrapped tail; slot review and the finder now
both include it. Unsupported transfers reject rather than clip.

Eight focused Python checks passed with the private disc and no skips, plus a
wrapped-tail overlap regression. Focused placement and existing image conversion
JavaScript checks passed. A fresh native vell editor workflow filled image (0,0)
and palette (320,511) for an 8x8 4-bit sample against92 normalized rectangles,
then separately converted the PNG. Independent overlap count was zero; project
document, history and selection remained unchanged, with zero page errors.
Desktop and narrow screenshots were inspected. No gameplay or installed build
changed. Details: [static texture placement](legaia-texture-placement.md).
Private evidence: `local-output/sdk-20260909/texture-placement-20261004/final/proof.json`.
The full SDK goal remains active and solo.

Reviewed trigger groups can now be inspected as Retail, Current or Proposed cells
in the central scene viewport. All selected cells receive a distinct outline, and
Frame reviewed group fits their combined bounds. The floating comparison control
switches layers without Apply; Return to group review restores the source display
and retains the accepted proposal and offsets. Restore source cells closes the tool.
Changed drafts, closed reviews and stale sources remove temporary geometry. Busy
and source/project guards apply. The Inspector reports the selected group's actual
layer bounds. Cell geometry uses raw128-unit half-open X/Z cells on Y=0, explicitly
an unknown-height reference plane; no floor or activation semantics are inferred.

Focused geometry, renderer, group lifecycle and existing single-cell JavaScript
checks passed, including bounded framing, byte-coordinate extremes, detached
geometry, group highlighting/canvas state, layer switching, retained Return, busy
Return and stale cleanup. A fresh native vell browser workflow verified Current
and Proposed Inspector bounds, read-only viewport comparison, retained Return,
then one Apply and one Retail reset. Project document and unrelated script binding
were restored, SDK selection unchanged, two Undo steps, zero page errors. Current,
Proposed and narrow review screenshots were inspected; the floating control gained
an opaque panel for readability and the workflow was rerun. Evidence:
`local-output/sdk-20260909/trigger-group-viewport-20261004/final/proof.json`.
The prior native Build/ZIP byte-ownership check remains separate; no backend or
serializer changed in this milestone. No game launched or installed output changed.
Contact, shadowing, height and activation need gameplay acceptance. The full SDK
goal stays active and solo.


## Atomic trigger group authoring - 2026-10-04

The registered trigger Inspector now offers Move trigger cell group for existing
primary kind-0/1 source rows. Select1..128 cells and review an integer X/Z tile
offset from their Current coordinates, or return just those cells to Retail.
Retail/Current/Proposed coordinates and a source-byte audit appear before Apply.
Changing the selection or offset withdraws Apply, including late pending replies.
Closing aborts requests. The backend requalifies source and project identity and
publishes one ordinary TriggerCells history step. Unselected cell edits and other
components remain retained; payloads, row count and table order stay source-owned.
Out-of-range results reject the whole group. No rows, height or trigger semantics
are invented. New routes: /api/trigger-group-review and /api/trigger-group-apply.

11 focused Python checks passed with the private disc and no skips. Real vell HTTP
Apply, stale rejection, Save/Open and normal Build/ZIP readback composed two moved
cells with an existing script-binding edit: exactly the expected five bytes changed
and every gate byte was retained. Synthetic checks covered unselected edits, Undo,
Redo, Retail reset, no-op history and atomic bounds/source rejection. Focused new
and existing JavaScript checks passed for source/layer/offset/audit validation,
retained cells, busy controls, changed drafts and closed pending replies.

Fresh native browser acceptance passed for two-cell Review, draft invalidation,
one Apply and one Retail reset, unchanged SDK selection and retained script binding,
two Undo steps and zero page errors. Desktop and540px screenshots were inspected;
checkbox alignment was corrected and the workflow rerun. An earlier harness matched
the action in both sidebar and asset dialog; the accepted check scopes the dialog.
Evidence: `local-output/sdk-20260909/trigger-group-20261004/final/proof.json`.
No game launched or installed output changed. First-match shadowing, activation,
contact/height and script execution still require gameplay verification; the full
SDK goal remains active and solo.


## Trigger binding Inspector layers - 2026-10-04

Gate-1 trigger assets in the active scene now show a read-only Script binding
section directly in their registered Inspector. Retail, Authored and Current
stable script identities come from the qualified asset-reference graph. Each
available target opens the shared script Inspector directly. No authored value
means inherit; unresolved Retail targets remain explicit, even when an authored
target is qualified. This inspection does not require opening the edit review.
Other gates do not acquire guessed script bindings. Source changes, busy state
and closed panels block navigation; closing aborts unfinished reference requests.

Focused JavaScript reference/registry checks and syntax checks passed, including
inherited/authored/unresolved layers, busy/stale navigation and late closed replies.
A fresh real vell browser workflow verified Retail8/Authored0/Current0, both Retail
and Current script endpoints, unchanged project document/selection/history/dirty
state, zero authoring requests and zero page errors. Desktop and540px screenshots
were inspected. Evidence:
`local-output/sdk-20260909/trigger-binding-inspector-20261004/final/proof.json`.
The first browser pass exposed a shortcut to metadata rather than the complete
Inspector; that route was corrected. A later check ran before the script report
loaded; final acceptance waits for the endpoint and rendered report. No game
launched or installed output changed. Runtime activation/dispatch remains deferred;
the broader SDK goal stays active and solo.


## Effective trigger references - 2026-10-04

The asset-reference graph now retains each original Retail gate-1 trigger edge
and adds a separate effective edge for its current authored script binding.
Active-scene, inverse-target and project-wide queries share this distinction.
Both targets navigate to their qualified source owners. Authored edges retain
MAP/component hashes and the original target-byte location; fresh source checks
reject missing targets, forged hashes, catalog mismatches and stale source rows.
The graph asserts no runtime binding, activation or script execution.

Six focused Python checks passed with the private disc and no skips, including
native vell Apply, read-only graph queries, provenance rejection and Undo removal.
JavaScript decoder checks and syntax validation passed. A fresh browser workflow
verified Retail record8 plus authored record0 in active/project scopes, authored
target navigation, unchanged project document and zero page errors. The panel
screenshot was inspected. Evidence:
`local-output/sdk-20260909/effective-trigger-references-20261004/verified/proof.json`.
An earlier harness waited for collapsed raw provenance to be visible; opening
that disclosure corrected the check. No game launched or installed output changed.
Trigger activation/dispatch still needs gameplay verification. Broader graph and
SDK buildout remain unfinished; the full goal stays active and solo.


## Reviewed trigger script binding editor - 2026-10-04

The AssetTrigger registry now offers Edit trigger script binding for supported
primary kind-1 gate-1 rows. The dialog lists only SDK-qualified P2 source targets,
shows Retail/Authored/Current/Proposed binding identities and exact source/byte-audit
metadata, and requires explicit Review then Apply. Changing the choice withdraws
Apply. Retail reset uses the same reviewed backend. Current/Proposed inspection
opens the corresponding existing source owner in the shared script Inspector,
retaining the binding review for Return by closing that inspection. No runtime
dispatch or reachability is inferred. Busy and project/source context guards apply.

Real vell browser checks passed for read-only Review and Proposed owner inspection,
review retention, changed-choice invalidation, one Apply and one Retail reset,
resource refresh and unchanged SDK selection/imports. Zero page errors; desktop
and540px screenshots inspected. Focused report/registry JavaScript checks and all8
Inspector-schema Python checks pass. The schema test's old two-action expectation
was updated for the new registered trigger action. Evidence:
`local-output/sdk-20260909/trigger-script-editor-20261004/verified/proof.json`.
No game launched or installed output changed. The prior16-test API/Build package
acceptance remains separate; gameplay activation/dispatch and general effective
asset-reference graph edges remain unfinished. The full SDK goal stays active.


## Existing trigger script bindings: SDK/API/Build - 2026-10-04

Existing primary kind-1 gate-1 trigger rows can now be rebound to a qualified
same-scene partition-two script through a separate TriggerScripts scene override.
Stable script identities retain their source record hash. Targets must fit the byte
index and have a unique, available source record; aliases, unavailable records,
other scenes, other trigger gates and guessed raw addresses reject. Review exposes
Imported/Authored/Current/Proposed identities, source target metadata and byte audit.
Revalidated Apply publishes one ordinary Undo step. Clear restores one row to Retail;
Save/Open requalifies retained targets. Existing coordinate edits remain separate.

Build composes bindings with scenery, walls, regions and trigger coordinates into
the ordinary MAP overlay, independently checking its exact target-byte audit and
rejecting overlap. Only the third byte of an existing gate-1 row changes; the gate,
row count and other payload stay source-owned. API routes: /api/trigger-scripts-review
and /api/trigger-scripts-apply; command: apply_trigger_scripts.

16 focused existing/new checks passed with the private disc and no skips, including
real vell HTTP review/Apply, stale rejection, Undo/Redo/reset, Save/Open and normal
Build/ZIP readback. Combined native coordinates/binding output changed exactly two
bytes in one MAP overlay and retained the gate. Town01 has39 qualified targets but
no primary gate-1 rows; no Retail row was invented. Evidence:
`local-output/sdk-20260909/trigger-script-authoring-20261004/parent/proof.json`.
Editor controls and effective-reference navigation remain next offline work. No
game launched, installed runtime changed or Retail disc exported; activation and
actual script dispatch remain unverified. The full SDK goal stays active and solo.


## Script family navigation - 2026-10-04

The verified script dialog now has an Inspect script families navigator for its
existing Dialogue, Transitions, Movement, Flags, Waits, Model selectors, Facing and
Branches tool sections. It also works on unedited source owners. Links reflect
rendered SDK tools, not invented components or execution claims; a tool can explain
that no supported source operands exist. Each link scrolls and focuses its section.
Source/project/owner guards reject stale actions, and buttons visibly disable
during loading before becoming available. Authored summaries and reset stay separate.

Focused navigation/owner checks passed. A real Town01 actor and unedited partition-two
owner verified all15 available links with exact project selection, history, dirty
state, authored data and imported metadata, no authoring requests or page errors.
Screenshot inspected. The initial browser readiness check wrongly required a review
action to be available; a subsequent early click established that loading was still
active. The accepted run uses the actual navigation readiness state. Private proof:
`local-output/sdk-20260909/script-family-navigation-20261004/accepted/proof.json`.
No game launched; this feature requires no immediate gameplay verification.


## Hierarchy parent and child keyboard focus - 2026-10-04

Right expands a collapsed group while keeping focus on the header; pressing Right
again enters its first available child. Left on a child returns focus to its group;
Left on the header collapses it. These keys only browse the hierarchy. Disabled
search headers, hidden/disabled children and modifier keys are respected.

Focused Node checks and a real Town01 browser workflow passed across Actors,
Environment and Scripts, including a later child, one Tab entry and filtered-parent
handling. SDK selection, authored data, history, dirty state and imports stayed
unchanged; no navigation API writes or page errors occurred. Screenshot inspected.
Private evidence: `local-output/sdk-20260909/hierarchy-parent-child-20261004/parent/proof.json`.
No game launched; this feature requires no immediate gameplay verification.


## Focused stability recheck - 2026-10-04

At SDK source `28bda1d7`, the inspected runtime/precompile source hashes still
match the preserved inclusion evidence. Fresh synthetic restore-entry and
restore-continuation execution passed through the real overlay loader. Production
audio-output readiness and locked statistics snapshot fixtures passed. Ninja
Multi-Config/GCC passed nine inventory/body variants in both Release and Debug
(18 executable sum checks), sparse numeric filename ownership and final unchanged
builds. The restricted Ninja invocation failed before configuration; the permitted
retry passed both tests in14.303s. No implementation change was justified by this
recheck. Private current evidence:
`local-output/sdk-20260909/stability-recheck-20261004/parent/accepted.json`.

This is focused fixture acceptance, not complete runtime/release equivalence.
The preserved local release source ref remains `3ac7d410`; the sibling reference
directory currently has no Git metadata and cannot establish a fresh source HEAD.
No game, installed runtime or retail disc output was launched or modified.
Startup audio overflow, field savestate performance and the existing deferred
gameplay/audio boundaries remain open.


## 2026-10-04: Reveal selection in the hierarchy

**Reveal selection** clears the hierarchy search, expands the selected row's group,
scrolls to it and restores keyboard focus. It resolves the current source-resource,
NPC-draft, scenery or actor selection in the same order as existing editor tools.
Unrelated folds stay intact; no selection command, authoring command or mesh-visibility
change is dispatched. Preferences remain local to the workspace.

Focused reveal/group/navigation checks and a real Town01 browser workflow passed
for actor and partition-two script selection behind folds and nonmatching filters.
SDK selection, history, dirty state, authored data and imports stayed unchanged;
zero page errors, screenshot inspected. Evidence: ignored
`local-output/sdk-20260909/hierarchy-reveal-20261004/parent/proof.json`.
No game launched; gameplay remains deferred.


## 2026-10-04: Collapsible scene hierarchy groups

Hierarchy groups for Actors, NPC drafts, Environment, Transitions, Triggers, Regions,
Collision and Scripts can now be folded with their header buttons. Fold state is a
local display preference scoped to the current project/scene, retained across panel
refreshes. Search temporarily expands matching groups and disables folding until
search is cleared, then restores the saved folds. Group headers participate in the
existing roving keyboard focus; Left/Right collapse/expand a focused header and
Up/Down/Home/End skip folded members. Entity identities and selection actions stay
intact. Folding does not hide meshes, edit source data or change SDK selection.

Validation: focused group-state and existing hierarchy-navigation JavaScript checks
passed. A real Town01 browser workflow verified actor/environment folds, keyboard
skipping, search expansion and restoration, catalog-refresh retention and subsequent
partition-two script selection/Inspector navigation. Source entities, authored data,
history, dirty flag and SDK selection were unchanged; imports stayed exact. Screenshot
inspected; zero page errors. Evidence: ignored
`local-output/sdk-20260909/hierarchy-groups-20261004/verified/proof.json`.
No game launched; runtime acceptance remains deferred.


## 2026-10-04: Hierarchy-selected script component Inspector

Selecting a verified partition-two script in the scene Hierarchy now exposes
its authored components in the central Inspector alongside source asset metadata.
The shared component panel supports counts/details, source-family inspection and
reviewed reset. Inspection opens the verified source editor at the chosen family.
After a successful reset, the editor refreshes scene resources and restores the
same script selection if project and scene still match. Empty authored state stays
explicit. Existing actor selection, runtime observation and serializers are unchanged.

Validation: shared owner/reset/component JavaScript checks passed. A real Town01
browser workflow refreshed the catalog, selected partition-two script 0 through
the hierarchy, inspected its native transition, cancelled a review without writing,
then reset one component. Resource refresh restored the selected script with an
empty component summary. One Undo entry, Undo/Redo, Save/Open, unchanged imported
evidence and zero page errors passed. Screenshot inspected. Evidence: ignored
`local-output/sdk-20260909/script-hierarchy-inspector-20261004/parent/proof.json`.
No game launched; runtime execution remains unverified.


## 2026-10-04: Standalone source-owner component Inspector

Verified partition-two script inspection now includes an **Authored script
components** panel using the shared registered Inspector. It renders supported
Dialogue, Transitions, Movement, Flags, Waits, ModelSelectors, Facing and Branches
from the project's existing authored script records, with detached counts/details.
Unknown families are omitted; no raw retail layout or execution is inferred.
Inspection actions focus the qualified source editor. Reviewed reset uses the
existing source-bound command, one Undo entry and imported inheritance. After
reset the source editor refreshes and retains an explicit empty component summary.
Only active-scene, typed partition-two owner identities can use this alternate
review path; actor Inspector behavior and commands remain intact.

Validation: 13 focused schema/component-review Python tests and JavaScript shared
Inspector/reset/focus/owner tests passed. The actual desktop browser workflow opened
a real Town01 partition-two transition from Authored Assets, focused source entry
controls, reviewed/cancelled without mutation, reset and refreshed to empty. Undo/Redo,
Save/Open, exact history depth and unchanged imports passed. Screenshot inspected;
zero page errors. Earlier harness attempts used an incorrect asset tab/ID selector
and made no writes. Successful evidence: ignored
`local-output/sdk-20260909/script-owner-inspector-20261004/desktop/proof.json`.
No game launched; runtime transition acceptance remains deferred.


## 2026-10-04: Dialogue and transition Inspector authoring summaries

Dialogue now shows its authored text-run count and offers reviewed component
reset only when text runs exist. Authored actor Transitions use a registered
component with an entry count, exact entry details, source-editor navigation and
reviewed reset. Source inspection focuses dialogue authoring or transition entries
with spacing below the sticky toolbar. Text runs remain strings under Dialogue.runs;
encoded transition values remain entries. Existing source-bound revert commands
remove one component in one Undo entry; unrelated overrides and imports survive.

Validation: 20 focused schema, dialogue, transition and component-review tests
plus JavaScript action/reset/focus checks passed. A private Town01 browser workflow
verified dialogue source focus, read-only review/cancel, reset while preserving
Transform, Undo/Redo and Save/Open. A real Town01 partition-two transition was
reset through the existing source-bound command with the same history/persistence
checks. Actor transition Inspector rendering is synthetic-contract validated: no
supported Town01 actor transition was found, so this does not claim a retail actor
transition browser workflow. Screenshot inspected; zero browser errors. Evidence:
ignored `local-output/sdk-20260909/dialogue-transition-inspector-20261004/parent/proof.json`.
No game launched; runtime text/arrival acceptance remains deferred.


## 2026-10-04: Facing and branch Inspector workflows

ScriptFacing and ScriptBranches now expose detached authored-instruction counts
and the same reviewed component reset as other supported script operand families.
Reset is available only with authored entries in Edit mode; source inspection
remains available after reset. The Inspector's facing and branch actions focus
their qualified editor sections. All six operand-family sections have scroll
spacing for the sticky script toolbar. Imported operands, authored values and
effective values remain distinct; branch reachability and runtime facing remain
unverified. Existing serializers and source-bound removal commands are reused.

Validation: 15 focused schema, facing and retail branch workflow tests passed,
including native branch Build readback. JavaScript component/action/reset/focus
checks passed. A private Town01 browser workflow verified source-editor focus,
review/cancel with no mutations, one Undo entry per reset, hidden reset actions
when empty, Undo/Redo, Save/Open and unchanged imports. Evidence: ignored
`local-output/sdk-20260909/facing-branch-inspector-20261004/verified/proof.json`.
No game launched; manual gameplay remains deferred.


## 2026-10-04: Reviewed script component reset in the actor Inspector

The registered ScriptMovement, ScriptFlags, ScriptWaits and ScriptModelSelectors
components now offer **Review component reset** in Edit mode. The dialog shows the
owner, exact authored instruction identities and operands, and removal count.
**Reset reviewed component** removes that family in one Undo entry and restores
inheritance from imported operands. Cancel is read only. Other authored components
remain intact. The existing source-bound component revert command rejects stale
witnesses; no new serializer, generic property write or runtime write is introduced.

Validation: 11 focused schema/component history tests and JavaScript review/action
checks passed. A private Town01 browser workflow reviewed and cancelled without
mutation, reset two authored wait entries together while retaining Transform, and
verified one Undo entry, Redo, Save/Open and unchanged imported evidence. Screenshot
inspected; zero browser errors. Evidence: ignored
`local-output/sdk-20260909/script-component-reset-20261004/parent/proof.json`.
This is an implemented offline authoring workflow; gameplay remains unverified.


## 2026-10-04: Actor Inspector component filtering

The actor Inspector now has **Filter Inspector components**, **Authored only**
and **Reset filter**. Text search matches component identity, heading and displayed
values. Authored-only uses the SDK's explicit authored component list; matching
words or live/derived values do not imply authored ownership. A visible/total count
makes an empty result explicit. Registered and fallback components expose stable
UI markers so filtering does not depend on guessed heading names.

Filters are local display preferences retained across actor selections and panel
refreshes. They write no project settings, overrides, history or Build input.
Reset restores all sections. Existing source/reference/actions and separate
retail/authored/live values remain in their sections; search does not decode or
rewrite them. This first workspace filter applies to actor component Inspectors.

Validation: focused identity/search checks, shared component renderer and asset
action checks passed. A private Town01 browser workflow verified authored-only
selection, ID search, empty results and exact Reset with unchanged component data,
history, dirty flag and source key. The source-editor action still focused the
wait family afterward; Undo/Redo presence and Save/Open passed. Screenshot inspected,
zero page errors. Evidence: ignored
`local-output/sdk-20260909/inspector-component-filter-20261004/parent/proof.json`.
No game launched; gameplay acceptance remains deferred.


## 2026-10-04: Component-directed script source navigation

Registered Inspector actions now carry their component identity to their existing
handler. Authored movement, flag, wait and model-selector actions open the source
editor and focus the matching operand-family section. Other script/dialogue and
asset actions retain their existing behavior. Navigation uses a fixed UI-section
registry, does not parse source IDs or infer execution, and sends no authored
command. Unknown or missing section targets receive no arbitrary selector focus.

Focused section/dispatch/asset checks passed. A private Town01 browser workflow
verified keyboard focus and visible wait targets, retail16 versus authored/effective17,
unchanged project state/history/source key, Undo/Redo presence and Save/Open, with
zero page errors. Screenshot inspected. Evidence: ignored
`local-output/sdk-20260909/script-inspector-navigation-20261004/parent/proof.json`.
The other three families have bounded section-registry coverage; gameplay remains
deferred. No game launched or physical Retail disc exported.


## 2026-10-04: Authored script components in the entity Inspector

Actors with authored movement, flag, wait or model-selector instruction overrides
now expose the corresponding SDK components to the shared Inspector. Each section
shows an authored instruction count, detached entries keyed by stable source
instruction identity, explicit semantic limits and a registered source-editor action.
Empty families are omitted. Undo/Clear removes the section; Redo/Save/Open restores
it with the project override. Source bytes and imported metadata remain separate.

These are readonly component summaries. Existing source editors retain qualified
retail/authored/effective operands and their native Apply/Clear/Build commands.
The common inspector does not parse MAN data, infer executed paths or write generic
component values. Movement height/behavior, flag story meaning, wait cadence and
model/animation rebinding remain unverified until appropriate gameplay acceptance.

Validation: six focused metadata checks cover all four families, detached data
and empty-component omission. Five existing movement/flag/wait project checks and
the common renderer/action checks passed. A private Town01 browser check opened
Actor0044's authored wait section and its source editor with retail16 versus
effective17, with unchanged authored state/history/source key and zero page errors.
Undo/Redo component presence and Save/Open passed; imported metadata stayed intact.
Screenshot inspected. Evidence: ignored
`local-output/sdk-20260909/script-component-inspector-20261004/parent/proof.json`.
No game launched. Browser workflow acceptance here covers waits; other families
have bounded metadata coverage and retain their existing source-editor workflows.


## 2026-10-04: Allocated assignment component inspector

The allocated initial-animation Inspector now uses the SDK component contract
for labels, properties, source witness details, notes and registered actions.
It exposes inherited/retained clip identity, record hash, captured model reference,
selector identity and explicit gameplay evidence status. The captured model uses
the shared reference-navigation adapter. **Manage allocated clips** is capability
and Edit gated; **Preview allocated initial animation** is available only for an
assigned retained clip and uses the existing readonly assigned-pose workflow.

The old ad hoc Inspector button handler is removed. Registered action dispatch
retains selection/source/busy guards, and management keeps the existing native
Review/Apply commands. No generic component writes or retail-format knowledge
were added to the property renderer. Specialized editor migration remains partial.

Validation: five focused SDK schema checks and the component-renderer/action
checks passed. Private Town01 browser verification covered the registered
assignment section, readonly assigned preview, library/content editing, one
reviewed Apply with reference updates, Undo/Redo, Save/Open and exact complete
normal Build ANM readback with original retail records preserved. A readonly
layout/navigation check verified that full hashes/model IDs fit their cells and
the captured-model link opens its asset details Inspector. Shared property styles
now wrap long code/reference values. Screenshots inspected, zero page errors.
Evidence: ignored `local-output/sdk-20260909/allocated-inspector-20261004/verified/`
(`proof.json`, `layout.log`, `wrapped-assignment.png`). No game launched or
physical Retail export; gameplay acceptance remains deferred.


## 2026-10-04: Retained animation output-frame timeline

**Edit retained content** now displays an **Output frame timeline**. Each cell
shows the output index, frozen donor index and authored-axis count for the selected
rigid object. Tooltips expose exact authored axes and total authored objects for
that frame. Repeated donor frames retain distinct output contributions. Authored
cells, the selected frame and the inclusive range have separate display cues.

Click selects an output frame and loads its channel fields. Shift-click extends
the range from the last clicked frame for reverse/repeat/remove/interpolation.
Navigation sends no API request and retains accepted Review if channel content is
unchanged. Pending operations disable navigation; stale context withdraws the
cells. Valid clips remain inspectable when their edit revision budget is exhausted.
Invalid mapping/range/object/channel data withdraws the timeline. Cells use
keyboard-accessible buttons, retain focus after navigation, and occupy a bounded
scroll region. No playback cadence or runtime state is inferred.

Validation: bounded timeline metadata and editor lifecycle checks pass repeated
donor frames, object-specific axes, 512-frame limits, no-request navigation,
review retention, exhausted-budget inspection and stale-source withdrawal.
Private Town01 browser checks pass click/Shift-click selection, channel loading,
range interpolation, readonly preview Return, assigned Apply, Undo/Redo and
Save/Open. Normal Build matches the complete candidate animation bank and preserves
every original retail record. Screenshot inspected, zero page errors. Evidence:
`local-output/sdk-20260909/retained-timeline-20261004/parent/proof.json` (ignored).
No game launched or physical Retail disc exported; gameplay remains deferred.


## 2026-10-04: Retained clip partial-axis interpolation

In **Edit retained content**, open **Frame sequence tools**, author the same
nonempty set of axes at two output frames for one rigid object, and choose
**Interpolate authored endpoint axes** over that inclusive range. Translation
rounds to source integers; rotation follows the shortest per-axis path modulo
4096 on the 16-unit grid. Half ties choose the larger integer and exact
half-turns choose the positive direction. This does not infer runtime timing.

Only the explicit endpoint axes are replaced within the range. Other authored
axes, other objects, frames outside the range and frozen donor mapping/capture
remain unchanged. Missing or mismatched endpoint axes, identical endpoint frames and
native budget violations reject without discarding an accepted Review. Staging
writes no project content; successful changes withdraw Review. The existing
native Review/pose/Apply workflow owns persistence and reference updates.

Validation: focused retained math/editor checks and the existing six-axis and
sequence checks passed. A private Town01 browser workflow verified five-frame
translation/rotation wrapping, retained unrelated contributions, range rejection,
readonly Review/pose Return, one Apply with assigned reference updates, Undo/Redo
and Save/Open. Normal Build decoded to the exact complete candidate ANM bank;
every original retail record remained intact. Screenshot inspected, no page
errors, game launches or physical Retail export. Evidence: ignored
`local-output/sdk-20260909/retained-interpolation-20261004/verified/proof.json`.
Gameplay cadence and rendering acceptance remain deferred.


## 2026-10-04: Retained animation frame sequence tools

**Edit retained content** now provides **Reverse selected frames**, **Repeat
selected frames**, and **Remove selected frames** for an inclusive output-frame
range. Authored partial translation/rotation channels follow their output frames,
including distinct edits on repeated donor frames. Repeats copy detached channel
values; the frozen donor capture remains unchanged. Empty clips, invalid ranges,
and native frame/channel budget overflow are rejected without losing a valid
review. Successful changes withdraw Review and require fresh Review before Apply.

These are local draft operations using the existing reviewed native ANM workflow.
Preview remains read only; Apply updates the retained record and its assigned
actor references together in one Undo entry. Gameplay timing and rendering
acceptance remain deferred.

Validation: focused sequence/editor checks and a private Town01 browser workflow
pass Review/pose Return/Apply, rejected all-frame removal, reference updates,
Undo/Redo and Save/Open. Normal Build decodes to the exact five-frame candidate
bank while preserving every original retail record. Evidence: ignored
`local-output/sdk-20260909/animation-sequence-tools-20261004/final/proof.json`.
No game was launched and no physical Retail disc was exported.


## 2026-10-04: Front and Side orthographic scene views

The existing Top/orthographic camera now also exposes **Front (X/Y)** and
**Side (Z/Y)**. Exact level views preserve target/scale. Right-drag pans on the
camera plane, including display Y, and scroll anchors the cursor's plane point.
A shared display-camera helper keeps axis orientation and overlay basis consistent.
Isolate selected temporarily shows one selected instance for unobstructed inspection;
Restore scene retains manual visibility/layers. Source changes/proposals withdraw it.
Saved views accept zero orthographic pitch and retain it through recall/history
and Save/Open; perspective keeps its existing minimum pitch. These camera actions
author no game transforms and do not infer unknown actor heights.

Six focused project tests and Node camera/source checks passed. Private Town01
browser verification covered all three GPU axis picks, Front/Side gestures,
cursor anchoring, saved recall, Undo/Redo and Save/reopen with unchanged imported
and authored game data/source keys and no page errors. Screenshots inspected.
Evidence: `local-output/sdk-20260909/scene-axis-views-20261004/integer-cursor/proof.json`.
Selected-instance isolation/restore, immediate post-selection availability and
representation reset passed with unchanged model/history/dirty/source state;
`isolation-proof.json` records the additional browser check.
No game launched; gameplay and runtime coordinate acceptance remain deferred.
See [saved scene views](legaia-saved-scene-views.md).


## 2026-10-04: Pick a native face from the authored scene

The main viewport now has **Pick model face**. One surface click resolves the
frontmost visible instance and triangle, selects its entity in the existing
Hierarchy/Inspector, and opens the corresponding Current native object/primitive.
Depth, hidden instances and texture-zero coverage participate in picking. Dragging
still orbits. Fresh source-key checks and exact native corner connectivity qualify
ownership, including supported posed geometry and complete object prefixes.
Retail comparison, live mode, pending proposals and conflicting tools cannot arm it.
Selection writes no model content; native changes retain the existing reviewed Apply.

Node ownership/lifecycle checks and private Town01 headless browser verification
passed, including readonly scene navigation, GPU overlap/transparency, combined
UV/material Apply, Save/reopen, Undo/Redo and exact model/TIM normal Build readback.
Evidence: `local-output/sdk-20260909/scene-face-picking-20261004/syntax-fixed/proof.json`.
Fresh ownership checks also passed for all 118 loaded Town01 model geometries
(29 posed, two complete object prefixes); `ownership-proof.json` records this.
No game launched. Runtime positions, visibility and gameplay remain unverified.


## 2026-10-04: Active native face outline

The model comparison now shows the selected native face's cyan boundary in both
Current and Proposed views. Outline selected native face can be toggled independently
of the yellow GLB face set. It preserves material fills, textures and geometry; a
quad's shared triangle diagonal is omitted. The caption identifies the native
object/primitive and states that hidden boundary edges are included. Picking,
corner fields and the UV workspace retain the same selection. The outline is
strictly display state and does not alter drafts, history, review hashes or Build.

Native ownership and one/two-triangle boundary checks passed, including quad
edge cancellation and malformed indices. The renderer caches only the boundary
buffer, refreshes it after vertex updates and releases it on disposal. Existing
face lifecycle and shared scene highlight checks passed. A private GPU test found
cyan boundary pixels while interior pixels and depth/transparent-texel picking
remained unchanged, with no WebGL error. Town01 browser selection/toggling stayed
readonly; UV dragging, scene comparison/Return, combined Apply, Undo/Redo, Save/Open
and exact normal Build model/TIM readback passed. Screenshot inspected:
`local-output/sdk-20260909/model-face-outline-20261004/parent/proof.json`.
No game launched; gameplay remains deferred and the full goal stays active.


## 2026-10-04: Direct native face selection in model comparison

Click a visible surface in either Current or Proposed model view to select its
native object/primitive. Existing corner fields, paging and the UV workspace update
together. A click retains the readonly comparison; selection changes no project
state. Pending face or texture-binding drafts must be applied/discarded first.
Dragging remains orbit; pointer cancellation does not select. Both decoded triangles
of a quad map to one native face. GLB selection highlights remain display-only.

The renderer now exposes a bounded single-model triangle picking pass. Material
batches retain decoded triangle IDs, and picking uses the ordinary depth test and
texture-zero discard. The normal entity picking path remains separate and tested.
Pick buffers/framebuffers are released through renderer disposal when the face
editor closes. Native layout/object/corner ownership is checked before selecting.
This selects unposed model faces; direct face editing from a placed scene is still
separate future integration, and runtime ownership is not inferred.

Focused ownership, face lifecycle and combined HTTP checks passed. A private GPU
proof selected the front surface, selected the surface behind a transparent texel,
rejected background/out-of-view clicks and restored ordinary entity picking with
no WebGL error. A Town01 browser selected native primitive 5 without authoring,
refused selection with pending drafts, then passed UV dragging, combined scene
comparison/Return, Apply/Undo/Redo/Save/Open and exact normal Build model/TIM readback.
Screenshot inspected; evidence:
`local-output/sdk-20260909/model-face-picking-20261004/parent/proof.json`.
No game launched; gameplay acceptance remains deferred and the full goal active.


## 2026-10-04: Native face UV workspace

The face editor now includes a 2D UV workspace with Current and Draft outlines,
numbered triangle/quad corners, a native byte grid and source-qualified static
texture crops after Preview. Drag a Draft corner to edit the same existing U/V
fields. Coordinates clamp to 0..255; vertex/color/normal/material drafts remain.
Dragging withdraws the accepted review and Proposed crop, changes no project state,
and requires Preview before Apply. Current's qualified crop remains readonly.
Ambiguous/missing texture evidence is labelled and does not display guessed pixels.
The existing numeric fields remain available, including coincident UV corners.

Focused Node checks passed corner/quad ownership, clamped pointer conversion,
detached pixel buffers and stale/duplicate/malformed/ambiguous texture guards. The
face lifecycle suite and five combined native/HTTP cases passed; HTTP serves the
new module. Private Town01 browser verification passed actual dragging and byte
field updates, readonly state, review invalidation, refreshed UV crops, combined
scene comparison/Return and one Apply/Undo/Redo/Save/Open/normal Build with exact
model/TIM readback. The workspace screenshot was inspected:
`local-output/sdk-20260909/model-uv-workspace-20261004/parent/qualified/proof.json`.
No game launched; live texture residency and gameplay acceptance remain open.


## 2026-10-04: Combined pending face/material scene comparison

The reviewed UV/face plus texture-binding draft can now be inspected in the authored
scene before Apply. The combined scene endpoint regenerates both native audits and
requires the accepted review key. Existing placement matrices, pose channels and
shared instance groups are retained; proposed crops/bindings are refreshed from the
verified texture catalog. Retained authored topology uses a temporary replayed
content ledger without publishing model files or history entries. The browser
checks the scene report against every accepted review metadata field before showing
Current/Proposed, isolation, optional GLB face highlights and Return to face editor.
Returning retains the accepted review and one combined model Apply.

Five focused native/HTTP tests passed, including two posed shared instances,
unchanged placements/source/history, exact final UV/material fields, invalid/stale
review rejection, and retained authored topology ledger composition. Existing face
lifecycle and shared scene highlight checks passed. Private Town01 browser proof
verified readonly scene comparison/isolation/Return, yellow display highlights,
combined Apply, Undo/Redo, Save/Open and exact normal Build model/TIM readback:
`local-output/sdk-20260909/model-texture-assignment-scene-20261004/parent/qualified/proof.json`.
The proof uses a non-overlapping static texture region and asserts both changed
materials resolve to the added texture. An earlier overlapping private test correctly
reported ambiguity; no upload ordering was inferred. No game launched. Static address
matching still does not establish live VRAM residency or gameplay correctness.
The earlier combined placed-scene-pending notes below are superseded.


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

## 2026-10-04: GLB image-to-native-face material selection

The material editor now offers **Select faces from GLB image**. Load an exact
Current SDK model GLB and its fresh binding JSON, qualify the image links, and
choose a material/channel/image. Qualification reruns the native GLB importer
and requires a byte-exact Current model roundtrip. Source-corner attributes
identify complete native faces independently of GLB draw-primitive numbering.
Choose a Current scene texture page separately, then **Use texture page for
GLB-selected faces** stages the page/depth/indexed-palette values in the existing
material drafts. Review, model/scene inspection, explicit Apply, and Undo retain
the existing material workflow. UVs and shared group blend drafts are retained;
other face drafts stay in place. Direct 16-bit assignment preserves the Current
CLUT word and removes obsolete pending CLUT coordinates.

A quad split across GLB materials, untextured native faces, more than 256 selected
faces/pending entries, stale bindings, or pending native model changes cannot stage.
GLB shader/image/UV/sampler properties never supply native page, palette or blend
addresses. Selection alone changes neither project nor history. This workflow
does not allocate native geometry, add texture slots, or convert image pixels;
those remain explicit existing tools.

Verification: three focused Python tests run the real GLB codec (indexed and
non-indexed corners), strict readonly HTTP qualification, client report validation,
draft preservation, split-quad and stale/changed-model rejection. The existing
Node material suite passed. A private Town01 headless browser test selected five
wall faces, staged an authored 16-bit checker page, invalidated/rebuilt material
Review, inspected Proposed in scene, and completed one model Apply and Save/reload.
Parent verification passed Undo/Redo, offline Open, stale binding rejection after
Apply, and normal Build package readback: exact authored TIM and exact five-face
model bytes, with neighboring decoded model bytes and Retail metadata unchanged.
Evidence: `local-output/sdk-20260909/model-glb-material-selection-20261004/parent/proof.json`.
No game launched; gameplay and live VRAM residency remain deferred.

## 2026-10-04: GLB image dependency views and retained image selection

Both embedded-PNG pickers now show which standard GLB material texture links use
the selected image: base color, metallic/roughness, normal, occlusion and emissive.
The readonly graph records material names/indices, channel roles, UV-set indices,
sampler references and GLB mesh/primitive uses. Shared images and unused materials
remain visible; images with no standard references are labelled accordingly. The
view presents up to 64 material links and 32 primitive uses per link, with complete
bounded graph evidence available below it. Names are displayed as text.

Authored-slot Load retained PNG/STP recipe freshly inspects the retained GLB and
restores its image selector. Another embedded image can be selected without an
external upload. This invalidates the earlier conversion/review, re-extracts exact
image bytes and carries the new image identity into the existing conversion and
source-retention workflow. Identical image bytes at another GLB image index still
require a fresh provenance review. Metadata-only source retention preserves Current
TIM and creates one Undo entry; native changes use the existing combined Apply.

The dependency report is display evidence, not native face, TPage, CLUT, UV, blend
or shader authority. Extension-owned references remain unresolved. URI images
are excluded and never fetched. Graph limits: existing 32 MiB GLB/64 images,
256 textures/materials/samplers, 1024 meshes, 4096 primitives, 2 MiB response.
Malformed references and over-budget graphs reject dependency inspection. Both
pickers visibly fall back to the separate strict PNG catalog, so unsupported mesh
or shader metadata does not prevent an otherwise qualified image extraction.
Abort propagates without a fallback request; invalid PNG catalogs still fail.

Qualification: seven focused Python cases across existing GLB texture import,
new graph/HTTP/Node decoder coverage and authored-slot GLB retention; three Node
suites for PNG editing, conversion and slot review. The final private browser
proof covers both pickers, retained graph reload, switching to an unused embedded
image with metadata Apply/Save/reload, unchanged native TIM, Undo/Redo, offline
Open and exact source snapshot retention. A final readonly pass covers graph
failure fallback and conversion plus zero URI requests. Evidence:
`local-output/sdk-20260909/texture-glb-dependencies-20261004/parent/qualified/proof.json`.

No game/installed runtime was launched or changed. Native material dependency
routing, broader GLB extension policy, general Retail mode/CLUT allocation, runtime
VRAM policy, scripting/scheduling, live scene identity/parity, world-map/MAPDSIP and
release/performance/gameplay acceptance remain open. The overall goal stays active;
manual gameplay checks can remain queued.

## 2026-10-04: GLB embedded images feed authored TIM conversion

Convert source PNG now accepts a bounded GLB and explicitly selected embedded PNG.
It reuses the existing readonly GLB catalog/extraction qualification; URI, JPEG and
unsupported image slots are excluded. Native bit depth, image/CLUT coordinates,
STP policy and optional STP plane remain explicit converter choices. No GLB shader
or material binding is inferred.

Review/Apply retain the full immutable GLB alongside PNG/STP inputs and the exact
TIM conversion recipe. The receipt includes GLB SHA/length, selected image index
and name, and embedded PNG SHA. Conversion and every retained-source read freshly
extract that image and check its bytes against the retained PNG. Review keys bind
this lineage; switching GLBs with identical image pixels still requires a fresh
review. All source files are preflighted before writes, and the project binding
and one combined Undo entry are published only after native/source qualification.

Save/Open, history and export-input snapshots preserve the source GLB. Download
retained image sources adds source.glb to PNG, optional STP and recipe downloads.
Load retained PNG/STP recipe restores GLB lineage too, so later native conversion
keeps the original source without another external file selection. Plain PNG
receipts remain compatible. Limits: 32 MiB per GLB, 64 MiB logical retained GLB
inputs per authored-slot project, existing 32 MiB PNG/STP project budget; only
participating conversion/slot commands accept the 68 MiB JSON transport envelope.

Focused qualification passed: nine Python cases across conversion, retention,
combined slot Apply and GLB sources; both Node decoder suites; synthetic raw and
compressed carrier readback, Undo/Redo, offline Open, snapshots, wrong/null/stale
selection and tampered file rejection. A fresh private Town01 browser run selected
an embedded PNG, converted RGB16 to indexed 4-bit, inspected Current/Proposed,
used combined Apply/Save/reload, restored GLB provenance and reproduced Current.
The normal package Build read back exact native slot 96. A separate readonly
browser pass checked exact PNG/STP/GLB/recipe downloads. Evidence:
`local-output/sdk-20260909/texture-slot-glb-20261004/parent/proof.json`.

Gameplay is still unverified. No game or installed runtime was launched/changed.
Still open: broader GLB/material dependency routing, general Retail mode/CLUT
allocation, runtime VRAM policy, scripting/scheduling, live scene identity/parity,
world-map/MAPDSIP and release/performance/gameplay acceptance. The overall SDK
goal remains active; manual gameplay checks can stay queued.

## 2026-10-04: reopen retained conversion inputs directly in the editor

For a saved slot with a source receipt, Convert source PNG now offers Load retained
PNG/STP recipe. It loads the immutable PNG and optional STP plane into the file
controls and restores the saved bit depth, image/CLUT coordinates and STP policy.
No external file selection or download/re-upload is needed. Loading is readonly;
it clears earlier drafts/reviews and requires Convert before using a draft.

The browser checks exact Current identity/context, source/recipe equality, PNG/STP
hashes and lengths, the recorded conversion report and Current TIM hash/header.
Saved JSON key order does not affect receipt comparison. Stale, missing, tampered
or mismatched inputs reject the load. Existing cancellation and busy-owner handling
prevent a closed or changed context from receiving delayed inputs.

Source and native choices remain editable after loading. Convert reproduces
Current with unchanged options, or creates a new complete TIM with changed options.
Use converted TIM draft goes through slot Review, Current/Proposed inspection and
combined native/source Apply, retaining the original inputs and updated recipe in
one Undo entry. Native material bindings remain an explicit separate edit.

Both Node decoder suites passed, including wrong context/identity, altered PNG,
missing STP, malformed receipts, Current TIM mismatch and reordered saved keys.
Private Town01 browser proof loaded PNG/STP without external file selection,
restored the recipe, reproduced Current exactly, changed RGB16 to 4-bit, passed
choice invalidation, readonly Review/pixels/Return and combined Apply/Save/reload.
Central checks passed Undo/Redo of content plus recipe, offline reopen, exact source
snapshot files and exact normal Build slot 96 readback. Parent visual inspection
covered the loaded reproduction dialog. Evidence:
`local-output/sdk-20260909/texture-retained-reload-20261004/parent/proof.json`.

Broader GLB/image dependencies, general Retail mode/CLUT allocation and runtime or
gameplay acceptance remain outstanding. No game was launched and no installed
runtime or physical disc was changed.

## 2026-10-04: combined converted TIM and source Apply

Use converted TIM draft now carries the exact PNG, optional STP plane and native
options into slot Review, Proposed pixel inspection and Apply. Review reproduces
the whole proposed TIM from those sources and includes the immutable source
receipt in its review digest. A mismatched or altered recipe, malformed source
fields, stale context or old review key rejects the operation before project state
changes. Converted command bodies are bounded at 24 MiB, each PNG at 8 MiB, native
TIM at 1 MiB, and retained slot sources at the existing 32 MiB project budget.

Apply retains the TIM and reproducible source receipt together under one binding
and one Undo entry, both for a new slot and for an edited saved slot. The persistent
UUID and native index remain stable. Undo/Redo restore native content and recipe
together; Save/reopen, retained-source downloads and input snapshots use the same
immutable source files. All source file targets are preflighted before writes.
Filesystem failures can leave unreferenced immutable files, but cannot publish a
partial project binding or history operation.

Manual TIM interchange continues to use the previous source-receipt preservation
and withdrawal rules. Pure source-receipt changes for an otherwise unchanged TIM
remain available through Review source retention / Retain reviewed sources; a
native no-op is not turned into an implicit Apply. The slot review identifies when
PNG/STP sources will be retained with the native edit.

Fourteen focused Python cases and both slot/conversion Node suites passed. Raw and
compressed construction checks covered combined append/edit, STP input retention,
readonly review/pixels, recipe-dependent stale keys, malformed/mismatched sources,
one Undo per Apply, snapshot inputs and native carrier readback. Private Town01
browser proof passed new 4-bit conversion/Apply, saved-slot RGB16 conversion/Apply,
review invalidation, readonly pixels/Return, Save/reload and normal Build assessment.
Central checks confirmed two combined history entries, recipe restoration on Undo,
offline reopen, exact PNG snapshot input, exact final slot 96 TIM in the normal
package and unchanged Retail TIM members. Evidence:
`local-output/sdk-20260909/texture-slot-conversion-apply-20261004/parent/proof.json`.

Broader GLB/image dependency integration, general Retail mode/CLUT allocation and
runtime/gameplay acceptance remain outstanding. No game was launched and no
installed runtime or physical disc was changed.

## 2026-10-04: retained PNG/STP sources and reproducible slot recipes

Saved authored slots can now retain their original PNG, optional STP plane and
conversion recipe. Open Edit authored texture slot, Convert source PNG, choose
the exact inputs and options, and convert. Review source retention is enabled
only when the draft reproduces Current TIM; Retain reviewed sources then adds one
metadata Undo entry. It preserves the native bytes, asset UUID and slot index.
Source or conversion choices invalidate retention review. Already-retained exact
inputs are a no-op and cannot be applied again.

Bindings have an optional source receipt with immutable PNG identities, lengths,
options and the conversion report. Each source is at most 8 MiB; retained sources
across slot bindings have a 32 MiB project budget. Save, offline Open, Current slot
reads and snapshot capture verify file hashes and reproduce the whole TIM exactly.
Missing/tampered files or inconsistent recipes fail closed. Snapshot inputs include
the exact PNG/STP files. Download retained image sources provides both inputs and
the recipe JSON after fresh Current/context/hash qualification.

Label-only edits keep the receipt. A TIM-content edit withdraws the old receipt;
Undo restores it. Immutable older files remain available for history. Source
retention is explicit and separate from the earlier native TIM Apply, so each
operation has its own reviewed history entry. Automatic retention during initial
conversion Apply and broader GLB/image dependency integration remain next work.

Twelve focused Python cases and both slot/conversion Node suites passed, including
recipe mismatch, stale context, no-op refusal, source tampering, receipt withdrawal,
history, offline Open and exact snapshot inputs. Private Town01 browser proof
passed conversion/retention review, invalidation, readonly inspection, metadata
Apply, Save/reload and exact PNG/STP/recipe downloads. Normal Build package readback
matched the unchanged slot 96 TIM; native identity, Undo/Redo and snapshot inputs
were checked centrally. Parent visual inspection covered the retention review.
Evidence: `local-output/sdk-20260909/texture-slot-sources-20261004/parent/proof.json`.

Gameplay, dynamic residency, upload order and STP blending remain unverified.
No game was launched and no installed runtime or physical disc was changed.

## 2026-10-04: source PNG conversion for new and saved authored slots

The slot editor now offers Convert source PNG. Its readonly conversion dialog
constructs a complete 4/8/16/24-bit TIM from bounded PNG samples with explicit
image/CLUT word coordinates and STP policy. Indexed output has one full local
palette using deterministic RGB5 median-cut; RGB16 uses nearest expanded RGB5
samples and RGB24 preserves opaque RGB8 samples. Partial alpha, incomplete native
words, unsupported PNG metadata and invalid placement fail before a draft returns.
Indexed CLUT origins must be 16-word aligned. No scaling, padding or placement is
inferred. An optional same-size black/white STP PNG overrides the default policy;
transparent/STP1 and opaque rounded-black/STP0 conflicts are rejected.

The dialog reports maximum/RMS RGB error, changed visible pixels, palette usage
and required black/transparent STP corrections. Source, plane or native choices
invalidate the conversion. Use converted TIM draft returns to slot Review and
Proposed pixel inspection; it does not apply to the project. The browser qualifies
source hashes, output TIM hash and native headers. Editing starts from Current
mode and coordinates. Existing reviewed Apply, history, Save/reopen and normal
Build deliver the resulting immutable TIM under the stable slot ID and index.

Ten focused Python checks and both slot/conversion Node decoder suites passed.
Independent packet expectations covered indexed nibble order, complete CLUTs,
direct RGB16/RGB24, binary alpha and separate STP; construction checks covered
quantization determinism, bounds and native pack delivery. Private Town01 browser
proof covered new 4-bit PNG conversion, draft invalidation, quantization inspection,
readonly draft/Review/pixels/Return, Apply/Save, saved-slot conversion to RGB16,
Current/Proposed comparison, second Apply and Save/reload/Build assessment. Normal
package readback matched final slot 96 exactly and every Retail TIM member stayed
unchanged. Undo/Redo and offline reopen passed. Parent visual inspection covered
conversion and comparison. Evidence:
`local-output/sdk-20260909/texture-image-conversion-20261004/parent/qualified/proof.json`.
The earlier failed resource-search harness attempt remains preserved alongside it.

Conversion evidence is available while drafting; original PNG/STP source retention
and a persistent conversion receipt remain next work. General Retail mode/CLUT
allocation, automatic material retargeting, dynamic residency, upload order, STP
blending and gameplay acceptance remain separate or unverified. No game was
launched and no installed runtime or physical disc was changed.

## 2026-10-04: authored slot editing and full TIM interchange

Saved authored slots now expose Edit authored texture slot and exact Current TIM
download. A complete TIM edit preserves the persistent asset ID and native slot
index, including when later authored slots exist in the same pack. Review checks
the Current content hash and project context, reconstructs the whole native pack,
and reports changes to mode, dimensions, palettes and VRAM placement. Static
footprint review excludes the old upload for the selected slot while retaining
other scene/authored/boot uploads and proposed image/CLUT intersections.

Current/Proposed pixel inspection is read-only. Current uses palette zero when
indexed; Proposed uses the selected local palette. File, name and overlap choices
invalidate review. Apply adds one Undo entry, retains the previous immutable TIM
for history, and refuses stale or unchanged proposals. Save/reopen and normal
Build use the existing authored slot collection; material bindings remain explicit
and must be reviewed again when mode, placement or palette addresses change.

Seven focused Python checks and the expanded Node decoder suite passed. Raw and
compressed construction checks covered editing a nonlast slot, mode/CLUT growth,
neighbor retention and history. Private Town01 browser proof passed Current
download, reviewed mode/palette change, Current/Proposed comparison, invalidation,
Apply, Save/reload and Build assessment. Normal package readback matched edited
slot 96 and unchanged slot 97 exactly. Undo/Redo and offline reopen passed; the
parent inspected the comparison screenshot. A final readonly browser check also
passed the edit labels, no-op refusal and reversed indexed/direct comparison. Evidence:
`local-output/sdk-20260909/texture-slot-edit-20261004/parent/proof.json`.

Gameplay/rendering, dynamic residency, upload order and STP blending remain
unverified. This implementation concerns authored slots; general Retail mode or
CLUT allocation and automatic image conversion remain separate work. No game was
launched and no installed runtime or physical disc was changed.

## 2026-10-04: saved TIM slots in resources and material assignment

Saved new TIM slots now appear in the active-scene resource catalog under their
persistent authored IDs and names. Current pixel previews qualify their native
pack receipts and retained files; Imported inspection rejects new slots because
there is no Retail counterpart. The texture dialog exposes inspection and
project history while hiding unsupported replacement/interchange actions.

The material texture picker includes the new slots and derives their qualified
page/depth and local indexed palette addresses. Existing primitive/group draft,
Review, Proposed scene inspection/Return and Apply workflows accept them. Current
scene/model catalogs include authored upload contributors; Imported scene views
exclude them. Cached previews reread retained authored files. Static overlapping
addresses keep the existing ambiguity rules; no upload-order inference is added.

Eight focused Python cases and the material-binding Node suite passed. Private
Town01 browser proof discovered and inspected a new 256×256 checker TIM,
selected its native page for five wall primitives, passed review invalidation,
readonly scene inspection/Return, one model Apply, Save/reload and normal Build
assessment. Independent packet masks matched the whole model candidate; relocated
package readback matched both the model and slot 96 TIM and preserved neighboring
decoded model bytes. Undo/Redo and offline reopen passed. Parent visual inspection
passed; a further readonly preview check covers the simplified authored-slot UI.
Evidence: `local-output/sdk-20260909/new-texture-material-20261004/parent/`.

Next: editing/interchange for saved new slots, broader source-image conversion,
VRAM placement and allocation policies. Runtime upload/residency, materials and
scene transitions remain queued for gameplay verification. No game was launched
or installed. The goal remains active.

## 2026-10-04: new TIM slot import editor

The texture resource dialog now opens **Import new texture slot** for its native
pack. Complete TIM files receive readonly placement/overlap review and Proposed
pixel inspection with an existing palette. File/name/overlap changes withdraw
the review; pixel Return retains it. One explicit Apply uses the exact reviewed
file hash/context, returns updated project state and creates one Undo entry.
Save/reload and normal Build preserve the slot. The resize decoder also accepts
qualified authored-slot identities in later overlap reports.

Four focused Python workflow cases and two Node suites passed. Private Town01
browser evidence passed file/review, blocked and accepted overlap choices,
review invalidation, pixels/Return, readonly project/history checks, Apply,
Save/reload and normal Build assessment. Independent package readback matched
the complete added TIM at slot 96; Undo/Redo and offline reopen retained it.
Parent visual inspection led to enlarging small Proposed images. Evidence:
`local-output/sdk-20260909/texture-slot-editor-20261004/parent/`.

Next: saved new-slot catalog/scene visibility, material assignment and content
editing, broader image conversion and automatic VRAM placement. No game was
launched or installed. Runtime upload/residency and appearance verification
remain deferred; the goal remains active.

## 2026-10-04: authored TIM slot persistence and normal Build

New TIM slots now have persistent `texture-new://` UUIDs, explicit native append
indices and hash-qualified Retail pack receipts. Readonly service Review
constructs the complete proposed pack with existing resize/payload edits and
reports known static image, flattened CLUT, authored-slot and boot overlaps.
One service Apply requires the current review and explicit overlap choice,
retains immutable TIM bytes and creates one Undo entry. Save/offline reopening
validate files, hashes, native TIM bounds, contiguous indices and pack receipts;
project input snapshots retain the TIMs. Scene and Build keys include additions.
Following resize reviews account for the new authored uploads.

Normal Build merges append, resize and ordinary member edits into one native
pack request, independently qualifies the source archive and audits each new
slot. Eleven focused Python cases passed. Private Town01 raw and Dolk2
compressed projects passed service Review/Apply, Undo/Redo, Save/reopen,
readonly normal Build assessment and actual package readback. Slot 96 and slot
50 respectively matched the complete added TIM; resized and payload-edited
neighbors matched too. Both reported one relocated texture pack. Evidence:
`local-output/sdk-20260909/texture-slot-project-20261004/parent/qualified/proof.json`.

The next integration is HTTP/editor import, pixel inspection, Current/Proposed
catalog/scene visibility and material assignment for new slots. Automatic VRAM
placement, broader source-image conversion and runtime upload/residency remain
unfinished. No game was launched or installed; gameplay verification stays
queued and the goal remains active.

## 2026-10-04: native TIM slot append allocation

The native allocator can append one to 128 complete TIM uploads to a qualified
raw or compressed texture pack, up to the existing 1024-slot limit. It expands
the native word-offset table while preserving existing slot indices, signature,
table gap, complete TIM bytes and opaque member tails. Existing qualified image
edits can share the same allocation. New TIMs carry explicit image/CLUT origins;
image bounds, flattened CLUT bounds and complete RGB24 pixels are checked.

Both physical archive rebuilders and the shared resource composer accept the
new addition requests, relocate following descriptors/sectors, and reopen the
result for exact pack/member readback. Nine focused Python construction cases
passed, including previous resize and fixed-payload growth checks. Private
Town01 raw and Dolk2 compressed archive proofs passed: 96 to 97 and 50 to 51
slots, preserving every original member and tail. Evidence:
`local-output/sdk-20260909/texture-slot-allocation-20261004/parent/proof.json`.

This is the native allocation foundation. New-slot project persistence,
Review/Apply, editor import/catalog controls and normal Build routing remain
unfinished. Automatic VRAM placement and overlap/residency acceptance are also
pending. No game was launched; runtime upload, material appearance, save/load
and scene-transition verification remain deferred. The goal remains active.

## 2026-10-04: scene texture assignment in the material editor

The material editor now browses freshly qualified active-scene TIM assets,
loads a selected Current texture/palette, and lists native page regions with
inclusive UV byte bounds. Saved texture allocations participate in that source
inspection. Copy a page binding into one textured primitive or its complete
textured packet group, then use the normal material Review, Proposed/scene
inspection and Return, and one explicit Apply. Indexed CLUT addresses are
qualified against the aligned flattened strip; direct 16-bit assignments retain
the model's CLUT word. UVs, geometry, normal references, group ABE drafts, ABR and
reserved source bits remain unchanged. Whole group copies retain other drafts
and reject batches over 256 entries without partial publication.

Validation passed three Node suites and 15 focused Python cases (14 synthetic
and one private Retail case). The private Town01 browser workflow loaded a
256×257 authored texture as two page regions, assigned its first page to five
wall primitives, and passed readonly catalog/source inspection, draft-copy
review invalidation, immutable scene inspection/Return, Apply, Save/reload and
normal Build review. Independent word-mask construction matched the complete
TMD candidate; runtime Undo/Redo and reopening retained it. Readback from the
combined relocated PROT package verified both the exact model candidate and
resized TIM, preserving neighboring decoded model bytes. Parent visual checks
passed. Proof-harness selector and carrier-span assumptions were corrected;
failed logs were retained. Evidence:
`local-output/sdk-20260909/material-texture-assignment-20261004/parent/`.
No game was launched.

See [the scene texture picker](legaia-material-texture-picker.md). This supplies
explicit existing texture address assignment beside texture resizing and UV
retargeting. New TIM slots, VRAM allocation, automatic atlas placement and
general external GLB material/image dependency import remain unfinished.
Runtime residency, texture windows, palette animation and final visual
suitability remain deferred gameplay checks. The full SDK goal stays active.


## 2026-10-04: reviewed UV rectangle retargeting

The model face editor now remaps an explicit Current UV rectangle into an
explicit target rectangle for one textured primitive or all textured faces in
its packet group. Inclusive byte endpoints support nearest-byte rounding and
reversed target axes. All selected corners must fit the source rectangle;
untextured faces are excluded and batches over 256 textured faces reject
without partial draft publication. Copy preserves the selected face's other
draft fields and all neighboring non-UV fields. It updates drafts only.

The existing source-qualified Preview, Current/Proposed models, scene inspection
and Return, one Apply, Undo/Redo, Save/Open and normal Build now carry the complete
UV batch. Changing rectangle controls withdraws review; Discard/Reset clears
neighboring batch drafts. Source packet/material ownership remains unchanged.
See [the UV rectangle workflow](legaia-model-uv-rectangle.md) for exact behavior.

Validation passed two Node suites and 17 focused Python cases (14 synthetic and
three private Retail cases). A fresh private Town01 browser workflow remapped
five wall primitives and passed review invalidation, immutable scene inspection /
Return, one Apply, Save/reload and normal Build review. Independent native byte
construction matched the candidate, Undo/Redo and reopening retained it, and
normal Build decompression/readback preserved every neighboring decoded byte
and the original compressed capacity. Parent visual inspection passed. Evidence:
`local-output/sdk-20260909/model-uv-rectangle-20261004/parent/`.
The initial browser harness had a wrong model-close selector; its failed log was
retained and the corrected complete run passed. No game was launched.

This connects explicit UV placement with the existing separate texture resizing
and source material editors. It does not infer image/material assignment, create
TIM slots or allocate VRAM. Automatic atlas placement and general imported
material/image assignment remain unfinished; final appearance, texture windows,
VRAM residency and palette animation remain deferred gameplay checks. The full
SDK goal remains active and incomplete.


## 2026-10-04: nearest-neighbor texture scaling

Resize image now offers **Crop and fill** and **Scale with nearest neighbor**.
Nearest scaling copies encoded source pixels at destination pixel centers using
integer mapping `floor((2*x+1)*source_width/(2*target_width))` (and the same
mapping for Y). Palette indices, complete PSX16 words including STP, RGB24
channel bytes, TIM mode, CLUT allocation and VRAM origin remain source-owned.
Nearest mode disables fill and requires its unused encoded value to be zero.
Changing methods withdraws the old review; method selection is bound into the
review key used by pixel inspection, scene inspection and Apply. Existing API
callers that omit `resize_mode` retain crop-fill behavior.

Validation passed 12 focused Python cases, the Node resize guard suite and an
additional high-bit/STP encoded-pixel check. A fresh private Town01 browser
workflow passed Review, overlap-choice invalidation, pixels/Return,
scene/Return, Apply, Save/reopen, Undo/Redo and normal Build review. Independent
native readback verified every scaled row and the exact delivered TIM in the
normal Build package. Parent visual inspection passed. Evidence is retained at
`local-output/sdk-20260909/texture-nearest-resize-20261004/parent/`.
No game was launched. Runtime appearance and upload-order verification remain
in the deferred gameplay queue. Scaling does not retarget model UVs, introduce
new TIM slots, change texture depth or implement VRAM placement planning.
The overall SDK goal remains active and incomplete.


**2026-10-04 — reviewed texture resizing in the editor:** The selected texture
Inspector now offers **Resize image**. It loads an exact current native source,
reviews width/height and encoded fill, shows added/removed pixels and native byte
lengths, and lists new overlap with known static scene/CLUT/boot uploads. Changing
dimensions, fill or the explicit overlap choice withdraws the review. A no-op or
unacknowledged new overlap cannot Apply. Native mode, image origin and CLUT layout
remain fixed; this workflow does not resample or retarget UVs.

The same source-qualified review drives side-by-side Current/Proposed pixel
inspection, an immutable scene texture proposal with Return to resize review,
and explicit Apply. Pixel inspection keeps the selected palette and qualifies
both PNG dimensions. Scene proposals reuse the texture inspection path already
used by PNG edits. Pending reads can be closed/aborted without publishing; stale
project, scene, mode or source disables the review. Apply is one Undoable edit,
followed by ordinary Save/Open and normal Build. Cropping back to the exact Retail
TIM clears the override as one Undoable edit rather than retaining a no-op binding.

Twenty focused Python checks passed, followed by four targeted checks including
exact Retail restoration; three Node suites passed for source/audit qualification,
review withdrawal, source changes, Apply and close/abort/busy ownership. A private
Town01 browser smoke passed source/review, overlap-choice invalidation, pixels/
Return, scene/Return, unchanged authored state during proposals, Apply, Save/reload
and normal Build review. The saved texture passed Undo/Redo, reopen and exact
normal-Build readback. A separate read-only PNG scene/Return regression passed
through the shared proposal integration. Evidence:
`local-output/sdk-20260909/texture-resize-editor-20261004/parent/`.
No game, installed runtime change or physical disc export ran.

The existing-TIM resize workflow now includes native allocation, project history,
Save/Open, following PNG/JSON/TIM editing, reviewed editor proposals and normal
Build. Broader allocation remains unfinished: new TIM slots, mode/CLUT growth,
VRAM origin planning, UV retargeting and general imported material/image assignment.
Runtime appearance, upload order/residency, UV coverage and scene transitions are
still deferred gameplay checks. The full SDK goal remains active and incomplete.

**2026-10-04 — resized-texture interchange and comparison reports connected:**
Saved image allocations now support current PNG export/reimport, PNG pixel
proposals and Apply, effective indexed JSON, and TIM/JSON file proposals.
Following payload edits preserve the saved dimensions and allocation binding.
Resized JSON uses `legaia.indexed-texture.v2` with both exact current TIM and
Retail source hashes; changing either hash, layout or current content requires
a fresh export. Existing fixed-layout JSON v1 remains supported.

Retail comparisons explicitly fit Retail pixels into the proposed dimensions,
preserve their top-left overlap, and zero-fill newly added pixels. Reports retain
the true Retail hash, identify the separate comparison baseline hash and count
added/removed pixels. Payload counts describe that baseline; they do not count
removed pixels as remaining source data or conceal a resize as a payload-only edit.
The PNG and file preview UI qualifies and labels this distinction. Current-to-
proposed payload counts remain exact and gate PNG Apply/no-op behavior.

Twenty-one focused Python checks and two Node suites passed. A private Town01
browser smoke passed resized PNG review, pixel inspection/Return, Apply, Save/
reload, JSON v2 file preview/Apply and Save. The saved result passed read-only
normal Build review and exact native texture readback from normal Build. The
new static comparison module was initially absent from the server allowlist;
that registration was corrected before the successful browser smoke.
Evidence: `local-output/sdk-20260909/texture-resize-interchange-20261004/parent/`.
No game, installed runtime change or physical disc export ran.

**Next:** editor resize controls and current-to-proposed resize pixel/scene
inspection using the reviewed allocation request. The resize service, history,
Save/Open, normal Build and following interchange paths are connected; the
complete editor resize workflow is still pending. Runtime appearance, UV coverage,
VRAM upload/residency and transition checks remain in the deferred gameplay queue.
The broader SDK goal remains active.

**2026-10-04 — saved texture resize bindings and normal Build (service stage):**
Reviewed native image resizing now has project Apply, one-step Undo/Redo and
Save/Open. The versioned `tim-image-layout-v1` binding retains the Retail TIM
hash and exact authored image layout; ordinary uploads cannot change dimensions.
Review is read-only and binds the current source, encoded fill value and explicit
potential-overlap choice. The footprint census includes effective scene images,
flattened CLUTs (including the edited texture's CLUT) and known boot uploads.
Only overlap added by the new footprint is reported. This census does not prove
runtime residency, upload order or material suitability.

Normal Build merges resized and fixed-layout edits sharing a pack into one
qualified raw/compressed allocation. Source slots, unedited members, opaque
member tails and physical neighbors retain the native allocation guarantees.
Build audits identify image allocations separately from payload-only edits.
Effective texture/scene previews and palette, pixel and rectangle commands
understand saved allocations; pixels outside the Retail image have no Retail index.
Resizing withdraws an earlier GLB image receipt rather than retaining stale provenance.

Thirty-one focused construction checks passed, followed by thirteen targeted
checks after report guards and added-pixel editing were refined. Private Town01
raw and Dolk2 compressed projects passed Review/Apply, history, Save/Open,
read-only Build review and exact normal-Build readback, including a neighboring
payload edit in the same allocated pack. Town01 allocated one extra PROT sector;
Dolk2 retained physical capacity. Private evidence:
`local-output/sdk-20260909/texture-resize-project-20261004/parent/`.
No game, installed runtime change or physical disc export ran.

**Remaining before the complete resize workflow:** editor resize controls and
reviewed pixel/scene proposals, plus allocation-aware PNG/JSON/TIM-file comparison
reports. Those report paths explicitly reject saved resized bindings for now;
normal native TIM publication and Build work. The HTTP service endpoints are
available without advertising a finished editor capability. Runtime appearance,
UV coverage, upload overlap/residency and scene transitions remain deferred.
This is an implementation milestone, not completion of the SDK goal.

**2026-10-04 — native texture image-allocation groundwork:** Added source-bound
TIM resizing for 4/8/16/24-bpp images. It keeps overlapping encoded pixels, fills
new pixels with an explicit encoded value and supports cropping without resampling.
Flags, pixel mode, CLUT headers/count/layout and image VRAM origin remain fixed;
new dimensions must contain whole native words and fit VRAM. The constructor
preserves the complete CLUT payload. The allocation validator also permits ordinary
palette/image payload edits while keeping the allocation's structural constraints.

Existing pack slots remain stable while their word offsets are rebased. Unedited
TIMs and each member's opaque tail remain byte-exact; additional alignment bytes
are audited. Standalone raw and compressed descriptor packs rebuild inside unique
physical PROT owners. Compressed decoded-size fields and later descriptor offsets
are updated; smaller raw allocations retain physical capacity. Both allocation
paths now participate in the shared resource composer with exact final readback.

Twenty-four focused Python construction checks passed, covering all four modes,
fill/crop/no-op behavior, typed and stale-source guards, alignment, raw/compressed
carriers, both PROT header positions and existing model/texture/animation Build
regressions. Private Town01 raw and Dolk2 compressed probes verify resized native
TIMs, all unedited members, opaque tails, neighbors and exact shared-composer
output. Evidence: `local-output/sdk-20260909/texture-layout-allocation-20261004/parent/`.
No project Apply, resized-texture normal Build collection, browser authoring, game,
installed runtime or physical disc export ran.

**Still required for the resized-texture workflow:** versioned project bindings,
Review/Apply/history/Save/Open, static footprint/conflict reporting, composition
with subsequent palette/PNG edits, normal Build collection and editor comparison
controls. These codecs do not establish safe upload ordering, material/UV matching
or runtime rendering. This stage is not ready for manual gameplay acceptance; the
existing fixed-layout texture workflow remains the supported editor path. The
full SDK goal stays active.

**2026-10-04 — compressed texture carrier growth in normal Build:** Layout-compatible
TIM edits no longer fail normal Build solely because their compressed pack exceeds
the original consumed stream span. Source-qualified TIM packs now join the existing
model/animation/MAN relocation pipeline. Decoded member offsets, TIM headers,
dimensions, CLUT/image VRAM rectangles and lengths remain fixed. The transform
preserves compressed-stream trailing opaque bytes, rebases later descriptors and
relocates the unique physical PROT owner with exact neighbor readback. Shared
model/texture growth composes in one carrier, and source-addressed overlays apply
before relocation. Legacy fixed-span texture export keeps its original limit.

Build review and the saved Build report expose relocation package bytes, PROT
growth bytes and rebuilt texture-pack count. Review table hashes wrap within the
dialog. Thirty-seven focused Python construction checks and two Build-review Node
suites passed. Checks include both PROT header positions, shared model/texture
growth, opaque-tail preservation, malformed candidates/source rejection, normal
Build review without writes, exact native package readback and existing texture
Build guards. Private Dolk2 browser workflow passed Preview/Return, Apply,
Save/reload and normal Build review. Undo/Redo, Save/Open and normal Build deliver
exactly the selected 32,832-byte texture; PROT grows 24,576 bytes. Private evidence:
`local-output/sdk-20260909/texture-compression-growth-20261004/parent/`.

This does not allocate new textures, resize TIMs, move VRAM or establish runtime
upload/rendering acceptance. No game, installed runtime or physical disc export
ran. Gameplay remains deferred; the full SDK goal remains active.

**2026-10-04 — original GLB recovery for legacy texture receipts:** The texture
Inspector now offers **Retain original GLB source** for older four-field image
receipts. Review verifies the exact recorded GLB hash, embedded PNG hash, image
index/name and current texture/source context without writes. Retain archives the
original file and upgrades its receipt in one Undo step; the native TIM remains
byte-for-byte unchanged. Save/Open, project-copy source capture and normal Build
use the retained bytes. Changed files, stale reviews and repeated Apply reject.
The action does not reconstruct the old palette/STP import recipe or establish
runtime texture acceptance. The duplicate 24 MiB PNG request cap was removed so
the intended 68 MiB combined GLB/PNG/STP envelope is effective.

Validation: 22 focused Python checks passed, including HTTP review/Apply guards,
Undo/Redo, Save/Open, source capture and browser response qualification. A private
Retail-derived browser smoke passed Review, file-change invalidation, Retain,
Save/reload and exact GLB download; native Build readback remained identical to the
pre-upgrade TIM. Evidence: `local-output/sdk-20260909/texture-source-backfill-20261004/parent/`.
No game launched; gameplay verification remains deferred.

**2026-10-04 — retained texture GLB import sources:** New GLB-image Applies
now retain the exact original GLB in `Authored/TextureSources/<sha256>.glb` and add
its bounded byte length to the source receipt. The embedded PNG remains recoverable
from that original file. Source writes precede override publication and share the
normal single Undo step. Unreferenced content files remain available to Undo.

The texture Inspector offers **Download retained GLB source**. The server verifies
size, digest and exact image identity; the browser verifies the returned receipt,
texture context and byte hash before download. Project reopen, Build and input
snapshots verify retained files; project copies include them and their copy/history
validators recognize the new content-hash path. Old four-field receipts remain
readable but do not claim retention or enable recovery. No source file is reconstructed
from quantized TIM pixels, and no GLB material assignment is inferred.

Twenty-nine focused Python construction checks, PNG lifecycle and project-copy Node
checks passed. Exact source recovery, source-copy/export inclusion, legacy receipt
compatibility and same-size corruption rejection are covered. Actual private Retail
Town01 browser workflow applies, saves/reloads, downloads the original GLB exactly,
and re-imports its image as a no-op review. Undo/Redo, Save/Open and normal Build
read back the exact candidate TIM; other CLUT rows, STP and imports remain unchanged.
Screenshot inspected. Private evidence:
`local-output/sdk-20260909/texture-glb-retained-source-20261004/parent/`.
No game, installed runtime or physical disc export ran. Original external STP files
and external GLB dependencies are not separately archived. Existing input-copy
byte/file limits remain. Gameplay is deferred; the full SDK goal remains active.

**2026-10-04 — persistent verified GLB image provenance:** Applying an
extracted GLB PNG now saves a source receipt with the native TIM override: GLB
SHA-256, input PNG SHA-256, image index and image name. Review, pixel/scene preview
and Apply re-extract the exact selected GLB bytes and require equality with the
submitted PNG. The receipt participates in the review key, so a plain-PNG review
cannot authorize a GLB-sourced Apply. Browser response qualification independently
matches the receipt to its extracted image.

Undo/Redo and Save/Open preserve the receipt. The reopened texture Inspector
shows both complete source hashes and the image identity. Later native edits or
ordinary replacements clear the receipt instead of misattributing changed content;
Undo restores it. Build uses the shared project texture validator and includes the
receipt in its texture audit. The native TIM payload is unchanged by metadata.
The original GLB/PNG files are not archived; the saved receipt identifies the
verified input, rather than providing those original bytes or a material assignment.

Seventeen focused Python construction checks and the existing PNG lifecycle suite
passed. Forged selections, removed provenance, typed identity errors and stale
review keys reject without publication. Actual private Retail Town01 browser
workflow extracts/reviews/inspects, applies, saves, reloads and displays the receipt;
Undo/Redo, Save/Open and normal Build independently read back the exact native TIM.
Other CLUT rows, STP and imported metadata remain unchanged. Screenshot inspected.
Private evidence: `local-output/sdk-20260909/texture-glb-provenance-20261004/parent/`.
Only the private project was authored; no game, installed runtime or disc export ran.
Gameplay remains deferred and the full SDK goal stays active.

**2026-10-04 — GLB strip connector compatibility:** Mesh import now omits
repeated-index connector triangles in `TRIANGLE_STRIP` sources. Original strip
parity is computed before filtering, preserving each drawable triangle's winding.
Inventory, section ranges and the 128-face native transaction budget count drawable
triangles. Each strip is bounded to 16,384 source indices. All indices are still
validated; connector-only strips and real triangles collapsed by native rounding
reject. Triangle-list/fan behavior, donor bindings and native layouts are unchanged.

Eight focused construction checks passed: source parity equals an explicit triangle
list, long connector sequences do not consume native face capacity, invalid/collapsed
sources reject, Review stays read-only, Undo/Redo and Save/Open preserve the candidate,
and normal Build reads back its exact native payload. Actual Retail Town01 editor
smoke qualifies an eight-index connected strip as two triangles, reviews it through
the existing native donor workflow and inspects Current/Proposed. Screenshot inspected;
project, history and saved files unchanged, no Apply or Run. Private evidence:
`local-output/sdk-20260909/glb-strip-connectors-20261004/parent/`.
Gameplay/culling acceptance remains deferred; full SDK coverage remains unfinished.

**2026-10-04 — prepared native texture inputs:** After **Prepare PNG export**,
**Use prepared binding and STP** now fills both native source inputs directly from
the qualified export. The chosen edited PNG remains, including an extracted GLB
image. The action replaces the binding and STP inputs, clears an unavailable STP
plane, and withdraws the previous review. This removes the download/re-upload
round trip while preserving explicit Review and Apply. Source/context, busy and
stale gates also govern prepared inputs.

Existing PNG lifecycle checks passed with focused additions for missing PNG,
retained image identity, review invalidation, stale context and a direct-color
export without STP. An actual Retail Town01 browser smoke prepared the export,
used its binding/STP, extracted a GLB PNG, reviewed and inspected pixels, returned,
reused prepared inputs and restored a cleared STP plane. Screenshot inspected;
no Apply or Run. Saved project/import data, authored state and history stayed
unchanged; the ordinary export artifacts were written beneath `Exports`.
Private evidence: `local-output/sdk-20260909/texture-prepared-source-20261004/parent/`.
No native codec or Build change; previous exact TIM Build proof still applies to
the shared pipeline. Gameplay remains deferred and the full SDK goal stays active.

**2026-10-04 — embedded GLB PNG source handoff:** The existing texture PNG
editor now accepts a bounded GLB and explicitly selected embedded PNG image.
Read-only inspection lists source image indices, names, dimensions and byte hashes;
extraction rechecks the exact GLB/image hashes and PNG structure/CRC. URI, JPEG
and extended image slots are excluded without fetching external content. Malformed
embedded PNG ranges or payloads reject. Limits: 32 MiB GLB, 64 image slots,
8 MiB PNG, 2,097,152 decoded pixels per image.

**Use embedded PNG** fills the ordinary edited-PNG input and displays both source
hashes. Supply the existing native binding JSON and optional STP plane; the normal
palette conversion, Review, Current/Proposed pixels, scene proposal, explicit Apply,
Undo/Redo and Save/Open paths remain in charge. Selecting another source/image
withdraws review. No GLB material, UV, sampler, shader or automatic texture assignment
is inferred. This replaces an existing fixed-layout TIM; new texture allocation
remains unfinished. The saved native binding records PNG provenance, not a persistent
GLB material association.

Fourteen focused Python construction checks and the existing PNG browser lifecycle
checks passed. An actual Retail Town01 editor smoke used the real resource refresh
and texture card, extracted/reviewed the image, inspected pixels, returned with the
file retained, and verified source/selection review invalidation without Apply or Run.
Screenshots inspected; project files, authored state and history unchanged by that
browser smoke. A subsequent private native Apply/Undo/Redo/Save/Open and normal Build
read back the exact TIM package payload with other CLUT rows and STP unchanged.
Private evidence: `local-output/sdk-20260909/texture-glb-20261004/parent/`.
No game launched; appearance, live upload and hardware blending remain deferred.
The full SDK goal remains active.

**2026-10-04 — larger GLB inventories with bounded imports:** File inspection
now qualifies each static section independently, reusing one parsed GLB and scene
ownership graph. A scene may expose up to 128 qualified sections, each within its
existing 128-triangle geometry limit, with up to 16,384 inventory triangles. This
is read-only inventory; it does not allocate one oversized native mesh.

Single all-section import and atomic donor mapping still require at most 128
selected triangles per transaction. The single dialog explains oversized complete
scenes and keeps section selection/donor mapping available. The batch dialog shows
the selected triangle budget and disables Review and Select all when over budget;
the native service and browser qualifier independently enforce the same limit.
Ten focused construction checks passed. A 144-triangle source qualifies as two
72-triangle sections; full import rejects, a subset publishes in one history entry,
Save/Open preserves it, and normal Build reads back the exact native candidate.
Malformed sections remain rejected. Actual Retail editor smoke loads a 153-triangle
inventory and reviews its explicit 1/17 subset, blocks a combined 144-triangle
mapping and reviews its 72-triangle subset, then verifies the existing scene/Return
workflow. Screenshot inspected; authored state/files unchanged, no Apply or Run.
Private evidence: `local-output/sdk-20260909/glb-large-inventory-20261004/parent/`.
No larger native allocation, malformed-section bypass, maximum-load performance
acceptance or gameplay appearance is claimed. The full SDK goal remains active.

**2026-10-04 — selective GLB section donor mapping:** **Map section donors**
now offers **Import this section**, **Select all sections** and **Clear selection**.
Choose 1–16 qualified source sections; unchecked rows keep their choices but
allocate no geometry. Files with at most 16 sections start with all selected.
Larger inventories start unchecked and require explicit selection, allowing a
bounded subset from a file that previously exceeded the batch section count.

Native mappings retain unique increasing source primitive IDs, including gaps.
Review records exact selected/skipped IDs, and browser qualification matches each
step against its original section's count, node ownership and UV inventory.
Selection changes withdraw Review; donor/UV/replacement controls are disabled for
unchecked rows. The complete selected mapping still publishes as one Undo entry.
Six focused construction checks passed, including sparse 0/2 selection, a single
section from a 17-section inventory, exact normal Build readback, Save/Open,
Undo/Redo, invalid selections and changed-selection rejection for identical bytes.
Actual Retail editor evidence:
`local-output/sdk-20260909/glb-section-selection-20261004/parent/`. The smoke reviews
an explicit 1/17 subset and a 0/2 subset of three hierarchy sections, inspects the
scene and returns with skipped choice, donors, scale and UVs retained. Selection
and clear/all controls withdraw Review. Screenshot inspected; authored state and
saved files unchanged, no Apply or Run. Whole-file inventory qualification bounds
remain; skipping cannot bypass malformed or unsupported source geometry.
Gameplay appearance remains deferred and the full SDK goal remains active.

**2026-10-04 — explicit GLB source units:** Static mesh import now offers
**Native units per GLB unit**, default 1. A finite positive factor from 0.000001
through 1000000 scales baked positions and node translations together before
signed native rounding. Normals, UVs, colors and winding retain their existing
conversion. File inventory qualifies at the chosen scale, allowing a smaller
factor to recover an oversized mesh without editing the external file.

Changing scale withdraws Review immediately and requalifies the selected scene,
retaining UV/section choices. Single import, atomic donor mapping, scene proposals
and Apply bind the same optional `source_scale`; older callers remain at 1.
Eight focused checks passed, including scaled hierarchy coordinates, exact normal
Build readback, one Undo/Redo entry, Save/Open, typed/range/degeneracy guards,
changed-scale HTTP rejection and distinct review keys for identical rounded bytes.
Actual Retail editor evidence:
`local-output/sdk-20260909/glb-source-scale-20261004/parent/`. The browser smoke
recovers a large single-scene mesh at a smaller scale, withdraws its review on
change, retains mixed UV mappings and the scale through scene inspection/Return,
and checks desktop/narrow comparison bounds. Screenshot inspected; authored files
and history unchanged. No Apply or game launch occurred. Runtime coordinate
parity and native appearance still require deferred gameplay checks; the full
SDK goal remains active.

**2026-10-04 — static scene import from mixed GLBs:** Static mesh qualification
now resolves bounded animation channel targets instead of rejecting every GLB
with an animation or skin table. The entire selected node hierarchy must stay
static and unskinned, including its parents. Other scenes may contain animation
and skin records; their payloads are excluded, not decoded or imported. Unknown,
missing, extended or invalid target ownership rejects qualification. Existing
static-only imports retain their previous reports.

Optional `static_scope` records selected nodes, animated nodes and excluded clip/
skin counts. Browser qualification checks typed, disjoint ownership and mesh
ancestry; atomic donor mapping requires matching scope in inventory and every
native step. Both import dialogs explicitly display the excluded-data counts.
Ten focused construction checks passed, including exact normal Build readback,
one Undo/Redo entry, Save/Open, changed-target review rejection even with identical
candidate bytes, ancestor/skin guards and malformed activity bounds. The actual
Retail editor smoke rejects an animated default scene, selects a static hierarchy,
reviews mixed UV donor mappings and returns from scene inspection with choices
retained. Screenshot inspected; project files/history unchanged, no Apply or Run.
Private evidence: `local-output/sdk-20260909/glb-static-selection-20261004/parent/`.
No immediate gameplay verification is required for source selection; final native
appearance remains deferred. General animated/skin import and the full SDK goal
remain unfinished and active.

**2026-10-04 — donor mapping beside the mesh comparison:** The batch GLB
mapping dialog now places its section controls alongside the Current/Proposed
comparison. The section list scrolls independently, keeping Review, Apply and
scene inspection actions visible. Narrow windows stack the panes within the
window width. Existing review invalidation and scene inspection/Return behavior
remain intact; the preview also retains its keyboard focus outline.

Two focused UV mapping construction checks passed. The actual Retail editor
browser smoke verified desktop canvas/action bounds, narrow-window bounds,
Current/Proposed switching and retained mixed UV choices after scene inspection
and Return. Visual screenshots were inspected. Private evidence:
`local-output/sdk-20260909/glb-donor-layout-20261004/parent/`.
Authored project files and history stayed unchanged; no Apply or game launch was
performed. This editor layout change needs no immediate gameplay verification.
The full goal remains active, with native gameplay checks deferred.

**2026-10-04 — per-section UV channels in atomic donor mapping:** Each row in
**Map GLB section donors** now offers its own **Source UV channel**. The file/import
choice seeds all rows; **UV channel for all sections** resets them together. Rows
can then select different channels (for example, UV1 for one section and UV0 for
another) while preserving a single Review, Apply and Undo entry. Mapping payloads
bind each exact optional `uv_set`; older mappings without it use the batch default.
Native preparation and browser review validate typed row choices, and changing any
row invalidates Review. Scene inspection and Return retain each row's choice.

Seven focused construction checks passed, including mixed native UV1/UV0 packet
values and exact normal Build readback, Save/Open, one Undo/Redo entry, changed-row
HTTP rejection, invalid/null row guards and identical-candidate review-key binding.
Private actual Retail editor evidence:
`local-output/sdk-20260909/glb-section-uv-channels-20261004/parent/`. The smoke reviews
mixed row choices, inspects them in the scene and returns with both retained; a row
change disables Apply. Authored files/history stay unchanged. Source texture/material
assignments are still explicit native donor choices; gameplay remains deferred.
The full goal remains active.

**2026-10-04 — source UV channel selection:** Static mesh import now offers
**Source UV channel**, default `TEXCOORD_0`, populated from the selected scene's
qualified section inventory. Standard consecutive channels 0 through 7 are
supported, including normalized unsigned byte/short accessors as well as float
UVs. Single/selected/group imports, atomic donor batches and scene proposals bind
the chosen channel. Changing it invalidates Review; mapping and Return retain it.
A source-scene change resets the channel to UV0. Missing selected UVs retain donor
values; untextured donors ignore UVs. Reviews state consumed textured-face counts.
The browser verifies channel availability/range ownership and native conversions.
Native texture bindings and Current UV regions remain; source images/material
`texCoord` assignments and wrapping are not imported automatically.

Ten focused construction checks passed, including normalized UV0/UV1, exact native
UV packets after normal Build, Save/Open, mixed missing-channel sections, atomic
HTTP Apply/Undo/Redo, changed-choice rejection and forged browser DTO rejection.
Private actual Retail editor evidence is under
`local-output/sdk-20260909/glb-uv-channels-20261004/parent/`: UV1 is carried through
Review, donor mapping, scene inspection and Return, and changing it disables Apply.
That read-only smoke preserves authored files/history; gameplay remains deferred.
The full goal remains active.

**2026-10-04 — recover unsupported GLB default scenes:** The editor now reads
an independent, bounded scene catalog before qualifying mesh geometry. A default
scene with an unsupported native transform or geometry can fail qualification
while **Source GLB scene** remains available. Choosing a usable scene reuses the
same file bytes/hash and performs fresh native qualification. Catalog DTOs state
`geometry_qualified=false`; labels/roots alone never enable Review or Apply. The
client checks chosen-scene inventory against the original catalog. Catalog HTTP
requests accept file bytes only and publish no model/history/files.

Eight focused construction checks passed, including unsupported-default recovery,
HTTP request guards, forged catalog rejection, read-only state/file checks,
selected-scene Apply/Undo and existing scene-selection/RGB/Build workflows. Actual
Retail editor evidence: `local-output/sdk-20260909/glb-scene-catalog-20261004/parent/`.
The smoke keeps the rejected default visible, selects a usable hierarchy, reviews
and inspects it, and returns with the review/donor choices intact. Gameplay remains
deferred; the full goal remains active.

**2026-10-04 — choose a static GLB source scene:** Mesh import now supports
bounded files containing several static scenes. **Source GLB scene** starts at the
file's declared default (or first scene when unspecified). Choosing another scene
refreshes section inventory, resets primitive selection and invalidates Review.
Empty scenes remain selectable in the read-only inventory, with Review/Apply
unavailable; a usable scene can be chosen without replacing the file. The selected
scene index, root/name inventory and node ownership travel through single/selected
imports, atomic donor batches, full-scene proposals and Return. Review keys bind
scene choice even when two scenes produce identical native model bytes. Other
source scenes are not imported by that transaction. Single-scene imports retain
their existing default behavior. Static-only and native allocation bounds remain.

Fifteen focused construction checks passed, including malformed scene/index guards,
shared nodes across scenes, empty inventory, changed-choice HTTP rejection, one
Undo, Redo, Save/Open and exact normal Build model bytes. The actual Retail editor
smoke selected a usable hierarchy from an empty default, switched scenes, reviewed,
inspected Current/Proposed and returned with scene/donor/RGB choices retained.
Private evidence: `local-output/sdk-20260909/glb-source-scenes-20261004/parent/`.
No authored state, saved files or history changed in that smoke. Gameplay remains
deferred, and the full goal remains active.

**2026-10-04 — optional GLB material RGB baking:** Static imports now offer
**Bake opaque material RGB factors**, default off, in single/selected/group imports
and atomic section-donor batches. Standard `baseColorFactor` RGB multiplies linear
`COLOR_0`, using white when vertex colors are missing. Textured unlit native
packets receive modulation RGB (neutral 128); untextured unlit packets receive
sRGB display bytes. Lit packets ignore RGB and reviews state the consumed face
count. The browser independently checks source colors, factor/range ownership,
linear products and existing native conversions. Review keys, Apply and scene
inspection bind the option even when lit native bytes match the default result.
Nonopaque alpha, malformed factors and material extensions reject before Apply.
Native texture/material bindings remain; no new images or PBR shading are imported.

Twelve focused construction checks passed, covering exact packet RGB and normal
Build readback, multi-section atomic HTTP Apply, rejected changed choices, one Undo,
Redo, Save/Open and malformed review DTOs. Private actual Retail editor evidence is
under `local-output/sdk-20260909/glb-material-colors-20261004/parent/`; its lit donors
exercise review/scene/Return and report zero consumed RGB faces. This does not prove
Retail RGB appearance. Gameplay remains deferred; the full goal remains active.

**2026-10-04 — static GLB child hierarchies:** Mesh source ingestion now
qualifies a bounded forest, rejects cycles/multiple parents/duplicate children and
roots with parents, and traverses selected roots depth-first in declared child
order. Transform-only group nodes are supported. Each mesh section carries its
root-to-node path and composed world matrix; native positions and inverse-transpose
normals are baked from that full matrix. TRS-valid parent/child composition may
introduce shear, which is retained in the composed bake instead of decomposed or
dropped. Local sheared matrices remain unsupported. Node paths appear in section
and donor-mapping labels and are qualified through Review/scene inspection.

Twelve focused construction checks pass, including independent inherited position
and normal expectations, composed shear, ancestry/forest rejection, browser DTO
forgery rejection, one-step history, Save/Open and exact normal Build model bytes.
An actual private Retail editor smoke loads two child mesh nodes under a translated,
nonuniformly scaled parent, maps distinct native donor objects, inspects the scene
and returns to the retained paths/mappings. Authored files/history remain unchanged;
no browser Apply, Save or Run occurs. The 64-node/mesh, 128-section and existing
native allocation limits remain; batch mapping still admits at most16 sections.
This bakes static geometry into existing native objects, not game parenting, rigs,
skinning, animation or arbitrary material/image allocation. Gameplay stays deferred
and the full solo SDK goal remains active.

**2026-10-04 — multiple static GLB mesh roots:** Mesh import now enumerates the
sole scene's ordered static root mesh nodes, including distinct meshes and shared
mesh instances. Each node's transform is baked independently; vertex ownership
includes node identity, preventing accidental merging of shared accessors across
instances. Global section ordinals retain node, mesh and source primitive IDs plus
transform evidence. The file selector and donor-mapping rows expose Node/Mesh
labels. Single-section and batch Review qualify these bindings against the file;
canonical single-node imports retain their earlier contract.

Nine existing transform/import/batch checks and seven source/group construction
checks pass. New checks cover root order, shared accessor isolation, source
selection, duplicate/invalid roots and child rejection, forged source ownership,
one-step history, Save/Open and exact normal Build readback for distinct meshes.
An actual private Retail editor smoke loads two transformed mesh nodes, maps the
sections to distinct native donor objects, inspects all scene instances and returns
to the retained mapping. Authored files/history remain unchanged; no browser
Apply, Save or Run is issued. Limits remain one scene, 64 declared nodes/meshes,
128 source sections and existing face/vector/group budgets (16 sections per batch).
Only selected scene roots are instantiated; unused resources are not guessed into
geometry. Child hierarchies, skinning, morphs, animation, arbitrary images/material
allocation and gameplay parity remain unfinished. The solo SDK goal stays active.

**2026-10-04 — static GLB node transforms:** Static mesh import now bakes the
sole node's translation/rotation/scale or column-major affine matrix before native
coordinate rounding. Normals use the inverse transpose followed by Y reflection
and Q12 normalization. Negative determinant mirrors combine with Y reflection to
preserve oriented triangle winding and matching UV/color/normal corners. Identity
imports retain the existing geometry contract. Nonidentity reports retain the
matrix, determinant, normal matrix and winding choice, qualified by browser DTOs
and the source GLB hash. Batch sections require the same file transform evidence.

Twelve focused checks pass, including independent TRS/matrix equivalence,
nonuniform normals, mirrored corner order, malformed/singular/sheared/overflow
rejection and existing import/normal/batch workflows. A subsequent four-check
construction run verifies transformed batch DTOs and forged-normal rejection,
one-step history, Save/Open and exact normal Build model readback. An actual
private Retail editor smoke loads a rotated/mirrored/nonuniform GLB, maps its two
sections to distinct native objects, inspects the combined scene and returns to
the retained review. Authored files and history remain unchanged; no browser
Apply, Save or Run occurs. Native units, one mesh node, no hierarchy/skinning/
morph/animation and existing allocation budgets still apply. Gameplay stays
deferred and the full solo SDK goal remains active.

**2026-10-04 — atomic multi-donor GLB sections:** Import GLB mesh now opens
Map donors for all sections. Each of 1–16 source primitives chooses a Current
native triangle donor and can explicitly replace its donor group. Sections create
independent native packet groups in their respective donor objects. Shared donor
groups cannot also be replaced. The SDK composes qualified intermediate ledgers
in a detached in-memory view; Review writes nothing and Apply publishes the final
candidate with one Undo entry. The full mapping/file/source is review-bound.

Four focused construction checks pass: chained browser DTO qualification and
forgery rejection, distinct-object group replacement, stale HTTP Apply rejection,
atomic HTTP Apply/history, Save/Open and exact normal Build model readback, plus
single-section compatibility. An actual private Retail browser workflow maps two
sections to donors in different objects, Reviews, inspects all supported scene
instances, toggles isolation/Current/Proposed and returns to the retained mapping.
A second Retail browser smoke changes both distinct-group replacement choices,
invalidates the prior review, and retains the re-reviewed replacement proposal.
Authored files and history remain unchanged; no Apply, Save or Run occurs in that
browser smoke. Source material names label sections; existing native bindings
supply materials. New images, packet families, rigs and arbitrary material
allocation remain unfinished. Gameplay remains deferred and the solo SDK goal
is active.

**2026-10-04 — source GLB primitive selection:** Import GLB mesh now offers
All primitives or one explicit source primitive. A native-qualified file inventory
shows source material slots/names and triangle counts. Only the selected section's
positions, faces and display attributes enter the native donor transaction; its
source index is bound into Review and rechecked by scene inspection and Apply.
Changing the section invalidates the review. Default whole-mesh behavior remains.

Seven focused checks pass, including source inventory/selection bounds, stale
selection rejection without mutation, browser DTO qualification, one-step
Undo/Redo, Save/Open and exact selected-model readback in a normal Build package.
An actual private Retail editor workflow reviewed four triangles from two source
sections, selected Trim, re-reviewed two triangles, inspected the proposal in the
full scene and returned to the retained selection. The browser issued no Apply,
Save or Run; authored inputs and history stayed unchanged. Source material names
identify GLB sections; native donor bindings still supply materials. This does
not implement arbitrary material/image allocation or a multi-donor batch. Gameplay
remains deferred and the full solo SDK goal remains active.

**2026-10-04 — actual Retail GLB scene inspection:** Mesh import inspection now
starts with its affected instances isolated, so surrounding scene geometry does
not obscure the reviewed proposal. The isolation control reflects the retained
inspection state; users can restore the full scene and compare Current/Proposed
without losing the mesh review.

A real private Retail V7 project passed the native source, Review and full scene
proposal HTTP endpoints without substituted scene geometry. The actual editor
browser smoke loaded 261 scene meshes and two supported model instances, exercised
isolation and Current/Proposed switching, and returned to the retained mesh review.
Screenshots verified visible inspected instances. Six focused scene/group checks
also pass. Authored files, project inputs and undo/redo history stayed unchanged;
no Apply, Save or Run was issued by the browser smoke. This establishes editor
inspection usability, not runtime coordinate or gameplay parity. Manual gameplay
remains deferred and the full solo SDK goal remains active.

**2026-10-04 — prefixed PROT export delivery:** The experimental parent
export now parses the composed archive's actual PROT header location and passes
it into the MAN batch rebuild. The deferred compressed scene path no longer
rejects the native-supported prefixed header. The selected-scene direct writer
already carries its qualified header offset.

Twelve focused checks pass, including synthetic physical-disc output/reopen with
a 2048-byte PROT prefix for model/ANM/MAN growth and raw ANM/MAN growth, plus
existing unprefixed, no-ledger, routing and export completion checks. Exact final
payload and preserved-neighbor checks remain in those construction smokes.
Routing-only fixtures explicitly substitute native archive-header parsing; the
physical-disc checks use real native transforms and writer. No physical Retail
disc export, game launch or installed-runtime modification occurred. Gameplay
stays deferred and the full solo SDK goal remains active.

**2026-10-04 — model topology in experimental archive export:** Export now
prepares source-qualified model-growth requests, keeps their authored pack members
out of each scene's fixed-layout model serializer, and composes model and ANM
growth after original-address asset patches. The selected single-scene shortcut
cannot bypass model topology delivery. Scene audits retain delegated model IDs.
After all MAN rebuilds, final model readback qualifies each unique physical owner,
TMD descriptor and decoded pack against its expected native candidate hash.
Malformed, duplicated, aliased, wrong-type or mismatched candidates reject.

A read-only Retail Town01 smoke passes eight NPC additions, retained ANM
allocation/shared axes/initial selector and a TMD face addition together, with
exact final MAN, ANM and authored model bytes and unchanged project/history.
Fifteen focused checks pass, including synthetic physical-disc output/reopen with
MAN/ANM/TMD growth in a shared owner, model/MAN delivery without an ANM ledger,
existing raw chunk orders, multi-scene routing and native final model verification
at original/prefixed PROT headers. No physical Retail disc was exported, game
launched or installed runtime changed. Gameplay remains deferred and the full
solo goal stays active. [NPC guide](legaia-npc-build-candidates.md).

**2026-10-04 — model topology and NPC Build composition:** Normal Build now
hands NPC preparation the exact authored model identities already owned by its
qualified model-growth requests. The NPC scene serializer handles remaining model
edits and records same-scene delegated identities; the parent delivers those
models through relocation with final native pack readback. The default NPC path
does not suppress model serialization. Unknown, malformed, duplicate and oversized
handoff identities reject before scene preparation.

A Retail Town01 construction smoke passes read-only review and actual format-7
package readback with eight donor NPCs, a retained animation capture, shared ANM
axes, an allocated initial selector and a TMD face addition together. Final MAN,
ANM and authored model bytes match their candidates exactly; source directory
coordinates identify the model slot even when imported metadata lacks pack_slot.
Project overrides, model bindings and history stay unchanged. Eleven focused
checks pass, including explicit/default handoff ownership, standard model-growth
packaging and synthetic MAN/ANM/TMD growth in one descriptor table, both MAN/ANM
orders and both PROT header positions, with neighboring patches retained.
No game, physical Retail disc export or runtime installation change occurred.
Gameplay verification stays deferred and the full solo SDK goal remains active.
[NPC guide](legaia-npc-build-candidates.md).

**2026-10-04 — compressed NPC growth in normal Build:** Donor NPC candidates
that exceed their original consumed compressed MAN stream now enter normal Build's
format-7 relocation package. Candidates that fit retain fixed-span delivery.
The source-qualified request identifies the physical owner, descriptor table and
MAN descriptor, verifies native MAN structure and exact LZS readback, and composes
with ANM growth in the same table. Final composition verifies the exact MAN bytes
after all resource growth. Existing actor-pool and imported-source checks remain.

Retail Town01 eight-donor batches pass inclusive read-only Build review and actual
package readback, both alone and with retained animation allocation, shared channel
edits and an allocated initial selector. Authored inputs and history stay unchanged.
Sixteen focused composition/guard regressions and six existing MAN container/archive
checks pass. Synthetic shared-table cases cover both descriptor orders, original
and prefixed PROT headers, preserved neighboring edits and malformed/stale request
rejection. The editor NPC review contract passes. No game, physical Retail disc
export or installed-runtime modification occurred. NPC runtime allocation,
spawning, scheduling and script behavior remain deferred gameplay checks. The full
SDK goal remains active and solo. [NPC guide](legaia-npc-build-candidates.md).

**2026-10-04 — streaming NPC candidates in normal Build:** Qualified raw MAN
append now enters normal Build's format-7 relocation package. The native composer
accepts one MAN and one ANM growth request in a shared raw physical owner, remaps
headers in operation order and reads back both exact final payloads. Fixed-span
compressed NPC delivery remains available; oversized compressed candidates remain
unsupported. Raw MAN growth also rejects changed declared opaque neighbors,
including odd-sized payloads overlapping a rewritten header.

Retail dolk2 smoke passes inclusive read-only Build review and actual package
readback with NPC append, retained animation allocation, shared axes, allocated
initial selector and existing actor placement. A separate NPC-only raw Build
passes exact package MAN readback. Fifteen focused native/carrier/export/guard
checks and both editor Build-review contract suites pass. Source NPC allocation,
spawning, scripts and scheduling still need deferred gameplay acceptance. No
game, physical Retail disc export or installed-runtime change was performed.
The full solo goal remains active. [NPC guide](legaia-npc-build-candidates.md).

**2026-10-04 — managed raw streaming experimental export:** Raw scene
preparation now composes retained allocated initial MAN assignments with donor NPC
append. Shared channel edits enter the expanded ANM bank once. Experimental archive
export remaps MAN headers after ANM growth and ANM headers after MAN growth using
completed, typed native relocation audits, then verifies the exact final bank.
Unmanaged allocation still rejects rather than silently omitting it.

A read-only Retail dolk2 smoke passes frozen capture, shared axes, allocated
assignment and NPC append together, with exact final MAN/ANM bytes and unchanged
project/history. Ten focused regressions pass, including two synthetic physical
disc exports covering both chunk orders, retained neighboring edits, exact reopened
bank/MAN payloads, stale disc rejection and damaged bank metadata rejection.
No physical Retail disc was exported, game launched or installed runtime changed.
Streaming NPC append in normal Build remains pending. Gameplay verification remains
deferred; the full SDK goal stays active and solo. [Guide](legaia-animation-allocation.md).

**2026-10-04 — raw streaming allocated ANM in normal Build:** Source-bound
animation growth now prepares raw type-5 chunk requests as well as compressed
bank requests. The archive composer applies guarded MAN/asset overlays at original
addresses before raw ANM growth, relocates the unique physical owner and verifies
the final bank after all resource composition. Raw owners accept one unambiguous
ANM request and cannot mix descriptor-table resource relocation in the same owner.
Scene/chunk offsets, payload length/hash and native bank contents must agree with
fresh imported evidence. Editor allocation/library/assignment Build capabilities
now include this qualified raw path rather than reporting it unavailable.

A Retail dolk2 normal Build smoke passes capture allocation, current shared axes,
allocated initial MAN assignment and placement together. Read-only Build review
succeeds; the actual format-7 package reopens with the exact expanded bank and
MAN payload, native selector, placement and fresh readback audit. Ten focused
native composition regressions and two editor lifecycle suites pass. Compressed
carrier Retail regression also passes, including allocated NPC composition and
rejection of unqualified raw metadata before package output. No game was
launched, Retail disc exported or runtime installation changed. Streaming NPC
addition in normal Build and managed raw streaming experimental export remain
separate pending integrations. Gameplay stays deferred and the full solo goal
stays active. [Guide](legaia-animation-allocation.md).

**2026-10-04 — native raw streaming ANM growth foundation:** A source-qualified
codec now grows a word-aligned type-5 animation bank inside a complete terminated
DATA_FIELD chain, preserving the native bank's existing records/table padding,
opaque chunks, prefix and suffix. It records following chunk relocation and can
rebuild the unique physical PROT owner with whole-sector TOC relocation and exact
reopened bank/chunk verification. Stale hashes/locators, malformed chains, wrong
types, shrinkage, alignment failures and changed opaque neighbors reject. Declared
neighbor payloads are checked too: truncated word traversal must not silently
change an odd-sized payload that overlaps the rewritten ANM header.

Two focused synthetic native checks pass for no-op identity, allocation growth,
opaque preservation, both MAN/ANM chunk orders and explicit locator remapping;
MAN-first and ANM-first operations produce identical final archives. Twelve
existing streaming/bank/archive regressions pass. No proprietary disc output,
game launch or installed-runtime change was performed. This is native delivery
infrastructure: raw-bank SDK request routing, managed streaming actor assignment
and final locator remapping still need integration, so the raw ANM Build/export
restriction remains. Gameplay stays deferred and the full solo goal stays active.
[Guide](legaia-animation-allocation.md).

**2026-10-04 — allocated animation delivery in experimental disc export:**
The project exporter now routes scenes with `AnimationRecords` through managed
ANM delivery, including the single-selected-NPC path. Existing allocated initial
assignments can be serialized with appended NPC MAN records instead of hitting
the old normal-Build-only restriction. Source-addressed asset patches are composed
first, qualified compressed ANM banks relocate once, then MAN owners rebuild.
Final verification reopens every bank after all MAN relocation and compares its
complete bytes to the qualified candidate. Export checks the disc identity again
between scene preparation and bank preparation, and publishes no success on a
changed source or failed final readback.

A synthetic SDK routing/archive/disc smoke passes shared-owner ANM growth plus
native NPC append, preserved authored neighbor patch, exact final bank/MAN bytes,
unchanged source disc and reopening a newly written Mode 2 disc. It rejects changed
bank metadata and disc identity. Nine focused archive/routing/export regressions
and four allocated-MAN/assignment composition checks pass. The synthetic smoke
substitutes source preparation; it does not establish a Retail full-disc export or
gameplay acceptance. No Retail disc was exported, game launched or install changed.
Raw streaming ANM relocation, multiple-table owner remapping and broader SDK work
remain. Gameplay stays deferred and the full solo goal remains active.
[Guide](legaia-animation-allocation.md).

**2026-10-04 — retained GLB content interchange:** Actor inspector →
Manage allocated clips → Edit retained GLB now exports the saved rigid clip and
its current capture/source binding, downloads both files, reviews externally
edited channels with an explicit captured-donor output mapping, previews the
proposed pose and applies it. Repeated mappings can grow or shorten retained
content without inventing opaque native data. The saved UUID and donor remain;
content hash and referring initial assignments update in one ordinary Undo entry.
STEP/LINEAR/CUBICSPLINE sampling and native quantization reuse the existing codec.
File/binding/mapping/source changes reject stale Review; no-op imports add no
history. Retired captures remain retired. Mesh changes are not imported.

The Retail HTTP workflow verifies unchanged roundtrip, three-to-four frame
content growth, exact proposed pose, read-only Review/Preview, wrong binding/file/
key rejection, atomic Apply/Undo/Redo, Save/Open and normal Build review. The
existing allocated export regression passes for saved, retired, proposed and
assigned representations, including encoding-time source change. Three focused
editor regressions pass. Private Edge smoke verifies exact GLB/binding downloads,
file selection, four-frame Review/Preview Return, mapping invalidation and Apply
with no page errors; form/pose screenshots were inspected and staging stopped.
No game was launched or installed. Retail playback timing and gameplay acceptance
stay deferred; raw streaming ANM relocation, full-disc allocation export and
broader SDK work remain. The full solo goal stays active.
[Guide](legaia-animation-allocation.md).

**2026-10-04 — retained animation content editor:** Actor inspector →
Manage allocated clips → Edit retained content now opens a source-qualified form
for captured-donor frame mapping and per-frame, per-object integer translation
and rotation axes. Review shows the proposed frame count and affected initial
actor references. Preview opens the actual reconstructed proposed pose over
Current geometry and returns to the same reviewed draft; explicit Apply updates
content and references together. Changing the draft or source invalidates Review.
Retired clips stay retired, and an exhausted revision budget is read only.

Focused editor checks cover exact requests, provenance/reference qualification,
invalid axes, draft/stale/close/late-response guards and Preview Return. The Retail
HTTP workflow passes including normal Build review, atomic Undo/Redo and
Save/Open. Private Edge smoke passes four-frame Review/Preview/Return/Apply and
verifies the new retained hash and actor reference with no page errors; screenshots
were inspected and the staging server stopped. No game was launched or installed.
Allocated GLB content import and broader bank relocation remain work. Gameplay
acceptance stays deferred; the full solo goal remains active.
[Guide](legaia-animation-allocation.md).

**2026-10-04 — retained animation content editing APIs:** Source-bound
Review/Pose/Apply can now replace a retained clip's captured-donor frame mapping
and integer channel axes while preserving its UUID, donor snapshot and retirement
state. Native reconstruction qualifies the new record and expanded bank. Every
referencing initial assignment is requalified and receives the new record hash
in the same ordinary multi-entity Undo entry as the ledger. No-op Apply adds no
history. Stale keys and invalid mappings/quantization reject before publication.

The Retail workflow verifies proposed pose, read-only Review/Preview, exact Apply,
atomic content/reference Undo/Redo, Save/Open and equivalent reconstructed banks,
no-op/stale rejection and editing a retired clip without restoring it. Reopened
assigned content also goes through normal Build review. Unapplied edit previews
cannot fall back to exporting a Retail clip. Editor editing forms and allocated
GLB import remain next; this is API infrastructure, not their completed workflow.
No game was launched or installed. Gameplay stays deferred and the full solo
goal remains active. [Guide](legaia-animation-allocation.md).

**2026-10-04 — retained allocated clip GLB export:** Saved active or retired
clips, reviewed initial-assignment proposals and current allocated assignments
now export their own posed frame or full rigid clip through
`/api/export/allocated-animation`. The server reconstructs the exact retained
record over Current geometry, enforces scene/source identity and proposal Review,
and checks the source again after encoding before publishing. No client geometry,
Retail selector substitution or caller output path is accepted. Audits and GLB
extras retain the UUID/hash, representation and caller-selected rate.

Retail HTTP checks pass for each representation, repeated frame/channel mapping,
unchanged project/history, invalid/stale inputs and encoding-time source change
with no published file. Three focused editor suites pass. Private Edge smoke
exported saved pose, saved full clip and proposed full clip, verified embedded
retained identity, unchanged project and no page errors; the export dialog was
visually inspected and staging server stopped. Allocated GLB import/content
editing, raw ANM relocation and full-disc allocation export remain work. No game
was launched or installed; gameplay stays deferred and the full solo goal active.
[Guide](legaia-animation-allocation.md).

**2026-10-04 — allocated clip/NPC Build composition:** Normal Build now combines
allocated initial animation assignments with appended source-qualified NPC MAN
records. Native qualification rebases audited initial header bytes through the
reparsed original actor identity after partition offsets move. New NPC donor
copies retain their Retail initial clips. The expanded ANM bank and current
shared channel changes are composed once by the parent Build path; NPC preparation
consumes that managed bank without emitting duplicate equal-span ANM patches.

All eight focused native, composition, NPC carrier and Retail package checks pass.
Independent combined-package readback recovers the exact expanded bank, allocated
selector 70 on the original actor and one appended NPC with its donor's original
clip. Existing source capacity, descriptor ownership, actor-pool qualification,
compression and exact MAN readback gates remain in force. Raw streaming ANM
relocation and experimental full-disc allocation export remain implementation
work. No game was launched or installed; spawning, scripts, animation cadence
and lifecycle remain deferred gameplay checks. The full solo goal stays active.
[Guide](legaia-animation-allocation.md).

**2026-10-04 — allocated initial assignment editor controls:** The actor inspector
now opens Manage allocated clips directly. The library filters retained captures
by the actor's exact inherited model, separately offers lifecycle changes, and
supports initial assignment Review, proposed posed Preview with Return, explicit
Apply and Review/Apply clear. Review exposes stable clip identity, current native
selector, Build support and gameplay limits. Assigned identity/hash/model remain
visible in the actor inspector. Proposal/assigned clip exports reject instead of
exporting a different Retail clip.

Focused editor checks cover provenance, exact Review and posed identity, Apply,
clear, retained Return and stale source rejection, alongside the existing library
lifecycle checks. The private Retail-backed Edge smoke passed Review, three-frame
posed Preview/Return, Apply and clear, with disabled exports and no page errors.
Review and pose screenshots were visually inspected. Gameplay remains deferred; no user game is launched or installed. Raw ANM
relocation and joint appended NPC MAN composition remain implementation work.
The full solo goal stays active. [Guide](legaia-animation-allocation.md).

**2026-10-04 — allocated initial assignment Build delivery:** Normal Build and
read-only Build review now compose retained clip assignments into fixed-layout
MAN headers and deliver them with the expanded compressed ANM bank. UUID/hash
resolve to current native selectors; allocated headers use exact donor/model
qualification and reject overlapping header edits. Existing position and script
edits share the normal source-bound serializer. Final MAN decode must match the
complete composed candidate; archive readback checks the expanded bank.

Retail package readback recovered the exact bank and the assigned selector after
another retained clip was retired. Synthetic composition checks preserve placement
and reject overlap. Assignment persistence/clear checks remain supported. Editor
assignment controls are next. Raw ANM relocation and combining allocated headers
with appended NPC MAN records remain explicit blockers, rather than silently
omitting assignments. No game was launched; runtime selection, scripts, cadence
and lifecycle remain deferred gameplay verification. The full solo goal is active.
[Guide](legaia-animation-allocation.md).

**2026-10-04 — persistent allocated initial actor assignment:** Source-bound
Review and explicit API Apply now store an `ActorAllocatedAnimation` component
using scene, retained UUID, record hash and exact model identity. Native selectors
are resolved afresh rather than persisted. Apply/clear use ordinary Undo/Redo;
Save/Open validates associations after all ledgers are loaded, including offline
metadata-only Open. A referenced clip cannot be retired or removed, and conflicting
appearance changes roll back without altering history.

Assigned clip Preview and scene frame zero use the captured record over Current
geometry. Observer correlation retains imported candidates without claiming an
allocated effective runtime match and invalidates cached observations on Apply,
replacement or clear. Imported GLB export/recapture reject while
this assignment is active instead of silently using a different clip.

29 distinct focused checks pass, covering persistence, stale Review rejection, reference guards,
scene pose, clear/Undo and malformed saved bindings. Normal Build explicitly
blocks allocated actor assignments pending MAN header composition; active
unassigned compressed banks remain supported. Editor assignment controls and
Build delivery are still implementation work. No immediate gameplay check is
needed, no game was launched, and the full solo goal remains active.
[Guide](legaia-animation-allocation.md).

**Allocated initial clip assignment — native/read-only review stage (2026-10-04):**
A saved clip UUID now resolves to its current active bank ordinal for a reviewed
MAN header proposal. Native checks prove the donor/model/channel layout, reject
aliased actors and byte-selector overflow, and patch only initial model/animation
header bytes. SDK review/pose APIs bind actor, record/hash, bank and current source
key; exact captured model identity is required. Pose uses Current geometry.

Synthetic native checks pass. The Retail review test confirms an allocated
selector rebases from 71 to 70 after another clip is retired while UUID/hash stay
unchanged, and stale pose reviews reject. This remains read-only infrastructure:
assignment Apply, persistent actor component, scene integration, normal Build
header composition and editor controls are not implemented yet. No gameplay is
required now or claimed verified. [Guide](legaia-animation-allocation.md).

**Expanded ANM bank delivery (2026-10-04):** Normal Build/review now deliver active
allocated clips in qualified compressed type-5 scene carriers. Shared channel
edits are composed once with frozen captures. The carrier updates decoded size,
grows compressed slots as needed, rebases descriptors/PROT starts and enters the
existing format-7 relocation package. Model and ANM growth may share one table.
Retired clips remain metadata-only; allocated clips are still unassigned.

Synthetic codec/composition, actual Retail package readback, generic package
consumers and related ledger/pose/model-growth checks pass. The Retail package
contains the exact 70-record composed bank with one capture retired and later
shared edits included. Editor capability labels now advertise compressed delivery.
Raw streaming banks and multiple distinct tables in one physical owner remain
explicit unsupported relocation cases. Content editing and actor assignment are
still unfinished; no game was launched or runtime acceptance claimed. No immediate
manual gameplay check is required. [Guide](legaia-animation-allocation.md).

**Saved allocated clip library (2026-10-04):** The actor editor now lists active
and retired allocated captures, previews their exact retained records against
Current donor-model geometry, and reviews/applies retirement or restoration.
Retired clips remain inspectable without being restored. Returning from the model
viewer retains selection and lifecycle Review; source/selection/late/close guards
protect Apply. Unsupported exports are disabled and clips remain unassigned.

Focused Node checks and two Retail HTTP checks pass, including Save/Open, frozen
transforms after shared donor edits and Current geometry. An actual Edge editor
smoke passed active/retired Preview, retained Return and retirement/restoration
with identical UUID/hash and no page errors; screenshots were inspected. Saved
content editing, assignment and native Build relocation remain unfinished. No
immediate gameplay verification is required. [Guide](legaia-animation-allocation.md).

**Allocated clip creator and posed Review (2026-10-04):** The actor animation
editor now creates independent clips from explicit source-frame sequences, with
bounded ranges/repetition/reversal, source-bound Review, posed Preview and explicit
Apply. Preview reconstructs the exact allocated record over Current authored
geometry; Return retains the reviewed sequence. Stale/late/closed work is guarded.
Proposals are labeled unassigned, and unsupported allocated exports are disabled.

Focused Node lifecycle/provenance checks and one actual Retail HTTP pose check
pass. An actual Edge editor smoke rendered seven frames with no page errors,
retained Review on Return and left project state unchanged; screenshots were
inspected. Saved-clip management, assignment and descriptor/carrier Build delivery
remain unfinished. No immediate gameplay verification is required; no game was
launched. [Details](legaia-animation-allocation.md). The goal continues solo.

**Persistent allocated animation clips (2026-10-04):** Reviewed allocation now
publishes one scene-owned `AnimationRecords` command. The ledger freezes the
donor's current shared contribution, retains stable clip UUIDs, supports ordinary
Undo/Redo and Save/Open, and reviews retirement/restoration with retained
identities. Later edits to a shared source clip do not change its allocated copies.
Authored asset/component review and scene source-key invalidation are integrated.

32 focused native, Retail HTTP, ledger and GLB numerical checks pass, including
two clips (69→71 records), retirement (→70), byte-exact restoration, frozen donor
edits, offline metadata Open and unchanged Build-review files. Active allocated
clips explicitly block Build/review pending descriptor/carrier relocation; no clip
is silently omitted. Editor/pose/assignment and delivery remain unfinished. See
[allocation](legaia-animation-allocation.md). No gameplay was launched; work stays solo.

**Animation record allocation — native codec and SDK review (2026-10-04):** New
donor-based rigid clips now support explicit frame repetition/reordering/extension
and exact axis edits. The expanded bank rebases its absolute offset table while
preserving all existing records and opaque padding. A source-bound SDK HTTP review
resolves current clip/model witnesses and copies effective shared edits into the
new clip without authoring files/history. Seven codec and two Retail HTTP checks
pass, including a 69→70-record Town01 bank and LZS readback.

This is allocation infrastructure, not delivered clip authoring. Apply, Build and
new-clip assignment are explicitly unavailable; ledger/persistence, editor/pose
integration and bank/carrier relocation are next. See
[animation allocation](legaia-animation-allocation.md). No game was launched;
the full SDK goal remains incomplete and continues solo.

**Cubic animation GLB import (2026-10-04):** Existing rigid clips now accept
CUBICSPLINE translation and rotation tracks alongside STEP/LINEAR. Segment-time
scaled Hermite sampling preserves quaternion derivative magnitudes/signs and
normalizes the sampled rotation. Invalid counts/keys, nonfinite tangents, sampled
zero quaternions and translation overflow reject before authoring. The editor
explains that curves are sampled into existing frames.

19 focused Python checks passed, including an actual private Retail Town01 HTTP
Review/Pose → stale-file rejection → one-command Apply → Undo/Redo → Save/Open →
normal Build with exact decompressed animation-bank readback. The editor Node
binding/review and lifecycle suite also passed. No game was launched or controlled.
See [animation interchange](legaia-animation-glb.md). General animation record/frame
allocation, retargeting, full-scene/live parity and the wider SDK remain unfinished;
gameplay timing and clip selection remain deferred. Work continues solo.

**Retail GLB primitive groups — scene/package/native evidence (2026-10-04):** A private copy of the Retail V7 project replaces Town01 model 36 copied object 2 group 0 with two separate groups from two GLB primitives. Four selected authored faces retire and four imported faces preserve their source ranges/order with shared position rows. The first group imports three stored normal directions and UVs; the second omits those attributes and inherits donor references/values. Other groups remain, Current ordinals rebase and the retired group retains its stable tombstone. Actual V7 source/review and V5 material-source browser qualifiers pass.

Read-only Review, one-step Undo/Redo, unchanged base binding, Save/Open, unchanged project during Build and saved Build integrity/current inputs pass. The model changes from 12,308 to 12,524 bytes, SHA-256 `73eb1a978275de8ea3b7014f21ebde1b27ed117122c069ade695973f3ebd2d1f`. The normal format-7 Build emits one relocation payload (121,272,992 bytes, SHA-256 `383a0f2077f29bed03fcc6ad07497ba445b3575fbbb95fa21d52bb0c0243152b`), with no duplicate overlays. Packed readback matches all three authored models, preserves 111 unselected slots and five other resources (qualified padding only), and keeps PROT 121,255,936 bytes, one sector above Retail.

A fresh native harness at `dd5eaa87` qualifies complete user/raw reads, metadata, Mode2 address/subheaders/EDC/ECC and vanilla restoration on netplay clear. The full Retail editor then inspects exactly the same candidate model hash on both supported placements through the real HTTP endpoint and renderer. Shared geometry, all placement matrices/display positions, isolated Current/Proposed views, Return/Restore, retained file/review and exact base restoration pass with unchanged project state and no page errors; screenshot inspected. Evidence: ignored `local-output/sdk-20260909/retail-glb-primitive-groups-20261004/parent/proof.json` and `local-output/sdk-20260909/retail-glb-primitive-scene-20261004/parent/isolation-browser-proof.json`. Private server/browser stopped. No game launch/control, user-runtime installation or full Retail disc export occurred. Gameplay appearance/collision/lifecycle remain deferred; GLB material/image allocation, arbitrary packet layouts, animation interchange/allocation and full-scene/live parity remain unfinished. The full SDK goal stays active and solo.

**GLB primitive boundaries — browser workflow (2026-10-04):** Mesh import now exposes Preserve GLB primitives as separate groups for independent-group append and donor-group replacement. The choice is disabled and cleared when appending into an existing group. Review, Apply and scene inspection carry the exact choice; changing it invalidates the review. The summary reports the primitive/native group count and explicit donor layout/material inheritance.

The V7 browser qualifier checks contiguous complete primitive ranges, source ordering, bounded mode/counts, distinct stable group requests and each range's exact faces. It independently reconstructs allocated group counts/origins/Current ordinals, face group membership, retained group rebasing/tombstones, full typed packet render output and vector/normal ownership. Retired stable face IDs are also reserved when qualifying new identities. Default V1–V6 review paths continue to pass.

Validation: 19 focused Python/Node tests pass across primitive preservation, scene proposal, replacement, independent-group and legacy append. Actual SDK reports qualify for append/replacement, copied V7 ownership, and mixed imported/inherited stored normals. Forged ranges, ordering, identities, group counters/origins, face membership, render UVs and preservation choice reject. A private headless Edge dialog/renderer check passes GLB upload, Current/Proposed render, primitive-toggle/mode invalidation, disabled existing-group choice, retained scene review, Return/Restore callback, stale Apply, one reviewed Apply, delayed scene disposal and busy release with no page errors. Proposed screenshot inspected. Evidence: ignored `local-output/sdk-20260909/glb-primitive-groups-20261004/parent/browser-proof.json`. The scene callback in this bounded check is injected; full Retail multi-group scene/package/native delivery remains next. No game was launched or controlled. GLB material/image allocation, arbitrary packet layouts, animation interchange/allocation and full-scene/live parity remain unfinished. Gameplay stays deferred and the full SDK goal remains active and solo.

**GLB primitive boundaries — native project/API allocation (2026-10-04):** Mesh import now supports exact boolean `preserve_primitives` when independent groups are selected. Geometry V5 records the contiguous source primitive index, first triangle, triangle count and source triangle mode. One native group is allocated for each GLB primitive, in source order, while shared POSITION accessor rows remain shared. Each group owns its corresponding stable added faces and inherits the selected donor layout/material. Mixed missing UV/normal/color attributes retain the established per-face donor behavior. GLB material/image allocation remains unfinished and is not implied by preserving boundaries.

Review V7 binds this choice and the primitive ranges in addition to the exact file, donor, group requests and proposed bytes. It supports append and donor-group replacement; replacement still retires only the selected Current group. Vector allocation and the complete multi-group request publish atomically, with optional retirement, as one Undo step. Cumulative face/vector/group/batch/operation budgets and copied V7 object ownership remain enforced. Existing default imports and review schemas remain unchanged. The scene proposal endpoint carries the choice through candidate regeneration and review matching.

Validation: four new cases pass for shared vertices/contiguous ranges, per-primitive UV absence, strict choice and group bounds, read-only Review/files/history, wrong-mode Apply rejection, distinct stable group ownership, one Undo/Redo, Save/Open, exact synthetic normal Build model readback, strict HTTP preview/scene/Apply/stale rejection and copied V7 group tombstones/scene continuation. All 18 focused primitive-group/scene/replacement/new-group/legacy append tests pass together. This milestone implements native/project/API support; browser V7 qualification and a visible preservation control are next. Retail multi-group package/native delivery and gameplay are not claimed. No game was launched or controlled. Manual gameplay stays deferred and the full SDK goal remains active and solo.

**Retail GLB scene inspection and temporary isolation (2026-10-04):** The full editor now qualifies the reviewed GLB replacement through the actual Retail HTTP scene endpoint on private Town01 model 36. Its two supported placements share one proposed geometry, retain all placement matrices/display positions, and return to the exact base scene. Both Return to mesh import and Restore retain the uploaded file and accepted review; project state remains unchanged and no Apply is sent. This extends the earlier injected-callback dialog check to the actual editor, scene service, texture-qualified proposal and renderer.

The first screenshot showed unrelated scenery obscuring the inspected geometry. Mesh scene inspection therefore adds a reversible Isolate inspected instances control. It filters only viewport visibility, applies equally to Current and Proposed, and clears on Return/Restore/disposal without editing scene visibility or placements. The Retail browser check confirms 259 unrelated instances hidden, the two selected instances visible, and the full base restored with no page errors. Isolated Current/Proposed screenshots inspected; geometry remains positioned in the scene rather than recentered into a separate object viewer. Evidence: ignored `local-output/sdk-20260909/retail-glb-scene-inspection-20261004/parent/browser-proof.json`, `isolation-browser-proof.json` and `retail-isolated-proposed.png`. Editor syntax and diff checks pass. The owned private server/browser are stopped. This establishes Retail static scene inspection for this replacement; it does not establish game appearance, collision/lifecycle or general animation/coordinate/runtime parity. No game launch/control, user-runtime installation or full Retail disc export occurred. Manual gameplay stays deferred, and the full SDK goal remains active and solo.

**Reviewed GLB mesh inspection in the scene (2026-10-04):** Mesh import now offers Inspect reviewed mesh in scene before Apply. The new endpoint regenerates the candidate from the exact file, donor, Current hash and group mode, then checks both reviewed key and proposed hash. It composes the full prepared topology ledger into existing scene pose groups rather than treating allocated geometry as a same-layout file. Shared supported placements retain their source geometry grouping, pose and matrices; unavailable instances are reported. Textures are freshly qualified through the existing scene proposal path. The editor supports Current/Proposed comparison, affected-instance framing, Return to mesh import and Restore while retaining the uploaded file and accepted review.

Validation: 18 focused tests pass across scene proposal, replacement, both append modes and object preview. Scene composition covers all three modes on original and copied V7 objects; copied objects retain explicit unposed ownership. HTTP rejects forged review/proposed hashes, wrong group mode, invalid scope, unavailable selection and extra fields. Successful inspection preserves the scene, project document/history and authored files. A private headless Edge dialog/renderer check passed scene review retention, Return/Restore, mode invalidation, stale Apply, one reviewed Apply and delayed callback disposal with no page errors; it exposed and fixed a queued-close event that could dispose an already reopened dialog. Both changed editor modules pass syntax checks. Evidence: ignored `local-output/sdk-20260909/glb-scene-inspection-20261004/parent/browser-proof.json`. This bounded browser check exercises the dialog lifecycle with an injected scene callback; full Retail scene endpoint/render integration remains next and is not claimed. No game was launched or controlled. Manual gameplay stays deferred; the broader SDK goal remains active and solo.

**Retail GLB donor-group replacement — package/native evidence (2026-10-04):** A fresh private copy of the existing Retail V7 project replaces Town01 model 36's copied object 2 group 0. Exactly four stable authored faces retire and two lit Gouraud GLB faces import with four new vertices, three compatible stored normals and UVs. Other groups remain, native group ordinals rebase, the retired allocated group retains its tombstone, and the copied object retains its stable identity. Both actual V6 source/review reports and the resulting V5 material source pass browser qualification, including explicit absence of Retail counterparts for the copied object/groups.

Read-only Review, one-step Undo/Redo, unchanged base binding, Save/Open and saved Build integrity/current inputs pass. The model changes from 12,308 to 12,444 bytes; original vectors remain stored even when their faces retire. Final model SHA-256 `8c91f56ec5ab0306e41cd8df934d450567235f3fa0f830972e003b5571c48e05`. The normal format-7 Build emits one relocation payload (121,272,992 bytes, SHA-256 `77a1f4ce47f838e2958bc5cb72ae2d9ff0590e156b67b846f45923e80b639265`), with no duplicate overlays. Packed readback exactly reproduces all three authored models, preserves 111 unselected model slots and five other resources (qualified carrier padding only), and retains the matching Retail source hash. PROT remains 121,255,936 bytes, one sector above Retail.

A fresh native harness built at `2fde4087` activates only private staging and checks complete relocated PROT user/raw reads, metadata readback, Mode2 address/subheaders/EDC/ECC and vanilla restoration on netplay clear. Evidence: ignored `local-output/sdk-20260909/retail-glb-replacement-build-20261004/parent/proof.json` and `browser-qualification.json`. Two fixture assumptions were corrected while preserving prior attempts: object face totals are not selected-group totals, and copied object ownership is represented by `retail_index: null`. No user-runtime installation, game launch/control or full Retail disc export occurred. In-game appearance, collision/lifecycle and material editing after replacement remain deferred manual/workflow checks. Arbitrary packet layouts, texture/image/material allocation, animation interchange/allocation and full-scene/live parity remain unfinished. The full SDK goal stays active and solo.

**GLB donor-group replacement — browser workflow (2026-10-04):** The mesh import dialog now exposes Replace donor group alongside both append modes. Its V6 qualifier independently checks exact retired stable face IDs, Current group selection, surviving face and group index rebasing, allocated-group tombstones, three-operation budgets, imported face donor ownership and full typed packet reconstruction. Replacement reconstructs native material ordering rather than assuming append-only material indices. Original vector rows remain stored, and retired identities stay restorable. Mode changes and stale project context invalidate Apply; the reviewed request carries both exact booleans.

Validation: 12 focused Python/Node tests pass across replacement, independent-group and legacy append. Replacement reports qualify for original, retained authored, retired authored and copied V7 group cases; forged retirement, selection, donor ownership, operation counts, vector/triangle data and allocated group ordinals reject, as does the wrong review mode. A private headless Edge check exercised the actual dialog/renderer with a GLB replacing two faces with three: Current/Proposed render, upload, mode invalidation, stale Apply rejection, exactly one reviewed Apply and busy release passed with no page errors. Proposed screenshot inspected. Evidence: ignored `local-output/sdk-20260909/glb-group-replacement-20261004/parent/browser-proof.json`. This browser check does not verify Retail replacement delivery, the material editing panel or gameplay. Those remain deferred; the broader SDK goal stays active and solo.

**Topology-changing GLB group replacement — project/API (2026-10-04):** Mesh import now supports an explicit `replace_group` boolean together with `new_group`. It imports the reviewed GLB into a qualified independent group, then retires exactly the complete Current donor group's stable faces in the same published project command. Original vector rows remain; the replacement appends its own vertices/compatible normals and retains donor layout/material inheritance and existing UV/RGB conversions. This changes group topology rather than accumulating visible old faces. It does not replace an entire multi-group object or allocate an arbitrary packet layout.

Review V6 reports the exact retired IDs and Current object/group selection. The key binds replacement mode and removal ownership as well as the imported group requests, file and proposed bytes. Applying an append/new-group review as replacement, or a replacement review as append/new-group, rejects. Three ledger operations (vector allocation, group allocation, face retirement) publish as one Undo step. Cumulative allocated identities/budgets are retained, retired faces stay reserved/restorable, group origin remains stable, and Current native indices rebase after the old group is removed. Copied-object replacement retains V7 and explicit authored group ownership.

Validation: three focused replacement cases pass: read-only Review/files/history, exact donor-face retirement and topology count change, wrong-mode key rejection, one-step Undo/Redo, Save/Open, exact normal synthetic-disc Build, stable no-Retail ownership mapping, ordinary retired-face restoration, strict HTTP boolean/independent-group requirements and stale/repeated Apply rejection. A copied V7 group's retired ownership is explicit and its resulting Current source passes the existing browser source qualifier. Existing four new-group cases passed during integration. Replacement V6 review qualification and the visible mode selector remain next; full material panel, Retail/native delivery for replacement and gameplay are not claimed by this milestone. No game was launched or controlled; broader SDK work remains active and solo.

**Retail GLB independent-group package/native qualification (2026-10-04):** A fresh private copy of the Retail V7 object project now qualifies independent-group mesh import on Town01 model 36. Its native object 1 supplies a supported lit Gouraud triangle layout; a complete copy receives a new group with two GLB triangles, four new vertices, three Q12 stored normal rows and imported UVs. The actual source/review reports pass browser qualification, including complete reconstructed geometry, normal references/vectors, group ownership and bounds. The earlier model 8/model 9 edits remain part of the same project.

Mesh Review is read-only and Apply is one Undo step after the separate object-copy command. Undo/Redo, stable V7/base binding, Save/Open and unchanged authored state during Build pass. The mesh step grows the copied model from 12,172 to 12,308 bytes (+136), SHA-256 `c0b9b7cff8f34eabab923b4f6e0ed046f295a971d249b4bde0658834687bf517`. Normal Build emits one format-7 relocation payload, 121,272,992 bytes, SHA-256 `4a902b38602c59dd00d950314167ed96b1911660fb024180fcc00b8360fec3a4`; PROT is 121,255,936 bytes (+one sector from Retail), with no duplicate model overlays. Packed readback reproduces all three authored models while 111 unselected model slots and five other scene resources remain byte-exact (qualified carrier padding only). Saved Build integrity/current inputs pass; the bound Retail disc hash remains `e6120a5d70716dd2f026a2da32d0171d52651971b52c4347a68541299f75258c`.

A fresh MSVC native harness at `d0a60379` activates private staging and verifies every relocated PROT user/raw sector, metadata patch, Mode2 address/subheaders/EDC/ECC and vanilla reader restoration through netplay clear. Evidence: `local-output/sdk-20260909/retail-glb-group-build-20261004/parent/proof.json`. This establishes exact emitted-package/native-reader delivery for lit normal/UV imports into a separate group on an authored object; it does not establish in-game rendering, material appearance or object lifecycle. No user-runtime installation, game launch/control or full Retail disc export occurred. Manual checks stay deferred; arbitrary new layouts, texture/image/material allocation, general animation allocation/interchange and full-scene/live parity remain unfinished. Solo work and the full SDK goal remain active.

**GLB independent-group browser workflow (2026-10-04):** The mesh import dialog now offers Append to donor group or Create independent group. The chosen mode is captured in Review, checked against V4/V5 report scope and submitted with the exact review key at Apply. Changing mode invalidates Review and hides comparison; pending/busy and stale project/scene/source/model contexts block Apply. The summary states whether imported faces share the donor's material group or form a separate group. Both modes retain the existing Current/Proposed orbit/zoom comparison and file/context lifecycle.

The mesh-specific source API includes qualified complete native group descriptors/footer hashes, raw normal vectors and next stable group-origin boundaries, including empty/deleted group history. Browser V5 qualification checks exact new group/face requests, stable identity reservation, retained group membership, group mode/flags, origin/current indices, V7 object ownership, ledger/budget increments and face ordering. It independently reconstructs complete Proposed packet geometry, normals and bounds from the Current donor plus imported attributes. Neither Review nor preview assigns a new object/pose/animation channel.

Validation: eight focused mesh/new-group Python cases pass; the actual browser qualifier covers repeated allocation, an authored V7 object and lit Gouraud normal import, rejecting forged mode/identity/index/ledger/normal/geometry/bounds fields. The actual new source HTTP route is checked. Headless Edge mounted the real dialog/renderer against actual synthetic backend reports: uploaded a GLB, reviewed both modes, rendered Current/Proposed layers, invalidated a mode change, blocked stale Apply and sent one reviewed new-group Apply with busy released and no page errors. Screenshot inspected; private evidence: `local-output/sdk-20260909/glb-native-group-import-20261004/parent/browser-proof.json`. Fixture styling is not full styled-editor acceptance. Exact Retail/native delivery for this mode and gameplay remain deferred; broader SDK requirements remain active, solo. No game was launched or controlled.

**GLB import into an independent native group — project/API (2026-10-04):** Mesh append now supports an explicit boolean `new_group` option in the ordinary source-qualified Review/Apply API. It allocates imported vertex/normal rows and one complete native packet group atomically in the selected Current donor object, preserving retained faces/groups and the existing GLB POSITION/NORMAL/UV/RGB conversions. The donor supplies the qualified packet layout, descriptor mode, material binding and opaque footer; imported faces receive stable identities in their independent group. The original append-to-donor-group behavior remains the default.

New-group reports use review V5 and carry the exact group request. The review key binds that mode and stable group/face requests in addition to the file, source, geometry and donor, so a review from one mode cannot authorize the other. Apply re-prepares the candidate and publishes one immutable project/history step. Existing cumulative face/vector/group/history bounds remain enforced through ordinary ledger replay. Imports into a copied V7 object retain stable object ownership and V7 rather than acquiring a Retail counterpart.

Validation: three focused new-group cases pass: read-only review/files/history, distinct mode hashes/keys, wrong-mode Apply rejection, retained packet fields, full new-group membership, one-step Undo/Redo, Save/Open, exact normal synthetic-disc Build, HTTP strict boolean/malformed/repeated Apply and copied-object V7 continuation. Four existing mesh-append cases passed during integration. Browser V5 qualification and a visible mode selector are the next implementation step; this milestone does not claim those controls are exposed. Retail/native delivery for this exact new mode and gameplay remain deferred. No game was launched or controlled. The full SDK goal remains active, solo.

**Retail actor V7 model/scene animation evidence (2026-10-04):** A fresh private project copy now qualifies the complete authored-object preview path against Town01 actor `scene://town01/actors/man-p1/0005`, model `asset://town01/models/scene-tmd/0112` and its verified MAN-associated clip `animation://town01/scene-anm/0056`. A complete Current donor object 2 clone expands six native objects to seven. All six original rigid channels and 30 frames remain evidenced; object 6 has no assigned channel. The raw clone suffix begins at vertex 128 and stays unchanged through the entire clip.

The actual EditorServer coordinated scene service admitted 22 tracks and 42 animated instances, explicitly reported ten static/unavailable instances, and retained unchanged project/history during sampling. The browser decoder qualified the full 68,217 frame-vertex report. Every frame's model-view normal sample exactly matches the scene-view sample; original Retail animation changes while the cloned object's vertices and normals remain static. Evidence: `local-output/sdk-20260909/retail-actor-object-animation-20261004/parent/proof.json`. No substitute synthetic clip was used for this milestone.

This establishes offline Retail clip/model/scene consumer compatibility. It does not establish rendered Retail browser acceptance, a new game animation channel, the scene's initial pose matching current gameplay, or in-game rendering/lifecycle. No game launch/control, user-runtime installation or full disc export occurred. Manual checks remain deferred; broader SDK allocation/interchange, scene/live parity and other specification requirements remain active and solo.

**Individual V7 model normal diagnostic compatibility (2026-10-04):** Fixed the model viewer's shared normal sampler to accept the V7 shape composer's explicit pose marker and unposed-object indices, as well as the scene sampler's structured scope. Both forms qualify through the same bounded prefix/range checks. Cloned objects retain source-local normal vectors while only evidenced existing channels rotate. Unknown scope, non-trailing exclusions and invented clone channels reject; no channel is inferred from a donor.

The actual V7 model-preview/scene-report integration first reproduced the rejection, then passed after the adapter repair: frame normals from both views match exactly. Four focused Python cases and the existing Node rigid-normal renderer checks pass. This is a model/scene adapter compatibility check; no additional Retail or gameplay rendering claim is made. No game was launched or controlled. Manual verification remains queued and the full SDK goal remains active, solo.

**V7 coordinated scene animation and normal scope (2026-10-04):** Fixed the scene sampler's assumption that every Current native object has an animation channel. V7 shape previews retain only the evidenced existing channel prefix; scene tracks now qualify and expose that prefix plus explicit unposed native object indices and vector boundary. Every scoped frame must reproduce the original channels and retain all unposed vectors exactly, even when normal preview is omitted by its budget. Canonical scene scope, frame ownership, PSX rotation words and full mesh/material mappings remain qualified. Missing scope, invented clone channels and moved unposed vectors reject.

Normal sampling rotates evidenced objects only and retains unposed native object normals in object-local coordinates. The browser independently qualifies scope/ranges, constant unposed vertex suffix, exact normal scope and channel count. Scene source coverage visibly lists existing channel count and unposed indices. Existing all-channel tracks retain their format and behavior; no new animation/bone channel, hierarchy, record or game schedule is allocated.

Validation: 11 focused Python cases pass across scene sampling, actual V7 shape composition and the new scope integration. A complete synthetic lit object clone feeds the real sampler and JavaScript decoder; posed geometry moves while copied vectors/normals stay fixed. Forged scope/channel/rotation/vector changes reject, including with normal budget zero. Existing Node scene-controller and rigid-normal renderer checks pass. Headless Edge mounted the real scene controller and renderer against the actual synthetic report, displayed scope, scrubbed the track, retained cloned vectors/normals, restored baseline and released busy state with no page errors. Screenshot inspected; private evidence: `local-output/sdk-20260909/scene-animation-object-scope-20261004/parent/`. This is a focused synthetic integration/render check, not full styled-editor, Retail clip, or gameplay acceptance.

Remaining animation/scene consumers, general animation allocation/import/retargeting, full-scene/runtime parity and other SDK buildout requirements remain unfinished. Game rendering, pose/lifecycle and coordinate checks remain deferred. No game was launched or controlled; the full goal remains active and solo.

**Retail V7 object package and native reader proof (2026-10-04):** In a fresh private copy of the prior Retail V6 group/vector project, Town01 model 9 now has one complete lit native object clone (donor object 1: 13 faces, 18 vertices and 11 normals). V7 retains the prior authored face/group/vector history, original object indices, stable clone ownership and base binding. Review is read-only; Apply is one Undo step, with Undo/Redo and Save/Open confirmed. Model bytes grew 4,892 to 5,500 (+608), SHA-256 `fd79db3d2b265c017f133e78f8de46194316e33884eb7de1fd955a42baeba4f5`. Actual Retail source/review reports also passed independent JavaScript geometry/identity/allocation qualification.

Normal Build emitted one format-7 PSXDRLOC payload, 121,272,992 bytes, SHA-256 `97cdf08171b04a5aa3b52293fe2d0ae8d6c90c341e0febf234c2479ebf90a58c`, with no duplicate model overlays. PROT is 121,255,936 bytes (+one sector from Retail). Packed readback matches the full V7 model and retained model 8 edit; 112 unselected model slots and five other scene resources remain byte-exact (qualified carrier padding only). Saved Build integrity/current inputs and unchanged authored state during Build passed. The bound disc hash remains `e6120a5d70716dd2f026a2da32d0171d52651971b52c4347a68541299f75258c`.

A fresh MSVC native reader harness at `c5277f3d` activated only private staging, read every relocated PROT user/raw sector and metadata patch, independently qualified Mode2 address/subheaders/EDC/ECC, and restored vanilla reader state through netplay clear. Evidence: `local-output/sdk-20260909/retail-object-allocation-build-20261004/parent/proof.json`. No full Retail disc export, user-runtime installation or game launch/control occurred. This establishes emitted-package/native-reader delivery, not in-game object rendering, animation/pose assignment or scene parity. Those manual checks remain queued; remaining animation/scene consumers and broader SDK work remain active and solo.

**Native object creation editor (2026-10-04):** The model editor now exposes Create native object in Edit mode with a bound disc. It copies one complete qualified Current donor into independent native primitive, vertex and normal allocations, including authored V7 donors. The independent browser adapter qualifies stable ancestry, complete packet/group order, signed vectors, geometry/bounds, table expansion and pointer rebasing, copied-span hashes, opaque metadata and cumulative allocation/history budgets before enabling Apply. Current/Proposed orbit/zoom comparison is available. Donor changes invalidate Review; closed or changed project/scene/source/model contexts withdraw the dialog; Apply requires the exact reviewed request/key and uses one existing project Undo step.

Validation: 17 focused Python cases pass across object byte/ledger/project/HTTP, browser qualification, authored consumers/materials and preview paths. The browser qualifier now exercises both multiple initial clones and cloning an authored V7 donor, rejecting forged geometry, pointers, spans, counts and stable ancestry. Headless Edge mounted the real dialog against actual synthetic backend source/review reports: Current/Proposed rendered, donor changes invalidated Review, stale context withdrew the dialog, one reviewed Apply was sent, busy state released and no page errors occurred. Screenshot inspected. Private evidence: `local-output/sdk-20260909/object-creation-browser-20261004/parent/`. Fixture styling does not establish full styled-editor or gameplay rendering acceptance.

Copies start at the same object-local coordinates and inherit Current material settings; they have no newly assigned pose/animation channel. Arbitrary object layouts, rig creation and scene-instance creation are outside this command. Retail/native V7 object-package qualification and remaining animation/scene consumers are next offline work; manual game rendering, pose/lifecycle and scene parity remain deferred. No game was launched or controlled. Solo work and the full SDK goal remain active.

**Object-allocation HTTP source/review/apply and shared donor compatibility (2026-10-04):** Added exact-field HTTP routes for object allocation source, preview and reviewed Apply. They require a model, current source key/hash, bounded stable requests and the reviewed identity key. Source reports now include each Current object's native table offsets, opaque metadata, complete packet-group counts/order and hashes for primitive allocation and padded vertex/normal tables. Review remains read-only; Apply uses the actual project command and late source gate, publishing one immutable override/history step. No object-creation capability or button is exposed yet.

The shared face donor adapter now qualifies V7 object ancestry and permits cross-object donors only through the copied object's explicit stable donor-object relationship and authored group ownership. Source objects remain bound to the ledger base hash/index; copied objects cannot acquire source face identities. Self donors and forged object history reject. This allows existing face/group donor inspection after object creation rather than rejecting legitimate copied provenance.

Validation: 14 focused Python cases pass across object HTTP/project commands, V7 primitive/vector consumers, group commands and authored-object material/GLB paths. HTTP cases cover read-only project/files/history, extra fields, malformed/bounded requests, stale source/hash, bad review keys and repeated Apply. Actual V7 face and group sources qualify in JavaScript; forged source indices, self ancestry, object budgets and face self-donors reject. Native source group coverage is checked. Existing Node face workflow/lifecycle and syntax checks pass. The independent object review adapter and Current/Proposed creation dialog are next; Retail/native object package, remaining animation/scene integration and gameplay remain deferred. No game was launched or controlled; solo offline work and the full SDK goal remain active.

**Authored-object materials, GLB editing and explicit preview pose scope (2026-10-04):** Material source V5 now carries stable V7 object mappings. Groups copied into a new object receive authored ownership with no Retail object/group/face counterpart; later face extensions preserve that ownership. Source/review browser adapters qualify the object ancestry and complete authored group/face membership while retaining protected descriptor bits. Existing material Review/Apply supports inherited texture selectors and shared group semitransparency on these objects, retains V7 and stable IDs, and preserves one-step history and Save/Open. Retail reset stays disabled and guarded.

The V7 shape-preview composer now handles expanded native object tables. It qualifies candidate/hash/ledger continuation and retained vertex spans, preserves only evidenced original pose channels and explicitly labels all remaining objects as unposed. Copied objects never receive a donor's pose/bone channel; a forged channel extending into a new object rejects. Known source pose prefixes and frame bounds are retained while full Current geometry is displayed. This unlocks fixed-layout Current GLB export/import on V7: unchanged files round-trip, and edits to a copied object's exported native vertex rows publish through existing typed content/history handling without inventing a new hierarchy or rig.

Validation: 18 focused Python cases pass across authored-object material/GLB/preview, earlier authored-group/material/vector consumers and object project Build paths. Actual material source/review reports qualify in JavaScript and reject invented Retail owners, self donors, missing group owners and changed protected flags. Targeted pose checks cover unposed geometry, retained pose prefixes, frames, later Current continuation and forged channel/hash/ledger rejection. Existing Node material workflow checks pass. A headless Edge smoke mounted the real material panel against actual synthetic reports, rendered inherited fields with absent Retail values, guarded disabled Reset, withdrew stale Review and sent one reviewed Apply with no page errors. Screenshot inspected; private evidence: `local-output/sdk-20260909/authored-object-material-browser-20261004/parent/`. Fixture styling is not full styled-editor or game rendering acceptance.

Object-creation HTTP/editor controls, remaining animation/scene consumer integration and Retail/native object-package qualification are still pending. General replacement meshes, image/material allocation, animation import and full-scene/runtime parity remain unfinished. No game was launched or controlled; gameplay stays queued and the full SDK goal remains active.

**Authored-object packet/vector inspection and edit compatibility (2026-10-04):** Primitive source V6 now carries complete stable object mappings on V7 models. Retained objects keep their original Retail index; cloned objects have a null Retail counterpart and explicit stable donor-object ancestry. Face mappings cover every Current object: authored objects have an empty Retail face map and complete authored face IDs. Vector growth includes all independently copied rows, and qualification checks its total against complete V7 replay. Packet Review/Apply can edit an authored object's existing vertex/normal/UV/RGB fields and retain V7, identities and one-step history.

Stored vertex/normal reference sources V4 carry the same object ownership. Copied objects have zero Retail vector count, null Retail coordinates, empty Retail users and complete Current authored face references. The browser adapters qualify stable object ID syntax, source indices, donor-before-clone ancestry, complete mappings, native counts and authored face coverage; they reject invented Retail ownership, self donors, changed identities and forged growth. Existing reference panels disable the absent Retail layer and navigate using the authored face identity.

Validation: 12 focused Python cases pass across V7 object inspection/project commands and earlier allocated-vector/editor/group Build consumers. Actual V7 source and complete packet-review reports qualify in JavaScript; forged object/face/vector ownership rejects. Existing Node primitive, vertex/normal and post-addition reference suites pass. The real HTTP server serves the shared object-ownership adapter. A headless Edge smoke mounts the real reference panels against actual synthetic reports, verifies disabled Retail layers, authored-face navigation and stale-context withdrawal with no page errors; its screenshot was inspected. Private evidence: `local-output/sdk-20260909/authored-object-references-20261004/parent/`. Fixture styling is not full styled-editor acceptance. Material/GLB/pose/shape consumer ownership, object-creation HTTP/editor controls and Retail/native object package qualification remain next. No game was launched or controlled; the full SDK goal remains active.

**V7 object provenance, reviewed project command and synthetic Build (2026-10-04):** Object allocation now has a stable ledger operation. Each clone references a stable Current object ID and supplies new UUIDs covering every donor group and face in native order. Replay qualifies the independent byte codec, records donor ancestry for each authored object/face and retains source object indices. New objects and their copied groups have permanent roots; face deletion/restoration, additional groups/faces, vector allocation and typed content edits preserve V7 and stable ownership. IDs remain reserved after face deletion. Copied native vectors, groups and faces count against cumulative 4,096-vector, 64-group, 128-face, eight-batch and 64-operation limits, alongside the 64-authored-object limit. Empty native groups reject in this ledger workflow; a group-free object with a qualified nonempty vertex table can be represented.

The SDK object source/review adapter exposes Current stable object donors, complete native previews, remaining budgets and exact allocation spans/pointer audit. The actual project command binds all object/group/face identities and donor choices into its review key, independently recomputes the candidate, retains the existing base binding and publishes one immutable override/Undo step through the existing late source gate. Same candidate bytes with changed identity cannot reuse the review. Source/Review remain read-only. V7 bindings Save/Open and build through the normal synthetic relocation path with exact packed-model bytes, without changing authored state during Build.

Validation: 25 focused Python cases pass across object codec/provenance/project command and existing V6 group/material/Build paths. New coverage checks deterministic JSON replay, cloned authored objects as later donors, full-group deletion followed by new allocation and restoration, independent content/vector edits, schema/hash/identity/coverage/budget rejection, unchanged Review files/history, one-step Undo/Redo, Save/Open, exact normal synthetic Build and stale publication. Group review now shares reserved-group extraction with object operations. Object-creation HTTP/editor controls, V7 authored-object inspection/material/vector/pose consumer ownership and Retail/native object-package evidence are still pending. No object-creation capability is exposed yet; no rig/scene hierarchy or animation channels are inferred. No game was launched or controlled; the broader SDK goal remains active.

**Native object-allocation codec foundation (2026-10-04):** Added a pure byte codec for allocating up to 64 independent objects from qualified Current native donors, subject to the 1,024-object and 4 MiB model limits. Requests carry distinct authored object UUIDs and exact donor indices. The object table expands without changing retained object indices; existing used pointers rebase, unused pointers stay exact and the entire original post-table byte suffix remains intact. Each appended object independently copies its donor's complete qualified primitive allocation (including descriptor/footer/opaque tail), signed vector rows/pads and opaque object metadata. New allocations align to four bytes; counts/pointers/native spans and source/proposed hashes are audited. Exact candidate recomputation rejects any unowned mutation. Donors require a nonempty qualified vertex table; no rig, pose, scene hierarchy or animation ownership is inferred.

Validation: three targeted cases pass across all 24 supported packet flag variants, multiple objects/groups, repeated and newly allocated donors, unowned source tails, absent normal tables, header/size/request/hash gates and independent new-object packet edits; four existing native-group codec cases also pass. This is byte-codec groundwork only. Stable object/face/group ledger provenance, project Review/Apply/history/Build integration, existing editor consumers and creation controls are not connected yet, so no object-creation capability is exposed. No Retail object package or gameplay acceptance is claimed; the full SDK goal remains active and the game stays closed.

**Retail V6 group-allocation package and native reader qualification (2026-10-04):** A private copy of the prior Retail GLB append project now applies a new two-face packet group in Town01 model 9 using an authored Current donor and existing imported vectors. Review remained read-only, Apply retained the independent base binding, V5 history replayed into V6, Undo/Redo was one step and Save/Open recovered exact final bytes. The model grows from 4,824 to 4,892 bytes, SHA-256 `d8f9fc5fc13544d8be6ebe88f9411b2283cb9323f13e7a5260f46c675d370e6b`. Actual Retail source/review reports qualify in the browser adapter.

Normal Build produced one format-7 relocation payload (121,272,992 bytes; SHA-256 `fd1af83a98d6203b1f27034d4b0a45133e1de1481d33f87428036694531dc55a`) and no duplicate overlays. PROT is 121,255,936 bytes, one sector larger than source. Build integrity/current inputs and unchanged authored project state passed. The prior neighboring model-8 edit remains exact; 112 untouched model slots and five other scene resources remain byte-exact, with only qualified padding. A fresh native reader harness compiled against runtime revision `c53d8b26` (executable SHA-256 `9ce3ccf8fae140e7253dc99ea1ab596c2a39ba3258ee852618713d7129a0bdd5`) activated private staging and read every emitted PROT user/raw sector, verifying raw addresses/subheaders/EDC/ECC, all metadata patches and netplay clear. Harness compile emitted existing CRT/conversion warnings. Retail source hash remains `e6120a5d70716dd2f026a2da32d0171d52651971b52c4347a68541299f75258c`.

Private evidence: `local-output/sdk-20260909/retail-group-allocation-build-20261003/parent/` (`proof.json`, source/review reports, qualifier scripts, fresh harness and staging). This qualifies package/reader delivery, not game rendering, collision or camera behavior. No game process, user-runtime installation or full Retail disc export occurred. Manual group visibility/gameplay checks remain deferred; new native objects, arbitrary replacement hierarchy/images/material allocation, animation import and full-scene/runtime parity remain unfinished. The full SDK goal remains active.

**Packet-group creation editor workflow (2026-10-03):** The Edit model panel now exposes Create packet group. Its dialog selects a qualified Current donor, edits typed vertex/normal indices, UVs and RGB where supported, and reviews complete Current/Proposed native geometry before Apply. This initial UI creates one group with one triangle or quad using existing vector rows; Add model face can extend it afterward. The API supports multi-group/multi-face requests. Capability, pending shape edits, busy state, selected asset and project context gate the action. Input changes invalidate review, context changes dispose the dialog, requests abort on close, and Apply sends the bound review key as one project history step.

The independent browser adapter checks source budgets, packet-group coverage/stride/footer ownership, stored normal vectors and table pointers; review checks typed packet geometry, stable retained/new identities, exact insertion at the owner's terminator, nonoverlapping growth and pointer rebasing (including preserved unused table pointers). No new native objects, packet families, vector rows, images, animations or arbitrary replacement hierarchy are created.

Validation: 21 focused Python tests pass across project/API, native group allocation/replay/Build and authored materials. New checks qualify actual reports for all 24 supported packet flag variants across two objects, multi-group/multi-face requests and reject forged geometry, pointers, spans, identity and budgets. The real server serves the new JavaScript module. Existing Node face workflow/lifecycle checks and editor/module syntax checks pass. An isolated headless Edge smoke against actual synthetic backend reports renders both preview layers, invalidates changed fields, withdraws stale context, sends one reviewed Apply and releases busy state without page errors; screenshots were inspected. Private evidence: `local-output/sdk-20260909/group-creation-browser-20261003/parent/`. Browser fixture styling is not full styled-app acceptance. Retail/native V6 package qualification and manual gameplay remain pending. The broader SDK goal remains active; no game was launched or controlled.

**Reviewed group-allocation project command and HTTP path (2026-10-03):** Added group-allocation source/review APIs and an actual project command that recomputes the reviewed candidate, retains the independently qualified base binding and publishes one immutable model override/Undo step. Review keys bind stable group/face IDs, donor identities, typed fields, source key, Current hash and proposed bytes; changing an identity while leaving candidate bytes identical still invalidates Apply. Source reports expose Current native donors, complete geometry/topology and remaining group/face/batch/operation budgets. Review supplies exact allocation spans, descriptor/footer/packet hashes, pointer relocation audit and Current/Proposed native geometry. The server accepts only exact model/source/request/review fields and exposes the group-allocation capability. Review and source leave project/history/files unchanged; late source publication gates remain active.

The shared browser face-source adapter now recognizes V6 allocated groups. It qualifies historical group counts, stable UUID/root/Current ownership, complete active authored face lists, inherited flags and donor provenance across separate groups. Missing/conflicting allocation records reject; existing source groups retain their original provenance rules. This supports donor inspection after creation rather than treating an authored group's template as its Retail group identity.

Validation: 29 focused Python tests pass, including four new command cases, native group replay/Build consumers, authored materials and mesh append regressions. Actual command checks cover read-only review/files, same-byte changed-ID rejection, one-step Undo/Redo, Save/Open with retained topology, normal synthetic Build with exact packed-model bytes, independent base wrapping and stale publication. HTTP source/review/apply cases cover exact fields, malformed/stale requests, review-key rejection and repeated Apply. Actual post-creation face sources qualify in JavaScript and reject changed allocation ownership; existing Node face workflow/lifecycle tests and syntax checks pass. The creation dialog, its independent review adapter and editor action remain next; the API is implemented but no new-group creation UI is exposed yet. Retail/native V6 package and gameplay checks remain deferred. New objects, mesh replacement/images/material allocation, animation import, full-scene/runtime parity and the broader SDK specification remain unfinished. No game was launched or controlled; solo offline work and the full goal remain active.

**Authored-group material ownership and editor compatibility (2026-10-03):** Material source V4 represents each allocated Current group with a null Retail group mapping and a stable authored group ID. V6 replay records the inherited creation flags/mode, allowing protected descriptor comparison without assigning a donor's Retail identity to the new group. Ordinary face extensions inherit the authored ownership; deletion removes the active group entry and restoration recovers its stable ID. Retained groups keep their existing Retail mappings. Material Review/Apply continues to audit against Current topology, including exact shared-group membership. The browser adapter qualifies all authored-group IDs, complete null-owner mappings, packet ownership and protected descriptor bits. The material panel renders absent Retail values explicitly, disables and guards Retail reset for authored groups, and keeps Current texture-binding and shared semitransparency authoring available.

Validation: 33 focused Python tests ran, 31 passed and two existing Retail-dependent tests were skipped. Three new cases verify literal source ownership, reviewed primitive/group material changes, no mutation during Review, stale-review rejection, one-step history, Save/Open, removed-base composition, deletion/restoration and fixed-layout GLB no-op export/import on V6 topology. Actual V4 source/review reports pass JavaScript and reject changed IDs, flags/mode, Retail mappings, missing/duplicate group owners, incomplete face ownership and changed shared-group audit membership. The normal synthetic Build fixture now includes an authored-group material edit and reopens exact final packed-model bytes. Existing Node material workflow and syntax checks pass.

An isolated headless Edge smoke mounted the real material panel against actual synthetic backend reports with fixture HTTP responses. It rendered the authored group with absent Retail values, guarded disabled Reset, reviewed group semitransparency, withdrew Apply on stale context and sent exactly one reviewed Apply. The screenshot was inspected; no page errors occurred. Private evidence is under `local-output/sdk-20260909/authored-group-material-browser-20261003/parent/`. This is panel/adapter evidence, not full styled-editor or Retail texture/rendering acceptance. New-group creation project/API/review controls, Retail/native V6 package qualification, native objects, replacement meshes/images/material allocation, animation import and full-scene/runtime parity remain unfinished. No game was launched or controlled; solo offline work and the full goal remain active.

**Stable native-group replay and Build consumers (2026-10-03):** V6 ledgers now carry typed `allocate_groups` operations using stable group and donor-face identities. Replay resolves all packet donors in the selected Current group, qualifies allocation through the native codec and chains exact input/output hashes. New group origins are permanent per-object ordinals after the base groups; they survive Current compaction, later face additions, full-group deletion, intervening new allocation and restoration. Authored group/face identities remain reserved after deletion. The audit exposes historical group count, allocation count and stable group IDs with explicit Current index or null when absent. V6 preserves prior vector/content/removal/restoration operations and enforces cumulative 64-group, 128-face, eight-addition-batch and 64-operation budgets. Earlier versions cannot replay group allocation.

Existing enlarged-vector primitive sources, reference-user inspection and rigid pose preview recognize V6 vector ownership. An internal qualified binding passes existing project reads, later vector-edit and primitive-edit history, Save/Open and normal synthetic-disc Build with exact packed model bytes. The group fixture installs the binding internally; it does not exercise a new-group project command or UI. Current V5 previews transitioning to V6 retain pose channels, appended vertex rows and complete new triangle data without mutating shared inputs.

Validation: 35 focused Python tests pass. New cases cover stable roots and ordering through deletion/intervening allocation/restoration, mixed V5/V6 vectors and lit references, content edits, tombstones, donor ownership, version/hash/schema rejection, cumulative limits, JSON replay, persistence/Build and pose composition. Actual V6 primitive source/review reports also pass the JavaScript adapters; new-group reference users have no invented Retail vector coordinates. Material-group ownership compatibility, new-group project/API/review controls and broader browser workflow remain unfinished, as do native objects, mesh replacement/images/material allocation, animation import and full-scene/runtime parity. No Retail/native V6 package, rendered browser smoke or gameplay acceptance is claimed; no game was launched or controlled. Solo offline work and the full goal remain active.

**Native packet-group allocation foundation (2026-10-03):** Added a bounded codec that creates new native primitive groups at an object's explicit terminator. Each request owns a UUID group identity and typed UUID face identities, selects a qualified same-object donor group, and supplies donor packet vertex/UV/RGB/normal-reference fields. The codec inherits descriptor bytes and opaque footer exactly, sets the new group count, preserves all retained packets and unowned bytes, updates object primitive counts and rebases used vertex/normal/primitive pointers. Unused pointers remain unchanged. Several new groups and several objects can grow in one candidate; later allocation may use a newly created group as donor. Qualification recomputes the entire candidate from source bytes and typed requests. Limits are 64 groups and 128 faces per operation plus the existing model-byte budget.

Validation: 20 focused Python cases ran, 18 passed and two existing Retail-dependent primitive tests were skipped. Four new allocation cases exercise all 24 supported native flag variants across multiple objects/groups; exact descriptors, opaque footers, retained packets and complete unowned-byte reconstruction; typed Gouraud UV/RGB and lit normal indices; repeated allocation and existing face extension of a new group; unused pointers; identity/owner/donor/field/count/budget errors; immutable requests and exact candidate tamper rejection. No Retail/native package, browser or game check ran for new-group allocation.

This is allocation infrastructure, not a published authoring workflow. Stable replay-ledger group ownership, removal/restoration composition, project command/history/persistence/Build integration and editor review controls remain next; users cannot yet create groups through the editor. Donor-layout inheritance does not invent new packet families or create native objects. Mesh replacement/images/material allocation, animation import, scene/runtime parity and the full SDK specification remain unfinished. Gameplay stays deferred and solo offline work remains active.

**GLB triangle strip/fan append (2026-10-03):** Static mesh append now accepts glTF TRIANGLES, TRIANGLE_STRIP and TRIANGLE_FAN primitives (modes 4/5/6). Strips alternate source winding; fans retain their anchor before the existing Y reflection and winding reversal. Every expanded corner retains its matching normal, UV and color. Indexed and nonindexed inputs produce the same typed triangle append operations and use the existing review/history/native donor gates. Expanded face count is bounded at 128 across all primitives; unsupported modes, incomplete inputs, out-of-range indices and triangles degenerate after native quantization are rejected. Degenerate strip connectors are not silently discarded.

Validation: 29 focused Python tests pass, including fixed-layout GLB regressions and three new mode cases. Independently specified odd/even strip and fan corners verify native position/normal/UV/color associations. Both modes exercise actual reviewed Apply, one-step Undo/Redo, Save/Open, normal synthetic-disc Build with exact model readback, and JavaScript qualification/tamper rejection using actual backend reports. No separate rendered browser smoke or Retail/native strip/fan run is claimed; the prior Retail/native proof covers triangle-list GLB input. The existing editor accepts the unchanged triangle review schema. New native groups/objects, replacement meshes/materials/images, animation import, full-scene parity and the broader SDK specification remain incomplete. Gameplay appearance remains deferred; no game was launched or controlled and solo offline work remains active.

**Retail GLB append package and native reader qualification (2026-10-03):** A private Retail Town01 project imported four GLB vertices and two triangles into model 0009, including normalized UVs and baked textured RGB. Review left project/history/files unchanged; Apply published one Undo step, Undo/Redo restored exact bytes, and Save/Open retained the result. Native packet readback confirms imported vertex references, UVs and RGB while preserving donor material words. Model size grew from 4,752 to 4,824 bytes (72 bytes); final model SHA-256 is `3c76b154c754938e6ab030d9e25a8e1895f7ca5d811db603c695af415619c7d1`. Normal Build preserved the prior model 0008 edit, all 112 unselected model slots and five other scene resources, with only allocation padding permitted. Saved Build integrity and private staging passed without changing project state.

The sole relocation payload is 121,272,992 bytes, SHA-256 `114ff9deadf54bcb41807a685ed76060196a728ffb2dd341192b848f9064554a`; proposed PROT is 121,255,936 bytes with one extra sector. A freshly compiled native reader harness at SDK revision `d9720e39` activated that emitted package against the unchanged Retail source, checked every replacement PROT user sector and raw sector (address, subheader, EDC/ECC), read all patched metadata, and cleared relocation state/sector count for netplay. Source disc SHA-256 remains `e6120a5d70716dd2f026a2da32d0171d52651971b52c4347a68541299f75258c`. Private proof, source hashes and harness are under `local-output/sdk-20260909/retail-glb-append-build-20261003/parent/`.

This qualifies the positions/UV/baked-color append through Retail packaging and the native reader. The selected donor is unlit, so NORMAL was explicitly ignored and no new normals were stored; lit normal allocation retains synthetic test coverage, not this Retail/native proof. Gameplay appearance, full-scene parity, new native objects/groups, mesh replacement/images/material allocation, animation import and the broader SDK specification remain unfinished. No game was launched or controlled, no full Retail disc was exported, and solo offline work remains active.

**GLB append baked color import (2026-10-03):** Standard COLOR_0 arrays now decode per imported triangle, including FLOAT and explicitly normalized unsigned byte/ushort RGB/RGBA accessors. Normalization is an opt-in shared-reader path, leaving existing fixed-layout GLB readers' defaults intact; buffer ownership also rejects boolean buffer IDs. Unlit native packets import colors with explicit native semantics: textured colors map linear modulation to neutral 128, while untextured colors invert the established export's linear/sRGB conversion into display-referred byte RGB. Gouraud donors preserve per-corner colors; flat donors require equal converted corners. Missing colors inherit the donor, lit packets ignore mesh colors, and nonopaque per-corner alpha is rejected for baked RGB. Native material, palette/page, command and packet-layout ownership remains unchanged. V4 review metadata exposes conversion mode, exact RGB fields and rounding; the browser independently qualifies those fields and proposed render colors. Donor labels distinguish Unlit Flat/Gouraud, and the review summary reports baked-color face count.

Validation: 26 focused Python tests pass, including existing fixed-layout GLB codec checks. Combined positions/UV/color commands verify literal packet RGB, UVs and unchanged materials, read-only review, one-step Undo/Redo, Save/Open and normal synthetic-disc Build with exact model readback. Additional cases cover normalized byte/ushort data, missing normalization, color domains, flat/untextured/lit ownership, missing-color primitives and rejected alpha with unchanged history/files. Actual textured, untextured-flat and lit backend reviews qualify in JavaScript and reject changed modes/counts/rounding, RGB fields and proposed colors. Isolated headless Edge rendered actual V4 synthetic backend reports with Gouraud RGB gradients; both layers, donor/context review withdrawal and one reviewed Apply passed, and the screenshot was inspected. Private evidence is under `local-output/sdk-20260909/mesh-append-color-browser-20261003/parent/`. This supersedes inherited-only colors for compatible unlit appends. Standard textured colors do not import amplification above neutral 128; native RGB editing remains separate. New mesh images/materials, native object/group creation, replacement topology, animation import and the broader SDK specification remain unfinished. Retail/native GLB workflow and gameplay appearance remain queued. No game was launched or controlled; solo offline work and the full goal remain active.

**GLB append UV import (2026-10-03):** Standard TEXCOORD_0 arrays now decode per triangle with the same winding conversion as positions/normals. For textured donors, the importer derives the Current UV rectangle of all packets sharing the selected CLUT/TPage binding and maps normalized mesh UVs into that explicit region. Conversion follows the existing texel-center convention, clamps half-texel crop edges and reports integer rounding error. Imported UVs are written into each new native packet while donor materials, palette/page words, colors and packet flags remain unchanged. Missing UVs retain donor values; untextured packets ignore mesh UVs. Coordinates outside 0..1 are rejected for textured imports rather than inferring wrapping/sampler state. V3 geometry/review reports expose region, converted values, imported-face count and rounding; the browser independently verifies the binding, conversion and proposed triangle UVs. The review summary identifies the target region and texel rounding.

Validation: 17 focused Python tests pass. A combined positions/normals/UV import verifies literal native UV coordinates, normal references, unchanged material words, read-only review, one-step Undo/Redo, Save/Open and normal synthetic-disc Build with exact packed-model readback. Cases cover missing-UV primitives, untextured donors, rejected wrapping with unchanged history/files, and browser rejection of changed regions, binding words, counts, packet UVs and proposed render coordinates. Existing mesh/normal allocation and allocated-row editor checks remain passing. Isolated headless Edge rendered actual V3 synthetic backend geometry with an explicitly synthetic checkerboard texture; both layers, changed-donor/stale-context withdrawal and one reviewed Apply passed, and the screenshot was inspected. Private evidence is under `local-output/sdk-20260909/mesh-append-uv-browser-20261003/parent/`. The checkerboard is a crop-mapping smoke, not Retail texture association or gameplay acceptance. This supersedes inherited-only UVs for compatible appends. New images/materials, baked-color import, native object/group creation, replacement topology and the broader SDK specification remain incomplete. Retail/native GLB workflow and gameplay checks stay queued; no game was launched or controlled and solo offline work remains active.

**GLB append normal allocation (2026-10-03):** Standard GLB NORMAL attributes now decode alongside appended positions/triangles. Referenced directions must be finite and nonzero; the importer normalizes them, reflects Y and rounds them to signed Q12 components. Lit Gouraud donors retain per-corner directions. Lit flat donors require equal converted corner directions rather than averaging away an unrepresentable layout. New stored normals are deduplicated and allocated with vertices in the same V5 operation; new face references bind their exact appended native indices. Missing-normal faces retain donor references, and unlit donors allocate no normal rows. V2 geometry/review metadata records normal conversion, allocation ranges, per-face references and imported-face counts; the browser independently checks those relationships. Donor labels now distinguish Lit Flat, Lit Gouraud and Unlit, and the review summary displays imported normal/face counts.

Validation: 14 focused Python tests pass. Actual lit fixtures verify converted stored XYZ words, complete per-corner indices, combined one-step Undo/Redo, Save/Open and normal synthetic-disc Build with exact packed-model readback. Cases cover flat equality/rejection, mixed primitives with missing normals, unlit inheritance, zero directions, standard indexed/nonindexed geometry, HTTP/review identity and existing allocated-row editing. Actual Gouraud/flat/unlit backend reviews qualify in JavaScript and reject zero/changed directions, counts, indices and allocation ownership. An isolated headless Edge smoke rendered the V2 lit report with the real scene renderer, verified both layers, donor/context review withdrawal and one reviewed Apply; the screenshot was inspected. Private fixture-backed browser evidence is under `local-output/sdk-20260909/mesh-append-normals-browser-20261003/parent/`. This supersedes inherited-only normals for compatible mesh appends. Imported UVs/colors/materials, native object/group creation, replacement topology and the broader SDK specification remain unfinished. No live lighting or gameplay acceptance is claimed; Retail/native GLB workflow qualification and gameplay checks remain queued. No game was launched or controlled, and solo offline work remains active.

**Reviewed standard GLB mesh append (2026-10-03):** Added a model-editor workflow that imports static GLB positions and triangle lists into the selected Current native triangle donor's object. Indexed and nonindexed geometry uses the existing bounded accessor reader, shares repeated source POSITION rows, reflects Y/reverses winding, rounds to signed native coordinates and rejects degenerate post-quantization faces. The command appends vertices and donor-layout faces through V5 replay, then publishes both allocations as one reviewed Undo step. Native donor UVs, baked RGB, normal references, packet flags and material bindings are retained; supported GLB display attributes are validated and explicitly excluded from import. No external resources are fetched.

The dialog offers file/donor selection, Current/Proposed rendering, orbit/zoom and a concise review summary. File/donor/context changes withdraw Apply. Apply is bound to the uploaded file hash, donor, source key and reviewed candidate; close/abort/busy handling retains ownership. The SDK serves the module and advertises the capability. One scene, one untransformed mesh node and triangle lists are accepted; skinned/animated/morph geometry, unknown attributes, nonidentity object transforms and quad-only donor models are rejected. New native objects/groups, imported normals/UV/colors/materials, general hierarchy and replacement topology remain unfinished. This is an append workflow, not complete arbitrary-model replacement.

Validation: 13 focused Python tests pass, including standard indexed/nonindexed axes/indices, malformed ownership/transforms, signed bounds and degenerate rounding, read-only review, one-step history, Save/Open, normal synthetic-disc Build with exact model readback, actual HTTP/module GET, changed-file review rejection and stale/repeated Apply. Actual backend reviews qualify in JavaScript before and after an append using a new authored donor, with vector/face/render-attribute/ownership tamper rejection. Isolated headless Edge rendered actual synthetic backend reports with the real scene renderer; both layers, changed-donor/stale-context withdrawal and a single exact reviewed Apply passed, and the screenshot was inspected. The browser smoke uses fixture-backed HTTP responses, not the complete styled editor/server session. Private evidence is under `local-output/sdk-20260909/mesh-append-browser-20261003/parent/`. Retail/native qualification of this GLB workflow and gameplay appearance remain pending. No game was launched or controlled, and the broader SDK goal remains active with solo implementation.

**Retail allocated-vector package qualification (2026-10-03):** An isolated copy of the Retail Town01 project appended two vertices and one normal to model 9, then added a donor-qualified face referencing vertices 71/72. The new stored normal remains unreferenced in this Retail case; synthetic lit-face tests separately cover references to allocated normals. The final model grew from 4,752 to 4,796 bytes (24 vector bytes plus a 20-byte face). Normal format-7 Build emitted one relocation payload and no overlays. Exact packed model readback includes the prior neighboring model-8 edit; all 112 unselected slots and five other scene resources remain byte exact, allowing only zero allocation padding. Build preserved authored state, saved project reopen passed, package integrity/current-input checks passed, and private RunService staging started no process.

A fresh isolated native harness compiled from current runtime sources at ce337cb8 activated the SDK-emitted package, read every replacement PROT user/raw sector, checked raw address/subheader/EDC/ECC framing, read all metadata patches and confirmed netplay clear restored the stock sector count and relocation state. PROT grew by one sector to 121,255,936 bytes; the 121,272,992-byte relocation payload has SHA256 `62e7f529e61af19246372bf2f970d75d97798cb41111adad2fdfe702eaf32280`. Private proof/scripts/source hashes are under `local-output/sdk-20260909/retail-vector-allocation-build-20261003/parent/`. No game executable was launched, no user runtime installation occurred, and no full Retail disc was exported. Native reader acceptance does not establish rendered geometry, lighting, animation or gameplay behavior. Those checks remain queued; broader SDK buildout continues solo.

**Allocated-vector editor compatibility (2026-10-03):** Primitive sources now emit V5 allocation ownership per object, derived from the qualified ledger and checked against Retail/Current table counts. The browser accepts enlarged tables only with matching growth, bounded native indices and unchanged retained/authored face ownership. Existing faces can reference appended vertices/normals; resetting a retained face restores its Retail references without removing allocated rows. The main vector editor labels rows without Retail counterparts and disables their Retail reset while retaining Current edit/discard behavior.

Validation: 34 focused Python tests ran, with 31 passing and three existing Retail-fixture skips. Actual synthetic V5 models with and without a retained-removal base passed primitive edit/reset and Undo/Redo, material editing, and real GLB no-op/export/import roundtrips editing an allocated vertex. Actual backend primitive/material/GLB sources and reviews qualify in their JavaScript adapters. Four Node suites pass, including mounted vector-handler regression checks for allocated vertices, the first normal in an empty Retail table, retained resets and invalid indices. Editor syntax and diff checks pass. No game was launched; this milestone does not establish live rendering or gameplay acceptance. Retail/native allocated-vector package qualification, topology allocation through GLB, new objects/groups and the broader SDK specification remain unfinished.

**Allocated-vector reference inspection (2026-10-03):** Vertex and normal reference endpoints now emit V3 reports for V5 models, distinguishing retained Retail rows from appended Current rows with explicit vector counts/origin. Appended rows have null Retail coordinates and an empty Retail user list; the endpoint never reads an absent Retail row. Existing source rows retain both layers. Browser validation checks the origin/index/count relationship and absent-counterpart contract, keeps complete retained/authored face coverage and correct source/current byte bounds, labels allocated rows and disables their Retail layer. Current face links continue to carry stable authored IDs; stale inspections withdraw navigation.

Validation: 22 focused Python tests and three Node reference suites pass. New cases cover used/unused allocated vertices and normals, retained rows, retained-removal bases, read-only state, HTTP stale/bool/out-of-range rejection, and the first normal allocated into a zero-row Retail table. Node DOM fixtures verify the disabled Retail option, Current labels, authored navigation and stale withdrawal, with identity/count/null-coordinate tamper rejection. Twelve actual backend reports qualify in JavaScript across retained, allocated and unused rows with and without a retained-removal base. No new browser rendering or native session ran in this milestone.

This resolves reference-panel ownership for appended vectors. Primitive/material/GLB and other panels still need enlarged-table compatibility checks, followed by Retail/native allocated-vector package qualification. New object/group allocation, animation import and the broader scene/runtime specification remain incomplete. No game was launched or controlled; offline work and the full goal remain active.

**Vector-allocation browser controls and review qualification (2026-10-03):** Added an Edit-mode model-editor action for appending object-local vertices or stored normals. The dialog accepts bounded signed XYZ triples, reports Current counts/new index ranges and remaining native/global budgets, renders Current/Proposed layers, invalidates review after input/context changes and submits only the reviewed hash. Browser adapters qualify stable face coverage, table/range/pointer ownership, exact requested new XYZ, preserved old vertices, rebased triangle references and unchanged face material/UV/color/normal content. The camera frames referenced geometry so distant unused new vectors do not shrink the visible mesh. The SDK advertises the capability and serves the module.

Validation: the Node vector-allocation suite and editor syntax check pass. Nineteen focused Python tests pass, including actual server module GET, API/history/Save/Open/Build, pose previews, replay and native allocation. Actual synthetic backend reports passed isolated headless Edge smoke checks for both vertex and normal allocation, both layers, changed-input Apply withdrawal and a single reviewed-hash submission. A screenshot was inspected; the smoke serves fixture-backed responses and is not a full styled-editor or live-runtime acceptance test. Browser pointer qualification also led to a native allocator fix: extending an existing table at EOF must precede allocating an empty table at the same EOF. A tight-layout regression confirms correct XYZ, table pointers and allocation order.

This supplies the pending allocation browser workflow. Other panels' new-vector ownership, GLB topology import and Retail/native qualification of allocated-vector packages remain pending, alongside new object/group allocation and the broader scene/animation/runtime specification. No game was launched or controlled; offline work and the full goal remain active.

**Reviewed vector-allocation project and HTTP commands (2026-10-03):** Added source inspection, read-only review and reviewed-hash Apply for new native vertex/normal rows. Source reports carry Current table counts, native limits, the remaining replay-wide row budget and stable topology. Reviews expose exact new row ranges/pointer relocations alongside Current/Proposed geometry, and independently compare direct allocation with complete V5 replay. Apply retains the independently qualified base and ledger through the existing immutable model asset/history mechanism. Face additions share that publication helper, which now rechecks the scene source immediately before history publication.

Validation: 63 focused Python tests pass without skips. Actual allocation commands cover read-only preview with unchanged asset files, wrong reviewed hashes, Undo/Redo, later new-normal editing, faces using newly allocated vertices, Save/Open and normal synthetic-disc Build with exact packed-model readback. A first allocation also wraps an ordinary independently qualified base. HTTP source/preview/Apply tests reject stale source/model hashes, extra fields, empty/malformed requests, duplicate table owners, boolean indices/coordinates, injected padding and repeated Apply without changing bindings/history. A source change after immutable asset preparation also prevents history publication. Existing face-addition, removal/restoration, GLB, vector replay and preview regressions remain passing.

This completes backend command publication, not editor/browser controls. Browser source/review adapters and controls, other panels' new-vector ownership, GLB topology import and Retail/native vector-allocation qualification remain pending. The broader SDK/editor/runtime specification remains incomplete; no game or browser session ran, and offline work stays active.

**Enlarged-vector model preview composition (2026-10-03):** Model previews now accept vector-count growth evidenced by a V5 binding already qualified by the project reader. The preview checks candidate hash/length, native ownership, bounded allocation requests and exact per-object growth. It updates object vertex ranges while retaining existing rigid channels, rebuilds candidate triangle/material data and applies the same channels to all frame vertices. Party-style prefixes continue to omit trailing equipment objects even when those objects grow. Current previews carrying an authored ledger must be an exact operation prefix of the proposed ledger; their existing allocations are subtracted so later allocations/content edits do not double-count growth.

Validation: 43 focused Python tests ran: 40 passed and three existing Retail-dependent cases were skipped. Four new cases cover complete unposed geometry, rotated/translated posed prefixes, frame transforms with independently checked new-row coordinates, later-object range shifts, new face indices, omitted equipment bounds, shared scene-instance immutability, successive V5 allocations/content previews and rejection of stale payload bindings, wrong counts/owners, invalid Current ledger ancestry and mismatched channels. Legacy shape/material/primitive/removal/addition preview regressions and vector replay/Build consumer tests remain passing. No browser or native session ran in this milestone.

This supplies preview composition for qualified bindings, not the vector-allocation project command or browser controls. Source/review/API/editor publication, other panels' new-vector ownership, GLB topology import and Retail/native qualification remain pending. The broader scene/animation/runtime specification stays incomplete; offline work and the full goal remain active.

**Vector allocation replay ledger and Build consumers (2026-10-03):** V5 ledgers add a typed `allocate_vectors` operation with exact table requests and chained hashes. Stable face identities remain unchanged when vectors are appended; further face additions may use the new indices. Content, removal and restoration operations preserve V5, including allocation between full-group deletion and packet restoration. The replay-wide budget permits at most 4,096 allocated rows across all operations, in addition to existing native table, model byte, metadata and 64-operation limits. V1/V2/V3/V4 remain readable and reject the new operation.

Validation: 51 focused Python tests pass. New cases cover lit faces using new vertices/normals, later edits of a new row, exact packet deletion/restoration, full-group origin recovery, JSON replay, immutable requests/ledgers, malformed schemas/hashes/requests, operation limits and the real cumulative 4,096-row boundary. A synthetic fixture installs a qualified V5 binding and passes existing project reads, later new-row vector-edit Undo/Redo, Save/Open and normal Build with exact packed-model readback. The fixture does not invoke a vector-allocation project command or prove browser/scene-preview support.

Vector-allocation commands, project/HTTP/browser source/review controls, preview adaptation for enlarged vector tables, GLB topology import and Retail/native qualification remain pending. New objects/groups, animation import and the broader SDK/runtime specification remain incomplete. No game was launched; no immediate gameplay verification is required and the full goal remains active.

**Native vector allocation codec (2026-10-03):** Added a source-bound allocator for appending vertex and normal SVECTOR rows to existing objects. It preserves all existing indices, vector padding, primitive packets, footers and opaque bytes while rebasing used table pointers and updating only requested vector counts. Previously unused vector tables receive an owned allocation at EOF rather than using their unused pointer. New rows contain explicit signed 16-bit XYZ and zero padding; no normal recomputation is implied. Requests reject duplicate table owners and are bounded to 4,096 new rows, 8,192 addressable rows per table and the existing 4 MiB model limit.

Validation: 26 focused Python tests pass. New evidence independently removes every insertion and restores only permitted header words to recover the complete original model byte-for-byte across four adjacent tables in two objects. Actual face packets use new vertices and normals without renumbering retained faces. The last addressable vertex (index 8,191) is accepted by the face codec, and another row is rejected. Empty normal-table allocation, exact zero-padded new rows, signed boundaries, hash/candidate tampering, duplicate/malformed requests and byte/row budgets are covered. Existing addition/removal/restoration ledger and reinsertion regressions pass.

This is internal allocation groundwork, not an editor vector-allocation command or retained-ledger operation. Ledger replay, project/HTTP/browser publication, GLB topology import and normal Build/native-reader qualification of new vector allocations remain pending. New objects/groups and the broader SDK/runtime specification remain incomplete. No game was launched; offline work and the full goal remain active.

**Real Retail restoration package/native-reader qualification (2026-10-03):** In an isolated copy of the saved Town01 project, the actual reviewed commands removed and restored one retained face and one authored face. Both restored packets match the preceding model exactly and current vectors are unchanged. The model grew from 4,752 to 4,796 bytes because deletion slack is preserved. Its restored SHA-256 is `f647f23827e9a6562d28afdb85abbee7dbc4945bbb6601d13feb6aaa4df51aa6`.

Normal Build emitted a private format-7 package with one relocation payload, no overlays and one additional PROT sector. The payload is 121,272,992 bytes, SHA-256 `b38aa54ea37f4bf7df7982fed4d1a83d55cbc752fe3d4c4dd35b839f81e1340e`; the ZIP is 72,034,620 bytes. Exact restored and neighboring edited model readback passed; all 112 unedited model slots and the original five other resources were preserved, allowing only zero allocation padding. Build left project/history unchanged, Save/Open retained the restored model, saved Build integrity verified, and private RunService staging accepted the payload without creating a process.

A freshly compiled isolated MSVC harness using runtime sources at `d3017aed` passed native activation, every replacement PROT user-sector read, every replacement raw-sector payload/address/subheader/EDC/ECC check, all metadata-sector reads and netplay clearing back to stock count/state. Existing CRT and size-conversion compiler warnings remain; this is not a warning-free compile or a fresh full-game executable build. Private proof and scripts are under `local-output/sdk-20260909/retail-restoration-build-20261003/parent/`. The source disc hash remains `e6120a5d70716dd2f026a2da32d0171d52651971b52c4347a68541299f75258c`; no full Retail disc was exported and no game was launched or controlled.

This supplies the pending Retail restoration package/native-reader evidence. Runtime rendering/behavior still awaits deferred manual gameplay verification. New vectors, objects and groups, animation import/retarget and the remaining scene/runtime specification remain incomplete; the full goal stays active and offline work can continue.

**Stable restoration project/HTTP/browser workflow (2026-10-03):** Added reviewed restoration of deleted source and authored faces in retained model ledgers. V4 source reports expose bounded deletion metadata and immutable group/order ownership; requests carry exact stable identities rather than stale Current indices or packet data. V2 restoration reviews qualify the selected identities, remaining deletions, reinserted order/groups, vector ownership, triangle counts and hash changes. Apply uses the existing transactional project path, preserving the qualified base binding and V4 ledger. The browser lists deleted face indices per object, maps them to stable IDs, renders Current/Proposed layers and withdraws Apply when selections change. Ordinary Retail restoration and V3 removal sources remain compatible.

Validation: 42 focused Python tests and the Node removal/restoration suite pass. Actual project commands cover reviewed hashes, read-only preview, Undo/Redo, later vertex edits, Save/Open and normal synthetic-disc Build with exact packed-model readback. HTTP tests cover authored restoration, stale source/model hashes, duplicate/unknown identities, injected packet fields, wrong reviewed hashes and repeat Apply rejection without history changes. Isolated headless Edge smoke checks using actual synthetic backend reports and the real renderer pass for both source and authored restoration, both preview layers, stale Apply withdrawal and exactly one reviewed-hash submission; a screenshot was inspected. HTTP responses in the browser smoke are fixture-backed; this is not full styled-editor or native gameplay acceptance.

This supersedes the pending restoration command and browser adapter items. Real Retail restoration package/native-reader qualification and deferred gameplay verification remain to be gathered; new vector/object/group allocation and the broader SDK/editor/runtime specification remain incomplete. No game was launched or controlled, and offline work remains active.

**Stable restoration replay ledger (2026-10-03):** V4 ledgers add a bounded `restore_faces` operation containing only stable identities and chained hashes. Replay recovers packet preimages in the same pass and reinserts them without recursive replay or caller-supplied packet bytes. Restored identities become active, leave the deleted set and may serve as later donors. Subsequent deletion captures a fresh preimage; historical authored identities and creation budgets remain reserved. Content and removal operations preserve V4. Older V1/V2/V3 ledgers remain supported and reject restoration operations.

Validation: 34 focused Python tests pass. New cases cover partial/full-group restoration, content and additions after restoration, deletion/restoration cycles, fresh deletion hashes, JSON roundtrips, forbidden identity reuse, nonrecursive replay, tampered operation fields/hashes and operation budgets. A synthetic fixture installs a qualified V4 binding and verifies existing project reads, later vertex-edit Undo/Redo, Save/Open and normal Build with exact packed-model readback. This is consumer/codec evidence, not a restoration project command or browser acceptance test.

Project/HTTP restoration command publication, source/review adapters and browser controls remain pending. The broad SDK/editor/runtime specification and deferred gameplay checks remain incomplete; no game was launched and offline work continues.

**Deleted-face reinsertion codec (2026-10-03):** Added an internal source-bound codec that restores exact recorded source/authored packets into their original groups, keeps surviving packet bytes and current group settings, recovers absent-group descriptors and opaque footers, preserves stable ordering, grows primitive streams and rebases existing object table pointers. Bytes outside replaced streams are copied unchanged; unused table pointers remain unchanged. Complete native model qualification runs before return, with bounded allocation and unique deleted-identity selection.

Validation: 30 focused Python tests pass, including all 24 supported packet flag layouts, byte-exact packets/footer/terminal/suffix checks, complete group removal, an empty object with another supported object remaining, two-object pointer rebasing, surviving vertex and transparency edits, authored packet restoration, input immutability, malformed selections, tampered replay and allocation-budget rejection. Existing project/HTTP removal, content/history, panel and GLB regressions pass.

This completes internal packet reinsertion groundwork only. Restoration ledger operations, project/HTTP/browser publication and end-to-end restoration Build qualification remain pending. Removed allocation slack is preserved rather than reclaimed. No game was launched; no immediate gameplay verification is required and the full SDK goal remains active.

**Replay-derived restoration packet sources (2026-10-03):** Added an opt-in capture API that recovers deleted face packets only after complete qualified ledger replay. Each detached record retains the exact packet, descriptor and opaque footer from the deletion preimage, its input hash/size/offset, stable face metadata, original group in the qualified ledger base and permanent ordering. Authored origins follow recorded donor chains across group compaction. No caller-provided raw packets are added to the ledger, and ordinary replay does not collect or retain these restoration copies.

Validation: 25 focused Python tests pass. New evidence compares independently sliced pre-deletion bytes with captured packet/descriptor/footer bytes after material edits, verifies original group 1 after Current group compaction to 0, checks source/authored permanent order, detached output and unchanged input ledgers, and rejects stale hashes, unknown identities and injected packet fields through full replay. Existing ledger, project/HTTP removal, post-removal panels, content/history and GLB tests remain passing.

This supplies verified restoration inputs, not a restoration command. Packet reinsertion/allocation, restoration replay operations, project/HTTP/browser integration and end-to-end Build qualification remain unfinished. No game or browser session ran; the full SDK goal stays active and offline work can continue.

**Post-removal panel ownership and history counts (2026-10-03):** Material packet groups now derive their original Retail owner through the complete qualified donor chain, including deleted donors. Authored-only surviving groups retain the correct original group after compaction; the browser accepts these groups while retaining ordered group ownership, header/layout and retained-face checks. GLB V3 bindings accept zero active authored faces without discarding the stable topology fingerprint or ledger. The addition panel separates active faces from the historical creation budget, accepts recorded deleted donor provenance, rejects deleted ID reuse and checks that reviews preserve deleted identities.

Validation: 23 focused Python tests and all three Node material/GLB/addition suites pass. New cases cover authored-only material editing, subsequent additions from surviving authored donors, a second Retail group compacting to Current group 0, and GLB no-op roundtrips with zero active authored faces. Actual backend source/review data for material, GLB and addition workflows qualifies in JavaScript for both authored-only and zero-active-authored cases. Existing project/HTTP removal, history, typed content and ledger regressions remain passing. No new browser-rendering or native gameplay session ran.

This supersedes the pending authored-only group and zero-active-authored panel items. Stable ledger restoration, new vector/object/group allocation and the broader SDK/runtime specification remain incomplete. No immediate gameplay verification is required; the full goal stays active.

**Browser removal adapter for stable ledger faces (2026-10-03):** The removal dialog now accepts V3 stable-identity sources and V2 removal reviews. It qualifies complete Current face coverage, source/authored identity domains, duplicate/deleted ownership, selected stable IDs, surviving group compaction, unchanged vectors and reviewed triangle counts. Stable deletion counts replace misleading Retail totals. Ledger restoration stays disabled, with source-appropriate help; ordinary Retail restoration remains supported.

Validation: the Node removal suite passes legacy removal/restoration plus authored deletion, authored-only surviving groups and identity/count tamper cases. Four actual backend retained/authored removal and no-op reports qualify in JavaScript. Eleven focused Python tests pass. Isolated headless Edge smoke tests use actual synthetic backend reports with mocked HTTP responses and the real scene renderer: both retained and authored cases load, render reviewed previews, switch Current/Proposed, withdraw Apply after selection edits, require a fresh review and submit the reviewed hash exactly once. A preview screenshot was inspected. This is browser integration evidence, not native gameplay or a full styled-editor visual acceptance run.

This supersedes the pending browser source/review adapter item. Other panels still need authored-only group and zero-active-authored handling; stable ledger restoration remains incomplete. No game was launched; offline work and the full SDK goal remain active.

**Reviewed project removal after additions (2026-10-03):** The project/HTTP removal command now resolves validated Current face selections to stable ledger identities and retains the original independent base plus the complete addition/content/removal ledger. Source reports expose active stable identities and deleted IDs; reviews identify the exact deleted IDs and replayed topology. Private replacement bindings remain internal. Reviewed hash, source key and current payload freshness gate publication; empty selections leave history unchanged.

Validation: 36 focused Python tests pass. New evidence covers retained and authored removals, HTTP source/review/Apply, wrong candidate and stale-repeat rejection without mutation, Undo/Redo, later vector edits, Save/Open, and normal Build using the real relocation packager with exact reopened model bytes after a retained-face removal. Earlier ledger, removal/restoration, addition/content, GLB, reference and normal Build tests remain passing. No game was launched.

This completes the backend command integration, not the browser feature. Browser V3 source/V2 review adapters, authored-only surviving group mappings, zero-active-authored GLB bindings and ledger restoration remain unfinished; old browser removal decoding rejects the new schema rather than guessing identities. Ledger restoration explicitly rejects until stable restoration ownership is implemented. The full goal remains active; no immediate gameplay verification is required.

**Typed face-removal replay groundwork (2026-10-03):** The pure model ledger now supports V3 stable-identity removal operations after additions and content edits. Removal uses the independently qualified allocation-preserving face codec, checks operation pre/post hashes, compacts surviving Current face and group indices, and retains deleted identity records. Deleted authored IDs remain reserved and still count against the historical 128-face budget; deleted faces cannot be donors. Content edits and later additions retain V3. V1/V2 replay remains compatible.

Validation: 32 focused Python tests pass. New cases independently compare removal bytes with the existing codec, drop a complete packet group, edit vectors between removals, remove an authored face, add from a surviving remapped donor, serialize/replay, reject deleted ID reuse and donors, reject malformed/stale operation chains without input mutation, and enforce the shared 64-operation limit. Existing addition/content, GLB, reference, removal and normal Build regressions remain passing.

This is replay-layer groundwork, not a completed editor feature. Project reviewed removal commands, panel mappings when an authored-only group survives, restoration and end-to-end Build evidence for V3 removals still need integration. Existing editor commands do not create V3 removals yet. No game was launched; the full SDK goal remains active and offline work can continue.

**GLB interchange after face additions (2026-10-03):** The SDK now exports and imports the effective model after additions and typed content edits through the real GLB codec. A V3 sidecar binds the current model/profile to a freshly qualified stable topology fingerprint and authored face count. The fingerprint includes retained Retail mappings and authored identities, so changing stable identities invalidates an older sidecar even when model bytes remain identical. V1 ordinary and V2 removal sidecars remain supported.

V3 reviews explicitly audit Current addition topology; they do not mislabel current packet offsets as Retail changes. Position edits and authored-face RGB edits append typed content operations while retaining the independent base and addition ledger. Tests cover exact no-op export roundtrip, reviewed Apply, Undo/Redo, Save/Open, stale/forged bindings and review keys, retained removal bases, and actual HTTP export/review/import endpoints. The focused Python run completes 25 tests with three Retail-gated skips; both Node GLB suites pass, and four actual backend export/import reports qualify in JavaScript. No game, external DCC application or browser-rendering session ran; gameplay appearance remains deferred.

This supersedes the pending existing-layout GLB composition item. GLB does not allocate further faces/vectors/objects/groups; count-changing post-addition removal/restoration and the broader SDK/runtime specification remain incomplete. Offline work can continue without immediate gameplay verification; the full goal remains active.

**Stored vector-reference navigation after face additions (2026-10-03):** Normal and vertex user reports now expose V2 retained Retail mappings, stable authored face identities, complete Current face counts and separate Retail byte bounds. The reports qualify the independently retained base and full addition/content ledger before inspecting stored operands. Normal and vertex edits remain read-only in these reference panels; vector/content authoring stays in the existing reviewed tools.

Both panels accept retained index gaps, reject overlapping/duplicate/missing authored ownership, and show authored faces without inventing a Retail counterpart. Current and Retail links navigate to the actual Current face index; authored links carry their stable face identity. Stale selection/source changes withdraw the links. Earlier removals compose with later additions; baked-color faces still report no stored normal operands. Validation: 28 focused Python tests pass, including real HTTP reference endpoints, unchanged project/history, stale hash/key rejection, later vector edits, retained removal bases and normal operand absence. Three Node suites pass for legacy decoders, authored ownership/navigation and stale withdrawal. Four actual Python reports (normal/vertex, addition/removal base) qualify in JavaScript. No game or browser-rendering session ran; runtime visibility and normal shading remain deferred.

This supersedes the pending stored vector-reference panel item. GLB workflows, count-changing post-addition removal/restoration, new vectors/objects/groups and the broader SDK/runtime specification remain incomplete. Offline work can continue without immediate gameplay verification; the full goal remains active.

**Material inspector after face additions (2026-10-03):** The material source now carries V3 explicit retained Retail face/group mappings and stable authored face identities. The panel accepts gaps from added faces, checks complete ownership coverage and UUID uniqueness, and keeps Retail reset available only for retained faces. Authored texture page/CLUT edits and shared packet-group ABE edits use the existing reviewed commands; all current group members, including authored faces, appear in the audit. Existing V1 sources and V2 removal mappings remain compatible.

V2 material reviews explicitly compare against Current addition topology, rather than reporting current offsets as Retail offsets. Review/Apply preserve the typed V2 face ledger, independently qualified retained base, stable identities, Undo/Redo and Save/Open. Tests cover retained removal bases, no-op review, stale source/hash/review-key rejection, actual HTTP source/review/apply envelopes and panel reset/discard/review lifecycle. The focused Python run passes 51 tests with one Retail-gated skip; all three Node material/donor/primitive suites pass; backend source/review data also qualifies in JavaScript after the HTTP asset identity decoration. Normal Build and pack-growth regressions remain passing. Gameplay appearance, live VRAM residency and hardware blending remain deferred; this checkpoint does not require immediate manual play.

This supersedes the earlier pending material-panel item. Reference/GLB panels, post-addition count-changing removal/restoration, new vectors/objects/groups and the remaining SDK/runtime specification still need work. The full goal remains active; no game was launched.

**Content authoring after face additions (2026-10-03):** Added a source-bound V2 face ledger that chains typed existing-layout content edits between addition batches. V1 ledgers remain readable. Each operation qualifies exact input/output hashes, ordered bounded byte preimages and complete typed model-content ownership; count/pointer/opaque changes reject. Stable source/authored face identities survive vector/normal, face vertex/UV/RGB, material and object edits, then further additions using an authored donor. Limits remain eight addition batches/128 authored faces, plus 64 total operations and 2 MiB finite ledger metadata.

Project model writes retain the original independently qualified base binding and append content operations. No-op writes preserve history. Current-topology TMD/OBJ/JSON preparation and object transforms can compose with additions; reports identify Current comparison rather than claiming a Retail topology comparison. Undo/Redo, Save/Open, export input snapshots, model-pack preparation/rebuild and normal relocation Build preserve the composed payload. Count-changing removal and GLB workflows are not covered by this checkpoint.

The face editor now accepts V4 explicit Retail/authored ownership maps, including gaps from added faces. Authored faces can be selected/edited; Reset to Retail is disabled when no Retail owner exists. Retained-face comparison still uses the actual Retail row. Ownership coverage, monotonic retained identities, authored UUID uniqueness/counts and row bounds reject malformed reports.

Validation: focused Python regression plus the Node face-editor source/draft/review/lifecycle suite pass. Coverage includes content between additions, edited authored donors, vector and normal edits, face UV/RGB/reference edits, material fields, object translation, history, Save/Open, retained-base snapshot bytes, pack readback and normal Build/archive readback with a V2 ledger. Stale/opaque/count changes, malformed runs/preimages/hashes and operation budget overflow reject without project/history mutation. Node coverage includes V4 ownership errors, authored selection, disabled Retail reset and Current draft discard. No Retail requalification, actual browser rendering or game launch ran in this checkpoint; earlier Retail V1/runtime qualification remains separate evidence. No immediate gameplay verification is required.

Remaining: topology-aware material/reference and GLB panels, post-addition removals/restoration, and new vector/object/group authoring still need independent ownership/integration work. The full SDK goal remains active.

**Retail model-growth package and fresh runtime qualification (2026-10-03):** Normal Build now passes on an isolated saved Town01 project containing two authored faces over retained content-v3 model 9 plus an independent model 8 shape edit in the same pack. PROT grows from 121,253,888 to 121,255,936 bytes (one sector). Both saved payloads reopen exactly; all 112 unedited model slots and the original bytes of all five other resources are preserved. Only zero allocation padding is added after the final resource. Build leaves the project unchanged; reopening and saved Build integrity verification pass. Private run preparation accepts the 121,272,992-byte relocation payload and records its expected hash/count without starting a process.

Fresh MSVC isolated native activation passes against the original verified Retail BIN. It compares every proposed PROT byte and every relocation metadata sector through the C reader. All raw PROT sectors also match proposed user bytes, source-derived first/terminal subheaders, relocated addresses and regenerated EDC/ECC. Netplay clear restores the original reader count and clears relocation status. Payload SHA256: `467734a7805f5d4312bc79b922108a4b81d31d89e6490bfc98bed14b1d200ecb`; package ZIP: 72,034,628 bytes. Private artifacts/proof: `local-output/sdk-20260909/retail-model-growth-build-20261003/parent/`. No Retail disc image was exported; proprietary package/source material remains private and ignored.

The complete stability runtime target configures offline from cached dependencies, compiles and links successfully in Release with two build workers. Its revision stamp is `nightly-565-g3322686e`, and binary SHA256 is `f584a9c44f74c22b0ccf62596bfbca6a480c8f0f5d64c1855dc606b6cd2b805f`. Binary: `local-output/stability-20260909/build/Release/LegaiaStability.exe`. An initial MSBuild attempt rejected duplicate inherited PATH/Path names; normalizing environment names resolved it. Regenerating CMake also corrected a stale cached revision label. Existing compiler/parser warnings remain. The game binary was not executed: isolated reader activation is not live Build & Run, visual/editor parity or gameplay acceptance.

Gameplay remains queued for later user verification. Offline work can continue on post-addition model authoring and the remaining SDK specification; this qualification does not mark the goal complete or require immediate manual play.

**Relocation-aware saved Builds and run preparation (2026-10-03):** Saved Build verification and private run preparation now share an exact audited payload inventory. Format 7 relocation packages qualify their sole asset/hash/length and binary readback; composed source overlays remain audit inputs rather than separately installed assets. Output overlay counts describe emitted overlays. Private staging accepts the native 256 MiB relocation payload bound with bounded manifest overhead, rejects unexpected/mixed inventory and descriptor tampering before staging, and retains the feature selection plus expected payload hash/virtual sector count. Ordinary overlay packages keep the prior 64 MiB private bound.

Runtime `mod_status` now reports active relocation count, prepared reader activity, virtual sector count, reader acquisitions since plan reset and payload SHA256. SDK readiness requires the exact active relocation and at least one CD reader acquisition; older/missing observations, wrong hash/count, inactive readers and zero acquisitions reject readiness. This is process/plan identity preparation, not scene acceptance or sector-consumption proof.

Validation: 30 focused Python tests pass (3 Retail-gated skipped), including actual normal-Build history integrity/tamper checks, exact private staging without process launch, descriptor size/hash/path/budget rejection and readiness mismatch cases. Fresh MSVC native mod-runtime regression passes, proving status before/after handle acquisition and reset on netplay clear. The debug server passes GCC C11 syntax qualification with existing cached SDL3 headers; its actual status handler compiles independently with `-Wall -Wextra -Werror` and active/cleared JSON round trips parse correctly. Private protocol proof: `local-output/sdk-20260909/relocation-package-consumers-20261003/parent/`; runtime build/log: `local-output/sdk-20260909/mod-disc-relocation-20261003/parent/`. Existing native compiler/parser warnings remain. Full runtime/game build, Retail package activation and live Build & Run were not run. No game or runtime installation was performed; gameplay remains deferred.

Remaining: qualify the complete Retail model-growth package and rebuilt runtime without launching gameplay, then retain the gameplay queue for explicit user verification. The full SDK specification remains unfinished, including post-addition model authoring, scene/runtime parity, animation and script coverage. Earlier overlay-only-consumer checkpoints below are historical.

**Normal Build relocation package composition (2026-10-03):** Normal SDK Build now gathers all saved models sharing a topology-growth pack, defers them from legacy shape overlays, composes ordinary PROT patches at original offsets before growth and emits one format 7 `disc_relocation` feature payload. Source-bound external Form 1 edits are composed into mapped sectors; overlap, stale hashes, PROT-boundary straddles, ISO metadata conflicts and native payload budgets reject. The existing format 6 path remains for builds without topology additions. Review computes/verifies proposed bytes without writing output; packing validates the emitted relocation asset, and repeated builds are deterministic.

Validation: 36 focused Python tests pass (3 Retail-gated cases skipped). New normal Build regression uses actual synthetic Mode 2 ISO sectors, saved addition/retained-shape bindings in one pack, original-offset patch composition, independent reopened model payload comparison, the real generic psxmod packer and archive readback. External edits crossing a sector boundary map correctly. A fresh MSVC native harness accepts/activates an SDK-emitted synthetic package, compares every proposed PROT/metadata sector through the C disc reader and restores stock count on netplay clear. Private proof: `local-output/sdk-20260909/model-growth-normal-build-20261003/parent/`. Existing native compiler/parser warnings remain. No Retail package/game launch, installation or full Retail ISO/BIN export ran; gameplay remains deferred.

Remaining integration: saved Build history verification and Build & Run still assume an overlay-only inventory/private size bound. Those consumers need relocation-aware inventory and runtime observation before this package is offered as a complete Build & Run workflow. This checkpoint supersedes the earlier claim that normal Build cannot emit growth packages; it does not complete the full SDK or prove Retail/gameplay acceptance.

**Runtime relocation publication and C reader lifetime (2026-10-03):** Commit now stages a fresh reader, rechecks whole-source SHA256 before/after native preflight and publishes only after successful plan/state preparation. The opaque C disc handle acquires the prepared reader for the bound source path. Competing source paths reject; replacing an active relocation invalidates old handles. Closing one shared handle leaves the other live. Netplay clear and reinitialization remove relocation from retained readers and restore stock layout. Failed recommits preserve the published reader. This supersedes the earlier unfinished-activation checkpoints below; normal SDK Build still emits format 6 ordinary overlays and does not yet compose/package model growth.

Validation: fresh MSVC mod-runtime regression passes both its built-in public synthetic source/payload and the independently Python-generated synthetic fixture. Coverage includes 60-to-62 sector mapping, replacement user/raw terminal framing, shifted movie/tail reads, undersized/out-of-range output preservation, wrong source, changed payload, same-path changed source, failed-commit isolation, plan replacement, shared close, netplay clear and reinitialization. The C bridge is now linked into the CMake regression target. Existing compiler/parser warnings remain; the full runtime/game build was not run. Private build/log: `local-output/sdk-20260909/mod-disc-relocation-20261003/parent/`. No game, installation or full Retail disc export ran; gameplay remains deferred.

**Native PVD/path-table relocation qualification (2026-10-03):** Activation preflight now qualifies mandatory/optional path tables in both byte orders, within a 1 MiB table budget. Original extents must belong to inventoried source directories; complete expected records are derived with exact insertion shifts while preserving names, parent identifiers and odd-name padding. Proposed PVD pointers and complete table bytes must match, including absent optional copies. The entire PVD must match its source transformation, preserving fields outside volume-size, table-pointer and root-extent updates. Invalid tables or post-install mismatches roll back the reader. Runtime publication/lifetime and normal Build remain unfinished; commit's activation guard remains.

Validation: fresh native ISOReader/preflight regression passes under MSVC. The source fixture now carries all four mandatory/optional LE/BE copies. New cases reject wrong mandatory/optional directory extents, changed odd-name padding, incorrect optional pointer and unrelated PVD mutation, preserving source layout. Native preflight also accepts the Python-generated payload and complete synthetic Mode 2 source fixture, reopens PROT at 8192 bytes and MOV/MOVIE.STR at LBA 50 in the grown 62-sector view. Private fixture: `local-output/sdk-20260909/relocation-path-table-preflight-20261003/parent/`; native build/log: `local-output/sdk-20260909/iso-reader-relocation-20261003/parent/`. Existing parser/library warnings remain; full runtime suite not run. No game, helper, installation or full Retail disc export ran; no immediate gameplay gate is added.

**Native relocation activation preflight (2026-10-03):** Added a parsed-payload preflight on an unmodified reader bound to the committed source identity. Original PROT/metadata hashes qualify first. A bounded source ISO inventory records every file/directory identity, allocation and child count, rejecting overlaps with PROT, invalid extents/names, duplicate paths and traversal budgets. After native installation, root and all reopened entries must match the expected insertion mapping; directory membership must remain unchanged. Complete proposed PROT readback is streamed and hashed. Failed post-install checks roll back to the source reader layout. This is preflight, not yet runtime publication/activation.

Validation: fresh MSVC ISOReader/activation regression passes, linked to existing libchdr and native SHA256. New cases reject stale source hash, an incorrectly relocated movie and an extra hidden directory entry, with rollback preserving source state; valid preflight exposes the grown PROT and correctly shifted movie. Existing ISOReader mapping/lifetime cases also pass in this executable. Private build/log: `local-output/sdk-20260909/iso-reader-relocation-20261003/parent/`; helper setup: `local-output/sdk-20260909/relocation-activation-preflight-20261003/parent/`. Existing parser/library warnings remain. Full runtime suite not run. Runtime commit still explicitly rejects relocation until publication/lifetime is connected; path-table semantic qualification and normal Build integration remain unfinished. No game, helper, installation or full Retail export ran; no immediate gameplay gate is added.

**Feature relocation manifests and resolver conflicts (2026-10-03):** Added format-version 7 `[[disc_relocation]]` declarations with exact feature/file/SHA256 fields. A declared feature, source-disc SHA256 target, safe relative asset path and strictly qualified native payload are required; duplicate owners, unknown fields, malformed payloads and older format versions reject. Catalog channel pruning includes relocation declarations. Enabled features reread/requalify payload bytes during resolution; the resolved payload hash/ownership participates in the plan fingerprint. Multiple active providers and combinations with active disc writes, overlays or legacy derived discs reject and clear the unresolved plan. Main-EXE writes remain separately addressable. Runtime commit explicitly rejects selected relocations while activation is unfinished, preventing silent stock fallback.

Validation: new relocation manifest/resolver regression, existing complete mod-package regression and updated mod-runtime regression pass. Coverage includes declaration rejection, disabled/enabled selection, fingerprint difference, installed payload tampering, competing providers, overlay conflict and failed-plan isolation. The runtime regression proves an enabled relocation that cannot activate rejects commit with an error. Native builds report existing TOML/parser warnings; the MSVC helper requires normal NOMINMAX configuration. CMake regression registered; full framework suite not run. A fresh read-only source metadata check finds PROT size 121,253,888 bytes, within the unchanged 256 MiB loader limit. Private builds: `local-output/sdk-20260909/mod-disc-relocation-20261003/parent/`. Activation and normal Build remain unfinished; SDK Build still emits format 6 ordinary overlays. No game, installation or full-disc export ran; no immediate gameplay gate is added.

**Native relocation payload parsing/source verification (2026-10-03):** Added native `PSXDRLOC` v1 decoding with the whole-package expected SHA256, strict header/extent/budget/length checks, complete proposed PROT hash and canonical metadata ownership/candidate hashes. Parsing stages a detached result and preserves the previous output on rejection. A separate verifier reads the unmodified committed source, checks physical sector count, hashes the complete original PROT and compares every metadata preimage. It also detects mutations to parsed candidate PROT/metadata data. Feature manifest/resolver/activation and complete ISO qualification are still separate unfinished integration.

Validation: fresh standalone native regression compiles with GCC C++17 `-Wall -Wextra -Werror` and passes. Tests cover valid parsing/source verification, changed source count/PROT/metadata, failed reads, candidate mutation, malformed headers/ownership/order, stale manifest hash, truncation/trailing bytes and failed parse isolation. A Python-generated 18,888-byte payload, SHA256 `88ec8609e1e62340b14fee948057c78d678ecda9332bcdaf5409eea57c53b5b4`, decodes with identical PROT bytes and all five source/proposed metadata LBAs; native verification also accepts the Python fixture's actual source sectors. CMake regression target registered; full runtime suite not run. Private proof: `local-output/sdk-20260909/native-relocation-package-20261003/parent/`. No game, helper, installation or full-disc export ran; no immediate gameplay gate is added. Normal Build packages do not activate this payload yet.

**Source-bound relocation package payload (2026-10-03):** Added a binary relocation payload codec for future feature-style packages. The existing `derived_disc` vcdiff channel explicitly rejects feature-style manifests and cannot substitute for normal SDK Build. Binary `PSXDRLOC` v1 binds original PROT hash, source physical sector count/allocation, complete proposed PROT user bytes/hash and canonical relocated metadata records with original/candidate LBAs and source/candidate hashes. Typed header extents, no shrink, MSF addressing limit, 1 GiB payload/4096 metadata budgets, exact byte length and sorted ownership are verified. Encoding reopens the payload and compares complete proposed PROT/metadata bytes; package activation must verify source preimages against the live source disc.

Validation: eight package/logical-disc/ISO tests pass; after adding the preallocation budget guard the two package regressions pass again. Tests cover exact bytes/preimage roundtrip and malformed version/counts, stale package hash, candidate mutation, metadata mapping, truncation and trailing bytes. Native payload parsing, feature manifest/resolver conflict rules, activation and normal Build remain unfinished. Codec reports `runtime_connected=False`, `build_ready=False` and `gameplay_verified=False`. No game, helper, installation or full-disc export ran; no immediate gameplay gate is added.

**ISOReader relocation wiring (2026-10-03):** User/raw sector reads and sector count now use an installed native relocation plan; the ordinary C CD-reader wrappers naturally consume these APIs. Installation validates physical sector count, original ISO PROT extent/size, uniform Mode 2 Form 1 first/terminal framing, proposed PVD volume size and root bounds before enabling mapped reads. Original volume size may be below physical disc length; growth updates both without conflating them. The relocated root is exposed to file lookup; Clear restores the original root, and Close/Open discard mapping. Virtual subchannel reads enforce virtual disc bounds. Installation supports one raw data track and rejects CHD, multiple tracks/audio and SBI replacement configurations. Source/package hashes and complete ISO qualification remain activation responsibilities.

Validation: fresh native ISOReader relocation regression passes under MSVC, linked to existing libchdr libraries. It covers invalid installs preserving source layout, moved-root/PROT/movie lookup, exact replacement/movie data, raw terminal/tail reads, out-of-range isolation, virtual subchannel bounds, duplicate installation, Clear, reinstall, Close and Open. Existing SBI and CDDA regressions rebuilt against the changed reader and independently exit zero. Registered CMake target; full runtime suite not run. Compilation reports existing parser/libchdr warnings, not a warning-free build. Private builds: `local-output/sdk-20260909/iso-reader-relocation-20261003/parent/`. Package activation and normal Build remain unfinished; these APIs are not enabled by generated SDK packages yet. No game, installation or full Retail disc export ran; no immediate gameplay gate is added.

**Native raw Mode 2 relocation (2026-10-03):** Added a portable native Mode 2 Form 1 EDC/P/Q codec and address relocator. The native disc mapper now reads raw sectors: replacement payloads use source PROT first/terminal framing, relocated metadata uses its original source framing, and shifted Mode 2 source sectors change only MSF address. Replacement/metadata payloads regenerate Form 1 protection; shifted XA/Form 2 data and protection bytes remain exact. Invalid framing, non-Mode 2 shifted sources and failed callbacks reject without modifying caller buffers. Activation must still qualify source provenance and stream framing.

Validation: both standalone native codec/mapping regressions compile under GCC C++17 with `-Wall -Wextra -Werror` and pass. The codec covers valid/invalid framing, duplicate subheaders, Form 2 rejection for Form 1 encoding, idempotence, unchanged payload/header protection and MSF bounds. Native output matches the existing Python codec byte-for-byte across 64 varied sectors (150,528 bytes), SHA256 `fbf8154320112dac223168df7ea5d1278882ded7de0952775c85b519f4801089`. Mapper regression compares raw/user payloads across the full virtual fixture, terminal flags, shifted XA bytes and error isolation. CMake codec test registered; full runtime suite not run. Private proof: `local-output/sdk-20260909/native-raw-disc-relocation-20261003/parent/`. ISOReader/CD controller wiring, package activation and normal Build integration remain unfinished. No game, installation or full-disc export ran; no immediate gameplay gate is added.

**Native logical sector mapper (2026-10-03):** Added `PS1::DiscRelocation` for qualified activation to configure a PROT replacement and relocated metadata sectors. It resolves proposed logical sectors to replacement payloads, metadata payloads or shifted source LBAs, and reports the grown sector count. Configuration validates whole-sector extents, source ownership, no shrink, CD MSF range and metadata bounds/nonoverlap before replacing any active plan. Failed source reads leave caller buffers unchanged; Clear drops the plan. Package provenance/hashes and ISO qualification remain activation responsibilities.

Validation: the standalone native regression compiles under GCC C++17 with `-Wall -Wextra -Werror` and passes. It checks all sectors of a 60-to-62-sector synthetic mapping, inserted payloads, shifted metadata/source framing LBAs and final tail, same-size mapping, invalid configuration preserving the active plan, null/missing/failed reader handling and Clear. Registered `disc_relocation_test` in runtime CMake; the full runtime suite was not run at this checkpoint. Private executable: `local-output/sdk-20260909/native-disc-relocation-20261003/parent/`. Compiler runtime PATH was corrected after an idle first attempt; owned stalled processes were closed. Package activation, physical reader/CD controller wiring and raw Mode 2 framing/EDC/ECC support remain unfinished. No game, installation or full-disc export ran; no immediate gameplay gate is added.

**Relocated logical ISO readback (2026-10-03):** Added a read-only logical-disc view that borrows an open source, verifies original PROT bytes, supplies a whole-sector grown replacement and maps following source sectors to their shifted positions. The existing ISO metadata relocation transform supplies changed directory/path-table/PVD sectors. The view reopens PROT through ISO lookup and verifies its unchanged starting LBA and new byte size. Metadata sector hashes and source/proposed sector counts are recorded without exporting a BIN. Runtime currently reads physical sectors before ordinary overlays, so insertion/sector-count support remains an explicit integration requirement.

Validation: 17 focused logical-disc/ISO/composition/preparation/archive tests pass. Synthetic readback covers shifted directories, both endian path tables, PVD sector count, unchanged following movie bytes, same-size whole-disc logical identity, stale/partial/shrinking source rejection and borrowed-source lifetime. Combined composition-to-ISO coverage grows model packs with retained patches, reopens the exact emitted PROT through the relocated directory and preserves shifted neighboring edits/movie data. Raw CD sectors are explicitly unavailable from this logical view. Normal Build/package/runtime integration remains unfinished; `runtime_connected`, `build_ready` and `gameplay_verified` are false. No game, helper, installation or full-disc export ran; no immediate gameplay gate is added.

**Model relocation patch composition (2026-10-03):** Added an archive transform that applies verified equal-length patches against original PROT offsets before processing model growth requests. Exact preimage hashes, payload bounds outside the TOC, nonoverlapping patches, strict request envelopes and unique resource requests are enforced. Growth requests use the patched archive, so stale original offsets are never applied after relocation. Every selected pack is reopened again from the final archive after all resource/entry moves. A patch that changes a selected pack's qualified source is rejected. This is the composition layer for normal Build; normal Build packaging and ISO integration remain unfinished.

Validation: 17 focused composition/preparation/archive/pack cases pass. New tests cover two growing carriers with existing patches and a shifted edited neighbor; two growing resources in one carrier; both supported header locations; stale preimages, overlaps, TOC/bounds violations, source-pack mutation and duplicate/malformed requests. Other payloads and patch bytes survive relocation. The transform returns bytes and an audit only, with `build_ready=False` and `gameplay_verified=False`. No game, helper, installation or full-disc export ran; no immediate gameplay gate is added.

**Shared-pack model growth preparation (2026-10-03):** Added source-bound SDK preparation that collects every authored model sharing a pack with a face-addition binding. Retained shape/content/removal bases are independently qualified before ledger replay; ordinary edited neighbors travel in the same request. Imported ownership length includes qualified native padding, while separate slot tails remain exact. Fresh scene metadata, physical PROT ownership, descriptor/slot locators, saved candidate bytes and authored-state identity are checked. The preparation reports deferred model identities for future Build composition; normal Build does not consume these requests yet.

Validation: 23 focused preparation/pack/archive/ledger/project tests pass. Actual private Town01 preparation combines model 9's two saved additions over its retained `tmd-content-v3` base with a model 8 shape edit. Independent whole-pack reconstruction agrees; all 112 unselected models and five other compressed resources remain byte-exact. Decoded pack grows by 48 bytes; the compressed carrier grows from 227,328 to 227,336 bytes. A bounded synthetic PROT wrapper reopens the complete qualified pack successfully. Preparation leaves project/history unchanged. Pack SHA256 `4dae2aa8fce63eedb5c56e5475e63a1bf06ab0b0786dfc9525b036168b1340fb`. Private proof: `local-output/sdk-20260909/model-growth-preparation-20261003/parent/`. No game, helper server, installation or full-disc export ran. Composition with other asset patches, normal Build/ISO relocation and post-addition editing remain unfinished; no immediate gameplay gate is added.

**Face-addition editor dialog (2026-10-03):** The model viewer now offers Add model face, connected to qualified donor inspection, typed vertex/UV/RGB/normal fields, exact-request Review and reviewed Apply. Current/Proposed wireframe comparison supports pointer/keyboard orbit and zoom. Field or donor changes invalidate Review; Apply returns updated SDK state and refreshes the authored viewport. The dialog checks stable donor ownership, vector/byte domains, unchanged preview vectors/object ranges, expected face-count growth and retained identity remapping. Close aborts inspection/review and disposes owned renderer/listeners; stale/late/mode/busy/error guards preserve context and release only owned busy state. A browser-discovered close-event race is fixed by checking actual dialog open state before accepting responses. Normal Build remains unfinished and the dialog states that limitation.

Validation: seven focused addition HTTP/project Python cases, three addition/removal/allocation Node suites and editor/module syntax checks pass. Eight actual private Town01 browser checks cover typed lit donor fields, read-only Review, edit invalidation, Current/Proposed comparison, 540px containment, Apply/history/authored viewport refresh, authored donors after reopening and close/late/stale/busy/mode/error guards. Orbit/zoom preserves the accepted review. No page errors or command/Save/Build/Run requests occur; Review leaves project files and history unchanged, while reviewed Apply writes only private authored-model state. The narrow screenshot was inspected and owned Edge/server helpers closed. Private proof: `local-output/sdk-20260909/model-face-addition-editor-20261003/parent/`. No game, installation or full-disc export ran. General new vectors/groups/objects, post-addition edit/removal/GLB composition and relocated normal Build/ISO integration remain unfinished; no immediate gameplay gate is added.

**Face-addition HTTP workflow and copy dependencies (2026-10-03):** Connected source, Review and reviewed Apply through `/api/model-face-addition-source`, `/api/model-face-addition-preview` and `/api/model-face-addition`. Exact typed envelopes validate model/source/hashes and bounded nonempty requests before source work; source uses the ordinary 32 KiB request limit and Review/Apply use 256 KiB. Source reports now include qualified typed primitive/normal fields alongside stable donor identities. Apply advertises the model-face-addition capability and returns current SDK state. The editor dialog is still unfinished. Fixed input snapshots/project copy omitting the independently qualified base model retained by an addition binding: both candidate and base bytes are now captured, budgeted and verified.

Validation: 24 focused addition HTTP/project, project-copy/history and GLB HTTP regression cases pass with private disc source and no skips. New tests cover read-only Review, reviewed Apply, stale repeat/mismatched hash rejection, exact envelope/domain/body limits before source calls, base dependency inclusion, snapshot budgets and tampered dependency rejection. A fresh private Town01 HTTP proof applies a third quad over the retained normal-reference base, returns normal SDK state/capability, rejects stale repeat, and copies/reopens the project with both candidate and base files qualified. Candidate is 4,776 bytes; SHA256 `bedb291651cdcea1a1be1ec15ce98e5ec1723598e7681b89284df3d3fef38cda`. Source history is preserved by copy; owned servers close. Private proof: `local-output/sdk-20260909/model-face-addition-http-20261003/parent/`. No browser, game, installation or full-disc export ran. Editor dialog, normal Build/ISO integration and edit/removal/GLB composition after additions remain unfinished; no immediate gameplay gate is added.

**SDK face-addition binding and project workflow (2026-10-03):** Added source/review/preparation services and a reviewed ProjectService Apply method for `tmd-face-addition-v1`. The saved binding retains a separately qualified base shape/content/material/normal-reference or face-removal edit, then replays additions against those exact base bytes. Repeated batches preserve stable authored donors. Saved asset bytes, Retail source hash, nested base binding and complete ledger replay qualify on every read and project Open. Apply writes content-addressed model bytes and participates in session Undo/Redo. Preview composition now accepts changed face counts while preserving existing object/vector pose channels. No editor or HTTP action is exposed yet.

Validation: 48 focused project/ledger/carrier/archive/topology cases and 34 existing model-authoring/primitive/material/GLB cases pass, 82 total with no skips. A private cloned Town01 project retains an existing `tmd-content-v3` base, reviews/applies two batches, checks composed geometry, exercises session history and passes Save/Open plus repeated authored-donor replay after reopening. Final model is 4,752 bytes; SHA256 `331fb079ef75e6db56d92696834aa3166dd7939478ee86e7c2017b0732d324be`. Open clears session Undo/Redo under the existing project convention; saved binding state persists. Tests reject changed source/base/ledger, stale mode/source and mismatched reviewed candidates before mutation. Existing-layout editors and overlay export explicitly reject an addition binding until their composition/relocated Build paths are integrated. Private proof: `local-output/sdk-20260909/model-face-addition-project-20261003/parent/`. No browser, helper, game, installation or full-disc export ran. Editor/HTTP Review/Apply, normal Build/ISO relocation and edits/removal/GLB after addition remain unfinished; no immediate gameplay gate is added.

**Model pack PROT physical relocation (2026-10-03):** Connected the source-bound model pack/carrier codec to consecutive-start PROT allocation and raw start-table relocation. The writer reads only the selected physical owner, permits resource growth, aligns the emitted carrier to sectors and updates later starts through the established archive writer. It reopens the archive, checks readable entry identities, verifies the exact physical carrier and decoded pack, and compares all other physical payload bytes. Overlapping legacy read windows cannot supply allocation capacity. Output remains `build_ready=False`; ISO relocation and SDK project/editor/normal Build integration are separate unfinished work.

Validation: 44 focused archive/pack/carrier/ledger/addition/allocation/removal/restoration/vector and existing MAN/PROT tests pass. New cases cover both supported header offsets, forced sector growth, no-op full archive identity, stale/type/source binding rejection and borrowed read-window capacity rejection. A bounded logical archive fixture uses a freshly read Retail Town01 physical carrier: the prior two quads fit with no growth; a 34-face UV-varied candidate forces 508 carrier bytes and one sector (227,328 to 229,376 bytes). Reopened pack equals independent assembly; all 113 unselected models, other resource bytes and archive neighbors remain unchanged. Fixture candidate SHA256 `6d7deb150ce2ebff42b9d0f3fe3f942d4b37851032e57e90e645e9ead1a53b84`. Private proof: `local-output/sdk-20260909/model-pack-archive-20261003/parent/`. This is a Retail carrier inside a synthetic bounded start table, not a full Retail archive/disc build. No helper, browser, game, installation or full-disc export ran; no immediate gameplay gate is added. Project binding/history/Save/Open, removal/GLB composition, editor Review/Apply/preview, normal Build and ISO relocation remain unfinished.

**Ledger-qualified model pack/carrier growth (2026-10-03):** Added a native TMD pack writer that resolves selected slots through their source-bound face ledgers, grows member packets, updates later word-offset directory entries, and preserves all unselected slots and member trailing bytes. A scene-resource writer qualifies an explicit type-2 descriptor, recompresses the grown pack, updates decoded size, and relocates later resource offsets in four-byte increments when compressed capacity is exceeded. Exact source hashes, canonical slot directory, typed slot/descriptor identities, duplicate/alias/bounds checks and compression readback remain enforced. These codecs do not yet create an SDK override, relocate PROT/ISO, or enter normal Build.

Validation: 35 focused pack/carrier/ledger/addition/allocation/removal/restoration/vector and MAN-container tests pass. Synthetic coverage forces compressed-slot growth and verifies independent multi-slot assembly, unchanged neighbors/tails, descriptor relocation, no-op byte identity and malformed/stale input rejection. Fresh private Town01 physical-span proof grows slot 9 by 48 bytes: decoded pack 304,116 to 304,164 bytes with all 113 neighbors unchanged. Compressed size is 154,531 bytes, fitting the original 154,547-byte slot; the six-section physical carrier stays 227,328 bytes. All other compressed sections remain byte-exact and all sections decode. Exact full-pack reconstruction agrees independently. Pack SHA256 `c98654dfb61e019aca6c9852fe4611e40a42cddeec07b4f22577bfce96b93791`; physical carrier SHA256 `7638580e313da93504533e743f30c0a01e9ab7a2a1fafc2fb29f76158b6a0738`. Private proof: `local-output/sdk-20260909/model-pack-growth-20261003/parent/`. No browser, helper server, game, installation or full-disc export ran; no immediate gameplay gate is added. PROT allocation/TOC and disc relocation, project/editor/history/Build and removal/GLB composition remain unfinished.

**Replayable new-face identity record (2026-10-03):** Added a model-only topology ledger with stable hash-bound source-face identities and authored UUIDs. Each saved batch names a stable donor identity; replay resolves that donor to its Current object/group/primitive before packing. A later batch can inherit a previously authored packet. Hash chaining and exact whole-model qualification reject changed sources, altered requests, duplicate UUIDs across batches, missing donors and unowned candidate mutations. Records are detached, JSON-roundtrippable and bounded to eight batches and 128 total authored faces. This is not yet an SDK asset override or a scene/runtime identity model.

Validation: 28 focused ledger/addition/allocation/removal/restoration/vector cases pass. A fresh private Town01 model0009 proof saves/reloads two addition batches, with the second inheriting the first authored quad. The model grows from 4,704 to 4,752 bytes; the complete candidate matches independent native packet/header/pointer reconstruction and source recovery is byte-exact. Proposed SHA256 `c10a3f846166f743d788feea837c16a29695996f688883217ba1881be4d5ecc8`. Reopening the project supplies the same source; project files remain unchanged. Private proof: `local-output/sdk-20260909/model-face-ledger-20261003/parent/`. No game, helper server, browser, installation or full-disc export ran. Carrier relocation, project binding/history/Save/Open, removal/GLB composition and editor Review/Apply/Build remain required offline work; no immediate gameplay gate is added.

**New-face native packet-growth codec (2026-10-03):** Added a source-bound codec that appends authored faces to existing native group formats using typed existing-vector references and optional UV/RGB/normal fields. Each new packet inherits its donor's immutable layout/material/command bytes, has a canonical authored UUID identity, and receives an explicit Current index/byte offset in the audit. Group and object counts change; active object-table vector/primitive offsets rebase around inserted packets. Footer, padding, existing packets/vector bytes and unused pointer fields are preserved. Complete candidate qualification recomputes the requested result and rejects any other byte changes. The initial codec budget is128 faces per batch within the4MiB model budget. It is not yet an SDK topology binding or editor action, and does not relocate the surrounding carrier.

Validation:22 focused new-face/allocation/removal/restoration/vector tests pass. Native-family tests cover all24 supported flags, triangles/quads, multiple objects/groups, shared-group IDs, typed attributes, explicit lit normal references, stale/invalid/duplicate identities, budget/domain rejection and unowned-byte tampering. Independent fresh Retail Town01 model0009 assembly adds one lit textured quad to object1/group0:4704→4728 bytes, insertion3160 and Current primitive11. Complete candidate bytes match independently assembled headers/pointers/new packet; removing the insertion and restoring headers recovers every source byte. Proposed SHA256 `7f8bcfeb444e4219163847e9914bb018a03f097b85597818d92b63712b36c0df`. Project files remain unchanged. Private proof: `local-output/sdk-20260909/model-face-addition-20261003/parent/`. No helper/browser/game, installation or full-disc export ran. Carrier relocation, durable topology binding, source-identity integration and editor Review/Apply/history/Build remain unfinished; no immediate gameplay gate is added.

**Native model allocation Inspector (2026-10-03):** The model viewer now offers Inspect native allocation, connected to the read-only SDK source endpoint. Retail/Current and object selectors show native group/count/stride extents, terminator, vector ranges and uninterpreted trailing bytes. Packet groups remain in a disclosure. The dialog qualifies hashes, stream equations, count sums, group continuity, vector ownership and global span overlap; close/stale/late/error/busy guards preserve source context. It does not label trailing bytes as free space or add a topology writer. This supersedes the earlier not-yet-connected allocation-reader limitation.

Validation:17 focused Python cases and both allocation/topology Node suites pass, plus both module/editor syntax checks. Six actual retail browser/HTTP checks cover every Retail/Current object in Town01 model0009, group disclosure,540px containment, Close, source response agreement and stale/extra-field/invalid-model rejection. No page errors or command/Save/Build/Run requests occur; saved project hashes, authored state and history remain unchanged. Screenshot inspected; owned helpers closed. Private proof: `local-output/sdk-20260909/model-allocation-inspector-20261003/parent/`. No game, installation or full-disc export ran. General new-face allocation, authored identities and model/carrier relocation remain unfinished; no immediate gameplay gate is added. See [model allocation inspection](legaia-model-topology-allocation.md).

**Model allocation inspection foundation (2026-10-03):** Added a source-qualified packet/vector extent reader and a read-only SDK Retail/Current source service. Reports include group counts/strides/byte extents, explicit terminator, primitive-stream boundary and uninterpreted trailing bytes. Trailing bytes are not labeled free or authorized allocation space. The service checks Edit mode/source freshness before and after inspection, detaches metadata and enforces a4MiB report budget. This is a foundation for general face addition; it is not yet connected to the Inspector and introduces no new-face writer or allocation format.

Validation:17 focused allocation/removal/restoration/vector tests pass. Cases cover group extents, vectors, empty streams, compaction tails, malformed layout/counts, detached results, mode/freshness rejection and unchanged state/files. Independent fresh retail/current Town01 model0009 readback matches group headers, packet strides, native primitive counts, explicit terminators and source vector boundaries; all four objects have zero uninterpreted stream-tail bytes. Saved project file hashes are unchanged. Private proof: `local-output/sdk-20260909/model-allocation-20261003/parent/`. The current same-length/removal bindings cannot implement general face addition for this source; an authored-face identity and model/carrier relocation path remain required. No helper, browser, game, installation or full-disc export ran; no immediate gameplay gate is added. See [topology allocation work](legaia-model-topology-allocation.md). Full SDK coverage remains unfinished.

**Conditional capture Inspector summary (2026-10-03):** Spawn packets with qualified capture descriptors now show a read-only summary in the script workspace: payload start/length, existing-actor continuation and new-actor capture continuation. The summary explicitly marks actor match and ownership unresolved; offsets remain plain text without navigation or editing controls. Raw operands stay available in a collapsed disclosure. Qualification checks the base packet/header/context bytes, descriptor extent, payload hex format/count, both offsets and unresolved/no-successor state; malformed or mismatched rows retain ordinary raw rendering. This is presentation, not a resolution of conditional ownership or runtime identity.

Validation: four focused Node suites and both editor/module syntax checks pass, plus three private-retail HTTP workflow cases with no skips. Three actual browser checks inspect Town01 actor0020 PC34, qualify all source core fields, verify15-byte payload start0x32 and conditional continuations0x30/0x41, open/close raw operands and check540px containment. No page errors or command/Save/Build/Run requests occur in the browser proof; saved project hashes, authored state and history remain unchanged. Screenshot inspected; owned helpers closed. Private proof: `local-output/sdk-20260909/capture-summary-20261003/parent/`. No game, installation or full-disc export ran. Conditional capture execution and full SDK coverage remain unfinished; no immediate gameplay gate is added. See [capture inspection](legaia-script-capture.md).

**Conditional capture ownership guard (2026-10-03):** The parent script decoder now reserves the marker, length byte and full declared EFFECT1 capture region separately from exact decoded instruction ownership. A queued or already decoded parent path entering that region, including a message/instruction overlapping it, invalidates the ambiguous graph. Captured bytes remain opaque rather than counted as decoded instruction bytes. This fixes an incoming-edge gap in the prior spawn-packet checkpoint; it does not resolve the native existing/new-actor ownership alternatives or permit capture editing.

Validation:104 focused Python cases pass with private retail source and no skips; both branch and source-overview Node suites pass. New regressions cover both headers, both graph discovery orders, captured dialogue/instructions, every marker/length/payload destination and the exact exclusive end boundary. A private comparison against dc4ca8dd reproduces one false parent dialogue segment before the fix and zero afterward, with the ambiguous record fully opaque. Fresh source-qualified inspection preserves the real Town01 actor0020 PC34 descriptor and existing stop exactly. No UI/browser change or new gameplay gate is introduced; no helper server, game, installation or full-disc export ran. Conditional capture execution and full SDK coverage remain unfinished. Private proof: `local-output/sdk-20260909/capture-ownership-20261003/parent/`.

**Native effect-spawn packet inspection (2026-10-03):** EFFECT1 now exposes its13-byte ordinary base packet (14 extended) and required following-byte peek. Without a40 capture marker, its native shared exit advances13. With the marker, inspection requires the complete length-prefixed capture descriptor, shows both conditional continuation offsets and retains a source-flow stop. Existing matching actors skip capture; newly spawned actors can consume it. The descriptor is neither decoded as parent dialogue nor offered as a branch destination. Conditional payload ownership and runtime actor match remain unresolved; no operand writer or spawned-actor identity is added.

Validation:101 focused Python cases pass with private retail source and no skips; both branch and source-overview Node suites pass. New tests cover both headers, empty/255-byte captures, every truncation boundary, required lookahead, no invented parent dialogue/target and hash-bound native match/spawn/capture/shared-return words. Two actual browser checks inspect Town01 actor0020 PC34 and the540px workspace without page errors or command/Save/Build/Run requests. Saved project hashes, authored state and history remain unchanged. Independent fresh carrier/record reconstruction confirms base packet decoded offset11484 and15 captured bytes starting11500; possible record offsets48/65 are reported as conditional facts without graph edges. Town01 remains27 stops, Dolk2 remains30 and map01 remains4. The former unsupported EFFECT1 stop is now an explicit conditional-ownership stop; this does not establish full source decoding or runtime acceptance. Screenshot inspected; owned helpers closed. Private proof: `local-output/sdk-20260909/effect-spawn-20261003/parent/`. No game, installation or full-disc export ran; no immediate gameplay gate is added.

**Native actor-acquire source coverage (2026-10-03):** ACTOR_CTRL00/01/A/B now expose the native acquisition success/pending edges, encoded XZ bytes and signed callback parameters. Executing retail words establish ordinary widths8/10 (extended9/11), not the pinned source's5/9. The words at+3/+5 are callback parameters, not resume destinations; wide forms read the signed vertical operand at+7. Success calls801D25EC and advances; pending acquisition restores the original PC. No operand writer, actor identity association or observed position is introduced.

Validation: 97 focused Python cases pass with private retail source and no skips; both branch and source-overview Node suites pass. Tests cover all four forms under both headers, signed extremes, full truncation, overlapping destination ownership and hash-bound table/parameter/callback/return words. Five actual browser checks inspect Town01 P2 record0005 PC1600 and records0012/0013/0014 PC57 plus the540px workspace, without page errors or command/Save/Build/Run requests. Saved project hashes, authored state and history remain unchanged. Independent fresh carrier/record reconstruction confirms extended nine-byte extents at decoded offsets34438/40292/40420/40548. Town01 stops31→27, partial scripts58→54, dialogue segments619→638 and qualified flag references1383→1506; all four affected owners have no supported-path stops. Dolk2 remains30 stops and map01 remains4. This does not prove runtime acquisition, callback semantics, actor positions, execution or complete SDK coverage. Screenshot inspected; owned helpers closed. Private proof: `local-output/sdk-20260909/actor-acquire-20261003/parent/`. No game, installation or full-disc export ran; no immediate gameplay gate is added.

**Retail FMV request source coverage (2026-10-03):** MENUE2 now decodes a signed16 FMV request ID, retains two trailing operand bytes and exposes its fixed continuation. Hash-bound native words establish halfword writes to8007BA78 and8007B83C=26 followed by the advanced PC return. The handler consumes the trailing bytes without reading them; their meaning remains unknown. Inspection neither plays an FMV nor adds an operand writer. This does not establish movie availability, activation, playback stability or runtime return behavior.

Validation: 93 focused Python cases pass with private retail source and no skips; both branch and source-overview Node suites pass. The retail catalog regression also checks Town01 P2 record0025 has204 instructions/28 dialogues and no decoder stops; that updated assertion passes separately. Two actual browser checks inspect PC1804 and the540px workspace without page errors or command/Save/Build/Run requests. Saved project hashes, authored state and history remain unchanged. Independent fresh carrier/record reconstruction confirms decoded offset44355, raw `4C E2 01 00 00 00`, ID1 and continuationPC1810. Town01 stops32→31 and partial scripts59→58; Dolk2 remains30 and map01 remains4. This is supported-path source coverage, not full script/runtime/SDK acceptance. Screenshot inspected; owned helpers closed. Private proof: `local-output/sdk-20260909/fmv-trigger-20261003/parent/`. No game, installation or full-disc export ran; no immediate gameplay gate is added.

**Retail actor-state-copy coverage (2026-10-03):** MENUE3 now decodes its selector and fixed continuation. Hash-bound executing retail words establish that the resolved actor's halfwords14/16/18/26 are copied into the current dispatch context, correcting the pinned reference's reverse camera-to-actor description. A missing lookup skips the field copy but still reaches current-context post-updates. Encoded selector pairs remain unresolved runtime identities; no imported actor association, position/facing inference or operand writer is added.

Validation: 90 focused Python cases pass with private retail source and no skips; both branch and source-overview Node suites pass. Seventeen actual browser checks inspect all sixteen Dolk2 P2 record0011 copy sites and the 540px workspace with no page errors or command/Save/Build/Run requests. Saved project hashes, authored state and history remain unchanged. Independent fresh MAN carrier/record reconstruction confirms all four-byte extended instructions and their source selectors/dispatch contexts. Dolk2 remains30 decoder stops: the former E3 boundary now reaches another unresolved choice27 boundary. Town01 remains32 and map01 remains4. This is additional source coverage, not complete decoding or runtime scene parity. Narrow screenshot inspected; owned helpers closed. Private proof: `local-output/sdk-20260909/actor-state-copy-20261003/parent/`. No game, installation or full-disc export ran; no immediate gameplay gate is added.

**Embedded STATE_RESUME0 completion coverage (2026-10-03):** The bounded decoder now supports the variable completion form: retail reads argument length at operand+2, retains the prefix byte and declared argument bytes, then consumes one native terminated payload starting at operand+3+length. The instruction owns all embedded bytes; no parent dialogue/instruction anchors or editable destination words are created inside them. The continuation remains conditional on `external_state_completed`, with menu effects and ownership unobserved. The shared native payload-span helper also preserves MENU80 behavior and token rules. This corrects the pinned source's argument-length offset and supersedes the earlier fixed-only STATE_RESUME limitation. Nonadvancing A/B/out-of-range forms still stop.

Validation: 87 focused Python cases pass with private retail source and no skips; both branch and source-overview Node suites pass. New checks cover both headers, distinct prefix/length bytes, zero/255 arguments, native Cx/5E/FF rules, every truncation boundary, token limits, conflicting ownership, empty payloads and hash-bound completion/walker words. Three actual browser checks inspect Dolk2 actor0011 PC115, actor0012 PC112 and the 540px workspace with no page errors or command/Save/Build/Run requests; project bytes, authored state and history are unchanged. Independent fresh carrier/record reconstruction confirms decoded offsets9872/10152, lengths24/25, ten arguments each and terminated payload lengths10/11. Dolk2 decoder stops32→30; Town01 remains32, map01 remains4 choice-pager stops. Screenshot inspected; owned helpers closed. Private proof: `local-output/sdk-20260909/state-resume-embedded-20261003/parent/`. No game, installation or full-disc export ran. No immediate gameplay gate is added; actual menu activation/resumption and semantic payload ownership remain unfinished.

**Retail scene-register and field-callback continuations (2026-10-03):** Opcode0x4F now exposes its three unsigned byte values, native scene halfword destinations10/12/14 and fixed four-byte ordinary continuation (five with extended header). MENUEA now exposes the call target8003C7EC and its fixed two-byte ordinary continuation (three extended). The executing handler advances before calling and returns the advanced PC; this corrects the pinned source's halt description. Scene register meaning, selected runtime scene and callback effects remain unobserved. Neither instruction has an editable target word, and no operand writer or runtime call is introduced.

Validation: 83 focused Python cases pass with private retail source and no skips; both branch and source-overview Node suites pass. New cases cover both headers, unsigned values, every truncation boundary, exclusion from target authoring, unknown trailing bytes and hash-bound native table/read/write/call/return words. Three actual browser checks inspect map01 P2 record0038 PC110, record0039 PC687 and the 540px workspace with no page errors or command/Save/Build/Run requests. Project bytes, authored state and history remain unchanged. Independent fresh carrier/record readback confirms decoded offsets6873/7983 and raw instructions `4F 01 38 5A` / `4C EA`. Sampled map01 decoder stops6→4 across50 scripts; all remaining stops are choice-pager boundaries. This does not establish complete record decoding, runtime reachability or full world-map/SDK coverage. Town01/Dolk2 remain32 stops each. Screenshot inspected; owned helpers closed. Private proof: `local-output/sdk-20260909/runtime-handoffs-20261003/parent/`. No game, installation or full-disc export ran; no immediate gameplay gate is added.

**Retail MENU8 child payload ownership and fixed writes (2026-10-03):** MENU80 now follows the executing native allocator's variable-length child list instead of stopping or assuming a fixed header. Each bounded child span uses SCUS8003CA38 token rules (only C0..CF consume a second byte; a byte≤1E ends the payload). The parent instruction owns the whole list; children remain opaque and are excluded from parent dialogue/instruction anchors and editable destinations. Acquisition success reaches the byte after all children; pending acquisition retains the original PC, including extended dispatch. Native MENU82 character-field mirror, MENU84 byte global write and MENU89 signed scalar global write now expose their fixed continuations. Runtime allocation, actor-table identity and global effects remain unobserved; no new operand writer is introduced.

Validation: 79 focused Python cases pass with private retail source and no skips; both branch and source-overview Node suites pass. New checks cover zero/255 child counts, native token differences, every truncation boundary, bounded tokens, conflicting branch ownership, both headers, signed extremes and hash-bound allocator/table/walker/write words. Six actual browser checks inspect five retail source sites and the 540px workspace with no page errors or command/Save/Build/Run requests; project files, authored state and history are unchanged. Independent fresh whole-carrier/record readback confirms offsets6826/6868/7479/8337/8669 and the extended allocator at map01 P2 record0039 PC183: 369 instruction bytes containing14 opaque child payloads. Map01 stops8→6, now four choice-pager boundaries plus newly reached opcode4F/MENUEA; Town01/Dolk2 remain32 each. Screenshot inspected; owned helpers closed. Private proof: `local-output/sdk-20260909/menu8-coverage-20261003/parent/`. No game, installation or full-disc export ran. No immediate gameplay gate is added; live allocation/child execution and complete script coverage remain unfinished.

**Retail value-comparison branches and MENU49 continuation (2026-10-03):** Opcode0x4E now decodes all source/comparison nibbles, retaining short signed16 or split signed32 thresholds, encoded selectors and unsigned relative destination words. Sources0..B with comparison0/1 expose value<threshold / threshold<value branches; default sourcesC..F and comparison2..F continue without offering target edits. Runtime values, scaling, RNG results and selector identity remain unobserved. Source-qualified VALUE_COMPARE_BRANCH target words join the existing Review/Apply path with selectors, thresholds, mode and high bank word immutable. Retail MENU49 now decodes a fixed field4A/global-delta write or ramp with encoded continuation: all native exits return the already advanced PC. This corrects the pinned source's unsigned-short threshold and sub49 yield interpretations without changing its pin. Unknown paths and all existing authoring restrictions remain enforced.

Validation: 72 focused Python cases plus one new retail P2 history/Save/Open/full-package regression pass with private source and no skips; both branch and source-overview Node suites pass. Mode coverage checks all 256 nibble combinations under both headers, truncation, signed extremes, inactive destination exclusion, mutable-word ownership and executing PROT/SCUS hashes. Six actual browser checks pass through 540px Review/Apply, Undo/Redo, Save/Open and normal Build with no page errors or Run requests. Map01 P2 record0009 PC52 retargets111→14; independent complete 11,274-byte MAN readback changes only offsets3006/3007 from `36 00` to `D5 FF`, preserving all comparison operands, field-write instructions and pointers. The carrier is descriptor/compressed MAN. Package SHA256 `bde95688550c4a382485ac426f08a90a0a797c2e553b9d05e9b3f7dd9039e611`. Map01 decoder stops26→8 across50 scripts; Town01/Dolk2 remain32 each. Remaining map01 stops are choice-pager boundaries and unsupported MENU80/82/84. Narrow screenshot inspected; owned helpers closed. Private proof: `local-output/sdk-20260909/inventory-branches-20261003/parent/`. No game, installation or full-disc export ran; branch story/runtime verification remains deferred.

**Fixed STATE_RESUME completion coverage (2026-10-03):** The bounded decoder now supports the retail fixed completion forms of opcode0x49: sub1/3/7 consume2 payload bytes, sub2/4 consume6, sub5 consumes13, and sub6/8/9/C/D consume4, plus the ordinary or extended header. Encoded payload stays opaque; it is neither interpreted as script nor editable. Continuations, including the previously supported forms, carry `external_state_completed` rather than an unconditional label, with runtime state explicitly unobserved. Embedded-message sub0 and nonadvancing A/B/out-of-range forms remain unsupported. This adds source coverage without running the menu state machine or introducing new operand writers.

Validation: 66 focused Python cases pass with private retail source and no skips; both branch and source-overview Node suites pass. New cases cover every fixed form/header, all truncation boundaries, opaque bytes that resemble instructions/messages, unsupported forms, exclusion from branch-target authoring and hash-bound executing PROT dispatch/completion exits. Four actual browser checks inspect Dolk2 actor0049 PCs959/1232/1611 and the 540px workspace; page errors and write/Save/Build/Run requests are zero, and project bytes/authored state/history remain unchanged. Independent fresh MAN readback confirms raw opcode4909 and five-byte boundaries at decoded offsets23055/23328/23707. Dolk2 stops35→32; Town01 remains32 and map01 remains26. Screenshot inspected; owned helpers closed. Private proof: `local-output/sdk-20260909/state-resume-20261003/parent/`. No game, installation or full-disc export ran; no immediate gameplay gate is added. Menu activation/resumption and full script coverage remain unfinished.

**Retail MENU8C/8D branch coverage (2026-10-03):** The bounded script decoder now recognizes FIELD_68_BRANCH (0x4C/8C) and ACTOR_SEARCH_BRANCH (0x4C/8D), including extended dispatch. Hash-bound executing retail PROT handlers establish relative signed-word targets at operand+1 / operand+3, with 16-bit wrapping. Empty or unmatched actor searches advance to the encoded fallthrough. This corrects the pinned reference's absolute-target/no-match-halt descriptions without changing that pin. The existing reviewed target-only writer supports both families; dispatch, field/search operands, source boundaries and unsupported-path restrictions remain intact. Runtime field values, actor search-table identity and branch execution are unresolved.

Validation: 61 focused Python regression cases plus one new retail P2 history/Save/Open/full-package test pass with private source and no skips; both branch and source-overview Node suites pass. Six actual browser checks pass through 540px Review/Apply, Undo/Redo, Save/Open and normal Build with no page errors or Run requests. Town01 P2 record0015 PC23 changes its destination PC50→12: independent complete 45,338-byte MAN readback changes only offsets40645/40646 from `18 00` to `F2 FF`. Package SHA256 `54707d3cd606648d1051ae10234c0435bdace401f603a26d76a0bb536c9ac06c`. Town01 decoder stops fall43→32 and partial scripts60→59; qualified flag references increase1339→1383 while 91 scripts/619 dialogues/710 assets remain. Dolk2's three newly decoded searches expose later STATE_RESUME09 stops; map01 reveals further unsupported paths (stops24→26). These are coverage changes, not runtime acceptance or complete decoding. Private proof: `local-output/sdk-20260909/script-coverage-20261003/parent/`. Narrow screenshot inspected; owned helpers closed. No game, installation or full-disc export ran. Gameplay verification stays deferred.

**Asset-reference instruction navigation (2026-10-03):** Dependency and Referenced by rows now offer Inspect reference instruction for decoded script→dialogue, flag, transition and named-scene relationships. The action uses the edge's structural P1/P2 owner and PC, refreshes its source catalog after ordinary scene navigation, and verifies owner/partition/index/extent/source key and any recorded hash before opening disassembly at the exact boundary. Unimported destinations do not prevent inspection of their imported source script. Busy, stale, closed and late-response guards remain in force. Runtime actor/model identity, execution and reachability remain unasserted.

Validation: 25 focused Python cases pass with private Retail source and no skips; four Node suites and both editor module syntax checks pass. The new suite covers P1/P2 source qualification, drift, unavailable/mismatched owners, source-only targets and exactly-once/stale/busy/close/late-response navigation. An outdated flag fixture now uses qualified ordinary SYSFLAG selectors and explicitly checks that unsupported extended dispatch stops before later references. Eight actual browser checks cover outgoing/incoming P1 flag sites, atomic dialogue PC15, P2 SCENE_CHANGE PC22 with an unimported destination, 540px Project controls, Town01→Dolk2 PC14 navigation, stale-key rejection and unchanged project bytes/authored state/history. Cross-scene navigation marks only the ordinary Active scene setting unsaved; returning restores the prior dirty state. Independent native MAN pointer/opcode checks confirm all four inspected source sites at decoded offsets4771/4774/28565/7466. Private proof: `local-output/sdk-20260909/asset-reference-instructions-20261003/parent/`. Screenshot inspected; owned helpers closed. No authoring, Save, Build, Run, installation or full-disc export occurred in the browser workflow. No immediate gameplay verification is required. See [reference-site navigation](legaia-asset-references.md#inspect-the-reference-instruction).

**Whole-record script flow overview (2026-10-03):** Actor and partition-2 disassembly now summarize verified entry reachability, cyclic components, encoded exits, undecoded targets and decoder stops, with paged source navigation. The branch workspace compares separate Retail, Current and reviewed Proposed overviews. Current/Proposed reports retain independently redecoded original anchors that a branch leaves unvisited; reached-path arrays keep their existing meaning. Missing or undecoded entries leave reachability unknown. Links open collapsed disassembly before focusing the exact row, and discarding a branch withdraws Proposed flow and its review status. Encoded reachability and closed cycles do not establish story activation, execution or nontermination. General control-flow authoring/live execution remain unfinished.

Validation: 47 focused Python cases pass with private Retail source and no skips, including branch history, Build/readback and HTTP regressions; both source-overview and branch Node suites pass. The overview suite covers an 8192-node cycle, dialogue boundaries, preserved unvisited anchors, unknown entries, malformed domains, pagination and disposal. Eight actual browser checks pass without page errors: Retail/Current cycle navigation, reviewed Proposed unvisited anchors, discard, 540px containment, unchanged files/overrides/history, unknown exits and paging. Independent per-node transitive reachability/mutual membership matches all three recorded graphs: Town01 actor0002 has 5 boundaries/one cycle; actor0011 Proposed retains 49 boundaries/two cycles and unvisited PCs 55, 57, 63. Private proof: `local-output/sdk-20260909/script-flow-overview-20261003/parent/`. Narrow screenshot inspected; owned helpers closed. Browser inspection submitted no command, Build, Save or Run; no game, installation or full-disc export ran. This read-only feature requires no immediate gameplay verification. See [source-flow overview](legaia-script-flow-overview.md).

**Selective model face restoration (2026-10-03):** The removal dialog now offers restoration using listed removed Retail indices. Restored packets recover Retail face fields with current vector tables; retained groups keep their current settings and fully absent groups recover Retail settings. Preview and reviewed Apply preserve unrelated typed edits. Partial restoration retains the remaining removal binding; restoring all removals transitions to the ordinary typed format or clears the override when byte-exact Retail. Each Apply is one undoable command. This restores existing Retail packets only; general new-face allocation/addition remains unfinished.

Validation:13 focused Python cases and the expanded topology Node suite pass. Tests cover dropped groups, partial/cumulative recovery, retained vector/material fields, removed-owner rejection, all-restored typed/clear transitions and history. Six actual private-retail browser checks verify native Retail-index domain, independently reconstructed188→190 triangle review, wrong-hash rejection without state mutation,540px Apply to `tmd-content-v3`, exact Undo/Redo format/bytes and Save/reload/Build. Complete candidate/carrier readback preserves Current vectors and retained packet fields and every decoded neighbor within154547 source bytes. Package SHA256 `d7bed311677f882ae97792d3544155ab425ddb695a11fc740bd090d211d76d68`. Private proof: `local-output/sdk-20260909/model-face-restoration-20261003/parent/`. Narrow screenshot inspected; owned helpers closed. No game, installation or full-disc export ran; native restored-face appearance remains deferred.

**GLB interchange after face removal (2026-10-03):** The model GLB workflow now exports the qualified Current topology with a v2 binding that names every removed Retail face. Profiles are regenerated from Current bytes; Review qualifies typed edits against the original Retail removal binding. V2 reviews retain the complete removal audit and reject missing, conflicting or pending removal identities. Reviewed Apply preserves the normal model override, cumulative removals and prior typed edits. Count allocation/addition and arbitrary replacement remain unfinished.

Validation:27 focused Python cases pass with private Retail source and no skips; the expanded GLB Node suite verifies binding identities, complete removal audits and existing review/lifecycle guards. Six actual private-retail browser checks cover exact no-op Current export, selected-file vertex review, reduced proposed-model inspection/Return,540px Apply, exact Undo/Redo and Save/reload/Build. Independent candidate/carrier readback proves only byte3196 changes for object1 vertex1 X126→128, retaining188 triangles, material/normal/UV/color data and every decoded neighbor within154547 source bytes. Package SHA256 `036b2732b290e954c578de666d3f9b9b7fd8e30e8310f45efd61f4deaa186d8a`. Private proof: `local-output/sdk-20260909/model-removal-glb-20261003/parent/`. Narrow screenshot inspected; owned helpers closed. No game, installation or full-disc export ran; native appearance/shared-instance behavior remains deferred.

**Material editing after face removal (2026-10-03):** The native material Inspector now uses exact retained Retail group and face owners for comparisons and Reset. The versioned catalog handles compacted packets and fully dropped groups. CLUT/page/depth and shared group ABE drafts edit Current source words; complete candidate review audits actual Retail ownership and preserves the removal binding and unrelated normal/vertex edits. Removed faces/groups cannot become Current edit targets. GLB interchange after removal is now supported as described above. General topology allocation/addition remains unfinished.

Validation:18 focused Python cases pass with private Retail source and no skips, plus material workflow/mapping and donor Node suites. Seven actual private-retail browser checks cover native ownership, mapped Retail reset, independently patched CLUT/page/ABE review, all-instance scene proposal,540px Apply, exact Undo/Redo and Save/reload/Build. Full candidate/carrier readback proves only bytes2895/2898/2902 change, retaining188 triangles, vector/UV/color/normal data and every decoded neighbor within154547 source bytes. Package SHA256 `9458a47b0aa62d030a5c62eb017157c2adc8ffe889895b35c0b2b530dbf40150`. Private proof: `local-output/sdk-20260909/model-removal-materials-20261003/parent/`. Narrow screenshot inspected; owned helpers closed. No game, installation or full-disc export ran; native palette/VRAM/blend appearance remains deferred.

**Reference retargeting after face removal (2026-10-03):** Object-wide vertex and normal retargeting now remains available with a removal binding. Preview qualifies every matching Current operand against the reference lookup; the final candidate is independently audited against actual Retail ownership. Reviewed Apply preserves removed Retail identities, vector tables, native Current packet counts/layout and other edits. Removed faces are never retargeted. Material editing is now supported as described above. GLB interchange after removal is now supported as described above. General topology allocation/addition remains unfinished.

Validation:13 focused Python cases and both exact-user retarget Node suites pass. Seven private-retail browser checks cover normal4→3 across three retained words, vertex5→6 across one retained word, Current/Proposed toggles,540px reviewed Apply, exact Undo/Redo for both operations and cumulative Save/reload/Build. Whole-candidate and compressed-carrier readback matches independent raw-word patches at bytes2908/2916/2964/2988, retaining188 triangles and every decoded neighbor within154547 source bytes. Package SHA256 `5dfcc1ffed7111883201e380d28eff5fdcbc328fbfbdf22962de9101aed99ac9`. Private proof: `local-output/sdk-20260909/model-removal-retarget-20261003/parent/`. Narrow screenshots inspected; owned helpers closed. No game, installation or full-disc export ran. Native appearance and shared-instance behavior remain deferred.

**Retained-face editing after removal (2026-10-03):** The face Inspector now supports compacted Current packet identities with exact retained Retail owners. Reset to Retail copies the mapped face, and existing vertex/UV/RGB/normal-reference drafts use Current packet offsets. Preview audits the complete candidate against actual Retail ownership; reviewed Apply retains cumulative removal identities. Vertex/normal user navigation is restored for retained faces. Object-wide retargeting is now supported as described above. The material editor now supports this binding as described above. GLB interchange now preserves removal bindings; general allocation/addition is unfinished.

Validation:14 focused Python cases pass with private Retail source and no skips; the expanded primitive Node suite passes v1/v2/v3 mappings, draft/audit/hash and removed-owner rejection. Six private-retail browser checks verify native Current0→Retail1 inspection, mapped Reset, independent UV proposal bytes,540px reviewed Apply, exact Undo/Redo and Save/reload/Build. Full compressed-carrier readback proves only byte2896 changes (corner0 U0→17), retaining188 triangles, the removed quad, vectors/materials/normals/opaque bytes and every decoded neighbor within154547 source bytes. Package SHA256 `f6f3bee2fbada9ba1d5f76b19e645ce18a4ec51baaf586fe56d6f1b74c77b911`. Private proof: `local-output/sdk-20260909/model-retained-faces-20261003/parent/`. An additional actual browser API check verifies all-instance scene proposal with188 triangles, the reviewed hash and unchanged project bytes; the scene handoff retains removal metadata. Narrow screenshot inspected; owned helpers closed. No game, installation or full-disc export ran; native UV appearance remains deferred.

**Reference inspection after face removal (2026-10-03):** Vertex/normal user lookup now qualifies the complete removal binding and reports exact Retail-to-Current face identities. Compacted Current indices display their retained Retail owners; removed Retail faces explicitly have no Current face. The lookup is restored in the vector Inspector. Retained-face editing/navigation now consume this mapping as described above. Object-wide reference retargeting is now supported as described above.

Validation:12 focused Python cases and both reference-decoder Node suites pass. Five private-retail browser checks cover removed-face labeling, retained vertex9 users with shifted identities, matching normal endpoint mapping,540px access and unchanged project files/overrides. No browser errors occurred. Screenshot inspected; owned helpers closed. Private proof: `local-output/sdk-20260909/model-reference-faces-20261003/parent/`. No authoring, Build, game, installation or disc export ran; no immediate gameplay verification is required for this read-only inspector feature.

**Vector and file editing after face removal (2026-10-03):** Existing removal bindings now survive vertex/normal edits, object translation/rotation/scale, normal-length adjustment and same-layout TMD/OBJ/JSON imports. Candidates are audited against actual Retail ownership and retain the exact removed Retail face identities. Reference lookup now displays qualified Current-to-Retail identities as described above. Retained-face editing/navigation now consume the mapping. Reference retargeting is now supported; material editing is now supported; GLB interchange now preserves removal bindings. General topology allocation remains unfinished. See [supported editing after removal](legaia-model-face-removal.md#editing-after-removal).

Validation:11 focused Python cases and two Node suites pass. Six private-retail browser checks verify enabled vector controls, reduced-topology object preview, reviewed vector Apply, exact Undo/Redo, Save/reload and normal Build. Independent readback confirms only model byte3188 changes for object1 vertex0 X126→143, retaining188 triangles and all materials, normals, opaque bytes and decoded neighbors within154547 source carrier bytes. Package SHA256 `f21d1fd224cbf19bba111a1b7398bf00da59e0b7af1767d3afcc4f45b7ed084b`. Private proof: `local-output/sdk-20260909/model-topology-vectors-20261003/parent/`. The540px screenshot was inspected and owned helpers closed. No game, installation or full-disc export ran; native appearance remains deferred.

**Count-changing model face removal (2026-10-03):** The model viewer now reviews and removes whole existing triangles/quads, compacts retained packet groups inside the source allocation and updates native primitive counts. A versioned binding preserves cumulative Retail identities independently of Current dense indices. Object and vector-table identities remain fixed; supported poses refresh face ranges without changing vertex channels. Apply requires the reviewed candidate hash. Undo/Redo, Save/Open, Clear, further removal and normal Build are connected. Vector and same-layout file edits are now supported as described above; material editing is now supported; GLB interchange now preserves removal bindings; retained-face editing is now supported. Arbitrary replacement/allocation remains unfinished. See [face-removal workflow and limitations](legaia-model-face-removal.md).

Validation:12 focused Python cases pass with private retail source and no skips; face-removal and rigid-normal Node suites pass. Eight actual private-retail browser workflows verify review/domain/hash guards, Current/Proposed,540px Apply, exact Undo/Redo, Save/reload and Build. Additional checks cover cumulative Current-to-Retail mapping, Clear/Undo, fresh capability and closed preview resources with unchanged project files/history. Independent full-model/carrier readback proves Town01 model0009 object1 quad removal,190→188 triangles, unchanged vector tables/object identity and every decoded neighbor within154547 source bytes. Package SHA256 `c6bcc7a8ccd981960b07cbb8482c0699e8179ce161a66594a8a841120d5a138c`. Private proof: `local-output/sdk-20260909/model-face-removal-20261003/parent/`. Narrow screenshot inspected; owned helpers closed. No game, installation or full-disc export ran; native appearance and shared-instance effects are deferred.

**Component reference navigation (2026-10-03):** The entity Inspector now opens exact Asset Database records from supported model, initial-animation and donor-actor reference properties. Imported/Authored/Effective layers retain separate values and accessible reference names. Navigation resolves the active source scene independently of Project browser filters; the opened metadata Inspector keeps its normal tool actions. Missing, ambiguous, stale and busy navigation fails explicitly. See [component reference workflow](legaia-component-references.md).

Validation: three focused Node suites pass. Five actual private-retail browser workflows verify exact model details and viewer activation, native Enter,540px access and unchanged selection/project/saved bytes. An additional two-scene proof filters the browser to Dolk2 while Town01 remains active: the absent Town01 model reference still opens its enabled Inspector, and the Imported Clip opens the native animation-binding Inspector. Narrow screenshot inspected. Private proof: `local-output/sdk-20260909/component-references-20261003/parent/`. Owned helpers closed. No gameplay verification is needed for this feature; no game, Build, installation or disc export ran. Full runtime correlation and scene parity remain unfinished.

**Object-wide vertex-reference retargeting (2026-10-03):** The vector Inspector now finds Current/Retail faces using an existing vertex and navigates to their exact current face. Retargeting changes every matching stored corner within its object to another existing vertex. Preview verifies complete Current-user ownership and offers Current/Proposed geometry; Apply requires the reviewed candidate hash. Coordinates, stored normals, counts, packet layout, material edits, padding and other objects remain fixed. Faces may collapse. See [vertex users and retargeting](legaia-model-vertex-retarget.md).

Validation:19 focused Python cases pass with private retail source and no skips, plus five Node decoder/retarget/primitive suites. Ten actual private-retail browser checks pass through lookup/navigation, target/review guards, independent whole-model preview, Current/Proposed,540px controls, rejected proposal, Apply, Undo/Redo, Save/reload and normal Build. Complete compressed-carrier readback matches Town01 model0009 object1 vertex0→9, with only byte2912 additionally changed and decoded neighbors preserved within154547 source bytes. Package SHA256 `37c6b64a03abcf663ac64c00462153ca87a8cb5eaf2f870b274427a2942dedc7`. Private proof: `local-output/sdk-20260909/vertex-retarget-20261003/parent/`. Screenshot inspected; owned helpers closed. No game, installation or full-disc export ran. Gameplay acceptance stays deferred; general count-changing topology remains unfinished.

**Asset database keyboard navigation (2026-10-03):** Asset cards now have one Tab entry, Up/Down result browsing, Left/Right Open/Details actions and Home/End boundaries. Project PageUp/PageDown retain the action while moving across result pages. Stable asset/action focus survives redraw and temporary busy controls. Rendered scope tracking prevents focus transfer across changed projects/scenes/scopes; search and external controls keep focus. Parent busy handling now refreshes the Tab entry after project-resource discovery enables its buttons. See [asset keyboard browsing](legaia-asset-keyboard.md).

Validation: focused asset-navigation and existing hierarchy Node suites pass, along with editor syntax and diff checks. Eight actual private-retail browser checks pass for native Details activation, stable redraw/busy focus, search/empty behavior, paging1614 retained results across13 pages, scope reset and540px access. Project files, history and selection remain exact; no authoring, Save, Build or Run request occurs. Desktop/narrow screenshots were inspected and owned helpers are closed. Private proof: `local-output/sdk-20260909/asset-keyboard-20261003/parent/`. No immediate gameplay verification is required; source coverage and runtime-use limits remain unchanged.

**Scene animation normal-channel inspection (2026-10-03):** Supported scene tracks now carry optional raw normal evidence and complete rigid channels. The timeline offers **Source normal directions** for those tracks during scrub and Play. Unsupported actors and environment retain surface shading. Canonical posed scenes retain raw vectors in a separate `normal_source` field, never as a qualified render stream. Preparation verifies that every channel reproduces its vertex sample; Restore clears the mode and restores the exact scene. See [scene normal channels](legaia-scene-animation.md#source-normal-channel-diagnostic-2026-10-03).

Validation:19 focused Python cases and three Node suites pass with no skips. Six actual private-retail browser checks pass for Town01's42 animated actors in22 qualified tracks: mode/default pixel restoration, tick7 direction/vertex agreement, Play without geometry/texture allocation,540px reachability, exact Stop/Restore and unchanged project files/history. These22 retail tracks contain no lit source-normal triangles and correctly appear neutral; lit rotation behavior is covered by the focused synthetic vectors. Desktop/narrow screenshots were inspected. Optional normal validation is bounded to three million frame corners within the existing64MiB report; exceeding it omits the diagnostic, retaining vertex playback. Private proof: `local-output/sdk-20260909/scene-normal-pose-20261003/parent/`. Owned helpers are closed. No authoring, Build, game, installation or disc export ran; native GTE lighting and gameplay appearance remain deferred.

**Animated source-normal directions (2026-10-03):** The individual model viewer now rotates qualified stored normal directions through the supported frame's independent rigid object channels. Scrub and Play update vertex and normal buffers in place; surface shading remains the default. Every object, vertex span and triangle owner must match the frame, and unknown poses retain surface shading. This is analytic SDK Rz × Ry × Rx direction visualization, not retail GTE lighting. Static posed and assembled-scene diagnostics without qualified channels remain unavailable. See [source normal directions](legaia-model-source-normals.md#supported-rigid-frame-directions-2026-10-03).

Validation: three focused Node suites pass, including rigid rotation/order/translation/ownership guards, stale metadata withdrawal and existing scene animation behavior. Eight actual private-retail browser checks pass for mode restoration without uploads, in-place scrub, Play, object slicing,540px controls, unknown-pose fallback, static compatibility and byte-exact project files. Independent Python pose math matches1488 private test directions across10 objects at frames0/1/14 with zero error. The real Vahn idle model has zero lit source-normal triangles and remains neutral; colorful screenshots use explicit private direction-only test data. Owned browser/server handles are terminal. Private proof: `local-output/sdk-20260909/rigid-normal-pose-20261003/parent/`. No authoring, Build, game, installation or disc export ran. Native appearance remains deferred.

**Object-wide normal-reference retargeting (2026-10-03):** The vector Inspector now retargets every qualified Current use of the selected normal within its object to another existing normal. Preview binds the complete Current-user ownership report, shows exact reference-word changes and offers Current/Proposed source-direction comparison. Apply requires the reviewed candidate hash and records one existing model replacement command. Coordinates, geometry, other references, padding and inherited material edits remain intact. See [normal retargeting](legaia-model-normal-retarget.md).

Validation:10 focused Python cases and both Node retarget/primitive suites pass with no skips. Nine actual private-retail browser checks pass through target/review guards, independent whole-model preview, Current/Proposed,540px controls, rejected mismatched proposal, one Apply, exact Undo/Redo, Save/reload and normal Build. A final read-only preview verifies the finished labels and narrow layout. Complete model/carrier readback matches Town01 model0009 object1 normal3→4: only bytes2940/2988 additionally change, decoded neighbors remain exact within154547 source bytes. Package SHA256 `31c7e714c2f90c3ba82496970558cb3371df67fbe87609cae9cb6f7e4b401b3f`. Private proof: `local-output/sdk-20260909/normal-retarget-20261003/parent/`. Owned helpers are closed. No game, installation or full-disc export ran; native lighting remains deferred.

**Precompile multi-configuration acceptance (2026-10-03):** The existing synthetic static-overlay fixture now builds and executes both Release and Debug for every inventory/body variant when using a multi-configuration generator. Shared generated sources must reach both configurations after growth, shrinkage, body-only changes, split/monolithic switching, empty output and regrowth. Single-configuration behavior remains unchanged. See [release parity evidence](legaia-release-parity.md#ninja-multi-config-acceptance-2026-10-03).

Validation: Ninja Multi-Config1.13.2, CMake4.2.3 and MSYS2 UCRT GCC16.1.0 pass both focused tests in12.745s with no skips: nine recipes times two configurations,18 executable sum checks, final no-change builds and sparse numeric filename ownership. A restricted invocation failed before configuration while starting the Winget Ninja executable; the approved retry passes. GNU Make is not installed and its coverage remains open. Private logs/tool/source identities: `local-output/sdk-20260909/precompile-ninja-multi-20261003/parent/`. No runtime implementation, game executable, installed mod, retail payload or gameplay acceptance changed; no game ran.

**Collapsible scene tools and viewport space (2026-10-03):** Existing secondary scene controls now live in a closed-by-default Scene tools drawer. Nodes move intact, retaining their handlers and drafts. The open drawer scrolls within available height, reserving180px for the scene where space permits. Runtime notices, field-map notes, proposed-scene restore controls, active actor-group controls and script-target controls stay outside. The viewport panel now has a zero minimum height, fixing expansion below the workspace. See [scene tools](legaia-scene-tool-drawer.md).

Validation: six actual private-retail browser checks pass with no page errors. The desktop scene area is640px collapsed and279px expanded; at540px it is389px collapsed and at least175px in the open-drawer check. Existing snap settings survive collapse/reopen. Project files, history and selection remain exact; no authoring, Build or game request ran. The existing narrow Hierarchy & assets tab exposes the keyboard hierarchy, correcting the prior Scene-tab-only limitation note. Desktop and narrow screenshots were visually inspected; the hierarchy Node suite still passes. Private proof: `local-output/sdk-20260909/scene-tool-drawer-20261003/parent/`. Owned helpers are closed.

**Hierarchy keyboard browsing and stable focus (2026-10-03):** The rendered SDK hierarchy now has one Tab entry. Arrow Up/Down and Home/End move focus across visible actor, draft, environment and resource rows without changing selection. Native Enter/Space retain existing row actions. Same-scene rebuilds restore the focused stable ID; filtering falls back safely and does not steal focus from search. Empty lists remain reachable; scene/context changes do not transplant old focus. See [hierarchy keyboard workflow](legaia-hierarchy-keyboard.md).

Validation: focused Node checks pass for roving focus, boundary keys, filtered/empty lists, context changes, modifiers and native selection keys. Seven actual private-retail browser checks pass with no page errors, including one Tab entry, mixed row browsing without requests, Enter selection through the existing API, rerender focus, search/empty behavior and exact project files/history. The original check covered desktop focus after resize and observed the hidden sidebar in the540px Scene tab. The later scene-tools proof verifies keyboard access through the existing Hierarchy & assets tab. No authoring, Build or game request ran. Private proof: `local-output/sdk-20260909/hierarchy-keyboard-20261003/parent/`. Owned helpers are closed.

**Face/normal Inspector navigation (2026-10-03):** Lit face controls now inspect their Current stored normal directly: one flat reference or the selected Gouraud corner. The vector Inspector opens the exact object and normal index, and its existing normal-user lookup returns to the source face. Any face draft blocks navigation until Apply or explicit Discard. Vector drafts withdraw reference results; explicit Discard now refreshes lookup availability. Post-Apply close handling distinguishes intentional navigation from background model refresh. See [normal navigation](legaia-face-normal-references.md#current-normal-navigation).

Validation: the expanded Node primitive suite passes for flat/Gouraud target ownership, detached bindings, UV-draft rejection, busy and stale-source guards. Seven actual private-retail browser checks pass with no page errors: initially clean state, UV/reference draft guards,540px controls, exact object1 normal3 navigation, vector draft withdrawal/discard, return to primitive1 and unchanged project files/history. No authoring, Build or game requests ran. Private proof: `local-output/sdk-20260909/face-normal-navigation-20261003/parent/`. Owned helpers are closed. Native lighting and runtime appearance remain deferred.

**Native face normal-reference editing (2026-10-03):** The existing face editor now selects existing object normals directly, with one shared operand for flat faces and per-corner operands for Gouraud faces. Unlit packets expose no normal editor. V2 source metadata and exact reference-word audit guards preserve counts, geometry, normal coordinates, materials, padding and prior edits. Source normal directions are available in Current/Proposed comparisons; the object extraction now slices normal metadata alongside its triangles. Existing reviewed Apply, Undo/Redo, persistence and normal Build carry the edits. See [face normal references](legaia-face-normal-references.md).

Validation:21 focused Python cases pass with private source and no skips; the Node primitive workflow and new V2 source/audit guards pass. Eight actual browser checks pass, including domain/shared ownership, independently matched preview, Current/Proposed source directions,540px layout, Apply, exact Undo/Redo, Save/reload and Build. Complete model/carrier readback matches: Town01 model0009 object1 primitive1 changes normal2 to3 at byte2940, adding only one changed byte to the inherited authored fixture; decoded neighbors and154547-byte compressed capacity remain exact. Package SHA256 `9a784f6398809281b8fca293aef9c800cd56381273d217b036e29943a7e92075`. Private proof: `local-output/sdk-20260909/model-primitive-normals-20261003/parent/`. Owned helpers are closed. No game, install or full-disc export ran; native appearance remains deferred.

**Stored normal reference navigation (2026-10-03):** The vector Inspector now finds qualified faces using a selected stored normal, with separate Current/Retail references, exact source-word offsets and flat/Gouraud corner ownership. Inspect current face opens the existing face editor at the source object and primitive. Requests bind the inspected model hash and project source key; selection changes and closing withdraw results. This is read-only source navigation. See [normal reference navigation](legaia-model-normal-users.md).

Validation: nine focused Python cases and the Node source/DTO guards pass. Seven actual browser checks pass with no page errors: exact private-retail report, distinct Current/Retail layers,540px layout, face navigation, selection invalidation, pending-response cleanup and unchanged files/history. Town01 model0009 object1 normal1 has one Retail operand at byte2940 and zero Current operands after its earlier reference edit. Independent raw packet reads match both layers. No command, Build or game requests ran; owned helpers are closed. Private proof: `local-output/sdk-20260909/model-normal-users-20261003/parent/`. Runtime visibility and native lighting remain deferred.

**Object-level stored-normal rescaling (2026-10-03):** The vector Inspector now rescales an existing object's nonzero normals to an explicit encoded length1..32767, with exact integer midpoint rounding and zero-vector retention. The client previews the same arithmetic with BigInt. Qualified Current/Proposed object previews, explicit Apply, history, persistence and normal Build reuse existing replacement infrastructure. Geometry, normal references, padding, material edits and other objects stay separate. An object-preview bug retaining full-model triangle normals after triangle slicing is also fixed. See [normal rescaling](legaia-model-normal-length.md).

Validation: eight focused Python checks and normal-length/source-direction Node suites pass. Eight actual browser checks pass with no page errors or game requests, including source domain guards, exact proposal, Current/Proposed,540px layout, one Apply, history, Save/reload and Build. Independent80-digit decimal construction matches the whole candidate:11 normals,14 coordinate words and19 bytes change; full compressed carrier readback preserves decoded neighbors and prior edits within154547 source bytes. Package SHA256 `509fe8cac4fe103973a10c2f19ddee0fa0275130b9aac710d6feda2729dd8f42`. Private proof: `local-output/sdk-20260909/model-normal-length-20261003/parent/`. Owned helpers are closed; no game, install or disc export ran. Native lighting acceptance remains deferred.

**Restore selected source walls to retail (2026-10-03):** Wall rectangles now offer Set wall bits or Restore retail walls. Restoration uses each selected quadrant's own source value, preserving mixed blocked/unblocked cells, outside overrides and floor tiers. Existing Review, Proposed/Return, one Apply, Undo/Redo, Save/Open and normal Build handle the operation; changing the choice withdraws prior review, and no-op restoration disables Apply. See [wall rectangle workflow](legaia-collision-rectangles.md#retail-restoration-evidence-2026-10-03).

Validation: five focused Python cases pass with private retail source and no skips; wall rectangle/viewport Node suites pass. Eight actual browser checks pass with no page errors or game requests, including mixed-bit review, retained comparison,540px controls, Apply, exact history, Save/reload, no-op and Build. Independent complete73,728-byte MAP readback returns the selected area to retail and changes only byte32767's retained outside wall bit; every floor nibble stays exact. Package SHA256 `143ca9497ec65065a56765605cedc07ff4e7f782335019c1880399ebeaf8b036`. Private proof: `local-output/sdk-20260909/wall-retail-restore-20261003/parent/`. Owned helpers are closed; no game, install or disc export ran. Native movement acceptance remains deferred.

**Shared NPC capacity gate for growth candidates (2026-10-03):** Compressed and raw-streaming appended-NPC preparation now uses the same retail executable qualification and initial-placement lower-bound assessor as normal Build. Candidate counts are checked before archive repacking; existing-only edits retain their prior compatibility. Per-scene growth audits and Review NPC output retain qualified pool evidence. A stale review limitation claiming normal Build rejects every draft is corrected.

Validation:17 focused Python cases passed with private source and no skips, including distinct Town01/Dolk2 growth rejection before either repacker, unchanged project files/history, valid rebuilt archive readback with retained donor clones/facing edits, normal Build regression and review/HTTP/multi-scene guards. After the review metadata addition, all six review cases pass, including detached pool evidence. Both Node review suites and five existing-only streaming/export snapshot regressions pass. No game, full-disc export or install ran. Complete native demand and gameplay acceptance remain deferred. See [shared growth gate](legaia-npc-actor-pool.md#shared-growth-candidate-gate-2026-10-03).

**Shared actor-pool consumers (2026-10-03):** Build audit metadata now qualifies nine complete retail functions and records six setup allocation sites, including scenery, two unconditional later allocation attempts and a conditional setup object. Review Build explains that intervening script execution prevents treating those attempts as an additive capacity budget. The existing proved initial-placement rejection remains unchanged. See [qualified shared consumers](legaia-npc-actor-pool.md#shared-consumers-qualified-on-2026-10-03).

Validation: six focused Python checks pass with private retail source and no skips, including a fresh normal Build and complete carrier readback; Node review guards pass. The packaged audit retains all six semantic sites after private-path filtering. No browser, game or export ran for this follow-up. Scenery lookup, script allocation/release and native scene completion remain deferred.

**Retail NPC actor-pool lower bound (2026-10-03):** Normal Review Build/Build now qualify the complete SCUS executable and initially seven retail function spans, derive the143-slot/216-byte actor pool, and reject unavoidable initial-placement overflow before MAN encoding. Source setup evidence establishes the anchor plus partition-1 loop; successful audit metadata keeps other scenery/channel/script demand unknown. Candidate features stay disabled and runtime allocation/gameplay unverified. See [pool check and evidence](legaia-npc-actor-pool.md).

Validation: six focused private-enabled Python checks and existing Node review guards pass. A bounded instruction harness executes the actual pool initializer/pop/failure path:143 distinct slots, then zero without memory changes. Six browser checks prove a normal one-draft package plus a real91-draft Town01 blocker (minimum144 nodes), disabled reviewed Build, unchanged authoring and540px layout. Independent full carrier readback preserves the earlier candidate MAN and fixed-span ownership. Package SHA256 `e8907db2b03619303d72cf3e09fbe2ac82bff7815534733d15c9337a00443c06`. Private proof: `local-output/sdk-20260909/npc-runtime-source-20261003/`. Helpers are closed; no game, install or disc export ran. Full runtime demand/acceptance remain deferred.

**Packet-group texture-binding copy (2026-10-02):** The source-binding picker now fills all textured primitives in a qualified target group in one draft action, with explicit target count. Other group/object drafts, group ABE, untextured rows, target UVs/geometry and source-owned bits remain separate. The complete resulting batch validates before draft replacement; over-budget groups reject atomically. Review, Proposed/Return, one Apply, history, persistence and Build reuse the existing material workflow. See [group copy](legaia-material-binding-picker.md#packet-group-copy-evidence-2026-10-02).

Validation: focused donor/material Node guards and seven actual browser workflows pass. Fresh effective-model hashes verify Undo/Redo. Independent complete TMD construction and packaged carrier readback match:14 target primitives,13 changed rows,26 CLUT/TPage word changes and39 additional bytes, preserving earlier edits and decoded neighbors. Package SHA256 `f1e9c622f00bf4b07fbee0ef1926ecd83872e8430125c94ebda325effcfd39c0`. Private proof: `local-output/sdk-20260909/material-group-binding-20261002/parent/`. Helpers are closed; no game, install or disc export ran. Native appearance/residency acceptance remains deferred.

**Imported model texture-binding picker (2026-10-02):** The material editor now browses active-scene AssetDB models and qualifies their Current source primitive bindings. Explicit Copy fills page/depth/indexed CLUT draft controls while retaining target UVs, geometry and blend flags. Review/Apply, Proposed/Return, history, persistence and normal Build reuse the existing source material command. See [binding picker](legaia-material-binding-picker.md).

Validation: three catalog Python cases, donor Node guards and the existing material lifecycle suite pass. Seven actual browser checks pass through one Apply and Build; a separate visual follow-up verifies UTF-8 labels and540px layout. Independent complete TMD construction/readback proves Current-to-Proposed bytes1102/1103/1106 only, retaining prior ABE byte1095; the entire carrier's neighboring decoded bytes stay unchanged. Package SHA256 `a952ee4f6443068d63f8ddc5b6f636aa31168d3625851d01fcc6a14d0e8a89a3`. Private proof: `local-output/sdk-20260909/material-binding-picker-20261002/parent/`. Helpers are closed. No game, install or disc export ran; UV suitability, live residency, palette animation and native blend appearance remain deferred.

**Assigned actor animation GLB interchange (2026-10-02):** Qualified appearance/initial-clip assignments now export and preview the assigned existing rigid pose. V2 sidecars bind the selected actor, imported clip contribution owner and inherited model witness; the export/review names ownership before Apply. Changes use the owner's existing AnimationChannels command, preserving the selected actor's original clip edits and assignments. Fresh witness/source checks and existing shared-axis conflict guards remain in force; unassigned v1 sidecars remain compatible. See [assigned GLB workflow](legaia-assigned-animation-glb.md).

Validation: four distinct private-retail Python workflow cases and the v1/v2 Node guard suite pass with no skips. Eight actual browser workflows pass through owner-labelled review, retained pose Return,540px controls, explicit Apply, Undo/Redo, Save/reload and normal Build. Independent complete ANM/MAN readback matches: town0b actor0019 retains clip0013 edits; witness0049 owns the clip0012 GLB change. Only ANM bytes8880/10336 and MAN byte9471 differ from retail. Package SHA256 `2d9eaec92f5076624af50f568c6494cd2f01b4b3b27b7f39becb60f2b3ad0aa7`. Private proof: `local-output/sdk-20260909/assigned-animation-glb-20261002/parent/`. No game, install or disc export ran, and helpers are closed. Native clip selection/timing and shared-user gameplay remain deferred.

**World source yaw rotation ring (2026-10-02):** World placements now offers an exclusive source-yaw ring with encoded-unit snapping, perspective-correct frozen-plane pointer conversion, continuous angle unwrapping and 0..4095 wrapping. Shared-record confirmation remains explicit. Temporary previews preserve positions and update every affected instance; Review and Apply use the existing source-qualified command, Undo, persistence, Build and export path. Current comparison gates hidden drafts and cancellation restores prior values/review. See [source yaw ring](legaia-worldmap-placement-yaw.md).

Validation: three focused Node suites and two private-retail Python source/package regressions pass with no skips. Seventeen browser checks pass, including both turn directions, wrapping, independent matrices and unchanged positions for all57 shared instances, cancellation, tool switching,540px controls, one Apply, Undo/Redo, Save/reload, normal Build and stale-source withdrawal. Independent full MAP readback matches X1280/Y256/Z256/yaw448; prior offsets persist and only the two yaw bytes additionally change. Package SHA256 `4a953cf8acfb12105dd121b7c3f6416f9469bfa00907ef4c2999d4e9bc9de6bf`. Private proof: `local-output/sdk-20260909/worldmap-placement-yaw-20261002/parent/`. No game, install or disc export ran; helpers are closed. Native runtime behavior remains deferred.

**World source viewport translation handles (2026-10-02):** World placements now offers source X/Y/Z pointer handles, 1/16/64/128-unit snapping and Frame anchor. Explicit shared scope is required. All affected instances and numeric offsets preview together; release retains a draft, Review qualifies it, and Apply alone records one command/Undo step. Cancellation restores prior draft/review state, and source/camera/layout changes invalidate frozen gestures. A dialog-close race was fixed so cancellation cannot clear another command's busy state. See [translation handles](legaia-worldmap-placement-gizmo.md).

Validation: two focused Node suites and fourteen Python regression cases pass with private input and no skips. Fifteen browser checks pass, including nonzero source/display X/Y/Z movement for all57 shared instances, cancellation, 540px layout, source invalidation, one Apply, Undo/Redo, Save/reload and normal Build. Independent complete MAP readback agrees exactly: record0477 is X1280/Y256/Z256/yaw1536, and only four retail source bytes differ. Package SHA256 `d15d8464e9486a9463dac0b5653e1005aadd9fa942c13e11ebf95fee8d28b6b7`. Private proof: `local-output/sdk-20260909/worldmap-placement-gizmo-20261002/parent/`. No game, install or disc export ran; owned helpers are closed. Native behavior and gameplay verification remain deferred.

**Current/Proposed world placement GLB export (2026-10-02):** World placements now downloads complete qualified kingdom scenes with applied record transforms or an exact reviewed proposal. Exports retain retail geometry, shared meshes, textures and ground, add source/current/exported MAP identities and per-instance retail/exported transform provenance, and preserve unknown runtime visibility/resting state. Proposal export does not Apply, Save or Build. The browser verifies representation, review identity, MAP hashes and binary digest, and rejects late or stale downloads. Existing World ground exports stay retail-source. See [authored world export](legaia-worldmap-placement-export.md).

Validation: six focused Python cases pass with private input and no skips, including unchanged legacy source exports. Independent all-three-kingdom MAP construction verifies every exported translation, yaw and record hash; geometry/image binaries remain identical to retail exports. Node guards validate actual private artifacts. Seven browser scenarios pass with no commands, game requests or page errors; Current and Proposed downloads match independent artifacts byte-for-byte, each with302 entities and57 changed source seeds. Saved project/import/Build files remain exact. The Current MAP hash matches the previously verified Build payload. Private proof: `local-output/sdk-20260909/worldmap-placement-export-20261002/`. No game, install or disc export ran.

**World source placement authoring (2026-10-02):** The World placements viewport now edits qualified shared object-record offsets and yaw for all three walk kingdoms. Source record selection and mesh picking, effective coordinates, shared-record scope, Current/Proposed comparison, frame/orbit, reviewed atomic Apply, Undo/Redo, Save/Open, Authored assets and normal Build are connected. Exact field masks preserve cells, anchors, model references, flags, other axes and opaque bytes. Disjoint MAP overlays compose; conflicting writes reject. Source spawn seeds remain separate from script-evaluated resting positions and visibility. See [world placement workflow](legaia-worldmap-placement-authoring.md).

Validation:17 focused Python cases pass with private source input and no skips, including all-three-kingdom source/package readback and ordinary Build regressions. Node source/review guards and independent transform arithmetic pass. Eight actual browser scenarios verify pending selection and Save/history guards, explicit shared scope, Proposed GPU pixels/matrices,540px controls, history/persistence, normal Build and actual GPU mesh selection. Independent browser-package readback matches all73,728 MAP bytes and changes only bytes15265/15275 against retail; shared record0477 affects57 seeds. No page errors, game requests, installs or disc exports ran. Private proof: `local-output/sdk-20260909/worldmap-placement-authoring-20261002/`. Gameplay acceptance remains deferred.

**Source NPC candidates in normal Build (2026-10-02):** Saved donor drafts now enter inclusive v2 Build review and normal package generation for qualified compressed MAN scenes whose complete candidate fits the original consumed stream. Two source-hashed overlays update that stream and its descriptor size word; carrier size, pointers, neighboring payloads, TOC and disc layout stay unchanged. Supported existing actor/P2 edits compose after append, while other asset overlays retain the normal pipeline. Streaming or oversized additions remain rejected. Packages identify source candidates and keep their feature disabled by default. Native allocation, spawning, scheduling and opaque script behavior remain unverified. See [NPC Build boundaries](legaia-npc-build-candidates.md).

Validation: eleven focused Python checks and sixteen ordinary Build regressions pass with private retail input and no skips; legacy and v2 Node review guards pass. Independent Town01 package readback verifies donor scripts, reached spawn-reference rebasing, existing placement/facing composition and counts `[36,53,39]` to `[36,54,39]`. Optimal LZS uses24,856 bytes within the original24,894-byte stream; decoded MAN grows45,338 to45,917 bytes. Four actual browser scenarios verify inclusive read-only review,540px controls, reviewed Build and unchanged authored/import files with no game requests or page errors. No game, install or disc export ran. Private proof: `local-output/sdk-20260909/npc-normal-build-20261002/`. This supersedes earlier blanket normal-Build draft rejection statements; broader gameplay acceptance remains deferred.

**World-map source GLB export (2026-10-02):** World ground inspection now connects to private GLB downloads for all resolved source placements plus terrain, terrain alone when the placement layer is hidden, or one selected source entity. Shared meshes, source transforms, embedded matched textures and source provenance use the existing scene exporter. Fresh source checks bind exports to the imported disc and current project; late responses after closing or changing sources cannot trigger downloads. Exported placement seeds retain unknown runtime resting positions and visibility. Exports create private artifacts without authored commands or Build/disc output. See [world-source export](legaia-worldmap-export.md).

Validation: 16 focused Python cases passed with private retail input and no skips; three Node guard suites and frontend syntax checks passed. Independent all-three-kingdom readback verifies source world corners, reflected winding, shared meshes, UVs, stored colors, embedded PNG pixels and provenance. Nine actual browser scenarios pass, including five downloaded artifacts, ground-only visibility scope, selected seed scope, 540px controls, cancelled late responses and stale-source withdrawal. Downloaded geometry binaries and normalized metadata match the independent exports. Blender 5.2.2 LTS imports the complete map01 scene with 302 entity roots, 303 mesh objects, 67 materials and 60 images; all local triangles match, and maximum world-coordinate float error is 0.0009765625 source unit. Saved project/import/Build files remain unchanged; no game, authoring command or disc export ran. Private proof: `local-output/sdk-20260909/worldmap-glb-20261002/`.

**Scenery group source-angle rotation (2026-10-02):** The existing anchor rotation workflow now accepts every integer source yaw delta from 0 through 4095, alongside its compatible quarter-turn controls. A frozen Q30 quarter-wave table and signed integer nearest-half-away rounding produce reviewed X/Z positions; cardinal turns remain exact. The editor independently checks the same arithmetic before accepting a report. Review, retained Proposed/Current inspection, atomic Apply, Undo/Redo, Save/Open and normal Build preserve source Y, other rotation axes, shared descriptors and unrelated components. Rounded positions can change distances slightly; this authoring convention does not establish retail GTE rounding or gameplay acceptance. See [group rotation workflow](legaia-scenery-group-rotation.md).

Validation: 19 focused Python cases passed with no skips; two Node guard suites and frontend syntax checks passed. All 4096 angles match between Python integers and JavaScript BigInt for six signed displacement pairs, with identical frozen tables. Twelve actual browser scenarios verify custom angle review, invalid-input rejection, retained Proposed/Current comparison, history, Save/reload, normal Build, cancellation and stale-state withdrawal; the 540px layout was visually inspected. Independent renderer matrices and reopened full 73,728-byte MAP package readback match the reviewed 45° proposal. Only bytes 171/256/260/267 change against the prior authored fixture; source Y, other axes, shared records, prior Collision and retail MAP remain intact. No game or disc export ran. Private proof: `local-output/sdk-20260909/scenery-group-angle-20261002/`.

The SDK is functional for supported offline authoring workflows, but the full editor and runtime parity objective is incomplete. Gameplay verification is deferred at the user's request. No new game launch is needed to review the work below.

**Source-normal model diagnostic (2026-10-02):** The static Model shading control now offers source-normal direction colors alongside the default textures/stored colors. Checked raw per-corner TMD normals follow flat/Gouraud references and quad triangulation; unlit or invalid references remain unavailable, and zero/singular directions display gray. One inverse-transpose display transform includes the Y reflection. Existing normal-vector/reference authoring is visible through Retail/Authored comparison, history, Save/Open and normal Build. Animated poses explicitly disable the diagnostic; assembled posed scene geometry does not retain static normal metadata. This visualizes source directions without reconstructing retail lighting.

Validation: 43 focused Python cases passed with private retail input (no skips), two Node guard suites and frontend syntax checks passed. Independent raw decoding matches all119 Town01 models:404lit and14,321unlit triangles, with no invalid or zero corners. Ten actual browser scenarios verify zero uploads on mode flips, exact default framebuffer restoration, normal-vector Apply/history/persistence,540px wrapping, animation playback/disablement and normal Build. Actual WebGL pixels independently prove Y reflection and unchanged picking with no GL errors. Package readback adds only bytes3332/3333/3335 to the previous authored model, preserving its material/reference edits, vector padding, decoded neighbors and154,547-byte compressed capacity. No game or disc export ran. See [source-normal workflow](legaia-model-source-normals.md). Private proof: `local-output/sdk-20260909/model-source-normals-20261002/`.

**Scenery group quarter-turn rotation (2026-10-02):** Selected static decorations can rotate their source X/Z layout around a selected anchor by 90°, 180° or 270°, with the same delta added to each source yaw. Exact integer arithmetic preserves distances and the anchor position. Qualified Review, retained Proposed/Current scene comparison, atomic Apply, Undo/Redo, Save/Open and normal Build are connected. Shared source descriptors and unrelated overrides remain intact. This edits source yaw while retaining X/Z rotation axes; it is not arbitrary three-axis rigid rotation.

Validation: seven focused Python cases passed (no skips), two Node guard suites and frontend syntax checks passed. Twelve integrated browser scenarios plus a bounded 540px control-layout regression passed. Independent expanded matrices match the actual Proposed renderer transforms; reopened full 73,728-byte MAP packages match independent source construction. Only bytes171/256/260/261/267 change against the saved Collision/offset fixture. Source MAP and prior Collision remain unchanged; no game or disc export ran. Gameplay visibility, script transforms and collision acceptance remain deferred. See [group rotation workflow](legaia-scenery-group-rotation.md). Private proof: `local-output/sdk-20260909/scenery-group-yaw-20261002/`.

**Scenery viewport yaw handles (2026-10-02):** Rotate scenery Y previews source-bound transforms without project writes during a drag. Individual static decorations retain cell ownership; placed scenery requires explicit shared-transform enable. Absolute-angle snapping, Undo/Redo, Save/Open and normal Build use the existing Environment command/writer. Resize, Escape and stale-source changes cancel previews; actor movement remains available. Preview uses source `Rz * Ry * Rx` and one display Y reflection.

Validation: ten focused Python cases passed with the private retail disc (no skips), the Node rotation guard suite and frontend syntax checks passed, and twelve integrated browser checks plus an actor-handle regression passed. Independent package readback changes only yaw bytes171 (0→4) and6987 (8→12), preserving prior Collision, offsets, grid ownership and other axes. No game was launched or disc output written. Runtime visibility, scripts and collision acceptance remain deferred. See [scenery yaw workflow](legaia-scenery-rotation-gizmo.md). Private proof: `local-output/sdk-20260909/scenery-yaw-20261002/`.

**Source-bound GLB material editing (2026-10-02):** Fresh profile v6 adds
`_LEGAIA_SOURCE_MATERIAL` for full stored CLUT/TPage words and shared group ABE.
Exact integer primitive aliases and whole-group transparency aliases must agree.
Qualified masks preserve reserved CLUT bits, source ABR, other mode bits, row
commands and allocation. Untextured CLUT/TPage retain -1; group ABE remains
editable. Existing source positions, UV/RGB, normals and references compose;
legacy profiles retain their earlier field permissions. Review/Proposed
inspection/Apply/history/Save/Build use the normal model replacement workflow.
Shader assignments and texture images are separate; static associations may
remain partial. Retail blend/appearance acceptance remains deferred. See
[material GLB workflow](legaia-model-glb-materials.md).

Validation: 44 focused Python cases passed with the private retail disc (no
skips), two Node guard suites and frontend syntax checks. Actual Blender 5.2.2
no-op roundtrips are byte-exact; independent CLUT/group ABE, TPage and untextured
sentinel proofs change only bytes131/138, byte142 and byte299 respectively.
Twelve integrated browser checks cover fresh exports, no-op, reviewed source
fields, Proposed/Return, 540px layout, Apply/history/Save/stale withdrawal and
normal Build. Reopened package readback retains prior normal-reference/XYZ
bytes2940/3332 and adds only material bytes131/138, preserving neighboring data
and the 154,547-byte compressed capacity. No game was launched and no disc output written.
Private proof: `local-output/sdk-20260909/model-glb-materials-20261002/`.

**World-map source placement inspection (2026-10-02):** **World ground** now
opens a source scene with 301/272/236 sparse model placements in map01/map02/map03.
The hierarchy, mesh picking, Frame selected and Source model placements toggle
expose stable entity IDs, MAP cells, record hashes, dictionary slots and source
XYZ. Column-major source yaw/translation becomes a row-major renderer transform
with one display Y flip. The ground asset and source coordinates remain unchanged.
This is read-only; source changes withdraw geometry and pending-close cancels reads.
Runtime visibility, script-adjusted resting positions and animation remain
unverified. Model textures are partially resolved and missing associations stay
explicit. See [placement workflow](legaia-worldmap-placements.md).

Validation: eleven focused Python cases passed with the private retail disc
(no skips), plus ground and placement Node guards and frontend syntax checks.
Independent raw-source comparisons match every seed position, rotation, record
hash, model slot, loaded model topology and source-member hash in all kingdoms;
ground geometry remains unchanged. Nine integrated browser checks cover actual
rendering, hierarchy/coordinates, mesh picking, toggles, camera controls, 540px
layout, source withdrawal, pending-close and exact saved project/Build file hashes.
No game was launched or disc output written. Private proof:
`local-output/sdk-20260909/worldmap-placements-20261002/`.

**World-map walk-ground workspace (2026-10-02):** The editor's **World ground**
resource action now opens source-backed textured 3D ground for map01, map02 and
map03 through the shared scene renderer. The importer qualifies the overlapping
kingdom carriers, exact 0x12000 MAP footprint, slot-2 MAN floor LUT and slot-0
TIM atlas. Orbit/zoom, Frame ground, Top view, Wireframe and source details are
read-only; source changes withdraw retained geometry and closing pending reads
releases controls. Imported field selection, authored state, history and Build
files remain unchanged. Source Y-down coordinates flip only at the renderer.
Overview/MAPDSIP, script-managed resting transforms, sky/fog and runtime parity remain pending.
See [world-ground workflow](legaia-worldmap-geometry.md).

Validation: six focused Python cases passed with the private retail disc (no
skips), plus Node source/geometry/texture guards and frontend syntax checks.
Independent readback matches every ordered vertex, triangle, UV and visible-cell
selector in all three kingdoms. Visible cells are 16,251/16,381/16,374; source
texture coverage is 23/23, 17/18 and 15/16. Missing palettes stay explicit, without
fallback textures. Eight browser checks cover actual three-kingdom rendering,
camera controls, 540px layout, stale withdrawal, pending-close and unchanged
project files. No game was launched, no disc output written. Private proof:
`local-output/sdk-20260909/worldmap-geometry-20261002/`.

**Source-bound GLB normal-reference editing (2026-10-02):** Fresh profile v5
adds `_LEGAIA_SOURCE_NORMAL_INDEX` for selecting an existing normal within the
source object. Immutable corners retain packet ownership; flat references and
all raw XYZ aliases must agree. Unlit index -1 and XYZ sentinel remain explicit.
Changed references use `tmd-content-v3`; older content versions keep normal
references immutable. Review/Apply/history/Save/Open and normal Build compose
reference changes with earlier authored normal words. Material inspection,
source-bound JSON/TMD review and object transforms preserve the new references.
Counts, allocation, padding and unrelated source bytes remain fixed. Retail
lighting and gameplay parity remain deferred. See
[normal-reference workflow](legaia-model-glb-normal-references.md).

Validation: 42 focused Python tests passed with the private retail disc (no
skips), plus Node workflow and frontend syntax checks. Twelve integrated browser
checks cover actual Blender review/no-op, proposed inspection, Apply/history/
Save, 540px layout, stale rejection and Build. Independent flat/Gouraud rewiring
changes only byte2940/byte4284 respectively, retaining the earlier normal edit.
Integrated Build retains bytes2940 and3332, unchanged neighbors and the original
154,547-byte compressed capacity. Legacy content downgrades reject the changed
reference. No game was launched. Private proof:
`local-output/sdk-20260909/model-glb-normal-references-20261002/`.

**Source-bound GLB normal editing (2026-10-02):** Fresh model profile v4 adds
`_LEGAIA_SOURCE_NORMAL` raw signed-i16 XYZ for existing lit packet normal owners.
Shared flat/Gouraud aliases must agree after rounding. Retail axes remain
[x,y,z], without POSITION's Y flip or normalization; unlit corners retain the
out-of-domain [32768,32768,32768] sentinel. Display NORMAL is ignored. Normal
references, padding, allocation and unrelated bytes remain unchanged. Review,
Apply, undo/redo, Save/Open and normal Build use the existing model replacement
workflow. Legacy v1-v3 codec behavior remains; SDK editing requires a fresh v4
export. Retail normal-based lighting and gameplay acceptance remain pending.
See [normal workflow](legaia-model-glb-normals.md).

Validation: 27 focused Python tests passed with the private retail disc (no
skips), plus Node workflow and frontend syntax checks. Twelve browser checks
cover actual Blender no-op/edit review, proposed geometry, Apply/history/Save,
540px layout, stale rejection and normal Build. Independent Blender 5.2.2
readback changes only byte3332 for a shared flat normal and byte4640 for a
Gouraud normal. Integrated Build preserves all decoded neighbors and the
154,547-byte compressed capacity. No game was launched. Private proof:
`local-output/sdk-20260909/model-glb-normals-20261002/`.

**NPC facing composition and output review (2026-10-02):** Source script facing
edits now compose with appended NPC drafts in compressed and streaming MAN
carriers. Original record ownership is re-resolved after append; only the facing
nibble changes, upper flags remain intact, and donor clones retain retail facing.
The editor's **Review NPC output** prepares an in-memory archive and reports
source identities, relocated fields and allocation limits without writing a
package/disc, changing history or launching the game. Normal Build still rejects
NPC drafts; gameplay, scheduling and general allocation remain unverified.
See [draft facing workflow](legaia-draft-facing.md).

Validation: 16 focused Python tests passed with the private retail disc (no
skips), plus Node metadata guards and frontend syntax checks. Six integrated
browser checks cover actual two-scene review, exact metadata, 540px layout,
stale-input withdrawal, pending-close handling and unchanged saved files.
Independent Town0b/Dolk2 readback verifies four/one facing-byte changes, each
rebased by three bytes after append; donor copies and unrelated bytes are retained.
Private proof: `local-output/sdk-20260909/draft-facing-20261002/`.

**Source-bound GLB face rewiring (2026-10-02):** Model profile v3 adds existing
polygon vertex references to the external mesh workflow. Immutable source corner
IDs retain face ownership; qualified vertex IDs may select existing vertices in
the same object. Seam/quad reference and coordinate aliases must agree. Review
shows exact source/current/proposed references before ordinary Apply/history/
persistence/Build. Object, vector, polygon and packet capacities stay fixed;
new objects/polygons, normal tables and material allocation remain pending.
Legacy v1/v2 codec behavior is retained; SDK authoring requires a fresh v3 export.
See [face workflow](legaia-model-glb-faces.md).

Validation: 22 focused Python cases passed with the private retail disc (no
skips), plus the Node workflow and frontend syntax checks. Twelve browser checks
cover exact reference Review, regenerated proposed geometry, no-op and stale
rejection, 540px layout, Apply/history/Save and normal Build. Actual Blender 5.2.2
updates both aliases of one quad corner, vertex 17 to 0; independent readback
changes only byte434 (136 to 0). Build retains earlier RGB/material bytes300,
1095 and1102, all decoded neighbors and the 118,461-byte compressed capacity.
No game was launched; gameplay appearance and general allocation remain pending.
Private proof: `local-output/sdk-20260909/model-glb-faces-20261002/`.

**Raw RGB model GLB editing (2026-10-02):** The existing external model workflow
now imports qualified baked RGB through `_LEGAIA_SOURCE_RGB` in the raw 0..255
byte domain. Profile v2 binds each flat/shared or Gouraud/corner color to its
source packet; duplicate aliases must agree, and packets without stored RGB
retain explicit -1 sentinels. Review exposes exact fields and rounding error
before ordinary Apply/history/persistence/Build. Display `COLOR_0`, shader colors,
normals, references, material words and allocation remain outside this lane.
Fresh exports use v2; the codec retains legacy v1 positions/UV behavior. Existing
bindings require a fresh export for SDK Apply. See [RGB workflow](legaia-model-glb-rgb.md).

Validation: 18 focused Python cases passed with the private retail disc (no
skips), plus the Node workflow and frontend syntax checks. Twelve browser checks
cover no-op, exact RGB Review, proposed model, 540px layout, file invalidation,
Apply, Undo/Redo, Save, Build and stale-source rejection. Actual Blender 5.2.2
round trips flat and Gouraud edits exactly. The saved Dolk2 Build adds only byte
300 (24 to 25) to the two existing material bytes, preserving decoded neighbors
and the 118,461-byte compressed capacity. No game was launched; runtime lighting
and appearance remain deferred. Private proof: `local-output/sdk-20260909/model-glb-rgb-20261002/`.

**Coordinated scene animation (2026-10-02):** The central viewport now previews
eligible actors together with Play/Pause, integer scrubbing, an explicit preview
rate and exact Stop/Restore. Retail and Authored projections retain their source
identity, placements, material/texture associations and separate shared channel
contributions. Sampling is transient; persistent editing is blocked until Restore.
Dolk2 covers 69/72 actors in 15 tracks; Town01 source proof covers 42/52 in 22.
Static/unavailable actors stay explicit. Six Python tests, the Node lifecycle
suite and integrated browser checks pass, with no game launched. Effective-channel
frame zero matches the independently composed bank; Retail stays distinct.
Retail timing, scheduling and current live animation remain unverified. See
[timeline workflow](legaia-scene-animation.md).

**Source-qualified model materials (2026-10-02):** The model inspector now edits
existing CLUT/page/depth bindings and shared packet-group ABE with exact masks,
source/current Review, proposed model/posed-scene inspection and explicit Apply.
Ordinary Undo/Redo, Save/Open and Build retain versioned material overrides.
Source ABR stays read-only because traced retail paths supply caller blend state.
Twenty-two focused Python tests, three Node suites and six integrated browser
checks pass. The actual Dolk2 proof changes only bytes 1095 and 1102; Build readback
preserves the 118,461-byte compressed capacity and every decoded neighboring byte.
Geometry and a fresh GLB round-trip stay exact. Gameplay blending/residency and
general material allocation remain pending. See [workflow](legaia-model-materials.md).

**Source-bound texture PNG editing (2026-10-02):** Imported textures now support
current PNG + binding + separate STP export, external image editing, exact
source/current Review, Current/Proposed pixel and scene inspection, and explicit
Apply through normal texture history, Save/Open and Build. Existing palette mode
retains words; deterministic rebuild changes only the selected CLUT row. Shared
indices, color error and forced black/transparent STP changes are reported.
Dimensions, bit depth, VRAM rectangles and source capacities remain fixed.

Validation: 12 focused Python cases, the Node workflow suite, both frontend
syntax checks and 11 integrated browser checks passed. Independent Pillow 12.1
proofs cover both palettes of a retail Dolk2 TIM, exact nibble/word edits,
transparent/opaque-black semantics and deterministic color reduction. The saved
Town01 browser Build contains the exact reviewed 33,312-byte TIM with unchanged
other CLUT rows and neighboring source bytes. Scene preview changes 26 materials
across 10 instances while preserving geometry/placements; Return restores the
scene and retains exact Files. Review-only, stale/no-op, history, persistence and
540px checks passed, with zero page/HTTP errors or game-launch requests. Large
unique-color images may be CPU-intensive; gameplay and live blending remain
deferred. See [workflow and limits](legaia-texture-png.md); private evidence is
under `local-output/sdk-20260909/texture-png-20261002/`.

**Source-bound model GLB editing (2026-10-02):** Imported models now support
Export current model + binding → external mesh edit → Review → Inspect proposed
model → Apply → Undo/Redo → Save/Open → normal Build. Explicit source vertex
and corner attributes retain identities across Blender splits and quad
triangulation. This imports existing positions and UV bytes; effective RGB,
normals, face references, material words, images and opaque bytes are preserved.
Topology allocation and arbitrary mesh/material replacement remain pending.

Validation: 14 focused Python tests, the Node workflow suite, both frontend
syntax checks and 12 integrated browser checks passed. Actual Blender 5.2.2
round-tripped a fresh SDK export exactly; its edit changed only vertex 27 X and
primitive 50/corner 2 U of Dolk2 model 0133. The saved browser Build independently
reproduces those two fields and unchanged neighboring decoded bytes within the
118,461-byte compressed source span. Review/preview are read only; stale/no-op
Apply guards, history, persistence and 540px layout passed. Page/HTTP errors and
game-launch requests were zero. Gameplay appearance remains deferred.
See [workflow and limits](legaia-model-glb.md); private evidence is under
`local-output/sdk-20260909/model-glb-20261002/`.

**Imported project Asset Database (2026-10-02):** The primary asset browser now
offers explicit project discovery, source-scene filtering, searches across all
retained memberships, and pages of 128 rows. Shared IDs retain complete per-scene
variants; Details selects one source membership before opening existing tools.
Cross-scene derived inspection refreshes and compares that source catalog first.
Discovery uses detached views and does not change imports, authored state,
selection, history, saved files or active caches. Navigation retains the index;
source or authored changes invalidate it and require a new refresh.

The Town01/Dolk2/map01 source audit returns 3,637 unique identities and 3,703
memberships, with all three inventories explicitly partial. Counts do not imply
complete format coverage, runtime residency, actor spawning or gameplay parity.
See [project asset workflow and limits](legaia-project-assets.md). Private
evidence is under `local-output/sdk-20260909/project-assets-20261002/`.

Validation: 18 selected Python tests, two Node suites, both changed-module syntax
checks and 19 integrated browser checks passed. Source discovery preserves
populated caches and saved files; exact P2 owner/PC focus and canonical tool
handoffs passed. A private edit followed by Undo verifies invalidation and stale
action rejection without Save/Build. Controls and the source inspector fit
540px. Page/HTTP errors and game-launch requests were zero.

**Source-qualified global landmark authoring (2026-10-02):** The world-map
workspace edits the 20 existing SCUS menu records with separate Retail,
Authored, Current and reviewed Proposed values. Existing name/discovery,
CDNAME destination and encoded X/Y fields have a duplicate-safe 2D diagram,
exact byte review, Apply/reset, Undo/Redo and Save/Open. Authored asset links and
normal Build reports reopen the source row. Normal Build emits a guarded
126-byte SCUS data overlay, with independent whole-executable reconstruction;
field placement composition retains both overlays and unchanged imports.
Experimental Export disc rejects this global component explicitly.

Name and discovery consumers are now qualified by retail static analysis.
Destination and X/Y meanings remain reference interpretations; drawing,
travel, discovery activation and gameplay are not verified. The table has 20
rows, terminator row 20 and two padding bytes before 16 immutable name slots.
See [landmark authoring workflow and evidence](legaia-worldmap-authoring.md).

Validation: 36 selected Python tests passed with the private retail disc and no
skips; two Node suites, both changed-module syntax checks and 16 browser
workflows passed. Browser page/HTTP errors and game-launch requests were zero.
The saved browser package independently reconstructs the executable with only
file byte 0x6429C changed 96-to97 (row 0 X), while fresh scene imports still match.
Review exposes field changes, byte offsets and the candidate hash; draft gates,
reset/history/persistence, 540px layout and Build-to-source navigation passed.
Private proof is in `local-output/sdk-20260909/worldmap-authoring-20261002/`.
The full SDK and gameplay acceptance remain incomplete.

**Source-qualified field branch authoring (2026-10-02):** The script workspace
now links a selectable source-flow diagram to disassembly and reviews existing
JMP, conditional, bounding-box, flag-word and ordinary system-flag destinations.
Retail, authored, current and proposed edges remain separate; encoded conditions
are not evaluated. Targets must be original instruction or atomic MES starts
through PC32767. Reviewed Apply/reset uses ordinary Undo/Redo and Save/Open;
normal Build, streaming export, appended-record composition and operand files/
bundles retain record layout and independently qualify changed flow. Other
authored operands survive branches that make source nodes unvisited.

Retail handler validation also corrects three existing decoder interpretations:
camera apply and FIELD43/44 continue, and flag-word targets use relative offsets.
Ordinary SYSFLAG forms cover50..7F; extended forms stop with an explicit reason.
The pinned Andrew reference remains unchanged. Town01 now has619 decoded dialogue
segments and1339 flag references; Dolk2 has629 segments and744 references.
See [field branch workflow and evidence](legaia-script-branches.md).

Validation:88 integrated Python regression cases passed with the private retail
disc and no skips, including compressed Town01 and raw Dolk2 normal packages.
Three HTTP cases reject18 malformed/foreign requests and stale Apply without
changing evidence or history. Four Node suites and15 browser workflows passed;
browser page/HTTP errors and game-launch requests were zero. The browser's
reviewed Town01 package independently reads back with only byte4791 changed
(PC31 target15-to11); its saved imports still match a fresh source import.
Dolk2 PC28 target63-to9 changes only bytes7481/7482. Real Town01 donor append
preserves that branch at rebased byte4794 in the prepared MAN; full rebuilt-disc
acceptance is deferred. Current/Proposed navigation, multiple pending choices,
reviewed Apply/reset, Undo/Redo, Save, no-op/stale gates, narrow layout and exact
Build-to-source navigation were checked. Private evidence remains in
`local-output/sdk-20260909/script-branches-20261002/`. Runtime branch activation,
story behavior and termination remain deferred; the full SDK remains incomplete.

**Model faces, UVs and baked colors (2026-10-02):** The model viewer now
provides a source-bound primitive editor with separate Retail, Current and
Proposed values. Existing face connections, UV byte pairs and stored RGB words
can be authored across all 24 supported flags. Preview uses paired textured
views with a shared camera; a reviewed proposal can be inspected across supported
scene instances while retaining their existing poses and placement. Apply checks
current model, scene and candidate hashes. Undo/Redo, Save/Open, authored TMD
export and normal Build use a versioned `tmd-content-v1` binding; legacy
`tmd-shape` bindings retain strict XYZ-only validation. Vector/whole-object/JSON
edits preserve authored primitives. Pose composition now refreshes face/color/UV
arrays, and proposed scene textures recrop from candidate UVs. Normal Build audit
links reopen the exact source primitive. Object/group counts, capacities, normal
references, material bindings and opaque bytes remain source-owned. Arbitrary
new mesh allocation and runtime lighting/culling acceptance remain unfinished.
See [model content workflow](legaia-model-content.md).

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

**Visual transition graph workspace (2026-10-02):** Scene and Project
transitions now open a selectable node/arrow diagram, scene list, search,
imported-only filter, direct-reference focus, zoom/pan/Fit and paginated source
instructions. Parallel instructions remain independent records; arrow badges
group only equal source/destination pairs. Retail, Authored and Effective entry
bytes stay separate. Source-script navigation selects the exact owner and PC;
imported destinations use ordinary scene selection. Coverage, unavailable
catalogs and unresolved names remain explicit. Project-only freshness changes,
stale responses and pending-close/reopen cleanup and old-request isolation invalidate retained controls. The
canvas draws at most 80 scenes and 160 pairs; every matching instruction remains
accessible in 20-row pages. No gameplay route or story reachability is inferred.
See [transition graph workflow](legaia-project-transitions.md).

Validation: 26 selected retail-enabled Python cases passed with zero skips;
6 Node suites and 3 changed-module syntax checks passed. Thirteen actual browser
workflow checks passed with zero page/HTTP errors, zero authoring commands and
zero game-launch requests. The four-scene Town01/Dolk2/Town0b/map01 fixture has
17 nodes, 18 grouped pairs and 35 instructions from 319 scripts (195 partial,
zero unavailable). Graph, narrow-layout and entry-layer captures were inspected;
long arrows avoid intervening scene boxes and badges remain selectable above
crossing lines. Imported metadata and the saved project are unchanged. This
source-reference workspace is accepted offline; gameplay/runtime verification
remains deferred for the wider SDK. No game was launched or package installed.

**Reviewed primary trigger cells (2026-10-02):** Existing primary MAP kind-0
teleport and kind-1 binding rows now have an Edit trigger cell action. Retail,
Authored, Current and Proposed X/Z cells remain separate, with outline and scene
comparison, per-row retail reset, one-step Undo/Redo and Save/Open. Fresh source
and review keys qualify the complete retained binding; stable row identity stays
independent of coordinates. Only two lookup-coordinate bytes are writable.
Destinations, record/gate payloads, row order, footprints, elevation and all other
MAP bytes remain unchanged. A separate trigger key invalidates annotations
without reloading geometry. Normal Build composes triggers, regions, scenery and
collision walls in one exact MAP overlay, independently binding every trigger
byte to the requested cells. Build report links reopen the source resource.
Fallback rows remain read-only; unknown gates keep their unresolved behavior.
Moving a row can change first-match shadowing. Height, contact, activation and
playable behavior remain deferred. See [trigger cell workflow](legaia-trigger-cells.md).

Validation:50 selected retail-enabled Python cases verified without skips,
including the12 affected/neighbor cases rerun after repairs;6 Node suites and3
changed-module syntax checks passed. Thirteen actual browser workflow checks
passed with zero page/HTTP errors and zero game-launch requests. Visually
inspected review and viewport captures are readable. The retained Town01
kind-0/0000 fixture changes only MAP65554 from30 to31, preserving destination
bytes146/132. Fresh disc-span, ZIP and imported-metadata readbacks agree. The
package is built, not installed or played; full SDK/runtime scope remains incomplete.

**Source-facing instruction authoring and object-index correction (2026-10-02):**
The actor Inspector now opens source-qualified facing controls for simple
CAM_CFG and nonparked NPC_RUN instructions. Retail, Authored and Effective
sectors remain separate; drafts have a numeric compass preview, Apply/Clear,
Undo/Redo and Save/Open. Source-bound operand JSON and scene bundles include
ScriptFacing. Normal Build composes the exact low-nibble writes with other MAN
edits and checks the full byte audit and compressed capacity. Retail dispatch,
LUT reads and actor-facing stores were verified statically before implementation.
The shared Inspector also renders additional registered components through their
schema. Gate-0 object references now preserve unresolved flat MAN indices;
gate-1 remains explicitly P2-local. Initial/live actor heading, branch selection,
experimental NPC append export and gameplay acceptance remain unresolved.
See [source-facing workflow](legaia-script-facing.md).

Validation:56 focused retail-enabled Python tests passed without skips in70.133s;
7 Node checks and3 changed-module syntax checks passed. Nine actual browser
workflow checks passed with zero page/HTTP errors and zero game-launch requests;
a real P2 report independently validates/renders31 controls with explicit
extended-context uncertainty. Retained Town0b actor0019 packaging changes only
MAN byte9479 from0x81 to0x85, preserving the upper flag. Imports remain unchanged.
The package is not installed or played; full SDK/runtime scope is incomplete.

**Reviewed field region bounds (2026-10-02):** Primary MAP regions now have
an Edit region bounds action, four strict corner inputs, separate Retail /
Authored / Current / Proposed layers, and outline/viewport comparison. Apply
and per-row retail reset use one undo step; inherited/no-op values normalize
without dirtying the project. Source-qualified effective annotations leave the
imported spatial envelope intact, and a separate region key invalidates views
without reloading geometry. Save/Open and normal Build preserve the region
type, padding, source order and all bytes outside audited corners. Region edits
compose with scenery and collision walls in one MAP overlay. Browser review,
frame, comparison, Apply, history, persistence and scene cleanup passed with
zero page/HTTP errors and zero game-launch requests. The retained Town01
fixture changes only MAP byte66692 from58 to59; its package is built but not
installed or played. Height, activation and movement acceptance remain deferred.
See [region bounds workflow](legaia-region-bounds.md). The full SDK/runtime
objective remains incomplete.

Region milestone validation:54 retail-enabled Python tests passed with no skips in74.565s;42 Node checks and40 module syntax checks passed. Actual browser comparison passed10 workflow checks with zero page/HTTP errors and zero run requests. Independent package readback confirms one byte changes; imported scene hashes remain unchanged. No game launched or package installed.

**Field source cells and script links (2026-10-02):** Verified trigger and
region rows now appear in the scene hierarchy and shared Inspector, with
viewport outlines, framing and explicit source-cell picking. Trigger dispatch
uses `world >> 7`; region lookup uses `(world - 64) >> 7`, preserving the
64-unit difference. Display Y=0 remains an inspection plane with unknown
height. Coincident rows retain separate source identities. Gate-1 rows link to
unique bounded P2 scripts in Active/Project reference graphs with both record
hashes; object binds, unknown gates and missing/aliased targets stay unresolved.
Town01 supplies 99 trigger cells,14 region bounds and 51 eligible script links.
Read-only HTTP, source qualification, browser navigation/picking and stale-scene
cleanup passed. No game launched or package installed; contact/activation and
retail height acceptance remain deferred. See
[field source workspace](legaia-field-source-workspace.md). Full SDK/runtime
coverage is still incomplete.

Final validation:59 retail-enabled Python tests passed with no skips in84.629s;41 Node checks and39 module syntax checks passed. Actual browser frame/pick, overlapping rows, reference/script navigation, actor restoration and scene invalidation passed with zero page/HTTP errors. The saved baseline/import hashes remained unchanged; no package or game was launched.

**Central transition assets (2026-10-02):** Decoded scene-change instructions
now appear in the Asset Browser, shared Inspector and Active/Project dependency
graphs. Imported/authored/effective entry bytes and static destination arrival
coordinates remain distinct from unknown source triggers. A dedicated transition
key invalidates stale views without reloading geometry. Fresh serializer checks
qualify authored entries; partial catalog coverage with zero decoder stops no
longer blocks otherwise supported entries. Retail discovery found 35 transitions
across Town01, Dolk2, map01 and Town0b.55 retail-enabled Python tests passed
with no skips;39 Node checks and38 syntax checks passed. Browser editing,
history, persistence, source/destination navigation and reference scopes passed.
Reopened Build changes only Town01 MAN bytes28574 (96 to128) and28576 (4 to2).
No game launched; existing transition-arrival gameplay acceptance is deferred.
See [transition asset workflow](legaia-transition-assets.md). The full SDK and
runtime objective remains incomplete.

**Reusable initial-animation presets (2026-10-02):** Versioned v2 presets
capture a verified initial clip alone or with authored position/appearance.
Frozen witness proof survives later source-actor edits; full proposed components
are validated together before one single/group Apply. Omitted components and
imported channel ownership stay intact. Inherited clip matches normalize to
absence, including a true no-op on untouched targets. Metadata-only v2 files
retain fresh source/import/hash proof and independent library identity; legacy
v1 files/scopes remain supported. Proposed/Current scene comparison, Return,
Undo/Redo and Save/Open are connected.47 focused retail-enabled Python tests
passed in57.695s, plus8 HTTP/project compatibility tests in1.293s;37 Node files
and37 syntax checks passed. Actual browser capture/transfer/single/group scene
review/Apply/history/Save passed with zero page or unexpected HTTP errors.
Independent Town0b pure-clip MAN readback changes only9471,14→13; inheritance
reproduces baseline output. The saved combined fixture changes only19122,13→14,
and19123,119→150 (X15296→2944), retaining model0102/Z1472. Reopened Build
reproduces package SHA256 `2cc94474453d5a5bd8eaddb07808c6f3dbd10d089d126f9a8e8c4cb0dbd06389`.
No game launched; existing playback/script/gameplay acceptance remains deferred.
See [animated preset workflow](legaia-animated-actor-presets.md). The full SDK
and runtime objective remains incomplete.

**Central flag-reference assets (2026-10-02):** Source-scoped flag groups
now appear in Asset Database search, a shared Inspector, and Active/Project
script dependency graphs. The Inspector shows retail/authored/effective sites,
coverage and exact-PC navigation for P1/P2 owners. A dedicated operand-state
key invalidates stale annotations without changing geometry; project flag
keys now include authored operands. Fresh Town01/Dolk2/map01 sources yielded
899 groups/2,142 sites; source browsing preserves project/saved state.
43 focused retail-enabled Python tests passed in20.085s;36 Node files and36
syntax checks passed. Browser P1/P2 exact-PC navigation, operand layers,
Undo/Redo/Save/Clear, stale-view closure and Active/Project references passed
with no page or unexpected HTTP errors. Runtime variables, story names and
unseen paths remain unresolved. See [flag asset workflow](legaia-flag-assets.md). Gameplay remains
deferred; the full SDK/runtime objective is incomplete.

**Initial animation assignment (2026-10-02):** The actor Inspector now offers
source-verified same-model clip choices, explicit Review/Apply/Clear and witness
preview. A separate ActorAnimation component preserves imported channel ownership,
Undo/Redo and Save/Open. The authored scene and assigned GLB preview keep target
identity/position; normal and draft writers compose the final MAN header once.
Effective references and unconfirmed Live candidates keep animation witnesses
separate from appearance donors and invalidate stale observations. Incompatible
appearance/preset/revert changes reject atomically. Legacy v1 templates capture position/appearance; versioned v2 presets now
include the separate initial assignment. Global/zero/unknown/partial pairings remain
unsupported; scripts, timing and gameplay suitability remain unverified.
39 focused retail-enabled Python checks passed in55.598s, plus a22-check
compatibility pass in21.572s; all34 Node files and35 syntax checks passed. Seven raw MAN/appearance compatibility checks
also passed in47.334s without skips.
Actual browser Review/Preview/Apply/Clear, assigned-frame GLB export,
Undo/Redo/Save, exact scene placement and initial/effective reference edges passed
with zero page errors; malformed/stale HTTP rejected without history changes.
Visual review repaired a clipped Review button; final layout and screenshot
passed. Fresh Town0b package readback changes only MAN offset9471,14→13,
model0102/positions/imports/saved bytes unchanged. Record12 digest and exact
retail import were reverified; clearing reproduces baseline package bytes.
Draft composition preserves the appended retail donor clip and rebases the
existing header9471→9474. Saved private fixture/package/evidence:
`local-output/sdk-20260909/actor-animation-assignment-20261002/`.
See [initial assignment workflow](legaia-initial-animation-assignment.md).
No game launched or package installed. Manual checks are queued for later;
full SDK/runtime acceptance remains incomplete and the565 checkpoint predates
this feature.

**Shared model/clip reference navigation (2026-10-02):** Asset references
now links the eight supported shared field clips to their five global models in
both Active scene and Project scopes. These are explicit reference-pinned
associations, separate from initial/effective actor assignments. Edges retain
the pinned commit, model/clip identity, decoded counts and full source locator;
strict model provenance, record mapping and bounded metadata checks reject
inconsistent evidence. Missing models remain unresolved. The browser labels
actor playback unknown and supports model-to-clip and clip-to-model navigation.
31 focused retail-enabled Python checks passed in 24.333s; all 33 Node files and 34
syntax checks passed with hashes matched to final source. Fresh Town01/Dolk2/map01
discovery verified all 8 clips and 24 source-qualified edges in 33.826s, exact edge
hashes and untouched project/cache/saved bytes. Actual browser Active/Project
HTTP, three-scene navigation and the auxiliary loop passed with zero page errors
or authoring commands; screenshot inspected. Private evidence:
`local-output/sdk-20260909/shared-clip-references-20261001/`.
No game launched; this read-only feature needs no new gameplay gate. The
565-test checkpoint predates both reference workflows; full SDK/runtime
acceptance remains incomplete.

**Project-wide asset references (2026-10-01):** Asset Details → Inspect
asset references now offers Active scene and Project scopes. Project discovery
freshly verifies all imported scenes and assembles existing decoded relationships
through detached scene/catalog views, preserving project state and caches. Shared
stable IDs retain source memberships separately from navigable catalogs, with
scene-qualified edges and deterministic cross-scene navigation. Coverage exposes
source hashes, partial-catalog limitations and explicit unavailable reasons;
recorded relationships do not establish runtime residency or reachability.
Scope/Close cancellation and stale-source guards prevent late results. Strict
HTTP shapes and bounded graphs/metadata retain the existing active response.
Twenty focused retail-enabled Python tests passed in13.948s; all33 Node files
and34 syntax checks passed with hashes matched to final source. Fresh Town01,
Dolk2 and map01 discovery checked actor/script/dialogue/animation/world-map links,
12 shared-model material edges and exact source hashes; complete project/cache
and saved bytes stayed unchanged. This final retail check took21.566s. Per-call
import-hash reuse produces an identical report to the earlier repeated-hashing
implementation. Actual browser Active/Project HTTP responses, three-scene scope,
source navigation, pending Close and stale-source rejection passed with zero
page errors; screenshot inspected. Private evidence:
`local-output/sdk-20260909/project-asset-references-20261001/`.
No game launched. This read-only feature needs no new gameplay gate. The565
checkpoint predates it; full SDK/runtime acceptance remains incomplete.

**Integrated offline checkpoint (2026-10-01):** Full retail-enabled SDK
regression passed565 Python tests in250.658s (252.001s wall time), exit0 with no
skips, on unchanged clean source `43994eb25f5125da4378f2cb970b311931745bf9`.
All33 Node test files and34 editor syntax checks passed with captured hashes
freshly matched to source. This supersedes548 and includes viewport source-wall
editing, atomic mixed actor/scenery placements and their X/Z handles, saved
scene selections and visible placement rectangle selection, alongside earlier
SDK workflows. User-owned disc identity and466714416-byte length were freshly
verified. Browser and package readback evidence remains separate from this
regression. No game launched; runtime parity, genuine Live identity, gameplay
acceptance and full16-layer SDK completion remain unproven.

Private evidence under `local-output/sdk-20260909/`:
`sdk-regression-20261001-scene-placement.log/.json` and
`node-checks-20261001-scene-placement.json`. Python log SHA256:
`4a52fe3e8f7923fc173298f8c6f38b6fa460193ccf72eb6ced78177ff27a595f`.

**Placement rectangle selection (2026-10-01):** Box select placements now
selects visible imported actor and static-decoration meshes through one
depth-tested renderer ID pass. Drag replaces the selection; Ctrl/Command adds,
and an empty rectangle clears it. Hidden entities/layers, ground, NPC drafts and
placed scenery are excluded. Results are canonical and bounded to128, with
atomic rejection preserving the previous selection. Hierarchy and focused
Inspector stay synchronized; the selection feeds existing mixed placement
review and saved scene selections. Escape, camera, resize and stale source
cancel gestures without a project command. Eleven focused Python checks passed
in3.214s; all33 Node files and34 editor syntax checks passed. Actual2×-DPI
pointer replacement/addition, single-actor focus, empty selection, both layer
filters, cancellation and fresh review handoff passed with zero page errors;
screenshot inspected. Saved bytes/history stayed unchanged. Private evidence:
`local-output/sdk-20260909/scene-placement-box-20261001/`. No game launched.
This selection-only feature introduces no new gameplay gate. Historical548
predates it; the full SDK objective remains incomplete.

**Mixed placement viewport handles (2026-10-01):** Retained Proposed
actor/static-decoration groups now expose X/Z handles. Every drag snaps to a
relative 64-unit offset, holding each displayed height and rotation; release
freshly reviews the full source-bound mixed proposal without a project command.
Current has no handles. Rejected/pending drags keep the prior verified matrices
and inputs; Restore cancels pending review and ignores late responses. Escape,
camera, preview/source/representation changes and resize cancel stale gestures.
Thirty-one focused retail-enabled Python checks passed in 18.361s, all 32 Node
files and 33 syntax checks passed. Actual 2×-DPI top-view X/Z pointer drags,
retained review, rejection, cancellation, Current matrices, Apply/Undo/Redo/Save
and fresh Escape/camera/resize checks passed with zero page errors; screenshots
inspected. Normal two-overlay MAN/MAP package passed exact full73728-byte MAP ZIP
readback and independent actor/grid decode, preserving prior actor/scenery edits,
height/rotation, 17 collision edits, floor tiers and saved selection metadata.
Private evidence: `local-output/sdk-20260909/scene-placement-drag-20261001/`.
No game launched; gameplay remains deferred. Historical548 predates this feature.
See [Mixed placement workflow](legaia-scene-placement-groups.md).

**Saved scene placement selections (2026-10-01):** Named project-local
selections now retain 1–128 imported actors, static decorations or mixed members.
Create/Rename/Replace/Delete use strict source-bound commands and one-step
Undo/Redo. Metadata validation remains portable without a disc; scenery Create,
Replace and Recall freshly verify static MAP identities. Cross-scene Recall seeds
actor, scenery or mixed placement tools without editing game overrides. Changed
reimport is blocked under the library and its history. Thirty-eight focused Python
checks passed in 2.554s, all 32 Node files and 33 syntax checks passed. Actual
Town01/Dolk2 browser Create/Rename/Delete/history, Save/Open, cross-scene mixed
recall, single-decoration replacement/recall/Undo and pending source/recall Cancel
checks passed with zero page errors; screenshot inspected. Private saved-project
copy retains the library; normal package is byte-identical before/after selection
metadata (SHA256 `1503a2fb0aa1c141927efac65285390afa876028bfd7ddc46f44dd70c02302fe`).
Private evidence: `local-output/sdk-20260909/scene-selection-sets-20261001/`.
No game launched. This feature requires no new gameplay gate; it does not establish
runtime placement parity. Historical 548 checkpoint predates it.
See [Saved scene selections](legaia-scene-selections.md).

**Mixed scene placement groups (2026-10-01):** Select scene placements combines
imported actors and static decorations in one bounded selection. Move scene
placement group reviews 2–128 targets, including at least one of each kind, with
common X/Z offsets in 64-unit steps within ±16320. Proposed/Current inspection
retains the review and holds preview height; runtime height remains unknown.
Fresh full-source validation precedes one atomic Apply/Undo/Redo operation across
actor and Environment overrides, preserving unrelated components and edits.
NPC drafts and placed scenery are excluded. Forty-seven focused Python checks
passed (43 in 23.086s, four HTTP checks in 2.912s); all 31 Node files and 32 syntax
checks passed. Actual 2×-DPI retail hierarchy selection, Proposed/Current matrices,
held height/rotation, no-op/input withdrawal, one-step Undo for both owners,
Redo/Save and pending Cancel/late-response withdrawal passed with zero page errors.
Fresh browser representation guards also passed without writes; screenshots inspected.
The normal package contains both MAN and complete 73728-byte MAP overlays: exact ZIP
readback and independent MAN/grid coordinate decoding preserved opaque bytes,
unselected scenery, shared rotations, existing collision edits and floor tiers.
The previous 548-test checkpoint predates this change and remains unchanged.
No game launched. Gameplay remains deferred. See [Mixed placement workflow](legaia-scene-placement-groups.md).

**Viewport source-wall editing (2026-10-01):** Select wall rectangle loads
verified source collision data and picks canonical X/Z cells directly in the
scene. Dragging prepares inclusive bounds without a project command; release
opens the existing review. Proposed/Current/Retail wall layers can be inspected
on the labelled Y=0 reference plane, with retained Return/Restore and explicit
atomic Apply/Undo/Redo, Save/Open and normal Build. Camera/source/representation
changes, Escape and pending cancellation withdraw stale gestures or reviews.
Twenty-one focused retail-enabled Python tests passed in10.570s, all30 Node
files and31 syntax checks passed. Real2×-DPI top/perspective browser drags,
comparison layers, no-op/input withdrawal, cancellation and exact full73728-byte
MAP ZIP readback passed with zero page errors; screenshots inspected.
No game launched. This postdates548; gameplay and full acceptance remain open.
See [Wall rectangle workflow](legaia-collision-rectangles.md).

**Integrated offline checkpoint (2026-10-01):** Full retail-enabled discovery
passed548 Python tests in247.512s, exit0 with no skips, on unchanged clean source
`80d4ae765f820551759f181d8372478a49358b72`. All29 Node test files and30 editor
syntax checks passed with captured file hashes. This supersedes514 and integrates
saved-copy discovery, wall rectangles/spatial comparison, scenery groups/drags,
actor transform preview refresh and scenery alignment/distribution with the
previous SDK workflows. The user-owned disc SHA256 and466714416-byte length were
freshly verified. Browser/package evidence remains separate; no game launched.
Full16-layer SDK, runtime parity, genuine Live identity and gameplay acceptance
remain incomplete. This checkpoint predates the viewport wall workflow above.

Private evidence: `sdk-regression-20261001-scenery-layout.log/.json` and
`node-checks-20261001-scenery-layout.json` under `local-output/sdk-20260909/`.
Python log SHA256:
`a247306827edfc8672e0133478dbf1d0fd83ebf6e24536f014a414b4c153da2a`.

**Scenery alignment and distribution (2026-10-01):** Arrange scenery group
aligns2–128 selected static decorations to an anchor on X/Z or evenly distributes
them between fixed endpoints using integer half-up rounding and stable identity
ordering. Other axes, shared transforms, Y/rotation, outside edits and Collision
are preserved. Fresh review, textured Proposed/Current comparison, retained
Return/Restore, atomic Apply/Undo/Redo, Save/Open and normal Build are connected.
Fifty-three focused retail-enabled Python tests passed in17.726s, all29 Node tests
and30 syntax checks passed. Retail browser alignment/distribution, input withdrawal,
comparison matrices, no-op Apply and pending-close cancellation passed with zero
page errors; screenshots inspected. Complete73728-byte MAP ZIP matches the saved
binding and independently decoded descriptor coordinates. No game launched.
Included in548; runtime visibility/collision/lifecycle remain deferred.
See [Scenery groups](legaia-scenery-groups.md).

**Scenery group drag and actor preview refresh (2026-10-01):** Proposed
scenery inspection now has X/Z handles with integer movement and optional
16/64/256/1024 snapping. Release obtains a fresh source-bound review; Apply
remains one explicit undoable command. Rejected and cancelled pending drags
retain or restore the verified proposal without saving. Canvas focus now prevents
scroll displacement during pointer gestures. Imported actor transforms now
invalidate preview identity while retaining cached geometry, fixing stale actor
positions after edits and resampling source height where Y is unknown.
Forty-five focused retail-enabled Python tests passed in16.686s; all28 Node tests
and29 syntax checks passed. Retail browser group drags, rejection/cancellation,
Apply/Undo/Redo/Save, individual actor/scenery drags and exact full73728-byte MAP
ZIP readback passed with zero page errors; screenshots inspected. No game
launched. Included in548; gameplay/full acceptance remain deferred.
See [Scenery groups](legaia-scenery-groups.md).

**Static scenery group placement (2026-10-01):** Ctrl/Command-click static
decorations in the hierarchy or viewport, or Shift-select a hierarchy range,
then choose Move scenery group. Source-bound review supports2–128 instances,
common integer X/Z offsets, retained Proposed/Current textured scene inspection,
one atomic Apply, Undo/Redo, Save/Open and normal Build. Shared offsets/rotations,
Y, unselected instances, Collision and imported identities remain preserved.
Full merged descriptor capacity, signed range, source/metadata/selection guards
and exact zero-offset no-op behavior are checked. Twenty-one focused retail-
enabled Python tests passed in16.060s, all28 Node tests and29 syntax checks passed.
Retail browser two-wall workflow and full73728-byte ZIP MAP readback passed;
screenshots inspected and zero page errors. No game launched; gameplay deferred.
Postdates integrated514. See [Scenery groups](legaia-scenery-groups.md).

**Spatial wall rectangle comparison (2026-10-01):** Reviewed rectangles now
show all selected bits in a top-down Retail/Current/Proposed comparison with
canonical source X/Z bounds, quadrant placement and proposed-change outlines.
Layer switching is read-only; changed inputs withdraw the map and Apply.
Twenty-two focused retail-enabled Python tests passed in17.122s, including five
new synthetic HTTP contract tests; all27 Node tests and28 syntax checks passed.
A synthetic browser fixture checked16 bits, three layer counts, coordinate
bounds, no extra requests/writes and input withdrawal; zero page errors and
screenshot inspected. This is a source-grid diagram, not a terrain/live viewport.
Postdates integrated514. No game launched. See
[Wall rectangles](legaia-collision-rectangles.md).

**Rectangular source wall editing (2026-10-01):** Collision tools now review
inclusive grid rectangles and apply one atomic wall override, preserving floor
bits, outside edits and unrelated components. Fresh source/review guards, bounds,
merged4096 limit, no-op and Undo/Save/Open support are connected. Seventeen focused
Python checks,27 Node files/28 syntax checks passed. Browser reviewed/applied16
town01 bits, verified history/Save/stale/no-op guards, zero errors and inspected
compact dialog. Normal package ZIP matches the expected complete73728-byte MAP
with floor tiers preserved. No game launched; runtime collision paints/gameplay
remain deferred. Postdates514. See [Wall rectangles](legaia-collision-rectangles.md).

**Saved editable copy discovery (2026-10-01):** Copy project now lists bounded
project-local creation records after restart, shows current saved names/metadata
changes, labels partial records and reopens through normal validation and the
dirty-source guard. Listing does not claim current input integrity. Twenty-eight
focused Python checks,26 Node files/27 syntax checks passed. Browser verifies
three states, corrupted-import rejection, dirty guard, reopened Dolk2 X9536,
pending-close withdrawal and Refresh with unchanged source bytes, zero errors
and inspected screenshots. No game launched; postdates514. See
[Project copies](legaia-project-copies.md).

**Latest integrated offline checkpoint (2026-10-01):** Retail-enabled discovery
passed **514 Python tests in 365.743 seconds**, exit0, no skips, on unchanged
clean source `7a6459e4e29ad96f858d2a8c79eab25dabbc60f2`. All26 Node test files
and27 editor syntax checks passed on that same source. This supersedes498 and
includes saved Build comparison, raw MAN normal Build and editable project copies.
The private retail disc SHA256 and466714416-byte length matched the expected
source. No game launched. Browser/rendered evidence remains separate; runtime
parity, genuine Live identity, gameplay and the full16-layer plan remain open.
Private logs: `sdk-regression-20261001-project-copy.log/.json` and
`node-checks-20261001-project-copy.json` under `local-output/sdk-20260909/`.
Python log SHA256: `cde485238587c1200c630c4cc6306f4cbf35d7ecdb4892458df9f02b1dfe7434`.

**Editable project copies (2026-10-01):** Copy project captures unsaved authoring
inputs into a fresh project-local folder, including referenced TIM/TMD files,
drafts, templates and saved views/selections. Hash readback, normal reopen and
source drift checks precede the completion report. Source files, dirty state and
Undo history are preserved; Open copy requires Save/Undo first when dirty.
Thirty-nine focused Python checks, all26 Node files and27 syntax checks passed.
Browser verified unsaved Dolk2 X9536, independent copy Save at X9600 and original
X9472 recovery with unchanged source bytes and zero errors; screenshots inspected.
No game launched. Postdates integrated498. See [Project copies](legaia-project-copies.md).

**Normal Build for raw streamed MAN (2026-10-01):** The typed source handoff now
routes raw MAN through existing audited placement/header/script composition,
preserving size, structural chunks, record layout and opaque bytes. Raw output is
explicitly uncompressed; raw validation and LZS round trips remain distinct.
Dolk2 placement, donor appearance, dialogue, P2 transition and flag changes
compose with a separate raw ANM bank. Twenty-seven retail-enabled Python checks,
25 Node files and26 syntax checks passed. Browser Review Build/Build agreed on
ten mixed Town01/Dolk2 changes, two overlays/68,930 bytes; authored/persisted data
unchanged, zero errors, screenshot inspected. No game launched; NPC drafts still
block normal Build. Postdates integrated498. See [Raw MAN Build](legaia-raw-MAN-normal-build.md).

**Saved Build audit comparison (2026-10-01):** Build history verifies two saved
packages and compares exact audit identities/records, including animation frame/
object and detailed deltas. Missing records do not imply deletion or runtime values.
Different retail sources, ambiguous identities, corruption and stale context reject.
Fifteen focused retail-enabled Python checks, all 25 Node files and 26 syntax checks
passed. Browser compared one changed Town01 record with eight identical records,
blocked identical IDs, rejected/restored corrupt bytes, and preserved all authored/
saved metadata with zero errors. Corrected spacing/status labels; final screenshot
inspected. No game launched. Postdates integrated 498. See
[Build comparison](legaia-build-comparison.md).

**Historical integrated SDK checkpoint after Build-history correction (2026-10-01):**
Retail-enabled discovery passed **498 Python tests in 368.664 seconds**,
exit0, no skips, on unchanged clean source `ba77695b6e4e86210a2d921e1e5d9935c706e611`.
All24 Node test files and26 editor module syntax checks passed on that source.
This supersedes the passing475 checkpoint and includes Project Settings,
dependency/material/effective-animation references, Build review, saved Build
history and its no-op package compatibility correction. The initial497-test
run at e49e09b0 failed four equality checks and one guard-order check; its evidence
is retained, and the unchanged regressions now pass in full discovery.
The user-owned disc SHA256 and466714416-byte length matched the expected source.
No game launched. Browser/package/rendered evidence remains separate, and native
runtime parity, genuine Live identity, gameplay and the full16-layer plan remain
incomplete. Private evidence: `sdk-regression-20261001-build-history-fixed.log/.json`
and `node-checks-20261001-build-history-fixed.json` under `local-output/sdk-20260909/`.
Log SHA256: `dd9141e0657fce546357327f9750709553de66284299018ba7353a218761ac28`.


**Build-history compatibility correction (2026-10-01):** Integrated discovery
at e49e09b0 ran497 tests but found four no-op package-equality failures and one
stale-source guard-order error. Content-derived package identity is restored;
separate immutable input receipts retain distinct authored snapshots. All29
focused regression checks passed, plus six history checks including conflicting
input-receipt rejection. The failed run is retained as evidence, not presented
as integrated acceptance. The integrated result above verifies this correction.

**Saved normal Build history (2026-10-01):** Successful Builds retain deterministic
completion receipts; Build history reopens reports after server restart. Input
match, package integrity and gameplay status remain separate. Verify saved files
checks receipt/audit/manifest, package payloads and exact ZIP contents. Older
folders without receipts show unavailable input match/integrity. Bounded scans
and path guards reject invalid coverage or redirected files. Nineteen focused
retail-enabled Python checks, all24 Node files and26 syntax checks passed.
Fresh-server browser reopened a real nine-change report and verified the package;
legacy labels/malformed request rejection passed, authored/persisted data unchanged,
zero page errors. Corrected clipped report columns and inspected the final view.
Postdates integrated475; no game launched. See [Build history](legaia-build-history.md).


**Read-only normal Build review (2026-10-01):** Review Build reuses the actual
serializer and manifest/file guards on detached authored inputs without creating
outputs. Retained NPC drafts remain explicit blockers; existing overrides are
assessed with the exclusion clearly recorded. Ready reviews can dispatch a Build
with browser/server input-identity guards. Five retail-enabled Python checks,
all23 Node files and25 syntax checks passed. Review audit/manifest/report matched
actual Build; normal raw/compressed animation packaging still passed. Browser
proved four retained draft blockers, nine existing changes, no review outputs,
stale dispatch rejection, Undo restoration and matching package creation in a
separate no-draft fixture. Zero page errors; saved metadata/authored content
unchanged; screenshots inspected; no game launched. Postdates integrated475.
See [Build review](legaia-build-review.md).

**Effective animation references and imported material reuse (2026-10-01):**
Actor reference views now distinguish initial retail clip bindings, effective
bindings from exact verified appearance donors, and authored draft donor clips.
Appearance donor relationships also navigate to imported actors. Missing bindings
remain unknown; equal counts do not create new combinations. Asset Database
material metadata is bounded to two eight-MiB entries, keyed by imported source,
scene, path and decoder version. Queries still verify retail sources before reuse
and assemble current authored relationships separately. Cache data is copied,
never persisted, and contains no pixels. Twenty focused retail-enabled Python
checks, all22 Node files and24 syntax checks passed; repeated retail query reused
material metadata while still verifying source. Browser proved separate retail/
effective links after one donor assignment, authored draft clips, current review
keys and Undo restoration; persisted metadata unchanged, zero page errors.
Screenshot inspected. Postdates integrated475; no game launched. See
[Effective animation relationships](legaia-effective-animation-references.md).

**Imported material source navigation (2026-10-01):** Model Dependencies and
texture Referenced by now include successful static UV/texture-page/CLUT address
matches with source hashes and material indexes. Missing/conflicting/unsupported
materials remain explicit diagnostics; shared and boot sources outside the active
navigable catalog remain disabled. Metadata has no pixel payloads. Relationships
describe candidate word providers, not unique upload ownership or runtime material
use; authored replacements remain separate. Twenty-three retail-enabled Python
tests, all22 Node files and24 syntax checks passed. Retail browser showed three
Dolk2 material groups linking to TIM69/0/19, opened its provenance and verified
the reverse texture Referenced by view, with zero
errors/authoring commands and unchanged authored content/history. Screenshot
inspected. Postdates integrated475; no game launched. See [Material references](legaia-material-references.md).

**Asset reference navigation (2026-10-01):** Asset Details exposes Dependencies
and Referenced by for verified imported membership/model assignments and active
script, dialogue, animation, field-table and landmark source relationships.
Authored draft donors and effective model assignments retain separate evidence
layers; unavailable destination scenes cannot be navigated. Runtime use,
script model pools, trigger dispatch and live animation state remain
unresolved. Fourteen focused Python checks, all22 Node test files and24 module
syntax checks passed. Browser verified actor/script and cross-scene navigation, stale-view rejection,
closed-request withdrawal, unchanged authored content/history and zero errors
or authoring commands; screenshot inspected. This feature postdates integrated475; full SDK/runtime
acceptance remains incomplete. See [Asset references](legaia-asset-references.md).

**Project settings inspector (2026-10-01):** Settings now uses SDK
property/action metadata for name, folder, retail source identity, scene count,
active scene and mode. Source/path values remain read-only. A validated rename
command supports dirty tracking, one Undo/Redo, Save/Open, no-op and stale-name
rejection without modifying imported content or authored assets. Browser proved
one quoted Unicode rename, persistence/history, stale-form withdrawal and zero
page errors; screenshot inspected and baseline restored. Independent reopen
retained four drafts and normal no-draft builds preserved every game-data
payload. The Unicode probe exposed invalid surrogate escapes in package TOML;
manifest names now emit literal UTF-8 with valid escaping. Fourteen focused
Python checks, all21 Node files and23 syntax checks passed. No game launched;
checks postdate integrated475. See [Project settings](legaia-project-settings.md).

**Latest integrated offline checkpoint (2026-10-01):** Retail-enabled
Python discovery passed **475 tests in 279.577 seconds**, exit0, no skips, on
unchanged clean committed source `9084e5454bd8e191f4f4b03e01f4c82497564619`.
All **20 Node test files** and **22 editor module syntax checks** passed on that
source. This supersedes the469-test checkpoint and includes script operand files
and atomic scene bundles, all12 catalog inspector types, bare scene URI search,
reviewed animation interpolation, and normal raw/compressed animation Build.
The final browser additionally verified observed authored-state changes withdraw
both interpolation Apply and review; baseline restored with zero page errors.
Independent user-owned disc SHA256 and466714416-byte length matched prior input.
No game launched. Native runtime parity, confirmed Live actor identity, gameplay
and the complete16-layer acceptance plan remain incomplete. Private metadata:
`local-output/sdk-20260909/sdk-regression-20261001-animation-build.log/.json`;
Node/syntax source hashes and results:
`local-output/sdk-20260909/node-checks-20261001-animation-build.json`.
Log SHA256: `2ceab6a68dee7a3088ff6faac10b73310931e1917b16cc0c4dcc206c4239791e`.

**Reviewed animation interpolation and raw ANM Build (2026-10-01):**
The animation channel editor now blends a copied verified pose into the selected
effective pose across an existing frame range. Read-only review precedes one
Undo/Redo command; unrelated channels remain. Translation rounds to integers and
per-axis shortest-path rotation to16-unit PSX increments, with explicit tie rules.
Actual retail verification exposed normal Build assuming all ANM banks were
compressed. Normal Build now reuses the source-preserving patch service for raw
and compressed banks with preimage/carrier checks. Thirteen focused Python
checks passed with retail input, including both normal Build layouts and existing
streaming composition; all20 Node files and22 editor syntax checks passed.
Retail browser passed review, stale-range rejection, Apply/Save/Undo/Redo and zero
errors. Independent reopened package matched all114764 bank bytes, preserved
other payloads and four drafts. Screenshots inspected; baseline restored.
No game launched or disc installed. Gameplay remains deferred; this postdates
integrated469. See [animation interpolation](legaia-animation-interpolation.md).

**Asset navigation inspectors (2026-10-01):** Actors, imported scenes,
actor presets and world-map landmarks now use the shared SDK read-only property
and registered-action contract, bringing supported catalog inspector types to12.
Navigation retains original source and authored provenance; landmarks expose
menu coordinates and discovery indices without claiming live state or gameplay
reachability. Source/catalog/schema/capability, busy and closed guards apply.
Fixed bare `scene://` searches being misread as `scene:` filters; explicit field
filters remain supported. Eleven focused Python checks, all19 Node test files
and21 editor syntax checks passed. Retail browser verified all four new panels,
actor selection, cross-scene navigation, preset library and landmark menu/source
catalog navigation, zero author commands/errors and unchanged authored state.
Screenshot inspected. Private evidence:
`local-output/sdk-20260909/navigation-inspectors-20261001/`.
No game launched. These checks postdate the integrated469 checkpoint; gameplay
and the full SDK objective remain incomplete.

**Scene script operand bundles (2026-10-01):** The asset tools now export
and review authored numeric operands across actors and partition-two script
owners in the active scene. All owners stage before one atomic Apply/Undo/Redo;
actual shared-byte conflicts, invalid owners and changed review contexts reject.
Five focused Python checks, all 19 Node test files and 21 editor syntax checks
passed. Retail browser verified two owners/four entries, export, read-only review,
Save/Undo/Redo, invalid/stale/closed guards and zero page errors. Independent
reopen retained four drafts; detached no-draft normal builds changed only MAN
bytes 4808/4811/4816/28557, with all other content payloads unchanged. Screenshot
inspected and baseline restored. No game launched or disc installed; gameplay
remains deferred. This postdates the integrated 469-test checkpoint. See
[scene operand bundles](legaia-script-operand-bundles.md).

**Script file review refinement (2026-10-01):** File controls now bind to
the script owner's authored-state snapshot. An owner edit observed during review
withdraws Apply in the UI; the server's existing stale-key rejection remains.
Reviews show a readable operand/instruction/current/proposed table, with complete
source-bound details collapsed. All 18 Node checks and 20 editor syntax checks
passed. Final retail browser checked one-command flag/model-selector/move imports,
actual partition-two asset-to-script navigation, P2 Apply/Save/Undo/Redo, stale
review withdrawal and a closed pending response, zero page errors. Baseline
restored; screenshot inspected. Independent Save/Open retained four drafts.
Detached no-draft builds matched the complete 45338-byte MAN: mixed actor edits
changed only4808/4811/4816; the P2 flag changed only28557. Raw record-table/opcode
checks established offsets independently; every other content payload was
unchanged. Private evidence:
`local-output/sdk-20260909/script-operand-files-advanced-20261001/`.
No game launched or disc installed. Gameplay remains deferred; these checks
postdate the integrated469-test checkpoint.

**Script operand JSON workflow (2026-10-01):** The script inspector now
exports authored movement, flag, wait, model-selector and transition operand
metadata. A bounded source/owner-bound file review stages every entry through
existing verified commands; one atomic Apply supports Undo/Redo and Save/Open.
Supplied entries replace their authored fields; other entries/components remain.
Duplicate/nonfinite/extra/oversized files, wrong source/owner and stale reviews
reject without partial edits. No instruction bytes, dialogue, control-flow layout
or runtime state are transferred. Nineteen focused Python checks, all 18 Node
checks and 20 editor syntax checks passed. Retail browser verified export,
read-only review, Apply/Save/Undo/Redo, wrong-owner rejection and restored baseline,
zero page errors. Screenshot inspected. Independent reopen retained all four
NPC drafts; a detached no-draft normal Build matched the complete 45338-byte MAN
with only offset4811 changed for owner0003's selector240→239. Other content
payloads were unchanged. Package SHA256:
`e440d265be2a20a7008801e89c60eb1de8adc586ef3cac470e6ad22dc4aad53e`.
Normal Build still rejects drafts. Private evidence:
`local-output/sdk-20260909/script-operand-files-20261001/`. This postdates the
469-test integrated checkpoint; execution/gameplay remains deferred. No game
launched or disc installed. See [operand files](legaia-script-operand-files.md).

**Previous integrated offline checkpoint (2026-10-01):** Retail-enabled
Python discovery passed **469 tests in 176.301 seconds**, exit 0, no skips, on
unchanged clean committed source `d948b2a0f27e77c2b60f17b490ca7d8878389646`.
All **17 Node checks** and **19 editor module syntax checks** passed on that
source. This supersedes the 463-test checkpoint and includes asset field search,
atomic group preset Apply, detached group scene inspection and SDK asset inspector
tools. The user-owned disc SHA256 and 466714416-byte length were independently
verified. Existing browser, package and saved-project evidence remains separate;
this does not prove native runtime parity, Live actor identity, gameplay or all
16 acceptance layers. No game launched. Private command/source/result metadata:
`local-output/sdk-20260909/sdk-regression-20261001-asset-inspectors.log/.json`;
Node/syntax file hashes and results:
`local-output/sdk-20260909/node-checks-20261001-asset-inspectors.json`.
Log SHA256: `eed72436dcc91f0631446e3786abeb42a58964fa8e8bfd967c68a33967da7de4`.

**SDK asset inspector tools (2026-10-01):** Asset Details now uses the
same SDK property/action contract as actor inspectors for eight catalog types:
models, textures, animations, scripts, dialogue, collision, triggers and regions.
SDK metadata supplies labels, read-only stable identity/source properties and
capability-bound tools; explicit type-specific handlers open the existing
verified workspaces. Details is now a consistent entry point, while asset-card
shortcuts remain. Changed source/catalog record/schema/capability, busy state and
closed dialogs block dispatch. Duplicate authored-open buttons are removed for
these types; authored details and source provenance remain separate. These are
inspector tool groups, not invented or persisted entity components. Eleven
focused Python checks, all 17 Node checks and 19 editor syntax checks passed.
Retail browser opened all eight Details panels through actual browser buttons,
loaded model/texture previews and opened the resource tools; busy/closed guards,
unchanged actors, zero author commands and zero page errors passed. Screenshot
inspected. Evidence: `local-output/sdk-20260909/asset-inspector-20261001/`.
This postdates the integrated 463-test checkpoint. Specialized editing forms,
other asset types, runtime identity and gameplay still need further work.
No game launched.

**Group preset scene inspection (2026-10-01):** The extension adds read-only Current/Proposed comparison in the assembled
3D scene for position, appearance and combined group presets. Return retains the
review for atomic Apply; Restore, changed selection and a closed pending request
discard it. Preview preserves the camera and unknown guest Y, and writes no
actor components. Markers and framing now use the active proposal's display
coordinates, matching its rendered meshes. Twelve focused Python checks, all 16 Node checks and 18 editor module syntax
checks passed. The final scene screenshot was inspected. All three scopes also passed the production
decoder against freshly verified retail-source scene responses. The retail browser
checked two changed actors, Current/Proposed/Return, Restore, late-response and
selection guards, Apply/Save/Undo/Redo, matching marker coordinates and unchanged
camera, with zero page errors. Independent normal Build readback matched the
entire 45338-byte MAN with only five expected donor/position bytes changed; all
other package payloads were preserved. Normal Build proof used a detached view
without drafts; projects containing drafts remain rejected. Private evidence:
`local-output/sdk-20260909/preset-batch-scene-20261001/`. These changes postdate
the integrated 463-test checkpoint. Gameplay and
runtime parity remain pending; no game was launched.

**Actor group presets (2026-10-01):** Position, appearance and combined
presets now review all 2–128 selected imported actors before one atomic Apply /
Undo/Redo command. Fresh source/target/donor compatibility, canonical membership,
stale-key rejection and no-op groups reuse existing commands on a detached
staging view. Absolute axes and possible overlaps are explicit; unrelated data
and unknown Y remain preserved. Eleven focused Python tests, all 15 Node checks
and 18 editor syntax checks passed. Retail browser group review/Apply/Save/Undo/
Redo passed without preview writes or page errors; screenshot inspected.
Independent Save/Open retained all four NPC drafts. A detached no-draft normal
Build package matched the complete 45338-byte town01 MAN with exactly target 0012
X changed from 3008 to 2944 at offset 8498. Package SHA256:
`a59e32eaf00f07971a0f36eb83ff10529eea908d34dd98404f07042bc6cf6567`.
Normal Build still rejects drafts; no game launched or disc installed. This
postdates the 463-test checkpoint; gameplay remains deferred. See
[group presets](legaia-actor-group-presets.md).

**Asset browser field search (2026-10-01):** Search now supports name,
stable ID, type, scene, model reference, recorded confidence and provenance
filters, quoted phrases and exclusions. Unknown fields and malformed/oversized
queries show errors without broadening results. Existing category and resource
scope remain; recorded confidence and model matches do not establish aggregate
certainty or runtime use. All 14 Node checks and 17 editor syntax checks passed.
Retail-source browser verified field combinations, imported/authored model users
against the SDK reference graph, phrases/exclusions, provenance, URI IDs, errors,
reset and actor navigation without authoring commands or actor changes, zero
errors. Screenshots inspected; narrow-panel controls now wrap. This postdates
the 463-test checkpoint. No game launched. See [asset search](legaia-asset-search.md).

**Historical integrated offline checkpoint (2026-10-01, 463 tests):** The retail-enabled SDK
Python discovery suite passed **463 tests in 264.543 seconds**, exit 0, no skips,
on unchanged committed source `2ca0a1a4fa0044f55e9b0dc6d6c217b9e061f578`.
This supersedes the 457-test checkpoint and includes the later SDK animation/preset
inspector actions and saved scene views. All **13 Node checks** and **16 editor
module syntax checks** passed separately on the same source. The disc SHA-256
was independently verified against the recorded retail source. Browser, package,
saved-project and rendered acceptance retain their separate evidence; this suite
does not establish native runtime parity, Live actor identity or deferred gameplay.
No game was launched. Private command/source/result metadata and log:
`local-output/sdk-20260909/sdk-regression-20261001-scene-views.log/.json`;
Node/syntax hashes/results: `local-output/sdk-20260909/node-checks-20261001-scene-views.json`.
Log SHA-256: `5509fa89b90dd8f040c80c33bc7f75cb02cd7cf0e38ac100361772f009d16111`.

**Saved scene views (2026-10-01):** Named project-local camera bookmarks
retain projection, target/orbit/distance, authored/retail representation and scene
layers, bound to the imported scene hash. Recall supports cross-scene navigation
without actor edits or a history command; metadata create/rename/update/delete
support Undo/Redo and Save/Open. Stale source/review, invalid cameras and changed
source beneath saved views/history reject. Live and active proposal inspections
disable capture/recall. Camera targets are editor display coordinates, not proof
of retail height or runtime identity. Fourteen focused Python/HTTP checks and
Node validation/syntax passed. Retail-source browser checked exact display
recall, cross-scene navigation, rename/delete/Undo and unchanged actors, zero
page errors; screenshot inspected and button wrapping corrected. This postdates
the 457-test checkpoint. No game launched. See
[saved scene views](legaia-saved-scene-views.md).

**Historical runtime review comparison (2026-09-30):** Saved node reviews
now support a baseline/comparison table, coordinate sample differences, status
and text filters, complete decoded evidence, return navigation and metadata
export. Declared scene/epoch/profile mismatches reject; matching node keys remain
unconfirmed because v1 has no process or object-lifetime identity. Missing axes
and numeric overflow retain unknown deltas; file-only keys do not imply spawning
or removal. Node checks and synthetic browser comparison/filter/download/return,
context rejection and closed-read withdrawal passed, zero page errors or authoring
requests. Project/camera/runtime state was unchanged. Screenshot inspected. This
postdates the 441-test checkpoint; no real runtime capture or game launch occurred.
See [saved runtime reviews](legaia-runtime-node-review.md).

**SDK animation and preset actions (2026-09-30):** Four more actor tools
now consume SDK action descriptors and registered handlers: imported scene
animation preview, Edit-only channel authoring, eligible reference animation
preview and the preset library. The SDK supplies reference-clip eligibility as
detached view metadata without modifying imported components. Unsupported actions
are omitted; source/selection/busy/Edit guards remain in dispatch. Eight focused
Python/HTTP checks and Node action eligibility checks passed. Retail-source
browser opened all four existing tools, checked unsupported/busy guards and
confirmed no actor changes or authoring commands, zero errors; screenshot
inspected. Specialized tool forms and asset actions still use their existing
adapters. This postdates the457-test checkpoint. No game launched. See
[inspector contract](legaia-inspector-schema.md).

**Historical integrated offline checkpoint (2026-09-30, 457 tests):** The retail-enabled SDK
Python discovery suite passed **457 tests in 178.185 seconds**, exit0, no skips,
against unchanged committed source `3c8d8f46af7063f2993d49fe74ec02e6a0005639`.
This supersedes the 441-test checkpoint and includes the later draft repetition,
project transition discovery, SDK inspector services, combined actor preset
review/projection and preset file transfer/source protection. All12 Node checks
and10 module syntax checks passed separately on the same source, including the
inspector registry, model-user selection, historical review comparison and
combined preset scene guards. Browser, package, saved-project and rendered
acceptance retain their independent evidence. This does not establish native
runtime parity, real Live actor identity or deferred gameplay. No game launched.
Private command/source/result/hash metadata and log:
`local-output/sdk-20260909/sdk-regression-20260930-preset-files.log/.json`;
Node/syntax metadata: `local-output/sdk-20260909/node-checks-20260930-preset-files.json`.
Log SHA256: `d5095cd0f752881ce0fcd7212c6cfa09e5361719362b62356c20906759734732`.

**Actor preset file transfer (2026-09-30):** Position, appearance and
combined presets can export metadata-only JSON and import into a project with
the same freshly verified source import. Name/source/donor/schema review precedes
one independent library entry and Undo/Redo; actors remain unchanged. Duplicate
names, changed sources, stale reviews, extra/payload fields and bounded JSON
reject. Saved preset libraries now block changed-source reimport after reopen.
Nineteen focused Python/HTTP checks and retail-source browser export/review/import/history,
no-preview writes, size/closed-response rejection passed, zero errors; screenshot
inspected. Independent cross-project retail Save/reopen/re-export passed with
preserved components/hash and no actor/import edits. This postdates the 441-test
checkpoint. No game launched. See [preset files](legaia-actor-preset-files.md).

**Combined preset scene comparison (2026-09-30):** The combined preset
review can now inspect proposed position and initial donor appearance together
in the assembled scene. A freshly verified detached project projection preserves
current overrides/history. Proposed/Current retains the camera; Return reopens
the review for one Apply/Undo, while Restore discards the retained dialog.
Placement/display/matrix/authored-layer and donor/owner/unrelated-geometry checks
bind the scene response. Scene components, preset or selection changes withdraw
it, and scene export requires restoration. Fourteen focused Python tests and Node
preset/appearance projection checks passed. Retail-source browser comparison,
no-preview writes, camera, Return/Apply/Undo, Restore, closed delayed-response withdrawal and stale-target rejection
passed with zero page errors; screenshot inspected. This postdates the 441-test
checkpoint. No game launched; gameplay remains deferred. See
[combined actor presets](legaia-combined-actor-presets.md).

**Combined actor presets (2026-09-30):** Authored templates can capture
position axes and a verified appearance donor together. A source/target-bound
read-only review shows imported/authored/effective/proposed positions and donor;
Apply updates both components atomically in one Undo/Redo entry, retaining other
axes/components. Thirteen focused tests and retail browser capture/review/history/
Save/reload/stale rejection passed; screenshot inspected, zero page errors.
Independent disk reopen retained the preset and target edits. A detached no-draft
Build view matched every expected MAN byte, retaining earlier menus, selector,
placements and appearances; package SHA256:
`a59e32eaf00f07971a0f36eb83ff10529eea908d34dd98404f07042bc6cf6567`.
Normal Build rejects projects containing NPC drafts. Full experimental archive
readback also retained all four drafts and preset edits, SHA256:
`2f9437b5a0eda2ed4ae9eaf8bf810a6f2f9c0936942e1caae8c3c0a818e43381`.
No disc installed or game launched. Gameplay remains deferred; this feature
postdates the441-test checkpoint. See [combined actor presets](legaia-combined-actor-presets.md).

**Select effective model users (2026-09-30):** Model asset details now offer
scene-qualified selection of2–128 effective imported actor users for the existing
viewport/group tools. Retail-only assignments and NPC drafts remain separate.
Fresh SDK references, scene owners and effective assets are checked before
selection; changed or ambiguous usage rejects. No component/history command is
issued by selection. Node checks and retail browser exact membership for model0112
(actors0005/0011/0012), Dolk2-to-town01 navigation and stale-review rejection
passed, zero page errors. Screenshot inspected. A footer obstruction found during
the cross-scene check was fixed by reserving asset-list space and scrolling the
library tools. These are initial assignments; runtime script replacements remain
unobserved. No game launched. See [model-user selection](legaia-model-user-selection.md).

**SDK-driven component inspector (2026-09-30):** Project state now exposes
a versioned property contract for Transform, ModelRenderer, Animation,
ActorAppearance, RuntimeCorrelation and RetailMetadata. The editor consumes it
for layered number/reference controls, read-only properties and evidence details;
unregistered components receive escaped read-only SDK details. Transform commands
use a bounded registry adapter and ordinary ProjectService validation/history.
SDK authoring limits remain distinct from retail Build encoding, with unresolved
retail Y and project-only authored height explicit. Busy/Edit/selection/source
checks guard controls. Nine focused Python tests and Node renderer/command/
fallback/layer/detail checks passed. Retail browser X edit/Undo and project-only Y Build
issues passed, zero page errors. Retail layered appearance Clear/Undo preserved
imported/effective pairs; runtime unconfirmed state and provenance details passed,
zero errors, screenshot inspected. Six donor/model/script/candidate action buttons
now consume SDK action metadata and registered handlers, with capability/condition
filtering and Edit/busy/stale dispatch guards. Retail registered Clear/Undo and
loaded source-script inspection passed. Specialized forms, animation/template
actions and asset inspectors retain existing adapters; migration is incomplete.
This feature postdates the441-test checkpoint. No game launched. See
[inspector property contract](legaia-inspector-schema.md).

**Project-wide transitions (2026-09-30):** Project transitions now merges
source-qualified decoded scene-change references across1–64 imported scenes,
with separate source coverage, unavailable reasons and imported destinations.
Inspect source script navigates across scenes to its instruction; imported
destinations retain the existing scene navigation. Imported/authored/effective
entry operands remain separate. Five focused tests passed, including self-edge,
merged identity, unavailable source, no-write and stale-state checks. Retail
HTTP/browser discovery found3 references across town01/Dolk2,180 scripts,
88 partial,0 unavailable; cross-scene source navigation and strict request shape
passed with zero page errors. Screenshot inspected. This feature postdates the
441-test checkpoint. These references do not establish reachable gameplay routes,
complete exits or runtime scene connections. No game launched. See
[project transition guide](legaia-project-transitions.md).

**NPC draft repetition (2026-09-30):** Repeat draft previews a named series
of donor-bound NPC copies with a count and X/Z grid spacing. Proposed/Current
scene comparison and Return retain the review; Apply adds the copies in one
Undo/Redo entry. Eleven focused Python tests and Node projection checks passed.
Retail-source browser checks confirmed three copies at X2944/3008/3072, Z5440,
unchanged existing scene/assets, preserved donor pairs, no preview writes,
retained camera, Apply/Undo/Redo, Save/reload, atomic bounds and stale-source
rejection, and zero page errors. Screenshot inspected; independent disk reopen
retained all four drafts. Independent experimental PROT reopen decoded the final
MAN and verified four appended records' exact positions, initial model105 /
animation13 and script bytes equal to donor0011. Archive SHA256:
`b386fb186853a10e445030c3b7f3dc09d2dde1d3faa817acdc6fb6b7f711b262`.
This feature **postdates the 441-test integrated checkpoint**. Normal Build
rejects projects containing NPC drafts; experimental export retains its existing gates. Runtime spawning,
scheduling, collision and visibility remain unverified. No disc installed or game
launched. See [NPC repetition guide](legaia-npc-draft-repetition.md). Private
browser/disk/archive evidence: `local-output/sdk-20260909/draft-repeat-20260930/`.

**Historical integrated source checkpoint (2026-09-30, 441 tests):** the retail-enabled SDK discovery
suite passed **441 Python tests in 177.315 seconds**, exit0, no skips, against
unchanged committed source `e76b05fb1775802057e41c33a5a1e4e36301a093`. This includes
group donor appearance and its detached scene projection, actor alignment/
distribution, saved actor selections and all prior Python SDK services. It
supersedes the425-test source checkpoint below. All eight Node checks (font,
texture usage, script operands, rectangle picking, saved runtime review, actor
group scene/selection, group appearance scene and saved actor selection recall)
and five editor/renderer/group module syntax checks passed separately on the same
unchanged source. Browser/package/disk/rendered evidence remains independent;
this checkpoint does not establish deferred gameplay or native runtime parity.
No game launched. Private exact-command/source/result/hash metadata and log:
`local-output/sdk-20260909/sdk-regression-20260930-saved-selections.log/.json`.
Node evidence: `local-output/sdk-20260909/node-checks-20260930-saved-selections.json`.
Log SHA256: `d095c9718e9cb0269f99a5eeccf1f05b265051dee98984abdee197af6decbed2`.

**Saved actor selections (2026-09-30):** the viewport tool row now saves named
source-bound imported actor groups for later editing. Create, Rename, Replace
members and Delete use project commands/Undo/Redo; Save/Open retains UUID identity,
scene import hash and sorted actor IDs. Recall can navigate to another imported
scene and seed the existing placement/appearance/component tools. It changes no
actor component or command history. Stale reviews reject and refresh displayed
state; changed imports are blocked under selections or their history. Fifteen
focused Python tests passed in1.318s, plus Node recall binding checks. Retail
browser create/rename/history/member replacement/delete/Save/reload, Dolk2-to-town01
recall, placement-dialog seeding and stale rename checks passed, zero page errors.
A clipped Recall button found in the first browser run was fixed with a wrapping
dialog layout; final screenshot inspected. Independent retail disk reopen verified
saved membership/import identity and unchanged build/scene input keys. These are
editor selections, not game parenting/prefabs. No gameplay check is required for
selection metadata; authored game edits retain their existing deferred checks.
Its Python services are included in the441-test checkpoint above. No game launched.

**Actor group alignment/distribution (2026-09-30):** **Actor group placements**
now offers Align X/Z to a selected anchor and Distribute along X/Z, alongside
offsets. Alignment preserves its anchor; distribution preserves coordinate
endpoints and sorts ties by stable source ID. Interior coordinates round to the
nearest retail64-unit grid (ties upward), with adjacent gaps differing by at most
64. Insufficient span rejects before mutation. Retail/Authored/Effective/Proposed
review, no-write scene comparison/Return/Restore, atomic Apply/Undo, Save/Open and
existing Build serialization are connected. Only changed axis values are authored;
height, facing, source and unrelated components remain unchanged. Ten focused
Python tests, existing Node group checks and two retail browser workflows passed;
zero page errors. Town01 actor0013 distribution Z changed2880 to3648 while endpoint
actors0012/0011 remained1856/5440. Independent ZIP/LZS MAN readback matched every
expected byte, retaining donor assignments, earlier placements, three menus and
selector240. Screenshots inspected. No game launched or package installed; the
441-test full checkpoint includes its Python services. See
[group placement guide](legaia-actor-group-offset.md). Gameplay remains deferred.

**Actor group appearance scene comparison (2026-09-30):** reviewed donor
assignments now offer **Inspect group appearance in scene** before Apply.
A detached SDK projection resolves the verified initial model/animation pair at
both actors' existing placements. Proposed/Current switches preserve the camera;
Return retains the donor review, Restore discards the comparison, and export
requires restoration. Source or placement/group changes withdraw the comparison;
closed delayed responses cannot attach. Seventeen focused retail-enabled Python
tests passed in 7.010s, no skips; the new Node projection checks passed. Town01
actor0011/0012 browser comparison verified changed geometry, unchanged positions,
transforms and unrelated geometry/texture content, no inspection writes, retained
Return/Apply/Undo, Restore, source withdrawal and delayed-response discard. Zero
page errors; comparison screenshots inspected. Shared pose geometry may identify
a different first source actor after deduplication; only that attribution is
ignored when comparing unaffected geometry, retaining model/animation evidence.
No game launched or package installed. This feature postdates the425-test full
checkpoint; its Python services are now included in441. Private evidence: `local-output/sdk-20260909/group-appearance-scene-20260930/`.

**Actor group donor appearance (2026-09-30):** selected imported actors now
share a donor-backed initial model/animation assignment through Group appearance.
Discovery intersects freshly verified compatible pairs across every actor; source,
object-count and initial-animation restrictions remain explicit. Preview separates
Retail/Authored/Effective/Proposed data without writes. Apply revalidates the whole
group before one command/Undo entry, preserving other components. Sixteen focused
retail-enabled tests passed in 7.005s, no skips. Town01 actor0011/0012 had12 common
donors; browser discovery/preview/Apply/Undo/Redo/Save and stale last-member rejection
passed, zero page errors. Actor0001/0002 correctly had no supported pair. Screenshot
inspected. Independent saved-project/package MAN readback matched exact donor
assignments and retained positions, three menus and selector240. No game launched
or package installed. Its Python services are included in the441-test full checkpoint; see
[group appearance guide](legaia-actor-group-appearance.md). Gameplay is queued.

**Historical integrated source checkpoint (2026-09-30):** the retail-enabled SDK discovery
suite passed **425 Python tests in 172.910 seconds**, exit 0, no skips, against
unchanged `55f5db15ec610db8642e1e995c29a0b4c6855730`. This includes actor group component
review/revert and all earlier Python services, superseding the 421-test checkpoint
and historical lower counts below. All six Node checks and editor/group/renderer
syntax passed separately against the same source, including box/range guards.
Browser/package/rendered checks retain their independent evidence; this run does
not establish gameplay or runtime parity. No game launched. Private log/metadata:
`local-output/sdk-20260909/sdk-regression-20260930-group-components.log/.json`.
Log SHA256: `69e0a61d32f73d1b313b00b543b0199f8787519991430e17eff44e23c31be60c`.

**Actor group component review/revert (2026-09-30):** selected imported actor
groups now offer Review group components, showing each actor's authored settings
or retail inheritance. A source-bound review includes every selected actor,
including inherited members; Revert validates the whole group before removing
only the chosen component, with one Undo entry. Other components and imported
provenance are preserved. Fifteen focused group/component/history tests passed
in 1.771s with no skips. Retail town01 three-actor browser review, atomic Revert/
Undo, unrelated-component preservation, stale inherited-member rejection and
closed pending-response checks passed with zero page errors; screenshot inspected.
A private fixture was saved during preparation; no game or package installation.
The 425-test source checkpoint includes this backend addition; browser evidence
remains separate. See
[component review guide](legaia-authored-component-review.md).

**Actor box and hierarchy range selection (2026-09-30):** Box select actors
now draws a marquee and gathers visible mesh IDs from one depth-tested render,
read in bounded strips. Shift-click selects a range in the filtered hierarchy;
Ctrl/Command adds boxes or ranges to the existing group. Replace/add operations
retain the 128-actor bound. Escape preserves selection; source/camera changes
reject a pending box, and proposal inspection disables these selection tools.
Node range/merge and rectangle/high-DPI/strip/restoration checks passed. Actual
2x-DPI town01 browser ranges, exact mesh ID boxes, hidden actor exclusion,
reverse/add/empty boxes, Escape, source withdrawal and exact placement-review
seeding passed without selection-service or authoring requests/page errors.
Screenshots inspected; no Save or game launch. These UI checks are separate
from the earlier 421-test Python checkpoint. See
[group placement guide](legaia-actor-group-offset.md).

**Viewport/hierarchy actor group selection (2026-09-30):** Ctrl/Command-click
now toggles imported actors into a bounded 128-actor group, with cyan scene and
hierarchy highlights, Frame actor group, Clear group and Review group offset.
Review seeds the existing placement dialog; normal clicks retain focused-actor
inspection. Group selection is transient and sends no selection or authoring
requests. Single-actor handles are suppressed while any group is selected.
Node membership/bounds/immutability checks and real town01 hierarchy/visible-mesh
Ctrl-click, filtering, framing, seeded review, +64 X proposal drag, atomic Apply
and project-restoring Undo passed. Client source/mode guards were checked with
injected state changes; actual Live remains unavailable without a checked runtime.
Screenshot inspected; no game launched or project saved. These UI checks are
separate from the earlier 421-test Python checkpoint. See
[group placement guide](legaia-actor-group-offset.md).

**Actor group proposal drag handles (2026-09-30):** Proposed mode now offers
X/Z handles for the selected actor group, snapping relative movement to 64 units.
Release revalidates the whole proposal without authoring; Return shows the updated
offsets/table, and Apply remains one atomic command. Escape restores the prior
proposal, bounds failures reject the whole move, and Current authored mode has
no group handles. Node offset/immutability/bounds checks and actual retail town01
browser pointer drags (+256 X, +64 Z), cancellation, no-write preview, Return,
one-command Apply and project-restoring Undo passed with zero page errors.
Screenshot inspected. This UI addition was checked separately after the 421-test
Python checkpoint; no new full-suite result is claimed. No game launched. See
[group placement guide](legaia-actor-group-offset.md).

**Actor group 3D proposal comparison (2026-09-30):** reviewed group offsets
now inspect in the assembled viewport, with Proposed/Current authored layers,
Frame group, Return retaining the draft and Restore. Only proposed transforms
change; source terrain preview heights are recalculated, with unknown runtime
elevation explicit. Single-entity handles are disabled; group handles are described
above. GLB export requires Restore.
26 focused tests in 1.301s/no skips and Node guards passed. Retail town01 exact
actor transforms, unchanged geometry/unrelated transforms, camera comparison,
Return/Restore and source withdrawal passed with zero authoring requests/page
errors; screenshots inspected. Separate Return Apply/Undo and export rejection
passed. No game launched. The 421-test source checkpoint includes this addition; browser evidence remains separate. See
[group placement guide](legaia-actor-group-offset.md).

**Actor group placement offsets (2026-09-30):** the editor toolbar now
previews and applies X/Z offsets to 2–128 imported active-scene actors. Retail,
Authored, Effective and Proposed positions stay separate. All source-grid/bounds
checks complete before one atomic command and one Undo entry. History protects
all group actors during reimport; stale source/project/actor states and replay
are rejected. 23 focused retail-enabled tests passed in 9.731s, no skips. Retail
town01 browser preview/no-write/bounds/Apply/Undo/Redo/Save and closed pending
response checks passed with zero page errors. Independent saved-project/package
MAN readback matched the four placement bytes while retaining prior menu and
selector edits. Screenshots inspected; no game launched or package installed.
The 421-test source checkpoint includes this feature; browser/package evidence remains separate. See the
[group placement guide](legaia-actor-group-offset.md).

**Authored component review (2026-09-30):** Authored Assets details now
show component-level review and source-bound Revert actions for actors, P2
scripts and scenes. Removing one component preserves the others and imported
evidence; Undo/Redo and Save/Open retain normal behavior. Stale reviewed values,
source/project identities and replay are rejected before mutation. 25 focused
tests passed in 1.334s with no skips. Retail town01 browser review/revert/history/
Save and stale rejection passed; independent disk reopen retained the selector
and three unrelated menu edits. Screenshot inspected, no page errors. No game
launched. The 421-test source checkpoint includes this feature; browser/package evidence remains separate. See the
[component review guide](legaia-authored-component-review.md).

**Script model-selector authoring (2026-09-30):** reached SET_ACTOR_MODEL
signed16 operands now use source-qualified commands, separate retail/authored/
effective layers, draft dispatch display, exact instruction-field navigation,
Undo/Redo, persistence, descriptor Build and experimental streaming/append output.
Runtime model-pool bases, actual assets and restaging remain unresolved; the
viewport does not execute the opcode. 34 focused retail-enabled tests passed in
35.413s with no skips, including five selector tests covering P2 ownership and
rebased extended actor-context rejection. Node binding/editor syntax and Dolk2 browser workflows passed; screenshots
inspected. Town01 package readback matched the exact MAN, retaining three menu
edits; Dolk2 rebuilt PROT contained the exact candidate. The 421-test source checkpoint
includes this feature; browser/package evidence remains separate. No game launched; gameplay deferred. See the
[model-selector guide](legaia-script-model-selectors.md).

**Project-wide text search (2026-09-30):** the same text search panel now
covers all imported scenes, retains scene coverage/reasons and opens the owning
scene before focusing the exact edit field. Discovery uses detached views and
checks imported/source and all dialogue-override identities. Retail town01/Dolk2
found645 supported runs across180 scripts (88 partial). Eleven focused tests and
editor syntax passed. Browser layer/scene search, cross-scene/return navigation,
stale aggregate and held-response close/reopen guards passed with unchanged
text/history and zero authoring requests/page errors. Screenshot inspected.
Explicit navigation changes Active scene; discovery leaves it unchanged.
Unknown/unvisited text remains excluded. The 405-test checkpoint includes this feature; gameplay remains deferred. See [text search guide](legaia-scene-text-search.md).

**Scene text search (2026-09-30):** source-qualified dialogue/menu runs
are searchable by text, owner and retail/effective/authored layers, with pages
and exact actor/partition-two edit-field navigation. Retail town01 discovery
found267 supported runs across91 scripts (60 partial), including eight P2 runs.
Nine focused Python tests and editor syntax passed. Browser filtering, paging,
field navigation, stale text-state and closed pending-response guards passed
with unchanged project state, zero authoring requests and page errors. Screenshot
inspected. Unknown/unvisited bytes and unsupported dialogue remain excluded;
coverage is explicit. The 405-test checkpoint includes this feature; gameplay deferred.
See the [scene text search guide](legaia-scene-text-search.md).

**Retail glyph preview (2026-09-30):** supported dialogue/menu forms show
Retail, Effective and padded unapplied Draft glyph stencils and source advances.
Nine focused Python tests, JavaScript font checks and editor syntax passed.
Retail browser pixel/advance readback, invalid drafts, Discard, held-response
close/reopen and malformed request rejection passed with unchanged project
state, zero authoring requests and page errors. Screenshot inspected. Controls,
substitutions, boxes, wrapping, pager behavior and runtime tint are not simulated.
The 405-test checkpoint includes this feature; gameplay remains deferred. See the
[glyph preview guide](legaia-text-glyph-preview.md).


## Ready for offline review

- Scene workspace: source-based textured scenes, hierarchy selection, inspector, orthographic/top views, coordinate locator, authored/retail layers, and actor/decorative/shared-scenery X/Z handles. Shared scenery browser checks moved three instances while preserving366 unrelated instances and verified Undo on both axes.
- Script movement: verified MOVE_TO/NPC_RUN X/Z authoring, source/effective values, history and persistence, viewport targets with source-instruction navigation, and descriptor/streaming experimental output composition. Y, executed branches and actor identity remain unknown where evidence does not establish them.
- Script flags and waits: source-qualified flag SET/CLEAR/TEST bit operands and WAIT_FRAMES targets have Inspector Apply/Clear/Discard, ordinary history and persistence, audited Build output and experimental append composition. Flag discovery shows separate retail/authored/effective indices with immutable retail grouping. Wait targets use host ticks0..32767; special context flags, larger wait targets and unresolved control flow remain unavailable. Story semantics, actual timing and runtime values are unverified.
- Animation: supported rigid clips can be previewed and exported. Channel edits and same-object retail/effective copy across frames/ranges use Apply/Undo/Discard. Existing-layout raw-record and readable channel-JSON download/import support retail/effective values. Raw-record checks pass shared-conflict, clear, persistence and package readback checks. Browser checks cover late responses, invalid selections and cross-object rejection. Shared clip users are explicitly listed. Proposed files can be inspected without applying them in both the model and scene viewers, restored, and returned to the same file form for explicit import.
- Model shapes: a diagnostic wireframe overlay displays all decoded triangle edges in the model viewer, including hidden edges. Focused WebGL and retail browser checks cover toggle, buffer reuse, vertex updates, picking and no project writes. Direct vector Inspector editing, per-vector retail reset, inspected-vertex camera location and exact-vector audit navigation are connected with focused browser checks. Existing-layout TMD, ordered-vertex OBJ and source-bound vertex/normal JSON replacements preserve source primitive/material data. Model build reports show scalar audits and navigate only to hash-matching authored previews. Normal-only edits are not visualized as lighting: the WebGL shader uses colors/textures without normal-based lighting. Equivalent oriented face order and relative indices passed exact roundtrip and isolated vertex edits on119 town01 models. A saved OBJ project passed Undo/Redo, reopen and package build.
- Textures: indexed scene palette-word and pixel-index editing, retail/effective JSON downloads and source-bound complete palette/pixel JSON imports are connected to texture Undo/Redo, Save/Open and Build. All96 town01 indexed textures round-tripped exactly. Source layout and other packed pixels are preserved; gameplay appearance remains unverified.
- Output: supported edits compose into private packages or experimental disc exports. Input snapshots, hashes and reopened archive checks support later review. Package descriptions list emitted edit families; output collisions are rejected instead of silently replacing existing builds.

**Scene proposal comparison (2026-09-30):** model-transform, model-file and
texture proposals can switch between Proposed (not applied) and Current authored
scene while retaining the proposal and camera framing. Exact layer/restore and
unchanged project checks passed in retail browser runs for shared model0074
(11 instances), a JSON model-file proposal, and texture29 (19 geometries,
31 materials, 58 instances). Texture checks also verified unchanged camera and
withdrawal on a stale scene source. These are browser checks, separate from the
390-test Python checkpoint; game appearance and retail visibility remain deferred.

**Animation scene comparison (2026-09-30):** supported animation inspections now
switch between the inspected animation and Current authored scene, retaining the
selected frame and camera. Switching layers pauses playback; the current layer
disables scrubbing, playback and rate controls. Returning restores the inspected
frame and slider together. A retail actor0011 JSON proposal (15 frames) passed
exact layer/placement/base checks, playback pause, Return retaining the file,
Restore, stale-source withdrawal and unchanged project state, with zero authoring
requests or page errors. Screenshot inspected. This is separate browser evidence;
retail animation timing, playback and gameplay visibility remain deferred.

**Independent animation consumer review (2026-09-30):** Blender 5.2.2 rendered
and evaluated a fresh complete Dolk2 actor0001 GLB (30 frames, ten rigid objects,
three embedded textures). All61 source-decoded samples, including half-frame STEP
holds and terminal pose, matched within0.000018 source units;24 distinct geometry
snapshots establish motion. First/middle/last renders were visually inspected.
The saved Blender scene reopened with all meshes, animation actions and three
packed textures. A reusable offline review tool and [consumer review guide](legaia-glb-consumer-review.md)
are available. Acceptance is specific to this clip; wider clips/consumers, retail
cadence, lighting and gameplay remain unverified. No game was launched.

**Indexed texture rectangle copy (2026-09-30):** copy an existing 4/8-bpp
image region to another location in the same texture, with draft pixels and
source/destination bounds before Apply. Overlaps read the immutable pre-copy
indices; packed neighbors, palettes, headers and VRAM layout stay unchanged.
Retail texture29 browser checks passed draft/no-write, bounds and stale-hash
rejection, no-op/no-history, Apply, Undo/Redo, Discard, Save/reopen and Build.
Independent package readback matched all pixels/palettes and the saved33312-byte
TIM; three indices/image bytes changed, zero palette words.24 retail-enabled
focused tests passed with no skips. This feature is included in the 405-test source checkpoint; browser
and package evidence remain separate. Gameplay appearance remains deferred.

**Renderer newline preservation fix (2026-09-30):** the plain-glyph
writer now excludes byte0x7C (`|`), which the pinned font renderer uses as a
newline even though MES emits it as a Glyph event. Source newline bytes split
editable runs and remain unchanged; form/API/text-file/Build writes reject new
pipe characters. Legacy saved projects open without rewriting their files;
invalid pipe edits have an unavailable effective value and can be cleared or
replaced. Clear/Undo and file-based null clearing retain normal history.
58 focused retail-enabled tests passed in29.566s with no skips, plus Node binding
checks and editor syntax. Retail browser rejection and legacy Inspector/Clear/
Undo passed with no page errors; legacy Build rejection created no output.
Synthetic dialogue/menu checks prove newline-byte preservation. The town01
52-actor read-only scan found no reached newline glyphs and no offered run
containing pipe; it is not wider retail preservation evidence. This fix follows
the397-test source checkpoint. No game launched; layout/gameplay remain deferred.

**Source-bound text JSON workflow (2026-09-30):** the script Inspector
exports supported dialogue/menu runs and previews external JSON before Apply.
Only each run's `text` is editable; null inherits retail. The file retains the
complete supported collection, verified MAN identity and current text-override
binding. All changes validate before one Undo entry; unrelated components stay
unchanged. Six focused text/project tests and editor/operand JavaScript checks
passed. Retail browser export/no-op/preview/immutable-field/stale-import,
two-run Apply/Undo/Redo/Save, oversized-file and closed pending-read guards
passed. Independent saved-project/package readback matched all three authored
label runs, including the prior override. Final preview screenshot and layout
bounds inspected. The 405-test source checkpoint includes this workflow; browser/package evidence remains separate.
See the [text-file guide](legaia-text-json-authoring.md). No game was launched;
menu reachability and display/selection remain deferred.

**Menu instruction-to-label navigation (2026-09-30):** decoded picker
choices now show separate retail/authored/effective glyph-run text and links to
the exact label forms. Owner, option, PCs, targets, capacity and source tokens
must match before a link is created. Duplicate or mismatched metadata is rejected.
The retail actor0001 browser exposed all30 supported label links, focused the
exact field and retained an unapplied draft. Stale source and withdrawn report
navigation were rejected; project/camera/service remained unchanged, with zero
authoring requests or page errors. Pure JavaScript checks cover multiple runs,
partition-two owners, detachment, bounds and ambiguity. Screenshot inspected.
This is separate browser/JavaScript evidence; gameplay remains deferred.

**Menu-label authoring (2026-09-30):** source-qualified plain-glyph runs
inside decoded two-, three- and four-option pickers now use the existing
Dialogue component and Apply/Clear/Discard, Undo/Redo, Save/Open and Build paths.
The Inspector identifies picker PC, option number, source capacity and encoded
choice target. Equal-span edits preserve jump entries, continuation bytes,
control/substitution tokens and record boundaries. Ordinary dialogue retains its
no-stop gate; conflicting or aliased menu spans remain unavailable. 54 focused
retail-enabled dialogue/script/resource tests passed in29.896s with no skips,
plus editor syntax and a retail browser workflow. A saved town01 actor0001
label package independently decoded to exactly the expected MAN. This is included in the 405-test source checkpoint; browser/package evidence remains separate. Menu story
reachability, glyph layout and runtime selection are unverified. See the
[menu-label guide](legaia-menu-label-authoring.md). No game was launched.

**Saved runtime node review (2026-09-30):** the Observed nodes panel can
export decoded metadata and reopen it later in Edit mode as a historical,
read-only Inspector. Positions/capture frames, uncertain fields, evidence and
unconfirmed candidate IDs are retained; raw prefixes and guard tokens are
excluded. Saved files never set Live state/correlation or change project/camera.
Serializer and synthetic browser download/reopen/filter/stale/file-read guards
passed with zero authoring requests or page errors. All17 fields from the actual
profile decoder on a synthetic prefix were accepted. See the [review guide](legaia-runtime-node-review.md).
No real runtime capture was performed; capture/gameplay acceptance remains deferred.

## Validation scope

The retail-enabled SDK discovery suite passed **421 tests in 172.966 seconds**,
exit code 0, with no skips, against unchanged committed source
`be7a5e42686119b2290643556a9827775cfb21c7`. This supersedes the 405-test
checkpoint at `cc41ded0` and includes model-selector authoring, authored component
review/revert, grouped placement commands/history and detached 3D proposal views,
along with earlier text/font/search services. Log and exact command, source,
result and hash metadata:
`local-output/sdk-20260909/sdk-regression-20260930-group-inspection.log/.json`.
Log SHA256: `4256992f5d0a3e1767a60056fbb625ce5c70b292f54373b7294743d3c7f2ef98`.
All five Node checks (font, texture usage, script operands, saved runtime review,
actor group scene coordinates) and editor/group-module syntax passed separately.
Browser workflows retain their independent pixel/render/navigation evidence;
a green suite does not establish gameplay, runtime parity or broader rendered
acceptance. Historical checkpoints below retain their dated evidence.

Recent private evidence lives under `local-output/sdk-20260909/`, including `sdk-suite-recheck-20260912.log`, `shared-scenery-multiple-check.json`, `shared-scenery-multiple-z-check.json`, `obj-equivalent-retail-20260912/report.json`, `animation-channel-copy-check.json`, `animation-effective-copy-check.json`, and `animation-copy-request-order-check.json`. These files are local evidence, not redistributable fixtures.

## Deferred gameplay

Use [the verification queue](legaia-gameplay-verification-queue.md) for saved input projects, exact artifacts and manual checks. NPC append/spawn behavior, script execution, animation playback, modified collision and visual behavior require their stated checks. Successful serialization does not establish gameplay acceptance. The user's wall-gap confirmation is bounded to that prior edit.

## Major unfinished work

- Arbitrary model topology/material replacement, general animation import and retargeting.
- Complete script/control-flow authoring, unknown records and scheduling behavior.
- Confirmed runtime actor identity and complete Unity-style live scene parity.
- Complete world-map behavior and unresolved MAPDSIP coverage.
- Remaining release/runtime acceptance, including the latest audio-lock build and deferred lifecycle/performance checks.
- Wider rendered animation acceptance beyond the reviewed Dolk2 clip, other consumers and broader scene parity.

See [feature coverage](FEATURE_MATRIX.md), [release parity](legaia-release-parity.md), [architecture](ARCHITECTURE.md), and [test plan](TEST_PLAN.md). The goal remains active; this report does not claim all offline work is exhausted.


Recent model interchange addition: source-bound complete vertex/normal JSON is
connected to model downloads, Apply shape, Undo/Redo and Save/Open. All119 town01
models round-tripped exactly. A retail normal-only model0009 probe preserved all
other TMD bytes and passed independent package-member readback. Browser checks
cover model0000 vertex upload, authored JSON download and Undo; they do not prove
runtime normal lighting. Saved probes are listed in the gameplay queue.

September 30 viewport authoring connection: enable **Wireframe overlay** and
Shift-click a projected vertex in an unposed model to open its exact object,
index and source XYZ in the vector Inspector. Selection does not apply changes.
Plain clicks and orbit drags do not select. Picking includes hidden vertices;
posed/proposed animation geometry, pending shape files and Live mode cannot
use this authoring shortcut. Retail browser checks verified the selected vector
and no submitted edits; projection checks cover center, behind-camera and
offscreen points.

Whole-object shape authoring: the vector Inspector now offers **Translate all
vertices in this object** with explicit integer XYZ offsets in source units.
It preserves normals, other objects and topology; validates every resulting
signed16 coordinate and the inspected model hash before applying one undoable
replacement. Zero offsets submit no change. Retail service checks proved all
vertices, preservation and exact Undo/Redo; browser checks proved Apply/readback/
Undo and disabled zero/overflow offsets. Gameplay remains deferred.

Script workspace addition: **Find a decoded instruction path** accepts a selected
start and destination and shows one shortest encoded-successor route, with
condition labels and clickable instruction steps. Cycles terminate; unknown
targets are reported as boundaries. No-path results do not establish gameplay
unreachability. Queries do not execute scripts or alter project state. Synthetic
browser checks cover branching, cycles, same-node queries and undecoded targets;
a retail actor-script path was checked edge-by-edge against its decoded report.
General control-flow authoring and live execution remain incomplete.

Script operand authoring now includes the one-byte **NPC_RUN encoded move
selector** (0–255), with retail/authored/effective values, Apply/Clear/Discard,
Undo/Redo, Save/Open and existing audited Build composition. X/Z and depth stay
unchanged when only the selector is edited. Selector behavior is unresolved;
no animation or speed meaning is assigned. Seven focused tests passed (four
separate retail streaming tests skipped without their environment input). A
saved town01 probe changed selector 13 to 14, and independent package ZIP
readback found exactly one changed MAN byte. Browser Apply/Undo passed.

EXEC_MOVE operand authoring: fixed-width encoded move selectors now share the
ScriptMovement workflow with NPC_RUN. EXEC_MOVE exposes only its move-selector
byte, with no invented X/Z or scene marker. Source-verified field offsets drive
Build audits and appended-record rebasing. Eight focused tests passed, including
all256 selector bytes with ordinary/extended headers and rejection of X/Z edits.
Retail actor0003 PC0x12 selector9->10 passed Save/Open, Undo/Redo, browser
Apply11/Undo10 and independent ZIP decode with exactly MAN byte4816 changed.
This addition follows the352-test checkpoint and has focused checks; runtime
move-table identity and behavior remain unverified.

Indexed scene texture palette authoring: **Edit selected palette** exposes
retail/effective words, RGB5/STP bit interpretation, explicit Apply, retail
reset and draft Discard. Entry changes lock while a draft is pending. Edits
are bound to the inspected effective TIM hash and use ordinary texture
replacement Undo/Redo, Save/Open and Build. Four focused synthetic/build tests
passed (one retail test skipped without its environment input); a separate
retail workflow and browser Apply/readback/Undo passed. Actual ZIP member
readback proved the saved entry change affected only TIM byte22. Other palette
entries, image data and headers are preserved. Shared/conditional banks and
runtime palette/blend behavior remain outside the accepted authoring scope.

Indexed texture pixel authoring: Shift-click the bitmap to inspect a pixel
and edit its encoded palette index. Retail/effective values and the inspected
palette colour word remain explicit. Apply/reset/Discard uses source-hash-bound
texture replacement history, persistence and Build. Four-bpp edits preserve the
other nibble; eight-bpp edits preserve neighboring pixels. Five focused tests
passed (one environment-gated retail test skipped), with exhaustive index
values at row/packed-byte boundaries. Separate retail checks passed authored
palette preservation, stale rejection, Undo/Redo, Save/Open, Build and exact
ZIP member readback. Browser Shift-click, range rejection, Discard, Apply and
Undo passed after correcting fractional canvas-edge rounding. Runtime residency
and visible/material/palette behavior remain deferred.

Indexed texture interchange: retail/effective JSON downloads and source-bound
JSON replacement now expose complete ordered CLUT words and pixel-index rows.
Existing TIM headers, bit depth, dimensions and array counts remain fixed;
duplicate keys, stale source hashes, unsupported formats and invalid values
reject before replacement. Effective JSON retains the retail source hash.
All96 indexed town01 scene textures round-tripped exactly; seven focused tests
passed (one environment-gated retail test skipped). Separate retail/browser
checks passed combined palette/pixel import, Undo/Redo, Save/Open, download/
upload and actual ZIP member readback. Existing TIM upload remains available;
file reads now reject changed texture/file contexts before submitting. No
quantization, resizing, shared-bank authoring or runtime acceptance is claimed.

Texture-file proposal preview: selected TIM/JSON files render without applying,
with palette-word, pixel-index and image-byte counts against both retail and
current authored data. Details are capped at256 changes while counts remain
complete. Return retains the file for explicit Apply. Source/layout validation
and changed-context guards precede display; Build capacity and runtime appearance
remain separate gates. Nine focused tests passed with one environment-gated
retail test skipped. Separate retail service and browser checks proved preview
leaves state/history/authored files unchanged, and Apply/Undo restores the exact
previous texture. Screenshot inspected; game not launched.

Texture Build reports now retain bounded palette-word/pixel-index/image-byte
audits with complete change counts. Changed pixel links open the effective
texture pixel editor only when its replacement hash matches the report;
older reports without payload details remain readable. Synthetic report tests
and a retail package readback verified the combined palette/pixel diagnostic
at TIM bytes22/544. This reports emitted payload edits, not runtime residency.
Browser checks passed report details, unchanged project state during pixel
navigation, and stale replacement hash rejection after a later edit.

Indexed texture rectangle fill: the editor previews an unapplied rectangle
using an existing encoded palette index, validates complete image bounds and
uses an inspected effective TIM hash. Apply creates one ordinary texture
replacement command; no-op fills create no history entry. Four-bit packed
neighbors, outside pixels and all palette words are preserved. Nine focused
tests passed with one retail environment-gated test skipped. Separate retail
checks passed stale rejection, Undo/Redo, Save/Open and actual ZIP readback;
browser draft/no-command, edge rejection, Discard, Apply and Undo passed.
This edits indices for every palette using the image; resizing, quantization,
shared-bank authoring and runtime appearance remain outside verified scope.

Project-wide flag references: imported scenes are freshly verified and scanned
without changing authored state or active selection. Scene/script-qualified
operand groups remain separate even when encoded bank/index values match;
partial/unavailable coverage stays explicit. Browser search includes scene
names, and source-instruction links navigate to the matching scene/script.
A three-scene town01/Dolk2/map01 retail probe found2142 references in899groups
across230scripts (128partial). Service state stayed unchanged. Browser coverage,
search and cross-scene instruction navigation passed with unchanged command
history; scene navigation uses the existing saved-view dirty tracking. Discovery
is bounded to64imported scenes,32768groups and262144references. Current runtime
values, shared variable identity and story names remain unresolved.

Scene texture dependency inspection: **Inspect scene texture uses** derives
static image/CLUT source contributors from the current verified scene preview,
keeps partial candidates separate from address matches, reports unresolved
materials/unavailable instances, and offers model/instance/material search plus
viewport Locate actions. Source keys guard navigation; inspection adds no
project edits/history. Focused Node checks cover shared/draft instances, CLUT
contributors, unresolved candidates, untextured exclusion, detached results and
bounds. Retail browser checks passed actor0005 navigation for texture25, and
texture29 fanout of31material matches/19geometries/58instances, scenery Locate,
empty search and stale-source rejection. Screenshot inspected. This addition
follows the365-test Python checkpoint; runtime residency/conditional visibility
and cross-scene dependencies remain unverified.

Model object quarter-turn authoring: rotate existing object vertices and normals
around their source-local origin by−90°, +90° or180° on source X/Y/Z. Exact
signed permutations preserve vector lengths, padding, topology and other objects;
signed16 overflow and stale effective hashes reject atomically. The vector draft
must be applied/discarded first. Three focused tests passed, including inverse/
four-turn restoration, all axes and invalid ranges. Separate multipart retail
checks passed object1 vertex/normal transforms, other-object preservation, stale
rejection, Undo/Redo, Save/Open and independent decompression of the actual ZIP
member. Browser draft guard, Discard, Apply, readback and exact Undo passed.
This addition follows the365-test checkpoint; gameplay shape/lighting/animation
compatibility remains deferred. Browser lighting does not use normal vectors.


Flag operand authoring foundation (2026-09-30): source-qualified ScriptFlags
commands preserve separate retail/authored/effective values, support Undo/Redo,
clear offline and Save/Open, and validate reached L/G/C flag SET/CLEAR/TEST
operands against immutable source records. Upper operand bits and dispatch/layout
remain unchanged; local width and context side-effect cases are unavailable.
Fourteen focused tests passed. Retail town01 actor0002 CFLAG_SET bit2-to3 changed
only decoded MAN byte4772; project history and reopening passed. Private project:
local-output/sdk-20260909/flag-authoring-project-20260930. Editor Apply and Build
composition remain pending. Build explicitly rejects ScriptFlags instead of
silently dropping them. This is foundation work, not a completed authoring
workflow or gameplay acceptance; the365-test checkpoint predates it.


Flag output integration (2026-09-30): ordinary Build now emits source-qualified
flag operands with independent audit checks for source/hash/owner/offset, upper
bits, requested bit, overlaps and unaudited changes. Build reports distinguish
flag.bit from raw operand bytes and name the source instruction. Experimental
compressed and raw-streaming exports rebase existing owners after NPC append;
flag changes participate in scene export audits. Thirteen selected tests passed
with the private retail disc and no skips (27.267s); sixteen focused project,
serializer and merge tests also passed. Retail ZIP readback changed only MAN
byte4772. Compressed town01 append reopened bit3 at rebased byte4775; raw dolk2
append composed bit24-to25 with dialogue and transition edits. Private package:
local-output/sdk-20260909/flag-authoring-project-20260930/Builds/flag-output-verified,
SHA256 adeeb217b679908845e4e9e260e31b3d22cccceb3fc0f63ab33fd502459c99bf.
Earlier foundation notes describing Build rejection are superseded by this
integration. Editor Apply remains pending; story meaning, execution, runtime
values and gameplay acceptance remain unverified. No game launched or package
installed. The365-test checkpoint predates this addition.


Flag operand Inspector (2026-09-30): supported source-qualified L/G/C flag
SET/CLEAR/TEST operands now expose retail, authored and effective bit indices
through script inspection APIs and editor forms. Apply/Clear use ordinary project
commands; Discard retains authored state. Numeric bounds and special context
SET8/CLEAR10 checks disable Apply; unapplied drafts block project history/save
controls. Unsupported scripts retain read-only reports and clearable unresolved
overrides. Failed refresh removes authoring controls. Flag Build report navigation
opens the source instruction. Six focused retail HTTP/project/merge tests passed;
HTTP checks include unexpected fields, invalid values and special context bits.
Browser checks passed layers, special-bit guard, pending draft guard, Discard,
Apply, Undo, Clear and restoration with no page errors; screenshot inspected.
Private evidence: flag-authoring-project-20260930/flag-browser-check.json and
flag-editor.png under local-output/sdk-20260909. Earlier pending-Apply notes are
superseded. Supported operand editing is connected through project persistence
and output; wider flag/control-flow authoring and gameplay acceptance remain
incomplete. No game launched. Temporary browser/server stopped.


Authored flag reference layers (2026-09-30): scene/project flag browsers now show
retail, authored and effective operands for source-qualified flag edits. Groups
keep their retail identity/index; matching effective indices never merge scripts,
scenes or unresolved contexts. Search includes effective operands. Authored
annotations pass the source serializer first; missing/stale source or unmatched
catalog identities reject, and project-wide discovery rejects state changes
during collection. No runtime values or execution are inferred. Twelve focused
flag/reference/project tests passed. Retail scene/project discovery retained
1249references with one authored operand (town01 actor0002 CFLAG_SET2-to3).
Browser layer display, retail grouping and exact instruction navigation passed
without page errors; screenshot inspected. Private evidence:
local-output/sdk-20260909/flag-authoring-project-20260930/flag-reference-browser-check.json
and flag-reference-layers.png. No edits/history were created by discovery;
temporary browser/server stopped. Gameplay remains deferred. The365-test
checkpoint predates this work.


In progress — script wait authoring (2026-09-30): WAIT_FRAMES inspection now
exposes its u16 target as duration_ticks, host_frame_delta units, signed16
accumulator width and explicitly unknown seconds/execution. Source-qualified
wait serialization changes only the two-byte target and preserves dispatch,
control layout and opaque bytes; source owners rebase after actor append.
Authored targets are restricted to0..32767 because the pinned reference uses a
signed16 saturating accumulator; larger retail targets remain unavailable.
Thirty-eight retail-enabled wait/inspection/catalog tests passed in2.226s.
Retail town01 has four eligible actor waits; actor0044 PC0x019F16-to17 changed
only decoded MAN byte24483. Dolk2 has no eligible actor waits under these source
coverage rules. Private evidence: local-output/sdk-20260909/wait-authoring-20260930/town01-wait-check.json.
Project commands, Inspector Apply and output composition remain pending; this is
serializer groundwork, not a finished editor workflow or gameplay acceptance.
Reference checkout HEAD has advanced to574ee5f603ed3ca9bd95c796711e595d9c2ad8a8;
WAIT handler evidence was read directly with git show from the unchanged SDK pin
d6e64c68ede25813d35db20980da82a1a025549b, step.rs opcode0x4A.
No reference checkout mutation or game launch occurred. The365-test checkpoint
predates this addition.


Wait project/output integration (2026-09-30): ScriptWaits commands now preserve
retail/authored/effective ticks, ordinary Undo/Redo, Clear, authored summaries
and Save/Open. Ordinary Build independently checks exact two-byte spans, requested
values, source identity and overlap/unaudited bytes. Reports expose wait.duration_ticks
and source instruction IDs. Experimental compressed/raw-streaming exporters
compose/rebase waits and include them in scene audits; new wait coverage in the
raw-streaming route subsequently received a retail own-wait probe in the rayman
checkpoint at the top of this report. Fifteen selected
retail-enabled tests passed in27.113s without skips. A focused merge check also
passed after adding explicit high-byte and second-byte overlap cases. Retail
town01 actor0044 wait16-to17 composed with actor0002 flag2-to3; saved project,
Undo/Redo, package ZIP/decompression and appended archive readbacks passed.
The two changed decoded MAN offsets were4772 and24483; append rebased the wait
to24486. Private project: local-output/sdk-20260909/wait-authoring-project-20260930.
Package under Builds/89f66b995f838276 has SHA256
148ab35c0b9146cab17359b9a870ab054c95aa98c415a7b26be199992da50971.
Earlier pending project/output notes are superseded. Inspector Apply is next;
seconds, execution, actual timing behavior and gameplay acceptance remain
unverified. No game launched or package installed. The365-test checkpoint
predates this work.


Wait target Inspector (2026-09-30): source-qualified WAIT_FRAMES forms now show
retail, authored and effective host ticks with Apply, Clear and Discard. Targets
remain0..32767; seconds and actual timing/execution are unresolved. Ordinary
script Undo/Redo and Save obey pending draft guards. Actor, partition-two and
trigger script routes expose authoring metadata without suppressing read-only
inspection when authoring is unavailable. HTTP commands reject extra fields,
invalid tick values and malformed identities. Build report links can open the
source wait instruction. Six targeted retail-enabled HTTP/project/merge/serializer
tests passed in7.768s. Browser layer/bounds/pending-draft/Discard/Apply/Clear/Undo
checks passed and restored the saved17-tick diagnostic; zero page errors and
screenshot inspected. Initial copied browser assertion had an encoding mismatch;
corrected test text, no application change required. Evidence retained under
local-output/sdk-20260909/wait-authoring-project-20260930/wait-browser-check.json
and wait-editor.png. Earlier pending-Apply notes are superseded. Supported wait
editing is connected through project and output; wider script/control-flow and
runtime timing acceptance remain incomplete. Temporary browser/server stopped;
no game launched or package installed. The365-test checkpoint predates this work.


Instruction operand navigation (2026-09-30): decoded instruction rows now display
retail/authored/effective values for verified movement, flag and wait targets,
with Open operand editor links that focus the matching form. Encoded source
operands and graph successors remain retail evidence. A reusable client metadata
adapter requires exact PC/mnemonic/context/retail values and consistent effective
layers; mismatches, duplicate PCs and oversized metadata withdraw links. It does
not simulate execution or mutate reports. Focused Node checks passed flags,
coordinate/selector movement, waits, bounds, ambiguity, context/value rejection
and source detachment. Retail browser flag/wait rows and exact input focus passed
with no project/history changes or page errors; screenshots inspected. Evidence:
local-output/sdk-20260909/wait-authoring-project-20260930/instruction-operands-browser-check.json
and instruction-flag-layers.png/instruction-wait-layers.png. Temporary browser
and server stopped; no game launch. This JavaScript addition follows the383-test
Python checkpoint and retains separate browser validation.


Model object uniform scaling (2026-09-30): Scale whole object in the vector
Inspector edits source-local vertices by an integer percent1..1000, with positive
uniform scaling, nearest-integer rounding and halves away from zero. Normals,
vector padding, topology/materials and other objects remain unchanged. Signed16
overflow, stale inspected hashes, invalid percentages/objects and pending vector
drafts reject before applying.100% is a no-op without history. Ordinary model
replacement supplies Undo/Redo, Save/Open and Build. Five focused scale/rotation/
JSON tests passed. Retail model0009 object1 at150% composed with its existing
rotation/normal override; normal/other-object preservation, history, reopening
and actual ZIP carrier decompression matched the replacement. Browser invalid/
draft guards, Discard,125% Apply, readback and exact Undo passed, no page errors;
screenshot inspected. Initial readback harness selected a scene-specific carrier;
corrected to the recorded shared model carrier, without rebuilding/replacing it.
Private project: local-output/sdk-20260909/model-scale-project-20260930; package
under Builds/e7728cba624de600 has SHA256
9d16d794517133d474921f7e001f9dd1929cc43f51df2ff8c33aca89f09aa3cb.
No game or package installation. Gameplay shape/animation/collision compatibility
remains deferred. The383-test checkpoint predates this addition.


Object-transform previews (2026-09-30): implemented before Apply in the model
vector Inspector for translation, rotation and scale. Source-bound proposed/current
geometry comparison, shared framing and draft/stale-response guards passed focused
model and retail browser checks without history or authored-file changes. Gameplay
acceptance remains deferred; the383-test checkpoint predates this feature.


Scene shape proposal inspection (2026-09-30): implemented for supported renderable
instances using their verified existing pose and scene placement. One-instance
isolation, Return to vector inputs and exact Restore passed focused and retail
browser checks without authored changes. Gameplay acceptance remains deferred;
383-test checkpoint predates this addition.


Model replacement file scene inspection (2026-09-30): TMD/OBJ/JSON proposals
can be inspected before Apply on a verified instance and pose, with exact Restore
and Return retaining the selected file. Retail browser/file-size/hash/state checks
passed without authored changes. Gameplay acceptance remains deferred;383-test
checkpoint predates this addition.


Shared model proposal impact (2026-09-30): all supported scene instances can be
previewed before Apply for transforms or replacement files, with distinct source
poses, preserved placements and explicit unavailable counts. Retail model0074
all11 placements, Restore/Return and unchanged state passed. Focused multi-pose
and browser checks passed; gameplay acceptance remains deferred.


Texture proposal scene inspection (2026-09-30): TIM/JSON proposals can be previewed
through the static image/CLUT material decoder before Apply, retaining geometry
and placement. Retail texture29 changed31 materials/19 geometries/58 instances;
Return/Restore, late-response withdrawal, unchanged project/authored-file hashes
and TIM readback passed.23 retail-enabled focused tests passed. Runtime texture
residency/gameplay appearance remain unverified;383-test checkpoint predates feature.

## External animation authoring — 2026-10-02

**Source-bound GLB animation authoring (2026-10-02):** An imported actor's
current effective rigid clip exports with a separate binding JSON. External GLB
translation/rotation edits receive an exact source-axis and quantization review,
proposed animation inspection and revalidated Apply through normal animation
commands. Unchanged axes retain their existing ownership; other shared-clip
contributors are not adopted. Stale exports, ownership-only changes, conflicts
and unsupported layouts reject. Undo/Redo, Save/Open and normal Build retain the
existing record and capacity checks. Counts, skinning, general retargeting and
retail timing/runtime acceptance remain unfinished. See
[animation GLB workflow](legaia-animation-glb.md).
