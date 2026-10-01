# Actor group donor appearance

Select 2–128 imported active-scene actors through Ctrl-click, hierarchy ranges or
box selection, then choose **Group appearance…**. The SDK verifies the current
retail import and lists only donor initial model/animation pairs compatible with
every selected actor. A group with no common pair stays read only and displays
source support reasons. NPC drafts, scenery and other scenes retain their tools.

Choose a donor and **Preview group appearance**. Review each actor's Retail,
Authored, Effective and Proposed data plus the shared model/animation summary.
Preview does not change the project or execute animation/script instructions.
**Apply reviewed group appearance** revalidates all actors and publishes one
atomic command. One Undo/Redo restores/reapplies the changed owners, preserving
Transforms, dialogue and other components. Save/Open and existing Build consumers
use normal ActorAppearance overrides. Reapplying an already identical group is a
no-op. Group component review can revert appearance independently afterward.

With the authored scene's models loaded, choose **Inspect group appearance in
scene** after Preview. The proposed source initial pair appears at each selected
owner's unchanged position. **Inspection layer** switches between Proposed and
Current without moving the camera. **Return to group appearance** restores the
current scene and retains the selected donor/report for Apply. **Restore scene
preview** discards the comparison. Export requires restoration first. A changed
scene/source, group or placement withdraws inspection; this is a static source
pose comparison, not runtime animation playback.

`/api/actor-appearance-batch-scene` accepts actor IDs, a nonnull donor and the
review key only. It recomputes the report before resolving a detached project
view through the ordinary scene service. No overrides, history or files are
written. The client binds every selected owner to the reviewed donor, checks
unchanged placements/transforms and checks unrelated geometry/texture content.
Shared initial-pose deduplication can change first-source actor attribution;
that metadata is excluded from unrelated geometry equality while animation and
model evidence remain checked. Unavailable models remain explicitly counted.

`/api/actor-appearance-batch` accepts actor IDs and a nullable donor ID only.
Discovery verifies one imported scene against the user-owned disc, loads its
assignment context once and intersects supported donor records. Chosen donors
must also satisfy each target's existing object-count/initial-pair checks.
The report binds project/source, selected ActorAppearance values, donor, options
and assignment provenance. Strict `set_actor_group_appearance` recomputes that
identity before mutation. A changed last member or unsupported donor rejects the
entire group. Other authored components remain independent. Closed/source-changed
responses cannot attach to another review; Live authoring is disabled.

This changes initial MAN header model/animation assignments only. Nonzero existing
animation and supported scene-model restrictions remain. Script scheduling,
runtime model-pool residency, retargeting and gameplay compatibility are unknown.
Source model/animation pairs are not proof of runtime acceptance.

## Evidence — 2026-09-30

Sixteen focused retail-enabled group/appearance/component tests passed in7.005s,
no skips. Six new group tests cover shared options, detached no-write preview,
source/unrelated preservation, atomic stale/incompatible rejection, one history
entry, no-op/replay, strict HTTP fields, real retail Save/Open/Undo/Redo and
unsupported initial pairs. Editor/new-module syntax and diff checks passed.

Retail town01 browser actor0011/0012 discovered12 common donors. Preview was
unapplied; one command assigned actor0005's initial pair (model0112/animation57)
to both. Undo restored authored assets and dirty status; Redo/Save retained it.
Changing the last actor's appearance after review rejected the group without
additional mutation. Actor0001/0002 correctly offered no donors because their
initial animation assignment is unsupported. Zero page errors. Screenshot inspected.

Independent disk reopen and ZIP/LZS MAN readback matched the exact expected source
with both header assignments, existing position overrides, all three menu runs
and selector240. Candidate actor headers were independently parsed. No package
installed or game launched; gameplay remains in the deferred queue. Private
`local-output/sdk-20260909/group-appearance-20260930/` contains
`group-appearance-browser-check.json`, `group-appearance-preview.png` and
`group-appearance-package-check.json`. Package SHA256:
`20146bacf0784539e79cf6a531cbd154ff921016895d8fe47ebd8e4b27b76be6`.
Owned browsers/servers closed. This backend/UI feature postdates the425-test full
source checkpoint; focused/browser/package evidence above is current.

## Scene comparison evidence - 2026-09-30

Seventeen focused retail-enabled tests passed in7.010s, no skips, including
detached projection, stale/discovery rejection and strict scene endpoint fields.
Node checks cover source/review/donor identity, exact placement, unrelated content,
missing/duplicate owners and geometry, detached return values and shared pose
attribution versus changed animation evidence. Editor/module syntax passed.

In a separate private saved-project copy, actor0011/0012 were compared with
actor0011's initial pair (model0105/animation13), while their current assignment
was actor0005 (model0112/animation57). Both proposed geometries changed; every
position/model-to-scene transform and unrelated geometry/texture payload remained
unchanged. Camera was unchanged across Proposed/Current. Preview performed no
commands; Return retained the report for one Apply, then Undo restored authored
assets and dirty status. Restore, export rejection, a real authored source change
withdrawing comparison and closing a held response all passed. Zero page errors;
Proposed/Current screenshots inspected. Browser and server closed. No game launch
or package install. Evidence lives privately in
`local-output/sdk-20260909/group-appearance-scene-20260930/`, including
`group-appearance-scene-browser-check.json`, `proposed-group-appearance.png` and
`current-group-appearance.png`. The425-test full checkpoint predates this feature.

## Integrated source checkpoint - 2026-09-30

All441 retail-enabled SDK Python discovery tests passed in177.315s, exit0, no
skips, on unchanged source `e76b05fb1775802057e41c33a5a1e4e36301a093`. This includes
the Python services described above; all eight Node checks and five syntax checks
also passed on that source. The earlier425 checkpoint predates these additions;
441 is the current integrated result. Existing browser/package/disk evidence
remains separate. No game launched; deferred gameplay acceptance is unchanged.
See SDK_STATUS.md for exact source/command/log/hash metadata.
