# SDK inspector property contract

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
