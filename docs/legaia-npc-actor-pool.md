# Retail actor-pool lower-bound check

Normal **Review Build** and **Build** now qualify the retail SCUS executable before assessing an appended NPC candidate's initial placement demand. The known executable initializes143 actor slots, each216 (`0xD8`) bytes. Scene setup allocates one anchor, then its initial-placement branch invokes the actor initializer for partition-1 records1 throughN1−1. That branch therefore requires at least `max(1, N1)` slots, before other scenery, channels and script-created objects.

Candidates above that lower bound are rejected before MAN encoding. The blocker identifies the requested minimum and143-slot capacity; the reviewed Build action stays disabled, and authored NPC drafts remain available. Passing this check does **not** prove a safe additional-NPC budget. Zero remaining lower-bound slots is not evidence that an entire scene will initialize successfully. Packages remain disabled by default and mark allocation/scheduling/gameplay unverified. Experimental growth export retains its separate source-candidate gates; this change adds the check to the ordinary package workflow.

Successful normal packages retain `draft_audit.actor_pool_evidence` with executable/function witnesses, candidate partition counts, minimum initial placement slots and explicit unknown other demand. The service reads the verified disc through the existing importer. Neither the browser nor the client supplies pool size or executable instructions. Existing compressed stream, descriptor, composition and opaque-byte checks remain intact. Repeat-draft metadata now correctly describes supported normal source candidates instead of claiming every NPC draft is rejected.

## Static source evidence

Complete SCUS SHA256: `292256e2e66db42727f613406785e444254d3f699569e611f65fcf1c6d2f3482`.
Disc SHA256: `e6120a5d70716dd2f026a2da32d0171d52651971b52c4347a68541299f75258c`.
The pinned reference stays `d6e64c68ede25813d35db20980da82a1a025549b`;
`crates/engine-core/src/field_channels.rs::spawn_channels` identifies the same scene-entry rule. Retail bytes independently establish the instruction paths below. Existing sibling generated annotations match each inspected instruction; they are comparison evidence, not the authority for constants or a claim of native execution.

| Retail path | Independently qualified conclusion |
| --- | --- |
| `0x800203EC`,56 bytes | Initializes the free stack with highest index142, node stride−216 and143 pointers spanning `0x8007C5AC..0x80083D7C`. |
| `0x80020454`,72 bytes, plus `0x8002049C`,8 bytes | Pops one free slot, decrements the index, and returns zero when exhausted. |
| `0x80020DE0`,424 bytes; `0x80024C88`,116 bytes | Propagate allocation failure as zero. |
| `0x8003A1E4`,888 bytes | Selects the partition-1 record, initializes source placement/context/entry PC and dereferences the allocation result without a null guard. Context ID is partition0 count plus record index. |
| `0x8003AEB0`,3416 bytes | Reads signed counts at MAN offsets `0x22/0x24/0x26`; allocates an anchor, then loops record indices1..N1−1 in the initial-placement branch. |

Production qualification checks the complete executable hash, bounded load image and all seven complete function hashes before deriving pool constants. Unknown executables reject this NPC normal-Build path rather than receiving assumed capacity. No runtime pool expansion, renderer fix or actor scheduling repair is inferred or installed.

## Offline verification, 2026-10-03

Private source qualification and bounded execution proof:
`local-output/sdk-20260909/npc-runtime-source-20261003/research/`.
The instruction harness runs the actual qualified initializer/pop/failure words in isolated memory with branch-delay semantics. It obtains143 distinct nodes at216-byte stride; allocation144 returns zero without changing memory. It does not run the game or reproduce full scene state.

Six focused Python checks pass with private source supplied and no skips: full executable qualification, changed-source rejection, lower-bound/domain boundaries, pre-encoding failure without mutation, carrier ownership/capacity guards and existing Town01 normal package readback. The existing Node NPC review guards pass. Six actual browser checks include ready review,540px layout, reviewed Build, unchanged authoring, packaged source evidence and the real91-draft blocker. No page errors or game requests occur; the blocker screenshot is inspected.

The one-draft Town01 candidate changes counts `[36,53,39]` to `[36,54,39]`. Its54-node placement lower bound leaves89 slots **before unknown consumers**. Independent full carrier readback retains the same candidate MAN hash `b44c838cc489e5eb4f900b59227bc618eceeaeb285ff4f735c9fdc3bd52a08c9`, uses24856 compressed bytes within24894, and preserves all non-owned carrier bytes, descriptor pointers and TOC. New audit metadata changes the package identity:
`e8907db2b03619303d72cf3e09fbe2ac82bff7815534733d15c9337a00443c06`.

Private ready and blocked fixtures/scripts are under
`local-output/sdk-20260909/npc-runtime-source-20261003/parent/`.
The owned browser and loopback server are closed. No game, install or full-disc export ran. Native spawn completion, scenery/script demand, visibility, collision, dialogue and lifecycle behavior remain deferred.
