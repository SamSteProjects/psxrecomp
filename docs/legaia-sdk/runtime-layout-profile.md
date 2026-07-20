# Legaia runtime layout profile contract

The v1 profile is a deterministic, metadata-only description of a supported runtime revision. It is stored at `integrations/legaia/layouts/scus94254-na-field-v1.json` and validated by both JSON Schema and `integrations.legaia.layouts.validator`.

## Identity and selection

`profile_id` is stable and revisioned: `legaia-na-scus94254-field-v1`. Schema version and profile version are separate. An incompatible format change increments `schema_version`; a new executable, overlay layout or materially different field mapping gets a new profile ID/file.

Selection is fail closed. A consumer must match:

1. executable serial and SHA-256;
2. advertised runtime protocol name/version and required capabilities;
3. all required execution witnesses, including backend, exact four-byte range,
   live identity, currentness and watched generation;
4. a stable profile-scoped observation guard;
5. every required scene signal;
6. main-RAM bounds, pointer-census stride and count;
7. scene-epoch boundary samples.

The checked-in profile retains a null canonical overlay content hash because no
whole-image range has been proven. That structural overlay hypothesis is no
longer a required selector. Protocol 1.4 supplied the accepted three-witness
field execution identity; protocol 1.5 binds it and the scene signals into a
scoped observation guard. Selection still fails closed when any
witness or scene/boundary signal is missing, stale, ambiguous, or mismatched.

## Actor-pool representation

The format distinguishes the owning storage from an observation index:

- `storage_kind`: linked actor nodes;
- `linked_list_head`: owning list locator;
- `pointer_census`: overlay-built filtered pointer table, stride and maximum;
- `actor_record.bounded_read_size`: maximum proven prefix;
- `actor_record.contiguous_stride`: null, because no fixed array stride is supported by evidence.

This prevents consumers from silently inventing `base + index*stride`. A profile with a non-null contiguous stride for this storage kind is rejected.

## Claims and unknowns

Addresses and fields carry lowercase provenance confidence values from the SDK contract. `unknown` values must be null. `contradictory` values must retain at least two alternatives. Class-dependent fields use neutral names until their writers/readers support a narrower meaning.

Evidence entries identify repository, pinned revision, path, symbol/function and role. They contain no disassembly, executable data, overlay data, RAM contents or local paths.

## Validator API

The standard-library validator provides:

- `load_profile(path)` and `validate_profile(document)`;
- `canonical_profile_json(document)` for stable serialization;
- `profile_identity(document)`;
- `validate_observation_context(profile, context)` for fail-closed selection and bounds;
- `establish_epoch(profile, before, after, observer_epoch)` for mixed-epoch rejection.

The validator performs no network access and no RAM reads. A future observer
supplies metadata from `protocol_info`, `runtime_identity`,
`observation_guard`, and guarded `read_regions`; it must reject an invalid,
unstable, or incompatible scoped token.

## Synthetic validation

The suite covers those structural checks plus missing, stale, and ambiguous
witnesses; backend/range/hash mismatches; watched-generation changes; scoped
guard mismatches; multi-witness completeness; protocol compatibility;
metadata-only identities; and the legacy unresolved-overlay failure mode.

All fixtures are synthetic or profile metadata. Retail bytes and runtime captures are not used.

## Observer policy

The profile now carries the client-visible pointer encoding, exact `0x9C`
prefix, `+0x00` next-pointer offset, two-sample stabilization rule, three-attempt
retry policy, and hard node/request/byte/time limits. The 128-node limit is a
confirmed safety policy rather than a claim about retail actor capacity.

Executable identity now preserves two distinct domains: the complete ISO file
hash used by disc provenance and the exact 440,320-byte `ps-x-exe-body` source
identity exposed by `runtime_identity`. Live selection requires the latter;
neither substitutes for the other.

The profile now requires protocol 1.5 and derives a scoped observation guard
from its existing scene signals, actor-list-head candidate, and three execution
witnesses. Stable town01 boundary-only sampling has been observed across fresh
launches. A transition-only client accepted a normal town0c round trip using a
metadata-only research selection derived from the field profile. A reviewed,
revisioned town0c profile is still required before actor traversal, which
remains fail closed.

## Live identity status

The protocol 1.4 native pass accepted three exact-instruction witnesses across
fresh launches and the natural field-scene replacement chain. The profile now
uses that repeatable field execution identity. The `0x801CE818` base remains a
research hypothesis and the null whole-overlay content hash remains unchanged;
neither is represented as the accepted identity. See
`field-execution-identity.md` and `field-overlay-0897-identity.md`.

The protocol 1.2 repeat retrieved all 562 registrations without response
overflow and explained duplicate static structural variants, but it still did
not expose an authoritative loaded image or active owner for overlay 0897.
Catalog success is not overlay acceptance, so no profile field changed.
