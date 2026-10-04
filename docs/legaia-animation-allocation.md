# Native animation record allocation and SDK review

The SDK can construct new rigid animation records from a verified donor and
review the proposed expanded native bank through
`POST /api/animation-record-allocation-preview`. This is the first allocation
stage. Project persistence, editor controls, authored-clip assignment and normal
Build delivery are still required; the response explicitly marks those
capabilities unavailable. Existing GLB channel import remains a separate complete
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

The review carries source/effective/candidate bank hashes, donor provenance,
per-record old/new offsets, exact frame mappings, axis audit and a review key.
An authored animation URI uses a canonical UUIDv4 identity derived deterministically
from the request/source context. This UUID is review metadata, not an embedded
native pointer or a persisted project identity yet. Changing source/ownership or
the request invalidates the previous review identity. No review creates files,
overrides or history.

Bounds are 64 records and 4096 allocated channels per batch, 512 frames per
record, 64 donor objects, 4096 native bank records and 4 MiB total decoded bytes.
Source frame/object indices, UUIDs, exact axis values, request schemas and source
hashes are validated before publication. A later project ledger must enforce
cumulative limits and reserve identities across history; this codec does not
claim those project-level guarantees.

On 2026-10-04, seven native construction checks and two actual Retail HTTP workflow
checks passed. Town01 grows from 69 to 70 records, preserves every old record and
round-trips the expanded bank through independent LZS decompression. SDK checks
cover effective shared edits, repeatable review identity, changed-request identity,
stale source/schema rejection, assigned clip/model witnesses, Edit-mode enforcement
and unchanged files/history. Existing GLB numerical checks also passed.

Still unfinished: allocation ledger/commands and Save/Open, scene/editor preview,
new clip assignment, expanded bank descriptor/carrier relocation and normal Build.
The fixed-layout Build serializer continues to reject bank-size changes. Runtime
animation selection, playback cadence, lifecycle and model compatibility require
later qualification and deferred manual gameplay checks.
