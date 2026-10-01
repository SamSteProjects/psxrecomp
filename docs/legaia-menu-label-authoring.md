# Field menu label authoring

Open an actor's **Script and dialogue** Inspector, or a supported partition-two
script through the resource catalog. Editable labels appear as **Menu option N
of M**, with picker offset, label-run offset, source byte capacity and encoded
choice target. In **Instruction paths**, each supported picker choice lists separate retail,
authored and effective text for its label runs. Use **Open label editor** to
focus the exact run without discarding an existing draft. A label containing
controls may have multiple run links. Links require matching owner, option,
source PC/target and glyph tokens; stale source or withdrawn reports cannot
navigate. Read-only instruction inspection remains available separately.

Enter printable ASCII and use **Apply text**. Shorter text is padded with spaces;
empty text becomes spaces. **Discard draft** restores the form. **Clear override**
inherits retail text. Apply or discard drafts before project actions. Existing
Undo/Redo, Save/Open, authored-asset navigation and Build use the same Dialogue
component as ordinary text; menu run IDs distinguish option ownership.

Only contiguous one-byte printable glyph runs are writable. Caret, controls,
substitutions, escaped/wide glyphs, longer text, jump entries and continuation
editing are unsupported. Controls split labels into separate editable runs.
Source-qualified IDs are reverified on edit and Build; aliased records and
conflicting decode boundaries are rejected. Ordinary dialogue retains its
existing no-stop gate. A decoded menu can offer local label spans while its
pager control flow remains explicitly unresolved.

The serializer compares the decoded graph and token boundaries after editing,
masking only permitted glyph bytes in picker raw/operand mirrors. Targets,
option count, continuation, controls and opaque bytes stay equal. Actor-table
append composition rebases each source span and requires an exact preimage.
Build audits label changes with `menu-label-glyph-run-only` scope.

Format evidence: read-only LegaiaRE commit
`d6e64c68ede25813d35db20980da82a1a025549b`, `crates/mes/src/picker.rs`,
MES token decoding and MAN record bounds. Relative targets use each signed
16-bit jump entry's own PC. Reference source is not a shipped dependency.

## Current evidence and limits

54 focused dialogue/script/resource tests passed with the private retail disc,
no skips, in29.896 seconds. These include two/three/four options, high-bit open
bytes, immediate/continue/terminate forms, controls and substitutions, aliases,
conflicts, invalid text/IDs, actor-table rebasing, and partition-one/two command
history and persistence. Editor JavaScript syntax passed.

A private town01 actor0001 source menu passed browser draft/no-write, capacity
and caret rejection, Apply/Clear/Discard, Undo/Redo, forged-option rejection,
Save and fresh browser reopen. The Inspector screenshot was inspected. Its
saved project rebuilt and independent ZIP/LZS readback matched the expected
MAN exactly, including all untouched controls/targets/offsets. Evidence is in
`local-output/sdk-20260909/menu-label-project-20260930/`.

This is source serialization evidence for a decoded menu. It does not establish
that actor0001's menu is reachable in ordinary gameplay. Runtime menu selection,
font/wrapping and story reachability remain deferred; no game was launched.
The392-test full-suite checkpoint at `1eafc313` predates this addition.

Instruction-to-label navigation was separately browser verified on the saved
retail project: all30 supported links present, exact textarea focused, an
unapplied draft retained, source/report withdrawal guarded, and project/camera/
service unchanged with no authoring requests or page errors. Pure JavaScript
checks include mismatched owner/PC/option/target/token data, duplicate ambiguity,
collection bounds, separate control-delimited runs and partition-two identity.
Evidence: `navigation-browser-check.json` and `menu-label-navigation.png` in the
private project directory. These checks do not simulate or execute choices.
