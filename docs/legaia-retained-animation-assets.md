# Retained animation assets

Refresh scene resources now registers saved retained clips in the Asset Database.
They appear in Animations and Authored assets, with an Authored badge and the stable
`animation://<scene>/authored-record/<UUID>` identity. Project resource discovery
includes their source-scene membership too. No extracted animation bytes are
stored in the metadata catalog or committed with this feature.

Open a retained asset to inspect its active/retired status, frame/channel counts,
authored initial-assignment count and source witnesses. Retired clips remain
inspectable; they are absent from the generated native bank. Inspect captured
model opens the recorded model asset. Select capture actor navigates to the actor
that supplied the saved capture. Neither action changes the animation assignment.

Preview retained clip verifies the current project source and reconstructs the
saved native record using the existing retained-pose decoder. It opens the normal
model viewer with the saved frames and Current model geometry. Preview works for
assigned, unassigned and retired clips without applying edits or reactivating
anything. Timing, looping, live playback and runtime assignment remain unresolved.

Asset Details → Inspect recorded references supports navigation to registered
retained clips. Each clip has an authored **retained model capture** relationship,
qualified by ledger/record/original donor hashes, captured model/channel owners,
counts and active status. This source relationship assigns no native slot. An
active authored initial assignment separately retains its existing verified
native selector/bank relationship and actor edge. These represent distinct
provenance layers. Unavailable scene resource catalogs remain explicitly partial.

Discovery and preview are readonly in Edit and observation contexts. A separate
verification view satisfies the existing saved-record decoder's Edit prerequisite;
it does not change the original mode. Exact asset identity and current source key
qualify preview requests. Changed source, wrong model/record, malformed metadata
or extra HTTP fields reject. Closing a pending inspector aborts its request.

## Verification - 2026-10-05

Validation: 42 focused/neighboring Python checks, four JavaScript workflow/contract
suites and three syntax checks passed. Native HTTP discovery, actor/clip/model
references, all three clip previews, Project membership, malformed/stale requests
and readonly observation mode passed. The actual browser verified animation/authored
categories, all three inspectors and model viewers, captured-model navigation,
actor reference -> registered clip metadata navigation and stale-source rejection.
Complete document/history/files/mode/scene were unchanged. Zero page errors or
authoring/Build/Save/game requests; screenshots inspected. Private evidence:
`local-output/sdk-20260909/retained-assets-20261005/proof.json`. Initial browser
harness assumptions about responsive-only tabs, total authored counts and collapsed
provenance text were corrected; prior attempts are preserved. No game launched.

## Direct content editing

In Edit mode, Edit retained content opens the existing frame/channel editor directly
from the asset. It does not select its capture actor. The clip's project/scene/source
context owns this workflow; changing an unrelated actor selection does not dispose
it. The actor-library route retains its existing actor-selection lifetime.

Change captured frame mapping or supported native channel axes, then Review. Preview
reviewed content opens the ordinary model viewer as Proposed retained content, not
applied; closing it returns to the reviewed editor. Apply uses the existing atomic
command and updates authored initial assignment witnesses with the retained record.
The stable clip identity persists. A retired clip remains retired after an edit.

Successful Apply schedules a source-qualified resource refresh after command busy
ownership releases. Inspect the same asset to see its new hash/status. Save project
to persist; Undo/Redo remain normal project commands. Source changes, Live mode and
missing animation authoring capability prevent direct editing. Review/options enforce
existing format and revision budgets; these controls add no retargeting or timing
semantics. Gameplay verification remains separate.

Verification: 6 retail-enabled Python tests, 2 Node checks and 2 JavaScript syntax
checks passed. The actual headless editor edited both assigned and retired assets
through Review, proposed-pose Preview and Apply; actor selection and retail imports
were preserved, with exactly two atomic commands. Undo/Redo and Save/Open round trips
passed. The normal private Build passed native bank, initial assignment and relocation
readback; package ZIP integrity and SHA-256 matched its receipt. No game was launched
or installed. Evidence: `local-output/sdk-20260909/retained-asset-edit-20261005/proof.json`.

## Direct GLB interchange

Open the retained asset and choose Edit retained GLB. Prepare retained GLB export at
an explicit FPS, then download both GLB and binding JSON. Edit its supported rigid
channels externally. Select the edited GLB and its original binding, choose the
captured output-frame mapping, then Review GLB content. Preview reviewed GLB content
opens the proposed pose without applying it; closing the viewer returns to Review.
Apply reviewed GLB content performs the existing atomic content command. Refresh is
automatic after a successful asset-based Apply; save the project to persist it.

