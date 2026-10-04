# Legaia SDK buildout milestone — 2026-09-09

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

**2026-10-04 — allocated initial animation assignment qualification/review:**
Implemented native appended-ordinal MAN header qualification using an evidenced
same-model donor and exact bank/record preimages. Only header bytes change;
aliases, unsupported mappings, old ordinals, stale hashes and selector overflow
reject. Read-only SDK actor/clip Review and posed Preview expose a portable
proposed component separately from the current native byte selector.

Synthetic checks pass. Retail HTTP review/pose checks prove stable clip identity
through 71→70 ordinal rebasing, exact review keys, unchanged project/history and
stale/incompatible input rejection. Assignment persistence/Apply, scene integration,
normal Build MAN composition and editor controls remain the next work. Existing
bank Build delivery remains implemented. [Details](legaia-animation-allocation.md).
No game was launched; the full goal remains active and solo.

**2026-10-04 — expanded compressed animation bank Build:** Implemented bounded
ANM bank qualification, type-5 descriptor/stream growth and physical PROT carrier
relocation. Normal Build/review compose active frozen captures with current shared
channels; retired captures are excluded. Source-addressed overlays precede model
and ANM relocation in a shared table, and final resources are reopened. Format-7
packages/audits carry the expanded bank and stable record provenance.

Synthetic carrier/composition checks, Retail Build package readback, generic
consumer checks and ledger/pose/model-growth regressions pass. Town01 delivery
matches the exact composed 70-record bank with one retired capture and later
shared edits. Project metadata stays unchanged. Raw streaming relocation and
multiple distinct tables in one physical owner remain explicit rejection cases.
Actor assignment and saved-content editing remain; no game/runtime qualification
is claimed. [Details](legaia-animation-allocation.md). The full goal stays active,
solo, with gameplay verification deferred.

**2026-10-04 — saved allocated clip library:** Added verified retained clip
summaries and standalone native record pose APIs, plus actor editor Preview and
reviewed retirement/restoration controls. Retired captures remain previewable
without mutation; Current geometry is posed using frozen saved transforms. The
viewer labels saved clips unassigned and prevents exporting a Retail donor instead.
Return retains library selection and Review; stale/late/close guards cover actions.

Focused Node checks, two Retail HTTP tests and an actual Edge lifecycle smoke pass.
Save/Open and later shared donor changes preserve captured transforms; restoration
preserves UUID/hash. Screenshots were inspected and the private server stopped.
Saved content editing, actor assignment and bank descriptor/carrier Build delivery
remain. [Details](legaia-animation-allocation.md). No gameplay was launched; the
full SDK goal remains active and work stays solo.

**2026-10-04 — allocated animation editor and posed preview:** Implemented an
actor clip creator with explicit frame ranges/repeats/reversal, donor/budget
options, source-bound Review, exact record pose preview and explicit Apply.
Current authored geometry is used; returning from the viewer preserves Review.
Selection/source changes, edited sequences, late responses and close are guarded.
Allocated proposals remain visibly unassigned; unsupported exports are disabled.

Focused Node checks and one Retail HTTP pose test pass. A real Edge editor smoke
rendered seven proposed frames without page errors or project changes, with
retained Return state and identical repeated donor poses. Screenshots were checked.
Saved-clip management, assignment and normal Build relocation remain implementation
work. [Guide](legaia-animation-allocation.md). No runtime/gameplay acceptance is
claimed; the full goal remains active and solo.

**2026-10-04 — persistent animation allocation ledger:** Allocation Apply now
reconstructs the proposed bank independently, then publishes one scene component
and history entry. The ledger stores exact captured donor axes and frame mappings,
Retail preimages and stable clip UUIDs. Undo/Redo, Save/Open, source-key invalidation,
authored component review and reviewed retirement/restoration are integrated.
Retired clip metadata/identities stay reserved; active native ordinals can rebase.

32 focused checks pass, including actual Retail HTTP Apply/lifecycle, two allocated
clips, frozen bytes after shared donor changes, offline metadata Open, malformed
ledger rejection and explicit Build/review blockage without files being written.
Project limits cover 64 retained identities/revisions, 4096 cumulative channels and
2 MiB ledger metadata. [Details](legaia-animation-allocation.md). Remaining work:
editor/pose/assignment and bank descriptor/carrier relocation/normal Build. No
runtime acceptance is claimed; the full SDK goal remains active and solo.

**2026-10-04 — animation record allocation codec/review:** Implemented explicit
donor frame sequences plus exact source-axis edits for new native rigid records.
The bank count/absolute-offset table grows without altering existing record bytes,
indices or opaque padding. Source-bound HTTP review includes actor/model/clip
witnesses, effective shared edits, UUID-based authored review identity and exact
bank/record audits, with unchanged project files/history.

Seven codec and two Retail HTTP construction checks pass; Town01 69→70 records,
complete old-record preservation and LZS decompression readback pass. Existing GLB
numerical checks pass. [Allocation details](legaia-animation-allocation.md) keep the
remaining work explicit: project ledger/commands/Save/Open, editor/pose/new-clip
assignment, bank descriptor/carrier relocation and normal Build. Review reports
Apply/Build/assignment unavailable. No runtime or gameplay acceptance is claimed.

**2026-10-04 — cubic animation interchange:** Implemented glTF CUBICSPLINE
translation/rotation import into existing source frames, including unequal key
spacing, segment-second derivative scaling, rotation normalization without
shortest-arc rewriting, exact keys and endpoint holds. Existing source binding,
quantization, ownership, review identity and fixed record layout remain in force.
Malformed or undefined sampled curves reject before a project command.

