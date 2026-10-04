# Persistent native animation record allocation

Raw streaming ANM delivery now has native transforms in
`importer/streaming_animation_bank.py`. `grow_streaming_animation_bank` qualifies
the carrier hash, typed chunk-header offset, original bank hash and candidate
bank. It requires a terminated chunk chain, type 5, word-aligned nonshrinking
payloads (at most 4 MiB) and a final carrier at most 16 MiB. The existing bank
qualifier preserves Retail ordinals, opaque table padding and unsupported old
records while admitting qualified existing axes and up to 64 appended records
within the cumulative 4096-channel limit. Only the bank header/payload and following
chunk positions change; all declared opaque neighbor bytes must survive. An
odd-sized preceding payload that overlaps the changed header causes rejection.

`rebuild_streaming_animation_bank_entry` binds this transform to a unique physical
PROT owner, rounds its allocation to sectors, relocates the TOC and reopens the
exact emitted carrier/chunk chain. Its audit records `relocated_chunks` with
before/after offsets, types and byte lengths. MAN/ANM edits in one owner must use
these verified offsets after the first growth; old header offsets are unsafe.
Synthetic native tests cover both orders and prove identical output after explicit
remapping, including native NPC MAN append and unchanged archive neighbors.

The codec does not yet participate in SDK animation growth requests or normal
Build/Export disc. Those integrations and managed streaming assignment remain
pending; the current raw-bank restriction stays in place until complete locator
composition and final readback are connected. No Retail timing, runtime pointer
behavior or gameplay acceptance is inferred from this native readback.

Experimental **Export disc** now delivers retained allocated banks through
qualified compressed ANM carriers together with ordinary MAN edits and appended
NPC records. It uses the same managed native assignment serializer as normal
Build: authored UUID/hash references resolve into qualified appended ordinals,
and the assigned original actor header stays distinct from a new donor NPC copy.
The selected-NPC shortcut is bypassed whenever a retained ledger is present, so
scene-owned allocation cannot be dropped or sent to the unmanaged path.

Project export first composes original-address asset patches, prepares the fully
qualified retained bank once, relocates compressed ANM carriers, then rebuilds
MAN owners. `animation_growth.final_archive_banks` records exact final bank hashes
and record counts after MAN relocation; `animation_container` records archive
resource composition. The source disc identity is checked again before bank
preparation. Shared table owners are supported when owner-relative tables remain
qualified through both operations. Raw streaming ANM and relocation that requires
remapping distinct tables inside a physical owner remain unsupported and fail
before a successful export report. Other existing Export disc limitations remain.

Synthetic routing and real native archive/Mode 2 writer smoke verify expanded
bank plus appended MAN content, preserved authored payload patches, final exact
readback and unchanged input. Source preparation is substituted in that smoke;
no Retail full-disc export or gameplay acceptance is claimed. Exported discs are
experimental; current runtime/gameplay verification remains on the deferred queue.

**Manage allocated clips → Edit retained GLB** supports external channel editing
of a saved active or retired capture. Choose an explicit 1–120 export FPS,
Prepare retained GLB export, and download both the GLB and binding JSON. Preserve
the rigid `object-N` nodes; the unchanged sidecar qualifies the current scene,
saved UUID/content hash, frozen donor, object count and interchange rate. Choose
the edited GLB (maximum 32 MiB) and sidecar (maximum 128 KiB), then specify the
output mapping into frozen captured-donor frames. It defaults to the saved mapping
and can repeat, reorder, grow or shorten within the native ledger budget. The
mapping sets output frame count and opaque native channel data; it is not inferred
from GLB duration. Shortened files must fit that chosen output duration.

Review GLB content samples object-local channels at `float32(i/binding_fps)` with
STEP, LINEAR or CUBICSPLINE interpolation and endpoint hold. The codec reverses
`[x,-y,z]`, rounds translation to native integers and quantizes rotation on the
existing byte-angle grid; the Review displays quantization error and referring
actor count. Same-mapping imports use existing retained content as the angular
baseline; changed mappings inherit captured donor frames before file sampling.
Mesh edits are ignored. No extra rigid objects, skinning or hierarchy is allocated.
The chosen rate does not establish Retail playback timing.

