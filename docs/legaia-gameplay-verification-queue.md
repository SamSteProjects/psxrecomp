# Deferred gameplay verification

**Normal Build relocation package composition (2026-10-03):** Normal SDK Build now gathers all saved models sharing a topology-growth pack, defers them from legacy shape overlays, composes ordinary PROT patches at original offsets before growth and emits one format 7 `disc_relocation` feature payload. Source-bound external Form 1 edits are composed into mapped sectors; overlap, stale hashes, PROT-boundary straddles, ISO metadata conflicts and native payload budgets reject. The existing format 6 path remains for builds without topology additions. Review computes/verifies proposed bytes without writing output; packing validates the emitted relocation asset, and repeated builds are deterministic.

Validation: 36 focused Python tests pass (3 Retail-gated cases skipped). New normal Build regression uses actual synthetic Mode 2 ISO sectors, saved addition/retained-shape bindings in one pack, original-offset patch composition, independent reopened model payload comparison, the real generic psxmod packer and archive readback. External edits crossing a sector boundary map correctly. A fresh MSVC native harness accepts/activates an SDK-emitted synthetic package, compares every proposed PROT/metadata sector through the C disc reader and restores stock count on netplay clear. Private proof: `local-output/sdk-20260909/model-growth-normal-build-20261003/parent/`. Existing native compiler/parser warnings remain. No Retail package/game launch, installation or full Retail ISO/BIN export ran; gameplay remains deferred.

Remaining integration: saved Build history verification and Build & Run still assume an overlay-only inventory/private size bound. Those consumers need relocation-aware inventory and runtime observation before this package is offered as a complete Build & Run workflow. This checkpoint supersedes the earlier claim that normal Build cannot emit growth packages; it does not complete the full SDK or prove Retail/gameplay acceptance.

**Runtime relocation publication and C reader lifetime (2026-10-03):** Commit now stages a fresh reader, rechecks whole-source SHA256 before/after native preflight and publishes only after successful plan/state preparation. The opaque C disc handle acquires the prepared reader for the bound source path. Competing source paths reject; replacing an active relocation invalidates old handles. Closing one shared handle leaves the other live. Netplay clear and reinitialization remove relocation from retained readers and restore stock layout. Failed recommits preserve the published reader. This supersedes the earlier unfinished-activation checkpoints below; normal SDK Build still emits format 6 ordinary overlays and does not yet compose/package model growth.

Validation: fresh MSVC mod-runtime regression passes both its built-in public synthetic source/payload and the independently Python-generated synthetic fixture. Coverage includes 60-to-62 sector mapping, replacement user/raw terminal framing, shifted movie/tail reads, undersized/out-of-range output preservation, wrong source, changed payload, same-path changed source, failed-commit isolation, plan replacement, shared close, netplay clear and reinitialization. The C bridge is now linked into the CMake regression target. Existing compiler/parser warnings remain; the full runtime/game build was not run. Private build/log: `local-output/sdk-20260909/mod-disc-relocation-20261003/parent/`. No game, installation or full Retail disc export ran; gameplay remains deferred.

PVD/path-table preflight checkpoint (2026-10-03): mandatory/optional LE/BE tables,
exact expected bytes and opaque PVD preservation qualify natively with rollback.
Python/native complete synthetic ISO/payload interoperability passes. Reader
publication/lifetime and normal Build remain unfinished; activation is still
guarded. No game/full Retail export ran; no immediate gameplay gate is added.

Activation preflight checkpoint (2026-10-03): source hashes, bounded ISO entry
mapping/membership and streamed proposed PROT readback qualify offline. Wrong
movie mapping/extra directory entries reject and roll back. Runtime publication,
lifetime, path-table semantic checks and normal Build remain unfinished. Commit
still rejects enabled relocation rather than silently running stock. No immediate
gameplay gate; no game or full Retail export ran.

Feature relocation manifest checkpoint (2026-10-03): format 7 declarations,
selection, payload requalification/fingerprinting and provider/disc-edit conflicts
pass offline. Runtime commit rejects enabled relocation while activation remains
unfinished, rather than silently booting stock. SDK Build still emits format 6;
activation and normal Build integration remain offline work. No gameplay gate.

Native payload qualification checkpoint (2026-10-03): strict native decoding and
original PROT/metadata preimage checks pass, including Python/native payload and
source-sector interoperability. Feature manifests, conflicts, activation and
normal Build remain unfinished. No game, installation or full-disc export ran;
no immediate gameplay gate is added.

Relocation package payload checkpoint (2026-10-03): source-bound PROT/metadata
payload encoding and strict readback pass offline. The legacy derived-disc
channel is forbidden for feature-style manifests. Native parser, feature conflict
rules, activation and normal Build integration remain unfinished. No game or
full-disc export ran; no immediate gameplay gate is added.

ISOReader relocation checkpoint (2026-10-03): native user/raw reads, grown sector
count, moved-root file lookup, virtual subchannel bounds and Clear/Close/Open
pass offline. Existing SBI/CDDA tests still pass. No generated SDK package yet
activates these APIs; qualified package activation and normal Build remain
unfinished. No game/full Retail export ran; no immediate gameplay gate is added.

Native raw-sector checkpoint (2026-10-03): codec/mapping regressions pass and
64 varied native sectors match Python byte-for-byte. Replacement/metadata Form 1
protection regenerates; shifted XA payload/protection stays exact. ISOReader/CD
controller wiring, qualified activation and normal Build packaging remain offline
work. No game or full-disc export ran; no immediate gameplay gate is added.

Native logical mapper checkpoint (2026-10-03): offline C++ regression passes for
inserted payloads, shifted sectors/metadata, sector count and failure isolation.
It is not yet connected to package activation or CD reads. Raw Mode 2 framing
and normal Build integration remain offline work; no immediate gameplay gate.
No game, installation or full-disc export ran.

Relocated logical ISO checkpoint (2026-10-03): composed model-pack growth now
reopens through synthetic ISO lookup, including moved directories/path tables
and unchanged following movie bytes. This is in-memory logical readback; no BIN
was exported. Runtime physical-sector mapping/sector count and normal Build
packaging remain offline work. No immediate gameplay gate is added.

Model relocation composition checkpoint (2026-10-03): original-offset patches
are verified and applied before pack/PROT growth. Synthetic tests preserve edits
across multiple growing carriers/resources and shifted neighbors; final packs
reopen. Normal Build package/ISO integration remains offline work. No game,
installation or full-disc export ran; no immediate gameplay gate is added.

Shared-pack preparation checkpoint (2026-10-03): retained-base additions and
ordinary edited neighbors qualify together, with actual Town01 independent pack
reconstruction and bounded PROT readback. The compressed carrier grows eight
bytes, demonstrating the need for relocation. Normal Build composition/ISO
integration remains offline work. No gameplay gate or game launch is required
at this checkpoint; deferred native appearance/culling/pose acceptance remains.

Face-addition editor checkpoint (2026-10-03): model viewer donor/typed fields,
Review, wireframe comparison/orbit/zoom, reviewed Apply and authored viewport
refresh pass in the private Town01 browser proof. Close/stale/late/mode/busy/error
guards pass, including the asynchronous close-event race. No Save/Build/Run or
installation/gameplay occurred. Relocated normal Build/ISO and subsequent edit/
removal/GLB composition remain unfinished. Deferred native appearance/culling/pose
acceptance is unchanged; no immediate gameplay gate is added.

Face-addition HTTP/copy checkpoint (2026-10-03): source/Review/reviewed Apply
pass through real loopback HTTP in a private Town01 clone; stale/mismatched
requests reject. Project copy retains and reopens both the addition model and
its independently qualified base dependency. Editor dialog and normal Build/ISO
integration remain unfinished. No installation or gameplay ran; existing deferred
native appearance/culling/pose acceptance remains. No immediate gate is added.

SDK face-addition project binding checkpoint (2026-10-03): internal source/review/
Apply, retained base edits, session history, Save/Open and composed preview pass
offline in a private cloned Town01 project. Existing project Open clears session
history while retaining saved asset state. Editor/HTTP actions and relocated normal
Build/ISO export remain unfinished, and existing-layout export rejects this binding.
No model was installed or played; deferred native appearance/culling/pose checks
remain unchanged. No immediate gameplay gate is added.

Model pack PROT relocation checkpoint (2026-10-03): physical carrier growth,
sector alignment, later start relocation and reopened model-pack verification
pass offline. A bounded logical start-table fixture with the fresh Town01 carrier
forces one sector of growth while retaining neighboring models/resources/archive
payloads. This is not a full Retail archive or normal Build. Project/editor/ISO
integration remains required; deferred gameplay checks are unchanged. No install,
gameplay or new immediate manual gate occurred.

Model pack/carrier growth checkpoint (2026-10-03): selected ledger-qualified
members and later directory/resource offsets can now grow offline. Town01 slot 9
passes exact reconstruction within its physical PROT span, with all 113 neighboring
slots and five other compressed sections preserved. This is not a normal Build or
installed-game result. PROT/disc relocation and project/editor integration remain
required; deferred added-face appearance/lighting/culling/pose checks are unchanged.
No immediate gameplay gate is added.