19 focused Python checks pass, including private Retail Town01 HTTP review/pose,
changed-file rejection, one-command Apply, Undo/Redo, Save/Open and exact normal
Build bank readback. Existing browser-module Node lifecycle checks pass. The editor
and [interchange guide](legaia-animation-glb.md) describe support. No runtime launch,
installation or gameplay verification occurred. General record allocation,
retargeting and broader scene/live/runtime SDK work remain open; goal incomplete.

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

Verified stability fixes and a connected authoring workflow are implemented
on `codex/legaia-upstream-20260909`. The full modern SDK is not complete. This
record separates functioning features, demonstrated failures and remaining
product work; the detailed [feature matrix](FEATURE_MATRIX.md) and
[16-layer acceptance plan](TEST_PLAN.md) remain authoritative for scope.

## Current buildout status — updated 2026-10-02

**World-map source GLB export (2026-10-02):** World ground inspection now connects to private GLB downloads for all resolved source placements plus terrain, terrain alone when the placement layer is hidden, or one selected source entity. Shared meshes, source transforms, embedded matched textures and source provenance use the existing scene exporter. Fresh source checks bind exports to the imported disc and current project; late responses after closing or changing sources cannot trigger downloads. Exported placement seeds retain unknown runtime resting positions and visibility. Exports create private artifacts without authored commands or Build/disc output. See [world-source export](legaia-worldmap-export.md).

Validation: 16 focused Python cases passed with private retail input and no skips; three Node guard suites and frontend syntax checks passed. Independent all-three-kingdom readback verifies source world corners, reflected winding, shared meshes, UVs, stored colors, embedded PNG pixels and provenance. Nine actual browser scenarios pass, including five downloaded artifacts, ground-only visibility scope, selected seed scope, 540px controls, cancelled late responses and stale-source withdrawal. Downloaded geometry binaries and normalized metadata match the independent exports. Blender 5.2.2 LTS imports the complete map01 scene with 302 entity roots, 303 mesh objects, 67 materials and 60 images; all local triangles match, and maximum world-coordinate float error is 0.0009765625 source unit. Saved project/import/Build files remain unchanged; no game, authoring command or disc export ran. Private proof: `local-output/sdk-20260909/worldmap-glb-20261002/`.

**Scenery group source-angle rotation (2026-10-02):** The existing anchor rotation workflow now accepts every integer source yaw delta from 0 through 4095, alongside its compatible quarter-turn controls. A frozen Q30 quarter-wave table and signed integer nearest-half-away rounding produce reviewed X/Z positions; cardinal turns remain exact. The editor independently checks the same arithmetic before accepting a report. Review, retained Proposed/Current inspection, atomic Apply, Undo/Redo, Save/Open and normal Build preserve source Y, other rotation axes, shared descriptors and unrelated components. Rounded positions can change distances slightly; this authoring convention does not establish retail GTE rounding or gameplay acceptance. See [group rotation workflow](legaia-scenery-group-rotation.md).

Validation: 19 focused Python cases passed with no skips; two Node guard suites and frontend syntax checks passed. All 4096 angles match between Python integers and JavaScript BigInt for six signed displacement pairs, with identical frozen tables. Twelve actual browser scenarios verify custom angle review, invalid-input rejection, retained Proposed/Current comparison, history, Save/reload, normal Build, cancellation and stale-state withdrawal; the 540px layout was visually inspected. Independent renderer matrices and reopened full 73,728-byte MAP package readback match the reviewed 45° proposal. Only bytes 171/256/260/267 change against the prior authored fixture; source Y, other axes, shared records, prior Collision and retail MAP remain intact. No game or disc export ran. Private proof: `local-output/sdk-20260909/scenery-group-angle-20261002/`.

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

**Coordinated scene animation:** Play/Pause and scrubbing now animate eligible
actors in the central viewport using shared source-qualified tracks. Stop restores
the exact canonical scene; sampling preserves placement/materials/history and
blocks persistent edits. Retail and Authored channels remain distinct. Dolk2
loads 69 actors/15 tracks; independent Town01 evidence covers 42/22. Six Python
tests, the Node suite and browser workflow pass. Runtime scheduling/timing and
current live clip identity remain pending. See [workflow](legaia-scene-animation.md).

**Source-qualified model materials:** Existing CLUT/page/depth fields and shared
group ABE now connect to source/current Review, model/posed-scene proposal, Apply,
history, Save/Open and Build. Source ABR remains read-only. An actual Dolk2 model
changes exactly two bytes; geometry, fresh GLB interchange, source allocation
and decoded neighbors are preserved. Twenty-two Python tests, three Node suites
and six browser checks pass. Runtime appearance and general material allocation
remain deferred. See [workflow](legaia-model-materials.md).

**Source-bound texture PNG editing (2026-10-02):** Effective PNG/binding/STP
export, external pixel edits, exact Review, proposed pixel/scene inspection and
Apply now connect to ordinary texture history, Save/Open and normal Build.
Indexed palette selection/rebuild preserves layout and other CLUT rows; Review
explains shared indices, numeric color error and forced STP changes.

Twelve focused Python cases, the Node suite, both frontend syntax checks and
11 browser checks passed. Independent Pillow verifies retail no-ops and exact
byte edits. Town01 Build readback matches the reviewed 33,312-byte candidate,
other palettes and neighboring source bytes; proposed scene textures affect
26 materials across 10 instances with unchanged geometry and placements.
Review/Return, stale/no-op gates, history, persistence and 540px layout passed;
page/HTTP errors and game-launch requests were zero. No new dependencies or
game launches are required. Allocation, large-image performance acceptance,
live blending/residency and gameplay remain pending. See
[workflow](legaia-texture-png.md) and `local-output/sdk-20260909/texture-png-20261002/`.

