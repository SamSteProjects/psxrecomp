# World TIM Project Authoring and Build

Offline checks passed on 2026-10-10. This slice connects existing native kingdom TIM payloads to project authoring, history, persistence and the normal SDK package Build. Dedicated World texture editing controls and a Current pixel/geometry preview still require editor integration. Gameplay appearance is unverified; this is not full feature acceptance.

## Native source and project ownership

The adapter qualifies the pinned map01/map02/map03 kingdom range and unique seven-slot entry-head descriptor table, then provides the existing exact-layout TIM serializer with native compressed-pack coordinates. Canonical identities are `texture://map01/kingdom/0000` and their corresponding kingdom/member IDs. The native inventory contains 47, 32 and 56 supported TIM members. Opaque members and unsupported TIMs remain unchanged and diagnostic.

World bindings share the existing private `Authored/Textures` content store and `texture_overrides` history. Their source owner is `worldmap://map01/textures` (or map02/map03), independent of the active field scene. Each binding retains the original disc and TIM SHA-256 values. Existing palette, index-pixel/rectangle and exact-layout replacement SDK methods reuse this context; immutable TIM headers, VRAM origins, image dimensions and palette layout remain protected. World image allocation is refused. No new compression or binary writer was introduced.

Undo/Redo, Clear/Undo and Save/Open retain the World binding independently of field imports. Offline Open checks canonical kingdom ownership and private content integrity; authoring and Build additionally re-read the native source and refuse changed disc/TIM identities. Imported disc identities, when present, must agree. The normal package Build keeps World textures out of field reimport routing, then reuses the existing guarded overlays, audit validation and relocation composition machinery. Native tests in this slice exercised existing-stream overlays; they did not exercise a growing native kingdom relocation.

## Evidence and remaining work

Thirteen focused Python checks passed with the retail disc enabled and no failures, errors or skips: native adapter, World project history/source refusal, existing field project integrity, field Build guards and the generic TIM serializer. The existing retail field texture Build test also passed, covering field texture/MAN composition, no-op packages, Clear and private-file tampering. Four changed Python modules passed AST checks. The field Build guard fixture was updated for the existing sequence-replacement collection so it reaches its intended texture guards.

Private native evidence: `local-output/sdk-20260909/worldmap-texture-authoring-20261010/proof.json` and `project-proof.json`. All three first native TIMs matched the independent read-only decoder; a one-word palette edit produced exact complete decoded-pack reconstruction. The project probe passed palette authoring, Undo/Redo, Save/Open and one normal SDK package Build containing all three kingdom changes. Every packaged stream exactly matched the independently requested overlay and decoded to the complete expected pack. Imported documents stayed unchanged. Private outputs and retail payloads are not committed.

The existing [Native World TIM Inspector](legaia-worldmap-texture.md) continues to show Retail source pixels. Dedicated World Review/Apply controls, Current preview, viewport texture refresh and their browser workflow verification remain next. No native recomp compile, game, runtime attachment, install or disc export ran. Runtime palette selection, animation and appearance remain unknown until gameplay verification. The full SDK goal remains active.