New-face identity ledger checkpoint (2026-10-03): stable source/authored donor
identities and serialized multi-batch replay pass offline, including an independent
Retail two-quad reconstruction. The record is not an SDK asset override; carrier
relocation, project/editor/history/Build integration and removal/GLB composition
remain required. No geometry was installed or played. No immediate gameplay gate
is added; deferred added-face appearance/lighting/culling/pose acceptance remains.

Native new-face codec checkpoint (2026-10-03): independent model-level packet
growth and source recovery pass offline. The candidate is not installable through
the SDK yet: carrier relocation, durable topology identity and reviewed editor/
history/Build integration remain required. Later gameplay must establish added-face
appearance, lighting/culling, pose and shared-instance behavior. No model was
installed or played; no immediate gameplay gate is added.

Model allocation Inspector (2026-10-03): read-only Retail/Current extent
inspection adds no gameplay gate. The source endpoint and editor dialog are
connected; general new faces, authored topology identities and relocation
remain offline implementation work. No geometry or allocation was authored,
installed or played by this checkpoint.

Model allocation foundation (2026-10-03): extent inspection adds no gameplay
gate and authors no geometry. General new faces remain unimplemented. Offline
work still needs authored-face identities, model/carrier relocation, Inspector
review/Apply and exact Save/Open/history/Build readback before native appearance,
culling, animation pose and shared-instance verification can be queued.

Conditional capture Inspector summary (2026-10-03): read-only presentation
adds no gameplay gate. Payload extent and both conditional offsets are visible,
but actor match, payload ownership and runtime execution remain unresolved.
No capture, branch or transform was authored or played by this feature.

Conditional capture source guard (2026-10-03): incoming-edge ambiguity is
now rejected offline and adds no gameplay gate. Native existing/new-actor
ownership alternatives and captured-byte execution remain unfinished. The guard
only prevents ambiguous captured bytes from appearing as parent source assets;
no effect, transform, dialogue or branch was authored or executed.

Effect-spawn source checkpoint (2026-10-03): inspection adds no immediate
gameplay gate. Conditional capture ownership still needs a source-model solution
before runtime verification can establish existing-actor match, allocation and
captured-byte execution. Town01 actor0020 PC34 has possible continuation offsets
48/65 and a15-byte captured payload. No effect or capture was authored, installed
or executed by this checkpoint; actor identity remains unresolved.

Actor-acquire source checkpoint (2026-10-03): inspection adds no immediate
gameplay gate. Later runtime observation must establish acquisition predicates,
callback801D25EC parameter meaning, pending/success behavior and actor/position
correlation independently of static edges. Source sites: Town01 P2 record0005
PC1600 and records0012/13/14 PC57. No callback parameters or transforms were
authored, and no game was launched during this checkpoint.

FMV request source checkpoint (2026-10-03): inspection adds no immediate
gameplay gate. Later runtime verification must establish ID-to-movie mapping,
request activation, playback stability and return behavior independently of
static PC advancement, including Town01 P2 record0025 PC1804's ID1 request.
Two trailing bytes are consumed but their purpose remains unknown. No movie
request was authored, played or installed during this checkpoint.

Actor-state-copy source checkpoint (2026-10-03): no immediate gameplay gate
is added. Later live observation must independently correlate MENUE3 selectors
and dispatch contexts to actors, establish copied field meaning and check
lookup-miss/context-update behavior. Dolk2 P2 record0011's sixteen inverse
selector pairs alone do not prove capture/restore roles or actor positions.
No actor transform was authored and no game was launched for this checkpoint.

Embedded STATE_RESUME0 source checkpoint (2026-10-03): inspection adds no
immediate gameplay gate. Later menu observation must establish activation,
suspension/completion and semantic argument/payload ownership independently of
the static extent, including Dolk2 actor0011 PC115 / actor0012 PC112. No menu
payload was authored or executed by the editor.

Scene-register/callback source checkpoint (2026-10-03): inspection adds no
immediate gameplay gate. Later runtime observation must establish the scene
register effects and callback8003C7EC behavior independently of encoded fixed
continuations, including map01 P2 record0038 PC110 / record0039 PC687. No
register operand was authored or callback executed by the editor.

MENU8 source-coverage checkpoint (2026-10-03): offline inspection adds no
immediate gameplay gate. Later native actor-allocation verification must establish
acquisition/resumption and child ownership/execution independently of static
payload spans, including map01 P2 record0039's14 children. Character selector
correlation and global-write effects remain runtime-unverified. No payload or
write operand was authored, and no game was launched.

## Value-comparison branch runtime - deferred

Offline fixture: `local-output/sdk-20260909/inventory-branches-20261003/parent/service-project/`.
Map01 P2 record0009 PC52 retargets VALUE_COMPARE_BRANCH PC111→14.
Package SHA256 `bde95688550c4a382485ac426f08a90a0a797c2e553b9d05e9b3f7dd9039e611`.
Review/history/Save/Open/Build and whole decoded-MAN comparison pass; only
encoded destination offsets3006/3007 differ. This is a serializer fixture,
not an accepted story change. Later verify branch activation, runtime comparison
values and MENU49 field/ramp behavior against a retail baseline. Random/scaled
conditions need separate runtime evidence. No package was installed or played;
offline SDK work can continue.

STATE_RESUME coverage checkpoint (2026-10-03): fixed completion-boundary
inspection passes offline and adds no immediate gameplay gate. Later menu-state
verification must establish activation, suspension and completion independently
of the static `external_state_completed` edge, including Dolk2 actor0049's three
sub9 sites. No menu payload was authored or game launched.

## MENU8C retail branch runtime - deferred

Offline fixture: `local-output/sdk-20260909/script-coverage-20261003/parent/service-project/`.
Town01 P2 record0015 PC23 retargets FIELD_68_BRANCH PC50→12. Package SHA256
`54707d3cd606648d1051ae10234c0435bdace401f603a26d76a0bb536c9ac06c`.
Review/history/Save/Open/normal Build and independent whole-MAN readback pass;
only decoded offsets40645/40646 differ. This is an encoding fixture, not a
recommended story change. Later verify activation and field0x68-dependent
behavior against a retail baseline before treating this retarget as accepted.
Actor-search runtime branches and selector/table correlation need separate
runtime evidence. No package was installed or played; offline work can continue.

Source-flow overview checkpoint (2026-10-03): this read-only feature is accepted
offline and adds no immediate gameplay gate. Its cycles and entry reachability
describe encoded source edges only; existing authored-branch story/runtime checks
remain deferred. No game was launched for this checkpoint.

## Restored Retail face with later edits - deferred gameplay

Ready offline fixture: `local-output/sdk-20260909/model-face-restoration-20261003/parent/browser-project/`.
Package SHA256 `d7bed311677f882ae97792d3544155ab425ddb695a11fc740bd090d211d76d68`.
Town01 model0009 restores object1 Retail quad0 (188→190 triangles), retaining later
vector/reference/UV/material edits in a normal `tmd-content-v3` binding. Whole-model
and compressed-neighbor readback match an independent reconstruction. Later verify
restored appearance, shared group settings and shared-instance/animation behavior.
The package is not installed or run.

## GLB vertex edit after removal - deferred gameplay

Ready offline fixture: `local-output/sdk-20260909/model-removal-glb-20261003/parent/browser-project/`.
Package SHA256 `036b2732b290e954c578de666d3f9b9b7fd8e30e8310f45efd61f4deaa186d8a`.
Town01 model0009 keeps the removed object1 quad and cumulative reference/material edits.
Its GLB alias edits retained vertex1 X126→128, with exactly byte3196 changed and
candidate/compressed-neighbor readback verified. Later verify appearance across
shared instances and animation/scene transitions. The package is not installed or run.

## Material editing after removal - deferred gameplay

Ready offline fixture: `local-output/sdk-20260909/model-removal-materials-20261003/parent/browser-project/`.
Package SHA256 `9458a47b0aa62d030a5c62eb017157c2adc8ffe889895b35c0b2b530dbf40150`.
Town01 model0009 keeps its removed quad and prior typed edits. Current0 / Retail1
CLUT column9→10 and page column10→11 change two words; Current group0 enables ABE
across ten retained faces. Exact candidate and compressed-neighbor readback pass.
Later verify palette/VRAM associations, caller blend state and appearance across
shared instances/scene transitions. The package is not installed or run.

## Reference retargeting after removal - deferred gameplay

Ready offline fixture: `local-output/sdk-20260909/model-removal-retarget-20261003/parent/browser-project/`.
Package SHA256 `5dfcc1ffed7111883201e380d28eff5fdcbc328fbfbdf22962de9101aed99ac9`.
Town01 model0009 object1 retains its removed quad and UV edit, retargets normal4→3
at three Current words and vertex5→6 at one Current word. Exact candidate and
compressed-neighbor readback pass. Later verify intended shape/lighting across
shared instances and animation/scene transitions. The package is not installed or run.

## Retained-face UV edit after removal - deferred gameplay

