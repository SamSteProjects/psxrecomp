# Native one-pass envelope sample preview

The bank parameter editor now supports complete standard-shift ADPCM samples
whose terminating block has END without REPEAT. Load a qualified envelope
sample, select Native ADPCM one pass, then load its native bytes. Choose the
existing explicit preview rate and either Linear preview or Native Gaussian
preview. Gaussian retains the quantized pitch register/effective-rate display.

The complete terminating block plays. At the next block boundary, output is
forced to silence, following the recomp's END-without-REPEAT envelope mute.
The preview does not decode or play filler after the terminator. Opaque tail
bytes remain inside the full source hash but outside decoded playback. Initial
predictor and Gaussian history are zero; history continues between preceding
blocks. No repeat point or sample rate is guessed.

Native loop and native one-pass availability are distinct. Non-repeating samples
cannot select native looping, and repeating samples cannot select the native
one-pass path. Existing decoded One pass and Encoded PCM loop remain available
under their existing contracts. Gaussian native one-pass uses the recomp's
four-tap arithmetic and fractional pitch/block counter; linear remains a
diagnostic preview rather than a claim of native interpolation parity.

Retail, Current and Reviewed Proposed retain their qualified sample/ADSR layers.
Native bytes require a separate explicit load, exact layer/sample hashes,
Current entry hash and first-pass PCM comparison. Unknown predictors/flags,
reserved shifts, missing END and oversized extents reject. Source changes,
discard/clear and close retain playback/cache withdrawal. Rate/mode/interpolation
changes stop playback. WAV filenames identify native one-pass and Gaussian.

END mute is independent of the displayed envelope trajectory: the existing
counter graph can remain nonzero while the sample output has stopped. This
feature does not claim complete native voice scheduling, driver semantics,
instrument assignment, hardware parity or gameplay audio acceptance.

## Offline acceptance, 2026-10-07

Seventeen focused Python tests passed without skips, including complete
non-repeating source delivery, retained opaque tail, Current/Retail ownership
and existing waveform/sample authoring workflows. Eight focused client suites
and three syntax checks passed. Native-loop and Gaussian regression fixtures
remain green. New checks cover exact native first-pass words, opaque-tail
exclusion, all-rate stopping, mode-specific DTO guards and output silence.

The standalone compiled fixture includes unchanged native `decode_block` and
the unchanged Gaussian header, with the explicit native END-without-REPEAT mute
condition. Every one of 1102500 checked output samples matched across Retail and
Current at five rates. Both complete Proposed WAVs independently matched the
compiled interpolation/mute output times the previously accepted literal
envelope trajectory.

Actual PROT 0877 tone page 13 / record 2, source sample 1, passed Retail, Current
and Reviewed Proposed native one-pass playback, Gaussian/linear switching,
explicit byte loading, six Gaussian WAVs and three linear WAVs. Discard/close
and rate-change stops passed. Wide and 400 px screenshots were inspected without
horizontal dialog overflow, page errors or game launch requests. Project
document/history/saved files, Build inputs and complete Current native entry
stayed exact; reopening the project retained the same bytes.

Current native entry SHA-256:
`2763446be4afa339ba8e6a10266e9216a96162608138e2f7f635894c37a60b40`.
Proposed Gaussian 44100 Hz WAV SHA-256:
`24130dce562c0496cfffee73be1038b6ebc0af5906981212fbaee96cfcfc61f2`.
Proposed Gaussian 48000 Hz WAV SHA-256:
`a258a7375becf6b2535d23a0a4a2095e2f0e01fbc6c8a4d3b566d6600895bc2c`.

Private evidence: `local-output/sdk-20260909/audio-native-one-pass-20261007/`.
No runtime source changed, new mod Build or full campaign was required, and no
game launch, runtime attachment, install or disc export occurred. Development
stays solo; gameplay verification stays deferred and the full SDK goal is active.
