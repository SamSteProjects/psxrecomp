# SDK inspector property contract

## NPC animation frames at authored scene placement — 2026-10-05

**Inspect animation in scene** now targets the selected NPC draft when entered
through its donor animation Inspector. The donor remains the verified animation
source; the NPC becomes the explicit display target. Existing imported-actor
inspection retains its prior target selection. A dedicated adapter qualifies the
current scene source, unique authored entity, recorded donor/model and authored
X/Z placement before accepting an NPC target. Wrong source, model, donor, duplicate
entity or changed placement rejects the inspection.

The existing isolated geometry workflow changes only the target's display geometry
key. Authored/source position, sampled elevation, display position and model-to-scene
transform remain intact. NPC selection and framing synchronize with the inspection;
the scene bar uses its authored name. Frame changes retain the same NPC geometry
instance. Restore returns the qualified Current scene. This is display-only pose
inspection, not animation assignment, runtime playback or gameplay acceptance.

Focused NPC Inspector Node checks pass source/target/placement rejection. Actual
private browser with shared authored channels and a different authored donor
appearance verifies exact frame vertices, unchanged donor/all other entities,
retained authored transform, NPC selection, frame advancement and restoration.
The 540px viewport is visually inspected with no page errors. Project document,
history and every project file byte remain unchanged. Evidence:
`local-output/sdk-20260909/npc-animation-scene-target-20261005/proof.json` and
`npc-scene-540.png`. No Build, game launch, install or disc export occurred.

## NPC animation Inspector matches shared authored preview — 2026-10-05

The NPC animation button previously opened the imported donor clip even when the
Authored viewport showed shared authored animation channels. It now uses a
qualified SDK draft model reference and the current NPC pose kind: imported pose
opens the retail donor clip; authored pose opens shared authored channels. Labels
identify the representation. Unsupported/missing poses have no fallback action;
pending refresh, busy state and detached scene proposals cannot arm navigation.
The click rechecks source context and binding before opening the model dialog.

The retail donor model and clip owner remain explicit. The donor's authored
appearance is separate. `ModelRenderer.asset_id` already retained the retail
model; inspection corrected the initial suspected wrong-model diagnosis. This
change fixes the animation representation mismatch and strengthens binding checks,
without claiming an NPC runtime animation identity or an established idle stance.

Focused NPC Inspector and Asset Inspector Node checks pass source/pose coherence,
imported/authored channel choice, unknowns and mismatched donor/model rejection.
Actual private browser uses a verified donor appearance override (0105 to 0092)
and a native shared channel edit in `animation://town01/scene-anm/0012`. It opens
model 0105 with the correct donor owner and authored representation; its first
frame differs from the retail response. The 540px dialog passes with no page errors.
Project document, history and all file bytes remain unchanged during inspection.
Evidence: `local-output/sdk-20260909/npc-donor-animation-binding-20261005/proof.json`.
No Build, game launch, install or disc export occurred. Gameplay stays deferred.

## NPC recorded donor-model inspection — 2026-10-05

Authored NPC records and central project inventory entries now expose the SDK's
existing `draft_initial_model_assignment` reference. It retains source draft/name,
owning scene, model asset ID, retail donor ID and `runtime_binding=not_asserted`.
Unresolved donor model references remain null. The draft assignment uses the retail
donor independently of that donor's authored appearance.

NPC Asset Details shows **Recorded donor model** as a read-only SDK reference and
provides **Inspect recorded donor model** when model preview capability and a
coherent assignment are present. The adapter qualifies source/name/scene/donor,
assignment kind and layer before registering navigation; the editor checks the
current SDK reference again before opening the imported model view. The project
inventory adapter also rejects inconsistent model bindings. There is no runtime
residency/pose claim or property-writing action.

Validation: 22 focused Python Inspector/inventory cases pass, including retail
donor separation and explicit unknowns. Asset Inspector and project inventory Node
checks pass binding, malformed-reference, capability and unresolved-action checks.
Actual private browser matches SDK fields in active/project scopes and opens the
exact recorded model response; 540px layout passes, with no page errors. Document,
Undo/Redo and all project file bytes remain unchanged. Evidence:
`local-output/sdk-20260909/npc-donor-model-navigation-20261005/proof.json`.
No Build, game launch, install or disc export was performed. Gameplay stays deferred.

