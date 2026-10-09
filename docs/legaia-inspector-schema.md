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
## Asset Section Rendering and Action Dispatch — 2026-10-09

Asset Details now uses the shared SDK component section renderer for all sixteen
registered asset categories and the separately qualified authored NPC draft.
Metadata owns headings, units, property layers and evidence details; the typed
local action registry retains source, capability and donor qualification. Asset
properties remain read only, and unsupported types keep their existing fallback.

The shared action handler now refuses disabled buttons and enforces the metadata
Edit requirement as well as the local registry requirement. Direct handler calls
cannot bypass those checks; existing freshness, busy and can-run checks remain.

Seven focused Node suites and two JavaScript syntax checks passed. Actual private
Town01 Asset Details checks covered ten categories with exact SDK property values,
plus authored NPC selection in Scene and Project scopes. Disabled action calls
issued no authoring requests. Project documents, imports, history and file bytes
remained unchanged. Desktop/400px model and 540px NPC layouts were inspected.
Evidence is retained under
`local-output/sdk-20260909/asset-section-renderer-20261009/`.
The harness corrections and failed attempts remain alongside successful evidence:
resource loading requires a catalog query, headings now include metadata units,
and one NPC startup attempt failed to fetch the main module before a successful
retry returned HTTP 200. No game, runtime attachment, native recomp compilation,
Build, installation or disc export occurred. Gameplay remains unverified and the
full SDK goal remains active.
## Project Settings Scene Navigation — 2026-10-09

Project Settings now uses the shared SDK section renderer for its heading,
properties, state badges, notes and registered Rename action. The active scene
reference opens its exact Asset Database record through the existing central
reference resolver. Project folders and retail paths remain plain text; no path,
ID suffix or guest address is interpreted as a navigation target. The reference
is rendered only when the complete local navigation adapter is available.

Opening scene details closes Settings. Missing/ambiguous catalog references stay
in Settings with the existing reference error; changed settings/schema/capability,
busy state and closed dialogs refuse navigation. Rename retains its bounded
command, snapshot identity, form and Edit requirement. Navigation does not rename,
switch the scene, write game memory or grant authoring capability.

Three focused Node suites, two JS syntax checks and the two project metadata
Python tests passed. Actual private Town01 Settings-to-Scene Asset Details,
unapplied rename draft, stale/busy reference refusal and Edit-only rename guard
passed without authoring requests or page errors. Desktop and 400px layouts were
inspected. Project document, imports, history and every project file stayed exact.
Private evidence: `local-output/sdk-20260909/project-settings-scene-reference-20261009/`.
No Build, game, runtime attachment, native recomp compilation, install or disc
export occurred. Gameplay remains unverified; the full SDK goal remains active.
## Asset Property Reference Navigation — 2026-10-09

Asset Details and source-resource Inspector properties can now open exact SDK
asset/entity references through the shared catalog resolver. Rendering opts in
only when the complete local navigation adapter is registered. The asset's own
identity remains plain text through a bounded, validated reference-exclusion
option; other property values, types and state badges remain supplied by SDK
metadata. Paths, unknown strings and guest addresses do not become targets.

Asset Details retains the originating catalog lookup, including selected Project
source membership. Source-resource inspection uses the active catalog. Missing
or ambiguous targets report the current catalog limitation without parsing IDs,
changing scenes, assigning models, selecting actors or granting editing. Existing
source, busy and pending-discovery guards remain. Both references and registered
actions additionally require their mounted content to remain connected to its
host. Replacing a dialog/Inspector withdraws old callback eligibility, even when
its original record still exists unchanged in the catalog.