Ready offline fixture: `local-output/sdk-20260909/model-retained-faces-20261003/parent/browser-project/`.
Package SHA256 `f6f3bee2fbada9ba1d5f76b19e645ce18a4ec51baaf586fe56d6f1b74c77b911`.
Town01 model0009 retains its removed object1 quad and edits Current0 / Retail1 corner0 U0→17.
Exact candidate and compressed-neighbor readback pass. Later verify texture appearance
across affected instances and native animation/scene transitions. The package is not installed or run.

## Vector editing after face removal - deferred gameplay

Ready offline fixture: `local-output/sdk-20260909/model-topology-vectors-20261003/parent/browser-project/`.
Package SHA256 `f21d1fd224cbf19bba111a1b7398bf00da59e0b7af1767d3afcc4f45b7ed084b`.
Town01 model0009 retains the removed object1 quad (188 triangles) and edits vertex0 X126→143.
Whole-model and compressed-neighbor readback are exact. Later verify the intended
vertex displacement and missing face across affected instances, animation and scene transitions.
This package has not been installed or run; other offline work can continue.

## Count-changing model face removal - deferred gameplay

Ready offline fixture: `local-output/sdk-20260909/model-face-removal-20261003/parent/browser-project/`.
Package SHA256 `c6bcc7a8ccd981960b07cbb8482c0699e8179ce161a66594a8a841120d5a138c`.
Town01 model0009 object1 Current quad0 is removed, reducing190 to188 model triangles.
Complete model and compressed-neighbor readback are exact; object/vertex channels,
source vector tables and carrier capacity survive. Later verify the intended
missing face in each affected instance, native traversal/culling, scene transitions
and normal actor/animation behavior. This package has not been installed or run.
No immediate gameplay check is needed to continue other offline SDK features.
See [workflow and limits](legaia-model-face-removal.md).

## NPC source capacity - deferred gameplay

Latest ready fixture: `local-output/sdk-20260909/npc-runtime-source-20261003/parent/browser-project/`.
Package SHA256 `e8907db2b03619303d72cf3e09fbe2ac82bff7815534733d15c9337a00443c06`.
The existing Town01 candidate retains its exact MAN bytes and now records a54-node
initial-placement lower bound against the qualified143-slot pool. Other consumers
remain unknown. The91-draft blocked fixture is a rejection proof and must not be
installed. Later verify actual available slots, initialization, native identity,
visibility, scripts, collision/dialogue and lifecycle on the disabled ready candidate
when gameplay verification resumes. See [source evidence](legaia-npc-actor-pool.md).

## Imported material binding selection - deferred

Additional group-copy fixture: `local-output/sdk-20260909/material-group-binding-20261002/parent/browser-project/`.
Package SHA256 `f1e9c622f00bf4b07fbee0ef1926ecd83872e8430125c94ebda325effcfd39c0`.
All14 Dolk2 model0133 object0/group4 textured primitives use the selected binding;
13 add26 CLUT/TPage word edits while the earlier single-row edit and ABE persist.
Complete TMD/carrier readback is exact. Later inspect every affected face/shared
instance for UV suitability, live residency, palette behavior, blending and revert.


Saved fixture: `local-output/sdk-20260909/material-binding-picker-20261002/parent/browser-project/`.
Package SHA256: `a952ee4f6443068d63f8ddc5b6f636aa31168d3625851d01fcc6a14d0e8a89a3`.
Dolk2 model0133 object0/group4/primitive36 retains authored group ABE and copies
model0000's page9/row0/4-bit and CLUT column0/row490. Offline complete payload
readback is exact; suitability is unverified. Later compare target UV coverage,
live uploads/residency, palette changes and native blend across shared users,
then verify revert at matching story state. No immediate gameplay is required
for the picker milestone. See [workflow/evidence](legaia-material-binding-picker.md).

## Assigned animation GLB - deferred

Saved fixture: `local-output/sdk-20260909/assigned-animation-glb-20261002/parent/browser-project/`.
Package SHA256: `2d9eaec92f5076624af50f568c6494cd2f01b4b3b27b7f39becb60f2b3ad0aa7`.
Town0b actor0019 has initial clip0012 via witness0049, retains its original
clip0013 X contribution, and adds frame0/object0 X=1 to witness0049's clip0012.
Independent complete payload readback changes only ANM bytes8880/10336 and MAN
byte9471 against retail. Later compare original/assigned clips at matching
story state, all known shared users, script-driven clip changes, actual timing,
pose suitability and revert behavior. No gameplay acceptance is inferred from
the browser pose or package. See [owner semantics](legaia-assigned-animation-glb.md).

## World source placement transforms - deferred

Additional yaw-ring fixture: `local-output/sdk-20260909/worldmap-placement-yaw-20261002/parent/browser-project/`. Package SHA256 `4a953cf8acfb12105dd121b7c3f6416f9469bfa00907ef4c2999d4e9bc9de6bf`. Record0477 retains X1280/Y256/Z256 with yaw448 across57 source seeds. Independent full MAP readback proves the two yaw-byte changes alongside the prior offsets. Pointer rotation, cancellation, history, persistence and Build pass offline; use matching story-state retail/authored gameplay comparisons below to check visibility, resting transforms, collision and script overrides.

Additional viewport-handle fixture: `local-output/sdk-20260909/worldmap-placement-gizmo-20261002/parent/browser-project/`. Package SHA256 `d15d8464e9486a9463dac0b5653e1005aadd9fa942c13e11ebf95fee8d28b6b7`. Record0477 is X1280/Y256/Z256/yaw1536; all57 source instances share it. Complete source reconstruction and package readback match, with only four MAP bytes changed. Source Y/Z move the display in the opposite directions. Apply, history and Save/reload pass offline; scripts, actual native resting positions, visibility and collision remain unverified. Use the same retail/authored checks below when gameplay verification is resumed.

Saved fixture: `local-output/sdk-20260909/worldmap-placement-authoring-20261002/parent/browser-project/`.
Latest package SHA256: `89b1be7633bd5911afd39bce3dcea41ea8723370f7f96535c11ace76dab1bb56`.
Map01 record0477 retains its source cell/anchor/model/flags and changes X offset
from0 to1024 and yaw from512 to1536; only complete MAP bytes15265/15275 differ.
The record serves57 qualified source cells. Independent source reconstruction,
package readback and editor Current/Proposed pixels/matrices agree. No install
or game launch ran; the feature remains disabled by default.

Later compare retail/authored map01 at matching story state. Check source-seed
offset/yaw visibility, affected instances, scripted initialization/resting transforms,
collision and travel behavior; then revert and compare again. Scripts may overwrite
these seeds or suppress them. An authored viewport cannot establish runtime parity.
See [workflow and source limits](legaia-worldmap-placement-authoring.md).

## Fixed-span source NPC candidates - deferred

Saved fixture: `local-output/sdk-20260909/npc-normal-build-20261002/parent/browser-project/`.
Package SHA256: `0e3f6dd4ef175db810ff9b3283432ef3459a429991ba370c3254b996fb4c1d30`.
Town01 donor11 is cloned as record53 at X3008/Z5440, with existing donor placement
and facing edits composed separately. Decoded MAN grows45338 to45917 bytes;
optimal compression occupies24856 within the original24894-byte stream. Only
that original stream and its four-byte size word change; pointers, neighboring
payloads, physical carrier and TOC stay exact. No package was installed or game
launched, and the candidate feature is disabled by default.

Later verify native allocation, record initialization, actual spawning/position,
script scheduling, dialogue, collision, transitions and save/reload behavior.
Reached decoded spawn-reference rebasing does not prove opaque script paths or
valid new-actor runtime identity. See [candidate boundaries](legaia-npc-build-candidates.md).

## Global landmark menu records - deferred

Saved fixture: `local-output/sdk-20260909/worldmap-authoring-20261002/browser-project/`.
Package: `local-output/sdk-20260909/worldmap-authoring-20261002/browser-project/Builds/a96da8f8cfabbc0c/legaia.sdk.0f096fa3c17d-0.1.0-a96da8f8cfabbc0c.psxmod`.
SHA256: `08eb08fe22cb2aa10dc5e034932deb9529c2c706e594dbf617f0bb00135be680`.
Row 0 Rim Elm encoded X changes 96 to 97; discovery index 32, destination 85
(`map01`) and Y 25 stay retail. Fresh source and complete executable readback
confirm only SCUS file byte 0x6429C differs. The 126-byte overlay retains all
other rows and the terminator; names, padding, code and headers remain exact.
The saved scene import matches a fresh disc import. Global/field Build
composition, history, persistence, byte review and source navigation pass.

Later compare stock/authored world-map menu drawing at matching story/discovery
state. This one-unit edit is a small drawing probe under the reference pixel
interpretation; the executing draw/travel consumers are not yet proved. Other
future name/discovery/destination edits need separate visibility, duplicate
suppression, destination and post-transition control checks. Do not infer a
reachable scene from CDNAME membership. Name/discovery have static consumer
evidence, without current flag values or runtime activation. No package installed
or game launched. Experimental Export disc rejects this global component; use
normal Build. See [workflow](legaia-worldmap-authoring.md).

