# Persistent native animation record allocation

The SDK can construct new rigid animation records from a verified donor and
review the proposed expanded native bank through
`POST /api/animation-record-allocation-preview`, then Apply the exact request and
`review_key` through `POST /api/animation-record-allocation`. Allocation is stored
in a scene-owned `AnimationRecords` component with ordinary Undo/Redo and
Save/Open. The editor now exposes creation, Review, posed Preview and explicit
Apply. Normal Build delivers expanded banks in qualified compressed ANM carriers.
Authored-clip assignment and raw streaming bank relocation remain unavailable.
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
rejection. Assignment Apply/persistence, actor scene projection, normal Build
header composition and editor controls remain explicitly unavailable. Carrying
an allocated bank and qualifying a MAN proposal do not establish runtime selection
or playback suitability. No game was launched.