Seven focused Node suites and four JS syntax checks passed. Actual Town01
controller owning-scene navigation worked from Asset Details and source Inspector.
NPC scene, retail donor actor and recorded donor model links opened their exact
Asset Details; model navigation also passed in Project scope. Direct calls to
retained buttons from replaced content could neither rerender the current dialog
nor invoke their old action. Desktop and 400px layouts were inspected. No scene
switch, authoring, Save, Build or Run requests occurred; project document, imports,
history and every file stayed exact. Private evidence:
`local-output/sdk-20260909/asset-property-navigation-20261009/`.
The initial NPC harness matched a scene ID inside longer donor-ID text; its failed
attempt is retained, and the passing check uses exact reference attributes.
No game, runtime attachment, native recomp compilation, installation or disc
export occurred. Gameplay remains unverified; the full SDK goal stays active.
## Asset Details Back Trail — 2026-10-09

Following a metadata asset/entity reference now remembers its origin and exposes
Back in the destination Asset Details. The editor keeps at most sixteen origins,
each retaining its original catalog lookup, exact record snapshot and project/
scene/schema/capability context. Back re-resolves the original stable ID in that
catalog and requires one unchanged record. Missing, ambiguous or changed records,
and changed source contexts, refuse without consuming history. The source snapshot
is bounded to 2 MiB and its context key to 256 KiB. This is transient editor
navigation, separate from project Undo/Redo or authored commands.

Independent Asset Details openings and dialog close clear the trail. Reference
navigation preserves it; a successful Back removes one origin. Detached Back
buttons and busy state cannot navigate. Newly rendered details start at the top
so the Back control stays accessible. Existing typed property references,
source membership and action permissions remain unchanged.

Four focused Node suites, two JavaScript syntax checks and server AST validation
passed. Actual private Town01 NPC-to-model-to-Back and NPC-to-scene-to-Back restored
exact NPC property values. Project scope restored the authored NPC's membership
panel. Controlled stale-source/busy checks and calls to a detached Back button
could not navigate or consume the held origin; close cleared it. Fresh details
started at scroll zero. Desktop and 400px captures were visually inspected. Zero
page errors, scene-switch or authoring requests occurred. Project document,
imports, history and every project file byte remained unchanged. Private evidence:
`local-output/sdk-20260909/asset-details-back-trail-20261009/`.
No Build, game, runtime attachment, native recomp compilation, install or disc
export occurred. Gameplay remains unverified; the full SDK goal stays active.
## Actor Asset Model and Clip Bindings — 2026-10-09

Imported actor Asset Details now presents Retail initial model/animation,
authored appearance and imported-clip witnesses, appearance-default animation,
and Current initial model/animation as separate SDK properties. Exact references
use the existing catalog navigation and Back trail. Missing models and unresolved
local clips remain explicit. An absent imported-clip witness no longer claims
that the Current animation inherits appearance when a retained clip is assigned.
Read-only evidence details expose the existing appearance, animation and model
resolution snapshots; the original actor-selection action remains.

The scene entity and Project Asset Database now share a reusable SDK projection
of existing initial bindings. Project catalog actor records receive detached
component metadata without changing their imported source document, provenance
or source membership. This reuses existing appearance/witness/allocated-record
resolution; no new retail decoder, runtime binding or authoring path is introduced.
The editor consumes the descriptor through its existing shared renderer.

Thirty-five focused Python tests, two Node suites and four SDK AST checks passed.
A captured pre-extraction baseline matched all three binding components for all
52 Town01 actors exactly. Synthetic authored appearance checks retain distinct
Retail/Current models and initial clips, with detached Project catalog snapshots.
Actual actor Asset Details matched SDK values, opened separate Retail versus
allocated Current clip records and the Current model, returned through Back, and
retained Project membership. Scene/Project binding projections matched. Desktop
and 400px layouts were inspected; zero page errors or authoring/scene-switch
requests occurred, with unchanged project/imports/history/files. Private evidence:
`local-output/sdk-20260909/actor-asset-bindings-20261009/`.
An older NPC membership fixture used a forbidden newline name; committed HEAD
reproduced that failure. The fixture now uses a printable name and separately
checks rejection of controls. Validation was not relaxed. No Build, game, runtime
attachment, native recomp compilation, install or disc export occurred. Initial
binding metadata does not prove runtime residency, visibility, playback or script
compatibility. Gameplay remains unverified; the full SDK goal stays active.
## Animation Binding Asset Search — 2026-10-09

