# Bounded `read_regions` command

`read_regions` captures several small main-RAM observations at one debug-server
safe point. It performs no guest writes and cannot address scratchpad, BIOS,
MMIO, VRAM, or host memory.

```json
{
  "id": 3,
  "cmd": "read_regions",
  "regions": [
    {"key": "signal_a", "addr": 2148000000, "len": 4},
    {"key": "signal_b", "addr": "0x8007A164", "len": 16}
  ]
}
```

Addresses may be JSON decimal integers or quoted hexadecimal values. They are
folded through the PS1 physical mask and must resolve wholly inside 2-MiB main
RAM. Length must be a positive JSON integer. Address addition is checked before
reading.

Keys are optional. A key is limited to 64 characters from
`A-Z a-z 0-9 _ . : -`. Duplicate supplied keys are rejected; they are never
silently renamed. Response records retain request order.

The response contains:

- `frame_before` and `frame_after`;
- `stable_frame`;
- `executable_state_before` and `executable_state_after`;
- `stable_executable_state`;
- one bounded hexadecimal payload per requested region.

Those executable-state fields are a native capability. Beetle and DuckStation
implement the same bounds, address/key rules, ordering, and frame stamps, but
omit executable-state fields because they cannot expose PSXRecomp's watched-page
and registration ownership semantics. Capability negotiation tells a client
whether the backend is suitable; a revisioned observer that requires executable
stability must reject either oracle response rather than infer stability.

Handlers execute synchronously on the emulation thread at `debug_server_poll`,
so a normal read has identical before/after stamps. Explicit stamps remain part
of the wire contract so clients detect future backend differences and reject a
mixed observation rather than assuming atomicity.

The executable-state token uses watched generations and registration state; it
does not recompute every executable live hash. `executable_regions` performs
the more expensive source/live comparison on demand.

## Limits and failure behavior

- at most 32 regions;
- at most 4,096 bytes per region;
- at most 16,384 bytes total;
- at most 65,536 response bytes;
- one request line and one response line;
- no streaming or partial success.

The whole request fails before reading if any entry is malformed, duplicated,
out of bounds, overflowing, or over budget. Clients must also reject a response
whose frame or executable-state stamps differ.

Polling should remain at or below 10 Hz for layout observation and normally
stay well under the aggregate limit. The debug server runs handlers on the
emulation thread and sends with a bounded main-thread budget; excessive polling
or slow socket draining is observer interference and is visible through the
existing TCP stall telemetry.

Live native acceptance measured small two-region reads at approximately
0.42-2.21 ms (1.76 ms average) with five of five requests stable and normal
frame progression between requests. Negotiation attempted before the emulation
thread reached a safe point may be boundedly dropped or answered busy; external
observers should reconnect with backoff rather than spin or increase polling.

## Protocol 1.5 guarded reads

Native `read_regions` accepts an optional `guard` descriptor. The server derives
the profile-scoped token before and after the payload reads and returns payload
only when the token is valid, stable, and compatible with `expected_token` when
provided. The broader executable-state stamps remain diagnostic and may change
because of unrelated executable activity. Unguarded requests retain the 1.1
contract. See `observation-guard-protocol.md`.
