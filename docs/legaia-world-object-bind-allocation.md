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
