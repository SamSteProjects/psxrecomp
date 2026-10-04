# Combined native face/material model assignment

Status: backend and HTTP qualified; combined browser authoring/review is pending.
The existing separate face and material editors are unchanged.

`POST /api/model-texture-assignment-preview` accepts exactly:

- `asset_id`: imported active-scene model identity.
- `primitive_edits`: 1 to 256 ordinary source-qualified face drafts (existing
  vertex connections, UV bytes, stored RGB and existing normal references).
- `material_edits`: 1 to 256 ordinary semantic material drafts (native page/depth,
  indexed palette coordinates or shared group semitransparency).
- `expected_sha256`: exact Current effective native model hash.
- `source_key`: exact Current editable scene source key.

The normal face/material codecs enforce their own source domains, duplicate
ownership and masks. Direct 16-bit bindings preserve Current CLUT; ABR/reserved
bits remain protected. Explicit group semitransparency affects its shared members.
Face topology, vectors, unknown bytes and packet capacities are unchanged.

Review independently constructs face-only and material-only candidates without
publishing either. Material edits are then applied to the face candidate. The
material audit must equal its independent Current audit, and a complete native
Current-to-final audit must equal the union. Retail/retained-topology comparison
and a source-bound `review_key` are regenerated from exact bytes and drafts.
Intermediate hashes are composition evidence; **Current** is always the actual
project model. HTTP adds the existing verified Current/Proposed texture previews.

`POST /api/model-texture-assignment-apply` requires the same fields plus the exact
`review_key`. It recomputes all qualification, rejects changed/stale/no-change
requests, and publishes only the final replacement. Existing additions/removals
and topology ledger replay stay with the ordinary writer. One model Undo restores
both field sets together. Save/Open, normal Build and independent package readback
use existing model content/ledger composition.

Texture creation, conversion and source retention remain separate explicit
operations. This transaction changes no TIM pixels or texture-slot metadata and
does not establish live VRAM residency, runtime ownership or gameplay correctness.

Verification: four focused real native codec/HTTP tests include group ABE,
unchanged readonly review, wrong/changed/stale/invalid/no-change rejection,
one-step history and stable authored face IDs with exact retained-ledger replay.
Private Town01 HTTP proof independently checked five-face UV/TPage bytes, one
combined model Undo, stale repeat rejection, offline Open and normal Build exact
model/TIM bytes with unchanged decoded neighbors:
`local-output/sdk-20260909/model-texture-assignment-20261004/parent/proof.json`.
No game launched. The combined browser workflow is the next integration step.
