# Export Complete SEQ Tracks as MIDI

The sequence inspector and operand editor can download complete decoded SEQ
tracks as Standard MIDI File format 0. This supports external inspection of
encoded music data without changing the project or applying an operand draft.

## Workflow

1. Open an Audio asset and choose **Inspect sequence events**.
2. Choose **Export source MIDI…** to download its decoded retail source.
3. Open **Edit sequence operands…** for separate **Export Retail MIDI…** and
   **Export Current MIDI…** controls.
4. Review an operand draft, then choose **Export Proposed MIDI…** to download
   the reviewed proposal. Export does not Apply it. Discard withdraws this export.

Current exports include effective saved operand changes. Unreviewed fields do
not affect any download. Proposed export uses fresh native proposed inspection
and the existing source/authoring ownership guards. Closing the editor or
changing its project/source invalidates pending work.

## Format and Limits

The exporter preserves event order, channel statuses and operands, delta ticks,
PPQN, initial tempo, declared time signature and encoded tempo changes. It writes
one MTrk with explicit channel statuses and standard meta-event lengths. Explicit
statuses avoid relying on SEQ running-status behavior across meta events.

Initial tempo and time signature appear at tick zero. The time-signature
metronome and notation fields use conventional values of 24 and 8; these two
fields are export conventions because the SEQ header does not declare them.
See the [Standard MIDI File specification text](https://midimusic.github.io/tech/midispec.html)
and [Mido's MIDI file documentation](https://mido.github.io/mido/files/midi.html).

Export requires a complete decoded track with its own encoded end-of-track.
Partial or unresolved prefixes refuse export; no ending or unknown events are
invented. Undecoded trailing bytes are not exported. PPQN must be 1–32767,
delta ticks at most 0x0fffffff, cumulative ticks at most 0x7fffffff, decoded
events at most 32768 and track bytes at most 512 KiB. Malformed identity,
timing, channel or operand values also refuse.

Program/bank/controller operands remain literal encoded values. General MIDI
instrument mapping, game bank resolution and synthesized audio are not supplied.
This is not a game playback, runtime cadence or external DAW compatibility
qualification. MIDI import is not implemented by this feature.

## Offline Checks Passed — 2026-10-07

Ten focused Python source/authoring tests passed with retail input and no skips.
Four Node suites covered the MIDI encoder, source decoder, authoring ownership
and a freshly qualified moved-carrier fixture with nine forged-layout refusals.
Three changed JavaScript modules passed syntax checks; the server passed AST
validation. Literal complete-file bytes and an independent binary reader checked
headers, meta lengths, all channel families, VLQ boundaries and exact ticks.

Actual private Town01 browser workflows at 1400/400 px downloaded Source,
Retail, Current and reviewed Proposed files. Readback matched native headers,
event ticks and operands; Source equaled Retail, and Current/Proposed reflected
their respective changes. Partial asset 1045 refused Source/Retail/Current
export. Discard disabled Proposed export. Fresh moved-carrier Retail/Current/
Proposed downloads also matched native inspections.

Complete project documents, history and file snapshots remained unchanged.
No page errors or Run/command requests occurred; owned browser/server helpers
terminated. No native Build, game, runtime attachment, installation or disc
export occurred. Gameplay remains deferred and the full SDK goal remains active.

Private evidence is under
`local-output/sdk-20260909/audio-midi-export-20261007/final/`; the root retains
the earlier harness failure after successful downloads, caused by attempting
to close an already closed asset-details panel. The final harness checks that
panel's visibility before closing it.
