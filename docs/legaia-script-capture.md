# Conditional capture inspection

Open an actor's **Inspect script and dialogue** workspace and select an
`EFFECT_SPAWN_PACKET` instruction with a decoded capture descriptor.
The **Conditional capture** summary shows its payload start and byte count,
then the possible continuations for an existing actor match and a new actor capture.
These offsets are relative to the bounded source record.

The offsets are plain text because they are not confirmed parent instruction
boundaries. Actor match and payload ownership remain unresolved. Captured bytes
are not automatically parent dialogue or instructions, and conflicting incoming
parent paths invalidate the ambiguous source graph. The summary does not edit,
execute or navigate the capture. Expand **Encoded operands** for its source bytes
and conditional descriptor; that disclosure starts collapsed when the summary
qualifies successfully. Other instructions retain their existing presentation.

For example, retail Town01 actor0020 PC34 has an extended14-byte base packet,
a15-byte payload beginning0x32, and possible continuations0x30/0x41. This does
not establish which path executes or correlate extended target56 to a live actor.
Conditional source ownership and runtime observation still need further work.

The summary checks packet/header/context bytes, payload extent and byte count,
both conditional offsets and unresolved/no-successor state. A mismatched row
falls back to ordinary raw rendering. It introduces no action controls or
new operand writer. Narrow viewport containment, raw disclosure and unchanged
project files/history were checked on the actual retail source.