Preview reviewed GLB content opens the proposed pose over Current geometry and
returns to the same Review. Apply reviewed GLB content replays the exact file,
binding and mapping, preserves UUID/donor/retirement, and updates content hash and
initial references together through ordinary Undo/Redo. Save persists the result.
Changing files, mapping or source invalidates Review. Unchanged imports add no
history; unapplied content cannot be exported as an applied clip.

Full saved or current-assigned exports through `/api/export/allocated-animation`
now include `.binding.json` beside the GLB, plus `binding`, `binding_path`,
`binding_filename` and `glb_base64` in the response. Initial-assignment proposals
and posed-frame exports have no content-import sidecar. The binding schema is
`legaia.animation-record-glb-binding.v1`.

`POST /api/animation-record-glb-review` takes exactly `scene_id`, `record_id`,
`source_frame_indices`, `expected_source_key`, `binding`, `glb_base64`.
`/api/animation-record-glb-pose` and `/api/animation-record-glb-import` additionally
require the returned `review_key`. The Review exposes GLB analysis, the qualified
native content request and native Review; Apply requalifies all referenced actor
headers. Browser and Retail smoke cover this workflow; gameplay remains deferred.

The actor inspector's **Manage allocated clips → Edit retained content** opens
an editor for the selected saved capture, including retired captures. Frame mapping
uses the frozen captured donor's indices; comma-separated indices and inclusive
ranges can repeat, reorder, shorten or extend the output within the displayed
frame budget. Select a mapped output frame and rigid object, then enter native
integer translation (-2048–2047) or rotation (0–4080, steps of 16) axes. Blank axes
inherit that captured frame. Contributions replace the retained edit, so clearing
an axis restores inherited content. Shortening a mapping does not silently discard
out-of-range channel contributions; correct those drafts before Review.

**Review retained edit** validates native reconstruction and all initial actor
references without changing the project. **Preview reviewed content** opens the
proposed pose over Current geometry; closing it returns to the same reviewed form.
**Apply reviewed content** preserves the record UUID and captured donor, updates
its content hash and referring actors in one ordinary Undo entry, and keeps a
retired record retired. Save persists the result. Draft/source changes invalidate
Review; content export is available after Apply. The options endpoint is
`POST /api/animation-record-edit-options` with exactly `scene_id`, `record_id`
and `expected_source_key`; it returns verified capture metadata, native frame
budget, revision availability and referring actor identities, without payload bytes.
Retained GLB content import is available through the file workflow above. Preview rate is a user setting;
Retail timing and gameplay are not claimed verified.

The SDK can construct new rigid animation records from a verified donor and
review the proposed expanded native bank through
`POST /api/animation-record-allocation-preview`, then Apply the exact request and
`review_key` through `POST /api/animation-record-allocation`. Allocation is stored
in a scene-owned `AnimationRecords` component with ordinary Undo/Redo and
Save/Open. The editor now exposes creation, Review, posed Preview and explicit
Apply. Normal Build delivers expanded banks in qualified compressed ANM carriers.
Persistent initial actor assignment is available through reviewed APIs and scene
Preview, editor Review/Apply/clear and normal Build for qualified compressed
carriers; raw streaming bank relocation remains unavailable.
Existing GLB channel import remains a separate complete
workflow for fixed-layout clips.

The request contains exactly `entity_id`, `expected_source_key`,
`source_frame_indices` and `edits`. The source key is the current
`scene_preview_source_key`. The actor must be imported in the active scene in
Edit mode. Initial appearance/animation assignments resolve the actual model and
clip witnesses; all current shared channel contributions are composed before
donor frames are copied. Fresh disc evidence must match imported metadata.

`source_frame_indices` is an explicit nonempty sequence of donor frame indices.
It can repeat, reorder, shorten or extend a clip, without assuming a cadence or
creating neutral poses. `edits` uses the existing exact integer axis format with
indices into the new sequence. Each new channel inherits the selected donor's
opaque nibble. Donor object count, header mode/flags and trailer are preserved;
only the frame-count word and requested known axes change within the new record.

