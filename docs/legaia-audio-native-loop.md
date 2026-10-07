# Native ADPCM history in envelope audition

The bank parameter editor now offers Native ADPCM loop alongside One pass and
Encoded PCM loop. This option re-decodes the source loop while preserving both
integer predictor history samples. It exposes the difference between repeatedly
playing the first decoded PCM range and decoding subsequent ADPCM passes.

## Source and mode ownership

The editor first loads its existing source-qualified PCM prefix. Native mode
then requires a separate explicit Load of the selected Retail or Current ADPCM
bytes through `/api/audio-sample-adpcm`. The read-only route accepts exact asset,
sample, layer and freshness fields, reconstructs Current native sample ownership,
checks its sample hash, bounds the complete sample to 65536 bytes, and returns
private encoded bytes with the existing qualified waveform and Current entry
hash. Encoded payload is never added to project metadata or tracked assets.

The client compares source/entry/layer identity, canonical encoding and full byte
hash. Its first native decoding pass must match every byte of the already
verified PCM prefix. Missing loop-start/end/repeat markers, unqualified prefixes,
bad predictors/flags, standard-shift violations and stale sources cannot enable
native playback. Retail retains Retail bytes; Current and Reviewed Proposed
envelopes retain Current sample bytes. Unreviewed local envelope drafts remain
excluded. The raw source cache belongs to its sample/layer and is withdrawn on
source, tone or review changes and close. Pending responses cannot revive it.

`editor/audio-native-loop.js` starts with zero predictor history, latches the last
encoded loop-start and continues both history values across end/repeat. Source
frames are decoded on demand within a 240001-frame bound, then linearly resampled
at the user's explicit preview rate and multiplied by the existing bounded
44.1 kHz envelope counter through key-off and Release. Native WAV filenames carry
`native-adpcm-loop`. Playback controls retain explicit Play/Stop and 20% default
volume. Changing layer, rate, key-off or playback mode stops the active source.

## Evidence boundary

Integer block arithmetic and continuous history follow the current runtime's
`runtime/src/spu.c::decode_block`, with source marker interpretation checked
against Andrew's pinned `d6e64c68ede25813d35db20980da82a1a025549b`,
`crates/engine-audio/src/spu/adpcm.rs`. Reserved shifts 13–15 differ between those
implementations: the pinned decoder uses effective shift 9, this runtime clamps
to 12. Native mode therefore accepts standard shifts 0–12 only; the existing
diagnostic prefix/PCM loop behavior and runtime remain unchanged.

This is a native integer ADPCM decoding preview. It does not simulate Gaussian
interpolation, live pitch/register changes, driver transforms, reverb, hardware
voices or the game mix. Native-history decoding does not establish full SPU
synthesis or actual playback cadence. No authoring command, serializer, project
format or runtime source changed.

## Acceptance

All 16 focused Python checks passed without skips; nine affected client suites
and three syntax checks passed.
Source tests reject malformed layer/hash/loop/shift/extent inputs and a source
change during decoding. Four actual HTTP negative requests reject before any
project change. Client checks cover byte hashes, first-pass equality, cache
ownership, pending close, stale source withdrawal and full output bounds.

A standalone fixture executable compiled the exact current runtime
`decode_block` function, preserving its body. IRQ/register scaffolding supports
the function without a game process. Five synthetic predictor cases and fresh
Retail/Current Town01 PROT 0877 sample-index-3 bytes produced 240867 native samples;
the editor decoder matched every sample. Compiler setup failures were retained;
adding the required UCRT DLL search path and correcting scaffold declarations
allowed the final comparison executable to build.

The actual private bank editor exercised packed tone page 4/record 0 and all three
envelope layers, loaded native bytes separately, played/stopped and exported WAVs.
Changing mode stopped playback; Discard withdrew the proposal; the nonrepeat
Current retained WAV sample 0 kept native looping unavailable. Wide and 400 px
layouts were inspected with no overflow, page errors or game requests.

Independent readback matched every Proposed WAV output sample at 44100 and
48000 Hz preview rates against the compiled runtime decoder plus literal
fast-attack/frozen-Release counters. The native-history WAV differs from the
repeated-PCM WAV on this retail sample. Proposed native WAV SHA-256 at 44100 Hz:
`f06beb62be4da7836bfdac710e19ed1a986a186dd998cb89d8a5c0ad49bdf451`.

Project document/history, active scene, saved bytes and Build input key stayed
exact; Save/Open retained the complete Current native entry SHA-256
`2763446be4afa339ba8e6a10266e9216a96162608138e2f7f635894c37a60b40`.
No native package Build or full campaign was repeated. No game was launched or
attached, package installed or full disc exported. Gameplay/audio listening
acceptance remains deferred. Development stays solo and the full goal stays active.

Private evidence: `local-output/sdk-20260909/audio-native-loop-20261007/` contains
the source extraction and compiled oracle, sample fixtures/native output, client
and HTTP checks, browser proof, WAVs, complete readback, screenshots and project.
