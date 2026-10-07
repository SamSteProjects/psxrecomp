# Project settings inspector

Use [Review Unsaved Project Changes](legaia-project-change-review.md) to compare saved/current metadata and save a current reviewed document.

For independent authoring experiments, **Copy project…** beside Settings captures
current inputs, including unsaved edits, without saving the original. See
[Editable project copies](legaia-project-copies.md).

Open **Settings…** beside Project in the top bar. SDK inspector metadata displays
the current name, project folder, retail source path and identity, imported scene
count, active scene and mode. Source and path properties are read-only. Unknown
source values remain unknown; this panel does not replace project Open/Create,
scene import or runtime launch configuration.

In Edit mode, **Rename project…** opens the name field. Apply sends one validated
project command with the inspected name identity. Names use1–120 Unicode scalar
characters after trimming; control characters and lone surrogate code units
reject. Quotes and characters outside the basic Unicode plane are supported.
Changing the name marks Project name unsaved. Save persists it; Undo/Redo restores
the old/new names. Imported records, asset identities and overrides are preserved.
An unchanged name adds no history. Renaming changes future package identity;
existing build freshness follows the ordinary authored-state check.

SDK action metadata is constrained by the editor's explicit rename adapter.
Unknown command descriptors, missing capability, Live mode, busy/closed panels
and changed settings snapshots cannot dispatch through the form. The server also
rejects a stale name review key and extra fields. Paths and retail inputs cannot
be changed by this command.

## Verification — 2026-10-01

Fourteen focused Python checks passed, covering project settings, existing
project workflows and inspector contracts. One retail-gated check builds a
quoted non-BMP project name and parses the actual TOML package manifest. All21
Node test files and23 editor syntax checks passed. The actual browser verified
SDK properties, one rename, Save/Undo/Redo, stale-form withdrawal, unchanged
authored content, zero page errors and restored baseline; screenshot inspected.

Independent reopen proved that only the project name metadata changed and all
four NPC drafts remained. Detached no-draft normal builds preserved every other
content payload; the renamed manifest parsed correctly. Package SHA256:
`4daae62c19f20ef0066966958460e73e904e824ab7c6f26b202696446c6c74c5`.
The probe exposed an existing manifest bug: default JSON escaping emits UTF-16
surrogate pairs for non-BMP names, which TOML rejects. Names now emit literal
UTF-8 with ordinary quote/backslash escaping.

Private evidence: `local-output/sdk-20260909/project-settings-20261001/`.
Normal Build still rejects drafts; verification detached them only in memory.
No game launched or disc installed. Gameplay remains deferred. These focused
checks postdate the integrated475-test checkpoint and do not prove full SDK or
runtime completion.
