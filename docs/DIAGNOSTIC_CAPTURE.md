# Runtime diagnostic capture

The runtime maintains a bounded, always-on heartbeat ring sampled roughly every
100 ms. It contains recent execution state, CPU state, and small bounded guest
memory diagnostic slices. It does not write to guest RAM or create a save
state.

`psx_freeze_heartbeat.json` is the continuously refreshed view. A severe brief
hitch automatically preserves the same rolling history as
`psx_hitch_report.json`. Longer freezes and fatal errors continue to produce the
larger existing freeze/crash reports.

The latest preserved hitch report overwrites the previous one, so diagnostics
remain bounded. Automatic capture is not armed until the runtime first shows
healthy frame progression, preventing normal frame-zero startup from being
reported as a hitch. The detector re-arms after later healthy progression.

Users can also request a capture with either:

- `Ctrl+F12` on a keyboard.
- `Select+L3+R3` on a controller, including Steam Deck/Proton configurations.

A manual request writes `psx_manual_snapshot.json`, retains one
`psx_manual_snapshot_prev.json`, and asks the heartbeat thread to preserve its
rolling history in `psx_hitch_report.json` within the next sampling tick.