**Source-bound model GLB editing (2026-10-02):** A connected model Export + binding,
external position/UV edit, Review, proposed-model inspection and explicit Apply
workflow now uses ordinary model commands, Undo/Redo, Save/Open and normal Build.
Source vertex/corner attributes qualify aliases and quad triangulation. Effective
colors, normals, face references, materials, images and opaque bytes survive.
Arbitrary topology/material replacement remains outside the supported layout.

Fourteen focused Python tests, the Node suite, both frontend syntax checks and
12 browser checks passed. A fresh SDK export through Blender 5.2.2 preserves
every source byte; its edit changes exactly two fields in Dolk2 model 0133. The
saved browser package reproduces the candidate and preserves decoded neighbors
and compressed capacity. Review/preview, stale/no-op gates, history, persistence
and 540px layout passed, with zero page/HTTP errors or game launches.
[Workflow and limitations](legaia-model-glb.md) include private evidence.
Gameplay acceptance remains deferred; the full SDK objective remains unfinished.

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

Validation: 26 selected Python cases passed with the private retail disc enabled
and zero skips; 4 Node suites and 2 changed-module syntax checks passed. Thirteen
actual browser workflows passed with zero page/HTTP errors and zero game-launch
requests, including file downloads, stale/late response guards, proposed pose
inspection, Apply, Undo/Redo, Save and normal reviewed Build. Final viewer and
narrow-layout checks verify the retained review and named clip. Blender 5.2.2
actually edited and re-exported Dolk2 object 0/frame 0 translation X+1 and rotation
X+16; baseline imports byte-identically, edited imports exactly those two axes,
with zero translation error and maximum angular error 0.0000191993 degrees.
Independent readback of the browser-produced 114764-byte raw animation bank
changes exactly bytes 52228/52233 and preserves every other byte. Save/Open
retains the contribution and imported metadata is unchanged. Private evidence
is under `local-output/sdk-20260909/animation-glb-20261002/` and
`local-output/sdk-20260909/animation-glb-integration-20261002/`. Gameplay clip
selection and cadence remain deferred; no game was launched or software installed.

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

**Rectangular source wall editing (2026-10-01):** Added source-bound collision
rectangle review and atomic Apply through existing wall-bit serialization,
preserving low-nibble floor tiers and unselected edits. Bounds, merged4096 limit,
stale/changed proposals, Live mode and no-ops reject or remain nonmutating.
Seventeen focused Python checks,27 Node files/28 syntax checks passed. Retail
browser reviewed16 bits, Apply/Undo/Redo/Save and stale/no-op guards with zero
errors; compact screenshot inspected. Saved normal package ZIP readback matched
the complete73728-byte MAP with floor tiers preserved. Andrew's exact pinned
movement source reread; no copied code or new runtime semantics. No game launched;
deferred package recorded in gameplay queue. Postdates514. See
[Wall rectangles](legaia-collision-rectangles.md).

**Saved editable copy discovery (2026-10-01):** Copy project lists creation records
from disk after restart, distinguishes changed saved metadata from partial records,
and opens validated copies with the existing unsaved-change guard. Bounded local
discovery has no write effects or current-input integrity claim. Twenty-eight
focused Python checks,26 Node files/27 syntax checks passed. Browser checked
matching/edited/partial rows, corrupt import rejection, dirty-open guard before
dispatch, Dolk2 X9536 reopen, closed-pending withdrawal and Refresh; source bytes/
authored state unchanged, zero errors and inspected screenshots. No game launched;
extension postdates integrated514. See [Project copies](legaia-project-copies.md).

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

**Editable project copies (2026-10-01):** Current unsaved metadata and referenced
authored files can be copied into an independent project without saving the source.
Copies retain drafts/templates/views/selections; retail discs, generated outputs,
runtime/live state and Undo history are excluded. Readback/reopen/source drift
checks and project-local path/size guards precede a completion report. Thirty-nine
focused Python checks,26 Node files and27 syntax checks passed. Browser verified
unsaved Dolk2 X9536, dirty-open guard, independent copy Save at X9600 and original
X9472 with unchanged saved bytes, zero page errors and inspected screenshots.
No game launched; postdates integrated498. See [Project copies](legaia-project-copies.md).

**Normal Build for raw streamed MAN (2026-10-01):** Dolk2's earlier placement
serialization gap is connected through the shared typed MAN source handoff.
Equal-span raw MAN edits use the existing audited compositors and structural
chunk/record/opaque-byte validation, with explicit uncompressed package members.
Descriptor LZS behavior stays separate. Twenty-seven retail-enabled Python checks,
all25 Node files and26 syntax checks passed; browser reviewed/built ten mixed
Town01/Dolk2 changes, with two overlays/68,930 bytes, unchanged authored/persisted
metadata, zero errors and inspected screenshot. Raw donor/dialogue/P2 transition/
flag/placement edits also compose with raw ANM. Andrew's exact pin was reread for
chunk/header evidence; no reference code copied. No game launched; broader scene/
family coverage and gameplay remain open. NPC drafts still block normal Build.
Postdates integrated498. See [Raw MAN Build](legaia-raw-MAN-normal-build.md).

**Saved Build audit comparison (2026-10-01):** Build history now verifies and
compares two saved package audits by stable record identity, preserving explicit
missing/changed records and separate integrity/input/gameplay status. Fifteen
retail-enabled Python checks, all 25 Node files and 26 syntax checks passed.
Town01 browser comparison verified actor0011 X2944→3008 as one differing record,
eight unchanged records, same-ID dispatch guard, corrupt archive rejection and
restored success. Authored/persisted data unchanged, zero page errors, no game
launched. Final screenshot inspected after spacing/status fixes. Postdates the
integrated 498-test result; full SDK/runtime acceptance remains open. See
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