## Authored NPC Asset Details — 2026-10-05

NPC draft cards in active-scene and project scopes now use the SDK-owned
`AssetNpcDraft` descriptor. It presents the authored identity, name, project scene,
retail donor binding and authored X/Z coordinates with Project/Authored state
badges. Imported actor cards retain their existing descriptor. The separate
`authored_asset_inspectors` mapping preserves imported asset contracts.

The adapter rejects inconsistent draft identities, scene/name/donor records and
invalid native-grid coordinates before mounting the descriptor. Its only registered
action, **Select NPC draft**, uses existing scene navigation and opens the draft
Inspector. This exposes current SDK authored records; it does not add imported
Asset Database memberships or establish runtime spawning/visibility.

Validation: twelve Python Inspector schema cases and the expanded Node asset
Inspector checks pass. Actual private browser checks match every SDK property in
both scopes, select the correct NPC Inspector and pass at 540px with no page errors.
Project document, Undo/Redo and all project file bytes remain unchanged. Evidence:
`local-output/sdk-20260909/npc-draft-asset-inspector-20261005/proof.json` and
`asset-540.png`. No Build, game launch, install or disc export was performed;
manual gameplay verification remains deferred.

The shared asset Inspector also covers transition resources through
`AssetTransition`: source script/PC, named destination, static effective arrival
and reachability, with a capability-guarded source tool action. No direct property
write is exposed. Source trigger positions stay unknown. See
[transition asset workflow](legaia-transition-assets.md).

Project state exposes `inspector_schema` with version
`legaia.inspector-schema.v1`. The SDK owns component/property labels, paths,
layer order, value types, authoring bounds, Build constraints and unknown states.
Definitions are newly allocated per response and never modify imported or
project-authored data. Current definitions cover Transform, ModelRenderer, Animation, ActorAppearance,
RuntimeCorrelation and RetailMetadata. Layered reference properties retain retail,
authored and effective values; fallback paths handle missing status/source fields
without inventing values. Evidence details come from SDK paths. Specialized donor,
scripts and asset tools retain their existing
validated adapters; this is an incremental migration.

The editor's `component-inspector.js` renders layered numeric properties and
read-only properties from this metadata. Unknown/unregistered components display
escaped SDK details without editable controls. Unknown values use a dash, never
an invented zero. Imported, authored and effective values remain distinct.

The Transform command adapter permits only X/Y/Z `set_transform` and
`clear_transform`. It rejects unknown properties, nonfinite/out-of-bounds values
and unexpected command identifiers. SDK metadata is not authority to issue
arbitrary commands or RAM writes. Existing ProjectService validation, Undo/Redo,
dirty state, Save/Open and Build validation remain authoritative. Controls also
check Edit mode, busy state, selection and source context.

Authoring accepts finite values between-32767 and32767; this is separate from
representable retail X/Z placements on the64-unit grid64–16384. Retail Y remains
unresolved. Authored Y remains a project-only preview value and must be cleared
before Build. Tooltips and SDK Build issues preserve those distinctions.

## Verification — 2026-09-30

Nine focused Python tests passed, including the schema contract and existing
project workflows. Node checks cover value layers, unknown values, read-only
mode, escaping, bounded commands, malformed command metadata and read-only
fallbacks. Retail browser checks passed for SDK-derived controls, X edit/Undo,
project-only Y Build diagnostics and zero page errors. Retail appearance layers,
Clear/Undo, explicit unconfirmed runtime binding and provenance details passed;
screenshot inspected. Private evidence:
`local-output/sdk-20260909/component-inspector-20260930/`.
This feature postdates the441-test checkpoint. No game launched.


## Registered tool actions

