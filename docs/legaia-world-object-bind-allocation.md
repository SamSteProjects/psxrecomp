# Scripted World Object Bind Allocation

In progress — 2026-10-11. This is a native writer prerequisite, not an available editor feature or gameplay acceptance.

Script-managed placed World objects need more than a copied decoration. The pinned Andrew reference `field_objects.rs` describes the scene-init sweep resolving a kind-1 bind at the object's footprint anchor; the bind supplies a flat MAN record index and a partition-0 animation header. The later subarea sweep has different ownership and skips anchors carrying `0x400`. Existing walk-decoration creation remains a separate workflow.

`importer/worldmap_object_bind_allocation.py` qualifies all four primary and fallback table spans and resolves the selected original primary donor through the existing MAN reader. A request copies its MAN index and opaque gate byte to a distinct native anchor. It refuses coordinates already claimed by either lookup table, shadowed donors, malformed or non-P0 MAN ownership, nonzero append preimages and overlapping tables. Complete MAP readback restricts changes to the kind-1 count and appended rows; all original rows remain byte-identical. The result explicitly reports `placement_allocated=false` and `gameplay_verified=false`.

Seven focused tests pass, including literal complete-MAP comparison, immutable inputs, table ownership, primary/fallback shadowing, MAN alias/header refusal and bounded request domains.

Fresh retail probing changes the next implementation step:

| Scene | Original kind-1 rows | End offset in primary block | Following kind-2 offset | Direct append |
| --- | ---: | ---: | ---: | --- |
| map01 | 6 | 44 | 46 | Refused |
| map02 | 33 | 152 | 154 | Refused |
| map03 | 20 | 100 | 102 | Refused |

All three sources have only two intervening bytes, so even one four-byte bind would overlap the next native table. The helper deliberately does not relocate or claim another zero region as free. Private evidence is `local-output/sdk-20260909/world-object-bind-allocation-20261011/proof.json`; it contains source hashes and refusal results, not extracted game payloads.

Next work must qualify table relocation, then compose bind allocation with placed-record allocation and anchor ownership. Project provenance, Review/Apply, Undo/Redo, persistence, Current viewport identity and package Build must follow before this becomes an editor workflow. No native compile, game launch, runtime attachment, installation or disc export was performed. Gameplay verification remains deferred.

## Explicit Table Relocation — 2026-10-11

The writer now accepts an explicit even `relocation_offset` within the primary 0x2000-byte block. It copies every original kind-1 row, in source order, into a completely zero destination outside all known table spans, appends the donor-derived rows, and updates only the kind-1 signed offset/count header. Original table bytes remain intact; other table offsets, counts and rows are unchanged. Full MAP comparison constrains every changed byte to the header and destination span. Default direct-append behavior retains its prior refusals.

Native evidence is now stronger than a format inference: fresh retail PROT[897], SHA-256 `216f846db5ab085a295cef4064747380a06c995caa3e1b2773e78a1d349f126b`, matches the six native instruction words at `0x801D5AE0` through `0x801D5AF4`. They index the header by kind times four, load the signed offset/count, and add the offset to the block pointer. This agrees with pinned `field_regions.rs::parse_tile_triggers`; the generated release routine was inspected separately.

Nine focused tests pass. Private reproducible verification at `local-output/sdk-20260909/world-object-bind-relocation-20261011/verify.py` and `proof.json` qualifies complete literal MAP bytes and independent native-offset scans for map01, map02 and map03. Experimental destination offsets are 418, 500 and 128 respectively. All 198, 43 and 34 existing primary/fallback coordinate lookups retain identical resolver results, including precedence, source row identity and MAN headers.

These checks qualify native serialization and lookup preservation. A zero preimage outside known tables does not prove that every runtime subsystem treats that region as free. The audit keeps gameplay unverified, and the private proof explicitly marks opaque-zero runtime ownership unverified. Relocation is therefore an experimental native prerequisite, not a user-facing scripted placement workflow. Placed-record/cell ownership composition, project/editor history and persistence, package Build and eventual gameplay verification still remain.

## Composed Scripted Placement Bytes — 2026-10-11

`importer/worldmap_scripted_placement_allocation.py` now composes a placed-record clone with its native footprint-anchor marker and donor-derived kind-1 bind. It requires a resolved init-owned placed donor, a distinct authored placement UUID, an unused zero record, empty source cells and explicit `shared_script=true`. The bind UUID derives from the placement UUID. The source script remains shared; this does not allocate or duplicate a MAN record.

