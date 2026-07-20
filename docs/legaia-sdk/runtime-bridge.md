# Runtime bridge design

## Decision

Use PSXRecomp’s existing localhost JSON-over-newline TCP server first. Do not introduce Rust/C FFI. The SDK bridge is an out-of-process client/orchestrator; it interprets generic runtime observations using revisioned Legaia layout profiles.

## Existing protocol

Request and response shapes are already documented in `TCP_COMMANDS.md`:

```json
{"id": 1, "cmd": "read_ram", "addr": "0x80080000", "len": 256}
{"id": 1, "ok": true, "addr": "0x80080000", "len": 256, "hex": "..."}
```

The native server lives in `runtime/src/debug_server.c`, is polled at emulation safe points, and has bounded send behavior. The Beetle implementation in `runtime/src/beetle_debug_server.c` and DuckStation patch provide parity surfaces for overlapping commands.

## Launch and connect

Proposed bridge launch configuration:

```toml
[runtime]
executable = "path/to/legaia-runtime"
game_config = "path/to/game.toml"
working_directory = "path/to/local-user-runtime"
host = "127.0.0.1"
port = 4370
startup_timeout_ms = 30000
```

Launch steps:

1. Validate executable/config paths and ensure working output directories are local/ignored.
2. Spawn the runtime with its normal `--game` configuration and configured debug port; do not alter release behavior.
3. Poll `ping` with bounded exponential backoff.
4. Negotiate capabilities (initially via known command/version profile; add `protocol_info` below).
5. Record runtime binary/config hashes and initial frame/registers as session metadata.
6. On exit, retain only opted-in metadata and ignored local diagnostics.

Successful startup means TCP accepted a request, `ping.ok == true`, the frame is observable, and the server capability/version is compatible—not merely that a process exists.

## Existing command coverage

| SDK need | Existing command(s) | Assessment |
|---|---|---|
| Startup/liveness | `ping`, `frame`, freeze heartbeat telemetry | sufficient; handshake metadata missing |
| Pause/continue | `pause`, `continue` | sufficient |
| Step/run | `step`, `run_to_frame` | sufficient |
| Registers | `get_registers` | sufficient |
| RAM read/write | `read_ram`, `write_ram`, `read_frame_ram` | sufficient for spike; typed/batched reads desirable |
| Snapshots | `set_snapshot`, `get_snapshots`, frame history | sufficient |
| Memory watches | `watch`, `unwatch`, `wtrace_arm/disarm/dump/stats`, `rtrace_*` | strong |
| Write/function traces | `wtrace_*`, `fntrace_*`, `dispatch_*`, `cyc_watch*` | strong, responses must stay bounded |
| VRAM | `vram_peek` (`read_vram` on oracle), `screenshot` | sufficient |
| GPU | `gpu_state`, `gpu_frame_dump`, `gpu_ring_stats`, `gp1_dump` | sufficient |
| DMA/IRQ | `dma_state`, `dma_trace_*`, `irq_state`, `imask_trace` | sufficient |
| Overlay | `overlay_dump`, `overlay_loader_status`, `overlay_candidates`, `overlay_native_ring`, `overlay_capture_dump` | data exists; canonical active identity missing |
| Scene | raw RAM plus symbols only | missing canonical/generic mechanism |
| Controller | `set_input`, `press`, `clear_input`, `pad_status` | sufficient |
| Correlate actor | RAM, watches, traces and overlay data | missing layout profile and batch observation command |
| Compare imported/live | bridge-side comparison | new SDK function, no runtime change required |

## Initial read-only correlation

The first slice uses a game-specific layout profile stored under `integrations/legaia/config/`, not hard-coded handlers. A profile may declare:

- supported disc executable/revision hashes;
- scene-name buffer or scene ID observation and validation rule;
- actor table base/pointer discovery evidence;
- slot count/stride and typed field offsets;
- model/animation/script pointer fields;
- overlay ranges and symbol-map revision;
- invariants used to reject false candidates.

Correlation algorithm:

1. Pause at a safe point and capture frame/registers.
2. Obtain current overlay identity and derive a scene epoch.
3. Read the scene marker and actor table in a bounded snapshot.
4. Decode live candidates under the exact layout profile.
5. Score imported actor ↔ candidate claims using independently useful fields: scene, model/animation references, transform proximity, script/record pointer, spawn order and traces.
6. Record all candidates and scores/evidence; do not force a match below policy threshold.
7. Resume only if the bridge paused the runtime.

Actor-slot reuse starts a new live identity when occupancy generation, scene epoch, actor handle/pointer generation, or discriminating fields indicate replacement.

## Implemented generic observer prerequisites

Protocol 1.3 implements the generic capabilities proven necessary by the layout
contract. The native server advertises `protocol_info`, `runtime_identity`,
`executable_catalog`, `executable_image_lifecycle`, `executable_regions`, `read_regions`, and
`watched_page_generation`.

