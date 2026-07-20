# Debug protocol versioning

The PSXRecomp debug transport is newline-delimited JSON: one bounded request
line produces one bounded response line. Existing commands remain compatible.
Identity support is an additive protocol revision:

- name: `psxrecomp-debug`
- major: 1
- minor: 3

A major change may remove or reinterpret fields and is incompatible unless a
client explicitly supports it. A minor change may add commands, capabilities,
response fields, enum values, or larger limits. Clients must ignore unknown
response fields and discover optional behavior from `capabilities`, not from a
server-kind guess.

## `protocol_info`

`{"cmd":"protocol_info"}` is available without guest assets. It returns the
protocol version, explicit server kind, deterministically sorted capabilities,
limits, and the current frame. Capability names are stable lowercase tokens.

The native server advertises:

- `executable_catalog`
- `executable_image_lifecycle`
- `executable_regions`
- `read_ram`
- `read_regions`
- `runtime_identity`
- `watched_page_generation`

An oracle advertises only mechanisms it can implement truthfully. In
particular, bounded RAM reads do not imply knowledge of PSXRecomp native
registration ownership.

Beetle and DuckStation advertise `read_ram` and `read_regions`. Their
`read_regions` responses carry frame stamps but no executable-state token.
DuckStation's checked-in patch is regenerated against upstream
`ffb33c281d196eb8ee0f559085ca285de7cdd51b`.

## Bounds

The v1.1 native limits are:

| Limit | Value |
| --- | ---: |
| Request line, including JSON but excluding newline | 8,191 bytes |
| Existing `read_ram` payload | 2,097,152 bytes |
| `read_regions` entries | 32 |
| One `read_regions` entry | 4,096 bytes |
| Aggregate `read_regions` payload | 16,384 bytes |
| `read_regions` response | 65,536 bytes |
| `executable_regions` records per page | 8 default, 8 maximum |
| `executable_catalog` records per page | 8 default, 8 maximum |
| `executable_lifecycle` records per page | 8 default, 8 maximum |

An overlong request, malformed range, overflow, or response-budget violation
fails closed with the existing `{id,ok:false,error}` envelope. Unsupported
commands continue to return `unknown command`.

## Compatibility rules

An observer must reject a different protocol name or unsupported major. It may
accept a newer minor only when every required capability is present. A missing
identity field is not a wildcard: a revisioned observer must fail closed.

Protocol responses contain no host paths. Runtime build identity is a source
revision, not a binary path. Program and executable identities contain hashes
and guest ranges, never executable bytes.

Build and acceptance evidence for this revision is recorded in
`docs/debug-observer-validation.md`. Protocol 1.2 adds the bounded, token-bound
catalog described in `docs/executable-catalog-pagination.md`. Protocol 1.3 adds
bounded image lifecycle and exact-PC execution-owner observations described in
`docs/executable-lifecycle-protocol.md`; older clients and commands remain
valid. Protocol 1.4 adds the bounded exact-instruction `execution_witness`
command described in `docs/execution-witness-protocol.md`; it is additive and
is advertised only by backends with authoritative ownership and watched-page
generation semantics.
