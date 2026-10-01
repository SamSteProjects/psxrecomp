# Select a model's effective actor users

Open a model's **Details** button in the Asset Database. The existing Used by
list distinguishes imported and effective assignments and authored NPC drafts.
When2–128 effective imported actors share the model in one scene, choose that
scene and **Select effective actor users**. The editor opens the imported scene,
focuses the first actor, highlights the group and frames its positions. Existing
group placement, appearance and component review tools can then consume it.

Selection issues no authored component or Undo/Redo command. Scene navigation
uses ordinary project selection. Use Saved actor selections separately if a named
persistent group is desired. Retail-only users and NPC drafts remain individually
browsable and are excluded from this group operation. Effective donor assignments
are included. A model's initial user list does not establish current script-driven
or runtime ownership.

The tool checks fresh SDK model references, project context, imported owner IDs,
active-scene effective model IDs, Edit mode and proposal state before selection.
Changed usage rejects; reload the editor and reopen asset details to obtain a
new review. Ambiguous owner IDs or groups outside2–128 are not accepted.

## Offline verification — 2026-09-30

Node checks cover effective-only membership, draft/retail-only exclusion,
ambiguous IDs, mismatched active-scene owners, stale membership, unknown scenes
and detached result arrays. Retail browser selection for town01 model0112 matched
actors0005/0011/0012 exactly, with unchanged overrides/drafts/history and no
selection authoring commands. Dolk2-to-town01 selection and externally changed
usage rejection passed. The stale probe uses one ordinary test command and Undo;
it is separate from the selection tool's zero authoring commands. Zero page
errors, screenshot inspected.

A Details button obstructed by the footer was found during the cross-scene test.
The Asset Database now reserves scrollable list space and allows the tool area to
scroll when its contents exceed the available height. The same browser click
passed after the fix. Private evidence resides in
`local-output/sdk-20260909/component-inspector-20260930/model-users-browser.json`
and `model-users.png`. No game launched; no native/runtime acceptance claimed.

The later integrated offline checkpoint on source `3c8d8f46` passed457 Python
tests with no skips, all12 Node checks and10 module syntax checks. See the
[current SDK status](SDK_STATUS.md) for exact source/command/log evidence.
Feature-specific browser/disk/package checks above remain separate from deferred
runtime and gameplay acceptance.
