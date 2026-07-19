# Future imported-to-runtime correlation signals

Status: research inventory only. No matching algorithm or live actor correlation is implemented.

The eventual matcher must operate within one verified scene epoch and support exact match, unique multi-signal match, ambiguous candidates, no match, stale slot and conflicting evidence. It must never use nearest-position matching or assume pointer/table index equality is actor identity.

| Candidate | Availability | Value | Limitations |
|---|---|---|---|
| Imported MAN partition/record index | Imported directly; runtime unavailable | Strong if found | No runtime field is proven. `.MAP` object index `+0x60` is a different namespace. |
| Model pool/index | Imported directly; runtime conditional | Strong/supporting | `.MAP` object model index `+0x64` is proven only for static-object actors. MAN-NPC selector field is unknown. |
| Stable model asset identity | Imported directly; runtime derivable in principle | Strong | Requires a proven runtime TMD/object-table pointer-to-pool mapping per actor class. Pointer equality alone is unstable. |
| X/Z position | Direct on both sides | Supporting | Runtime movement, script teleports, duplicate placements and parked `(127,127)` actors make it non-unique. Exact position is useful only as one signal. |
| Y position | Runtime direct; imported unavailable | Weak | Imported town01 Y remains unknown. |
| Heading/yaw | Runtime direct; imported derivable from script in Andrew only | Weak | Mutable and absent from the accepted importer contract. |
| Animation-record ID | Imported direct; runtime pointer only | Supporting if mapped | Requires a proven active-bank pointer-to-record mapping. |
| Actor initialization order | Scene-dependent, not yet observed | Supporting | Allocation and pre-run scripts can reorder or suppress actors. |
| Pointer-census index | Direct but per-frame | Unsafe | Census is distance-culled, filtered and rebuilt; index changes are expected. |
| Linked-list order | Direct but lifecycle-dependent | Weak/unsafe | Relinking and multiple actor classes can reorder nodes. |
| Field-script pointer | Runtime conditional; imported source known | Strong in principle | Requires mapping live MAN buffer spans to imported record spans without exporting bytes. |
| Movement-script reference/cursor | Runtime conditional | Supporting | `+0x94` is subclass-dependent and currently Contradictory. |
| `.MAP` object record index | Runtime direct for static props | Strong for props only | Does not identify MAN partition-1 actors. |
| Actor flags/class | Runtime direct | Supporting | Only traced bits are meaningful; many actors share a class. |
| Spawn/lifecycle frame | Derivable by observer | Supporting | Requires uninterrupted epoch observation and canonical overlay identity. |

## Ranked recommendation

For MAN NPCs, the best future composite is expected to be a proven MAN record/source pointer plus model pool/index or stable model identity, with exact X/Z and initialization order as supporting evidence. None of the strong runtime half is currently proven.

For `.MAP` props, object-record index plus the subclass-scoped model pool and source scene may provide an exact structural key. That is a separate correlation namespace from the accepted MAN actor importer.

Position-only, census-index-only, slot-index-only and nearest-neighbour approaches are unsafe. A runtime pointer is at most an epoch-scoped locator and is never a persistent semantic ID.

## Required observations before implementation

- trace the MAN placement spawner's writes into a created NPC node;
- identify whether it retains a MAN record/source pointer or record index;
- trace the MAN NPC model selector into its runtime model/object table;
- observe initialization order and suppression across at least two town01 entries;
- observe list/census behavior across an inter-scene transition and a same-scene door reposition;
- prove whether a node address is reused inside one epoch;
- establish the animation-bank pointer-to-record mapping if animation is used.

Until those observations are complete, actor correlation remains premature.