The native bank starts with a u32 count and absolute u32 offsets. Appending records
grows that table, rebases existing offsets, preserves opaque table padding and
keeps every existing record byte and ordinal unchanged. Only a selected donor
must be decodable; unsupported neighboring records are retained without guessing
their formats. Readback checks the complete reconstructed table and each old/new
record. The implementation follows the pinned `player_anm.rs` layout at
`d6e64c68ede25813d35db20980da82a1a025549b`.

The v2 review carries source/effective/candidate bank hashes, donor provenance,
per-record old/new offsets, exact frame mappings, axis audit and a review key.
An authored animation URI uses a canonical UUIDv4 identity derived deterministically
from the request/source context. Apply persists it as the clip's durable project
identity; the native table ordinal can change independently. Changing
source/ownership or the request invalidates the previous review. No review
creates files, overrides or history, and Apply independently replays the proposed
ledger before publishing one history entry.

The `legaia.animation-record-ledger.v1` stores Retail bank/record preimages,
source actor/model/clip witnesses, the donor's captured exact axis contribution,
frame sequence, requested new axes and the allocated record hash. It contains no
raw Retail record bytes. Replay reconstructs the captured donor against Retail,
then allocates the new record. Later shared channel edits affect the existing
source clip without changing the independently allocated clip. Scene source keys
include the ledger, so Apply invalidates old reviews. Authored asset/component
reviews expose the scene's allocated clip settings.

`POST /api/animation-record-activation-preview` reviews retirement/restoration;
`POST /api/animation-record-activation` applies its matching `review_key`. Both
accept `scene_id`, retained `record_id`, exact boolean `active` and
`expected_source_key`. Retired entries remain in the ledger with their complete
capture and reserved UUID. Undo/Redo or restoration keeps that identity and bytes;
only native ordinals rebase. Resetting the entire authored scene component is a
separate intentional return to the Retail layer.

Bounds are 64 records and 4096 allocated channels per batch, 512 frames per
record, 64 donor objects, 4096 native bank records and 4 MiB total decoded bytes.
The project ledger also bounds cumulative allocated channels to 4096, retained
identities (including retired clips) to 64, revisions to 64 and metadata to 2 MiB.
Source frame/object indices, UUIDs, exact axis values, schemas and preimages are
validated before publication. Open/Save validate metadata structure offline;
composition, Apply and Build additionally verify disc/model witnesses and exact
record replay. Opening metadata without the disc does not prove payload validity.

On 2026-10-04, 32 focused native, SDK HTTP, ledger and existing GLB numerical
checks passed. Retail Town01 grows from 69 to 71 records across two allocations,
then returns to 70 when a clip is retired. Every existing record is preserved;
expanded banks round-trip through independent LZS decompression. SDK checks cover
effective shared edits, assigned witnesses, exact reviewed Apply, one-step history,
stale review rejection, frozen donor snapshots, Save/Open (including metadata-only
offline Open), UUID/tombstone preservation and unchanged Build-review files.

Still unfinished: editing saved clip content, new clip assignment and raw streaming
bank relocation. Compressed carriers use the expanded-bank relocation path;
unsupported streaming carriers explicitly block Build/review rather than omitting
clips. The fixed-layout serializer remains limited to equal-length changes. Runtime
animation selection, playback cadence, lifecycle and model compatibility require
later qualification and deferred manual gameplay checks.

## Editor creation and proposed pose preview (2026-10-04)

Select an imported actor in Edit mode, open **Author animation channels**, then
choose **Allocate independent animation clip**. Enter zero-based source frames,
separated by commas; inclusive ranges may run forward or backward. For example,
`0-2,2-0,0` creates seven frames, including repeated and reversed donor poses.
The creator checks the donor frame count and remaining cumulative ledger budget
before Review; it does not silently truncate an oversized sequence.

Review binds the sequence, current source and resolved donor/model witnesses to
the proposed ledger and bank hashes. **Preview reviewed clip** decodes the exact
new record and poses Current authored model geometry. Closing the model viewer
returns to the retained sequence/review. Preview does not publish project edits;
**Apply allocated clip** is a separate explicit action. Editing the sequence,
changing the source/selection or closing the creator invalidates pending work.
Allocated proposal exports are unavailable rather than exporting the donor clip.

