# Encoded PCM looping in envelope audition

The bank parameter editor's envelope sample audition now offers One pass and
Encoded PCM loop playback. The default remains One pass. Looping becomes
available only after the selected Retail or Current sample passes the existing
source, entry, PCM hash and waveform-bin checks and its decoded prefix has an
explicit encoded loop-start and final end/repeat block. No start point or repeat
behavior is guessed for a budget-limited prefix, missing marker or one-shot end.

## Ownership and playback

`editor/audio-pcm-loop.js` qualifies ordered block markers and decoded extents.
The last loop-start before the terminating end/repeat block owns the loop range;
an end/repeat/start block can supply a one-block loop. The intro plays once, then
the decoded PCM range repeats. Linear resampling interpolates across the last
frame back to the loop start. The existing 44.1 kHz integer envelope applies
through explicit key-off and Release, within the same bounded output window.

Retail uses qualified Retail PCM. Current and Reviewed Proposed envelopes use
qualified Current PCM, preserving existing native sample/WAV ownership. An
unreviewed local envelope is excluded. Layer, rate, key-off and playback changes
stop the active audition; source/tone changes and close withdraw its bytes.
Loop mode resets when its source disappears or a new tone/review is loaded.
Loop WAV filenames include `encoded-pcm-loop`; one-pass filenames stay compatible.

This repeats already decoded PCM. It does not re-decode native ADPCM predictor
history at a wrap, infer driver pitch, use Gaussian filtering, establish live
voice behavior or reproduce the game mix. The product UI states that boundary.
No project format, authoring command, native serializer or runtime code changes.

The flag interpretation follows the pinned Andrew reference
`d6e64c68ede25813d35db20980da82a1a025549b`,
`crates/engine-audio/src/spu/adpcm.rs` (`BlockFlags`), and the current runtime's
`runtime/src/spu.c` loop-start latch and end/repeat traversal. The local reference
checkout's HEAD has advanced; the intended pin was read explicitly without
changing it. Those sources justify encoded marker interpretation, not equality
between repeated PCM and native ADPCM decoding over subsequent passes.

## Acceptance

Eight affected client suites and three JavaScript syntax checks passed. Focused
literal checks cover last-start ownership, one-block loops, intro, wrap
interpolation, fast and stationary Release, immutable PCM, one-pass fallback,
malformed flags/markers/extents and bounded output. Existing audition checks
retain stale-entry, late-response, stop/close and layer ownership coverage.

The actual private bank editor exercised PROT 0877, packed tone page 4/record 0,
sample index 3 (displayed sample 4). Qualified encoded frames 16940–19851 form its
loop. Retail, Current and Reviewed Proposed each played/stopped and exported both
modes, producing six bounded mono 44.1 kHz, 16-bit WAVs. Changing playback mode
stopped playback. Discard withdrew the proposal. Current retained WAV sample 0,
whose end has no repeat flag, kept looping disabled. Wide and 400 px layouts were
inspected with no overflow, page errors or game requests. The first browser
attempt used a disabled-option assertion that did not read its DOM property;
the corrected check and original failure evidence are both retained.

Independent Python readback verified headers/extents of all six WAVs and every
Proposed loop output sample from literal fast-attack counters, the frozen Release
case and separately constructed source indexing. One-pass output becomes silent
after its decoded source; the loop output continues. Proposed loop WAV SHA-256:
`c15bcff8edb1ac741f840fd82d65f35abd3ecf4b0bd118d4a49167bd9d4672d5`.

Project document/history, active scene, saved bytes and Build input key remained
exact; Save/Open preserved the complete Current native entry SHA-256
`2763446be4afa339ba8e6a10266e9216a96162608138e2f7f635894c37a60b40`.
No new native Build or full regression campaign was needed for this private
preview feature. No game was launched or attached, package installed or full
disc exported. Native audio/gameplay verification remains deferred.

Private evidence: `local-output/sdk-20260909/audio-pcm-loop-20261007/` contains
fresh fixtures, client logs, browser proof, six WAVs, complete PCM/native-entry
readback, screenshots and the private project. Development stays solo and the
full SDK goal remains active.
