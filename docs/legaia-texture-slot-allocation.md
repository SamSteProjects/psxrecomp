# Native TIM slot allocation

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

## Editor import workflow

Open a Retail texture in the resource browser and choose **Import new texture
slot**. The selected texture identifies the target native pack. Choose a complete
TIM up to 1 MiB, give it a name, and review the proposed slot, pixel dimensions,
bit depth, image origin, palette count and known upload overlaps. Changing the
file, name or overlap choice withdraws the review. Palette selection is readonly
and controls Proposed pixel inspection. Return preserves the reviewed choices.

Apply requires the exact reviewed file hash, source context and overlap choice.
It returns the updated authored collection and creates one Undo entry. Save the
project to persist; normal Build includes the appended slot. The dialog rejects
stale project/scene/mode contexts and bounds requests/responses. Closing cancels
readonly work; closing during Apply is disabled. Small images are enlarged with
nearest pixel display and transparency backing for inspection.

HTTP routes are `/api/texture-slot-review`, `/api/texture-slot-pixels` and
`/api/texture-slot-apply`; requests have exact fields and bounded base64 TIM
bytes. Pixel inspection reconstructs the current review and verifies the PNG's
reviewed dimensions. No arbitrary file paths or archive locators are accepted.

Current catalog/scene visibility, material assignment to new slots, editing a
saved new slot, source-image conversion and automatic VRAM placement remain next
integration work. This dialog does not infer materials or runtime upload order.

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
