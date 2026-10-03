# Script source-flow overview

MENUE3 actor-state-copy coverage (2026-10-03) exposes a fixed encoded
continuation and the native resolved-actor-to-dispatch-context direction.
A missing lookup skips the field copy; context post-updates still run.
Selector/context numbers remain encoded facts, not imported actor identities
or observed positions. Sixteen Dolk2 P2 record0011 sites are now visible;
the next unresolved choice27 boundary still stops inspection. No editable
target word or runtime transform operation is introduced.

Embedded STATE_RESUME0 (2026-10-03) now owns its full declared argument block
and terminated native payload as one instruction. These bytes are not parent
instruction/dialogue starts or target destinations. Its outgoing edge retains
`external_state_completed`; decoding the extent does not prove menu activation,
completion, story reachability or payload meaning. Nonadvancing forms still stop.

Scene-register writes (opcode4F) and field callback MENUEA (2026-10-03) expose
verified fixed continuations without editable target words. Callback effects and
runtime scene/register meaning remain unknown. A continuation after a native call
does not establish which story path executes or when its effects become visible.

MENU80 allocator coverage (2026-10-03) treats the full native child payload list
as one owned instruction span. Child payload PCs are operand locations, not parent
instruction/dialogue boundaries or editable destinations. The acquisition success
edge reaches the end of that list; pending acquisition retains the original PC.
Its self-edge does not prove an infinite loop or runtime allocation success.
Native MENU82/84/89 writes expose fixed continuations with effects unobserved.

Fixed STATE_RESUME edges (2026-10-03) are conditional completion continuations.
The `external_state_completed` label does not establish that a menu has opened,
finished or resumed in the game. Fixed menu payload bytes remain opaque operands;
embedded-message/nonadvancing forms still stop decoding. Encoded path queries and
overviews retain this condition without evaluating the external state machine.

Open an actor's **Inspect script and dialogue** workspace or a partition-2
script's disassembly, then expand **Whole-record source flow overview**.
The branch workspace offers the same overview for the selected **Script flow
layer**, plus a separate **Reviewed Proposed encoded flow** after Review.
No command is submitted by opening an overview or following its links.

The overview shows the verified source entry, decoded instruction/message
boundaries and encoded edges. **Cyclic components** groups mutually reachable
boundaries, including self-loops, and counts their outgoing encoded edges.
A closed component means no encoded edge leaves that component; it does not
prove an infinite loop. Conditions, external resumption and story state are
not evaluated. **Unvisited decoded boundaries** lists known source anchors
outside the encoded entry path. It does not establish gameplay unreachability.

**Undecoded targets** retains source references, encoded condition labels and
decoder-stop reasons. Unknown bytes are never scanned for convenient nodes.
**No decoded successors** describes the graph only, without assigning a VM
termination meaning. **Decoder stops** also lists stops without incoming edges.
Missing or undecoded entry offsets leave reachability explicitly unknown.

Use **Inspect** to select the exact source row. The editor opens a collapsed
disassembly before scrolling and focusing it. A branch proposal's unvisited
anchor can be inspected in Retail disassembly; the existing flow layer explains
its source fallback. Lists show 32 items per page using **Previous flow page**
and **Next flow page**. Selection preserves open overview details and paging
when the report remains unchanged. Discard withdraws Proposed flow.

## Qualified data and bounds

`inspect_record` exposes its exact supplied `entry_pc`. Branch candidate
qualification independently redecodes original instruction/message anchors,
returning `unvisited_instructions` and `unvisited_dialogues` alongside the
existing reached-path arrays and `unreachable_source_pcs`. This preserves source
ownership while allowing whole-record graph diagnostics. It does not broaden
branch authoring destinations or recover opaque bytes.

The analyzer accepts at most 8192 distinct bounded nodes and 64 successors per
instruction. Messages contribute one atomic encoded continuation. It rejects
duplicate owners, invalid PCs/conditions and conflicting unvisited metadata.
Iterative strongly connected component traversal avoids recursion overflow.
It returns detached graph metadata, writes no project state and executes no VM.

## Offline evidence — 2026-10-03

47 focused Python cases pass with private Retail source and no skips, including
branch history, Build/readback and HTTP regression coverage. Two Node suites
pass graph, lifecycle, review and authoring guards, including an 8192-node cycle.
Eight browser checks cover native source navigation, retained Proposed anchors,
discard, 540px layout, file/history preservation, unknown exits and pagination.
An independent transitive-reachability implementation confirms Retail/Current
Town01 actor0002 (five boundaries, one cycle), and actor0011 Proposed (49
boundaries, two cycles, unvisited PCs 55/57/63). Browser inspection submitted no
authoring command, Build, Save or Run. Screenshots and private reports are under
`local-output/sdk-20260909/script-flow-overview-20261003/parent/`; helpers closed.

No immediate gameplay verification is required for this inspection feature.
General control-flow authoring, runtime execution and authored story behavior
remain unfinished or separately deferred.

Asset dependencies now provide [reference-instruction navigation](legaia-asset-references.md#inspect-the-reference-instruction)
into this disassembly and its overview, including P1/P2 sources in Project scope.
