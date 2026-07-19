# SCUS-94254 field runtime-layout research

Status: read-only research baseline for `town01`, 2026-07-18.

Profile: `legaia-na-scus94254-field-v1` (schema version 1).

This pass identifies runtime structures needed by a later observer. It does not connect Legaia Trace to a runtime, enumerate actors live, correlate imported actors, or authorize guest writes.

## Revision boundary

The profile applies only to the North American `SCUS-94254` executable whose ISO9660 file is 442,368 bytes and has SHA-256 `292256e2e66db42727f613406785e444254d3f699569e611f65fcf1c6d2f3482`. The executable loads at `0x80010000` with a `0x6B800` text image. These values were independently checked from the user-supplied supported disc without retaining its path or bytes.

Field/town mode loads PROT entry 897 at slot-A base `0x801CE818`. The local source entry is 325,632 bytes with SHA-256 `216f846db5ab085a295cef4064747380a06c995caa3e1b2773e78a1d349f126b`. That source-entry hash is not yet a canonical hash of the active loaded overlay: the entry contains more than the slot-A head and overlay-local virtual addresses alias other modes. The profile consequently leaves `content_sha256` unresolved and refuses live selection until the runtime can report a canonical overlay identity.

## Evidence inventory

PSXRecomp-side evidence inspected:

- `legaia-release/game.toml`: serial, load address, entry PC and text size;
- `TCP_COMMANDS.md`, `runtime/src/debug_server.c`, `runtime/include/debug_server.h`: bounded `read_ram`, frame-ring reads, watches/write traces, overlay diagnostics and main-thread send budget;
- `runtime/src/overlay_loader.c`, `runtime/src/overlay_capture.c`, `runtime/src/memory.c`: content/generation validation exists for compiled overlay candidates, but is not exposed as a canonical active-overlay identity;
- `docs/legaia-sdk/architecture.md`, `provenance-model.md`, `runtime-bridge.md`, `project-schema.md` and accepted importer/model contracts;
- a local metadata-only extraction of the SCUS executable identity and bounded disassembly of `FUN_8003A1E4`, `FUN_8003A55C`, `FUN_8002519C`, `FUN_80020454` and `FUN_800204A4`.

The local SCUS disassembly independently confirms:

- `FUN_8003A1E4` reads the MAN pointer global at `0x8007B898`;
- `FUN_8003A55C` reads the field buffer pointer at scratchpad `0x1F8003EC`;
- `FUN_8002519C` traverses nodes through `+0x00`, reads flags at `+0x10`, position/state words at `+0x14/+0x18`, and an object-table pointer at `+0x44`;
- `FUN_80020454` and `FUN_800204A4` manipulate intrusive list-link records and the stack index at `0x8007C348`, confirming linked storage/reuse rather than a contiguous actor array.

Attributed Andrew reference evidence at commit `d6e64c68ede25813d35db20980da82a1a025549b`:

- `docs/reference/memory-map.md`: scene/mode globals and actor list-head family;
- `docs/reference/functions.md`: SCUS and field-overlay function ownership;
- `docs/subsystems/asset-loader.md`: named transition packet and scene-name lifecycle;
- `docs/subsystems/boot.md`: modes 2/3 and field overlay 0897;
- `docs/subsystems/field-locomotion.md`: collision census, rebuild function, node fields and interaction lifecycle;
- `docs/subsystems/actor-vm.md`, `move-vm.md`, `anm.md`: class-dependent record fields;
- `scripts/pcsx-redux/autorun_s5_actors.lua`, `walk_actor_lists.py` and `crates/engine-shell/tests/field_collision_discriminator.rs`: capture-backed field observations.

Andrew's clean-room `World::actors` collections and host traits were inspected only for semantic context; they are not retail RAM evidence.

No generated game C, executable bytes, overlay bytes, RAM dumps, save states or captures are committed.

## Active-scene identity

No one signal is accepted alone. A settled `town01` observation requires all of the following in two boundary samples:

