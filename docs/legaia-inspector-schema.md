# SDK inspector property contract

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
