# Read-only actor script and dialogue inspection

Effect-spawn evidence (2026-10-03): unchanged hashed PROT897.
Opcode34 table801CED0C→801DFCAC. Sub1 scans existing actors and compares
actor+90 to current s5; matching exit801DFF48→801E2EA0 skips capture.
Otherwise callback801E5668 at801DFFE0 creates/selects the effect actor.
801DFFEC advances operand pointer12, then801DFFF0/F4/F8 peeks for40.
Capture writes the pointer after marker/length to actor+94 at801E0000;
801E000C/10/18 adds2+declared length to adjusted PC. Shared exit
801E2EA0/2EA4 adds13 and returns advanced PC through801E3624.
Thus base packet extent is13 ordinary/14 extended, but following capture
ownership depends on existing-actor match. Inspection requires lookahead and
full capture extent; unlike pinned missing-byte defaults it never substitutes
zero or an empty payload for absent source bytes. Conditional offsets are
operands only; no graph edges or editable destinations are fabricated for capture.
Town01 actor0020 PC34 contains an extended14-byte packet at decoded11484,
marker40 at record48, length15 and payload at record50/decoded11500.
Existing-actor continuation48 and new-actor capture continuation65 remain
conditional/unexecuted. Record SHA256
fd45c73fb74606b946f73639b2b768c75dc72cd782448ac6302ccd68419be4f4.
Independent full carrier/record reconstruction and actual browser source fields
agree; no project files/history/authored state change. Conditional payload
ownership and runtime actor identity remain unresolved source/model work.

Actor-acquire evidence (2026-10-03): unchanged hash-bound PROT897.
Opcode43 table801CED48→801DF354; inner entries801CEDA8/AC/D0/D4
share801DF384 for00/01/A/B. Failure801DF410→801DEE4C restores s8=s4;
801DEE54 returns original PC. Success reads encoded XZ bytes+1/+2, derives
or queries a position, and passes a stack vector plus signed parameters+3/+5
to callback801D25EC. These fields are not resume PCs. Player/nonplayer
parameter pointer reads are801DF550/554 and801DF580/584. Wide>=A reads+7
at801DF524/528, negates the vertical operand and advances2 at801DF534.
The shared success exit801DF5B4/5B8 advances8 then returns advanced s8 via
801E3624. Ordinary widths are8/10; extended widths9/11. Pinned actor_ctrl.rs
5/9-byte widths, target-word interpretation and failure advance are superseded.
Encoded positions are retained without imported actor or runtime pose inference.
Independent fresh whole-carrier/record reads confirm Town01 P2 record0005
PC1600/decoded34438 (parameters12/12) and0012/13/14 PC57 at40292/40420/40548
(parameters96/24). All four are nine-byte extended forms; dispatch contexts70
and248 remain unresolved numeric selectors. The branch writer rejects these
instructions: callback parameters cannot be edited as script destinations.
Browser evidence agrees on source core fields and preserves all project bytes,
authored state and history. Runtime acquisition/flags/pose remain unobserved.

FMV request evidence (2026-10-03): unchanged hashed PROT897 and SCUS.
Table801CF010 dispatches E2 to801E30E4; call8003CE9C reads operand+1
(delay slot801E30E8). The SCUS loader packs low/high bytes and sign-extends
via SLL16 / SRA16 at8003CEAC/CEB4. PC advances6 at801E30EC.
801E30F4 stores the returned halfword to8007BA78;801E30FC loads26 and
801E3104 stores it to8007B83C in the jump delay slot.801E3100 jumps to
801E3624, which returns advanced s8. No instruction in this handler reads
operand+3/+4, although both belong to its six-byte ordinary extent (extended7).
Pinned nibble_e.rs reads the same ID but its truncation guard only requires
three payload bytes; inspection requires the full five-byte payload to avoid
accepting incomplete instructions. It does not label unread bytes as parameters.
Town01 P2 record0025 PC1804 contains4CE201000000 at decoded offset44355;
record SHA256 e99ea95a92c44ced1f884ed122bac6d8ea34db76939093b87eda14ccb68b4cc3.
Fresh complete carrier/record reconstruction confirms that extent andPC1810.
The catalog has204 supported-path instructions/28 dialogues/no stops for this
owner. Two browser checks preserve files/history/authored state; no request is
executed and no request-ID editor exists. Movie activation and playback remain
runtime-unverified. Private proof: `local-output/sdk-20260909/fmv-trigger-20261003/parent/`.