SDK component definitions now describe six actor tools: choose/clear/preview
appearance, inspect model, inspect script/dialogue and inspect NPC candidate.
Action descriptors contain label, required capability, optional component-value
condition and Edit requirement. The editor renders only actions with an explicit
registered handler and a matching current capability. Unknown IDs are omitted.
The registered handler can require Edit even if metadata omits that requirement.
Labels and IDs are escaped; metadata supplies no executable code or command body.

Before dispatch, the registry checks busy state, source/selection context, Edit
requirements and handler-specific eligibility. Donor editing still uses the
source-verified donor forms and normal validated commands; script inspection still
uses the bounded decoder. Tool forms and animation/template/asset actions have
not all migrated. This registry does not add runtime writes or new serializer
support.

Node action checks passed for unknown IDs, capability/value conditions, escaped
labels, stricter handler Edit requirements and blocked busy/stale/ineligible
calls. Nine focused Python tests passed. Retail registered donor Clear/Undo and
source-script opening through a fully loaded decoded report passed. Private
`registered-actions-browser.json` shares the existing inspector evidence folder.
No game launched; the441-test integrated checkpoint predates this work.

The later integrated offline checkpoint on source `3c8d8f46` passed457 Python
tests with no skips, all12 Node checks and10 module syntax checks. See the
[current SDK status](SDK_STATUS.md) for exact source/command/log evidence.
Feature-specific browser/disk/package checks above remain separate from deferred
runtime and gameplay acceptance.

## Animation and preset action migration — 2026-09-30

The SDK now declares four additional registered tools. Animation's supported
imported association gates **Preview imported scene animation** and **Author
animation channels**; the latter additionally requires the explicit authoring
capability and Edit mode. ModelRenderer's **Preview reference animation** requires
a supported reference clip, kept separate from the imported placement animation.
**Open actor templates** uses the ActorPresets tool-group descriptor and the
existing preset library. ActorPresets is an inspector tool group, not an invented
retail or persisted entity component.

Reference support and the first supported clip ID are derived into detached
editor state from the imported asset catalog. Source preview/authoring still
verifies actual data through existing services. No metadata can supply code,
commands, runtime writes or permission to edit unknown structures. Dispatch uses
the existing source/selection/busy guards and registered Edit requirement. The
four old bespoke button creation/callback paths were removed. Numeric animation
forms, template library forms and asset tools still retain their validated
specialized adapters; the full inspector migration remains incomplete.

Eight focused Python/HTTP checks passed, including schema capability/condition
contracts and unchanged imported state. Node checks separate unsupported source
eligibility, readonly preview and Edit-only authoring. Retail-source browser
checked unsupported actors and busy disabling, opened the loaded channel form,
imported scene preview, idle reference preview and preset library through
registered buttons, and submitted zero authoring commands. Components were
unchanged; zero page errors. Final action-section screenshot inspected. Private
evidence: `local-output/sdk-20260909/inspector-animation-actions-20260930/`.
This postdates the457-test integrated checkpoint. No game/runtime launched.

## Asset catalog inspector migration — 2026-10-01

`asset_inspectors` maps eight catalog record types to SDK-owned inspector
contracts. AssetModel, AssetTexture, AssetAnimation, AssetScript, AssetDialogue,
AssetCollision, AssetTrigger and AssetRegion are tool groups for existing catalog
records. They are not retail entity components and are not persisted as such.
Their stable ID, type and source properties use the common read-only renderer.
An explicit asset-type registry whitelists five tool handlers. Unknown IDs,
wrong-type handlers and missing capabilities produce no action. Metadata supplies
no command body or executable code.

The asset browser's Details button opens a consistent inspector; its primary
card retains the direct workspace shortcut. Registered actions open the existing
source-verified model, texture, animation binding, script/dialogue or field-map
tool. Imported and authored source/details remain separate; duplicate authored
opening controls for migrated types are removed. Generic source details remain
available for unmigrated types. Source/catalog/schema/capability snapshots,
closed-dialog and busy guards prevent dispatch through an obsolete inspector.
Cross-scene authored navigation and tool-specific edit checks remain in existing
adapters. This does not add new serializers or writable runtime properties.

