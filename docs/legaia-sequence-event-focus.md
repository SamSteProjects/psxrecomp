# Reveal Selected Sequence Events in Note Timelines

Source event-table selection and operand-editor event navigation now reveal the
selected event in their encoded note timelines. Opening a timeline also focuses
the currently selected event. Source timeline start/release navigation updates
both the table and the timeline marker.

The white vertical marker represents the exact encoded event tick. Details show
the selected event's index, kind, tick and declared time. Note starts and paired
releases also show their FIFO pairing, key, velocity and ambiguity. Selecting
an event without a paired note clears the old note details and disables note
start/release navigation; tempo, controller and ending events still have markers.

Focus selects the event's existing quarter-note window. If the channel filter
would exclude it, focus resets the filter to All. When more than 512 notes are
visible, a selected visible note participates in the bounded display. Invalid
indices, stale source context and disposed timelines cannot publish selection.
Programmatic focus does not emit a new selection callback.

This remains a read-only encoded-data view. Sustain, instruments, audible
duration and runtime playback are not evaluated. It does not Apply an operand
draft or mutate source data.

## Offline Checks Passed — 2026-10-07

Three existing Node suites passed note-pairing, sequence source/late-response
and operand-authoring/ownership checks. Both changed JavaScript modules passed
syntax checks and the worktree passed whitespace validation.

Actual private Town01 editor checks passed Source start/release/program-event
selection and Retail/Current synchronized focus. A 400 px screenshot was visually
inspected: the dialog fits, labels wrap and the existing timeline scrolls
horizontally. Additional real-browser checks passed selected-note retention past
the 512-note display limit, excluded-channel reset, non-note/end-of-track markers,
invalid/stale/disposed refusal, source immutability and callback isolation.

Complete project document/history/file snapshots remained unchanged. No page
errors or Run/command requests occurred, and owned browser/server helpers
terminated. No native Build, game, runtime attachment, installation or disc
export occurred. Gameplay remains deferred; the full SDK goal remains active.

Private evidence:
`local-output/sdk-20260909/audio-event-focus-20261007/final/`.