## Authored primary trigger cells - deferred

Saved fixture: `local-output/sdk-20260909/trigger-cells-20261002/project/`.
Package: `local-output/sdk-20260909/trigger-cells-20261002/authored-build/legaia.sdk.0f096fa3c17d-0.1.0-f5d1cda012898e68.psxmod`.
SHA256: `f626c5d0fd53fff6ddf51fad209304ee4587fa03d4015136e8785c35f865ccf3`.
Town01 primary kind-0 row0000 changes tile X30 to31, retaining tile Z40 and
teleport destination bytes146/132. Fresh disc, MAP and ZIP readback confirms
only65554 changes30 to31. The effective source cell is world X[3968,4096),
Z[5120,5248), with Y=0 an unknown-height inspection plane. Retail remains
X[3840,3968). Actual browser review, separate layers, frame, history, persistence,
reset and primary binding composition passed. Build composition with regions,
scenery and walls changes exactly the four audited bytes in one MAP overlay.

Later gameplay acceptance should compare stock/authored contact at both cells,
retained destination/binding, primary/fallback precedence and coincident-row
shadowing. Check scene initialization, object-cell footprints, story state,
height and normal control afterward. The reference dispatcher covers tiles0..127;
byte values outside that range have no activation claim. This package does not
paint object/collision flags or change trigger payloads. No package installed or
game launched; manual verification is saved for later. See
[trigger cell workflow](legaia-trigger-cells.md).

## Source-facing instruction fixture - deferred

Saved fixture: `local-output/sdk-20260909/script-facing-20261002/project/`.
Package: `local-output/sdk-20260909/script-facing-20261002/authored-build/legaia.sdk.760132307200-0.1.0-19dab14dc2db8d24.psxmod`.
SHA256: `556dbae3db541bbd729188d81832ace68aeceac381d74c85495038c06d6c36ea`.
Town0b actor0019 CAM_CFG at source PC0x0011 changes sector1 to5. Original-disc,
MAN and ZIP readback changes only MAN9479 from0x81 to0x85; the upper0x80 flag,
placement, model/animation and every other byte are unchanged. Inspector source
layers, compass drafts, Apply/Clear, Undo/Redo, Save/reload and mixed-placement
Build pass offline. P2 source/context qualification is also checked.

Later gameplay acceptance should establish the visible actor/source binding in
Town0b, verify that this installation instruction executes in the chosen story
state, compare stock versus authored facing, and check later script behavior.
The compass is an instruction-operand preview; generic scene-model/initial/live
heading is unresolved. Conditional Town01 facing instructions need branch-specific
acceptance. No package installed or game launched; this fixture does not require
immediate gameplay. See [source-facing workflow](legaia-script-facing.md).


## Authored region bounds - deferred

Saved fixture: `local-output/sdk-20260909/region-bounds-20261002/project/`.
Package: `local-output/sdk-20260909/region-bounds-20261002/authored-build/legaia.sdk.fec5aa9d3474-0.1.0-a26b58e7bca78d90.psxmod`.
SHA256: `0c9a9fe907206e20d7ca3d71c44185661fecdcd5a542870461b31be51e57f803`.
Town01 primary region0000 retains type4, padding and corners107/127/1; x0
changes58 to59. Independent package readback changes only MAP byte66692. The
minimum X boundary moves7488 to7616 under the source `(world-64)>>7` lookup.
Review, distinct coordinate layers, viewport framing/comparison, one-step Undo,
Redo, Save/Open, retail reset and stale scene cleanup pass offline. Combined
region/scenery/wall Build also preserves its exact combined byte audit.

Later gameplay acceptance should compare the stock region boundary with the
fixture, establish what encoded type4 affects, and verify actual entry/exit,
height and movement continuity. These behaviors remain unknown; the browser
reference plane does not prove activation. No package installed or game launched.
See [region bounds workflow](legaia-region-bounds.md). This adds a later fixture
and does not require immediate manual verification.

## Field source cells and trigger contact - deferred

The private baseline project is `local-output/sdk-20260909/field-spatial-20261002/project/`.
No edits or installable package were produced. Town01 source cell framing,
explicit pick, coincident-row cycling, Inspector/source-script navigation and
scene-change cleanup pass offline. Gate-1 MAP rows resolve 51 source links to22
P2 records, without proving their dispatch or story conditions.

Later gameplay comparison should check trigger tile contact and region boundaries
against the correct quantizers: trigger `world >> 7`, region `(world - 64) >> 7`.
The inspected fallback kind1 row0000 resolves P2[38], with source bounds
X[12416,12544), Z[1280,1408). Its display Y=0 is an inspection plane; retail
height, activation and reachability remain unknown. This does not establish
which trigger executes any particular SCENE_CHANGE. Gate 0 cells are object
lookup keys, not proven player-contact volumes. No game was launched.

## Transition arrival Inspector fixture - deferred

The saved project is `local-output/sdk-20260909/transition-assets-20261002/project/`.
Package: `local-output/sdk-20260909/transition-assets-20261002/authored-build/legaia.sdk.0f096fa3c17d-0.1.0-50a14a259788567b.psxmod`.
SHA256: `7277e4d50b88a668386beab8f707f6616be894a2b4e11e7a52b9591100a27a46`.
Town01 P2[0], PC0x16 retains encoded destination map01 and Z3264; authored X
is128 (from12352), facing1024 (from2048). Independent package MAN readback
changes only28574 (96 to128) and28576 (4 to2); Save/Open reproduces the package.
The shared transition Inspector, source navigation, guarded destination
navigation, operand layers and history/persistence passed offline browser checks.

Remaining gameplay acceptance is to identify and traverse the actual source
trigger, verify map01 arrival/facing and scene/script continuity, and compare a
retail baseline. The source trigger location is unresolved; encoded arrival is
not its location. No package was installed and no game was launched. This adds a
fixture to the existing transition-arrival gate rather than requiring immediate
manual verification. See [transition assets](legaia-transition-assets.md).

## Initial animation assignment — deferred

The saved fixture is
`local-output/sdk-20260909/actor-animation-assignment-20261002/project/`.
Package inside it:
`Builds/initial-animation-verification/legaia.sdk.0f096fa3c17d-0.1.0-1ee1fc4c87dcc868.psxmod`.
SHA256: `8352ed3e3d0cb287091e657b344d0ebfa036ec85f266c2f83649ca78bb52e9cc`.
Town0b actor0019 retains model0102 and its imported position, with initial
animation byte14→13 (ANM record13/15frames→record12/30frames), qualified by
same-model actor0049. Independent MAN readback differs only at9471; source
record12 digest, exact fresh import and unchanged saved project bytes verified.
The browser applies the assignment to the target; channel edits still own their
imported shared clip. No package was installed and no game launched.

When manual verification resumes, establish the actual Town0b scene and intended
actor/script branch first. Check scene entry, whether scripts replace the initial
clip, visual suitability/looping, interaction and progression, and scene exit.
A correct initial header and offline pose do not prove runtime timing or branch
execution. No immediate manual check is required; other offline work may continue.
See [workflow and scope](legaia-initial-animation-assignment.md).


## Mixed viewport-drag placement — deferred

The exact copied-project path is recorded in
`local-output/sdk-20260909/scene-placement-drag-20261001/prepared.json`.
Package within that project:
`Builds/e15173dcb8d4b4e7/legaia.sdk.2899fc3afad4-0.1.0-e15173dcb8d4b4e7.psxmod`.
SHA256: `caf02c24b52e375563bc4a904f6601684a7acfcac236d47a18b94c83294c84f2`.
Actor `scene://town01/actors/man-p1/0012` now has X/Z `(3840,1984)`;
decoration `environment://town01/field-map/decorations/01833` `(5705,2240)`.
The reviewed viewport drag added `(64,128)` to both current placements. Prior
actor0001 `(9984,8704)`, unselected scenery/shared rotations, all17 collision edits,
floor tiers and saved selection metadata remain unchanged. Exact MAP ZIP readback
and independent MAN decode passed. No game launched. Use the exact saved package
and an identified interactive runtime to compare visibility, terrain contact,
collision, entry/re-entry and any script-driven replacement of initial actor
placement. Preview height is held; it does not establish runtime Y.

## Mixed actor/static-decoration placement group — deferred

Private copied-project identity is recorded in
`local-output/sdk-20260909/scene-placement-group-20261001/prepared.json`.
Package within that project:
`Builds/327b5af3b3396091/legaia.sdk.98a51b29d3fe-0.1.0-327b5af3b3396091.psxmod`.
SHA256: `3e53d091e78ad808ad3a3164e83ade2ac3985b2780765a391a5b08b913c496d1`.
Actor `scene://town01/actors/man-p1/0001` is authored at X/Z `(9984,8704)`;
decoration `environment://town01/field-map/decorations/01833` at `(5641,2112)`.
Both moved by `(64,64)` from the saved source. Existing 17 wall edits (16 in the
viewport rectangle plus one outside), unselected decorations and shared rotations
remain preserved. Exact full MAP ZIP readback and independent MAN decoding passed.
Manual verification must use this saved project, package and an identified runtime.
Check both placements, terrain contact, collision interaction, scene entry and
whether actor scripts replace initial placement. Undo/revert should restore both
kinds together while existing wall edits remain intact. Proposal height is held
and does not establish runtime Y. No game launched.
See [Mixed placement workflow](legaia-scene-placement-groups.md).