`POST /api/animation-record-allocation-options` accepts `entity_id` and
`expected_source_key` and returns the verified donor counts and remaining limits.
`POST /api/animation-record-allocation-pose-preview` accepts the allocation request
plus its exact `review_key`. It independently reconstructs the reviewed bank and
labels the returned record as an unassigned proposal with bank/record provenance.
The viewer's playback rate remains a preview setting, not inferred Retail timing.

Focused Node checks cover bounded sequence parsing, response identity/provenance,
explicit Apply and stale/late/close/Return lifecycle. One actual Retail HTTP test
checks frame repetition, exact poses over Current translated geometry and stale
review rejection without project mutation. An actual Edge editor smoke rendered
the seven-frame proposal without page errors, retained Review on Return and left
project source/overrides unchanged. Repeated donor frames rendered identically;
the review and posed-model screenshots were inspected. This qualification covers
the model viewer, not gameplay or allocated scene-inspection acceptance.

## Saved clip inspection and lifecycle (2026-10-04)

The actor animation editor's **Manage allocated clips** opens the actor's active
and retired captures. Each clip retains its authored UUID, frame/object counts
and record hash. **Preview saved clip** verifies the source and replays the saved
donor snapshot, including captured axes, before posing Current geometry for that
captured model. Retired clips remain inspectable without restoration or mutation.
The viewer identifies them as saved unassigned clips and disables unsupported
exports. Closing it returns to the retained library selection and lifecycle Review.

**Review retirement** or **Review restoration** computes the proposed bank and
ledger; **Apply reviewed change** is a separate explicit action. The existing
ledger command provides Undo/Redo and Save/Open. Changing source/selection or
closing the library invalidates pending work. Revision exhaustion disables new
lifecycle reviews; retained clips remain inspectable. Retired identities and
captured bytes stay reserved rather than being deleted or reassigned.

`POST /api/animation-record-library` accepts exactly `scene_id` and
`expected_source_key`, validates Retail witnesses/replay and returns bounded clip
summaries. `POST /api/animation-record-pose` additionally requires `record_id`.
Saved pose provenance names the standalone retained native record; it does not
invent a runtime assignment or a native bank ordinal for retired records.

Focused Node checks cover library/provenance validation, lifecycle Review,
explicit Apply, retained model-viewer Return and stale/late/close guards. Two
Retail HTTP checks (saved library and existing proposal preview) pass. The saved
test covers retirement, Save/Open, preview without mutation, source invalidation,
Current geometry, frozen transforms after later shared donor changes and exact
identity/hash preservation through restoration. Assignment and streaming bank
relocation remain separate unfinished work.

An actual Edge editor smoke additionally passed active/retired model Preview,
Return with retained lifecycle Review and explicit retirement/restoration on a
private fixture. Preview left project state unchanged; restoration retained the
same UUID/hash. There were no page errors. Saved-pose and restoration-review
screenshots were inspected, and the private server was stopped afterward.

## Expanded compressed bank delivery (2026-10-04)

Normal Build and Build review now reconstruct active ledger records together with
all current shared channel edits. A source-qualified physical ANM owner carries
the expanded bank: its type-5 descriptor gets the new decoded byte length, LZS is
independently decoded, and compressed overflow grows the owned slot on a word
boundary. Following descriptors move by that growth while neighboring payloads,
table padding and opaque bank records remain preserved. PROT physical spans are
sector-aligned and later TOC starts are rebased through the existing relocation
pipeline. Existing record ordinals remain unchanged; active allocated ordinals
follow them. Retired captures stay metadata-only and do not enter the bank.

Source-addressed equal-span overlays are composed before relocation. Model and
animation growth requests may share the same resource table; all final resources
are reopened after all relocations. Multiple distinct tables in one physical
owner are rejected pending explicit locator remapping. Raw streaming ANM carriers
also reject with a specific unimplemented relocation reason. Neither case drops
authored data. Native limits remain 4 MiB banks, 4096 records, 64 appended records,
4096 new channels and 16 MiB physical scene carriers, with the existing 32-resource
batch and 256 MiB native relocation package limits.

