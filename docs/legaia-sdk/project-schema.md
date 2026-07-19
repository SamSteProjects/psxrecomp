# Legaia SDK project schema

## Format decision

Use a small human-authored `project.toml` as the entrypoint and versioned canonical JSON documents for scene/entity/claim graphs. TOML keeps metadata and build targets reviewable; JSON supports schemas, deterministic generated snapshots and large structured graphs. Mesh/texture caches are referenced by digest and remain local.

```text
my-legaia-project/
  project.toml
  authored/
    scenes/rim_elm.json
    dialogue/*.json
  imports/
    <disc-import-id>/manifest.json
    <disc-import-id>/scenes/*.json
  provenance/
    claims.json
  runtime/                 # ignored, ephemeral observations
  generated/               # ignored, build outputs
```

The SDK must create ignore rules for `runtime/`, `generated/`, extraction caches and any local source-disc links before the workflow is implemented. Imported metadata may be tracked only if a metadata-only validator proves it contains no proprietary bytes/text.

## Project metadata

```toml
schema = "legaia-sdk-project/0.1"
id = "example.rim-elm-study"
name = "Rim Elm Study"

[source]
disc_identity = "sha256:<digest>"
serial = "SCUS-94254"
region = "ntsc-u"
importer_version = "0.1.0"
semantic_reference_revision = "d6e64c68ede25813d35db20980da82a1a025549b"
import_manifest = "imports/<id>/manifest.json"

[runtime]
profile = "legaia-ntsc-u-scus94254-v1"
bridge = "tcp://127.0.0.1:4370"

[[build.targets]]
id = "runtime-preview"
kind = "extended-native"
output = "generated/preview"

[[build.targets]]
id = "ps1-patch"
kind = "ps1-patch"
format = "ppf3"
output = "generated/patch.ppf"
```

The disc path is a local launch/import setting, not persisted in shareable project metadata. The project stores identity, not ownership or redistribution rights.

## State envelope

Each editable property uses explicit layers:

```json
{
  "transform": {
    "imported": {"translation": [1088, 0, 2624], "rotation": [0, 0, 0], "scale": [1, 1, 1]},
    "authored": null,
    "live": {"session": "...", "frame": 18422, "translation": [1090, 0, 2620]},
    "effective_preview": "live"
  }
}
```

`effective_preview` is a UI decision and is not serialized as authoritative state. Imported data is immutable for an import ID. Authored data is a sparse overlay; deletion means remove the overlay, not delete imported retail state.

## Scene document

```json
{
  "$schema": "https://example.invalid/legaia-sdk/scene-0.1.schema.json",
  "id": "scene://rim_elm",
  "import_id": "sha256:...",
  "source": {"cdname": "town01", "prot_range": [5, 12]},
  "geometry": [],
  "actors": [],
  "collision": {},
  "triggers": [],
  "doors": [],
  "camera_regions": [],
  "encounters": [],
  "shops": [],
  "battle_triggers": [],
  "claims": []
}
```

## Entity shapes

### Geometry/model/animation references

References use semantic IDs plus source locators and never embed retail bytes:

```json
{
  "id": "asset://rim_elm/models/scene-tmd-42",
  "kind": "model",
  "imported": {"object_count": 12, "bounds": {}},
  "source_locator": {"prot_entry": 8, "decoded_offset": 4096, "record_index": 42},
  "cache_ref": {"digest": "sha256:...", "local_only": true}
}
```

Animations reference an ANM bundle/record and include indexing convention/evidence. A model reference does not imply an animation relationship.

### Actor

```json
{
  "id": "scene://rim_elm/actors/record-p1-07",
  "aliases": ["village_elder"],
  "origin": {"carrier": "man-main", "partition": 1, "record": 7},
  "transform": {"imported": {}, "authored": null},
  "model_ref": {"claims": ["claim:model:..."]},
  "animation_refs": {"claims": []},
  "movement": {"claims": []},
  "interaction": {"claims": []},
  "visibility_conditions": {"claims": []},
  "dialogue_refs": {"claims": []}
}
```

Future authored actors use `origin.kind = "authored"` and a new UUID/semantic slug. They do not counterfeit a retail record index.

### Scripts and conditions

Script documents distinguish raw imported identity from an authored higher-level program:

- `raw_ref`: carrier/partition/record/span and digest.
- `decoded_ir`: derived instructions with per-instruction confidence.
- `authored_program`: editor-owned command/graph form.
- `lowering`: generated mapping/report for a build target.

Story conditions use an expression AST (`flag_test`, `all`, `any`, `not`, comparisons) with each imported leaf citing claim/evidence. Unknown opcodes remain opaque nodes with raw locators, not invented semantics.

### Dialogue

Dialogue records contain stable IDs, tokenized authored content and import references. Retail text is never placed in repository fixtures. The model distinguishes:

- inline MAN dialogue;
- MES container/record dialogue;
- derived decoded tokens;
- authored replacement tokens/text;
- generated encoded bytes (local build artifact).

### Collision, triggers, doors and cameras

- Collision: heightfield/grid reference, static collider records and authored overlay shapes.
- Trigger: region/shape, event/script claim and activation conditions.
- Door: trigger reference, destination scene/entry/facing claims.
- Camera region: MAP/MAN region source, raw 18-byte record locator, decoded parameters with field-level confidence.

### Encounters, shops and battle triggers

These are independent typed collections even when backed by the same MAN carrier. They reference formation/shop/script records through claims; the first slice imports but does not edit them.

## Runtime overrides

Runtime preview configuration is authored intent, separate from live state:

```json
{
  "id": "override:actor-transform:...",
  "target": "scene://rim_elm/actors/record-p1-07",
  "operation": "set_transform",
  "value_source": "authored.transform",
  "policy": {"reapply": "never", "rollback": "on_disconnect"},
  "allowed_profiles": ["legaia-ntsc-u-scus94254-v1"]
}
```

No override is implemented in the read-only slice. Future overrides require explicit user action and runtime address/profile validation.

## Undo and redo

Use project-model commands over authored state only (`SetActorTransform`, `ReplaceDialogue`, `SetVisibilityCondition`). Commands carry before/after authored values and stable targets. Import refreshes and runtime observations are events, not undoable authored edits. Generated builds never enter the undo log.

## Versioning and migrations

- Every document declares schema name/major/minor.
- Readers reject unsupported major versions and preserve unknown additive fields on round trip where practical.
- Migrations are deterministic, tested and never need the source disc unless explicitly described.
- Importer, semantic-reference and runtime-profile revisions are recorded independently from project schema version.

## Validation

- JSON Schema validates shape and state-layer separation.
- Referential integrity validates semantic IDs and claim/evidence links.
- Privacy validator rejects binary payloads, disc paths, decoded retail dialogue and disallowed extensions in shareable trees.
- Build preflight requires exact disc/import/profile compatibility, resolved target capabilities and an explicit policy for tentative/contradictory claims.