**SDK asset inspector tools (2026-10-01):** Asset Details now uses the
same SDK property/action contract as actor inspectors for eight catalog types:
models, textures, animations, scripts, dialogue, collision, triggers and regions.
SDK metadata supplies labels, read-only stable identity/source properties and
capability-bound tools; explicit type-specific handlers open the existing
verified workspaces. Details is now a consistent entry point, while asset-card
shortcuts remain. Changed source/catalog record/schema/capability, busy state and
closed dialogs block dispatch. Duplicate authored-open buttons are removed for
these types; authored details and source provenance remain separate. These are
inspector tool groups, not invented or persisted entity components. Eleven
focused Python checks, all 17 Node checks and 19 editor syntax checks passed.
Retail browser opened all eight Details panels through actual browser buttons,
loaded model/texture previews and opened the resource tools; busy/closed guards,
unchanged actors, zero author commands and zero page errors passed. Screenshot
inspected. Evidence: `local-output/sdk-20260909/asset-inspector-20261001/`.
This postdates the integrated 463-test checkpoint. Specialized editing forms,
other asset types, runtime identity and gameplay still need further work.
No game launched.

The subsequent integrated offline checkpoint on source `d948b2a0` passed
469 Python tests in176.301s with no skips,17Node checks and19editor module syntax
checks. It includes the asset inspector migration; browser workflow evidence
above remains separate from native runtime and gameplay acceptance.


## Catalog navigation inspectors — 2026-10-01

**Asset navigation inspectors (2026-10-01):** Actors, imported scenes,
actor presets and world-map landmarks now use the shared SDK read-only property
and registered-action contract, bringing supported catalog inspector types to12.
Navigation retains original source and authored provenance; landmarks expose
menu coordinates and discovery indices without claiming live state or gameplay
reachability. Source/catalog/schema/capability, busy and closed guards apply.
Fixed bare `scene://` searches being misread as `scene:` filters; explicit field
filters remain supported. Eleven focused Python checks, all19 Node test files
and21 editor syntax checks passed. Retail browser verified all four new panels,
actor selection, cross-scene navigation, preset library and landmark menu/source
catalog navigation, zero author commands/errors and unchanged authored state.
Screenshot inspected. Private evidence:
`local-output/sdk-20260909/navigation-inspectors-20261001/`.
No game launched. These checks postdate the integrated469 checkpoint; gameplay
and the full SDK objective remain incomplete.

Actor, scene and preset actions use the existing selection, scene and library
adapters. The world-map inspector has two explicitly registered actions:
landmark menu inspection and, when a destination source label exists, source
catalog inspection. Metadata contains no executable commands. Missing capability
or unknown action/type suppresses controls; changed record or contract snapshots
withdraw navigation. The previous bespoke landmark properties/buttons and
redundant authored-open buttons for these types are removed. Card shortcuts
remain. Specialized edit forms, full project settings and live actor identity
are still separate work; this does not add runtime writes or serializers.


## Project settings

**Project settings inspector (2026-10-01):** Settings now uses SDK
property/action metadata for name, folder, retail source identity, scene count,
active scene and mode. Source/path values remain read-only. A validated rename
command supports dirty tracking, one Undo/Redo, Save/Open, no-op and stale-name
rejection without modifying imported content or authored assets. Browser proved
one quoted Unicode rename, persistence/history, stale-form withdrawal and zero
page errors; screenshot inspected and baseline restored. Independent reopen
retained four drafts and normal no-draft builds preserved every game-data
payload. The Unicode probe exposed invalid surrogate escapes in package TOML;
manifest names now emit literal UTF-8 with valid escaping. Fourteen focused
Python checks, all21 Node files and23 syntax checks passed. No game launched;
checks postdate integrated475. See [Project settings](legaia-project-settings.md).

The ProjectSettings contract defines read-only source/project properties and a
registered Edit-only rename action. The bounded name adapter rejects arbitrary
command metadata; ProjectService owns history and stale review validation.
Project creation/opening and runtime launch configuration retain their existing
workspaces.

## Property-state presentation

