# Persistent native animation record allocation

The SDK can construct new rigid animation records from a verified donor and
review the proposed expanded native bank through
`POST /api/animation-record-allocation-preview`, then Apply the exact request and
`review_key` through `POST /api/animation-record-allocation`. Allocation is stored
in a scene-owned `AnimationRecords` component with ordinary Undo/Redo and
Save/Open. Editor controls, authored-clip assignment and normal Build delivery
are still required; the response explicitly marks those capabilities unavailable.
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

Still unfinished: scene/editor preview and controls, new clip assignment,
expanded bank descriptor/carrier relocation and normal Build. Active allocated
clips explicitly block normal Build and Build review with the missing
descriptor/carrier relocation requirement; they are never silently omitted.
The fixed-layout serializer still rejects bank-size changes. Runtime
animation selection, playback cadence, lifecycle and model compatibility require
later qualification and deferred manual gameplay checks.
