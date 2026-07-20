# Scoped scene epoch

The SCUS-94254 field profile now derives its scene-epoch boundary from protocol
1.5's profile-scoped observation guard. The recipe is stored in
`integrations/legaia/layouts/scus94254-na-field-v1.json`; observer code does not
duplicate the addresses.

The guard contains the bounded town01 scene-name signal, runtime PROT base,
master mode, actor-list-head candidate, and all three accepted field execution
witnesses. Runtime process identity and main executable identity are also part
of the server-derived token.

An epoch becomes stable only after the initial guarded signal read and a second
compatible guard sample. Every later node read must carry the same descriptor
and expected token, and a final guard sample must still agree. Any scene signal,
head, required witness bytes/backend/currentness/generation, relevant lifecycle
identity, runtime process, or profile change invalidates the attempt.

The process-global executable and lifecycle tokens remain diagnostic. Their
unrelated changes do not invalidate this scoped epoch.

## Live boundary acceptance

On 2026-07-19, a freshly built native runtime repeatedly reached town01 through
normal input. Across multiple fresh launches, an initial guarded read, one
stabilization sample, and ten subsequent samples retained one scoped token while
frames advanced. The global token changed six or seven times per run. Component
diagnostics attributed the observed churn to the global watched-page and
lifecycle-catalog components; registration state remained stable. Because the
required witnesses and scene signals are members of the unchanged scoped token,
the changing global state was outside the profile-required set.

Each boundary-only pass used 13 protocol requests, read no actor-node bytes,
performed no RAM writes, and completed in approximately 154–333 ms. Runtime
process and scoped tokens changed across fresh launches as designed.

## Transition acceptance

A transition-only state machine and manual `--transition-watch` CLI prove
old-token rejection, stable outside sampling, and re-entry stabilization
without actor reads. Retail evidence established the asymmetric
`town01 -> map01 -> town0c` lifecycle and accepted a normal
`town0c -> map01 -> town0c` round trip. The prior temporary selection is now
represented by the revisioned town0c profile. The scoped state fingerprint returned
to its original value after re-entry, while the intervening map state rejected
it and the observer-owned epoch sequence advanced. Retail actor-node traversal
remains separately gated. See `scene-transition-acceptance.md`.
