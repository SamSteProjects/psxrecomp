# Executable ownership diagnostics

`executable_catalog` reports the predicates used to explain whether one
dispatch registration currently owns its range. Diagnostic reporting does not
alter dispatch selection or cache invalidation.

## Predicates

A native registration is valid only when its exact live bytes match its source
guard, its watched generation is the generation last validated, the loader and
native backend are enabled, the backend is eligible, and all dispatch guards
pass. `active_owner` additionally requires that it be the first dispatchable
candidate selected at its entry.

The structured reason is the first applicable failure in dispatch order:

| Reason | Meaning |
|---|---|
| `valid` | All predicates pass and the registration is selected. |
| `validated-bytes-mismatch` | Current exact-range bytes differ from the compiled source guard. |
| `generation-invalidated` | The current watched generation has not been revalidated. |
| `registration-inactive` | The overlay loader is inactive. |
| `shadowed` | Another valid candidate owns the entry. |
| `blacklisted` | Correctness policy has blacklisted the candidate. |
| `native-disabled` | Native overlay execution is disabled. |
| `dispatch-guard-failed` | A blocklist or differential guard prevents native execution. |
| `backend-ineligible` | The candidate cannot safely use its backend, including device-touch exclusions. |
| `unknown` | Metadata cannot establish a more specific reason. |

Same-byte writes may advance watched generations even when the later live hash
is unchanged. Different bytes loaded at the same base and length cannot retain
the former registration's ownership: generation and exact byte guards fail
closed until the appropriate candidate is revalidated.

## Comparability

Registration source CRC and live SHA-256 are comparable only because both cover
the same ordered exact guest ranges. Algorithm differences do not change the
byte domain. Image-level captured-cache CRCs may cover a broader image and are
therefore marked non-comparable to a child registration's live identity.

`registration_time_validated_identity` is null until the registration has
actually passed validation. Static registrations retain that validation
history after later invalidation, while current ownership remains false.

## Execution ownership

`execution_owner` is an exact-PC, last-observed backend record and does not
replace the native predicates above. Its `observation_current` flag compares
the authoritative watched generation sampled at dispatch with the current
generation. A mutation can therefore make a formerly observed native or
interpreter backend stale without inventing a replacement owner. The next real
dispatch records the backend that actually acquires the PC.

See [Backend-neutral execution ownership](execution-ownership.md).
