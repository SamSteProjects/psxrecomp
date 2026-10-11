# World Source Object Bind Inspector

The read-only SDK resolver and
`POST /api/worldmap-object-bind` now connect a qualified Current placed-object
identity to the retail kind-1 trigger at its footprint anchor and the kingdom
MAN slot. The request contains exactly `scene`, `source_key`, and `entity_id`.
The registered Source Object Bind Inspector action appears only on Current resolved placed objects. The browser independently qualifies Current footprint bytes, trigger rows, flat MAN layout, record ownership and header bytes before displaying fields. Selection, layer, source and pending-request guards suppress stale results.

The native flat MAN index is resolved before partition interpretation. Only a
bounded partition-0 header exposes its encoded animation selector. Another
partition remains unsupported; absence of an anchor trigger is `no_source_bind`.
Neither case invents a script, animation asset, or active runtime object.
Primary rows precede fallback rows. An invalid primary hit refuses inspection
rather than being replaced by a valid-looking fallback. Aliased record starts,
section overlap, header overrun, and byte/record budgets are checked.

Results retain Current placement/footprint provenance, source trigger identity,
shadowed trigger IDs, carrier and slot hashes, flat/local MAN indices, record
span/hash, and a bounded header byte witness. The representation is explicitly
`retail-bind-at-current-anchor`: authored World MAN binds are not supported.
No project command, history entry, game launch, or runtime observation occurs.

## Evidence — 2026-10-10

Three focused Python tests pass primary precedence, fallback resolution,
non-P0 refusal of header interpretation, missing binds, immutable inputs,
malformed index, alias, overlap, header overrun, and anchor bounds.
Retail checks cover all 64 placed source objects: Map01 resolves 6/6; Map02
33/33; Map03 resolves 20/25 and reports five absent source binds. Each resolved
selector agrees with a direct byte lookup. Private evidence is retained in
`local-output/sdk-20260909/worldmap-object-bind-20261010/proof.json`.
The shared schema suite also passes (23 Python tests total). Independent Node checks qualify all 64 results and refuse 40 altered headers, identities and scope claims. Three actual kingdom HTTP/browser workflows pass source selection, qualified Inspector fields, selection clearing, zero authoring commands and zero page errors. A second three-kingdom browser run confirms the Map03 absent-bind Inspector state with the final qualifier guards. Wide and 400-pixel captures were inspected without overflow; private document/history and Save/Open baselines remain unchanged. No Build or runtime validation was performed.

Pinned reference `d6e64c68ede25813d35db20980da82a1a025549b`,
`crates/engine-core/src/field_env.rs::object_binds` and `partition0_anim_id`,
supplies anchor lookup and P0 header evidence. The SDK's existing native
`FUN_8003C8F0(id,0)` interpretation in `importer/field_map.py` establishes flat
index space; the reference's direct P0 indexing is not generalized blindly.
The reference skips malformed records before considering fallback; this SDK
instead reports the malformed primary source. Runtime activation, interaction
script entry, resolved clip identity, and gameplay behavior remain unverified.
