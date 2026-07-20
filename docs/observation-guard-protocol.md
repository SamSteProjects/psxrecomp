# Observation guard protocol

`psxrecomp-debug` 1.5 adds the native `observation_guard` capability and an
optional `guard` object on `read_regions`. The extension is additive: unguarded
`read_regions` and all older commands retain their previous behavior.

## Limits

The native server advertises the authoritative values in `protocol_info`:

| Limit | Value |
|---|---:|
| Guard RAM regions | 16 |
| Bytes per guard RAM region | 256 |
| Aggregate guard RAM bytes | 2,048 |
| Guard execution witnesses | 8 |

The existing request-line, response-line, and `read_regions` limits also apply.

## Descriptor

```json
{
  "ram_regions": [
    {"key": "scene_name", "addr": 2147487744, "len": 8}
  ],
  "execution_witnesses": [
    {"pc": 2148000000, "require_current": true}
  ],
  "expected_token": "guard-..."
}
```

`expected_token` is optional for the first sample. Keys must be unique;
addresses and lengths are decimal JSON integers; and `require_current` must be
true. The server sorts descriptor entries canonically before hashing while a
guarded `read_regions` preserves the requested payload-region order.

## `observation_guard`

The response includes before/after scoped tokens, frame stamps, `valid`,
`stable`, and `compatible` results, bounded evidence summaries, and the global
executable-state/component stamps as diagnostics. It returns hashes and
structural metadata, never guarded bytes.

## Guarded `read_regions`

When `guard` is supplied, the server derives a token before reading and again
after reading. Payload regions are emitted only if both samples are valid, the
tokens match, and an optional expected token matches. A failed guard is a
fail-closed response; clients must discard the complete attempt.

Frame stamps remain observational. Frame advancement alone does not invalidate
a guard. The global executable-state stamps are also retained but are not the
profile-scoped acceptance boundary.

## Backend support

The native server provides full support. DuckStation and Beetle do not
advertise `observation_guard` because they cannot expose equivalent watched-page
and execution-owner evidence truthfully. Profiles requiring the capability
must reject those servers.