Build emits a source-bound format-7 disc relocation package and includes record
UUID/hash/count metadata in the audit. Allocated clips remain unassigned to MAN
actors; carrying their bytes does not prove runtime selection or playback.
Editor capability labels distinguish compressed delivery from unsupported raw
streaming relocation. Passing capability checks is not a blanket Build readiness
claim; the complete normal Build review still validates all authored content.

Eight synthetic codec/composition checks passed, covering nonzero table offsets,
both PROT header locations, simultaneous model/ANM growth, original-address patches,
neighbor preservation, no-op identity and stale/aliased/opaque mutation rejection.
A Retail Town01 normal Build test independently decoded the generated format-7
package and recovered the exact composed 70-record bank (one of two captures
retired), including later shared edits, while saved project metadata stayed
unchanged. Generic package-consumer checks passed. No game was launched and no
runtime/gameplay acceptance is claimed.

## Initial actor assignment qualification and review (2026-10-04)

`ManAssignmentContext.patch_allocated` qualifies an expanded ANM bank against its
Retail source, then checks an explicit imported donor/target pair and new record
hash. Target and donor require non-aliased MAN partition-1 records, an evidenced
compatible local model/channel mapping and supported donor headers/trailers.
Only initial model/animation header bytes are patched; script, coordinate,
partition, local and opaque bytes stay unchanged. Appended record index plus one
must fit the nonzero MAN animation byte (1–255). Old record ordinals cannot be
submitted as allocated clips. Current authored channel axes may be composed in
the bank, with the native qualification still guarding old layouts/opaque data.

`POST /api/allocated-animation-assignment-review` accepts exactly `entity_id`,
`record_id` and `expected_source_key`. The clip must be active in the scene ledger
and its captured asset must equal the target's inherited appearance model; no
retargeting is inferred. Review resolves the stable UUID/hash to the current bank
ordinal, checks the native MAN proposal, and reports a portable proposed component
separately from its current native byte selector. No project state is published.

`POST /api/allocated-animation-assignment-pose` adds the exact `review_key`,
independently repeats Review and poses the frozen captured record over Current
geometry. The response labels a proposed initial clip and marks it unapplied.
Retiring another clip may rebase the selector without changing the selected
UUID/hash; that source change invalidates the previous Review and pose request.

Two new native tests plus eight existing synthetic MAN checks pass (the optional
Retail importer case was skipped in that synthetic run). The Retail SDK test
covers read-only Review/Pose, exact captured record, Current geometry, selector
71→70 after another clip's retirement, and stale/missing/incompatible request
rejection. This was the read-only qualification milestone; persistence and scene
projection and normal Build delivery were subsequently added below. Editor
controls remain unavailable. Carrying
an allocated bank and qualifying a MAN proposal do not establish runtime selection
or playback suitability. No game was launched.

## Persistent initial actor assignment (2026-10-04)

`POST /api/allocated-animation-assignment` accepts the exact Review request plus
`review_key`. Apply independently replays Review and stores `ActorAllocatedAnimation`
with exactly `scene_id`, `record_id`, `record_sha256` and `model_asset_id`. It replaces
an existing imported `ActorAnimation` in one history entry; Undo restores the whole
prior actor state. It stores no ordinal or Retail payload. Repeating a current
no-change Review/Apply creates no history entry. Stale source/review keys reject.

Review/Apply with `record_id: null` clears the allocated component and restores
the inherited appearance initial clip. Undo restores the allocated component.
The displaced imported assignment is restored only by Undo, not by clear.

Save/Open structurally verify the retained active capture, exact hash/model and
actor association after all ledgers are loaded, independent of JSON key order.
Offline Open does not claim native payload validation. Native Review, posed
Preview and guarded mutations independently verify disc evidence. Referenced
clips cannot be retired or removed; incompatible appearance changes and whole
ledger reset roll back overrides and history together.

Actor initial Preview and scene geometry use the assigned frozen record over
Current model shape, with frame zero in the scene. Cache source keys include the
portable assignment. Imported observer candidates stay available; imported
witnesses are not reported as an effective allocated runtime match. Cached
observations invalidate on assignment Apply, replacement or clear. GLB
interchange and capture from assigned allocated clips remain unsupported and
reject explicitly rather than substituting the imported clip. Ordinary shared
channel authoring remains attached to imported channel ownership.

