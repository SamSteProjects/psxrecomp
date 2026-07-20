# Scene-transition acceptance

Status: implementation and synthetic validation complete; retail exit/re-entry
acceptance pending a compatible normal-game save.

## Scope

The transition watcher proves that a settled `town01` scoped epoch cannot be
reused after a normal scene transition and that returning to `town01` creates a
new stable observer epoch. It never traverses the actor list, reads a `0x9C`
node prefix, emits an actor snapshot, or writes guest RAM.

The command is:

```powershell
python integrations/legaia/tools/legaia_observe.py `
  --transition-watch `
  --profile integrations/legaia/layouts/scus94254-na-field-v1.json `
  --output "<local-output>\town01-transition.json"
```

Manual navigation is intentional. Once the initial epoch is established, the
operator exits and re-enters `town01` through ordinary controller input while
the watcher samples at no more than 10 Hz. There is no force, ignore, scan, or
write option.

## State machine

The accepted sequence is:

```text
waiting_for_initial_town01
  -> stabilizing_initial_epoch
  -> initial_epoch_stable
  -> waiting_for_exit
  -> old_epoch_invalidated
  -> outside_town01
  -> waiting_for_reentry
  -> stabilizing_new_epoch
  -> new_epoch_stable
  -> completed
```

Every wait and stabilization phase is bounded. Failure records the last safe
structural sample in the diagnostic instead of continuing indefinitely.

Initial and re-entry epochs require two compatible boundary samples, at least
ten further stable guard samples, and a final guard-only verification. Exit
requires a stable profile-relevant incompatibility and explicit rejection of
the original expected token. Frame advancement and process-global executable
token churn are diagnostic only and cannot prove an exit.

Outside `town01`, only the profile-declared scene-name, PROT-base, master-mode,
and actor-head guard ranges are read. Two consecutive samples must agree and
each request must have stable frame and executable-state boundaries. The
town01 profile is not treated as selected while its signals or witnesses are
incompatible.

## Token and actor-head semantics

The guard token and runtime-instance identity are process-local. Same-process
re-entry must retain the runtime instance but produce a guard token different
from the initial town01 epoch. A fresh process must receive a different runtime
identity; tokens are not compared for equality across processes.

The actor-list-head address may change or be reused after re-entry. Either is
reported as structural metadata. Reuse does not imply that any semantic actor
survived the transition.

## Synthetic validation

On 2026-07-19, 35 transition tests passed. They cover scene, PROT, mode, head,
witness, runtime, token, frame, and before/after boundary behavior; stable
outside sampling; re-entry; timeouts; navigation cleanup; metadata privacy;
and explicit zero actor-read/write behavior. Fixtures contain only synthetic
addresses, identities, and bytes.

## Retail status

A freshly built `RelWithDebInfo` runtime launched successfully and exposed
`psxrecomp-debug` 1.5. Normal Load-menu testing found a valid local memory-card
save, but it loads a later transformed Rim Elm scene rather than the accepted
`town01` revision. Fresh New Game reaches `town01`, but its south gate is
story-locked; arbitrary directional input therefore cannot provide a valid
normal exit/re-entry proof.

No RAM write, save-state injection, teleport, actor-node read, or profile
weakening was used to bypass that gate. Retail transition acceptance remains
open until a normal `town01` save with the south gate accessible is supplied.
The live acceptance output will remain outside the repository.

## Remaining gate

Retail actor traversal stays disabled. After same-process exit/re-entry and a
second fresh-process repeat pass, bounded guarded traversal can be considered
as a separately approved phase. Imported/runtime correlation remains later
work even after traversal is enabled.
