# Direct SPU pitch in offline envelope audition

Envelope sample audition now offers Preview rate (the default) or Direct SPU
register in qualified native Gaussian loop and one-pass modes. Direct register
accepts integer values 0 through 16383. The native source counter advances by
that value per 44.1 kHz output frame, with 4096 representing unity. Effective
source rate is shown as register × 44100 / 4096; it is a counter rate, not a
sample header or inferred retail note pitch. Zero holds the source counter and
Gaussian phase. It is never coerced to unity and need not mean silent output.

Load the qualified PCM prefix, choose a supported native playback mode, then
load its complete verified ADPCM bytes. Gaussian interpolation enables the
pitch-source control. Direct mode does not require selecting a rate preset.
The five existing presets retain their values, quantization, output bytes and
metadata. Linear/PCM modes return to the existing preset workflow.

Retail, Current and Reviewed Proposed use their separately qualified sample and
ADSR layers. Register changes stop active playback; invalid, fractional, blank
and out-of-range values disable playback and WAV export. Mode/layer/review changes
retain the existing ownership, cache, cancellation and stale-source guards.
Review changes reset to preset mode, unity register and the original unloaded
mode. Direct pitch is a transient preview choice; it does not author tone data.

WAV output remains 44.1 kHz signed16 mono at full preview level. Direct-register
filenames carry `pitch-<register>`, distinct from preset `Hz` labels. Playback
volume remains local and defaults to 20 percent. Native one-pass END silences
source output after the terminating block; native loops retain predictor and
previous-block interpolation history. The displayed ADSR counter model is the
existing offline approximation, not a complete native voice, driver or game mix.

Direct Gaussian rendering shares the existing decoder and interpolation engine.
The original `decodeNativeLoop` limit remains 240001 source frames. The separate
`decodeNativePitchLoop` entry point permits at most 882001 frames, enough for
five output seconds at maximum pitch plus the next source tap. Raw ADPCM stays
bounded to 65536 bytes and output stays bounded to 220500 mono frames. Register
validation rejects upper bits rather than silently masking user input.

The native runtime supplies the 14-bit pitch mask, zero-hold and block-boundary
phase rules (`runtime/src/spu.c`) and unchanged Gaussian header. The intended
Andrew reference remains `d6e64c68ede25813d35db20980da82a1a025549b`; its
`crates/engine-audio/src/vab_bind.rs` uses an inferred 22.05 kHz base for note
tuning. This control does not adopt that inference or the checkout's newer
revision. Program/tone selection, note-to-register mapping, tuning, bend,
modulation, instruments, scheduling and full sequence mixing remain incomplete.

## Offline acceptance, 2026-10-07

Nine affected client suites and three module syntax checks passed. The new
native comparison covers 32 freshly qualified Retail/Current loop and one-pass
cases: 3,969,000 output samples at registers 0, 1, 1024, 3072, 4096, 8192, 16382
and 16383. Maximum pitch runs through the full five-second output budget.
Inputs remain immutable and all five rate presets retain exact metadata and
output. Client ownership, loaded-byte guards, invalid input, register/filter
stop, reset and stale-source withdrawal passed.

The compiled standalone oracle includes the unchanged native `decode_block`
body and Gaussian header, with native phase stepping and one-pass END mute.
It does not run a game or establish complete voice/driver timing. Actual PROT
0877 tone page 4 record 0 (sample 4) and page 13 record 2 (sample 1) passed
Retail/Current/Reviewed Proposed editor audition, direct playback without a rate
preset, strict input controls, register/filter/discard stopping, close and
wide/400 px layouts with no page errors or game launch requests. Wide and narrow
screenshots were inspected.

Six complete Proposed WAVs at zero, unity and maximum pitch matched native
source output shaped by independently stated ADSR counter levels. The project
document, history, active scene, saved file, complete native audio entry and
Build input key remained exact; reopening retained the same document and audio.
Native entry SHA-256: `2763446be4afa339ba8e6a10266e9216a96162608138e2f7f635894c37a60b40`.
Private evidence: `local-output/sdk-20260909/audio-direct-pitch-20261007/`.

No backend/serializer/runtime change, new Build, full campaign, game launch,
runtime attachment, installation or full-disc export was needed. Development
stays solo. Gameplay/audio listening stays deferred; the full SDK goal is active.
