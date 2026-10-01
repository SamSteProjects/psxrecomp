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

## Preview both components in the assembled scene

From the combined preset review, choose **Inspect combined preset in scene**.
The authored scene must be loaded. A detached SDK projection resolves the
proposed position and donor's initial model/animation together. Inspection writes
no project overrides or history. Source terrain supplies a display height only
when retail Y is unknown; it does not establish runtime height.

**Inspection layer** switches between Proposed and Current while retaining the
camera. **Return to combined preset** restores the authored scene and reopens the
same review for Apply. **Restore scene preview** discards the inspection and its
retained review. Export requires restoration. Changes to the scene components,
preset, source or selection withdraw the comparison; delayed or closed requests
cannot attach. Both source-qualified donor and reviewed position are checked,
including display coordinates, matrix and unchanged owners/geometry.

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

## Scene comparison validation — 2026-09-30

Fourteen focused Python checks passed, including detached two-component
projection, preserved target axes/history and forged/stale/inactive target
rejection. Node preset and existing appearance checks passed for positions,
display matrices, authored axes, height uncertainty, donor ownership and
unchanged geometry. Retail-source browser comparison moved town01 actor0012
from X2880 to X2944 with donor0005/model0112, retaining Z1856 and unknown
retail Y. Inspection changed no component/history state. Current/Proposed
retained the camera; Return preserved one Apply/Undo; Restore removed the review;
closed delayed-response withdrawal, stale target and export guards passed.
Zero page errors; final focused screenshot inspected.
All transient fixture edits were restored without saving.
Private evidence: `local-output/sdk-20260909/actor-preset-scene-20260930/`.
No real runtime or gameplay acceptance is claimed.

Presets can also be [exported/imported as source-bound metadata files](legaia-actor-preset-files.md) for reuse in another project.

The later integrated offline checkpoint on source `3c8d8f46` passed457 Python
tests with no skips, all12 Node checks and10 module syntax checks. See the
[current SDK status](SDK_STATUS.md) for exact source/command/log evidence.
Feature-specific browser/disk/package checks above remain separate from deferred
runtime and gameplay acceptance.
