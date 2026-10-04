# Native TIM slot allocation

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
