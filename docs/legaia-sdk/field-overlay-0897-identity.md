# Field overlay 0897 live-identity attempt

Validation date: 2026-07-19. Status: **not accepted**.

## Accepted boundary evidence

A fresh native runtime was advanced through normal controller input only. No
debugger RAM write, title-specific hook, actor traversal, or correlation was
used. Two-boundary `read_regions` samples agreed on:

- active scene name `town01`;
- runtime PROT base `3`;
- master game mode `3` (settled field mode);
- identical frame and executable-state stamps within each request.

This accepts the scene boundary but not an overlay identity.

## Executable-region findings

The researched load-base hypothesis `0x801CE818` did not appear as an
`executable_regions` base and was not contained by any reported exact code
range in three complete metadata scans.

The independently documented field function `0x801CF754` was covered by eight
registrations representing three distinct structural ranges:

| Guest base | Aggregate length | Duplicate registrations | Live/source match | Native valid | Active owner |
|---|---:|---:|---|---|---|
| `0x801CF3BC` | 4,084 | 5 | no | no | no |
| `0x801CF0D8` | 3,864 | 2 | no | no | no |
| `0x801CF470` | 3,360 | 1 | no | no | no |

Their metadata was stable across the three scans, but none described current
native ownership. Unaccepted source CRCs, live SHA-256 values, and watched-page
digests remain local and are not recorded in the profile.

The registration census grew from the main executable alone to 468 records as
normal game flow exercised static overlays. Natural lifecycle change was
visible through registration count and executable-state changes. It did not
leave the field-overlay records above dispatchable, so it cannot prove the
required current owner for overlay 0897.

## Protocol discrepancies exposed by retail acceptance

- `protocol_info` advertises up to 128 executable records per response, but a
  128-record request exceeded the 65,536-byte response buffer and returned
  `invalid executable registration`. Sixteen-record pages succeeded. The error
  conflates response capacity with registration validity.
- A complete 468-record census spans multiple requests. The process-local
  executable-state token includes watched generations for the canonical main
  image, whose data portion mutates during play, so it changed between pages.
  The discovery scans are therefore not claimed as atomic snapshots.
- The main executable source/live identities diverged after normal mutable data
  writes, making its conservative native-ownership projection false. This is
  fail closed, but it contributes token churn and needs a clearer observer
  contract before multi-page field selection.

## Decision

Overlay 0897 has no accepted canonical live range, length, source relationship,
live SHA-256, watched generation, or native owner. The revisioned layout profile
remains unchanged and fail closed.

The next safe prerequisite is a separately reviewed generic executable-region
representation/coverage correction that:

1. advertises a page size that always fits the response cap and reports
   response overflow distinctly;
2. permits a stable or explicitly revisioned multi-page ownership snapshot;
3. explains why the current town01 field code has no source-matching native
   owner, or builds/registers the correct static variant without weakening its
   byte guard.

Only then should this acceptance be repeated across stable samples and a second
fresh launch. Actor observation and correlation remain premature.