| Signal | Address | Width | Required value | Owner | Confidence | Risk if used alone |
|---|---:|---:|---:|---|---|---|
| Active scene name | `0x80084548` | 8 bytes | `town01\0` | SCUS | Confirmed | Can contain pending/transition state. |
| Runtime PROT base | `0x80084540` | u16 | `3` | SCUS | Confirmed | Numeric value is meaningful only in the correct build and CDNAME numbering space. |
| Master game mode | `0x8007B83C` | u16 | `3` | SCUS | Confirmed | Identifies field-run, not a particular scene. |
| Active overlay | `0x801CE818` slot A | identity | field 0897 | overlay loader | Strongly Inferred | A bare address aliases multiple overlays. Canonical live hash is missing. |
| Executable | build identity | identity | supported hash | runtime/host | Confirmed locally | Serial alone does not distinguish revisions. |

`0x8007050C` is the pending/mirror scene-name buffer. It is useful as a transition signal but is not accepted as the active scene by itself. `0x80084540 = 3` is the retail/CDNAME value; the importer converts that to extraction-frame start 1. Mixing those numbering spaces is a known off-by-two failure mode.

## Scene-transition lifecycle and epochs

`FUN_8001FD44` stages a named transition, updates the name buffers and spawns the transition-streaming actor. `FUN_80021934` drives a five-state load sequence and eventually selects mode 2. Mode 2 loads/initializes field overlay 0897 and the scene resources; the initializer hands off to mode 3. During this interval actor pointers, counts and scripts are not safe to interpret as a settled scene.

An epoch is observer-owned and never written to guest RAM. Its token contains:

```text
(observer_epoch, profile_id, scene_name, prot_base, executable_id,
 overlay_id, actor_list_head, actor_census_base, first_stable_frame)
```

The observer samples identity before and after the bounded actor read. It discards the snapshot if the scene name, PROT base, mode, overlay identity, list head, census base or frame boundary contract changes. It increments its own epoch only after two agreeing boundary samples. Reusing the same node address in a later epoch never preserves actor identity.

## Actor storage model

The retail model is not `actor_base + slot * stride`.

- `0x8007C354` is the field actor linked-list head used by field collision/motion paths. It belongs to a wider multi-list actor system whose heads occupy nearby SCUS globals.
- Nodes are individually allocated/relinked. `FUN_80020454`/`FUN_800204A4` operate intrusive link records and the free-stack index at `0x8007C348`.
- Field overlay `FUN_801CF754` rebuilds a collision/interaction candidate census at `0x801C93C8` every frame. It walks the live list, culls to approximately `±0x180` around the player, skips nodes with `flags & 3 != 0`, and caps the census at 32 pointers.
- `0x8007B6B8` is the field census count when the field overlay/mode gate is satisfied. Capture-backed tests read it as u32. An older probe reads u8, and world-map documentation assigns mode-dependent behavior at the same address; the profile uses u32 but keeps the ownership claim Strongly Inferred.

The pointer-census stride is confirmed as 4 bytes and the maximum is 32. The actor-node allocation size, a contiguous actor stride and a fixed actor-storage base are unknown. The profile permits a bounded `0x9C`-byte prefix read from each validated pointer because the final exposed field is the four-byte collision link at `+0x98`.

The census is deliberately not called the complete actor table. It omits distant and disabled actors, may contain only one NPC in a settled `town01` interaction capture, and does not imply that all 52 imported MAN placements have persistent runtime nodes.

## Actor field map

