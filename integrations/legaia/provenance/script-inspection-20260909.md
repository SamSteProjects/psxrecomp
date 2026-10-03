# Read-only actor script and dialogue inspection

Retail value-comparison and MENU49 evidence (2026-10-03): unchanged hashed
PROT897/SCUS sources, recorded below. Opcode4E table801CED74→801E0A04 dispatches
source0..B through801CEE30; C..F retain initialized zero state/threshold.
Compare0/1 use signed SLT at801E0BB0/0BA4; other modes leave the branch false.
Short thresholds call signed helper8003CE9C (SLL16/SRA16 at8003CEAC/CEB4).
Bank A/B pack the low threshold word at operand+2 and high at+6; their false
path advances9 rather than7. Taken paths read unsigned target word+4/+5 and
return adjusted PC+5+word through801E35FC/3604, wrapping at the existing16-bit
PC consumers. Scaling sources0/1 multiply the runtime factor by signed16 input,
retain low32 bits and divide toward zero by256. No runtime comparison executes.
The pinned source's unsigned16 short thresholds are superseded by these words.

MENU49 outer4 table801CEE70→801E1138 advances6; inner table801CEF1C→801E1480.
Story-word masks01000000/02000000 choose field4A/global-delta write/ramp paths.
All zero-tick writes return through801E3624. Nonzero ramp exits801E175C/205C
call8003C5F0 and return advanced s8 through801E1768/2068, not the original PC.
The pinned sub9 yield description is superseded; native signed value/tick words
are preserved. World-map/actor/story state and field-ramp appearance remain
runtime-unverified. Independent package readback changes only one target word
in map01 P2 record0009; no source pin, game process or disc installation changes.

Fixed STATE_RESUME completion evidence (2026-10-03): unchanged hashed PROT897
(as recorded below), dispatch table801CED60→801E08C4, reads external slot8007B450.
Completed sentinel1 routes sub1/3/7 to801E00B8 (adjusted PC+3), sub2/4 to801E212C
(delay slot801E2130 adds7), sub5 through801E0948 (+14), sub6/8/9/C to801DF898
(+5), and D through801E0978 (+5). Extended dispatch contributes its earlier+1.
Other state values may arm or wait; these static edges are labeled
`external_state_completed`, never evaluated. A/B return without advancing in
Done; out-of-range Idle forms do not arm. Sub0's embedded message walker still
requires separate ownership/length evidence and remains a decoder stop.
Fixed payload bytes are retained as opaque operands, with no new authoring gate.
Dolk2 actor0049 record SHA256
`b7e592fb94b104493a77bd2dc979db548c5a753d7fe48fe8e80bcf2139e17356`
has three ordinary4909 sites at PCs959/1232/1611, independently verified from
fresh source carrier bytes. Runtime activation/resume values remain unobserved.

Retail correction (2026-10-03): MENU_CTRL8C/8D now decode from executing
PROT entry897 SHA256 `216f846db5ab085a295cef4064747380a06c995caa3e1b2773e78a1d349f126b`.
At base0x801CE818, outer table801CEE80 selects801E1EA0; subtable801CEF78/7C
selects801E23EC/2404. 8C tests signed field0x68, advances4 and uses the signed
word at operand+1 for its zero path. 8D advances6, reads selector+1/marker+2,
and matches into801E3608 (word operand+3). Empty searches branch801E3624;
unmatched searches return the already advanced PC through801E3628.
Shared exit801E360C/3614/361C reads the signed word, subtracts2, then adds the
advanced PC: both targets are relative and wrap16. Extended dispatch adds1 to
operand and PC before this handler. The unchanged pinned nibble_8.rs describes
absolute targets and a no-match halt; those descriptions are superseded here.
Hash-bound regression checks and private native-word evidence independently
qualify this correction. Runtime search-table ownership and values remain unknown.
Target-only authoring uses the existing fail-closed review/Apply/build gates.

Central transition assets (2026-10-02) adapt existing catalog/graph evidence;
no decoder, opcode handler or retail source pin changed. Each asset retains
source record SHA, source PC/stop count and layered entry bytes. Existing static
retail arrival interpretation remains runtime-unverified and does not identify
a source trigger. Fresh caller qualification uses the existing transition
serializer, including partial catalogs with no actual stops. See
[`docs/legaia-transition-assets.md`](../../../docs/legaia-transition-assets.md).

