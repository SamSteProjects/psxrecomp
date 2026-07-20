# town0c runtime profile

Status: revisioned profile and synthetic validation complete; a second fresh-process retail transition remains an acceptance prerequisite.

`integrations/legaia/layouts/scus94254-na-town0c-field-v1.json` is the revisioned selection document for the normal post-map01 Rim Elm state. Its resolved profile ID is `legaia-na-scus94254-town0c-field-v1`. It uses a same-directory, single-hop metadata-only base reference to the existing field profile; the loader resolves and validates the complete resulting document before an observer can use it. This avoids a second divergent copy of the shared executable, witness, guard, node-prefix, and safety contract.

## Promoted evidence

The prior transition-only report was metadata-only and read no actor nodes.

| Property | Accepted value | Basis |
|---|---|---|
| Scene name | `town0c` | guarded initial and re-entry samples |
| Runtime PROT base | `21` | guarded initial and re-entry samples |
| Master mode | `3` | guarded initial and re-entry samples |
| Actor-list-head locator | `0x8007C354` | inherited accepted field contract; only its four-byte locator is guarded |
| Node prefix bound | `0x9C` / 156 bytes | inherited accepted structural bound; not read in this phase |
| Runtime identity | SCUS-94254 `ps-x-exe-body` SHA-256 identity | protocol-validated shared executable contract |
| Protocol | `psxrecomp-debug` 1.5+ | native implementation plus existing required capabilities |
| Witness set | collision rebuild (interpreter), VM dispatch and actor helper (static-native) | exact four-byte current, generation-matched witnesses |

The observed `town0c -> map01 -> town0c` run had thirteen stable samples at each town epoch, rejected the old expected token in the intervening `map01` state, and created a distinct observer epoch. The state fingerprint itself returned to its earlier value, which is valid because it is a fingerprint, not a nonce. The actor-list-head locator was reused; that is structural metadata, not evidence that an actor persisted.

## Guard and transition contract

The profile retains the profile-derived observation guard: scene name, PROT base, master mode, the `0x8007C354` head locator, and all required witnesses. Every selection requires current witness ownership/backend/range/live identity and watched-generation agreement before and after a bounded read. A process restart changes runtime process identity; a same-process re-entry must reject the old token before a new observer epoch can be established.

No process-local guard token, RAM content, host path, actor bytes, disc bytes, or save state appears in the profile.

## Unresolved fields

- There is no authoritative whole-image identity for the field overlay; the profile therefore continues to rely on current generation-matched execution witnesses rather than pretending that the source-entry digest is live-image identity.
- List membership, allocation size, node reuse semantics, and node-to-import identity remain unresolved.
- A fresh-process retail transition must pass before any separately approved bounded node-prefix read. This phase does not read a node prefix.
