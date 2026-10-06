# NPC-owned branch destination foundation

The native serializer supports independent branch destination words for appended
NPC records. It uses the existing source-qualified branch authoring adapter; it
creates no new instruction families or speculative script semantics. Only
original reached instruction or atomic message starts can become destinations.
Unknown/conflicting paths, opaque/interior boundaries, changed conditions,
selectors, contexts and foreign/aliased allocations reject.

The adapter resolves final record extents after appending all clones. It rebinds a
clone to its immutable donor slot in a private in-memory MAN snapshot for native
qualification, then copies only audited destination words into that clone.
Imported records are untouched. Complete entries qualify together against both
the original source graph and the proposed graph. Source spans are retained even
when changed edges make their instructions unreachable.

Branch serialization should run after the other NPC-owned script families so
those qualified operands remain present even if the final graph skips them.
Runtime branch activation, story reachability and termination are not asserted.

Project review/history, Inspector controls, normal Build, portable presets and
saved-script authored explanations remain to be connected. This document does
not describe an available editor command yet.

Thirteen focused Python checks pass with private retail input enabled. A fresh
Town01 two-clone proof changes SYSFLAG_TEST PC14 to source boundaries11/12 and
preserves appearance, waits, movement, flags, donor, layout, unrelated bytes,
project/history and all file hashes. Evidence:
`local-output/sdk-20260909/npc-branches-native-20261005/proof.json`.
No game launch or full-disc export was used.