The asset editor does not select the capture actor and remains independent of
unrelated actor selection. Project, scene, mode and source changes invalidate it.
Busy and stale asset Inspectors cannot open a replacement workflow. Bindings must
match the current saved capture; file/mesh changes do not imply model replacement.
Retired clip imports preserve retirement. Runtime playback/timing and physical game
verification remain separate acceptance gates.

Verification: 3 retail-enabled Python tests, 2 Node workflow checks and 2 JavaScript
syntax checks passed. The actual headless editor completed export and byte-verified
GLB/binding downloads, external channel replacement, Review, proposed-pose Preview
and exactly two Apply commands for assigned and retired assets. Capture actor
selection and retail imports were unchanged; assigned reference hashes updated and
retirement persisted. Undo/Redo, Save/Open and normal private Build passed, including
native bank/initial-assignment/relocation readback and package ZIP/SHA verification.
Both proposed screenshots were inspected. No game was launched or installed.
Evidence: `local-output/sdk-20260909/retained-asset-glb-20261005/proof.json`.

## Direct retained lifecycle

Choose Manage retained lifecycle from an authored animation asset. The Inspector
loads and verifies only that clip against the fresh saved library; it offers Preview,
Review retirement/restoration and Apply reviewed change. Preview returns to the same
Inspector. Review preserves project state. Apply changes the authored bank membership,
preserving the stable UUID and captured bytes; refreshed asset status follows Apply.
Save project to persist. The asset view can also open its direct content/GLB editor.

This view does not assign an actor or clear initial references. If retirement is
blocked because the clip is still assigned, clear the intended actor's authored initial
assignment through its Inspector, then reopen the asset and Review again. It never
silently clears references. Actor selection is independent of this asset workflow.
Project, scene, mode, source and busy guards remain active, and a mismatched fetched
capture cannot enable lifecycle Apply. Undo/Redo, Save/Open and normal private Build
are supported; runtime playback and game appearance remain separately unverified.

Verification: 3 retail-enabled Python tests, 2 Node workflow checks and 3 JavaScript
syntax checks passed. The actual headless editor verified exact single-asset scope,
blocked assigned retirement, readonly saved-pose Preview/Return and lifecycle Review,
then retired an unassigned clip and restored a retired clip through exactly two Apply
commands. Actor selection, retail imports, every captured record hash and the complete
initial-assignment component were unchanged; asset status refreshed automatically.
Undo/Redo and Save/Open passed. Normal private Build passed native bank, initial header
and relocation readback plus ZIP/SHA integrity checks. Restoration screenshot inspected.
No game launched or installed. Evidence:
`local-output/sdk-20260909/retained-asset-lifecycle-20261005/proof.json`.

## Assign to the selected actor

Select an imported actor in the Hierarchy or viewport, then open an active retained
animation asset. Choose Assign to selected actor. Verify the target actor ID in the
assignment dialog before Review initial assignment. A different capture actor is
allowed only when the native service proves the exact captured model/channel binding;
unsupported retargeting remains blocked. This action does not select the capture actor.

Preview reviewed assignment shows the target's proposed initial pose without applying
it. Close the viewer to return to Review, then Apply reviewed change. The retained
UUID/capture/ledger stay unchanged while the selected target gets its authored initial
assignment. Asset references refresh automatically. Save project to persist, or use
Undo/Redo. Clear is available through the actor's existing Inspector workflow.

Retired clips have no assignment action. Missing or non-imported actor selection,
Live mode, missing capability and stale source block entry. The assignment view is
bound to its explicit target selection and invalidates if that target changes. It
exposes no retirement/restoration, Clear, content editing or GLB replacement actions.
Scripts may later select other clips; runtime timing, looping and gameplay suitability
remain unverified. Normal Build re-resolves the current native selector.

Verification: 4 retail-enabled Python tests, 3 Node workflow checks and 3 JavaScript
syntax checks passed. The actual headless editor hid retired assignment, rejected an
incompatible model, then reviewed/previewed/applied the captured actor-0011 clip to
selected actor0012 through one exact command. The target pose screenshot was inspected;
asset assignment metadata refreshed. Imports, ledger/capture hashes and capture actor
overrides were unchanged. Undo/Redo and Save/Open passed. A second readonly browser
check changed target selection and verified disposal with no command or document,
history or file changes. Normal private Build passed native bank/initial-header/
relocation readback plus ZIP/SHA checks. No game launched or installed. Evidence:
`local-output/sdk-20260909/retained-asset-assignment-20261005/proof.json`.
