# Executable identity and generation contract

PSXRecomp distinguishes immutable compiled source from current guest RAM. A
source match is necessary for native ownership; the existence of a DLL or
static function is not sufficient.

## Runtime and program identity

`runtime_identity` reports the native runtime revision, server kind, guest
architecture, BIOS identity, configured program serial, main executable guest
base, canonical source length, immutable source SHA-256, and current frame.
Fields unavailable on a backend are omitted rather than guessed.

The main-executable source hash covers exactly the body bytes registered by the
text-image guard:

- the 2,048-byte PS-X EXE header is excluded;
- only bytes present in the source file or disc EXE are included;
- a config-only page-rounded analysis tail is excluded;
- BSS and other zero-filled RAM are excluded;
- later guest mutations, relocation, and runtime patches are excluded.

The current live hash covers the same physical base and canonical source
length in main RAM. This makes source and live identities directly comparable
without hashing arbitrary RAM. Intentional reference-image blessings do not
rewrite the stored immutable source hash.

## Authoritative watched generation

Main RAM has 512 4-KiB pages. `memory.c` owns one unsigned 32-bit generation per
watched page. Executable registration sets watch bits. Ordinary byte, halfword,
and word guest stores call the single RAM-write chokepoint; DMA and CD transfers
use those stores and therefore advance watched generations. Debugger writes use
the same guest store API. A same-byte write still advances generation.

The counter is per page, not per region. It wraps modulo 2^32. The existing
overlay dispatch cache stores the sum of generations across its code pages;
that sum is an internal fast-path key and is not claimed to be a unique or
monotonic region generation.

The observer-facing `watched_generation` is SHA-256 over this canonical stream:

1. ASCII domain `psxrecomp-watch-v1`;
2. each distinct covered page in ascending physical-page order;
3. each page index as little-endian u32;
4. its current generation as little-endian u32.

The response also states page size, first page, page count, and the legacy sum.
The digest is process-local state: it is not stable across restarts and is not
an allocation generation.

### Implementation audit

The protocol is a view of the existing runtime mechanism, not a second
generation system:

| Concern | Authoritative implementation |
|---|---|
| Watch registration | `overlay_watch_set_range` in `runtime/src/memory.c`; called by main-text registration, dynamic candidate registration, and `psx_overlay_static_code_matches` |
| Page state | `overlay_watched_pages[512]` and `overlay_page_gen[512]` in `runtime/src/memory.c` |
| Guest-store mutation | `overlay_watch_note_write`, before the RAM mutation in the byte/half/word raw store paths |
| DMA and CD transfer | `runtime/src/dma.c`; to-RAM words, including CD DMA, use `psx_write_word` |
| Debugger mutation | `handle_write_ram` in `runtime/src/debug_server.c` uses `psx_write_byte` |
| Dynamic validation | `cand_gensum`, `cand_crc`, candidate `val_gen`, and the dispatch checks in `runtime/src/overlay_loader.c` |
| Static validation | `psx_overlay_static_code_matches` and `StaticMatchCache.gen_sum` in `runtime/src/overlay_loader.c` |
| Main executable guard | `dirty_ram_register_text_image` and `dirty_ram_text_native_ok` in `runtime/src/memory.c` |
| Observer projection | `watched_generation_digest` and `executable_state_token` in `runtime/src/debug_server.c` |

There is no overlay-unload operation in the current loader: loaded DLL images
and registrations are retained, while current live bytes and dispatch guards
decide eligibility. Same-address replacement advances watched page state; a
registration does not remain native-valid merely because its address and length
are unchanged. An unchanged-byte write also advances the page generation, then
may revalidate successfully against the unchanged final hash.

## Mutation coverage and limitations

- CPU stores: covered at byte, halfword, and word widths.
- DMA/CD transfers: covered because DMA writes through `psx_write_word`.
- Debugger writes: covered because `write_ram` uses `psx_write_byte`.
- Main executable: the registered source-image range participates in watched
  generation tracking.
- Runtime overlay candidates: every exact manifest/JIT code range is watched.
- Static overlay variants: the reconciled matcher watches every exact range
  before sampling generation.
- Dirty executable pages: writes participate when a native/static registration
  watches the page; dirty-page identity remains separately observable.
- State restoration and diagnostic shadow copies can replace RAM directly.
  These are not ordinary guest execution. A future general save-state restore
  API must explicitly notify the memory generation layer before it can be used
  by a live observer.

## Executable regions

`executable_regions` is deterministic and paged in registration order. It may
contain:

- the canonical main executable;
- statically compiled overlay variants that have actually reached their byte
  guard;
- loaded native overlay candidates;
- runtime-compiled candidates;
- authoritatively executed dirty RAM pages where represented.

Each record includes structural guest ranges, source and live identities,
watched generation, backend, source-match state, and conservative native
validity. Multiple contents at the same address remain distinct because source
identity and registration identity are included. IDs are deterministic only
within one runtime process unless explicitly stated otherwise.

Native validity requires a live source match, a non-blacklisted registration,
current generation validation, enabled native execution, and applicable
dispatch guards. Unknown or mixed validity is reported conservatively and must
not be promoted by clients.

## Executable-state token

The lightweight state token is SHA-256 over the domain
`psxrecomp-exec-state-v1`, the complete ordered page-generation array, main
source identity/range, and overlay registration-state digest. It changes on
watched executable writes, registration changes, blacklist/ownership changes,
or native enable-state changes. It is process-lifetime scoped and is not a
separate counter. SHA-256 collision resistance is assumed; no persistence or
cross-process ordering is promised.

## Retail acceptance limitations

The 2026-07-19 native acceptance found two constraints not covered by the
synthetic contract. First, the advertised 128-record page can exceed the
65,536-byte response cap for ordinary static-overlay records; 16-record pages
worked, but clients must currently use a conservative page size and treat
`invalid executable registration` as ambiguous until the server distinguishes
capacity from invalid metadata. Second, the state token covers the watched
pages of the whole canonical main image. Mutable data inside that image can
advance generations continuously during play, so token equality across a
multi-request census is not currently guaranteed.

Neither limitation permits a client to ignore a token mismatch or promote a
non-matching registration to native ownership. See
`docs/legaia-sdk/field-overlay-0897-identity.md`.