The writer preserves the donor's complete record except requested signed16 offsets, low12 yaw and the target's original four terrain bytes. It retains signed footprint offsets, checks the resulting anchor remains inside the native grid, and sets anchor cell `0x400`. Source and anchor cells can differ. Neither can belong to an existing placement anchor or another request; an existing init marker or primary/fallback bind refuses. A bound donor must resolve through an effective original primary P0 row. Original placed/decorative seeds, unresolved records and excluded coverage remain unchanged after full decode.

Seventeen focused allocation/bind/object-script tests pass, including literal complete MAP comparisons for same-cell and separate anchors and ownership/domain refusals. Fresh retail map01/map02/map03 composition also matches independently assembled complete MAP bytes and the donor's MAN header. Evidence is private `local-output/sdk-20260909/world-scripted-placement-20261011/verify.py` and `proof.json`. Experimental fixtures use donor cells 2656/6205/2353, target cell 0 and free records 4/5/5. These are serialization fixtures, not recommended gameplay placements.

This is still an incomplete authoring workflow. No project command, Review/Apply service, editor control, persistence binding or package Build consumes the new writer yet. Shared-script gameplay effects, runtime actor-pool demand and opaque zero relocation-space ownership remain unverified. The next integration must retain those limits, qualify current coauthors and provide provenance/history/persistence before exposing creation. Gameplay verification remains deferred; the full SDK goal remains active.

## Read-Only Project Source and Review — 2026-10-11

The project service `sdk/worldmap_scripted_placement_allocation.py` and HTTP routes `/api/worldmap-scripted-placement-source` and `/api/worldmap-scripted-placement-review` now expose this prerequisite through fresh Edit-mode source keys. Source provides separate original/Current MAP and MAN bytes, fallback witness/hash, floor LUT, eligible primary-P0 placed donors, preliminary empty cells and free records. A deterministic zero relocation candidate reserves room for up to 32 additional rows; this still does not establish runtime ownership of opaque zero space.

Current composition retains existing World transform and authored decoration replay, plus Current World fixed arguments and branch edits. Existing imported scene Environment, Collision, FloorTiers, RegionBounds, TriggerCells and TriggerScripts MAP coauthors pass through their native writers against the immutable source. Declared wall-bit and floor-nibble masks preserve independent fields; overlapping coordinate/record bytes refuse divergent edits instead of forming hybrid values. FloorHeights coauthors explicitly refuse pending their MAN composition path.

Review requires exact native requests and explicit shared-script scope, rejects UUIDs already held by authored decorations, emits full candidate MAP bytes and audit, and binds its reproducible Review key to project path, source key, Current source hashes, request, relocation and proposal. Both routes are read-only and report `build_ready=false`. Project documents and Undo/Redo remain untouched.

Twenty focused tests pass, including HTTP schemas, reproducibility, stale/Edit guards, retained identity refusal and coauthor-mask/conflict checks. An actual saved private project with existing World script/branch and placement coauthors supplies 6/33/20 donors across map01/map02/map03. For all three kingdoms, HTTP Review equals direct project Review and complete native candidate bytes, with document/history/source-key baselines unchanged. Reproducible private evidence is `local-output/sdk-20260909/world-scripted-placement-review-20261011/verify.py` and `proof.json`.

Apply, a retained scripted-placement component, Undo/Redo persistence, Current viewport identity, editor controls and package Build remain unfinished. No native compile, game, runtime attachment, install or disc export was run. Shared scripts are not new NPC behavior; actor-pool demand, runtime zero-space ownership and gameplay still require later evidence.

## Authored Floor-Height Composition — 2026-10-11

The read-only scripted placement source/Review service now qualifies an imported scene's FloorHeights binding through the existing project validator and composes its signed16 MAN height header with Current World arguments/branches through the existing floor-height serializer. Original MAN bytes remain separate. Source and Review identify `scene_man_coauthors` separately from MAP coauthors. The earlier FloorHeights refusal is superseded by this path; a changed source hash or overlapping authored MAN header still refuses.

Floor LUT values now come from the fully composed Current MAN. Eligible donors and proposed native seeds therefore use authored heights consistently. Existing authored decoration seed audits are refreshed against the same Current MAP/height table; their retained native records and stable authored identity are preserved.

Twenty-three focused regression tests pass. Fresh private three-kingdom verification imports immutable map metadata into isolated in-memory views of the saved project, authors all sixteen heights, and compares complete Current MAN bytes with literal signed16 header replacement over the prior Current script/branch bytes. Proposed Y equals the negative authored target-tier height. Each kingdom's two retained decorations matches independently decoded Current positions. Direct and HTTP Review agree exactly, and original project, view document, Undo/Redo and source-key baselines remain unchanged. Evidence: `local-output/sdk-20260909/world-scripted-placement-heights-20261011/verify.py` and `proof.json`.

