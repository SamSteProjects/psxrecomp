# Field script branch authoring

The script workspace supports source-qualified edits to existing branch
destination words. It shows separate Retail, Authored, Current and reviewed
Proposed flow, links graph selection to source disassembly, and preserves
unknown conditions and opaque regions. Decoded reachability does not establish
story activation, execution, termination or gameplay acceptance.

Open an imported actor's **Inspect script and dialogue** action, or the source
workspace of a partition2 script. Under **Source flow and branch destinations**,
select a source branch and a qualified decoded destination. **Review destination**
shows the actual changed byte offsets and newly reached/unvisited source nodes.
**Apply reviewed destination** creates an ordinary project command; Undo/Redo and
Save/Open retain it. **Review reset to Retail** removes the authored destination
only after the same review/Apply process. No-op reviews cannot create commands.
Multiple pending branch choices survive an ordinary workspace refresh, and block
project history/Save until applied or explicitly discarded.

## Whole-record diagnostics

The [source-flow overview](legaia-script-flow-overview.md) summarizes Retail,
Current and reviewed Proposed entry reachability and cycles. It preserves
qualified unvisited source anchors without treating them as executed paths.
Links open the disassembly at the exact source boundary; Discard withdraws the
Proposed overview. Conditions and external resumption remain unresolved.

## Source and wire contract

`BranchAuthoringContext` reuses the verified, uniquely owned MAN P1/P2 record
snapshot. P0/controller records, aliases, section overlap, unknown/conflicting
paths, instruction interiors, message interiors, opaque tails and record-end
sentinels are excluded. A partial report caused only by an unvisited tail can
qualify. Destinations are original reached instruction or atomic MES starts
between the source entry and PC32767. No instructions or allocations are added.

Stable entries use `script://<owner>/branch/<pc04hex>` and exactly
`{"target_pc": integer}` inside the owner's `ScriptBranches.entries` component.
MENU80 child payloads remain inside the allocator instruction, not selectable
parent instruction or MES starts. Embedded STATE_RESUME0 arguments and payload
also stay inside one instruction and offer no destination words.
MENU82/84/89 fixed writes have no target words.

Opcode, target context, encoded test, flag bit/bank, bounds, selectors, ticks,
record lengths and MAN pointers remain source-owned. For `p = pc + header_length`:

| Branch family | Destination word / relative base | Writable header |
| --- | --- | --- |
| JMP_REL0x26 | p | Ordinary or extended |
| SYSFLAG_TEST0x70..7F | p+1 | Ordinary |
| COND_JMP0x42, modes0/1 | p+2 | Ordinary or extended |
| BBOX_TEST0x4D | p+4 | Ordinary or extended |
| FLAG_WORD_BRANCH0x4C/A0..A2 | p+2 | Ordinary or extended |
| FIELD_68_BRANCH0x4C/8C | p+1 | Ordinary or extended |
| ACTOR_SEARCH_BRANCH0x4C/8D | p+3 | Ordinary or extended |
| VALUE_COMPARE_BRANCH0x4E, source0..B/compare0..1 | p+4 | Ordinary or extended |

All targets are `(word_base + delta) & 65535`; the emitted word is
`(target_pc - word_base) & 65535`. Retail callers sign-extend the returned PC
before storing it and adding it to the script base, which establishes the signed
authoring limit. Conditions remain encoded labels and are never evaluated.
LFLAG/GFLAG/CFLAG TEST instructions are wait gates without destination words.
FIELD_68_BRANCH labels zero/nonzero field0x68 paths. ACTOR_SEARCH_BRANCH preserves
its character selector and marker; empty or unmatched searches fall through.
Neither family observes runtime values or establishes actor identity.
VALUE_COMPARE_BRANCH retains its selector, source/comparison mode and signed
threshold, including the bank high word after the branch destination.
Default sourcesC..F and comparison modes2..F have no editable branch edge.
Encoded field/slot/bank sources do not establish runtime values or asset identity.

