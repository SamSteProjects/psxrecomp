# Encoded Channel State

The source sequence inspector and sequence operand editor share a channel-state view. Selecting a channel event focuses its encoded channel; selecting a meta event retains the explicit channel choice. With no prior choice, a meta event asks the user to choose a channel.

The view reports the last encoded program, controller, raw 14-bit pitch-wheel, channel-pressure and per-key-pressure write through the selected event, inclusive. Each value includes its originating event index and SEQ-relative byte offset. Unseen fields remain **Unknown**. Only controllers and pressure keys with encoded writes appear as additional rows.

Retail, Current and reviewed Proposed occupy separate columns. Proposed requires the existing independently decoded native-review report; local operand drafts cannot populate it. Review now requests that report even when note timelines are hidden. Discard, changed source context, Refresh and parent close withdraw the appropriate state. Pending operations lock channel selection.

This is a derived editor view over existing qualified sequence metadata, not a sequence interpreter. The shared calculation preserves encoded event order, including equal-tick writes, and isolates channels 0–15. Pitch-wheel bytes combine as `LSB + 128 * MSB`; zero and 16383 remain literal values. It does not assume a default program, pitch-wheel center, pressure or controller value. Controller 121 is recorded as an encoded write and does not clear other displayed values.

No sustain, controller-mode/reset semantics, bend range, instrument ownership, voice allocation, scheduler, driver state or gameplay result is inferred. Declared sequence timing remains separate from observed playback. Partial decoded sources are labeled; no state beyond their decoded events is fabricated. This feature adds no project mutation, runtime operation, native format, import or export.

Implementation: `integrations/legaia/editor/audio-channel-state.js`, integrated by both sequence editors, with one static server alias. The pure bounded service returns detached state; existing source/current/proposal decoders remain the authority for native ownership and source identity.

## Verification

Focused checks cover inclusive same-tick ordering, channel isolation, program/pressure/pitch zero, 14-bit pitch maximum, repeated writes, literal controller-reset handling, unknown values, malformed and bounded prefixes, partial-source labeling, detached results and UI selection/clear/busy/dispose behavior. Existing source, operand-authoring, note-timeline and moved-carrier qualification suites also pass. These checks establish editor behavior; manual gameplay and driver equivalence remain unverified.

Private carrier0877 browser and preservation evidence is retained under `local-output/sdk-20260909/audio-channel-state-20261007/`. The first harness expected a stale child status after the owning source dialog had correctly disposed that child; its failure is retained. The corrected qualification checks parent withdrawal rather than requiring the disposed child to stay visible.

The corrected `qualified/` workflow passed actual carrier0877 controller 10/channel 12/event 5: Retail and Current 64 versus independently decoded Proposed 65, pending locks, Discard and parent/stale disposal. All 16 Current channel states matched a separate Python calculation. Wide and 400-pixel screenshots were visually inspected. Complete project document, history, saved-file sizes/timestamps, native entry bytes and authored Build key stayed unchanged; Open matched. No page errors or command/Build/Run requests occurred; browser and server helpers terminated. Current entry SHA-256: `2763446be4afa339ba8e6a10266e9216a96162608138e2f7f635894c37a60b40`.
