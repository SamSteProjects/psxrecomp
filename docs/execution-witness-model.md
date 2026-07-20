# Execution witness model

An execution witness is bounded evidence that one exact aligned guest PC was
executed by a named backend while a particular four-byte live instruction and
watched-page generation were current. It is not a function, decoded block, or
loaded executable image.

## Authoritative range

The dirty-RAM interpreter does not retain decoded basic blocks. `exec_one`
fetches one four-byte instruction and branches execute their delay-slot
instruction through a separate `exec_one` call. Local flow can cross many basic
blocks inside one dispatch. Consequently the strongest retained range is the
exact executed instruction `[pc, pc + 4)`. The protocol reports
`block_range_available: false`; it never expands the witness to a watched page,
nearby window, assumed function, or overlay.

Native acquisition points use the same exact entry-PC representation. Native
registration validity remains separate: a witness says which backend actually
handled the PC, while registration records say whether a native registration
is eligible.

## Identity and currentness

The runtime retains the instruction word and watched generation at observation.
On query it computes SHA-256 over both the retained four bytes and current live
RAM over that same span. A witness is current only when:

- the exact owner observation remains current under the authoritative watched
  generation;
- the current bytes equal the observed bytes; and
- the owner is not ambiguous.

A same-byte write can leave the SHA-256 unchanged while advancing generation,
so byte and generation identities are both required. Process restart clears all
observations. `witness_id` is process-local and includes range, bytes, backend,
generation, provenance identifiers, and observation epoch; it is not promised
unique or stable across processes. The range/backend/live-hash tuple is the
repeatable structural identity used by revisioned profiles.

## Provenance

When the PC belongs to an active exact DMA fragment or native registration, the
witness reports those identifiers. Null provenance is valid execution evidence:
it means the runtime cannot authoritatively connect the instruction to a larger
image. Adjacent DMA fragments are never joined.

The model performs no guest writes, instruction-history streaming, or control-
flow reconstruction.