Normal Build now composes this component into the initial MAN header alongside
the expanded compressed ANM bank, as described below. Editor assignment controls
remain the next work; runtime script selection, timing and suitability remain
deferred gameplay checks. No game was launched.

## Normal Build initial header delivery (2026-10-04)

Build resolves all assigned retained UUIDs against the freshly composed bank.
Each exact capture/hash and inherited model is requalified through the native
MAN context. Its audited initial model/animation byte changes merge with normal
fixed-layout header, position and script edits; overlapping header bytes reject.
An inherited appearance assignment for the same actor is represented by the
allocated proposal's exact model header instead of being written a second time.
No ordinal is written back into the saved project.

Final compressed MAN readback must equal the whole composed decoded candidate,
and its audit includes retained UUID/hash, native ordinal and captured model.
`allocated_initial_MAN_header_readback` marks this qualification. The existing
format-7 relocation package applies MAN overlays before ANM bank relocation and
independently reopens all expanded bank descriptors. Retail package testing
recovers the exact bank and selector 70 after another capture is retired, with
saved project metadata and overrides unchanged. Synthetic composition preserves
placement and rejects conflicting header edits.

This covers initial source headers, not a runtime assignment observation. Raw
streaming ANM relocation remains explicitly unsupported. Joint composition with
appended NPC MAN records was subsequently added below. Build rejects unsupported
carriers before package publication. Gameplay selection, script changes, cadence and lifecycle are still
deferred; no game was launched or installed.

## Initial assignment editor workflow (2026-10-04)

Select an imported actor and use **Manage allocated clips** directly in the actor
inspector, or through the imported channel editor. The library lists retained
captures for the actor's exact inherited model, including captures from other
actors with that same asset identity. Retired clips remain previewable and
restorable but cannot be assigned. Native Review rechecks compatibility.

**Review initial assignment** shows the portable retained identity and current
native selector, marks the change unapplied, and reports Build support and
limitations. **Preview reviewed assignment** opens the captured pose over Current
geometry; close returns to the same Review. **Apply reviewed change** sends the
exact reviewed source/record/key and publishes the actor component. An already
assigned no-change Review disables Apply. A new source, selection, pending work
or closed dialog invalidates the held Review. Retirement/restoration retain their
separate Review path and cannot be confused with initial assignment Apply.

The inspector displays the assigned UUID, record hash and captured model.
**Review clear assignment** then **Apply reviewed change** restores the inherited
initial clip; normal Undo/Redo and Save/Open remain available. Proposal/assigned
clip exports are unavailable and explicitly disabled, so they cannot silently
export an imported clip. Scripts may replace the initial clip at runtime.

Two focused Node workflow suites pass. A private Retail-backed headless Edge
smoke exercised direct inspector entry, Review, three-frame posed Preview and
Return, Apply and clear, with no page errors and disabled exports. The Review and
pose screenshots were inspected. The staging server was stopped. This is browser
acceptance, not gameplay acceptance; no game was launched or installed.

## Joint allocated clip/NPC composition (2026-10-04)

Normal Build now supports allocated initial headers on original actors in scenes
with appended NPC records. `patch_allocated_appended` first qualifies the exact
bank/donor/target proposal against Retail, then requires bounded partition-1
additions with unchanged other partition counts and target record/header layout.
It reparses actor identities to rebase header offsets, checks the new preimages,
and independently reads back the resulting model/clip bytes. Source and rebased
offsets remain distinct in the audit. New NPC copies retain their imported donor
clip; an original actor's allocated assignment is not copied implicitly.

The normal NPC preparation path explicitly marks expanded animation delivery as
managed by the parent Build. Scene ledgers bypass MAP handling, and shared channel
patches for ledger scenes are composed once into the expanded ANM bank. Allocated
header changes are retained in `existing_actor_allocated_animation_changes` in
the NPC audit. Existing bounded compression, source capacity, neighboring payload
preservation and actor-pool qualification apply to the complete appended MAN.
Experimental full-disc draft export does not claim expanded bank support and
rejects this assignment path rather than omitting it.

