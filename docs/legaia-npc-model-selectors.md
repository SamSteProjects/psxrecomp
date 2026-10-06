# NPC-owned script model selectors

## NPC-owned script model selector foundation - 2026-10-05

Appended NPC scripts now have independent native SET_ACTOR_MODEL selector-word
serialization using the existing source-qualified MENU_CTRL 0x50 adapter. The
shared final-allocation guard binds each unique clone to its immutable donor.
Signed16 values preserve encoded meaning, opcode, sub-op, extended context and
all other bytes. No-op requests still verify full instruction/word preimages.
This changes script operands; runtime model-pool resolution and mesh restaging
are not inferred, and the viewport does not simulate this instruction.

Validation: 10 focused native/model-selector/wait Python checks pass. Ordinary and
extended forms, signed boundaries, two independent clones, final offsets, retained
wait operands, no-op preimages, invalid types/owners and forged allocations reject
or retain bytes as required. A fresh retail Town01 actor0003 two-clone proof sets
PC12 to selectors240/-1, preserving the retail donor, complete MAN layout, every
unrelated byte, project document, Undo/Redo history and all project file hashes.
Evidence: `local-output/sdk-20260909/npc-model-selectors-native-20261005/proof.json`.

Project commands, editor review, normal Build, portable presets and saved authored
comparison are still pending for NPC-owned model selectors. The existing imported
actor workflow is unchanged. No game launch or full-disc export occurred; runtime
model identity, pairing, restaging and story execution remain unverified. The full
SDK goal remains active and manual gameplay verification remains deferred.
