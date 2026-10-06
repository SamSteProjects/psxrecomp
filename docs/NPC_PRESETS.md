# NPC draft presets

Select an authored NPC in the hierarchy, then choose **NPC presets…**. Enter a
library name and capture the selected draft. Its default NPC name, retail donor
and native X/Z placement are frozen in the project template library. The source
panel records the owning scene, original draft ID, disc identity and import SHA-256.
Editing or deleting the original draft does not update the captured preset.

Choose **Review new NPC instance** in the owning scene, enter its new name and
X/Z position, then review. Coordinates must be exact multiples of 64 from 64 through
16384. **Inspect NPC instance in scene** displays a detached proposal and permits
comparison with Current. **Return to NPC preset** restores the review dialog.
Changing an input withdraws Apply. Apply creates one independent authored identity;
Undo removes it, Redo restores the same identity and metadata. Save retains the
preset and placed NPC. Renaming/deleting a preset does not change placed instances.

The SDK endpoints `/api/npc-preset-review` and `/api/npc-preset-scene` qualify the
full project source key. Commands `create_npc_preset` and `instantiate_npc_preset`
operate only in Edit mode; instantiation requires the reviewed key. The schema is
`npc-draft-preset-v1` within `actor_templates`, separate from imported-actor override
presets. Generic imported-actor Apply explicitly rejects it.

Presets capture retail donor and placement defaults only. They do not freeze donor
appearance overrides, authored actor scripts, animation assignment, source height,
collision or runtime state. Shared model and animation asset edits remain project-wide.
There is no inherited prefab link or cross-scene remapping.
Use Review Build to assess the entire candidate and supported normal Build to verify
native output. Gameplay still needs manual validation of spawn, behavior and visibility.

## Transfer between projects

Choose **Export preset JSON** on an NPC preset card to download `npc-preset.json`.
In the recipient project, import the same supported retail scene from the same disc,
open the preset library, and choose **Import preset JSON**. Review its new library
name and source provenance, then **Import reviewed preset**. Import creates one
independent library identity and changes no NPC instances. Undo removes the imported
preset; Redo restores it. Save/reopen retains its frozen defaults and provenance.
Choose **Review new NPC instance** afterward to place it in its owning scene.

The metadata-only file schema is `legaia.npc-preset-file.v1`, distinct from actor
preset file versions 1/2. Exact donor, name and native-grid X/Z defaults are retained
with capture draft identity, scene/disc identity and import hash. The original draft
need not exist in the recipient. A current user-owned disc and freshly matching
retail import are required for file export/import. Files are limited to 8 KiB;
unknown payload fields, mismatched schema/scope/hash and changed library reviews
reject. No model, texture, script, animation, live state or native binary is embedded.

Private transfer evidence is under
`local-output/sdk-20260909/npc-preset-transfer-20261005/`: `proof.json` records actual
download/upload, reviewed import, library Undo/Redo, Save/reload and placement;
`transfer-review-540.png` records the narrow review. `normal-build-proof.json` verifies
the recipient's format-6 compressed reserved-span package, exact native MAN, descriptor
size, model/animation binding and saved current-input receipt. No game was launched.

Acceptance evidence (private fixture, no game launch):

- `local-output/sdk-20260909/npc-presets-20261005/proof.json`: actual browser capture,
  review, scene comparison, Apply, Undo/Redo and persistence; imported content and
  existing drafts unchanged.
- `normal-build-proof.json`: normal format-7 compressed MAN growth, all seven appended
  rows, exact prepared native MAN and saved receipt/current-input verification.
- `preset-review-540.png`: narrow review layout with wrapped action buttons.
- Focused checks: `test_npc_presets.py` and `test_npc_presets.mjs`; existing actor and
  appearance template/HTTP regression checks also pass.