Eight focused checks pass. Independent Retail combined-package readback confirms
one new NPC, the original actor's allocated selector 70 and the donor copy's
original selector, plus the exact composed ANM bank. Synthetic tests reject
stale target headers and invalid partition growth, verify rebased audited byte
coverage and preserve placement edits. No gameplay was run. Source qualification
and package readback do not prove native NPC spawning, scripts, cadence or lifecycle.

## Retained allocated GLB export (2026-10-04)

Open a saved clip or reviewed initial-assignment pose, then use **Export GLB** for
the displayed frame or **Export full clip GLB** with an explicit rate (1–120 fps).
Retired captures can also be exported. The output contains Current geometry,
embedded matched textures and either the baked selected pose or independent rigid
TRS channels for the captured frame sequence. Retail timing is not inferred; full
clips use STEP interpolation and hold the final frame for one selected interval.
Looping remains controlled by the receiving application.

`POST /api/export/allocated-animation` requires exactly `scene_id`, `record_id`,
`expected_source_key`, `representation`, and one of `frame_index` or `clip_fps`.
Supported representations are `allocated_record`, `allocated_assignment_preview`
and `allocated_initial_assignment`. The latter two also require `entity_id`;
proposed assignments additionally require the exact `review_key`. Assigned export
checks that the requested retained identity is still the actor's assignment.
Saved export reconstructs that capture even if retired. Proposal export repeats
native Review. No output path, address, binary payload or geometry is accepted.

Encoding completes privately in memory and the source key is rechecked before
publication into project-controlled Exports. Invalid requests and source changes
publish no new file. Export does not alter overrides, saved metadata or history.
Both the audit sidecar and GLB extras preserve the retained UUID/hash and the
saved/proposed/assigned representation. Unapplied allocation previews still need
Apply to establish a retained identity before export. Allocated content GLB import
remains separate unfinished work; the imported shared-channel sidecar is not an
allocated-clip import binding.

Retail HTTP checks cover active/retired/proposed/assigned exports, three-frame
mapping with repeated first/third poses, exact retained identity, posed frame,
invalid/stale requests, unchanged project/history and source changes during
encoding without publication. Three editor workflow suites and actual private
Edge export smoke pass. The exported proposed GLB was reopened to verify embedded
identity and animation channels. The export dialog screenshot was inspected;
staging was stopped. No game was launched or installed.

## Retained content edit APIs (2026-10-04)

`POST /api/animation-record-edit-review` accepts exactly `scene_id`, `record_id`,
`source_frame_indices`, `edits` and `expected_source_key`. The mapping indexes the
original frozen captured donor, not the current allocated frame sequence or later
shared channel changes. The complete axis contribution replaces the prior `edits`;
untouched axes inherit the selected captured frame. Translation values are exact
signed native integers; rotations retain the 16-unit native quantization. Existing
512-frame, 64-object, 4096 cumulative channel, metadata and revision bounds apply.

Review reconstructs the existing source witnesses, builds the new native record,
updates its hash in a proposed ledger and reports every referencing initial actor
assignment. Each proposed updated binding is independently native-qualified against
the proposed bank. UUID, donor snapshot and active/retired state stay unchanged.
A no-change request reports `project_change: false` without consuming a revision.

`POST /api/animation-record-edit-pose` adds the exact `review_key`, replays Review
and reconstructs proposed captured poses over Current geometry without publishing.
Its `allocated_record_edit_preview` representation is explicitly unapplied and
cannot export an imported substitute. `POST /api/animation-record-edit` accepts
the same exact reviewed request and key, replays qualification, then publishes the
scene ledger and all affected actor hashes in one `entity_overrides` history entry.
Undo/Redo restore all affected components together. Retired clips remain retired.
Source changes invalidate prior assignment/pose/export Reviews through normal keys.

The Retail HTTP workflow covers active assigned editing, four-frame posed Preview
with an exact changed native translation, read-only previews, malformed mapping
and rotation rejection, wrong/stale review keys, one-entry content/reference
Undo/Redo, no-op Apply, Save/Open and reconstructed bank equality, normal Build
review of reopened assigned content, and retired two-frame editing without
restoration. Editor forms and allocated GLB import are still implementation work;
these APIs do not claim that UI workflow or runtime/gameplay acceptance. No game
was launched or installed.