**Build-history compatibility correction (2026-10-01):** Full discovery at
e49e09b0 ran497 tests with four no-op package-equality failures and one stale-source
guard-order error. The failed run is retained and does not supersede the passing
475 checkpoint. Content-derived package identity now preserves byte-identical
no-op packages; separate immutable input receipts retain authored metadata
contexts. All29 focused regression checks and six history checks passed. The integrated
checkpoint above verifies this correction; no game launched.

**Saved normal Build history (2026-10-01):** Build completion receipts preserve
package provenance after editor/server restart. History compares recorded input
identity separately from an explicit file verification operation covering audit,
manifest, source payload files and exact ZIP members. Older folders without
receipts remain unavailable; no provenance or acceptance is invented. Nineteen
retail-enabled Python checks, all24 Node files and26 syntax checks passed. A
fresh-server browser reopened a real nine-change package report with unchanged
authored/persisted metadata, verified package files, explicit older-build status
and rejected malformed requests. Zero page errors; corrected column clipping and
inspected the final screenshot. No game launched. Postdates integrated475; full
SDK/runtime acceptance remains incomplete. See [Build history](legaia-build-history.md).

Current buildout includes menu-label and source-bound text-file authoring, saved runtime node
review, indexed texture rectangle copying and model object
translation/rotation/scaling, instruction-to-operand navigation, flag/wait editing,
and isolated/shared model and texture proposals in the assembled scene. The dated
filename is retained for existing links. This section supersedes the historical milestone inventory and
old test counts below; those sections record what was proven at that time.

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
label package independently decoded to exactly the expected MAN. This is included in the current405-test source checkpoint; browser/package evidence remains separate. Menu story
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

**Indexed texture rectangle copy (2026-09-30):** copy an existing 4/8-bpp
image region to another location in the same texture, with draft pixels and
source/destination bounds before Apply. Overlaps read the immutable pre-copy
indices; packed neighbors, palettes, headers and VRAM layout stay unchanged.
Retail texture29 browser checks passed draft/no-write, bounds and stale-hash
rejection, no-op/no-history, Apply, Undo/Redo, Discard, Save/reopen and Build.
Independent package readback matched all pixels/palettes and the saved33312-byte
TIM; three indices/image bytes changed, zero palette words.24 retail-enabled
focused tests passed with no skips. This feature is included in the current405-test source checkpoint; browser
and package evidence remain separate. Gameplay appearance remains deferred.

**Independent animation consumer review (2026-09-30):** Blender 5.2.2 rendered
and evaluated a fresh complete Dolk2 actor0001 GLB (30 frames, ten rigid objects,
three embedded textures). All61 source-decoded samples, including half-frame STEP
holds and terminal pose, matched within0.000018 source units;24 distinct geometry
snapshots establish motion. First/middle/last renders were visually inspected.
The saved Blender scene reopened with all meshes, animation actions and three
packed textures. A reusable offline review tool and [consumer review guide](legaia-glb-consumer-review.md)
are available. Acceptance is specific to this clip; wider clips/consumers, retail
cadence, lighting and gameplay remain unverified. No game was launched.

**Animation scene comparison (2026-09-30):** supported animation inspections now
switch between the inspected animation and Current authored scene, retaining the
selected frame and camera. Switching layers pauses playback; the current layer
disables scrubbing, playback and rate controls. Returning restores the inspected
frame and slider together. A retail actor0011 JSON proposal (15 frames) passed
exact layer/placement/base checks, playback pause, Return retaining the file,
Restore, stale-source withdrawal and unchanged project state, with zero authoring
requests or page errors. Screenshot inspected. This is separate browser evidence;
retail animation timing, playback and gameplay visibility remain deferred.

**Scene proposal comparison (2026-09-30):** model-transform, model-file and
texture proposals can switch between Proposed (not applied) and Current authored
scene while retaining the proposal and camera framing. Exact layer/restore and
unchanged project checks passed in retail browser runs for shared model0074
(11 instances), a JSON model-file proposal, and texture29 (19 geometries,
31 materials, 58 instances). Texture checks also verified unchanged camera and
withdrawal on a stale scene source. These are browser checks, separate from the
390-test Python checkpoint; game appearance and retail visibility remain deferred.

**Object-transform proposal previews:** translation, rotation and uniform scale
can now be viewed before Apply, with proposed/current layers sharing camera
framing. Preview leaves project history and authored files unchanged. The 405-test Python discovery checkpoint covers these services; JavaScript and
browser checks retain their separate evidence. Gameplay acceptance
remains deferred.

**Supported flag operand authoring:** local, global and context flag-bit
serialization has focused source-preservation validation, including rebasing
source owners after an actor append. Fourteen focused flag/movement/project tests passed on
September 30. Source-qualified ScriptFlags project commands, authored summaries,
Undo/Redo and Save/Open are connected. A retail town01 actor0002 CFLAG_SET
bit2-to3 probe changed exactly one MAN byte and survived project reopening.
Ordinary Build and experimental compressed/raw-streaming exports now compose
these operands with audited source offsets. The script Inspector now supports
Apply, Clear and Discard with separate retail/authored/effective operands.
Independent package and rebuilt archive readbacks passed; see the update below. Special context side effects, unresolved
local widths, system flags and branch selectors remain unsupported. The
earlier365/383/390-test checkpoints have been superseded by the earlier392-test run
below. Browser checks for texture dependency inspection, model rotations and
script operand forms remain separately recorded. Manual gameplay verification remains deferred.

**Texture-file proposal preview:** TIM/JSON files can now be inspected before
Apply, with proposed pixels and separate retail/current payload comparisons.
Focused synthetic, retail service and browser checks passed without preview
state, history or authored-file changes. Gameplay appearance remains deferred.