## Town01 viewport-selected source walls — deferred

Private copied project path: `local-output/sdk-20260909/wall-viewport-20261001/prepared.json`
contains the exact `project` directory.
Package within that project:
`Builds/39bd3cdfa55cdd03/legaia.sdk.44ca503d8301-0.1.0-39bd3cdfa55cdd03.psxmod`.
SHA256: `a8e9c953747947da0a147e6aeff86ce26c5c44fc322ff6b3cd68c09d4a3bd012`.
Viewport drag authored all16 source wall bits in rows15–16, columns20–21:
reference X `(2560,2816]`, Z `[1792,2048)`. One previous outside wall bit and
saved scenery distribution remain preserved; full MAP byte readback passed.
Source-plane Y0 does not establish floor height. Actual movement, runtime paints,
actor blockers, scene-entry and lifecycle acceptance remain deferred. No game
launched. See [Viewport wall workflow](legaia-collision-rectangles.md).

## Town01 scenery distribution copy — deferred

Private project:
`local-output/sdk-20260909/scenery-group-20261001/project/ProjectCopies/project-e94a1a3e9c7549098a2fcce4b2167aed/ProjectCopies/project-7e22aae86c724d9ab4457e65276fa720/`.
Package: `Builds/c020258ae4210ec6/legaia.sdk.9708e254159b-0.1.0-c020258ae4210ec6.psxmod`.
SHA256: `75d11678520b6acb2f4b21987436a8f21390f5cf1575b0db65dc2d5de8e0a055`.
This copies the saved group drag project and distributes decoration cells1833,
2089,2345 along Z: final X/Z5577/2048,5577/2208,5312/2368 respectively.
Existing shared transforms, selected Y/rotation, collision and floor tiers are
preserved. Offline review/browser/history/persistence/full MAP checks passed;
visibility, collision interaction, scene-entry/scripts and lifecycle remain
unverified. No game launched. See [Scenery groups](legaia-scenery-groups.md).

## Town01 scenery group drag copy — deferred

Private copied project:
`local-output/sdk-20260909/scenery-group-20261001/project/ProjectCopies/project-e94a1a3e9c7549098a2fcce4b2167aed/`.
Package: `Builds/8d426bc1dcefbc5f/legaia.sdk.d9a4c92650c7-0.1.0-8d426bc1dcefbc5f.psxmod`.
SHA256: `d5ce6e02dc710814a1fa015b2634eabbac3cba951ddd218de63dc032241eacc2`.
The copied previous group edit was offset another X+73/Z+128 via reviewed drag.
Final source world X/Z: cell1833=5577/2048, cell2089=5577/2272. Existing shared
record194 X64/Y-rotation64, cell2089 baseline Z32, source wall bit and floor tiers
remain preserved. Offline pointer/review/history/persistence/full MAP checks
passed. Defer in-game visibility, collision, scene-entry/scripts and lifecycle.
No game launched. See [Scenery groups](legaia-scenery-groups.md).

## Town01 static scenery group placement — deferred

Private project: `local-output/sdk-20260909/scenery-group-20261001/project/`.
Package: `Builds/b00ea72e47be4add/legaia.sdk.0f096fa3c17d-0.1.0-b00ea72e47be4add.psxmod`.
SHA256: `eca7822f30607c925c345ad825a1075331167b8d0b042c35b54104f3df25f4f4`.
Cells1833 and2089 reviewed/applied X+128 / Z+64 relative to existing authored
placements; record194 shared X64/Y-rotation64, cell2089 existing Z32 and one
source wall bit were preserved. Offline source/preview/history/persistence/full
MAP package checks passed. Defer visible placement, collision interaction,
scene-entry/script behavior and lifecycle acceptance. No game launched.
See [Scenery group workflow](legaia-scenery-groups.md).

## Town01 rectangular source walls — deferred

Private project: `local-output/sdk-20260909/collision-rectangle-20261001/project-final/`.
Package: `Builds/ab02650b81407720/legaia.sdk.0f096fa3c17d-0.1.0-ab02650b81407720.psxmod`.
SHA256: `63176d4fd5b8b5bc89bbcf199ca25148e84543568b301a5de3d3d9af9ddefed1`.
Rows15–16, columns20–21, all quadrants changed from unblocked to blocked:16 source
wall bits, guest integer extent X(2560,2816], Z[1792,2048). Browser review/history/
Save and independent complete73728-byte MAP ZIP readback passed; floor tiers
preserved. Deferred checks include scene entry, collision-grid loading and later
script repainting, movement probes and visible behavior at the chosen extent.
No installation or game launch performed. This does not request immediate manual
gameplay verification or imply source walls necessarily survive runtime scripts.

## Normal raw MAN placement in mixed package — deferred

Private saved project: `local-output/sdk-20260909/raw-MAN-normal-build-20261001/project/`.
Package: `Builds/60c1e00eb53ebb09/legaia.sdk.0f096fa3c17d-0.1.0-60c1e00eb53ebb09.psxmod`.
SHA256: `1a2effd3c3f17f30efa9a77a6945bb98ba5b2a458e71dc11950430e0b02f8ef1`.
Dolk2 actor0011 initial X9408→9472 is one raw MAN byte edit; the package also
contains nine preexisting Town01 changes. Exact raw/compressed serialization,
mixed report review, package integrity and browser Build passed. Deferred checks
include Dolk2 scene entry, initial actor position, visibility, collision and
subsequent scripted repositioning, plus mixed-package scene transitions. No
installation or game launch performed. This queue does not request immediate
manual gameplay. NPC drafts are not part of this normal package.

## Combined town01 position/appearance preset — deferred

Private saved project: `local-output/sdk-20260909/component-inspector-20260930/`.
Actor0012 combines X2944, retained Z1856 and donor0005 initial appearance.
Detached no-draft package SHA256:
`a59e32eaf00f07971a0f36eb83ff10529eea908d34dd98404f07042bc6cf6567`.
Full logical experimental archive retaining four drafts SHA256:
`2f9437b5a0eda2ed4ae9eaf8bf810a6f2f9c0936942e1caae8c3c0a818e43381`.
Disk and independent MAN/archive readbacks passed. The saved project still has
all four drafts; normal Build rejects that input, and the logical archive is
not an output disc. Deferred checks include actor initialization/placement,
appearance, interaction, script relocation and visibility/collision. No game
launched or artifact installed.


## Repeated town01 NPC drafts — archive prototype, deferred

Saved project: `local-output/sdk-20260909/draft-repeat-20260930/`.
Prepared logical archive: `repeat-candidate.prot`, SHA256
`b386fb186853a10e445030c3b7f3dc09d2dde1d3faa817acdc6fb6b7f711b262`.
No output disc exists for this prototype; use the existing experimental export
workflow later before manual testing.

Independent disk/archive reopen verified the original at X2880 and three copies
at X2944/3008/3072, all Z5440, appended records53–56 with model105/animation13
and script bytes equal to donor0011. Browser scene comparison and history passed.
The donor script decoder has partial coverage. Deferred checks include scene load,
initialization, visibility, interaction, story scheduling and collision for every
copy. Serialization does not establish these behaviors. No game launched.


## Streaming NPC review project — deferred

Saved project: `local-output/sdk-20260909/streaming-npc-review-20260912/project.legaia.json`.
Export directory inside that project: `Builds/experimental-drafts-00000000000040008000000000000003`.

- `draft.bin`: 466,716,768 bytes; SHA256 `a0e2f44dcfeec3f3ce0f6621eb6390f11001a6c362dd60427fe2f176053386bf`.
- One authored Dolk2 NPC, donor `scene://dolk2/actors/man-p1/0001`, X=64/Z=16320. This is a boundary serialization probe, not a confirmed walkable or visible placement.
- Fresh output-disc inspection found 73 actors and new record 73 at the authored coordinates. Final MAN hash agrees with the report. Export history matches current inputs; disc hash and both retained snapshot files verify.
- Deferred manual checks: load the intended scene, determine whether the new actor initializes and is visible at that coordinate, inspect script-driven relocation/behavior, and confirm no scene-load regression. Successful serialization does not prove spawn scheduling or opaque script paths.
- Open the saved project for review or use Export history's editable-copy action on its retained Inputs. No game has been launched for this artifact.


The user requested on 2026-09-12 that implementation and non-gameplay validation
continue while manual checks are saved for later. This queue does not authorize
launching or controlling the game. A passing archive or browser check does not
close a gameplay item.

New experimental exports also retain `Inputs/project.legaia.json`, imported
evidence and referenced model/TIM replacements. Open that project to recover the
exact authored inputs even after the working project changes. The export report
lists every snapshot file's SHA256 and byte count; the original retail disc is
still required. Older exports listed below predate input snapshot support.

