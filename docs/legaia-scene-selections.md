# Saved scene placement selections

## Select Model Instances

Select an imported actor, authored NPC draft or static decoration in the current
**Authored scene**, then choose **Scene tools -> Select model instances**. The action
replaces the placement selection with all eligible current scene placements that
share the selected row's exact SDK model asset identity. Hidden placements and
qualified bindings without rendered geometry remain eligible. Ground and other
nonplacement rows are excluded. This is identity matching, not mesh/texture/hash
similarity or a claim of runtime model use.

The current focus stays active. The hierarchy query is cleared and relevant folds
are revealed. Actor-only results populate the actor group; scenery-only results
populate the scenery group; actor/NPC or other mixed results populate the existing
scene-placement group. **Review group placements**, **Move scenery group** and
**Move scene placement group** retain their existing source-qualified Review/Apply
workflows. **Focus** frames a group; **Saved scene selections** can retain the IDs.
Selection itself creates no command, authored edit or history step.

Edit mode, a current authored scene preview and a qualified selected model are
required. Busy/held proposal tools, Retail comparison mode, missing model bindings,
conflicting/duplicate identities, stale source or focus and more than 128 matching
placements refuse selection. Oversized groups are never trimmed; use hierarchy
queries to select a smaller group instead. Hidden members stay hidden until an
explicit visibility action.

Offline checks passed (2026-10-07): three focused Node suites, two JavaScript syntax
checks and actual private Town01 editor checks at 1440 and 400 px. Five actors and
11 scenery placements matched independent SDK preview groupings, included a hidden
focus and reached the exact dedicated Review targets. The shared hierarchy-query
handoff regression passed for 12 placements. A separately prepared private project
with one SDK-created NPC also passed exact mixed actor/NPC model selection and
Review. All reviews were cancelled. Retail comparison blocked selection. The
prepared documents, Undo/Redo stacks and saved file sizes/timestamps stayed unchanged.
No native Build, game launch, runtime attachment or installation occurred; the NPC
fixture was not spawned. Gameplay remains deferred.

Private evidence: `local-output/sdk-20260909/model-instance-selection-20261007/`
and its `npc-mixed/` directory (`browser.json`, `readonly.json`, fixture receipt,
browser logs and wide/narrow screenshots). Earlier passing pre-reveal logs remain
preserved. These are focused editor checks, not full SDK or gameplay acceptance.


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

Choose one imported actor, NPC draft or static decoration, a placement group, or use
**Select scene placements** for a mixed group. **Saved scene selections** stores
1–128 distinct scene placements under a scene-local name. **Save current
placements** captures source identity and membership. Save the project to retain
it across sessions. Placed scenery and ground are excluded.

The dialog supports **Rename selection**, **Replace with current placements**
and **Delete selection**. Each operation has one Undo/Redo entry and changes
editor metadata only. Names are unique per scene; the library allows 128 sets.
**Recall placements** can switch to the saved imported scene. It verifies fresh
source membership, selects the focused entity and recalls actor-only, scenery-only
or mixed membership into the corresponding existing placement tools. NPC-only
sets focus a draft or retain multiple draft IDs. Opening the NPC group Inspector
tool seeds those recalled IDs for placement or removal review. Mixed NPC sets feed
the mixed placement tool; the NPC tool scopes them to their NPC members explicitly. A single
member focuses one placement. Recall does not apply saved transforms or move
objects; edited objects keep their current authored positions.

The library stores imported metadata identity and MAP identity when scenery is
included. Project metadata can reopen without the disc; Create/Replace/Recall
with scenery require the current verified source. Missing/drifted input rejects
recall. Pending Close, changed context and late responses cannot reinstate a
cancelled selection. Changed reimport is blocked while sets or their undo history
still bind the prior source. Rename/Delete remain metadata-only operations. NPC IDs retain their current
authored positions and names. Deleted NPC references remain portable metadata;
Create/Recall reject unavailable members. Undo deletion restores recall.
A set containing a deleted NPC can still be renamed, deleted or repaired with
**Replace with current placements**. Replacement verifies the saved import/MAP
source even when dropping all scenery, requires every new member to be available,
and retains the set identity/name. Undo restores its previous missing membership.

## Verified offline workflow — 2026-10-01

38 focused Python checks passed in 2.554s; 32 Node files and 33 syntax checks
passed. Actual Town01/Dolk2 browser checks covered Create/Rename/Delete/history,
Save/Open, cross-scene mixed recall, single-decoration replacement/recall/Undo and
pending source/recall cancellation. Zero page errors; screenshot inspected.
A saved project copy retained exact membership; normal Build produced identical
package bytes before and after editor-only selection metadata. Private evidence:
`local-output/sdk-20260909/scene-selection-sets-20261001/`.
No game launched. This does not establish runtime visibility, parenting,
instantiation or gameplay position parity.


## Scene Selection Metadata Transfer

In **Saved scene selections**, select a current group and choose **Export selected scene selection JSON**. The `legaia.scene-selection-transfer.v1` envelope contains only its name, historical stable group ID, imported scene digest, optional source MAP digest and sorted placement IDs. It contains no retail model/script/map payloads and no transforms. File size is bounded to 256 KiB; groups remain bounded to 1–128 placements.

Choose that JSON through **Import scene selection JSON**, review its metadata and proposed name, then choose **Import as new scene selection**. Import requires the current exact imported scene source and available eligible placement IDs. Static decorations require the matching MAP digest; actor/NPC-only groups require a null MAP binding. Missing NPC UUIDs, unsupported/runtime IDs, foreign sources, unsorted/duplicate membership and unsupported envelope fields refuse. NPCs are not created by import; matching drafts must already exist, such as in a full project copy. The proposed distinct name can be changed before Apply.

The existing source-qualified create command verifies membership against native source bytes and creates a fresh group UUID. Import selects the new group, integrates dirty/change review, atomic Undo/Redo and Save/Open, and supports the existing Recall placements workflow. Original group identity and members remain intact. Closing the dialog invalidates late file reads; source/selection changes during reading refuse publication. Export/import do not move objects, alter native game content or control runtime state.

Offline checks passed on 2026-10-08: eleven existing Python selection tests, focused transfer/selection Node suites and affected JS syntax passed. Transfer checks cover detached output, exact create commands, actor/NPC/decoration membership, source/MAP bindings, canonical bounds, Unicode names, stale/foreign/missing/unsupported refusal and the byte budget. A private Town01 fixture used the SDK's source-binding service to prepare an actor/verified-static-decoration group. The actual browser exported it, refused a foreign MAP digest without issuing a command, canceled a delayed read and reopened, imported/selected a new UUID, recalled the exact mixed placements, and passed Save/independent Open/Undo/Redo. NPC transfer was checked by the focused Node suite; the browser fixture contained no NPC draft.

Wide/400 px scrolled transfer controls were inspected and dialog width checks passed, with no page errors. Complete prepared private document/imports/database/files and original Undo history were restored with one legitimate Redo; native Build key and actor state stayed unchanged, and helpers closed. Evidence: `local-output/sdk-20260909/scene-selection-transfer-20261008/`. Initial fixture preparation refused decoration cell 0 as unsupported, then selected a static cell using the SDK's source predicates and verified it through the source-binding service. A mistaken fixture helper method name was corrected before any preparation command ran. No package Build, native recompilation, game or runtime attachment ran. Metadata transfer needs no gameplay verification; the full SDK goal remains active and solo work continues.
