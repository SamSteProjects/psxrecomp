# Scene-transition acceptance

Status: implementation, synthetic validation, and one same-process retail
`town0c -> map01 -> town0c` acceptance pass complete.

## Scope

The transition watcher proves that a settled profiled-scene epoch becomes
invalid during a normal scene transition and that returning creates a new
observer-owned epoch. It never traverses the actor list, reads a `0x9C`
node prefix, emits an actor snapshot, or writes guest RAM.

The command is:

```powershell
python integrations/legaia/tools/legaia_observe.py `
  --transition-watch `
  --profile integrations/legaia/layouts/scus94254-na-field-v1.json `
  --output "<local-output>\town01-transition.json"
```

Manual navigation is intentional. Once the initial epoch is established, the
operator exits and re-enters the profiled scene through ordinary controller input while
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

Outside the profiled scene, only the profile-declared scene-name, PROT-base, master-mode,
and actor-head guard ranges are read. Two consecutive samples must agree and
each request must have stable frame and executable-state boundaries. The
town01 profile is not treated as selected while its signals or witnesses are
incompatible.

## Token and actor-head semantics

The guard token and runtime-instance identity are process-local. Same-process
re-entry must retain the runtime instance and create a new observer-owned epoch.
The scoped guard token is a state fingerprint, not an epoch nonce: it may return
to its earlier value when the same guarded bytes and execution identities are
restored. Such reuse is accepted only after the old expected token was observed
failing closed in a stable intervening state. A fresh process must receive a
different runtime identity; tokens are not compared for equality across
processes.

The actor-list-head address may change or be reused after re-entry. Either is
reported as structural metadata. Reuse does not imply that any semantic actor
survived the transition.

## Synthetic validation

On 2026-07-20, 36 transition tests passed. They cover scene, PROT, mode, head,
witness, runtime, token, frame, and before/after boundary behavior; stable
outside sampling; re-entry; timeouts; navigation cleanup; metadata privacy;
and explicit zero actor-read/write behavior. Fixtures contain only synthetic
addresses, identities, and bytes.

## Retail status

A fresh `RelWithDebInfo` runtime exposed `psxrecomp-debug` 1.5 and loaded the
user's memory-card slot 1, save 1. The save established that Rim Elm's lifecycle
is asymmetric: the one-time night departure scene is `town01`; after leaving
through `map01`, normal later entry resolves to `town0c`. Requiring a symmetric
`town01` return was therefore an invalid game-lifecycle assumption.

A metadata-only research profile then selected settled `town0c` using scene
name `town0c`, runtime PROT base 21, master mode 3, the bounded actor-head guard,
the supported SCUS executable, and the three accepted field witnesses. The
normal controller-driven `town0c -> map01 -> town0c` pass completed with:

- 13 stable samples for both the initial and re-entry epochs;
- explicit rejection of the old expected token on exit;
- a stable non-town scene signal (`map01`);
- a new observer-owned epoch on return;
- 1,154 bounded observer requests over approximately 107 seconds;
- zero actor-node requests, zero actor bytes, and zero RAM writes; and
- metadata-only output retained outside the repository.

The scoped token returned to its original value after re-entry because every
guarded value returned to the same state. Live evidence therefore corrected the
earlier assumption that this fingerprint must differ. The intervening map state
rejected the token, while the observer sequence produced a distinct epoch; no
stale epoch was accepted.

## Remaining gate

Retail actor traversal stays disabled. The town0c research selection must first
become a reviewed revisioned profile, and a second fresh-process round trip is
still desirable. Bounded guarded traversal can then be considered as a
separately approved phase. Imported/runtime correlation remains later work even
after traversal is enabled.