Use **Export history** in the editor toolbar to find this project's experimental
exports and their saved input paths. **Verify saved files** checks the disc hash
and, where available, every input snapshot file against the completion report.
This does not launch the game or mark a gameplay check as passed. History lists
exports under the current project's Builds directory; separately prepared CLI
fixtures in this queue retain their explicit paths below.

For exports with retained inputs, **Open editable copy** verifies and copies those
files into a new project under ReviewCopies, then opens it. Save your current
project and use Edit mode first. Subsequent edits affect the copy; the original
export inputs stay available for reproducing the test.

The toolbar's **Export disc** action exports supported authored changes without
requiring an NPC draft. It uses the same experimental output, input snapshot and
history workflow. CLI callers may omit `--draft` for project-wide export. A
project with no authored changes is rejected; ordinary Build remains the retail
baseline workflow. Export completion still requires later gameplay acceptance.

## Streaming dialogue export probe

- Artifact: `local-output/sdk-20260909/streaming-dialogue-export-20260912/draft.bin`.
- SHA256: `cb8f9914ee04069625b066d7bf043171e5003bc7b62789fdc58065c595ec564f`; 466,714,416 bytes.
- Adjacent report and Inputs snapshot preserve one dolk2 actor0003 text override: run `script://dolk2/actors/man-p1/0003/dialogue/0017/run/0018`, replacement `SDK` plus twelve spaces in its original 15-byte capacity.
- Browser Apply/Undo restored original text and clean state. Exported disc hash, directly reopened MAN text bytes and all snapshot hashes passed independently.
- Deferred manual check: reach the corresponding actor/script branch in dolk2 and verify the changed message, subsequent messages and interaction progression. Branch execution and story prerequisites have not been established by static decoding. No gameplay run has occurred.

## Streaming placement export probe

- Artifact: `local-output/sdk-20260909/streaming-placement-export-20260912/draft.bin`.
- SHA256: `834a22c50b0bc527bd8b9327246ca8c342b34ad82548501e42a3cc47c28f36de`; 466,714,416 bytes.
- Adjacent `report.json` and `Inputs/project.legaia.json` retain the exact export and authored inputs.
- One dolk2 actor-0001 initial placement field changes: X16320 to X64, retaining Z16320. This is a boundary/serialization probe, not an added NPC or a known visible walkable destination. Its script can relocate or hide it.
- Offline verification: independent disc hash, reopened PROT, directly decoded output MAN coordinates X64/Z16320, unchanged TOC, and all snapshot hashes passed. The retail-only project importer intentionally rejects this modified disc.
- Deferred manual check: use this exact disc and an identified runtime; reach dolk2 and inspect actor/script behavior with the live observer when available. Verify scene entry and existing progression remain intact. Do not infer a runtime placement failure solely from not seeing the actor at its encoded initial position.
- Gameplay has not run. Streaming NPC additions, model/texture replacement and other unsupported authored components remain outside this export implementation.

## Ready artifact: added NPC

- Artifact: `local-output/sdk-20260909/saved-draft-export-20260911/draft.bin`.
- Report: adjacent `report.json`.
- SHA256: `f8a75661a02acd537257029a9df9e7e79ec1703b766a942a333e63c217e04f97`.
- Saved project: `local-output/sdk-20260909/actor-draft-persistence-check`.
- Draft: Candidate NPC, donor town01 actor0011, authored X3008/Z5440.
- Offline evidence: exact reopened MAN/PROT, independent output hash, matching
  CLI and browser exports. This artifact contains one draft, not the later
  separate appearance/dialogue/transition composition experiments.
- Manual steps: cold boot this specific disc with an identified runtime; reach
  town01 (Select can skip the prologue); locate the draft using the editor;
  inspect appearance, position, animation and interaction; leave and re-enter;
  check that existing actors, dialogue and scene progression still behave.
- Expected: added actor at the authored initial position, subject to its cloned
  script; no missing original actors or broken transitions. Script relocation
  coverage is incomplete, so any unexpected behavior must be captured rather
  than dismissed as a placement issue.
- Record runtime executable hash, disc hash, location, screenshots and results.

## Features needing a dedicated manual fixture

### Isolated collision fixture available (2026-09-12)

- Disc: `local-output/sdk-20260909/collision-only-export-20260912/draft.bin`.
- SHA256: `f77fb410addd646904208f184b2a1a174f73d9b7378f7fa54c28a25c90822c5d`.
- Adjacent `report.json` and reopenable `Inputs/project.legaia.json` preserve the exact inputs.
- Only authored edit: town01 row30/column30/quadrant0, unblocked to blocked,
  MAP byte20254 bit16. No NPC drafts, model, texture or animation edits.
- Locate center X3872/Z3744. Exact canonical integer bounds are
  `3840 < X <= 3904`, `3712 <= Z < 3776`. Use the editor's coordinate locator
  and Effective collision overlay to inspect the location before gameplay.
- Alternatively open collision wall editing, choose the saved cell under Applied
  wall edits, then click Locate cell in viewport. This browser flow is verified;
  the reference marker uses sampled guest Y-128 here. The grid remains a Y0
  overlay, not a runtime collision surface. Screenshot:
  `local-output/sdk-20260909/collision-terrain-locator-20260912.png`.
- Later manual check: compare approach from each accessible side against the
  unchanged retail disc, leave/re-enter and repeat. Runtime scripts, other
  blockers and floor tiers may affect accessibility; record those observations.
- Final MAP/PROT reopening, independent disc hash, all snapshot-file hashes
  and collision-only project reopen passed. No gameplay was performed.

### Combined integration fixture available (2026-09-12)

`local-output/sdk-20260909/combined-assets-export-20260912/draft.bin`, with adjacent
`report.json`, SHA256 `8e1fd5be2cc845c06aa6293964bd0b581a06d3db5d4c6a86c54d65c9bc0f805f`.
Contains the saved town01 NPC draft, model0105 first vertex-X increment,
clip0012 frame0/object0 translation X100, TIM5/raw/0 last payload byte XOR1,
decoration cell1833 Z-256 and collision row30/column30/quadrant0 toggled.
Final MAP/model/texture/animation carrier checks, MAN/PROT reopening and independent
disc hash passed. This fixture checks combined behavior; its tiny texture/model
changes are serialization probes, not a substitute for visually obvious isolated
acceptance fixtures. Use the NPC steps above, inspect shared clip users and the
wall edit, and record any regressions. No gameplay has been run on this image.

These are implemented within bounded authoring scopes but must have a current,
identified output prepared before asking the user to test them. Historical
packages must not be silently substituted.

| Feature | Manual check | Preparation still needed |
| --- | --- | --- |
| Animation channels | Confirm edited pose and motion throughout playback, shared users and scene reload. | Export a minimal current authored/baseline pair with the exact clip and axes recorded. |
| Model shape | Confirm edited mesh under animation and scene lighting, then baseline restoration. | Export a minimal model-only pair and record model identity and source/output hashes. |
| Collision wall bits | Attempt movement across the exact edited subcell boundaries; compare baseline. | Isolated collision fixture above is ready; baseline is the unchanged retail disc. |
| P2 dialogue | Trigger the edited P2 text, close it and resume normal control. | Build a minimal fixture with the owning trigger, text and expected interaction documented. |
| Transition arrival | Traverse the exact source trigger and inspect destination arrival/facing. | Build a minimal arrival-only pair; preserve destination name and record encoded values. |
| Combined draft edits | Check original actor edits plus added NPC behavior together. | The combined integration disc above is ready; isolated visible edits still need dedicated fixtures. |
| Stability and restores | Check field/cross-scene restore, controller behavior, battle/audio cases. | Use the per-fix provenance and acceptance gaps in `legaia-release-parity.md`. |

The previously user-confirmed wall gap and bounded actor49 appearance/dialogue
acceptance remain recorded in the feature matrix. Do not repeat those checks
without a changed build or a specific unresolved behavior.

## Work that continues independently

- Complete authored asset/container composition and multi-scene draft export.
- Preserve report provenance and expose completed artifacts coherently in the editor.
- Expand supported editor tools and source-backed inspection from the original SDK requirements.
- Validate commands, history, persistence, source preservation, serialization and browser behavior.
- Prepare minimal manual fixtures as their implementation reaches that boundary.


### Deferred: script movement plus NPC composition (2026-09-12)

Private package: `local-output/sdk-20260909/movement-disc-20260912/Export/draft.bin`.
SHA256: `2b9a12bdffbaebf93941623e35b3ba5afc77157ae2b2e35ab3c8fb6e20faccce`.
The adjacent report and Inputs snapshot preserve the authored state.

Contains Dolk2 actor0002 MOVE_TO PC0x27 target X9408/Z10816, town01 actor0011
NPC_RUN PC0x23 target X9728/Z8640, and one Dolk2 donor0001 NPC at X64/Z16320.
Rebuilt PROT readback passed. No game was launched. These are script targets,
not initial actor positions; a reproducible trigger/story-state setup remains
to be established before gameplay can verify either target. NPC scheduling,
visibility, interactions and the proposed location's walkability remain unverified.