| Offset | Width | Profile name | Meaning | Observation | Correlation | Confidence |
|---:|---:|---|---|---|---|---|
| `+0x00` | 4 | `next_actor` | intrusive next pointer | Safe | Unsafe | Confirmed |
| `+0x0C` | 4 | `tick_function` | SCUS/overlay tick function | Conditional | Supporting | Confirmed |
| `+0x10` | 4 | `flags` | class/lifecycle bitfield | Safe per traced bit | Supporting | Confirmed |
| `+0x14` | 2 | `position_x` | signed world X | Safe | Supporting | Confirmed |
| `+0x16` | 2 | `position_y` | signed world Y | Safe | Weak | Confirmed |
| `+0x18` | 2 | `position_z` | signed world Z | Safe | Supporting | Confirmed |
| `+0x26` | 2 | `heading_yaw` | 4096 units/revolution | Safe | Weak | Confirmed |
| `+0x2A` | 2 | `touch_counter` | interaction counter | Conditional | Unsafe | Strongly Inferred |
| `+0x44` | 4 | `model_object_table_pointer` | object-table pointer | Conditional | Supporting | Confirmed |
| `+0x4C` | 4 | `animation_record_pointer` | animation-bank pointer | Conditional | Supporting | Confirmed |
| `+0x50` | 2 | `field_0x50` | bind index or class state | Conditional | Unsafe | Contradictory |
| `+0x5A` | 2 | `saved_heading` | interaction save/restore | Conditional | Unsafe | Strongly Inferred |
| `+0x60` | 1 | `map_object_record_index` | `.MAP` object index for static-object subclass | Conditional | Unsafe for MAN | Confirmed, subclass-scoped |
| `+0x64` | 2 | `map_object_model_pool_index` | scene TMD pool for `.MAP` object subclass | Conditional | Supporting | Confirmed, subclass-scoped |
| `+0x90` | 4 | `field_script_pointer` | class-dependent script pointer | Conditional | Supporting | Strongly Inferred |
| `+0x94` | 4 | `field_0x94` | VM cursor, encounter pointer or effect channel | Conditional | Unsafe | Contradictory |
| `+0x98` | 4 | `collision_partner_pointer` | transient mutual link | Safe | Unsafe | Confirmed |

“Safe” means safe to read after pointer/range validation; it does not mean safe to interpret outside the documented actor class. Model and script pointers are ephemeral runtime locators, not stable asset identities and never exported payloads.

No evidence currently supports a runtime `man_record_index` for MAN NPC nodes. `.MAP` object index `+0x60` must not be relabelled as one. Likewise, `.MAP` model pool `+0x64` must not be projected onto MAN NPCs without a writer trace.

## Lifecycle findings

- Initialization: `FUN_8003A1E4` walks MAN placements and pre-runs spawn prologues; `FUN_8003A55C` creates field-map object actors; `FUN_80020DE0` is a generic descriptor-driven actor allocator.
- Update: `FUN_8002519C` walks generic actor nodes; `FUN_8003BC08` services field motion/AI list members; overlay `FUN_801CF754` rebuilds the nearby collision census.
- Disable: field census inclusion rejects `flags & 3 != 0`; specific flag meanings beyond traced bits remain class-dependent.
- Reuse/destruction: intrusive list links are returned/reused by `FUN_800204A4`/`FUN_80020454`. Exact actor allocation teardown, stale contents, and same-scene node-address reuse remain unresolved.
- Coverage: player, NPC, props, effects and transition/system actors use related node layouts but do not share every field semantic. The collision census is filtered and incomplete by design.

## Contradictory and unresolved evidence

- `0x8007B6B8` is read as u32 by capture-backed field tests, u8 by an older Lua probe, and has a different world-map description. The profile gates it to field overlay 0897/mode 3 and records Strongly Inferred width/ownership.
- `+0x50` is reported as a bind-record index by collision code and a generic state field by an older probe. It remains neutral.
- `+0x94` has multiple proven subclass meanings. It remains neutral and Contradictory.
- The 0897 PROT source-entry hash is not a live-overlay hash. No address claim in the overlay window may be used until this is resolved.
- Exact allocator block size, actor-node allocation base, complete list membership, runtime MAN record identity, MAN-NPC model selector, animation-ID mapping and teardown generation are unknown.

## Observation safety recommendation

The profile and bounds model are ready for a later observer implementation, but actual live actor observation is not yet safe with the current native capability surface because fail-closed overlay selection cannot be completed. A small, generic, separately approved protocol addition should expose protocol version, executable identity and canonical active-overlay identity/hash; an atomic-ish bounded `read_regions` or a frame token around reads is also strongly recommended.

Once those generic capabilities exist, poll identity at no more than 10 Hz, read at most 4 KiB per request, normally read only the 128-byte pointer census plus validated `0x9C` prefixes, and check frame/epoch boundaries. Never poll full RAM. Actor correlation remains premature.
