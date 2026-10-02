# Project transition references

Central transition assets now expose the same decoded instruction identities in
the Asset Browser and shared Inspector, with encoded/static arrival layers and
Active/Project asset references. Authored entry spans are freshly qualified before
annotation; scene annotations have a separate freshness key. See
[transition asset workflow](legaia-transition-assets.md).

Choose **Project transitions** in the Asset Database tool area to inspect decoded
scene-change references from all imported scenes. Scene transitions still limits
the view to the current scene. Discovery verifies retail source evidence, batches
disc access and does not refresh resources, change selection or author values.

Each row retains source scene, owner script, instruction offset, partition,
coverage, source provenance and encoded destination. Entry operands show retail
values and separate authored/effective values where overridden. Unknown names
remain unresolved; matching destination IDs merge scene nodes without collapsing
independent source instructions. An unavailable scene remains listed with its
reason. Project sources/authored state are checked again before returning data.

**Inspect source script** opens its imported source scene and the instruction in
the normal script inspector. **Open imported destination** is enabled only when
the destination already belongs to the project. Navigation uses ordinary scene
selection; it does not write an actor or transition component. Close aborts
pending discovery; stale context blocks retained row actions.

## Limits and evidence

The service accepts no client source bindings and is bounded to1–64 imported
scenes,16,384 references and16,448 nodes. Only supported decoded paths are
covered. Edges have reachability `not_evaluated`: no gameplay route, story flag
condition, complete exit inventory or runtime transition is inferred. Source
inspection uses existing bounded authoring rules separately.

Five focused Python tests passed. Retail HTTP/browser checks across town01 and
Dolk2 returned three references to map01 from180 scripts,88 partial and zero
unavailable scripts. Cross-scene source navigation, no authoring commands,
unchanged draft/override state, strict request rejection and zero page errors
passed. Screenshot inspected. Private evidence:
`local-output/sdk-20260909/project-transitions-20260930/`.
This feature postdates the441-test integrated checkpoint; no game was launched.

The later integrated offline checkpoint on source `3c8d8f46` passed457 Python
tests with no skips, all12 Node checks and10 module syntax checks. See the
[current SDK status](SDK_STATUS.md) for exact source/command/log evidence.
Feature-specific browser/disk/package checks above remain separate from deferred
runtime and gameplay acceptance.