- **Scene editor:** assembled textured field/world-map previews, hierarchy and
  picking, authored/retail comparison, orthographic views, coordinate location,
  actor and scenery transform handles, and inspection of supported animations.
  Full game-equivalent visibility, placement and live actor correlation remain
  unverified where the source evidence does not establish them.
- **Animation authoring:** source-bound channel editing, copy across frames and
  ranges, raw-record/JSON import and export, shared-clip conflict checks, Undo
  and persistence. Proposed files can be reviewed and posed in model/scene
  viewers without applying, then returned to the file form for explicit import.
  Supported full rigid clips export to GLB; retargeting and arbitrary clip
  layouts are still unsupported.
- **Model authoring:** same-layout TMD/OBJ/JSON replacement, complete vertex and
  normal JSON, file-change preview, direct vector Inspector editing, per-vector
  retail reset, and inspected-vertex camera location. Build audits show exact
  scalar changes and link to the matching model/vector with stale-hash checks.
  A model-view wireframe overlay exposes decoded triangle edges, including
  hidden edges; it follows preview vertex updates without authoring changes.
  Added/deleted objects or packets, new vector capacity and changed material bindings remain unsupported. Existing face rewiring/UV/baked-RGB authoring is implemented above. Browser shaders
  do not calculate normal-based lighting.
- **Scene content:** supported dialogue, appearance, transitions, script movement,
  textures, collision and scenery edits use source-validated overrides. NPC
  drafts compose into experimental disc exports. General script/control-flow
  authoring, native spawn scheduling and story behavior remain incomplete.
- **Output and verification:** saved private projects, packages, hashes and
  independent archive/member readbacks are retained for later review. All119
  town01 models passed exact JSON round trips; a retail normal-only edit and a
  combined model/animation package passed offline readback checks.

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

**Gameplay is deferred at the user's request.** These later changes did not
launch the game. Full runtime parity, normal lighting, wider scene/animation
playback, world-map behavior, MAPDSIP coverage and documented runtime acceptance
remain open. The full SDK goal is active, and offline work is not exhausted.

For current details use [SDK status](SDK_STATUS.md),
[feature coverage](FEATURE_MATRIX.md), and the
[deferred gameplay queue](legaia-gameplay-verification-queue.md).

## Historical September 9 milestone evidence

## Source and preservation

The starting revision was `56892d6216cf1ccf87d4a376c8e0feec67ac4182`, based on
upstream `1a64f611`. Recovery ref
`codex/recovery-legaia-stability-20260909` retains that starting point.
Changes are local commits in Recomp. No push or sibling-repository mutation was
performed. Existing generated game/BIOS sources were read by an isolated build;
they were not regenerated or edited. The sibling known-good binary is preserved.
Its mixed source/build provenance is documented in
[the release ledger](legaia-release-parity.md), rather than inferred from a tag.

Disc images, BIOS, decoded retail assets, screenshots, PCM, cards, snapshots,
private projects/packages and build outputs stay outside tracked source under
ignored local paths. Existing `.codex-remote-attachments/`,
`integrations/legaia/inspector/` and `legaia-release/` remain preserved, untracked
material. No proprietary payload was added to these commits.

## Implemented milestones

| Commit | Result |
|---|---|
| `189a2d24` | Static overlay inventory regeneration, restore ownership invalidation and independent controller-port injection. |
| `4d7e955f` | Integrated disc import, scene hierarchy, authoring project, undo/save/reopen and model inspection. |
| `aa3b22ab` | Exact unchanged MAN/LZS round trip and guarded private placement packages. |
| `bae00098` | Generic mod installer resolves assets at their final installed paths. |
| `be90a25d` | Guarded runtime observation and actual mod-sector consumption diagnostics. |
| `c8e69ccd` | Default-stack Windows hashing fix and diagnostic-independent snapshot identity rejection. |
| `a9507c7c` | Bounded TIM decoding and conservative material-address matching. |
| `f506ec8e` | Guarded MAN/model evidence and explicit, ambiguous live actor candidates. |
| `27cf180b` | Strict, versioned town01 field execution profile and live evidence record. |
| `ce747f44` | Private editor Build & Run, owned-process Attach/Stop and upright textured previews. |
| `d1b3b229` | Validate/prepare all snapshot sections before restore; safe partial-command MDEC capacity. |
| `5d8337da` | Remove unnecessary Windows directory rename in private run staging. |
| `946c76d8` | Reject invalid incoming savestate resume addresses before guest mutation. |
| `a9478f88` | Give runtime identity the compiled source-revision stamp. |
| `85fba8a5` | Reusable authored transform templates with provenance, undo/redo and persistence. |
| `cf3a51ae` | Validate actor requirements per HTTP command so template deletion works. |
| `58794999` | Route realtime XA away from CPU data-ready interrupts; fix reproduced 17-frame FMV stall. |
| `c8378677` | Six reference-scoped field-party idle/walk clips with assembled poses, stepping and playback. |
| `487e1716` | Build verified retail baselines after clearing or reverting authored placements. |
| `d4f01910` | Decode model-scoped shared party texture uploads with independent VRAM validation. |
| `0f98218c` | Export supported textured models and static poses as private, validated GLB files. |
| `392de27f` | Connect shared party textures and current-pose GLB export to the editor. |
| `29310f0d` | Verify scene-header ANM associations and assemble 39 town01 actor poses. |
| `c0aabe0d` | Render supported textured scene geometry with mesh picking, focus and authored transforms. |
| `4f865bb3` | Build source-verified scene payloads with bounded caching and request-scoped disc verification. |
| `082e164b` | Search SDK assets and inspect NPC clips, frame exports, scripts and inline dialogue in the editor. |
| `957acb85` | Expose actor-scoped animation/export and read-only script inspection APIs with strict request validation. |
| `27014048` | Add a bounded donor model/animation assignment serializer foundation. |
| `103eb9be` | Inspect verified MAN script paths and inline dialogue with explicit opaque boundaries. |

