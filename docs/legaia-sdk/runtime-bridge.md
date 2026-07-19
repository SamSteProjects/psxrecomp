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

## Proposed generic protocol extensions

No extensions are implemented in Phase 0. Add only those proven necessary by the contract spike.

### `protocol_info`

Returns bounded server metadata and commands/capabilities, avoiding version guessing:

```json
{
  "id": 1, "ok": true,
  "protocol": {"name": "psxrecomp-debug", "major": 1, "minor": 0},
  "runtime": {"build_id": "...", "backend": "native"},
  "limits": {"max_read_ram": 2097152, "max_vram_pixels": 16384, "max_batch_regions": 32},
  "capabilities": ["read_ram", "overlay_identity", "memory_regions"]
}
```

Additive fields and a new command preserve existing clients.

### `memory_regions`

Returns a bounded list of generic mapped guest ranges and roles (`main_ram`, `scratchpad`, `bios`, `mmio`), not Legaia concepts. This lets clients validate requests.

### `overlay_identity`

Returns only the currently active executable/code ranges known by the generic loader: address, length, content digest, backend, capture/installation generation and frame. It must not return overlay bytes. This is the canonical input to game-specific correlation.

### `read_regions`

A bounded atomic-ish safe-point batch read:

```json
{"id": 4, "cmd": "read_regions", "regions": [{"tag":"scene","addr":"0x...","len":16},{"tag":"actors","addr":"0x...","len":4096}]}
```

The response repeats one frame/cycle stamp and returns tagged hex blocks. Limits cap region count and total bytes. Existing `read_ram` remains unchanged.

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