The Asset Browser now accepts `animation:` filters. They search recorded stable
animation identities in asset metadata, including separate Retail/Current actor
bindings, retained authored clips and Project source variants. A clip's own asset
identity is searchable too. Combine `type:actor animation:<clip-id>` to locate
actors with a recorded association; exclusions and quoted terms use the existing
bounded query parser. Unresolved numeric initial-animation fields are not turned
into invented clip identities. Searching does not select a different source
membership, change an actor or imply runtime playback.

Positive animation filters in All records trigger the existing source-qualified
resource discovery. Actor-only searches use the actor metadata already available;
negative-only and invalid filters do not request additional catalogs. The shared
search help documents the new field and its evidence limits. No binary format,
serializer, native Build or runtime transport changes were needed.

Two focused Node suites and three JS syntax checks passed. Actual muted editor
checks found the same Town01 actor by its distinct Retail and retained Current
clip in Active Scene and Project scopes; All records discovered the referenced
clip automatically. Exclusion, missing reference and invalid-filter behavior,
clip Asset Details/Back and Project source membership passed. Desktop and 400px
layouts were inspected. Zero page errors or authoring/Build/Run/scene requests
occurred; project/imports/history/file bytes were unchanged. Private evidence:
`local-output/sdk-20260909/animation-binding-search-20261009/`. Initial harness
failures used a nonexistent narrow-layout tab and omitted the Project catalog
readiness wait; corrected checks passed, with both diagnostic logs retained.
Gameplay association and playback remain unverified. The full SDK goal is active.

## Layered Hierarchy Asset Bindings — 2026-10-09

Hierarchy search now supports `model:` and `animation:` to find imported actors
by either recorded Retail or Current initial bindings. Layer-specific fields
`retail_model:`, `current_model:`, `retail_animation:` and `current_animation:`
keep those associations separate. Values come only from SDK ActorAppearance and
ActorAnimation components; numeric unresolved animation IDs are not converted to
invented clip identities. Current includes persistent authored assignments, not
live playback or later script-driven changes. NPC draft and resource bindings
are not inferred. Ordinary unqualified name search remains unchanged.

The same filtered actor records feed visible hierarchy rows and the existing
bounded Select matching actors workflow, preserving fresh-source/Edit/busy gates
and viewport group highlighting. Search help describes the layers and limits.
Saved Scene View validation supports the new fields and fixes an existing
mismatch that rejected the editor's `attached:` field on the SDK side. Saved
filters remain editor metadata and do not alter native authored input keys.

Three Node suites, two JS syntax checks, one SDK AST check and three focused
Python tests passed, including server/client grammar parity, metadata history,
Save/Open, Undo/Redo and unchanged native inputs. Actual Town01 checks compared
all matching IDs against SDK component values for Retail/Current models and
clips; distinct retained Current clip, combined filters, exclusions, empty and
invalid results, exact group selection and viewport highlighting passed. Desktop
and 400px layouts were inspected; narrow hierarchy rows remain accessible by
panel scrolling, and narrow group selection passed. No page errors or
command/Build/Run/Save/scene requests occurred; project/imports/history/file bytes
were unchanged. Private evidence:
`local-output/sdk-20260909/hierarchy-asset-bindings-20261009/`.
No game or runtime attachment was used. Runtime residency, initial assignment
behavior and playback remain unverified; the full SDK goal is active.

## Asset Binding Navigation and Usage — 2026-10-09

Model and animation Asset Details expose SDK-registered Find Retail actor bindings
and Find Current actor bindings actions. Navigation retains the selected Project
source membership through the existing verified asset resolver, then opens the
source scene hierarchy with a layer-qualified actor query. It does not implicitly
select or author actors. The narrow workspace reveals Hierarchy & assets; existing
Select matching actors remains available. Full model/animation URI filters now
match exact identities, while shorter filter text retains substring search.
Qualified type/layer, bounded identity and existing source/busy/mounted-action
checks prevent foreign, stale or detached navigation.

