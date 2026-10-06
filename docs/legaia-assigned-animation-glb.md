# GLB authoring for assigned actor poses

An actor with qualified **ActorAppearance** or **ActorAnimation** assignments can
now use **Author animation channels → Edit animation through GLB**. Export uses
the assigned existing pose witness and inherited model. The selected actor keeps
its identity in the export and proposed-pose viewer.

The v2 binding sidecar adds `channel_owner_entity_id` and
`model_source_entity_id`. Channel ownership remains anchored to the imported
actor that witnesses this shared clip. For example, town0b actor0019 assigned
clip0012 exports through witness0049. Apply stores the imported clip0012
contribution on actor0049; actor0019's existing imported clip0013 contribution
and initial assignments remain intact. Every user of the shared clip receives
its channel changes. The export status and reviewed proposal show the owner
explicitly before Apply.

Assignments and their witnesses are freshly qualified before export, review,
pose preview and Apply. Changing the model/clip, contribution ownership or scene
source invalidates the binding. A forged owner or model witness rejects against
the regenerated binding. V1 sidecars retain their original exact contract for
unassigned actors. The review schema remains v1; assigned reviews require an
owner field that matches the v2 binding.

Unchanged axes retain ownership, changed axes update the named owner's existing
AnimationChannels component, and values restored to retail remove that owner's
axis. Other contributors remain separate. Conflicting shared contributions still
reject, and no-op uploads cannot clear edits. Review and pose preview remain
read-only; Apply creates one normal command/Undo step. Save/Open and normal Build
use the existing serializers and source capacities.

This supports existing, qualified rigid-object bindings. It does not allocate
clips, change frame/object counts, infer timing, retarget skeletons or establish
native clip selection/visibility. Unsupported source bindings stay unsupported.
See [GLB workflow and limits](legaia-animation-glb.md).

## Offline evidence — 2026-10-02

Four distinct focused Python workflow cases pass with private retail input and
no skips, including v1 shared-axis/conflict/source regressions and the new
assigned clip/appearance path. Node checks pass exact v1/v2 bindings, owner
matching, contributor identities and the existing review/Return/late-response
guards. Eight actual browser scenarios pass: assigned export, exact file
downloads, owner-labelled review, proposed pose with retained Return,540px
layout, explicit Apply, history/persistence and normal Build. No page errors or
game requests occurred. Desktop review/pose screenshots were inspected.

The town0b fixture preserves all selected actor0019 components, including its
clip0013 X edit. The GLB adds one frame0/object0 X unit on witness0049's clip0012.
Independent packed-X reconstruction verifies all91784 decoded ANM bytes;
only bytes8880 and10336 differ from retail. Complete MAN readback verifies only
byte9471 changes from14 to13 for the existing initial assignment. Record
capacities, other channels, headers/trailers and imported provenance remain
exact. The private helper and browser processes are closed; no install or disc
export ran.

Package SHA256: `2d9eaec92f5076624af50f568c6494cd2f01b4b3b27b7f39becb60f2b3ad0aa7`.
Decoded ANM SHA256: `f79ee9a8e4bbf594b6d0fc6fc642f5bbbb747b89a046a2dc934e07c7d8bc9e11`.
Private evidence: `local-output/sdk-20260909/assigned-animation-glb-20261002/parent/`.
Gameplay verification remains deferred.

## Direct actor inspector entry for allocated clips - 2026-10-06

Select the actor and choose **Allocated initial animation → Edit assigned clip
through GLB**. The Animation channels component also exposes **Edit actor clip
through GLB** for supported imported associations. Both actions resolve the
actor's current assignment before opening an editor.

An allocated assignment opens **Edit retained clip in GLB** for its exact active
UUID. Prepare/download its GLB and retained binding, edit externally, choose the
files, then Review, Preview and Apply. Explicit captured-frame mapping supports
retained frame growth; Apply updates every referring initial assignment hash in
one normal command. Export and Review leave the assignment untouched. A stale
assignment, source, actor selection, model/hash mismatch or retired record rejects.

The direct entry reuses retained interchange, content validation and Build;
it does not make allocated records compatible with the imported v1/v2 binding
API. Imported channel authoring and its existing sidecars remain unchanged.
The full-editor private Town01 export check, wide/narrow captures and unchanged
history proof are in `local-output/sdk-20260909/actor-animation-glb-20261006/`.
Retail retained GLB roundtrip, frame growth, reference updates, Undo/Redo and
Save/Open passed separately. Gameplay playback and timing remain deferred.
