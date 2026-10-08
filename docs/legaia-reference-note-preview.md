# Reference Note Pitch Preview

In a source bank’s **Edit bank parameters** inspector, select a tone’s ADSR, center or fine-shift field. Load a qualified envelope sample, select **Native ADPCM loop** or **Native ADPCM one pass**, load the native bytes, then select **Native Gaussian preview**. Choose **Reference note model**, an explicit base sample rate and a note key from 0 through 127. Play and WAV export use the existing bounded envelope/sample pipeline, stereo register gains and independently controlled monitor volume.

The selected layer supplies its exact encoded center and shift bytes. Shift is interpreted as signed8 cents by this reference model. Retail and Current tuning stay separate. Reviewed Proposed carries reviewed edits, with Current sample bytes for envelope/tuning proposals. Unreviewed parameter drafts are excluded. Center/shift proposals now expose the same audition as ADSR proposals; reviewing, discarding or changing the owning tone clears/requalifies the audition through the existing lifecycle.

The model is based on `compute_pitch` in the intended pinned Andrew reference `d6e64c68ede25813d35db20980da82a1a025549b`, `crates/engine-audio/src/vab_bind.rs`:

```
fine_cents = signed8(encoded_shift)
semitones = note_key - encoded_center - fine_cents / 100
pitch = round(4096 * chosen_base_rate / 44100 * 2 ** (semitones / 12))
reference_step = clamp(pitch, 1, 16384)
```

The reference implementation chooses 22050 Hz historically, because VAB headers do not supply per-sample rates. This editor requires you to choose a base rate; it never promotes that reference assumption to imported metadata or actual game pitch. Its reference result can reach `0x4000`, while the existing direct Gaussian renderer accepts only `0..0x3FFF`. Such a result remains visible and rendering is refused; it is not silently reduced to fit. Ordinary preset and direct-register paths retain their existing arithmetic and defaults.

This is a one-voice preview model. It does not resolve native driver rounding/tables, SEQ program/tone ownership, pitch-bend/controller state, hardware parity, runtime residency, velocity/pan/reverb or the complete game mix. Sample/loop ownership, source hash, allocation bounds and preview limits remain enforced. Changing a note, rate, layer or mode stops playing audio. Blank/fractional/out-of-range keys refuse rendering; closing or stale ownership releases native sample buffers and audio resources. Export names identify the assumed note/base rate, selected layer, center/shift bytes and resulting pitch register. No authored/native/project data changes.

## Offline Checks

Seven focused Node suites passed: note-pitch model/UI, direct pitch, envelope audition, native Gaussian, envelope counters, ADSR fields and bank authoring. Literal note cases cover unity, octaves, chosen base rate, signed fine shifts, minimum and reference maximum, malformed operands and layer ownership. The UI test verifies complete output samples against the selected explicit pitch, stops on changes and withdraws stale ownership. The direct-pitch regression matched 32 native oracle cases / 3,969,000 frames; the Gaussian regression matched 81,920 native tap results and 1,102,500 counter samples. Three editor-module syntax checks, server AST and scoped diff checks passed.

Actual private Retail carrier0877 loop and one-pass workflows passed Retail/Current/reviewed Proposed note preview, explicit base-rate selection, malformed/capped-key refusal, parameter/selection changes stopping playback, Discard reset and WAV export. Four complete Proposed WAVs matched independent Python note math, the existing native C sample oracle and literal fast-ADSR counters exactly. The note formula is reference-qualified; the sample render is compared against the native oracle. Neither proves actual driver note pitch, hardware parity or audible/gameplay acceptance. Wide and 400 px captures were inspected. Project document/history/files/native entry/Build key stayed unchanged and Open matched; no game-launch requests or page errors occurred, and owned helpers terminated. No native Build, installation, runtime attachment or full-disc export ran.

The final expanded browser pass also verified reviewed center+12 and encoded shift255 (signed −1 cent) proposals for both loop and one-pass samples, exact displayed reference registers, enabled preview and Discard/reset without state changes. Passing extended evidence is in `local-output/sdk-20260909/audio-note-pitch-20261007/qualified-tuning/`.

Evidence is retained in `local-output/sdk-20260909/audio-note-pitch-20261007/`, including complete WAV/PCM readback, browser captures and source-preservation proof. Full audio driver/mix and manual gameplay verification remain unfinished; the full SDK goal remains active.