Visual verification exposed an older contradiction: a retained clip had a Current
actor assignment, but Used by said there were no initial users. Animation Used by
now replaces the active imported-actor donor/model join with explicit Retail and
Current SDK animation components. This also preserves Retail-only users when
Current points elsewhere. Other-scene and NPC witness rows retain their existing
evidence, detached from source data. Preview-choice construction is unchanged.
Usage callbacks now also require the original mounted Asset Details and fresh
resource snapshot, refusing callbacks retained from a closed/replaced panel.

Nineteen focused Python tests, four Node suites, four JS syntax checks and SDK
schema AST passed. Actual muted editor workflows compared exact matching IDs
against SDK components for both layers of model and animation resources, including
a retained clip with zero Retail users and one Current user. Active/Project actions,
source membership retention, narrow hierarchy handoff, busy/detached refusal,
correct imported/effective Used by labels and absence of detached selection
requests passed. Desktop and 400px layouts were inspected; zero page errors or
command/Build/Run/Save/scene requests occurred, with unchanged project/imports/
history/file bytes. Private evidence:
`local-output/sdk-20260909/asset-binding-hierarchy-navigation-20261009/`.
No game, runtime attachment or native Build was used. Initial bindings do not
prove runtime residency, script-selected use or playback; gameplay remains
unverified and the full SDK goal active.

## Retail and Current Animation Preview Choices — 2026-10-09

Scene animation resource choices now join explicit SDK ActorAnimation/ActorAppearance
layers to the selected clip's catalog actor/model witnesses. Retail choices keep
the original model and scene-header preview. Current authored animation choices
use the assigned initial-animation preview; appearance-only Current choices use
the existing appearance preview. Only identical unmodified choices are combined
as Retail + Current initial. Changed actors no longer appear as Current users of
their old clip merely because their model is unchanged. Retained records continue
to use their dedicated inspector and preview workflow. Missing pairings remain
unavailable; no model retargeting or runtime playback inference is introduced.

The bounded choice service returns detached actor identities and refuses ambiguous
or foreign actors. Dialog selection/preview callbacks require their original
mounted view, current resource identity and unchanged choice projection, and
refuse busy, stale or closed/replaced panels. Shared-field reference preview
callbacks now also require current source and original mounted dialog ownership.
Source decoder, native serializer and project authoring behavior are unchanged.

Two focused Node suites, two JS syntax checks and server AST passed. Actual muted
Town0b workflow used an existing authored assignment with distinct Retail/Current
clips. The original clip offered that actor as Retail-only; the assigned clip
exposed Current initial and requested the assigned preview endpoint. Complete
Retail frames matched the Retail source preview and complete Current frames
matched the verified donor-witness preview, with exact source clip/witness IDs.
Busy, stale and detached preview/selection refusal passed, including a detached
available shared-field reference button. Desktop/400px layouts were inspected;
zero page errors or authoring/Build/Run/Save/scene/selection requests occurred.
Project/imports/history/file bytes were unchanged. Private evidence:
`local-output/sdk-20260909/animation-resource-preview-bindings-20261009/`.
The initial harness used a nonexistent model close selector; its failure log is
retained, and the corrected full workflow passed. These are editor sampling and
routing checks, not gameplay timing/playback acceptance. No game, runtime attach
or native Build was used; the full SDK goal remains active.

## Project-Wide SDK Animation Usage — 2026-10-09

ProjectService now exposes `animation_references()` and a detached
`animation_references` state projection across all imported scenes. Each recorded
initial clip has stable actor/scene/clip identities, independent Retail/Current
flags, layer-qualified model identities and Current source metadata. Retained
assignments preserve their recorded IDs. NPC drafts reference the Retail initial
clip of their independent appearance witness, without inheriting the script
donor's authored assignments. Zero/unresolved/global-pool initial clip identities
remain absent under the existing SDK local-clip rule. These are derived project
bindings, not verified runtime residency or native allocation receipts.

