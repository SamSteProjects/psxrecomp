# NPC-owned flag-bit authoring

Select an authored NPC in the scene hierarchy and choose **Edit NPC script
flags...** in the Inspector. Asset Details exposes the same action. Supported
source donor instructions appear with their Retail bit index, dispatch context
and preserved upper bits. Check a target to enable an independent NPC override,
enter its bit index, then Review and Apply. Unchecking a target and applying
restores its Retail operand. Input changes withdraw the proposal.

Apply makes one Undo step. Undo/Redo and Save/Open retain the complete NPC draft.
Normal Build writes these operands to the final appended NPC record for both
compressed and streaming scene carriers. Imported donor operands remain separate.
Repetition qualifies and retains the flag entries. NPC preset capture freezes
qualified flags with the five other supported families. Flag-bearing files use
metadata-only v7; export/import and reviewed new-instance placement requalify the
source donor operands. Earlier preset versions retain their schemas and limits.

The supported field is a **bit index**, not a true/false flag value. LFLAG
SET/CLEAR/TEST support indices 0..15. Qualified GFLAG and CFLAG operations support
0..31, except CFLAG_SET index8 and CFLAG_CLEAR index10, whose special side effects
are excluded. Unsupported or stopped script paths cannot be edited. Source hashes,
owner-qualified PCs, donor identity, instruction preimages and final allocation
extents are checked. The serializer holds upper three operand bits, extended
context, layout and every unrelated byte.

Runtime variable identity and story meaning remain unknown. This workflow does
not establish actor flag isolation, branch execution, scheduling, visible behavior
or gameplay acceptance. Saved-script comparison labels exact flag-bit changes as source-qualified authored
spans, alongside appearance, text, waits, movement and facing. Other differences
remain unexplained; this is byte accounting, not execution equivalence.

## Evidence

Twenty-two focused Python checks pass with the private retail fixture enabled;
two Node suites pass. The actual browser workflow covers Review/Apply/Clear,
changed-input withdrawal, Undo/Redo and Save/reload. The 540px dialog was visually
inspected. A private Town01 normal Build independently reopens with bit0 and
preserved upper bits, changing exactly one byte against the previously verified
record while retaining appearance, text, waits, movement and facing. Evidence:
`local-output/sdk-20260909/npc-flags-editor-20261005/proof.json`.

A private streaming Rayman normal Build independently reopens two NPCs with bit
indices 3 and 4, exactly one changed byte each and all five previous own script
families retained. Evidence:
`local-output/sdk-20260909/npc-flags-streaming-20261005/proof.json`.

Native two-clone byte preservation is recorded separately in
`local-output/sdk-20260909/npc-flags-native-20261005/proof.json`.
No game launch or full-disc export was used.

Saved comparison evidence:
`local-output/sdk-20260909/npc-flags-script-comparison-20261005/proof.json`.
Thirteen focused Python checks and the Node comparison suite pass. Read-only
browser comparison explains 28 of31 changed Town01 bytes across all six families,
leaving three unexplained; both streaming NPC flag spans also qualify. The 540px
table was visually inspected. Both projects retain documents, history and all
file hashes.

## Portable preset verification

Eighteen focused Python checks and two Node suites pass. Actual browser capture,
v7 download/upload, reviewed independent library import, Undo/Redo, Save/reload
and reviewed new-instance scene placement pass. The 540px import review was
visually inspected. Private recipient normal Build `248da4af5e7947dd` independently
reopens bit0, sector0, wait11, own text, model105/animation13 and own movement
X3200/Z5696/move10. Source NPC, imports and existing entities stay held. Evidence:
`local-output/sdk-20260909/npc-flags-presets-20261005/proof.json`.
