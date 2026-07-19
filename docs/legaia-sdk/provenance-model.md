# Semantic identity and provenance model

## Goals

The model must answer both “what does the editor call this?” and “why do we believe it maps to retail data/runtime state?” It stores observations and claims, not just flattened properties. Multiple incompatible claims may coexist until evidence resolves them.

## Identity

A semantic URI is stable within a project/disc-revision namespace:

```text
scene://rim_elm
scene://rim_elm/actors/village_elder
scene://rim_elm/actors/record-p1-07
asset://models/prot-0042/tmd-03
script://rim_elm/man-main/p1/record-07
dialogue://rim_elm/mes-prot-0046/record-12
```

Human names such as `village_elder` are aliases, not proof. Before a curated alias is accepted, the importer generates a deterministic structural ID from disc identity, normalized scene label, carrier identity, partition and record index. Renaming an alias does not change the underlying object ID.

Recommended primary key:

```text
sem:v1:<disc-family>:<entity-kind>:<canonical-source-path>
```

`disc-family` identifies a compatible retail data family, while the project records the exact disc hash separately. IDs must not include absolute local paths, decoded dialogue, RAM addresses, catalog ordering after filters, or runtime actor slots.

## State layers

| Layer | Meaning | Mutable | Source of truth |
|---|---|---:|---|
| `imported` | Deterministic facts decoded from a particular disc snapshot | no | user disc + provider version |
| `derived` | Recomputable semantic interpretations/claims | replaceable | evidence graph + algorithms |
| `authored` | User intent and edits | yes | SDK project |
| `live` | Timestamped PSXRecomp observations | ephemeral | runtime session |
| `generated` | Build/import caches and export products | disposable | pipeline inputs |

For transforms, expose `imported_transform`, optional `authored_transform`, and optional `runtime_transform`. The editor computes an effective preview transform, but never overwrites one layer with another.

## Core records

```text
SemanticEntity
  id: SemanticId
  kind: scene | actor | model | animation | script | dialogue | ...
  aliases[]
  imported_fields{}
  authored_fields{}
  claims[]: ClaimId

Claim
  id
  subject: EntityRef
  predicate
  object: EntityRef | typed literal | RawLocator | RuntimeLocator
  confidence
  status: active | superseded | rejected | unresolved
  evidence[]: EvidenceRef
  alternatives[]: ClaimId
  algorithm{id, version, source_revision}
  created_at

Evidence
  id
  kind
  source
  locator
  observation
  digest
  captured_at
  tool{id, version, source_revision}
```

## Confidence

| Level | Meaning | Minimum treatment |
|---|---|---|
| `confirmed` | Direct parser span plus validated semantics, or repeatable runtime trace establishing the relationship | Show as fact with evidence link |
| `strongly_inferred` | Independent evidence agrees and plausible alternatives are materially excluded | Show inference badge and evidence |
| `tentative` | One coherent clue or heuristic; alternatives remain | Never use silently for export |
| `unknown` | No supported mapping | Preserve absence; do not fabricate default |
| `contradictory` | Two or more supported incompatible interpretations | Display competing claims; block dependent export unless resolved |

Confidence is a property of each relationship, not of the whole entity. An actor’s placement-to-model link may be confirmed while placement-to-dialogue remains unknown.

## Locators

### Disc/raw locator

```json
{
  "disc": {"sha256": "<local-disc-digest>", "serial": "SCUS-94254"},
  "iso_file": "PROT.DAT",
  "prot_entry": 42,
  "scene_block": "town01",
  "carrier": {"kind": "bundle_man", "entry": 42, "chunk_offset": null},
  "record": {"partition": 1, "index": 7},
  "byte_span": {"offset": 1234, "length": 16},
  "decoded_as": "legaia_asset::man_section::ActorPlacement"
}
```

Offsets declare their coordinate space (`iso_file`, `prot_entry`, decoded carrier, or record). A locator without a coordinate space is invalid.

### Runtime locator

```json
{
  "session_id": "runtime-uuid",
  "frame": 18422,
  "scene_epoch": 9,
  "overlay": {"load_address": "0x801C0000", "size": 196608, "hash": "sha256:..."},
  "actor_slot": 11,
  "ram_span": {"address": "0x8008A120", "length": 320},
  "layout_profile": "legaia-ntsc-u-scus94254-actor-v1"
}
```

The tuple `(session, scene_epoch, overlay hash, slot, observation interval)` scopes a live actor. Address or slot alone is never identity because both are reused.

### Symbol locator

```json
{
  "program": "field-overlay",
  "overlay_hash": "sha256:...",
  "address": "0x801E35E8",
  "original_function": "FUN_801E35E8",
  "ghidra_label": "field_vm_test_system_flag",
  "symbol_map_revision": "d6e64c6",
  "confidence": "strongly_inferred"
}
```

## Actor relationship example

For `scene://rim_elm/actors/village_elder`, independent claims may include:

- actor **originates_from** MAN partition 1 record 7 — confirmed by parser span;
- actor **uses_model** scene TMD pool index 42 — confirmed if the placement model byte and `SceneResources` index resolve;
- actor **uses_animation** ANM record 9 — strongly inferred until record indexing and pose are validated for that carrier;
- actor **executes_interaction** partition 1 record 7 — confirmed only if placement/script binding is explicit;
- interaction **tests_story_flag** `0x142` — confirmed or inferred per a clean instruction walk/runtime trace;
- interaction **references_dialogue** MES record 12 — unknown unless an operand/data-flow chain or runtime trace reaches that MES record;
- actor **correlates_to** live slot 11 — time-bounded claim supported by scene epoch, model/transform/script pointer and trace evidence.

The editor may display all of these, but must not render the MES relationship as settled merely because the dialogue appears near the actor record.

## Evidence kinds

- `parser_span`: exact bytes decoded by a named parser/version.
- `control_flow`: decoded instruction/branch/data-flow path.
- `runtime_read` / `runtime_write`: bounded RAM observation with frame and PC/function where available.
- `runtime_trace`: ordered read/write/function trace digest plus query parameters.
- `overlay_identity`: load address, byte length and content digest.
- `symbol_map`: named function/address mapping with source revision.
- `documentation`: exact repository path/section and commit.
- `cross_runtime_parity`: clean-room/imported state compared with PSXRecomp state.
- `curated_alias`: human label, contributor/source, never structural proof by itself.
- `negative_evidence`: a bounded search that failed, including corpus and algorithm so it is not mistaken for global absence.

## Competing interpretations

Claims are append-only within an import snapshot. A validation operation can mark a claim rejected or superseded, but does not delete it. `alternatives` forms an explicit set; `contradictory` is derived when two active alternatives cannot both hold. Consumers must select only claims meeting a declared confidence policy.

## Determinism and privacy

- Canonical JSON serialization, sorted maps and fixed numeric/address formats make claim IDs/digests deterministic.
- Evidence stores hashes and minimal windows/decoded operands, not proprietary payloads. Raw bytes remain on the user’s machine behind disc locators.
- Dialogue fixtures contain synthetic token streams or counts/digests, never retail text.
- Runtime trace artifacts default to local ignored storage. A shareable report must pass a metadata-only allowlist.

## Validation rules

1. Every relationship shown by the first slice has at least one evidence record.
2. Every inferred relationship has an algorithm version and explicit confidence.
3. Every raw relationship identifies disc, container and byte coordinate space.
4. Every live relationship includes session, frame/interval and scene/overlay epoch.
5. An authored property may cite an imported source but cannot mutate or masquerade as it.
6. Reimporting the same disc with the same provider version yields identical structural IDs and imported digests.
