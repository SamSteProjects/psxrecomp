# Executable image model

PSXRecomp's observer model separates objects that the legacy
`executable_regions` response combined. This distinction is generic and is not
based on any game's scene or overlay numbering.

## Object hierarchy

1. A **loaded executable image** is a source/load event or a conservative image
   group. Examples are the main PS-X EXE, a native overlay bundle, and a static
   overlay variant. An image identity does not by itself grant dispatch
   ownership.
2. A **structural range** is one exact bounded guest-memory range associated
   with an image. Ranges may overlap. Address proximity is never a grouping
   rule.
3. A **dispatch registration** is one static-native, cached-native, or
   runtime-native candidate and its exact validation ranges. Registrations that
   differ in source, backend, generation, validation, or ownership remain
   separate even when their ranges are identical.
4. **Native ownership** means that a registration passes every current dispatch
   predicate and is the candidate dispatch would select for its entry.

The catalog also keeps three identity domains separate:

- **immutable source identity**: the content or cache key used to build a
  registration or image;
- **registration-time validated identity**: the exact registration-range CRC
  that has previously passed the dispatch byte guard, plus its validation
  generation when available; and
- **current live identity**: SHA-256 over only the current guest bytes in the
  registration's ordered exact ranges.

The SHA-256 values are diagnostics. Dispatch continues to use its existing CRC
and watched-page guards.

## Grouping contracts

Native DLL registrations use the loader's cache-image identity (load base and
captured image CRC) as their image group. That image CRC covers a captured-image
domain, while child registrations cover exact function ranges; the catalog
therefore marks the image source as not directly comparable to child live
hashes.

Static registrations do not have an authoritative guest overlay-load object.
They are grouped as `static-overlay-variant` by the expected CRC and exact
ordered range set passed by generated dispatch code. Repeated cache slots with
the same structural identity remain distinct registrations but share one image
and range group. Their `load_base` is null. This is a structural variant group,
not proof of a loaded image base or length.

Runtime-compiled candidates use their exact registration source identity and
range set. Dirty executable RAM without an authoritative native registration
is not invented as a catalog image; the main executable reports that its
per-dispatch ownership is not cataloged.

IDs and ordering are deterministic within one catalog. They are diagnostic
structural IDs and are not promised as cross-process semantic identities.

## Fail-closed interpretation

Observers must select an image, range, and registration using all required
identity fields. A source hash, live hash, watched generation, or overlapping
address alone is insufficient. Missing image lifecycle metadata remains
explicitly unresolved rather than being inferred from neighboring addresses.
