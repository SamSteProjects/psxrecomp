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
