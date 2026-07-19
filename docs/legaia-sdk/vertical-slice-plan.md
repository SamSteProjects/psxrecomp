# Read-only vertical slice plan

## Outcome

Given a user-supplied NTSC-U disc, enumerate and display one Rim Elm field scene, select one existing NPC, show its imported source/model/transform/script/flag/dialogue evidence, connect to PSXRecomp, and show any defensible live correlation beside imported state. Every relationship includes provenance and confidence.

The slice ends without editing RAM, authoring actors, rebuilding a disc, replacing renderers, adding an ECS or building the final web/React editor.

## Stages and acceptance gates

### 1. Contract and privacy scaffold

- Add `integrations/legaia/{config,symbols,schemas,provenance,bridge,project-model,generated}` as needed.
- Add explicit ignore rules for user discs, extracted/cache/runtime/generated paths; verify with `git check-ignore` tests.
- Define semantic snapshot, claim/evidence and runtime-observation schemas.
- Pin the PSXRecomp importer/runtime profile and the Andrew reference revision without vendoring upstream code.

Gate: synthetic fixtures validate; repository scan proves no proprietary bytes/text were added.

### 2. PSXRecomp-side importer spike

Implement a narrow importer under `integrations/legaia/`, using Andrew's existing chain as the traced reference behavior:

```text
RawDisc/ISO9660 → PROT.DAT + CDNAME.TXT → ProtIndex → Scene::load
→ build_field_scene → build_npc_catalog → MAN record/flag/dialogue analyses
```

Input: disc path and `town01`/Rim Elm selector. Output: schema-versioned metadata, geometry cache references, actor placements, model/ANM refs and claim/evidence records. Do not export retail dialogue into committed output.

The SDK implementation lives in PSXRecomp. For each parser or semantic rule, record the exact Andrew source/doc path and reference commit used. Development parity tests may compare the importer with Andrew's tools, but those tools are not required by users.

Gate: two imports of the same disc/importer version produce identical IDs and canonical metadata digests.

### 3. Headless SDK workbench

Implement a small CLI/backend before an editor UI:

```text
legaia-sdk inspect --disc <user.bin> --scene town01
```

It enumerates geometry groups/placements/ground, actors and a selectable actor detail report. The report includes raw carrier/partition/record/span, imported transform, model reference, animation/movement/interaction candidates, story-flag sites and dialogue candidates. Unknown relationships are shown as unknown.

Gate: one selected NPC has a stable semantic ID and every displayed relationship links to evidence/confidence.

### 4. Runtime connection

Implement the TCP client against existing commands first: `ping`, `pause`, `get_registers`, `read_ram`, `vram_peek`, `overlay_dump`/status, snapshots/watches and `continue`. Add `protocol_info`, `overlay_identity` or `read_regions` only if the spike demonstrates a concrete need.

Gate: launch/connect, startup detection, bounded observation and clean disconnect work without source logging or runtime behavior changes.

### 5. Legaia layout profile and correlation

Create one evidence-backed profile for the exact tested executable/revision. Determine scene marker, actor table/pointers, slot lifecycle and fields through symbol research plus structured RAM/write/function traces. Correlate the selected imported actor using multiple signals.

Gate: either (a) a time-bounded live actor claim reaches the declared threshold with reproducible evidence, or (b) the UI truthfully reports no resolved match and lists candidates/unknowns. A forced match is a failure.

### 6. Side-by-side presentation

Present:

- geometry/actor enumeration;
- selected actor semantic ID and aliases;
- imported source record and transform;
- model/animation/script/flag/dialogue claims;
- live session/scene/overlay/slot and runtime transform when resolved;
- imported vs runtime values;
- provenance/confidence drill-down and contradictions.

Gate: the report remains useful with PSXRecomp disconnected, with no disc, and with correlation unresolved; each condition has a clear diagnostic/skip state.

## Exact next implementation task

After approval, implement only the **PSXRecomp-side Rim Elm import contract spike**: schemas plus a headless importer under `integrations/legaia/` for `town01`, producing metadata-only actor/source/model/transform claims. Use Andrew's latest scene/NPC implementation as the reference and parity oracle, not as a runtime dependency. Do not touch generic PSXRecomp runtime code in that task.

This validates the most important repository boundary before runtime correlation or UI work.

## Testing strategy

| Test | Fixture/source | Assertion |
|---|---|---|
| Stable semantic IDs | synthetic metadata + disc-gated Rim Elm | unchanged across order/filter/UI alias changes |
| Parser determinism | user disc, importer/reference revisions pinned | canonical import digest repeats |
| Semantic-to-raw provenance | synthetic carriers; disc-gated real spans | every imported property resolves to valid container/span |
| Scene actor enumeration | `LEGAIA_DISC_BIN` | count/order/source records deterministic |
| Actor-to-model | disc-gated | placement model index resolves or emits explicit diagnostic |
| Script reference | synthetic bytecode + disc-gated | claim includes carrier/record/instruction evidence and confidence |
| Dialogue resolution | synthetic MES/inline tokens + disc-gated locators | inline and MES are not conflated; no text committed |
| Flag reference | synthetic op streams + censuses | clean/alias/desync status retained |
| Runtime correlation | synthetic RAM/layout profile | candidate scoring, no-match and ambiguity behavior |
| Actor slot reuse | scripted synthetic epochs | new live identity after reuse |
| Overlay transition | synthetic/runtime metadata | old live claims expire on generation/hash change |
| Project round trip | metadata-only project | canonical authored state round trips; live/generated excluded |
| TCP compatibility | captured synthetic JSON + runtime tests | old clients/commands unchanged; bounds enforced |
| No proprietary bytes | repository allowlist/content scanner | no discs, sectors, assets, extracted text or overlay bytes |
| Disc gate | CI without environment variable | clean skip/pass with actionable message |
| Metadata regression | handcrafted synthetic structures only | deterministic claims without Sony content |

All tests requiring the game read a user-provided `LEGAIA_DISC_BIN`, validate its existence/identity and skip cleanly when unset. They never copy disc content into temp paths inside tracked trees or snapshot decoded dialogue.

## Evidence needed before claims

- NPC → actor record: parser record binding.
- Actor record → model: placement field plus scene TMD-pool resolution.
- Actor → movement/interaction: explicit binding/control-flow or runtime trace.
- Interaction → story flags: clean decoded op path and/or live read trace.
- Interaction → MES: explicit operand/data flow and scene MES context and/or runtime dialogue trace.
- Imported actor → live slot: scene epoch plus multiple stable fields; transform proximity alone is insufficient.

## Stop point

After the headless read-only slice is accepted, seek separate approval for any RAM write, live override, project authoring UI, asset addition, serializer/patcher work or generic runtime protocol change.