Actor-state-copy evidence (2026-10-03): unchanged PROT897 SHA256
216f846db5ab085a295cef4064747380a06c995caa3e1b2773e78a1d349f126b,
load base801CE818 and unchanged Andrew pin d6e64c68ede25813d35db20980da82a1a025549b.
Table801CF014 dispatches E3 to801E3108. Selector byte+1 is passed to lookup
8003C83C at801E310C; returned v0 becomes a0 at801E3114. LHU(a0)/SH(s5)
pairs3120/3128,312C/3134,3138/3140,3144/314C copy fields14/16/18/26 from
resolved actor to current dispatch context. The pinned nibble_e.rs camera-to-actor
direction is superseded by these words. Missing lookup branches3118→3174,
skipping field copies but retaining context post-updates; it is not a full no-op.
Current flag bit29 gates negative sourceY to context+8E at3164/316C/3170.
Player context invokes80017EC8; both exits advance adjusted PC3, giving ordinary
width3 / extended4. Runtime fields and imported actor correlation remain unknown.
Fresh Dolk2 P2 record0011 SHA256
3f6b3ecde4e9c576319804e1739cf4d1155c79d923c21cd23639ae70160428bc
contains sixteen extended copies at PCs51/59/67/75/83/91/99/107 and
1160/1168/1176/1184/1192/1200/1208/1216. First selectors44/33/32/38/36/39/34/35
use dispatch contexts82..89; later selectors82..89 use those earlier contexts.
These are encoded inverse pairs, not proved capture/restore roles. Independent
fresh decoded-MAN/record readback confirms offsets33009..33065 and34118..34174
at eight-byte intervals. Browser core fields match all source fixtures; no files,
commands or history change. The new choice27 stop leaves Dolk2's total at30.

Embedded STATE_RESUME0 evidence (2026-10-03), superseding the earlier
fixed-only limitation: unchanged hashed PROT897/SCUS. Completed state dispatch
801E08EC reads length at operand+2;801E08F4/F8 adds length+4 to adjusted PC.
801E08FC/0904 passes operand+length+3 to native walker8003CA38.
801E0908/0910 adds1 plus returned payload bytes, owning its terminator.
This establishes total ordinary width length+5+walker_count (extended+1).
The pinned flow.rs reads length at operand+1; retail words supersede that offset.
Prefix+1 and declared arguments remain encoded facts with runtime meaning unknown.
A shared bounded native payload helper now serves both this form and MENU80;
only C0..CF skip a second byte, and byte≤1E ends a span. It does not run a VM,
render text, create parent dialogue assets or permit embedded target editing.
Dolk2 actor0011 PC115/decoded9872 has24 bytes (10 arguments,10-byte payload);
actor0012 PC112/decoded10152 has25 bytes (10 arguments,11-byte payload).
Independent fresh carrier/record readback confirms both layouts. Completion is
conditional on external state; menu activation/effects remain unobserved.

Scene-register/callback evidence (2026-10-03): unchanged hashed PROT897.
Table801CED78→801E0C0C reads byte operands0/1/2 at801E0C14/20/2C,
stores zero-extended values into scene halfwords10/12/14 at801E0C1C/28/38,
and advances adjusted PC4 at801E0C30. No target word exists.
OuterE table801CF030→801E34CC calls8003C7EC, adds2 to adjusted PC in
its delay slot801E34D0, then returns advanced s8 at801E34D8. The pinned
nibble_e.rs description of a halt is superseded by these executing words.
Callback effects and scene-register runtime meaning remain unresolved.
Neither handler is invoked or given an operand serializer by inspection.
Fresh map01 P2 record0038 PC110 contains4F01385A at decoded6873;
record0039 PC687 contains4CEA at decoded7983. Full carrier/record comparison
and actual browser source inspection agree on both boundaries. Remaining
map01 catalog stops are choice-pager boundaries; this is not proof of full
world-map overlay coverage or runtime branch execution.

MENU8 allocator and fixed-write evidence (2026-10-03): unchanged hashed PROT897
and SCUS, recorded below. Tables801CEF48/50/58/6C dispatch80/82/84/89 to
801E1ECC/206C/2134/22C8. MENU80 success first advances3 at801E1F78; it then
reads count at operand+1 and repeatedly calls native walker8003CA38, adding
walker length+1 to both adjusted PC and source pointer (801E1F98..1FB8).
The failure path801DEE4C restores original saved PC, including extended header.
The pinned source's fixed header-only continuation is superseded here.
SCUS walker tests byte<31, consumes an extra argument only when high nibble=C,
and returns bytes before the terminator; caller owns that terminator too.
Child spans are opaque allocator operands, not parent MES assets or guessed
child actor scripts. Every child must terminate inside the verified record;
truncation/token-limit/ownership conflicts stop without recovery.

MENU82 reads byte selector+1, copies character fields6CC→6CE /6D0→6D2 and
advances3. MENU84 reads byte+1, writes8007B630 and advances3. MENU89 reads
signed word+1, stores low16 at80073F00 and advances4 through801E3620.
These offsets label native evidence only; runtime selector correlation is unknown.
Fresh map01 P2 record0039 SHA256
`6854ade69c74c22fe34153c1550014a7ca574944b70e20600b275490b51ff942`
contains extended MENU80 at PC183/decoded7479, length369 with14 children.
Independent carrier/record reconstruction agrees with the inspector. No allocation
executes, and no serializer for these operands is introduced.

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
