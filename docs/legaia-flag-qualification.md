# Independently qualified Current flag operands

An imported actor's native-qualified flag edit can now appear in the Asset
Database, Flag Inspector and active/project flag indices when the broader script
catalog has partial coverage. Previously the native authoring adapter accepted
the edit, but the flag asset validator rejected its Current annotation solely
because the general catalog was partial.

## Source-bound qualification

The SDK reuses the existing `FlagAuthoringContext` verification and serializer
validation. For each owned operand it attaches
`legaia.flag-operand-qualification.v1`: owner and operand IDs, source-record SHA,
instruction PC, mnemonic, extended context, Retail bit, authored bit and supported
maximum. The asset and client validators compare every field with the source
reference and Current ownership. Qualification keys must exactly match authored
operands. Inherited references carry no authored qualification.

The reference DTO's optional field is `authored_qualification`; the graph's
Current binding exposes the same proof as `native_operand_qualification`.
Existing complete-coverage DTOs remain accepted without the new field. Partial
coverage requires the independently verified proof for a Current annotation.
Local flags remain limited to bits 0–15, other supported banks to 0–31. Existing
context SET-8/CLEAR-10 side-effect exclusions remain enforced. Missing, forged,
extra-field and incorrectly owned proofs reject.

The Inspector keeps partial coverage visible and explains that qualification
applies to one native authoring operand. This is no claim of complete script
decoding, runtime flag values or actual execution. Retail flag group identities
remain stable. NPC clone Current operands retain their own ownership; an imported
donor's Current override does not propagate to clones. Project format, native
serialization and runtime behavior are unchanged.

## Acceptance

Forty-one affected Python checks passed with no skips, five client suites and
three syntax checks passed. Focused tests cover source validation, Undo/Redo,
active/project indices, imported/NPC graph ownership, HTTP authoring and malformed
proof rejection. The full regression campaign was not repeated.

The actual Town0b donor `scene://town0b/actors/man-p1/0037` retains partial general
coverage. Its CFLAG_SET operand at PC `0x001e` keeps Retail bit 2 and Current bit
5. Its two NPC clones independently keep Current bits 3 and 4. The private editor
exercised the real Inspector modules and live SDK reference API, source-PC
navigation and wide/400 px layouts. Both screenshots were inspected; there were
no page errors or game launch requests. Save/Open remained exact, and inspection
did not change project, history, saved content, active scene or Build key.

A fresh normal private compressed Town0b Build `a08ef2394ae1b806` passed integrity
and current-input verification. Independent readback matched all three complete
native records against Retail bytes plus their separately owned edits:

| Record | SHA-256 |
| --- | --- |
| Imported donor, Current bit 5 | `5d1cdf03821f9e2238dc3ca6b65431bf35b5a06d3f402d40b0e65200c01ce2c3` |
| NPC `2e1273b5-4544-4aa7-ae1f-201c31890a01`, bit 3 | `b5eb849ea38a47bc6952dc0aa15b130c90d0b0a67524e56eae3f21dc235d20d5` |
| NPC `7eecb0e2-8518-4816-a11c-55d20455b730`, bit 4 | `2cfaff162afb4bf5af9aa80b11a5e8629af756745357f1c20ccd17e6c1fe281f` |

Package SHA-256:
`e7fc1378ad1db2b13b87cea12d0c75edd09757002b0965f331840f55062a4d70`.
Retained NPC placement, facing and color edits survived. Build left project and
history unchanged. No game was launched, no package installed and no full disc
exported. Gameplay verification remains deferred.

Private evidence: `local-output/sdk-20260909/partial-flag-qualification-20261007/`
contains fixtures, focused checks, browser proof, screenshots, complete native
record proof and the private project/Build. Development remains solo; the full
SDK goal remains active.
