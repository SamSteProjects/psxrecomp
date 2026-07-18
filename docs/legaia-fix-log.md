# Legend of Legaia Fix Log

This is a user-visible regression log for the Legaia recompile. A fix is
recorded here only after it has been rebuilt and exercised in-game.

## 2026-07-17 — Healing Leaf and spirit-action deadlock fixed

**Status:** verified in the first battle tutorial.

**Symptom:** using Healing Leaf froze or crashed the game. Spirit actions hit
the same failure class. The final run report showed execution repeatedly
entering `CdStateMachine_SeekAndPlaySequence` (`0x8003D764`) and then stalling
inside libcd's synchronous `VSync` wait.

**Root cause:** `interrupts_service_scheduled_events()` returned immediately
while `in_exception` was set. Legaia's CD/XA callback can call `VSync` from an
exception-handler context. Guest cycles therefore continued to advance, but no
VBlank edge was scheduled and the guest frame counter never advanced, leaving
the callback's `VSync` wait unsatisfiable.

**Fix:** scheduled VBlank edges now continue to be produced while an exception
handler is active. This does not force nested interrupt dispatch: delivery
remains gated by the guest's COP0 interrupt-enable state and the existing
nested-exception depth and escape guards.

**Verification:** Healing Leaf completed successfully after the rebuilt
runtime. Spirit actions, Hyper Arts, and summons also complete. All four paths
still exhibit lag, which is a separate CD/XA performance issue; this fix
targets correctness and must remain in place while performance is profiled.

## 2026-07-17 — Battle XA audio/animation synchronization fixed

**Status:** verified with normal attacks, combos, Spirit, Hyper Arts, and a
summon. A small summon-audio stutter remains under investigation.

**Symptom:** XA audio began well before the corresponding battle animation.
Increasing XA sector speed shortened the delay but overflowed the SPU CD ring
and dropped Hyper Art audio, proving that sector acceleration was not a valid
fix.

**Root cause:** the CD model delayed presentation of a response to the CPU
interrupt controller, but exposed the controller's `irq_flag` and response FIFO
immediately. Legaia's libcd callback polls the controller directly. It therefore
saw responses for commands it had just issued and recursively consumed the XA
seek/play state machine inside one exception instead of returning to the battle
loop between responses. Function-level profiling isolated 77.5% of the
audio-to-animation delay window to exception context, led by the libcd
interrupt decoder/poll path at `0x8005C4AC`, `CD_cw`, `CdControlF`, and
`CdStateMachine_SeekAndPlaySequence`.

**Fix:** with `PSX_CD_RESPONSE_VISIBILITY_DELAY=1`, the controller IRQ reason
and response FIFO remain hidden until the already-modeled 5,000-cycle response
presentation delay expires. Sector cadence, XA decoding, SPU buffering,
controller acknowledgement, and INTC delivery are unchanged. Each asynchronous
command response now arrives after the callback has returned, matching the
state machine's intended scheduling.

**Verification:** attack and combo animation/audio are smooth and synchronized;
Spirit, Hyper Arts, and summons are synchronized and complete with normal
`PSX_XA_ACTION_SPEED=1`. The speed-2 experiment remains diagnostic-only and
must not be enabled for normal testing.

## 2026-07-17 — Back-to-back Hyper Art XA audio fixed

**Status:** verified with a combo containing two Hyper Arts. Both animations
and their audio executed correctly.

**Symptom:** when a combo contained multiple Hyper Arts, the later art could
lose its XA audio even though its animation and SPU sound effects continued.
The problem affected multiple characters and depended on the art's position in
the combo rather than its identity.

**Root cause:** Legaia correctly issued `SetMode`, `Setloc`, `SetFilter`, and
`ReadS` for the later XA clip. It then polled `GetlocL` to decide whether the
stream had reached its ending sector. After `SeekL` completed, the runtime
continued reporting the final sector from the previous stream. Legaia
therefore believed the new clip was already past its endpoint and issued
`Pause` in the same frame, before any of its XA sectors could be decoded.

**Fix:** completing `SeekL` or `SeekP` now updates the CD drive's reported
position to the active `SetLoc` target. The next physical sector continues to
replace the complete header and XA subheader through the normal delivery path.
This prevents stale stream position from leaking across back-to-back reads.

**Verification:** a double-Hyper-Art combo that consistently lost the second
clip's audio completed with both Hyper Arts sounding correctly. Four-stage
audio capture also confirmed that XA decoding, SPU mixing, and host delivery
were not dropping the missing cue; the failure occurred before the second
stream began.
