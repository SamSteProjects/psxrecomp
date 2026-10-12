# Shared Field TIM Authoring

In progress — 2026-10-11. The native source/replacement prerequisite is implemented and checked. Project/history/persistence, Current composition and fixed-span package delivery now pass focused checks. Shared source registration and the complete reviewed editor editing workflow remain unfinished.

## Native Source And Replacement Scope

`importer/field_texture_authoring.py::load_field_texture_authoring_context` freshly qualifies the pinned eight-member field-party bank at PROT874 section2. It uses the existing field texture parser, disc identity guard, TIM validator and bounded compression/readback mechanisms. Original IDs remain `texture://legaia/field-party/874/2/{slot}`. Full native source locators retain section/pack slot, decoded byte interval, compressed offset/consumption, disc hash and the pinned upload evidence.

The original model and animation sections are separate. Replacements keep every TIM header, indexed 4-bpp mode, dimensions, image/CLUT address and byte length exact. Existing palette/image payloads can change; unchanged TIMs emit no overlays. CLUT storage remains literal; field upload flattening is separate from TIM-local palette preview and must not be inferred from ordinary scene texture behavior.

This context permits only the original consumed compressed section span. Recompression uses the shared greedy/bounded-optimal path and exact independent decode checks. Rewrites that need more capacity reject. `build_patch` deliberately returns no scene-descriptor growth requests: the shared bank has a different container ownership model, and normal Build integration must qualify it explicitly. No scene upload catalog is silently expanded or substituted by this native prerequisite.

## Focused Evidence

All eight originals qualify and no-op without overlays. One existing CLUT word per TIM changes while image bytes and headers stay unchanged. Each rewrite independently matches the requested member and preserves every decoded sibling member, both other decoded sections and bytes before/after the compressed stream. A combined eight-member rewrite matches all replacements; changed decoded bytes are confined to the eight selected CLUT words. Header mutation and forced compressed-capacity overflow reject.

Six focused tests pass: the new shared-bank check and five existing scene texture-authoring checks. Private evidence: `local-output/sdk-20260909/field-equipment-20261011/shared-tim-proof.json`. Proprietary TIMs and overlay bytes remain private. No project mutation, package Build, compilation, installation, game, attachment or disc export ran.

## Remaining Workflow

Register shared sources in the project asset/browser services with an explicit global bank scope. Add fresh reviewed edits, immutable retained inputs, normal commands/history and Save/Open. Compose qualified Current textures into selected field models while retaining Retail comparison and STP/palette provenance. Integrate fixed-span writes with normal native package preparation and verify full carrier/neighbors and composed model/texture delivery. Growing container allocation and runtime visual/cadence/lighting/palette behavior remain separate unverified requirements. The full SDK goal remains incomplete and active.


## Project Ownership, Current Composition And Build

In progress — 2026-10-11. The saved `texture_overrides` collection now supports the explicit global owner `field-party://textures`. Canonical IDs are limited to the eight source bank members. Bindings retain immutable Retail disc/TIM hashes separately from authored TIM hashes and sizes; ordinary scene and World ownership rules stay distinct. Only exact image/palette layouts are supported, including on Open and Build. Existing typed texture commands create normal history steps and immutable content files.

Save/Open verifies original source identity and the exact replacement layout. Current field-equipment inspection composes saved model geometry and shared-bank replacements before crop association; its selector now says Current Model / Current Textures. Retail ignores authored replacements. Clip sources remain Retail and live residency/palette animation/lighting remain unverified. Current geometry and GLB provenance include the complete texture binding map with original hashes; export freshness still covers project content.

Normal Build routes this global owner separately from imported scene revalidation and World resources. Source hashes, exact TIM replacements, payload audits and disc preimages qualify the original compressed section overlay. There are no guessed scene descriptors or growth requests. Native model and texture edits can share the same PROT entry while retaining separate compressed-section ownership.

Eight palette edits survive eight-step Undo/Redo and Save/Open alongside a saved model edit. Six selected-model/variant Current receipts independently match 26532 literal green BGR555-derived RGBA pixels. Clients replay geometry/source selection and reject 36 altered layer/binding/geometry/export envelopes. The native package's edited texture stream independently decodes to all eight requested TIMs, and directory/ZIP bytes match. A first Build run exposed global ownership being routed through imported-scene revalidation; the corrected routing and repeated workflow pass. Private evidence: `local-output/sdk-20260909/field-equipment-20261011/current-texture-cases.json`.

Actual muted Edge editor renders the authored shared textures and downloads a Current full walk clip with all eight binding receipts embedded. Wide/400-pixel captures were inspected; exact download/API bytes, selection withdrawal and unchanged project/history pass, with no errors or commands. This is one selected model/variant browser check, not a whole-game visual acceptance claim. Evidence: `current-texture-browser-proof.json` in that same private directory. Existing Retail static/full-clip clients pass; thirteen targeted Project/World/scene-texture tests report one retail-gated skip.

Remaining work: project/browser source registration and fully reviewed shared-bank editing controls; wider authoring workflows, growing container relocation and runtime appearance/residency. A private data-package Build ran. No recomp compilation, installation, game, attachment or disc export ran. Full goal remains incomplete and active.