`inspector_schema.property_states` is a detached catalog of labels and explanatory notes.
Registered properties declare their state; layered references declare the state of each
layer, retaining a more precise authored workflow when supplied. Transform uses explicit
Imported/Authored/Effective column states, plus separate full-width Retail Y: Unresolved
and Build Y: Unsupported labels. The shared component and asset renderer displays these
states without changing values, commands, actions or reference-navigation names.

Labels identify a property's evidence/ownership category. An empty Authored value still
inherits; a Live observed category does not establish a sample, freshness or confirmed
actor identity. Read the displayed value/status and evidence together. False evidence
status remains false; unresolved values never become zero. Unsupported height remains
project-only and must be cleared before Build. Unknown/malformed catalog entries show
Unclassified and do not grant authoring. Legacy schema fixtures without the additive
catalog retain their previous display. Catalog text is escaped and bounded.

Nine focused Python contract tests, component/reference Node checks and a real retail
browser passed. Actor and asset navigation, declared labels/notes, coordinate values,
540px layout and collapsed-component keyboard behavior preserved document/history,
scene/selection and saved bytes. No authoring, Save, Build or Run requests occurred.
The first screenshots exposed axis-column label wrapping; full-width state rows fixed
it. Private proof/screenshots:
`local-output/sdk-20260909/inspector-property-states-20261005/`.
This presentation milestone does not complete specialized-editor migration or live parity.

## Scenery snapshot components

Selected SDK environment instances use four read-only descriptors:
`EnvironmentPlacement`, `EnvironmentRetailTransform`,
`EnvironmentPreviewTransform` and `EnvironmentMetadata`. The browser passes the
SDK preview instance directly to the shared property/details renderer. It does
not decode retail bytes or synthesize transform values for this panel.

Retail coordinate/angle paths point into `source_record.imported_transform`;
Current paths point into `effective_transform`. Both have separate X/Y/Z position
and rotation rows; 4096 PSX angle units equal a turn. Current means the displayed
Retail/Authored preview snapshot. If refresh is pending, the panel explicitly
labels the previous snapshot. Missing values use a dash and never inherit a retail
value into a missing Current field. These are native source/preview coordinates;
they do not establish runtime placement or visibility.

Source metadata retains the imported MAP hash, placement record index, grid byte
offset and complete decoder source/evidence in expandable sections. Coordinate
spaces remain those of the source decoder. Frame object and the specialized
shared/individual transform forms remain available with their existing validation,
commands, Undo/Redo, Save/Open and Build constraints. These descriptors contain
no authoring or action commands; the snapshot renderer rejects authoring metadata.

## NPC draft snapshot contracts — 2026-10-05

NPC Inspector display now uses three read-only SDK component definitions:

- `NpcDraftIdentity`: project identity/name/scene, authored retail donor binding,
  and donor retail metadata details. Donor source is separate from this draft.
- `NpcDraftTransform`: authored X/Z, owned by supported project commands on the
  retail64-unit placement grid. No authored Y is inferred or offered.
- `NpcDraftPreview`: source snapshot X/Z, unresolved placement Y, derived sampled
  elevation/status, SDK model/pose/geometry metadata and evidence details.

`npc-draft-inspector.js` renders these through the shared property/details renderer.
It rejects authoring definitions for snapshot sections; specialized adapters retain
existing command, bounds, Undo/Redo and persistence ownership. Schema paths have
no fallback from preview to authored/donor values. Missing fields remain unknown.

The root editor supplies explicit preview context. A pending source refresh shows
a stale warning. A detached viewport proposal retains the Inspector's source
snapshot and labels that distinction; it does not substitute proposed coordinates.
Retail representation contains no draft preview, so snapshot fields are unavailable;
Authored representation restores the qualified snapshot. Neither derived elevation
nor sampled animation pose implies runtime placement, playback, spawning or collision.

Eleven focused Python schema cases and NPC/environment Node rendering checks pass.
Actual private browser matches all schema property values, verifies height separation,
retained authoring controls, controlled pending/proposal labels and Retail/Authored
switches. The540px Inspector is inspected. All project/history/files remain unchanged,
with no authoring, Save, Build or game. Evidence:
`local-output/sdk-20260909/npc-draft-inspector-schema-20261005/proof.json`.