- `protocol_info` returns the protocol version, explicit server kind, sorted
  capability tokens, limits, and frame. A client rejects an unsupported major
  and requires every profile capability.
- `runtime_identity` returns safe runtime/build metadata, BIOS SHA-256, and the
  canonical main-executable source identity when registered. It returns no host
  paths or executable bytes.
- `executable_regions` pages the main executable and actual static, native-DLL,
  or runtime-compiled registrations. Immutable source identity, current live
  guest-memory SHA-256, authoritative page-generation digest, and conservative
  native validity are separate fields.
- `executable_catalog` provides token-bound views of image groups, structural
  ranges, and registrations, with explicit source/live comparability,
  registration-time validation, and ownership failure reasons.
- `executable_lifecycle` provides exact DMA capture instances, supersession
  links, bounded lifecycle events, and exact-PC backend observations. A last
  owner becomes non-current after its watched generation changes.
- `read_regions` reads up to 32 ordered main-RAM ranges, 4 KiB each and 16 KiB
  total, with frame-before/after and executable-state-before/after stamps.

The ownership token is derived from watched generations for exact executable
registration pages and loader registration state; it is not a Legaia counter.
A same-byte write may change the token while the final live hash remains
unchanged. Different contents at the same address and length cannot retain
stale native ownership. A separate structural catalog token binds pagination.

Beetle and DuckStation advertise only `read_ram` and `read_regions`; their
responses include frame stamps but omit executable-state fields. The
DuckStation patch was regenerated against pinned upstream commit
`ffb33c281d196eb8ee0f559085ca285de7cdd51b`. Neither oracle backend is assumed
to know PSXRecomp native ownership. Missing identity is never treated as a wildcard.

See `docs/debug-protocol-versioning.md`, `docs/executable-identity.md`, and
`docs/read-regions-command.md` for the wire contracts and performance limits.

### Game extension mechanism (only if raw profiles prove insufficient)

Prefer bridge-side interpretation. If runtime-only knowledge is unavoidable, add a registry/namespace such as `ext.legaia.scene_state` compiled only into a Legaia game target, never a title check in generic dispatch. Extension responses still use the same envelope, limits and documentation requirements.

## Missing Legaia-specific knowledge, not generic commands

- Exact retail actor table discovery and layouts per executable/overlay revision.
- Reliable current-scene marker and transition semantics.
- Mapping between MAN placement/record and runtime actor allocation.
- Model/animation/script pointer interpretation across scene variants.
- Slot reuse and dynamically allocated actor generation signals.
- MES/dialogue runtime buffer and context mapping.

These require evidence from symbol maps, code, bounded RAM observations and traces. They must not be “solved” with temporary printf logging.

## Compatibility and safety

- One request produces one structured response; large data uses bounded paging or existing file-dump variants.
- New fields are additive and unknown commands remain a normal error.
- A protocol-major mismatch blocks mutation; the read-only bridge may degrade only when required capabilities remain present.
- Writes are disabled by default in the SDK. Future preview writes require an explicit transaction, captured original bytes, range allowlist and rollback attempt.
- Never write MMIO or code/overlay memory through editor operations without a separately reviewed capability.
- All responses include enough frame/generation metadata to detect a transition during observation.

## Verification

- Golden request/response tests for new handlers and old commands.
- Existing `tools/debug_client.py` remains functional.
- Native and oracle schemas stay parallel where both implement a command.
- Bounds, malformed JSON, disconnect and slow-client behavior are tested.
- A metadata-only Legaia test uses synthetic RAM/layout fixtures; disc-gated live tests require `LEGAIA_DISC_BIN` and skip cleanly.

## Runtime-layout research result

The first revisioned profile now lives at `integrations/legaia/layouts/scus94254-na-field-v1.json`; see `runtime-layout-research.md` and `runtime-layout-profile.md`.

The research changes the proposed actor read from a contiguous table read to a bounded pointer-census read. Retail field actors are linked, individually allocated nodes. Field overlay 0897 rebuilds a filtered, 32-pointer collision census each frame; its four-byte entries are not actor records and its indices are not identity. A future observer should read the 128-byte census, validate each pointer, then read only the documented `0x9C`-byte node prefix.

The generic transport prerequisites now exist. A later observer can negotiate
protocol 1.2, verify program identity, enumerate executable registrations, and
discard mixed frame/executable-state snapshots. The checked-in profile still
refuses live selection while overlay 0897's canonical live range/hash is
unresolved. Resolving and accepting that evidence is the next prerequisite; it
is not permission to traverse actors or correlate imported records. No
Legaia-specific command or runtime hook has been added.

The protocol 1.2 pass confirmed bounded complete paging and explained duplicate
static structural variants, but it did not clear the overlay gate. In stable
town01, records covering field code were not source-matching native owners, and
the researched overlay base was not an authoritative loaded-image event. The
next prerequisite is evidence for the real generic image lifecycle/identity,
not actor traversal. See `field-overlay-0897-identity.md`.