## Animation repeated-channel review — deferred

Saved project: `local-output/sdk-20260909/animation-range-project-20260912/project.legaia.json`.
Package: `Builds/3f58c4c8568e7f56/legaia.sdk.0f096fa3c17d-0.1.0-3f58c4c8568e7f56.psxmod` under that project.
SHA256: `9ee1bf808795d71e5bc26af514b7977962e3a64f07cec6f0cb471c569dd73ebf`.

The probe edits town01 scene clip0012, object0: frame0 X123 and full copied channel values on frames1..3. This is a serialization/authoring probe, not a finished animation design. Six scalar differences fit one41595-byte animation overlay; Save/Open and30 sampled frame/object comparisons passed. The source clip is shared by actors0011,0012,0016,0028,0044,0046. Confirm scene/clip activation, visible motion, other shared users and scene transitions when gameplay verification resumes. Timing is not established by this source edit. No game has been launched for this package.


## Readable animation JSON import probe (2026-09-12)

Saved private project: `local-output/sdk-20260909/animation-json-project-20260912`.
Package: `Builds/13bfaa4efe06bfb6/legaia.sdk.0f096fa3c17d-0.1.0-13bfaa4efe06bfb6.psxmod`.
SHA256: `69e7af4585f4c2334c2ed2e1374d2a27e156faab49edb8e6c0b0153e2f29db9d`.
This is a diagnostic probe, not a finished animation: town01 actor0011 contributes
frame2/object0 translation X202 and rotation Y64 to shared clip0012. Other users
of the clip may visibly change. Offline JSON round trips, browser import/Undo,
Save/Open and a two-axis package report passed. Later manual acceptance should
check animation playback and shared users; source cadence and visual suitability
remain unverified. No installation or game launch was performed.


## Model JSON serialization probes (2026-09-12)

These are diagnostic serialization probes, not finished asset edits. No game
launch or installation was performed.

- Normal-only project: `local-output/sdk-20260909/model-normal-json-project-20260912`.
  Package: `Builds/c64c73463d58702f/legaia.sdk.f29d5595fa1c-0.1.0-c64c73463d58702f.psxmod`.
  SHA256 `1c2d835a46053f748f8473324fa220b0d9f80d0145504c919820bfbde4cb4106`.
  Town01 model0009, object1, normal0, X changes0->1. Independent ZIP decode
  recovered the exact replacement TMD; all other model bytes remain unchanged.
  This tiny word change is not expected to guarantee a visible lighting change.
  Runtime normal use, lighting and affected instances remain unverified.
- Combined project: `local-output/sdk-20260909/model-json-project-20260912`.
  Package: `Builds/5ebfeaccd1190c99/legaia.sdk.0f096fa3c17d-0.1.0-5ebfeaccd1190c99.psxmod`.
  SHA256 `edbbf6d15f598358abb5b68960fa28575f8ca5a71cd9c656e8b0e45f76750c4a`.
  Includes model0000's first-vertex X+1 and the earlier actor0011 animation probe
  (frame2/object0 X202 and rotationY64). Both decoded package streams matched
  their audited hashes. Keep these combined effects in mind during later checks.

## NPC_RUN selector serialization probe (2026-09-30)

Private project: `local-output/sdk-20260909/move-selector-project-20260930`.
Package: `Builds/cfb671e4145eec59/legaia.sdk.1ab152598197-0.1.0-cfb671e4145eec59.psxmod`.
SHA256 `4e11fb952ea4767a18b6f909c4b9edecef2865b6c78a823866984712ead6c3c3`.
Actor0011, NPC_RUN at PC0x23, selector13->14. Independent archive decode
confirmed exactly one MAN-byte change at7951; coordinates and depth preserved.
This is a diagnostic byte-serialization probe. No selector behavior, animation
identity, speed or reachable branch is established; it is not a finished mod.
Manual acceptance must establish selector meaning and observe the relevant
executed script before drawing behavior conclusions. No launch/installation
was performed; gameplay remains deferred.

## EXEC_MOVE selector serialization probe (2026-09-30)

Private project: `local-output/sdk-20260909/exec-move-project-20260930`.
Package: `Builds/568af58d0e3b08f8/legaia.sdk.ab8d8f268668-0.1.0-568af58d0e3b08f8.psxmod`.
SHA256 `8c2e76ed649965bb1b216c987f0be003b6fd517eef398ca8fef687d4296d844c`.
Town01 actor0003 EXEC_MOVE at PC0x12: selector9->10. Independent package
readback found exactly MAN byte4816 changed. This is an isolated diagnostic
serialization probe, not a finished behavior edit. Selector/table meaning,
executed branch and resulting playback require later gameplay investigation.
No launch/installation performed.

## Palette-entry serialization probe (2026-09-30)

Private project: `local-output/sdk-20260909/palette-project-20260930`.
Package: `Builds/424d0ff175d0abb2/legaia.sdk.ed30c97ac66f-0.1.0-424d0ff175d0abb2.psxmod`.
SHA256 `591932a1a3acea7897f6a10334fb6459ecd511e0751859352dbbc5577e0dfbcc`.
Texture `texture://town01/5/raw/0`, palette0 entry1, word5386->5387. Only TIM
byte22 differs from retail; actual ZIP member equals authored TIM. This tiny
RGB5-word probe is diagnostic, not a finished texture edit or guaranteed
visible change. Runtime material users, residency and palette/blend behavior
remain unverified. No game launch or installation performed.

## Indexed pixel serialization probe (2026-09-30)

Private project: `local-output/sdk-20260909/pixel-project-20260930`.
Package: `Builds/8f6aa3069ff2baa3/legaia.sdk.a90ea2239c4b-0.1.0-8f6aa3069ff2baa3.psxmod`.
SHA256 `fb310f7a53040b1393ebb068d3b1bcf5993bae17c39cf0d59fcc7af2454df1bc`.
Texture `texture://town01/5/raw/0`, pixel X1 Y0, encoded index13->14.
Only TIM byte544 changed; the other packed nibble and all palettes/header
bytes remain unchanged. Actual ZIP member equals authored TIM. Diagnostic
one-pixel probe, not a finished texture edit. Affected runtime users, residency
and actual visibility remain unverified. No game launch or installation.

## Indexed texture JSON serialization probe (2026-09-30)

Private project: `local-output/sdk-20260909/texture-json-project-20260930`.
Package: `Builds/6f9cafc6ca0f8331/legaia.sdk.9a55c316dc66-0.1.0-6f9cafc6ca0f8331.psxmod`.
SHA256 `f168c11a83dfd51f28e465585c1ec360cdf6dc591936b90cdcac25cd185a3f79`.
Texture `texture://town01/5/raw/0`: palette0 entry1 word5386->5387, and
pixel X1Y0 index13->14. Only TIM bytes22/544 changed. Actual ZIP member
equals the authored TIM; JSON effective values retain the retail source hash.
Combined diagnostic serialization probe, not a finished texture edit or
verified visible change. Runtime users/residency/blends remain unverified.
No game launch or installation.


2026-09-30 texture audit diagnostic (offline only): private project
`local-output/sdk-20260909/texture-audit-project-20260930`, texture
`texture://town01/5/raw/0`, palette0 entry1 word5386→5387 and pixel(1,0)
index13→14, only TIM bytes22/544 changed. Package
`Builds/9fa9adc820268690/legaia.sdk.9a55c316dc66-0.1.0-9fa9adc820268690.psxmod`,
SHA-256 `f4b5ec9b4a6473219c1fe7069bb17ae7b7d4ddfac47901593461a214e33b5175`.
Actual ZIP member matches payload audit; browser report/pixel navigation and
stale rejection passed. This is a serialization probe, not a finished visual
mod. No game launched or package installed. Visible materials, active palette
and runtime residency remain deferred with the other texture probes.


2026-09-30 rectangle fill diagnostic (offline only): private project
`local-output/sdk-20260909/texture-rectangle-project-20260930`, texture
`texture://town01/5/raw/0`, fill X3…5 / Y1…2 with index14, composed with the
previous palette word5386→5387 and pixel(1,0)13→14 probe. All pixels outside
the rectangle and palette words were checked against the pre-fill effective
texture; Undo/Redo, Save/Open and actual ZIP member readback passed. Package
`Builds/c2a23ad8ef7308ca/legaia.sdk.9a55c316dc66-0.1.0-c2a23ad8ef7308ca.psxmod`,
SHA-256 `004599994c11e8db2dec4ea969a815afc97e3d36f5883c20c56f37264b5a5142`.
Browser draft, invalid bounds, Discard, Apply and Undo passed. This is a
serialization diagnostic, not a finished visual mod. No game launched or
package installed; visible materials, active palette and residency are deferred.