`importer/script_inspection.py` independently inspects a selected actor's bounded
MAN record. It never runs the field VM, writes guest state or offers a serializer.
The unchanged Andrew source pin is
`d6e64c68ede25813d35db20980da82a1a025549b`.

Reference evidence:

- `crates/asset/src/man_section.rs`: partition-1 actor records contain a local
  count, two-byte local entries, four-byte placement header and script body.
  The first script byte is at `1 + 2 * local_count + 4` relative to the record.
- `crates/engine-core/src/man_field_scripts/records.rs` and `placements.rs`:
  record bounds come from MAN record/section offsets. Dialogue prologues are
  normal field-VM bytecode; naive linear disassembly desynchronizes inside text.
- `crates/engine-core/src/dialog.rs`: inline field dialogue consists of
  `0x1F`-led MES segments inside MAN actor records, containing lines across story
  branches. It is not the scene MES descriptor, and segment order alone does
  not determine boxes, option labels or the active conversation.
- `crates/mes/src/lib.rs`: MES terminators, two-byte glyph/name substitutions,
  spacing and skip aliases, and pager-control bytes. A `0x00` substitution
  operand must not terminate the containing text segment.
- `crates/asset/src/field_disasm/{decode,decode_subops}.rs` and
  `crates/engine-vm/src/field/step.rs`: supported opcode widths, cross-context
  prefixes, flag tests and relative jump arithmetic. Relative PCs wrap at
  16 bits. The pinned disassembler describes system-flag opcodes through `0x7F`,
  but the executing VM's explicit arm ends at `0x77`; this inspector leaves
  `0x78..0x7F` unsupported rather than resolving that discrepancy by assumption.

`inspect_actor_script(disc, scene, actor)` verifies the actor's source locator,
model reference and placement fields against a fresh scene import. It bounds
the compressed MAN stream before the next descriptor and uses the verified
record's existing offset/length. The report contains structural IDs, record
hash/raw bytes, decoded instruction summaries, dialogue text and typed tokens,
source-relative/absolute decoded-MAN spans, explicit stops and opaque regions.

The decoder follows supported encoded continuations and both statically known
flag-branch targets. It does not select story branches, run interaction state
machines, assume every continuation executes, or recursively inspect spawned
records. Inline MES segments are consumed atomically. Unknown opcodes/sub-ops
stop the affected path; there is no one-byte recovery and no scan for attractive
text markers inside opaque instructions or data. Conflicting target/instruction
boundaries invalidate the decoded graph and preserve the record as opaque.
Unvisited bytes remain opaque even when their appearance is familiar.

Names are retained as placeholders such as `{character_name:0}`. Spacing,
wide glyphs, font codes and pager controls remain explicit tokens. Printable
ASCII is a readable inspection rendering, not a full retail-font renderer.
No dialogue boxes, option semantics or current story state are fabricated.

Limits are 65,536 bytes per inspected record, 4,096 visited graph nodes and
4,096 tokens per message, in addition to the existing bounded disc/MAN parsers.
Reports are private source-derived data; they are not project metadata to track.

Actual read-only SCUS-94254 verification, disc SHA-256
`e6120a5d70716dd2f026a2da32d0171d52651971b52c4347a68541299f75258c`:

- Town01 actor0049: record offset 27081, length 255, script offset 21. The
  inspector decodes 23 instructions and seven dialogue segments, including the
  leading character-name substitution. Unvisited tail bytes remain opaque;
  there are no unsupported stops on the traversed paths.
- Actor0052 savepoint: all eleven supported instructions decode, with no
  dialogue. Actor0001 debug record decodes three dialogue segments before
  explicitly stopping at an unsupported `0x29` picker instruction.
- A bounded 52-actor town01 sweep recovered 344 dialogue segments from 29
  actors. Three records have fully covered supported paths; 49 remain partial.
  No conflicting decode boundaries were found. These counts do not establish
  complete dialogue coverage or runtime branch reachability.
- Eight focused tests verify zero-valued substitution operands, aliases and
  opaque tokens, text/data opcode lookalikes, branch arithmetic, conflict
  rejection, unknown-width stops, truncation, source identity and unchanged
  source objects. Decoded/opaque regions partition the inspected script bytes.

Private reports are in ignored `local-output/sdk-20260909/script-inspection`.
No retail dialogue or script payload is included in tracked fixtures.