Existing dialogue and operand writers first qualify their independent retail
spans. Branch words compose last over those authored values, with exact source
preimages at the target words. Every original instruction/message anchor is
redecoded even if the new flow no longer visits it. Candidate flow must have no
stops, changed instruction widths, new boundaries or opaque destinations. Changed
reachability is reported; existing authored operands remain retained.

Review keys bind the owner, source and current/candidate hashes, complete authored
state, active scene, project root, Edit mode and disc stamp. Apply independently
recomputes the review. Geometry preview freshness is not used as script freshness.
Normal Build preserves layouts, checks compressed capacity or raw carrier length,
and rescans branch owners after independent serialization readback. Streaming and
experimental appended-record composition rebind original owners by partition/index;
appended data stays outside branch writes. Operand files/bundles use the same
reviewed command and atomic composition. The Build audit links back to the source PC.

## Retail evidence and decoder corrections

The read-only Andrew reference remains pinned at
`d6e64c68ede25813d35db20980da82a1a025549b`. The SDK adapter follows executing
retail evidence where that reference's interpretations disagree. Independent
proofs read unchanged PROT897 and the SCUS executable, verify handler/consumer
instruction windows against fixed hashes, and test their arithmetic separately
from the authoring service.

| Evidence | SHA256 |
| --- | --- |
| PROT897 executing field handlers | `216f846db5ab085a295cef4064747380a06c995caa3e1b2773e78a1d349f126b` |
| SCUS executable / signed-PC consumers | `292256e2e66db42727f613406785e444254d3f699569e611f65fcf1c6d2f3482` |
| Town01 decoded MAN | `85a1ed2fdf79e7bf2e2daa4bf100740a1e18c9f92bc9f82fa4b72c296a3af5b3` |
| Dolk2 raw MAN | `a623b1a0534d2e70ca6186037af19693df26cdc7874cd071a9cd2a54319c46b2` |

Retail camera45/C0 reads a signed parameter and invokes camera processing at
801DF210..288, then continues at ordinary PC+4 or extended PC+5. It is not an
absolute jump. FIELD4C/43 and44 write/ramp context fields at801E1234/126C and
preserve their continuation. FLAG_WORD_BRANCH uses the signed relative word
base through801E360C/3614. Ordinary SYSFLAG covers50..7F; extended forms read
raw dispatcher operands differently and stop explicitly until those semantics
are independently qualified. These fixes remove false branches and false
overlap diagnostics without scanning opaque bytes for convenient opcodes.

Current catalog totals are Town01:91 scripts,619 dialogue segments,60 partial
scripts and1339 flag references; Dolk2:89 scripts,629 segments,28 partial and744
references. Historical totals in older status sections reflect previous decoding.

Private integration evidence is under
`local-output/sdk-20260909/script-branches-20261002/`. Town01 actor0002 PC31
target15-to11 changes byte4791 and fits the existing LZS capacity; a composed
dialogue/flag/branch normal package independently reads back exactly. Dolk2
actor0002 PC28 target63-to9 changes bytes7481/7482 in its44036-byte raw MAN.
Other bytes, import metadata, record ownership and layouts remain unchanged.
The final integrated run passed88 Python cases with no skips, including three
HTTP cases that reject18 invalid requests without mutation; four Node suites
also passed. Fifteen browser workflows cover reviewed mutation, stale/no-op
rejection, graph/source navigation, ordinary history/persistence, reset, multiple
pending choices across Apply/reopen, close and narrow layout. The final browser
Build and its audit-to-source navigation pass. Independent package readback
finds exactly byte4791 changed in45338 decoded bytes, retains the entire MAN
layout, and confirms saved imports equal a fresh source import. The private
browser evidence retains earlier harness selector failures and their corrected
package continuation separately.

A real Town01 donor append produces45379 prepared MAN bytes and rebinds the
branch word from source offset4791 to4794; Dolk2 streaming preparation preserves
its44036 bytes and exact branch spans. These are prepared inputs, not full rebuilt
disc or gameplay acceptance. No game was launched. Story behavior and the wider
unfinished SDK remain deferred.
