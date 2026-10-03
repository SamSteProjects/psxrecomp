# Facing edits composed with appended NPC drafts

Source script facing edits can be retained when preparing an experimental NPC draft archive. This operates on the existing, reached `CAM_CFG` and nonparked `NPC_RUN` operands described in [source script facing](legaia-script-facing.md). It does not introduce a general actor heading or prove which story branch will execute.

Author a supported facing sector on an existing source script owner, create the NPC draft from an imported donor, and use the editor's read-only draft serialization review. Save and reopen the project to retain both edits. Preparation resolves each original MAN record after the appended record table changes, then applies the facing nibble to that original owner. The donor's appended clone retains its source script operand; changing the original owner is not a request to change every clone or a runtime actor targeted by extended dispatch.

The review prepares a logical PROT archive in memory and returns provenance and change metadata. It does not write an ISO/BIN, start the game, apply live memory changes, or add a project history entry. Experimental output can be requested separately later. Normal Build continues to reject NPC drafts because allocation and opaque script references remain unverified; a successful serialization review does not make the draft playable.

## Composition and exact ownership

MAN partition counts and three-byte relative record pointers define the post-append record layout. Source facing ownership is retained as the original partition, record index, and record-relative instruction byte. The serializer re-resolves the original record after append rather than writing to the previous absolute MAN byte offset. It verifies source record membership, the unchanged instruction location and mechanism, and the current operand before writing. Only the low nibble changes. The upper nibble retains flags, including `NPC_RUN`'s flag bit and `CAM_CFG`'s source upper bits. Other authored components remain composed into their own fields.

Partition-1 actors and qualified partition-2 scripts are supported. Extended instruction context remains part of the audit and is preserved; it can select another runtime actor. Sector values 0 through 7 index the verified retail direction table. Parked targets, halt-acquire forms, unknown or conflicting paths, unsupported sector values, ambiguous ownership, and source changes reject preparation.

## Private retail evidence

Independent record-table walking qualified both source carrier families using the user-owned North American disc. No game was launched and no disc output was written. Proof artifacts are retained privately under `local-output/sdk-20260909/draft-facing-20261002/research/`.

For the LZS Town0b scene, one appended donor plus an authored Transform moves the selected original record offsets by three bytes. Four source facing edits then change exactly four bytes relative to the same append-and-Transform baseline:

| Source owner | Instruction | Source PC | Operand before → after | Extended context |
|---|---|---:|---|---:|
| P1 actor 0019 | CAM_CFG | 17 | `0x81 → 0x82` | none |
| P1 actor 0006 | NPC_RUN | 34 | `0x00 → 0x01` | none |
| P1 actor 0036 | NPC_RUN | 150 | `0x02 → 0x03` | 74 |
| P2 script 0008 | NPC_RUN | 207 | `0x00 → 0x01` | 49 |

For raw streaming Dolk2, P1 actor 0002's `CAM_CFG` at source PC 42 changes `0x87 → 0x80`. Its original record also moves by three bytes. The upper flag nibble remains `0x80`.

Both logical archive preparations preserve all other composed MAN bytes and leave appended donor clone records identical to the corresponding preparation without facing edits. Project state and imported metadata remain unchanged during preparation. The saved fixture includes both scenes, one draft per scene, the source facing edits, and authored placement changes. Source files and retail MAN payloads are retained unchanged. Runtime allocation, current script execution, clone behavior in gameplay, and visible facing still require deferred manual verification.