The local initial-animation identity rule is shared with existing scene component
projection. Animation Asset Details Used by now consumes SDK references for both
active and inactive scenes. The editor donor/model inference and interim active
scene replacement helper are removed. Usage navigation recognizes NPC animation
references and retains source scene selection semantics. Its freshness snapshot
includes animation references, so a changed inactive-scene or draft assignment
also invalidates a retained callback. Native serializers and authoring commands
are unchanged.

Twenty focused Python checks passed, with one existing retail-disc-gated check
skipped because its environment input was absent. Two Node suites, two JS syntax
checks and three SDK AST checks passed. Focused checks cover appearance history,
Save/Open, Undo/Redo, inactive-scene independence, detached nested source metadata,
retained IDs, unresolved clips, NPC appearance/script donor separation and unchanged
native authored input keys. An in-memory integration fixture combined existing
saved Town01 and Town0b source evidence, assigned clip overrides and NPC draft
metadata without changing the original fixtures. Its 89 references across two
scenes matched every imported actor's SDK layer values. Actual muted browser
checks matched SDK usage rows for retained clips, NPC witnesses and inactive
Town0b Retail/Current assignments in Project scope. Changed usage callbacks were
refused; desktop/400px layouts were inspected. Zero page errors or command/Build/
Run/Save/scene/selection requests occurred; browser project/imports/history and
all original fixture files remained unchanged. Private evidence:
`local-output/sdk-20260909/project-animation-usage-20261009/`.
No game, runtime attachment or native Build was used. Gameplay remains unverified;
the full SDK goal stays active.


## Asset Usage Filters and Pages — 2026-10-09

Model and animation Asset Details share a usage browser over the existing SDK
reference projections. Retail and Current flags remain independent. Source-scene
selection and case-insensitive actor name, stable ID or source-scene search filter
the recorded rows without inferring runtime membership. Source order and exact
source identities are preserved. At most 64 rows render per page, with bounded
Previous/Next controls and a matching/total count. Filters reset the page; pages
clamp when results shrink. Empty results are explicit. Duplicate source identities
or missing layer metadata are refused rather than combined silently.

Navigation retains the existing actor/NPC and source-scene behavior. A removed
row cannot navigate after filtering or paging. Pending navigation locks controls
and rows, while busy, detached and stale source contexts refuse callbacks. Rows
passed to navigation are detached copies. No SDK serializers, authored overrides
or runtime behavior changed.

One focused Node suite covers filtering, explicit layer flags, source-scene and
ID/name searches, detached metadata, 64-row paging and malformed input refusal.
Two JS syntax checks and server AST passed. The actual muted editor workflow used
an in-memory two-scene fixture with 89 SDK animation references, checked model and
clip filters in Scene/Project catalogs, and preserved the source membership. A
separate synthetic 165-reference DOM fixture verified pagination and filtered,
pending, busy, stale and detached callback refusal; it does not establish that a
retail asset has more than 64 users. Desktop and 400px screenshots were inspected.
There were no page errors or command/Build/Run/Save/scene/selection requests.
Project/imports/history and original fixture files remained unchanged. Private
evidence: `local-output/sdk-20260909/asset-usage-browser-20261009/`.
No game, runtime attachment or native Build was used. Gameplay remains unverified;
the full SDK goal remains active.


## Reference Result Ownership — 2026-10-09

Relationship rows previously retained callable navigation handlers after their
filters or result rows were replaced. Reference target, exploration and instruction
callbacks now require their original accepted report, source scope/root, unchanged
display filters and a mounted row. Detached dialogs are ineligible. A delayed trace
module import also retains the original report generation and root.

Trace navigation retains its accepted report generation, mounted target and exact
current direction/depth/layer controls. Downloads require the same control binding.
Controls cannot invalidate a pending request through retained change callbacks;
responses are accepted only for their original selected controls. Reference responses
likewise retain selected scope/root, and report downloads require that ownership.
Recorded relationships and reverse-engineering interpretations are unchanged.

