# Combined actor presets

Select an imported actor with authored position axes and a donor appearance.
Open **Authored actor templates**, enter a name and choose **Capture position
and appearance**. Existing position-only and appearance-only presets remain
supported. The combined preset stores only captured authored axes and the
source-qualified donor, with template UUID and disc/scene/actor provenance.

Select another compatible existing actor and choose **Review combined preset**.
The read-only dialog separates imported, authored, effective and proposed
positions, shows the donor and reports Build issues. Saved coordinates are
absolute. Uncaptured axes and unrelated target components remain unchanged.
Apply revalidates the template, imported evidence, target overrides and fresh
compatible donor options before one history entry. Stale/incompatible reviews
reject both changes. An already matching target creates no history entry.
Undo/Redo, template rename/delete and Save/Open use normal project services.
No actor is instantiated and no imported provenance is replaced.

## Output and verification — 2026-09-30

Thirteen focused Python tests passed for combined capture, validation, read-only
review, one-entry history, unchanged axes/components, Save/Open, no-op and stale/
incompatible/Live rejection. Retail browser capture/review/Apply/Undo/Redo,
Save/reload and stale-target rejection passed, zero page errors; screenshot
inspected. Independent disk reopen retained the combined preset and its target.
Town01 actor0012 received X2944 and donor0005 while retaining Z1856.

Normal Build rejects projects containing NPC drafts. The private fixture keeps
all four drafts; normal package verification used a detached no-draft project
view and changed no saved project inputs. Full package MAN bytes matched expected
positions/appearance and retained earlier menu/selector/distribution edits.
Package SHA256: `a59e32eaf00f07971a0f36eb83ff10529eea908d34dd98404f07042bc6cf6567`.
Full experimental archive preparation/reopen retained all four drafts and preset
edits. Archive SHA256:
`2f9437b5a0eda2ed4ae9eaf8bf810a6f2f9c0936942e1caae8c3c0a818e43381`.
Private evidence is in `local-output/sdk-20260909/component-inspector-20260930/`.

No disc installed or game launched. Script-driven movement, model replacement,
visibility, collision and gameplay remain deferred. This feature postdates the
441-test integrated source checkpoint.
