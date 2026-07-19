# Legaia runtime layout profile contract

The v1 profile is a deterministic, metadata-only description of a supported runtime revision. It is stored at `integrations/legaia/layouts/scus94254-na-field-v1.json` and validated by both JSON Schema and `integrations.legaia.layouts.validator`.

## Identity and selection

`profile_id` is stable and revisioned: `legaia-na-scus94254-field-v1`. Schema version and profile version are separate. An incompatible format change increments `schema_version`; a new executable, overlay layout or materially different field mapping gets a new profile ID/file.

Selection is fail closed. A consumer must match:

1. executable serial and SHA-256;
2. advertised runtime protocol name/version and required capabilities;
3. every required overlay identity, load address and canonical content hash;
4. every required scene signal;
5. main-RAM bounds, pointer-census stride and count;
6. scene-epoch boundary samples.

The checked-in profile intentionally has a null canonical overlay content hash. Protocol 1.1 can now supply source/live identities and watched-generation state, but the canonical field-overlay range/hash has not yet been accepted into this profile. It therefore validates as research metadata but cannot select a live runtime. This is a safety feature, not an incomplete validator.

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

The validator performs no network access and no RAM reads. A future observer supplies metadata from `protocol_info`, `runtime_identity`, `executable_regions`, and `read_regions`; it must require the advertised capabilities and reject unstable frame/executable-state stamps.

## Synthetic validation

The suite covers schema validation, stable identity, supported/unsupported executable selection, overlay mismatch, missing scene signals, actor-base bounds, pointer stride, slot-count overflow, 32-bit wraparound, field bounds, duplicate offsets, contradictory/unknown claims, epoch invalidation, duplicate overlays, deterministic serialization, proprietary-payload rejection and unresolved-overlay fail-closed behavior.

All fixtures are synthetic or profile metadata. Retail bytes and runtime captures are not used.

## Live identity status

The 2026-07-19 native pass accepted startup, protocol negotiation, and the
multi-signal town01 boundary, but did not find an authoritative native owner for
field overlay 0897. The `0x801CE818` base remains a research hypothesis, not an
accepted executable-region identity. The null overlay content hash and
fail-closed selection remain unchanged. See `field-overlay-0897-identity.md`.
