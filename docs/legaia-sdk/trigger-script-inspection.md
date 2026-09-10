# Trigger script inspection

The field trigger inspector can follow verified kind-1, gate-1 references to
their MAN partition-2 records. Open a trigger in the Asset database and choose
**Inspect referenced script**. The separate read-only view shows supported
instruction paths, decoded dialogue, opaque ranges and decoder stops. Back
returns to the source trigger. Object bindings and local teleports do not offer
this action.

`POST /api/trigger-script` accepts only a structural `asset_id`. The resource
service freshly verifies the active imported scene, resolves the trigger from
its source catalog, and checks source identity again before returning. Client
partition numbers, record indexes and byte spans are rejected. Reports remain
private transient responses; they do not modify imports, authored data or builds.

The importer bounds the compressed MAN descriptor against adjacent descriptors,
rejects aliases, checks all three partition tables and six section spans, and
bounds the target record against every record and section start. Its variable
header is checked before passing its entry offset to the existing bounded
script inspector. The prefix word count and three gate-array counts describe
structure only; they are not interpreted as names or evaluated story conditions.

The reference remains Andrew revision
`d6e64c68ede25813d35db20980da82a1a025549b`. P2 header/entry evidence is
`crates/asset/src/man_edit.rs::p2_pc0`, blob
`7e35fc570fb448072005a8a7588d9e34ebbb3da0`. Gate-1 dispatch evidence is
`crates/engine-core/src/field_regions.rs`, blob
`8f54e88895ecdf0ca3fe1fc5602ce583911c5feb`.

Retail town01 has 51 eligible triggers referencing 22 distinct P2 records.
The bounded sweep returned 16 reports with supported paths decoded and 35
partial reports. These are counts per trigger, including shared references.
The first fallback trigger resolves P2 record 38 at decoded MAN offset 44621,
24 bytes long, with entry offset 20 and NOP/JMP_REL instructions.

No opcode support was added. Unknown instructions terminate paths, and opaque
bytes are never searched for plausible opcodes or strings. Inspection does not
prove activation, reachability, a named scene edge or gameplay execution.
Script editing and dispatch-gate evaluation remain unsupported.
