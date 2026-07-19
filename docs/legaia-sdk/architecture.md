# Legaia SDK architecture and boundaries

## Architectural decision

Keep three systems and two explicit bridges:

```text
user-supplied disc
        |
        v
legend-of-legaia-re semantic provider --versioned JSON--> Legaia SDK project model
                                                            |
PSXRecomp runtime <---------------JSON/TCP runtime bridge----+
                                                            |
                                                     future editor/API
```

There is no direct dependency from PSXRecomp's execution loop to the clean-room engine, and no dependency from legend-of-legaia-re to generated MIPS-to-C output. The future editor talks to the SDK model, never directly treats live RAM as authored state.

## Ownership boundary

| Owner | Belongs here | Does not belong here |
|---|---|---|
| Generic PSXRecomp | MIPS translation, generated-code ABI, PS1 memory/hardware, dispatch, overlay capture/load, interpreter fallback, generic TCP diagnostics | Legaia scene names, actor layouts, story flags, MES semantics |
| PSXRecomp Legaia integration (`integrations/legaia/`) | manifests, schemas, semantic-provider adapter, runtime correlation profiles, project model, generated non-proprietary symbol/provenance metadata | copied clean-room engine, extracted game content, hardware special cases |
| legend-of-legaia-re | typed disc/asset parsers, scene interpretation, VMs, semantic rendering, patching knowledge, clean-room research and provenance | generated recomp C, PSXRecomp dispatch internals, SDK authored project truth |
| Future editor | viewport/selection, Inspector, dialogue UX, commands, undo/redo, user workflows | raw parser logic, retail RAM ownership, hardware emulation |
| Game-specific configuration | disc/revision identities, named scene aliases, retail layout profiles, symbol-map versions | generic runtime logic |
| Semantic schemas | versioned DTOs, IDs, claims, evidence, state layers | proprietary payload bytes or extracted text |
| Generated artifacts | reproducible JSON indexes, symbol/provenance maps, build reports, hashes | source-of-truth authored edits |
| Extracted user data | local decoded assets and caches derived from the user's disc | Git, release archives, telemetry uploads |
| Runtime-only state | RAM/register/VRAM snapshots, active overlay/scene epoch, traces, actor-slot observations | project persistence unless explicitly captured as evidence metadata |

## Directory policy

The Phase 0 docs establish this intended isolated root:

```text
integrations/legaia/
  README.md
  config/          # revision/layout profiles; no user disc data
  symbols/         # generated factual maps with source revision
  schemas/         # versioned JSON Schema or equivalent
  provenance/      # non-proprietary evidence manifests
  bridge/          # semantic-provider and TCP clients
  project-model/   # authored/imported/derived/live/generated types
  generated/       # ignored local build/import results
```

Exact implementation directories remain subject to review after the first contract spike. `external/legend-of-legaia-re/` is intentionally not created in Phase 0.

## Dependency strategy

| Mechanism | Evaluation | Decision |
|---|---|---|
| Git submodule | Reproducible source pin, but adds a second large runtime/toolchain and suggests in-process coupling | Defer; acceptable later for developer convenience, not required at PSXRecomp runtime |
| Cargo git dependency | Good Rust types and performance, but binds SDK release/build to upstream internals and pulls a broad workspace graph | Do not use initially; reconsider after DTO stability |
| C ABI / Rust-C FFI | Low per-call overhead but high ownership/error/toolchain complexity; unnecessary for read-only import | Reject for initial work |
| Subprocess | Strong process/license/failure isolation; can invoke a pinned `legaia-sdk-export`-style command | Recommended initial semantic boundary |
| TCP | Already canonical and safe-pointed in PSXRecomp | Required initial runtime boundary |
| Generated JSON | Human/debuggable, schema-versionable, language-neutral | Recommended semantic snapshot, project and provenance interchange |
| TOML | Good for small human-authored config; poor for large claim graphs | Use for project/config entrypoints, not bulk scene graphs |
| Generated schemas | Enables compatibility testing and independent releases | Required |
| Symbol/provenance records | Natural metadata-only boundary | Required; include source commit/profile |
| Shared files on disk | Suitable for local user caches and large meshes if content-addressed | Allowed behind manifest, hashes and ignore rules |

The initial provider should emit bounded/versioned JSON metadata and optionally content-addressed local mesh buffers. It should never emit extracted dialogue into tracked fixtures. A provider executable can come from an independently built/released legend-of-legaia-re checkout; PSXRecomp does not compile or link it to execute a game.

## Public integration contracts

1. **Semantic provider contract**: input is user disc path plus scene selector; output is provider/schema version, disc identity, imported scene graph, raw-span locators, semantic claims and diagnostics.
2. **Runtime bridge contract**: input is launch/connect configuration and generic TCP commands; output is session capabilities and timestamped/epoch-scoped observations.
3. **Project contract**: authored overlays reference imported semantic IDs; imported snapshots are immutable/reimportable; derived claims are recomputable; live state is ephemeral.
4. **Build contract**: consumes an authored project plus a verified import snapshot and emits a report/artifact. PS1 patch and extended-native are separate targets.

## Extension rules

- Prefer a generic TCP command when the information is useful across games (memory maps, loaded executable ranges, overlay hash/range, process capabilities).
- Put Legaia interpretation in a named extension/profile, not `debug_server.c` conditionals. A generic command may return raw bounded memory plus epoch metadata; the bridge interprets it with a revisioned Legaia layout profile.
- Never add game-specific branches to hardware timing, GPU, DMA, CD-ROM, IRQ, BIOS, generated dispatch or interpreter fallback for editor convenience.
- Never make a runtime address, Ghidra label, catalog index or inferred display name the sole semantic identity.
- Never upgrade an inference because the editor requires a value. Unknown and contradictory are valid model states.

## Lifecycle

1. Verify disc identity locally.
2. Ask the semantic provider to import one scene and create immutable imported state plus claims.
3. Overlay authored project changes without mutating the imported snapshot.
4. Launch/connect PSXRecomp and negotiate protocol capabilities.
5. Observe current scene/overlay epoch and actor candidates.
6. Correlate candidates, recording evidence and confidence; show imported and live state side-by-side.
7. Disconnect without changing authored state.
8. Later, an explicit preview transaction may apply reversible live overrides; build/export remains a separate operation.

## Legal and clean-room boundary

- No disc image, sector, executable bytes, assets, extracted text, overlay bytes or generated proprietary game code is added by this integration.
- User-data/cache directories must be ignored before extraction is implemented.
- Only factual metadata necessary for interoperability (addresses, sizes, hashes, names, record layouts) is proposed for generated maps, with provenance and license review.
- Clean-room Rust code must never receive translated/decompiled MIPS-to-C output. PSXRecomp must never absorb the clean-room runtime wholesale.
- Both upstream licenses and attribution remain intact. This design is not an opinion on commercial redistribution rights.

## Rejected Phase 0 designs

- Linking the entire Rust clean-room engine into the PSXRecomp runtime.
- Copying parser crates into this repository.
- A shared mutable in-process world/ECS spanning both runtimes.
- Using retail RAM as project persistence.
- Building the final editor UI before stable semantic and runtime contracts.
- Embedding Legaia-specific scene or actor logic in generic PSX hardware handlers.
