# Native TIM slot allocation

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

`integrations/legaia/importer/texture_slot_allocation.py` exposes
`append_texture_pack(source, expected_sha256, additions, *, edits=None,
standalone=False)`. `additions` is a nonempty list of complete immutable TIM
bytes. No image conversion, palette generation, origin inference or material
assignment happens in this transform.

The source pack must match its hash and existing native format. A raw pack
retains its four-byte signature; compressed decoded packs have no signature
prefix. The count and word-offset table grow; any bytes between the old table
and first member survive. Existing slots retain their indices. Every old TIM
and opaque tail survives, including an old final sector-padding tail that now
precedes the appended members. Only required zero word-alignment padding is
added. Optional existing edits use the existing source-qualified image-layout
allocator before appending. New indexed CLUTs must fit the native flattened
upload strip; RGB24 data must contain complete pixels. All output is bounded
and independently parsed and compared before return.

## Archive composition

Compressed requests use `kind='texture-addition-pack'` and exact fields
`entry_index`, `table_offset`, `descriptor_index`, `expected_pack_sha256`,
`pack`, `layout_edits` and `slot_additions`. The complete proposed pack must
match a fresh allocation from the qualified source and member inputs.

Raw requests use `kind='texture-addition-raw'` and exact fields `entry_index`,
`expected_pack_sha256`, `edits` and `slot_additions`. Empty existing-edit lists
are accepted for either addition request; empty additions are rejected.

The archive rebuilders retain unique physical ownership checks, descriptor
relocation, sector allocation and exact physical-neighbor readback. The shared
composer rejects conflicting requests and verifies the final reopened raw or
compressed pack after other resource relocations. Its
`final_texture_additions_verified` audit reports whether a verified addition
request participated. Neither the codec nor composer writes the physical disc.

## Evidence and remaining integration

Nine construction cases pass across the slot allocator, image-layout allocator
and fixed-payload growth modules. They cover raw/compressed tables, nonzero gaps,
opaque tails, STP-bearing additions, simultaneous existing resize edits, both
PROT header layouts, archive neighbors, stale hashes, incomplete TIMs, VRAM
bounds, full slot tables, contradictory candidates and duplicate ownership.

Private Retail-source evidence is in
`local-output/sdk-20260909/texture-slot-allocation-20261004/parent/`.
Town01 appends slot 96; Dolk2 appends slot 50. Exact reopened archives preserve
all prior slots and tails. The source disc remains unchanged and no game runs.

Next: stable authored texture identities and persistence; source-qualified
Review/Apply with explicit overlap policy; Current/Proposed catalog/preview;
Undo/Redo and offline reopening; normal Build routing and package readback.
Gameplay must later establish runtime upload, placement, material appearance,
scene transitions and save/load behavior. Native readback does not establish
runtime residency or successful game rendering.
