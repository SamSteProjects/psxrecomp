# Trigger script inspection

The current source workspace also lists triggers in the scene hierarchy and
links qualified gate-1 rows to exact P2 records in the central Active/Project
reference graph. Viewport source-cell frame/pick is available, with separate
X/Z quantization and unknown Y. See
[field source workspace](../legaia-field-source-workspace.md).

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

The initial navigation implementation added no opcode support. Unknown instructions terminate paths, and opaque
bytes are never searched for plausible opcodes or strings. Inspection does not
prove activation, reachability, a named scene edge or gameplay execution.
Script editing and dispatch-gate evaluation remain unsupported.

## Opening conversation and bounded decoder extension

The 2026-09-10 investigation resolved fallback kind-1 trigger 0045 to P2
record 3, decoded MAN offset 28616, length 2407, entry PC 12. The pinned
`docs/formats/scene-v12-table.md` identifies this opening trigger; its blob is
`1d76050aa7cce1b4a6b849e62e3e91491d5726f2`. A private text locator places
the opening Elder line inside this record, but that locator is not decoded
dialogue evidence and is not offered as an authorable span. Existing dialogue
authoring remains restricted to validated P1 runs.

The inspector now recognizes two additional MENU_CTRL forms: ED has one
unsigned state byte and E8 has four signed little-endian 16-bit camera
operands. Their ordinary lengths are 3 and 10 bytes; the extended-context
header adds one byte. Both continuations come from the pinned executing
`crates/engine-vm/src/field/step/menu_ctrl/nibble_e.rs::op_4c_ne`, blob
`61ad972bd5455bdb84b1ab376f6ad959cb23190b`. Other sub-ops remain unsupported.

A fresh sweep of all 51 town01 references changed only trigger 0045: its
inspection now exposes five instructions and stops at PC 31 on unsupported
opcode 0x34, instead of stopping at PC 12 on ED. It still exposes no dialogue.
The aggregate remains 16 supported-path reports and 35 partial reports.
Private before/after metadata is retained in
`local-output/sdk-20260909/dialogue-trigger-{baseline,extension}.json`.

All 31 focused inspection, catalog, dialogue authoring, persistence and build
tests passed with the private retail input. New synthetic cases check every
truncated instruction prefix, extended-context lengths, signed extremes,
operand bytes resembling dialogue leads, and continued unknown-op stops.
No runtime execution or dialogue-display acceptance is inferred from these
source checks.