This removes one coauthor integration gap. Scripted-placement Apply, retained lineage/persistence, Current viewport/editor controls and package Build remain unfinished. Runtime actor demand, opaque relocation-space ownership and gameplay remain unverified. No game, runtime attachment, installation or disc export ran. Existing focused floor-height regression coverage may build private data packages; no native recomp compilation occurred.

## Retained Replay and Current Ownership Merge — 2026-10-11

The prerequisite `sdk/worldmap_scripted_placement_binding.py` defines a dedicated owner/component and a bounded native ledger. Validation requires exact source/base hashes, the imported disc identity, ordered operations, unique authored UUIDs and native record owners, explicit shared-script scope and a total creation budget of 32. Each operation retains its requests, explicit relocation offset and complete proposed MAP checksum.

Replay takes a caller-qualified immutable base MAP and Current MAN/fallback witnesses. It reproduces each complete native candidate in order and refuses a changed base, fallback or operation checksum. Subsequent operations can clone previously authored placed objects. The module does not retain files or mutate the project; callers must validate the ledger and qualify its immutable source before replay.

Current merge preserves later unrelated MAP edits over retained creation bytes. It protects complete created record spans, source/anchor cell words, offset/count fields and every copied/allocated bind-table byte, including zero-valued owned bytes. A changed source kind-1 table requires renewed ownership review so the relocated copy cannot silently become stale. Full table parsing and Current placement decoding check original seed, unresolved and excluded coverage, and every new object's init ownership. Independent wall/floor bytes and existing donor transforms can change while the authored clone keeps its retained values.

Three focused ledger checks cover two-operation replay, creation from an authored donor, source/checksum/schema/identity refusals and literal Current merge/conflicts. Private actual-project three-kingdom qualification is `local-output/sdk-20260909/world-scripted-placement-ledger-20261011/verify.py` and `proof.json`. Complete replay must equal project Review; independently assembled MAP bytes preserve a later wall bit and donor transform. Three owned-byte conflicts per kingdom refuse, and project document/history/source key remain unchanged.

This ledger is not registered for project persistence or Build yet. Apply publication, private base-file retention, Save/Open validation, editor Current selection and package delivery remain unfinished. The full SDK goal remains active; gameplay and runtime zero-space/pool qualification remain deferred.

## Apply, History and Save/Open — 2026-10-11

`allocate_scripted_worldmap_placements` is now a normal project command. Apply re-prepares its exact requests and source key, checks the Review key, then publishes the qualified base MAP privately under `Authored/WorldMapBases/<sha256>.map`. Paths derive only from the content hash and remain within the project; complete size/hash readback is required before the dedicated `WorldMapScriptedPlacementAllocations` component enters project state. A stale Review refuses before publication. The command records before/after state in the existing Undo/Redo system.

Review now returns the proposed retained binding and previous binding. Subsequent creation operations independently replay the original base and merge later Current coauthors; their complete result must equal direct allocation from Current. Source composes the saved ledger, exposes distinct authored scripted placements and remaining total creation capacity, and refreshes all authored seed coordinates against composed Current MAP/floor data. Source witnesses remain separate from immutable retail provenance.

Save/Open admits only the exact dedicated component, validates source/operation/identity domains and verifies the content-addressed base file. Missing or modified retained bytes refuse. Authored Assets lists the scripted placement owner. Native source keys and readback still qualify Current on use. This does not yet add scripted objects to the main browser geometry/selection workflow.

Thirty-four focused project/allocation/bind/floor checks pass with retail input. The final creation-budget/source-capacity changes pass the seven affected focused checks. Actual private project copies pass four HTTP Apply workflows: two successive Map01 operations (the second uses the first authored object as donor), plus Map02 and Map03. Each passes stale-key refusal, complete reviewed/Current bytes, Undo/Redo document restoration, Save/Open and authored identity readback. Retained-base tampering prevents reopening. The original project is unchanged. Evidence: `local-output/sdk-20260909/world-scripted-placement-persistence-20261011/verify.py` and `proof.json`.

Scripted-placement package delivery explicitly refuses in Build until serialization integration is implemented; it cannot silently omit this component. Editor creation controls, full Current geometry/selection/bind inspection and package delivery remain unfinished. Runtime demand, shared-script effects, opaque zero-space ownership and gameplay remain unverified. No native recomp compilation, game, runtime attachment, install or disc export ran. Existing focused floor regression coverage builds private data packages; the scripted-placement Build attempt is a verified refusal.
