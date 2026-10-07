# NPC-owned flag operand references

Asset references now connects an authored NPC to every reached encoded flag
reference in its qualified Retail donor script. Selecting a flag asset shows
all NPC clone owners in Referenced by. Selecting the NPC shows its flag groups
in Dependencies. Search can filter by stable operand ID, bit, bank or owner.
The same links appear in active and project scopes and reference-report exports.
Inspect retail donor instruction navigates to the source script and exact PC;
its label distinguishes that source site from the NPC's generated script.

## Ownership and qualification

The existing source flag asset remains grouped by Retail script/context/bank/bit.
It is not renamed when the NPC changes its encoded bit. Each
`npc_script_flag_operand` edge uses the authored ownership layer and carries:

- Retail group bank, bit, scope, operation, mnemonic and extended target;
- complete qualified donor proof, including source-record SHA, pinned reference,
  byte coordinates, script coverage status and complete authored NPC digest;
- stable editable operand ID, or null for a noneditable source reference;
- separate Retail, authored (nullable) and effective NPC bit indices;
- `authored_operand_qualified`, true only for a freshly native-qualified NPC edit;
- imported document hash and resource catalog key.

`sdk/npc_flag_references.py` compares each site with the unique decoded source
instruction. The graph validates NPC flag ownership through the existing
`npc_flags`/`FlagAuthoringContext` adapter once per NPC, then matches owned target
PC, mnemonic, source hash, context, original bit and supported maximum. The
broader catalog may have partial coverage while the dedicated native adapter
qualifies a reached editable operand. Those two facts remain separate in the
proof and visible UI. Local-bank widths and context SET-8/CLEAR-10 side effects
retain their existing authoring exclusions. Missing catalog rows remain
unresolved; duplicate sites and conflicting source proofs reject.

The client validates exact proof shapes, source/target/scene types and ownership,
source ranges/pin, operand IDs, bits, side-effect exclusions and repeated owner
consistency. Inherited references retain nullable authored values. An NPC's
Current bits do not inherit the donor actor's authored `ScriptFlags`; they come
from the NPC draft or its immutable Retail donor. Matching source groups are not
merged into global runtime variables. Live values, actual execution, scheduler
behavior and emitted Build bytes are not asserted by these graph links.

No new project mutation, saved format, native serializer or runtime behavior is
introduced. Existing NPC flag authoring, history, persistence and Build adapters
remain responsible for changes and native delivery.

## Acceptance

Thirty affected Python checks passed with no skips, four client suites and two
syntax checks passed. Synthetic checks distinguish two NPC bit owners from a
third imported donor override. Fresh actual Town0b reports decoded in the client;
the private editor navigated NPC -> flag -> other NPC, project scope and the
source donor instruction. Retail bit 2 remained distinct from NPC Current bits
3 and 4. Source-change refresh withdrew links; wide/400 px layouts were inspected
without page errors or game launch requests. Inspection left project, history,
scene selection, saved file and Build key unchanged. Save/Open readback stayed
exact. No new native Build or full campaign was run.

Private evidence: `local-output/sdk-20260909/npc-flag-navigation-20261007/` contains
`reports.json`, `metadata-proof.json`, `browser.json`, `focused.json`, logs and
screenshots. Initial private harness failures are retained separately.

The retail exercise exposed a separate imported-actor limitation: Current
`ScriptFlags` annotations required complete general catalog status even when the
native adapter independently qualified an operand. The subsequent
[flag qualification fix](legaia-flag-qualification.md) resolves that rejection
without changing partial coverage. Its fresh Town0b Build independently matches
the imported donor's Current bit 5 and both NPCs' separately owned bits 3 and 4.
The evidence above records this earlier milestone before that fix.

Gameplay verification remains deferred. Development remains solo; the full SDK
goal remains active.
