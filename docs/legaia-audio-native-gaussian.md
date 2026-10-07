# Native Gaussian envelope sample preview

In the bank parameter editor, select a qualified tone and envelope layer, load
its sample, then choose Native ADPCM loop and load the native bytes. Envelope
native interpolation now offers Native Gaussian preview. Linear remains the
default. Gaussian is available only for the already supported complete,
standard-shift native loops; one-pass and repeated PCM previews retain their
existing linear behavior.

The preview uses the exact 512-entry table and four-tap arithmetic from
`runtime/include/spu_gauss.h`. Initial preceding samples are zero. Previous
decoded samples survive block and loop boundaries, while ADPCM predictor
history also continues. Products are summed, shifted once and cast to signed16
as in the recomp. Signed envelope multiplication uses an arithmetic right shift.

The sample rate remains an explicit user choice. Gaussian preview rounds it to
`pitch = round(rate * 4096 / 44100)`, then advances the native fractional phase
counter. Index stepping stops at each 28-sample block boundary and carries
remaining phase into the next block, matching the recomp path. The editor shows
the requested rate, register and effective rate. For example, requested 48000 Hz
uses pitch 4458 and effective rate 47997.509765625 Hz. No note, tone center or
driver pitch assignment is inferred.

Retail, Current and Reviewed Proposed reuse the existing source-qualified
sample ownership and envelope word layers. Changing interpolation halts
playback. Missing native bytes, changed inputs, cleared proposals and closed
inspectors withdraw the option through the existing cache/disposal guards.
WAV output is bounded mono signed16 at 44100 Hz and names Gaussian explicitly.
Playback volume remains separate from the full-level exported WAV.

## Offline acceptance, 2026-10-07

A standalone C++ oracle compiled the unchanged native Gaussian header and
unchanged `decode_block` function. All 81920 checked tap results matched across
every fractional phase, extreme/mixed signed samples and history boundaries.
Every one of 1102500 decoded/Gaussian samples matched across Retail and Current
native loops at all five supported rates. This verifies interpolation and pitch
counter behavior; it does not establish hardware or whole-game audio parity.

Seven focused client suites and two syntax checks passed. The new controller
check also compared every sample sent to Web Audio with the Gaussian renderer,
verified explicit native loading, mode availability, interpolation-change stop,
clear/reset and stale withdrawal. Existing native loop, PCM, envelope, ADSR and
sample audition behavior stayed green.

The actual muted retail editor exercised Retail, Current and Reviewed Proposed
native Gaussian playback and six WAV downloads at requested 44100/48000 Hz.
Both complete Proposed WAVs independently matched native Gaussian output times
the previously accepted literal counter trajectory. Gaussian output differed
from the linear preview. Wide and 400 px screenshots were inspected without
horizontal dialog overflow or page errors. Project documents, history, saved
files, Build input key and the complete Current native audio entry stayed exact.

Current native entry SHA-256:
`2763446be4afa339ba8e6a10266e9216a96162608138e2f7f635894c37a60b40`.
Proposed Gaussian 44100 Hz WAV SHA-256:
`d0691e940d1649f208ea069365c755f2405a5363634d9973fb7d211857d8090b`.
Proposed Gaussian 48000 Hz WAV SHA-256:
`fc7ba8b66494c7fd3ef2f8e835187086e7467d70dbbf592b97d00f6a5bb0ae86`.

Private evidence:
`local-output/sdk-20260909/audio-native-gaussian-20261007/`.
This is an offline sample/envelope diagnostic, using the existing envelope
counter model rather than claiming the whole native voice update schedule.
Instrument resolution, pitch bend, modulation, noise, voices, mixing, reverb,
driver transformations and audible gameplay acceptance remain open. No native
runtime source changed, no new mod Build or full campaign was required, and no
game launch, attachment, install or disc export occurred. Development stays solo;
gameplay verification stays deferred and the full SDK goal remains active.