The earlier reapplied release fixes include CD/XA response visibility,
seek-position refresh, VBlank handling and Windows startup. Current frame
pacing and host timing match `release-full-fixes`. Both inspected manifests
contain the ten intended roles; 0899 is excluded and dynamic caching remains
disabled. MAPDSIP handler seeds do not establish full native coverage.

## Verified workflow and limits

The primary editor workflow imports a verified user-owned disc, lists scenes,
selects imported actors, edits authored transforms, undoes/redoes, saves/reopens,
inspects geometry/textures and builds a private package. The run controller
checks the actual child/listener identity, executable, BIOS, disc and enabled
mod plan; Stop exits the owned child normally. Imported, authored and Live
values remain separate, and failed observation clears transient candidates.

Retail town01 import resolves 52 actors and 119 models. All 29 actor-referenced
models decode. The 96-TIM catalog yields 38 uniquely matched textured material
crops, 26 untextured materials and eight explicitly unresolved materials among
72 references. A separate verified party bank resolves all eight used textured
materials for F0/F1/F2. Six idle/walk clips assemble ten rigid object channels,
with frame stepping and playback in the preview. General NPC/battle animation,
live equipment state, texture residency and animated palettes remain pending.

The central viewport now renders 51 of 52 town01 entities using 28 unique
geometries and 5,920 unique triangles. This includes 39 scene-header poses,
independently checked across 5,028 vertices, plus supported static models and
explicit reference party idle poses. One multipart savepoint remains a marker.
Mesh-body picking, focused textured NPC appearance, authored movement, imported
position tether, undo and model visibility toggle passed browser inspection.
The source-verified request hashes the image once and took 2.145 seconds in the
recorded run. Unknown height/facing and scripted placement/visibility remain
explicit; parked and overlapping instances are retained. Full asset-category
authoring remains outstanding.

NPC playback controls and selected-frame export are now connected: actor0049's
15-frame clip steps/plays/pauses at an explicitly chosen preview rate, and its
Frame5 browser export retains actor/ANM provenance. Search spans 119 models,
52 active-scene actors and one imported scene, including cross-reference and
provenance queries. The read-only script inspector presents seven dialogue
segments and 23 supported instructions for actor0049, preserving its opaque
tail; actor0001 explicitly stops on unsupported opcode0x29. This does not
implement dialogue writes, story-state evaluation or general script execution.

The next writable foundation can borrow an existing same-scene model/animation
pair for a compatible initial MAN header. Seven focused tests pass, including
actor5 borrowing actor40's pair with only two decoded bytes changed and an exact
compressed round trip. This helper is not yet connected to authored commands,
the editor or package builder, and its gameplay behavior remains unverified.

The final importer suite passes all 83 tests with private retail input enabled;
six focused HTTP/project tests also pass. Script fixtures retain retail text
hashes and structural expectations rather than dialogue payloads. The updated
main editor remains on port4388; the private acceptance editor was closed.

Authored templates transfer saved position axes to another imported actor,
preserving unspecified axes. The browser capture/apply/undo/redo/save workflow
and reopened project were checked with a synthetic two-actor fixture. This
does not implement native actor creation or model/animation presets.

Earlier cold field runs consumed all 24,894 patched bytes across 13 sectors
without a disc guard failure and rendered Rim Elm. The v2 profile accepted 90
nodes with strict executable, witness, scene, generation and epoch checks.
An actor candidate's MAN header contained authored X9984 versus imported X9920.
Its world position was parked; this does not establish visible actor placement,
confirmed identity or successful revert. See
[the field evidence](legaia-sdk/live-field-20260909.md).

Those early private builds had empty Release optimization flags. Subsequent
builds restore standard MSVC `/O2 /Ob2 /DNDEBUG` and `/GR /EHsc`; functional
captures from the earlier builds are not performance truth. Software rendering
is the tested backend. HLE is the current shipping tier; LLE/oracle parity is a
separate acceptance task.

The earlier optimized runtime contained the runtime changes through `a9478f88`:
SHA-256 `99d4e3b6742c864c3087a73c356f0d0de51bdc623accb0e1dd8e026052e94afa`.
The protocol now reports `nightly-16-ga9478f88-dirty`. The dirty suffix includes
in-progress documentation/editor work; the ignored final validation manifest
records exact runtime source hashes independently. Its new cold run reached
New Game, name selection and Rim Elm with the authored overlay fully consumed.
After name confirmation, the editor accepted all 90 actor prefixes (14,040
bytes; 94 requests; 1,114.530 ms total) and all 90 binding samples (2,670 bytes;
31 requests; 414.146 ms). They produced 82 candidate links, zero confirmed
identities. Actor0001's candidate header still carried X9984 and its world
position was parked. Stop exited normally and cleared the Live candidates.

The opening-FMV retry was subsequently reproduced without input or restore
and traced to erroneous CPU data-ready interrupts on XA-only sectors. The old
FIFO video header was copied again, causing retail chunk validation to discard
partial frames. Commit `58794999` fixes generic sector routing. The corrected
optimized executable has SHA-256
`148c66b1d509d4728d4ea3fcd24e7267776da5ee8104db72f27cfffed625ba6e`. Its
embedded configure-time label is stale; exact binary and source hashes are
recorded independently. Two no-input cold runs decoded 1,337 movie frames;
the later run visibly reached New Game / Continue and subsequently restarted
attract playback. Both exited normally. Other FMVs and audible quality remain
separate acceptance tasks. See the release ledger for root-cause evidence.