## Shared Component Section Renderer — 2026-10-09

`renderComponentSection` in `component-inspector.js` composes registered SDK component headings/units, property layers/state badges, capability-qualified actions and evidence details into one escaped section with an explicit component identity. Actor Transform, retained assignment, presets, runtime observation, Retail metadata, dialogue and generic registered components use it. All four environment snapshot sections and the controller owner Inspector use the same renderer. Existing specialized appearance, model and animation adapters remain partial migration work.

Action Edit eligibility (`editable`) and numeric property editing (`propertyEditable`) are separate. Property editing defaults off and requires both options; Transform opts in through its existing bounded command adapter. This migration adds no writable component or runtime capability. Unregistered components retain escaped read-only fallback details. Registered action dispatch retains current-selection/source, busy, capability/condition and Edit guards.

Render options permit only bounded data attributes and h3/h4 headings. Optional section decoration is a local function over frozen rendered property/action/detail strings; SDK JSON metadata cannot supply executable callbacks. This preserves Transform Build warnings, runtime candidate summaries and environment pending-source warnings/framing controls without duplicating the shared section pipeline.

Offline qualification: thirteen Python schema tests, five focused Node suites and four JavaScript syntax checks passed. Actual private Town01 actor filtering, collapse/expand, registered Transform input eligibility, allocated assignment and Retail evidence display passed. Controller BGM asset component evidence and registered source-editor navigation passed; all thirteen supported controller projection families retain existing unit coverage. Environment tests retained exact Retail/Current values, source-qualified authoring/framing controls, pending-preview warnings, authored/retail switches and renderer matrices. Desktop, 400px actor/controller and 540px environment layouts were inspected. Project/imports/history/files remained exact; no authoring, Save, Build, game or runtime attachment ran. Initial controller browser harness failures (modal occlusion and missing narrow Inspector-panel selection) are preserved separately from the successful checks. Evidence: `local-output/sdk-20260909/shared-component-sections-20261009/`. Gameplay remains deferred and the full SDK goal active.
## Registered Actor and NPC Section Migration — 2026-10-09

All registered actor component sections now use `renderComponentSection`, including the remaining ActorAppearance, ActorAnimation, ModelRenderer and Animation paths. The renderer retains the appearance styling through bounded local class tokens; invalid, duplicate, oversized or injected class names refuse. Appearance evidence details, ModelRenderer units and placement-marker notes are supplied by SDK metadata. Local decoration preserves the existing authored clip witness and source-support note. Model/animation actions retain their registered handlers, source qualification and Edit/capability guards.

NPC draft Identity, authored Transform, optional ScriptBinding and Preview snapshot sections use the same renderer. Their explicit read-only snapshot checks remain, alongside independent script-action mounting and specialized donor/placement authoring adapters. Pending/unavailable/proposal snapshots do not substitute donor, authored or Proposed coordinates for missing preview values. No new writable component or runtime binding is introduced.

Fourteen Python schema tests, six focused Node suites and three editor syntax checks passed, covering metadata-only evidence/notes, safe local styling, source/reference/action guards, NPC script ownership, snapshot separation and existing environment/controller behavior. Actual Town01 actor sections retain appearance evidence, model reference units, filtering/collapse controls and numeric Transform eligibility. Registered model inspection and source animation preview opened and closed with empty error fields. NPC browser checks matched source/authored/preview values and retained authoring controls through pending-source, detached proposal and Retail/Authored switches. Desktop/400px actor and 540px NPC captures inspected. Project/imports/history/files stayed exact, with no authoring, Save, Build, game or runtime attachment. The early NPC readiness-probe race is preserved separately from the successful proof. An older NPC script-binding fixture omitted the already-supported animation-operand family; it now checks the complete eleven-family count and fifteen-action contract, including missing-family refusal. Evidence: `local-output/sdk-20260909/registered-inspector-migration-20261009/`. Specialized command adapters and broader asset/runtime work remain separate SDK tasks; gameplay remains deferred and the full goal active.