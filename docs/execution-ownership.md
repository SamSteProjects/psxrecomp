# Backend-neutral execution ownership

Native registration validity and actual execution ownership are separate.
Invalid native code can correctly fall through to the live-byte interpreter;
the interpreter is then the observed execution owner, not an absence of an
owner.

## Dispatch order

For a dispatch into executable RAM, the runtime attempts:

1. the main statically compiled executable when its live text is native-safe;
2. generated static-overlay dispatch;
3. validated cached-native or runtime-native candidates from the overlay
   loader; and
4. the dirty-RAM interpreter after its executable-admission and decode guards.

Blacklist, byte identity, watched generation, backend eligibility,
differential guards, and per-entry dispatch guards remain fail-closed. A failed
native candidate does not become valid merely because the interpreter can run
the current bytes.

## Observed owners

The lifecycle recorder is called only at the existing backend acquisition
points. Its vocabulary is:

- `static-native` for the main compiled image and generated static overlays;
- `cached-native` for validated cache DLL candidates;
- `runtime-native` for runtime-compiled candidates;
- `interpreter` for the dirty-RAM interpreter;
- `unavailable` when no current observation is safe; and
- `ambiguous`, reserved for evidence that cannot distinguish a backend.

Each record is keyed by exact physical guest PC. It records the last observed
backend, reason, frame, hit count, associated DMA instance when one contains the
PC, and native registration ID when applicable. This is bounded dispatch-level
attribution, not per-instruction tracing.

For interpreter interiors, queries reuse the pre-existing bounded
`g_dirty_ram_exec_pc_table`, which already records every PC the interpreter
executes for overlay capture. The lifecycle work adds the observation frame and
watched generation to that record; it does not create a second instruction
trace.

At observation time the exact PC page is registered with the authoritative
watched-page mechanism and its generation is sampled. A later write makes
`observation_current` false and changes the executable-state token. The record
remains useful as history but must not be presented as current ownership until
a backend executes that PC again. Registration records continue to report
native validity independently.

No backend name is inferred from address proximity or from catalog overlap.

Protocol 1.4 can turn one current exact-PC observation into a bounded execution
witness. The witness hashes only the exact four-byte instruction span and keeps
backend ownership separate from native registration validity. See
`execution-witness-model.md`.