A new authored savepoint build moved town01 actor0052 from retail `(9792,8512)`
to `(4480,11904)`. Its short source script contains no own position override.
The cold game displayed the purple savepoint beside Vahn in the opening
Village Elder dialogue, and the guarded candidate carried both the edited MAN
header and world position `(4480,-128,11904)`. All 24,894 overlay bytes were
consumed without guard failure. This proves the chosen visible edit; generic
identity correlation remains conservatively classified as a candidate. A
fresh retail-baseline run completed revert acceptance: zero overlays and zero
modified bytes, no savepoint beside Vahn in the same first dialogue, and a
guarded candidate back at retail world `(9792,0,8512)`. That final coordinate
sample followed one dialogue advance to execute the required VM witness; the
guard was never weakened. Both private processes exited 0. The complete pair
is recorded in `local-output/sdk-20260909/visible-placement-revert-acceptance.json`.

## Focused validation

One retail idle save/restore comparison now passes on the fixed binary.
Three ten-second windows measured cold/restored median 59.85/60.02 FPS and
16.6897/16.6894 ms frame-period p95; static hits remained about 5,100/second.
Save/load completed, the same scene stayed visible, and settled windows added
no audio underruns or ownership-validation churn. A nonrecurrent VM witness
was cleared by restore and did not execute again, so the strict full Live
profile correctly remained unavailable. This bounded result does not establish
cross-scene or repeated-restore performance, nor observer reacquisition.

- All 62 importer/project/serialization/texture/animation/export tests passed with the local
  retail disc configured, including the retail-gated cases.
- Twelve observer/profile/correlation tests passed, including stale identity,
  wrong backend/hash, bounded reads, ambiguity and transient-layer clearing.
- Six focused project/template/HTTP tests passed. The exact Delete request
  failed before the route-validation fix and passes afterward; malformed
  actor commands still reject without changing project state.
- Production snapshot and savestate caller tests passed malformed and partial
  files, missing/duplicate sections, raw/zlib/reordered/repeated restoration,
  allocation failures, partial MDEC continuation, blob/file resume rejection
  and preservation of the live machine on ordinary failure.
- The actual mod runtime passed with the Windows default 1 MiB stack after the
  hashing-buffer fix; the previous implementation reproduced `0xC00000FD`.
- The isolated two-worker MSVC Release build passed. Browser checks covered
  authoring, textured preview, template application, private launch identity,
  guarded Live rejection and graceful owned-process Stop.

These focused results do not replace the comprehensive plan or manual audio,
physical-controller, battle and transition acceptance. The final private
manifest, screenshots, PCM and full guarded observations are retained under
`local-output/sdk-20260909/`; none is tracked source.

The editor now also exports the displayed party pose or a full supported raw
model through Export GLB into private project `Exports`. Vahn and tree outputs
pass Khronos validation with zero errors/warnings and import/render in Blender
5.2.1. The browser selected idle frame2 and produced a ten-object, 496-triangle,
four-texture export with explicit static-pose limits. All three party idle/walk
previews were visually checked with face/clothing textures and frame controls.
That initial checkpoint did not include animated GLB channels. As of 2026-09-12,
full rigid-object clips are available through Export full clip GLB with an
explicit chosen rate. A 30-frame actor export passed Khronos validation with
zero errors/warnings and independent glTF-Transform import (10 nodes, 20 channels).
Rendered animated playback in Blender/Unity remains unverified. Native replacement
and physical-meter scale are not established by these interchange exports.

## Historical remaining-work assessment

The reproduced STR/XA stall is fixed and reaches the title menu. Muscle Dome
relocation remains unresolved: the cited old change documents a repair but contains no
recovered implementation. A title-layer fix requires the failing lifecycle and
retail comparison, not a guessed runtime address patch.

At this milestone, the SDK proved a visible savepoint edit and fresh retail revert. The following was the remaining-work assessment then; use the current status above for later implementations. Full
posed scene rendering, general animation tools, asset replacement, native
entity/templates, dialogue encoding and editing,
script opcode/CFG tools, event flags, transitions and world-map authoring are
still incomplete. Unknown semantics remain explicit. Audio continuity,
field/battle/world-map transitions, physical controller behavior and
cross-scene/repeated restore performance also remain unaccepted.

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
raw-streaming route has not yet received a retail wait probe. Fifteen selected
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


Model-object transform previews (2026-09-30): the vector Inspector has explicit
Preview buttons for translation, quarter-turn rotation and uniform scaling, with
an orbit/zoom canvas and Proposed/Inspected current layers under shared framing.
The server binds previews to the inspected effective SHA and uses the same
serializers as Apply, including a shared translation serializer. Invalid fields,
stale hashes, overflow and vector drafts reject previews. Input changes, dialog
close and delayed responses withdraw proposals; comparison-layer changes retain
geometry. Seven focused model tests passed. Retail model0009 object1 previews
matched exact Apply-operation bytes for all three transforms while project state
and authored-file hashes stayed unchanged. Browser checks passed all transforms,
layer comparison, draft/input guards, close/reopen and delayed-response withdrawal
with zero page errors; scale/rotation screenshots inspected. An initial browser
failure exposed comparison-select input events clearing the preview; fixed and
rerun successfully. Private evidence: local-output/sdk-20260909/model-scale-project-20260930/
object-preview-service-check.json, object-preview-browser-check.json and
object-preview-{translation,rotation,scale}.png. Temporary server/browser stopped.
No game launch, package installation or gameplay claim. The383-test checkpoint
predates this addition; full SDK goal remains incomplete.


