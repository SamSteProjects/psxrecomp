# Actor-observation readiness

Decision: **NOT YET SAFE** to begin one bounded read-only actor traversal.

## Completed prerequisites

- `legaia-na-scus94254-town0c-field-v1` now resolves to a fully validated, revisioned field profile.
- The shared protocol, executable identity, execution-witness, guarded observation, node-prefix and traversal-limit contracts remain fail closed.
- The prior same-process transition report demonstrated old-token rejection, map01 outside-state observation, re-entry witness recovery, a new epoch, and zero actor-node requests, zero actor bytes, and zero RAM writes.
- The world-map A/B harness is bounded, metadata-only, target-validated, and has synthetic coverage for repeat aggregation, idle versus modest polling, counter deltas, failed target rejection, and privacy.

## Outstanding gates

1. Repeat `town0c -> map01 -> town0c` in a **fresh** runtime process using the revisioned profile, two compatible initial samples, ten subsequent stable samples, explicit old-token rejection, ten stable re-entry samples, final guard validation, and frame progress.
2. Run the state-equivalent map01 A/B cases. If polling materially changes the result, reduce or redesign observer cadence before traversal.
3. Confirm the fresh run still has an accepted actor-list-head locator and current witnesses. Address reuse is never actor identity.

No actor-node prefix was requested in this phase, no actor snapshot was emitted, and no imported/runtime correlation was attempted. Even after a future `SAFE TO BEGIN ONE BOUNDED READ-ONLY ACTOR TRAVERSAL` decision, correlating observed nodes to imported town actors remains a separate, later approval.

A fresh debug-server process was probed only at boot/menu to validate protocol and
executable identity; that is explicitly not a substitute for the required retail
town0c transition.
