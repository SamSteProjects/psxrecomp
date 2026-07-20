# Executable image lifecycle

PSXRecomp records process-local executable-image evidence at authoritative
runtime events. The initial lifecycle source is a completed post-game CD-ROM
DMA transfer into bounded main RAM. One transfer creates one
`dma-load-fragment` instance with an exact capture base, length, CRC32, frame,
and process-local sequence. Adjacent transfers are never grouped by proximity.

A later transfer that overlaps an active instance supersedes it and links the
old and new instance IDs. Same-address and same-length reloads still create new
instances, including same-byte reloads. This makes lifecycle identity distinct
from content identity.

The runtime has no generic authoritative unload event today. An instance stays
active until an observed overlapping transfer supersedes it. The protocol does
not infer unload from inactivity, a missing native registration, a scene
transition, or a catalog scan.

## Identity domains

| Identity | Byte domain | Comparison rule |
|---|---|---|
| Immutable source | Input/cache domain known by a loader or compiler | Compare only to the same documented source domain. |
| Capture | Exact bytes of one completed DMA transfer | Compare to the same exact span only. |
| Registration-time validated | Ordered exact dispatch-registration ranges | Compare to current bytes over those same ranges. |
| Current live | Current guest RAM over the record's exact documented span | Never substitute a source or generated-code hash. |
| Execution-owner observation | Backend selected at one exact guest PC | This is backend evidence, not a byte identity. |

The DMA capture is not claimed to be a whole overlay, executable segment, or
decompression output. `whole_image_identity` and transformed-source identity
remain null until another authoritative event supplies those relationships.

## Bounds and lifetime

Instances are retained in a 32,768-record process-local table. Execution-owner
observations use a 65,536-entry exact-PC table. Lifecycle events use a
4,096-entry ring and expose its oldest and latest retained sequences. Overflow
is sticky and visible; consumers must fail closed when complete evidence is
required.

Instrumentation is observational. It does not change dispatch priority,
validation, emulation semantics, or guest memory. Its hot-path attribution is
disabled until a client negotiates `protocol_info` or directly requests the
lifecycle command. The response reports `tracking_started_frame`; evidence
before that frame is intentionally unavailable rather than reconstructed.

An execution witness may link to one of these exact fragments when the
instruction lies inside it. A null link remains valid execution evidence and
must not be expanded by joining adjacent fragments or guessing a whole image.
