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

## Remaining transition gate

A transition-only state machine and manual `--transition-watch` CLI now prove
old-token rejection, stable outside sampling, and re-entry stabilization in
synthetic tests without actor reads. Retail acceptance remains pending: fresh
New Game has a story-locked south gate, while the available memory-card save
loads a later transformed Rim Elm revision rather than the accepted `town01`
profile. Synthetic coverage is not a substitute for the normal live
transition. Retail actor-node traversal remains disabled until the transition
gate is completed. See `scene-transition-acceptance.md`.
