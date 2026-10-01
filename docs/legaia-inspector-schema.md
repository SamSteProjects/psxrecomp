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