Four focused Node suites and two JS syntax checks passed. The instruction test now
covers filtered and detached row callbacks with a connected DOM fixture. Actual
muted Edge components with synthetic qualified metadata verified trace control
changes, reruns, busy/stale/detached/closed-pending refusal, filtered reference target
and exploration refusal, exact downloaded evidence and current navigation once.
There were zero page errors. Private evidence:
`local-output/sdk-20260909/reference-result-ownership-20261009/`.
This was a browser component fixture, not a retail SDK or gameplay acceptance run.
An initial fixture used an invalid depth stopping reason and assumed synchronous
close-event removal; those fixture expectations were corrected before the pass.
No project authoring, game, runtime attachment or native Build occurred. Gameplay
remains unverified and the full SDK goal remains active.


## Model and Texture Material Binding Inspector — 2026-10-09

Model and texture Asset Details now share a recorded material binding inspector.
It consumes the existing Project Asset References API and its strict decoder;
models show outgoing TIM matches, textures show incoming model-material matches.
The existing SDK static address evidence, source/current model hashes, native page
and CLUT fields, material index, UV bounds and source-scene provenance stay intact.
Retail decoded edges and separately decoded Current edges are distinct filters.
Missing Current matches do not imply inheritance or absence of users. No new
material association or reverse-engineering inference was introduced.

The inspector shows source catalog availability and at most 64 rows per page.
Each row opens the recorded counterpart in its qualified source scene; same-scene
navigation participates in the existing Asset Details Back trail. Unavailable
counterparts remain disabled. Source changes, filtered/replaced rows, busy or
pending navigation and disposed content refuse callbacks. Closing aborts pending
metadata requests. Project authoring and native serializers are unchanged.

Three focused Node suites, two JS syntax checks and server AST passed. Actual
muted editor checks used the saved authored Vell material/texture fixture and fresh
SDK graph qualification: all model Retail/Current and authored texture Current row
identities matched exact reports, filters preserved layers, an old filtered callback
was refused, and texture-to-model-to-Back navigation worked. Desktop and 400px
screenshots were inspected. Separate synthetic 165-edge browser component checks
covered 64-row paging, filtered/page replacement and pending/busy/stale/disposed
refusal; this does not claim a retail asset has 165 material links. Zero page errors
or command/Build/Run/Save/scene/selection requests occurred. Project/imports/history
and all saved fixture files stayed exact. Private evidence:
`local-output/sdk-20260909/asset-material-bindings-20261009/`.
The browser harness initially needed a guarded startup probe and a unique Inspector
selector; both were corrected before the final pass. No game, runtime attachment
or native Build occurred. Runtime residency, animated palette behavior and gameplay
remain unverified; the full SDK goal stays active.


## Asset Source Context Classification — 2026-10-09

The generic asset inspector previously declared its catalog display label `source`
as read-only Retail, including authored TIM slots and retained clip records. The
SDK descriptor now labels that field Source context and classifies it as Derived.
A shared note distinguishes the catalog label from actual Retail origin and authored
inputs in the recorded provenance. This corrects a misleading badge without
inferring a resource origin from its name or identity. Concrete source metadata,
Retail/authored binding fields, persistence and action capabilities are unchanged.

Sixteen Python inspector schema checks and two Node inspector suites passed. The
actual saved Vell editor workflow verified the authored texture source context has
one Derived badge and no Retail badge, with unchanged exact model/texture material
rows, filters and counterpart/Back navigation. The corrected 400px screenshot was
inspected. Existing desktop/400px and synthetic pagination/callback checks passed,
with zero page errors or authoring/scene/selection requests; project/imports/history
and saved fixture files remained exact. Private evidence reuses
`local-output/sdk-20260909/asset-material-bindings-20261009/` with an explicit
`source_context_derived_not_retail` browser assertion. No game, runtime attachment
or native Build occurred. Gameplay remains unverified; full SDK goal active.
