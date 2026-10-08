# NPC Arrival Viewport Authoring

The destination preview now supports local X/Z and facing drafts, a 64-unit X/Z placement gizmo, Draft/Proposed markers, Review, Discard and Apply. **Edit NPC Arrival in Viewport** exposes the controls. **Move NPC arrival draft** enables the gizmo; Escape restores the draft/proposal captured when dragging began. Height stays a separate reference plane. Numeric fields refuse off-grid or out-of-range inputs without rounding.

Review binds the source NPC, its typed transition, navigation-independent persistent inputs and the loaded destination preview key. It preserves direction-byte upper bits and other owned transition entries, then reuses the ordinary NPC source Review and native Current composition. The client independently validates typed requests, ownership and every source byte audit. Imported donor actor overrides remain independent of the clone.

Apply uses `set_actor_draft_arrival` through ProjectService. The ordinary `set_actor_draft_transitions` command runs on detached source-scene NPC ownership/history; fresh input, destination and history checks precede committing those collections. Destination navigation, imports and other authored collections remain held. A changed edit adds one Undo step; an already saved full entry is a no-op. Partial/inherited ownership becomes an explicit full entry only on Apply. Save/Open and native Build continue using the existing transition writer.

A successful Apply obtains a fresh saved preview. Project changes withdraw old Draft/Proposed state. Local drags and Review do not change project data. The controls use grouped readable fields and bounded scrolling; the 400px layout preserves at least150px of viewport height in the checked1000px-high window. Collapsing the editing panel preserves the staged comparison.

## Offline Checks — 2026-10-08

One focused Retail Python workflow passed partial ownership to exact full record bytes, independence from a separately authored clone and donor actor, actual HTTP200/400 boundaries, immutable Review, stale/wrong-destination/Live refusal, one-step Apply, no-op Apply, Undo/Redo and Save/Open. Map02 donor0002 PC53 changes source arrival bytes at62..64 from partial Current `1f1ef8` to `8001ff` (X128/Z192/facing sector7); every other record byte stays exact. The existing source arrival preview workflow also passed.

Five Node suites passed: new destination Review, existing NPC arrival preview, all256 native grid references, existing NPC arrival source/Review/Current selection and shared arrival gizmo contracts. Four Python AST and four JavaScript syntax checks passed. Fresh private browser checks passed invalid X65 refusal, actual64-unit gizmo movement, Escape, Discard, immutable Review, independent complete-record literal equality, retained direction upper bits, Apply/fresh preview, Undo/Redo and Save/Open. Wide/400px captures were inspected with zero page errors and no horizontal control overflow. The original document/Undo stack/imports were restored, one Redo entry retained, the original state saved again and helpers closed.

Private evidence: `local-output/sdk-20260909/npc-arrival-authoring-20261008/qualified/retail.json`, `browser-complete/`, `source-hashes.json` and `checks-receipt.json`. Earlier Save-selector harness and insufficient narrow-height attempts remain retained separately. The actual Retail example is a self-destination Map02 transition; it does not establish cross-scene travel or runtime activation.

No native Build, game, runtime attachment, installation or disc export ran for this checkpoint. Destination height, streaming delivery and gameplay remain unverified. The full SDK goal remains active.
