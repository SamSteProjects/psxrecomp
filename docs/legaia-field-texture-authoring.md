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


## Shared Palette Editor

Offline checks passed — 2026-10-11. Eight source-qualified shared TIMs now register in the merged Project Browser under Global shared field textures. This is a global bank scope with stable texture IDs; no imported scene membership or live residency is fabricated. The native metadata endpoint returns original hashes, dimensions, local palette counts and immutable source intervals without pixels.

The inspector distinguishes Current palette inspection from unsaved Review/Proposed pixels. Native palette index/entry/unsigned16 word inputs operate on existing source words. The client independently reads the inspected word bytes and replays full TIM-local nibble indices into RGBA; source model association continues to use flat VRAM uploads. Changing the draft withdraws Apply and restores the inspected pixels. Apply uses the exact fresh Review receipt, project context, Current hash and palette selection. It creates one normal texture history step. Review checks all existing shared replacements together against the original compressed section capacity, preventing a newly reviewed word from producing an undeliverable combination.

Exact routes: `/api/field-texture-resources`, `/api/field-texture-inspect`, `/api/field-texture-review`, `/api/field-texture-apply`. Native HTTP checks pass metadata/source inspection, unchanged Review state, stale Apply refusal, one-step history, Undo/Redo and Save/Open. Clients reject five altered Review envelopes and independently match complete native TIM-local pixels. Sixteen existing Asset Database tests plus its Node workflow pass.

Actual muted Edge browser verification uses a standalone private disc project without an imported scene. It passes discovery of all eight assets, inspection, Proposed pixel preview, unchanged pre-Apply project, one-step Apply, Undo/Redo and Save. Wide/400-pixel captures inspected; no errors or commands. An earlier imported Town01 browser run reached Apply, but automatic full-scene refresh remained busy beyond the observation timeout before history checks could finish. This remains a separate imported-scene browser/performance limitation; it is not included in the passing standalone claim. Source fixture attempts and final proof remain under `local-output/sdk-20260909/field-equipment-20261011/`; evidence files are `texture-editor-cases.json` and `texture-editor-browser-proof.json`.

Remaining: broader shared image/file replacement and retained-input controls, imported-scene responsiveness and wider workflow verification, growing allocation and actual runtime palette/appearance acceptance. Existing native package delivery evidence is documented above; this editor check ran no Build, compilation, game, attachment, installation or disc export. Full SDK goal remains incomplete and active.


## Scene And Native GLB Texture Composition

Offline checks passed — 2026-10-11. The general model/scene adapter and native GLB authoring texture preview now use the same shared TIM composition service as field-equipment inspection. This closes an adapter gap where the saved bank appeared in the dedicated inspector but general model rendering still used Retail. Retail scene projections clear authored bindings and are tagged separately. Qualified field model routes skip unrelated scene TIM loading rather than merging the two bank scopes.

All three party model adapters independently match 18721 authored green pixels and the native GLB texture preview; Retail/Current differ as expected and project/history remain unchanged. A focused guard rejects any attempted scene-bank load for these routes. Evidence: `local-output/sdk-20260909/field-equipment-20261011/adapter-proof.json`. Twenty-one existing scene/model workflow tests report one retail-gated skip; sixteen Asset Database tests and its Node suite pass.

Direct Town01 backend measurements cover 119 assets and 261 entities: cold 7.13 seconds, palette-edit rebuild 7.35 seconds, cached 0.25 seconds. Evidence: `scene-refresh-timing.json` in that same private directory. These measure backend preview only, not total browser responsiveness or game performance.

Read-only Project Browser discovery previously held the global editor busy state across serial resource-scope refreshes after palette edits. The desktop editor now opts into background discovery while retaining generation, source freshness and abort checks. A mounted-control test verifies that a pending read does not claim the mutation busy state and that completion/disposal preserve another operation's busy state. Server commands remain serialized by their existing lock. Actual muted Edge browser with Town01 imported now passes all eight source registrations, palette inspection, unsaved Proposed preview, one-step Apply, Undo/Redo and Save in wide/400-pixel layouts with no errors or commands. The earlier imported-scene timeout scope is superseded by this focused passing result; broad responsiveness and gameplay performance are not established. Evidence: `texture-scene-browser-proof.json` in the same private directory. No Build, compilation, game, attachment, install or disc export ran for this adapter/coordination check.


## Shared TIM File Replacement

Offline checks passed — 2026-10-11. The shared-bank inspector now downloads exact Retail and Current TIM files after inspection. Replacement Shared TIM accepts an existing-layout file up to 1 MiB. Review validates the original source headers, mode, dimensions, VRAM/CLUT rectangles and member length, then checks the candidate together with other saved bank overrides against the original compressed section budget. It displays unsaved Proposed TIM-local pixels. Apply Reviewed Shared TIM requires the same file bytes, project/source context, inspected Current hash and exact Review receipt.

Exact routes: `/api/field-texture-download`, `/api/field-texture-file-review`, `/api/field-texture-file-apply`. Download checks the inspected Current hash even when returning Retail, so navigation/source changes cannot silently change context. File Apply stores the exact uploaded native TIM in the immutable authored texture cache and uses normal texture history; subsequent numeric palette edits can create another native content version. This does not add a separate historical upload-library abstraction or resize/allocation support.

Native HTTP checks pass exact Retail/Current downloads, image-index plus palette-word replacement, unchanged Review state, stale Apply refusal, exact byte retention, one-step history, Undo/Redo and Save/Open. Normal private package Build independently decompresses its texture overlay and reads back the complete requested TIM. Client checks compare the entire uploaded/proposed bytes, protected headers, source/Current/file hashes and refuse five altered file Review envelopes. Eight existing Project/World checks pass.

Actual muted Edge standalone disc-project browser passes both downloads with exact API/file byte identity, file chooser Review, Proposed image preview without project mutation, one-step Apply, Undo/Redo and Save. Wide/400-pixel captures inspected; no page errors or commands. Evidence: `local-output/sdk-20260909/field-equipment-20261011/tim-file-cases.json` and `tim-file-browser-proof.json`. This check does not repeat the broader imported-scene/browser campaign or prove runtime upload/appearance. Native package Build only; no recomp compilation, installation, game, runtime attachment or disc export ran. Full SDK goal remains incomplete and active.