Scene model-object proposal inspection (2026-09-30): a validated translation,
rotation or scale proposal can be inspected on one renderable instance in the
authored assembled scene. The endpoint resolves the existing source-bound pose
and applies local coordinates through its supported transforms, preserving
instance placement and source geometry. It rejects stale scene keys, wrong
asset/instance bindings and unsupported pose layouts. Proposed geometry is isolated
from shared instances and marked not applied. Restore recovers the exact scene;
Return to model vectors retains the input parameters for explicit Apply or discard.
Animation playback controls are hidden for static shape inspection and restored
when entering animation inspection. Ten focused model/pose tests passed. Retail
browser verification used environment://town01/field-map/cells/05913, model0009,
animation4/frame0; scene matrices, other instances, base scene and project state
were preserved, with exact Return/Restore and zero page errors. Stale scene keys
and unknown instances rejected without project changes. Screenshot inspected.
Private evidence: local-output/sdk-20260909/model-scale-project-20260930/
scene-shape-browser-check.json and scene-shape-preview.png. Browser/server stopped;
no game launched or package installed. Gameplay placement/visibility remains
unverified. The383-test checkpoint predates this feature; full SDK remains incomplete.


Proposed model-file scene inspection (2026-09-30): TMD, OBJ and JSON replacement
files can now be inspected on a selected supported scene instance before Apply.
The endpoint revalidates the file, inspected proposed TMD hash, active scene source
key and asset/instance binding, then uses the same pose-preserving scene proposal
service as object transforms. The selected file remains pending during inspection;
Return to model file and Restore recover the exact scene and retain it for explicit
Apply or Discard. New model contexts clear retained draft metadata. No proposal
creates authored files, commands or history. Nine focused model/file/pose tests
passed. Retail browser checks passed all three formats, one-instance isolation,
scene matrices/base/project preservation, Return/Restore file retention, discard
and stale hash/source/instance/base64 rejection with zero page errors. Screenshot
inspected. A43090-byte JSON proposal passed the upload route with exact proposed
hash and unchanged project state/authored-file hashes. Private evidence under
local-output/sdk-20260909/model-scale-project-20260930/model-file-scene-browser-check.json,
model-file-scene-large-check.json and model-file-scene-preview.png. Temporary
browser/server stopped; no game or package installation. Gameplay placement and
visibility remain unverified;383-test checkpoint predates this addition.


Shared model proposal impact (2026-09-30): object-transform and model-file scene
inspection now offer All supported model instances. Each instance retains its
existing placement and pose; proposed geometries are grouped by the source scene
geometry key rather than duplicated per placement. Nonrenderable matching instances
are reported as unavailable and remain unchanged. Unsupported renderable pose
bindings reject the proposal. The client verifies instance/source-geometry bindings,
isolates proposal assets from the immutable base and frames affected instance bounds.
Restore and Return retain the existing authoring workflow. Ten focused file/model/
pose checks passed, including two distinct synthetic pose geometries, repeated
placements and unavailable instances. Retail browser town01 model0074 previewed
all11 supported placements using one geometry; placements, unrelated entities,
base scene/project state and exact Return/Restore passed with zero page errors.
The JSON file all-instance selector and strict boolean scope rejection also passed
on model0009. Private evidence: local-output/sdk-20260909/model-scale-project-20260930/
shared-shape-browser-check.json, shared-shape-preview.png and
shared-file-scene-browser-check.json. Initial camera framing included unrelated
scene bounds; adjusted to affected instances and rechecked. Screenshot inspected
for proposal controls; scene occlusion and retail visibility remain approximate.
Temporary browser/server stopped. No game or package
installation.383-test checkpoint predates this addition; gameplay acceptance
remains deferred and the full SDK remains incomplete.


Proposed texture files in the scene (2026-09-30): validated TIM/JSON proposals can
now be inspected before Apply across their decoded scene materials. A private
in-memory catalog substitutes the proposed TIM alongside current authored texture
bindings, then uses the existing static VRAM image/CLUT decoder for model and ground
materials. Separate field-party banks retain their established scope. Geometry,
topology, poses and placement remain source-owned; the renderer only substitutes
texture payloads. Changed material/instance counts and unavailable geometries are
explicit; the16MiB scene texture budget still applies. Candidate hash and scene key
are revalidated. Closing the proposal withdraws delayed replies. Restore/Return
recover the exact scene while retaining the selected file for explicit Apply or
Discard.23 focused retail-enabled texture tests passed with no skips, including
prepared-ground catalog substitution without source mutation. Retail texture29
JSON browser probe changed31 materials across19 geometries/58 instances; vertices,
topology, poses, matrices, base/project state, exact Restore/Return, retained file,
discard and stale hash/source/base64 rejection passed with zero page errors.
A held response after closing the proposal did not change the scene. TIM readback
matched the candidate hash and same31 materials/58 instances. All11 authored-file
hashes remained unchanged. Screenshot inspected for proposal controls; visual
occlusion remains approximate. Evidence under local-output/sdk-20260909/model-scale-project-20260930/
texture-scene-browser-check.json, texture-scene-tim-check.json,
texture-scene-authored-check.json and texture-scene-proposal.png. Temporary browser/
server stopped; no game/package installation. Runtime VRAM residency and gameplay
appearance remain unverified;383-test checkpoint predates this addition.


Historical regression checkpoint (2026-09-30): all390 Python discovery tests passed
in163.243s against05e93405, exit0, retail disc supplied, no skips. Owned process
continued to terminal completion without restart; no application repairs required.
Texture usage/operand layer Node checks and editor syntax passed. Evidence:
local-output/sdk-20260909/sdk-regression-20260930-scene-proposals.log and matching
.json metadata/hash. This supersedes the383-test checkpoint and historical
predates notes for current Python services. Browser workflows remain separate;
no game launched, runtime parity/gameplay acceptance still deferred.
