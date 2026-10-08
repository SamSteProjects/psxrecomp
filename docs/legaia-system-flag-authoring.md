# System Flag Selector Authoring Foundation

The native writer for normal SYSFLAG SET/CLEAR/TEST selectors is implemented separately from existing one-byte L/G/C flag authoring. A selector spans the opcode's low four bits and its following byte. `patch_system_flag_selector` accepts only an integer `index` from0 to4095 and preserves the high opcode nibble, operation, TEST branch word, decoded continuations, record length and surrounding bytes. Source paths must have no decoder stops. Extended raw addressing remains unsupported.

`SystemFlagAuthoringContext` discovers stable `script://.../system-flag/PPPP` targets from uniquely owned Retail actor or partition-two records, returns two-byte provenance audits and patches a complete MAN while preserving immutable source input. The edit collection is bounded to1024. Full spans are reserved even for no-op edits; overlap and aliasing refuse. Appended MAN support locates the original owner's rebased record, checks the source operation/preimage/edges and leaves donor clones unchanged. Candidate preimages and edges are checked even for no-op requests.

This is infrastructure for the requested editor-to-playable authoring workflow. It is **not exposed as an SDK project component, editor command or normal Build family yet**. Existing ScriptFlags and NPC flag schemas still describe one-byte indices; they are deliberately not broadened to accept this new two-byte format. No UI authoring capability is advertised by this change. The next integration must add typed Current/Proposed reports, atomic Review/Apply and persistence, followed by Build and package readback before exposing the control.

## Focused Offline Evidence

On October 7, 2026, 12 Python tests passed across the new writer, source system-flag evidence and existing flag authoring. Tests check all4096 selectors for each SET/CLEAR/TEST operation, distinct forward/backward TEST continuations, full byte equality, unchanged widths, exact no-ops, invalid inputs, unresolved/extended dispatch refusal, MAN ownership and aliases, detached audits, clone-preserving appended ownership, and no-op candidate preimage/branch-word refusal.

Fresh private Town01 actor0011 PC22 qualifies selector326. Editing to4095 produces `71 46` → `7F FF`. The complete MAN equals an independent literal two-byte replacement; every other byte and the MAN record layout remain exact. The existing native Retail helper test verifies the executing MSB-first system-selector behavior against the intended Andrew pin, described in [System Flag Simulation](legaia-script-system-flags.md). No proprietary payload is committed.

No project commands, native Build, game, runtime attachment, installation or disc export ran for this foundation. Native bank allocation capacity, story meaning and gameplay behavior remain unverified. The full SDK goal stays active; source qualification is one necessary stage, not completion of the authoring feature.