2026-09-30 object rotation diagnostic (offline only): private project
`local-output/sdk-20260909/model-rotation-project-20260930-verified`, model
`asset://town01/models/scene-tmd/0009`, object1 +90° around source-local X,
vertices/normals(x,y,z)→(x,−z,y), composed with the existing normal-X probe.
Other objects, layout/padding and vector lengths preserved; stale writes,
Undo/Redo, Save/Open and independently decompressed ZIP TMD readback passed.
Package `Builds/06cc352ef59b38db/legaia.sdk.f29d5595fa1c-0.1.0-06cc352ef59b38db.psxmod`,
SHA-256 `832d626b1b75bd17f4b71304f2c45e6d95e7304839c90af63068fcf2a29e60bf`.
Browser temporary Z rotation, vector draft guard, Discard and exact Undo passed.
This is a serialization diagnostic, not a finished visual mod. No game launched
or package installed. Gameplay shape/lighting and animation compatibility remain
deferred; the browser does not calculate normal-based lighting.


Deferred flag operand diagnostic (2026-09-30): private project
local-output/sdk-20260909/flag-authoring-project-20260930 contains town01 actor0002
CFLAG_SET PC0x000C bit2-to3. Package under Builds/flag-output-verified has SHA256
adeeb217b679908845e4e9e260e31b3d22cccceb3fc0f63ab33fd502459c99bf.
Independent ZIP/decode readback proves the single intended MAN byte4772 change.
This is a serialization diagnostic, not a story mod or a proven visible change.
Do not infer flag meaning or launch automatically. Gameplay/story execution and
runtime compatibility remain deferred. Compressed NPC append readback and raw
streaming composition passed offline; editor Apply is still pending.


Deferred wait operand diagnostic (2026-09-30): saved private project
local-output/sdk-20260909/wait-authoring-project-20260930 contains town01 actor0044
WAIT_FRAMES PC0x019F16-to17 ticks plus actor0002 CFLAG_SET2-to3. Package under
Builds/89f66b995f838276 has SHA256
148ab35c0b9146cab17359b9a870ab054c95aa98c415a7b26be199992da50971.
Independent ZIP readback confirms only MAN offsets4772 and24483 changed; compressed
NPC append readback retained the wait at24486. This diagnostic is not a finished
story mod or proven perceptible timing difference. Manual execution/timing and
runtime compatibility are deferred; do not launch automatically.


Deferred model scale diagnostic (2026-09-30): saved private project
local-output/sdk-20260909/model-scale-project-20260930 scales model0009 object1
vertices150% around the source-local origin, composing prior rotation/normal
edits. Normals and other objects retain their pre-scale values. Package under
Builds/e7728cba624de600 has SHA256
9d16d794517133d474921f7e001f9dd1929cc43f51df2ff8c33aca89f09aa3cb.
ZIP decoded-carrier readback, Undo/Redo, Save/Open and browser Apply/Undo passed.
This is a geometry diagnostic, not a finished mod. Rendering, animation and
collision compatibility remain for manual verification; no automatic launch.


## September 30 — Indexed texture rectangle copy probe

Saved private project: `local-output/sdk-20260909/texture-copy-project-20260930/`.
Texture `texture://town01/5/raw/29`,4-bpp256×256, copied3×2 from(0,0) to(1,0)
with overlapping source/destination. Three pixel indices/image bytes changed,
zero palette words; all surrounding pixels and source layout unchanged. The
copied project also retains its existing model override; this is a composed
package, not a texture-only baseline. Save/reopen, exact Undo/Redo, no-op history
and independent package TIM readback passed. No game launched.

Package: `Builds/e11d13216555bd72/legaia.sdk.f29d5595fa1c-0.1.0-e11d13216555bd72.psxmod`.
SHA256: `ec8bd5c42a995f0772842aab1ff7bd8ad82b78d45409bb38452ccdfd8c23b614`.
TIM SHA256: `8ef191b30f8307f6f1129265ea89bc90948f02bf575e5009e708235e4754713c`.
Evidence: `copy-check.json`, `copy-package-readback.json`, `expected-copy.json`.

Later verification should confirm runtime consumption of the exact TIM and
appearance of affected materials where that atlas region is used. Static
associations do not establish runtime VRAM residency; a tiny atlas probe may
require byte inspection rather than an obvious visual difference. Gameplay
verification remains deferred until the user elects to perform it.


## Field menu label source probe — 2026-09-30, deferred

Saved project: `local-output/sdk-20260909/menu-label-project-20260930/project.legaia.json`.
Package: `Builds/d91ec96d0b439b7e/legaia.sdk.59e13c627546-0.1.0-d91ec96d0b439b7e.psxmod`
inside that project; SHA256 `acf25ce12a487fb23aa4128f242fb19842d8bb0ba0f2cb5db21a339ca87bcec4`.

Town01 actor0001 picker0x6B, option0 plain run0x75 has a six-byte source span;
replacement `SDK` retains three spaces. Source jump entry/target and every
outside byte are unchanged. Saved-project reopen, retail browser workflow and
independent package ZIP/LZS readback passed (`package-readback.json`).

This actor's source menu is not established as reachable during ordinary
play. The artifact is a serialization review probe. Later gameplay acceptance
requires an evidenced reachable menu in the intended story state, then visual
label/font/wrapping inspection and confirmation that all choices retain their
original behavior. No game launch or manual verification is requested now.


## Text-file multi-label source probe — 2026-09-30, deferred

Saved project: `local-output/sdk-20260909/text-json-project-20260930/project.legaia.json`.
Package inside that project:
`Builds/0010e9bffbcfadef/legaia.sdk.b344e5758277-0.1.0-0010e9bffbcfadef.psxmod`;
SHA256 `86a89fd5deff5ce9bbf113fce26c864085481604831bfd9b32a731db8c975bd4`.

Text JSON atomically added two source-menu label overrides to the earlier
actor0001 override. Browser preview/no-write, Apply/Undo/Redo/Save and reopened
package readback passed. Three authored glyph runs match expected MAN exactly.
`browser-check.json`, `late-read-check.json`, `package-readback.json` and
`text-file-preview-final.png` retain offline evidence. This source menu's story
reachability remains unproven; it is not a claimed normal-gameplay checkpoint.
Later visible label/font/selection verification still requires an evidenced
reachable menu. No game launch or immediate manual check is requested.

## Script model selectors - manual acceptance pending

Private town01 selector/menu package SHA256
`228abd8eea3d71114f5401b7897c12109a5d257130474757d51e5b1dfe9ebaac`
is retained under `local-output/sdk-20260909/model-selector-town01-20260930/`.
Actor0003 selector at PC0x0C changes241 to240; three earlier debug-like menu
labels remain composed and their normal-play reachability is unproven. The
Dolk2 actor0002 saved project and logical rebuilt-archive evidence are under
`model-selector-project-20260930/`; a playable disc was not emitted/installed.
When manual verification resumes, establish which source branch executes,
resolve the runtime pool/actual asset, and verify restaging, draw/movement and
animation behavior through a matching cold build. No predicted character identity
is supplied by the numeric selector. Offline bytes/history/persistence and
package/candidate exactness do not prove runtime behavior. No game was launched.

## Actor group placement offsets — deferred 2026-09-30

Private actor-batch-project-20260930 package SHA256
`cf2f42b2604cca3e3fccfdb778c0934e94ab00942df0fcff366f3ce87ed196c0`
contains town01 actor0001/0002 effective X/Z offsets +64 each, alongside the
existing three menu edits and actor0003 selector240. Offline exact MAN readback
is verified. Later gameplay must establish actor reachability/visibility,
collision and whether scripts override the initial placements. No package has
been installed and no game launch is authorized for this offline pass.

## Town01 actor group appearance — deferred 2026-09-30

Saved private project: `local-output/sdk-20260909/group-appearance-20260930/project.legaia.json`.
Built package: `local-output/sdk-20260909/group-appearance-20260930/Builds/5b08a0ee13d82bd9/legaia.sdk.0f096fa3c17d-0.1.0-5b08a0ee13d82bd9.psxmod`.
SHA256: `20146bacf0784539e79cf6a531cbd154ff921016895d8fe47ebd8e4b27b76be6`.

Actors0011/0012 use donor0005's verified initial model0112/animation57. Package
MAN readback matched the exact expected source, preserving existing position,
menu and selector edits. Deferred manual checks: confirm both intended actors
initialize/render/animate with the donor pair and that scene movement/transitions
and script behavior remain usable. No game launched or package installed for
this artifact. Browser/package checks do not close these gameplay items.

## Actor group layout package - deferred 2026-09-30

Private saved project: `local-output/sdk-20260909/group-layout-20260930/`.
Actor0011/0012/0013 Distribute Z retains endpoint1856/5440 and changes actor0013
from2880 to3648; its X stays3776. Source initial donor0005 assignments on0011/0012,
earlier placement changes, three menus and selector240 are retained. Independent
full MAN ZIP/LZS readback and parsed actor coordinates passed; package SHA256
`9469e6b0ba790f166e6f7b540887ee15cde09d60a1c6a0e749d118038724c00f`.
See the private group-layout-package-check.json for the exact generated package.
Manual review later should check initial location, script relocation/visibility
and collision/walkability of the moved actor. Alignment is browser/Undo verified;
its transient proposal was undone before this saved package. No game launched or
package installed. This queue does not authorize a game launch.
