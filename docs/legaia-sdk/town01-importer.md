# Read-only `town01` metadata importer

## Purpose and boundary

The first Legaia SDK vertical slice imports actor-placement metadata for Rim Elm's field scene, structurally named `town01`. It belongs entirely to `integrations/legaia` and does not alter PSXRecomp's runtime, hardware emulation, generated code, debug protocol or renderer. AndrewAltimit/legend-of-legaia-re is not required to run it.

The importer reads a user-supplied North American Mode 2/2352 disc image, looks up `PROT.DAT` and `CDNAME.TXT` through ISO9660, converts the CDNAME scene window into PROT extraction indices, finds the scene's MAN-bearing asset table, decompresses its type-3 MAN stream and decodes partition-1 actor placements. It writes metadata JSON only.

## Requirements and command

Python 3.11 or newer is sufficient; there is no build or third-party package step.

```powershell
python integrations/legaia/tools/legaia_import.py `
  --disc "C:\path\to\Legend of Legaia.bin" `
  --scene town01 `
  --output "C:\local-output\imported-town01.json"
```

A `.cue` may be passed when it names one binary track. The supported image is the North American `SCUS-94254` Mode 2/2352 build. The importer verifies both the ISO serial-file marker and the published whole-image SHA-256. It does not read or embed executable bytes in its output.

Outputs should be written outside the repository. Local output/cache/disc patterns under `integrations/legaia` are ignored as an additional safeguard.

## Output contract

The schema is `integrations/legaia/schemas/town01-import.schema.json`. Its top level contains:

- `schema_version` and `importer_version`;
- `source`, with the exact disc digest, supported build, scene label, tool version and pinned reference revision;
- `scene`, with its structural identity and MAN partition counts;
- `actors`, one entry for every readable partition-1 actor record after controller record zero;
- `diagnostics` and explicit `unresolved` questions.

No timestamp is emitted. Objects are sorted by key and actors remain in structural MAN record order, so identical disc and tool versions produce byte-identical JSON. A runtime metadata-only validator rejects binary values and fields conventionally used for payloads, sectors, meshes, textures and dialogue.

## Stable actor identity

An actor ID is derived only from scene, MAN partition and partition-relative record index:

```text
scene://town01/actors/man-p1/0001
scene://town01/actors/man-p1/0002
```

Partition-1 record zero is the scene controller, so the first actor is record one. IDs do not contain guessed names, model names, decoded text, runtime addresses, actor slots, absolute paths or filtered display order.

## Claims and confidence

Every exposed semantic relationship has a claim containing `property`, `value`, `confidence`, `evidence`, `source` and `notes`. JSON uses the approved provenance document's lowercase serialized values: `confirmed`, `strongly_inferred`, `tentative`, `unknown` and `contradictory` (displayed as Confirmed, Strongly Inferred, Tentative, Unknown and Contradictory).

This slice emits:

- confirmed record provenance and byte span in the decoded-MAN coordinate space;
- confirmed X/Z position and tile coordinates using the retail placement formula;
- unknown Y and rotation/facing, because those are not present in the confirmed placement prefix;
- confirmed model pool/index selection, including the `0xF0` special-pool threshold;
- unknown referenced model asset record, because the scene/global TMD pools do not yet have stable asset IDs here;
- confirmed raw animation-record ID semantics, without resolving or exporting animation assets.

Exact record bounds use the next higher record or MAN-section offset across all partitions. Conflicting active values are retained and normalized to `contradictory`; exact duplicate claims are removed.

## Attribution and independent evidence

The reference manifest at `integrations/legaia/provenance/reference-manifest.json` pins AndrewAltimit/legend-of-legaia-re commit `d6e64c68ede25813d35db20980da82a1a025549b`. For each adapted interpretation it names the source files, documentation, functions/types, evidence, independently implemented behavior and differences.

The implementation was written independently for PSXRecomp and is narrower than the reference: read-only ISO/PROT/CDNAME, count-6/count-7 scene tables, LZS decode, and MAN placement metadata only. The reference repository is an attributed development reference and optional parity oracle, never a submodule, Cargo/Python dependency, subprocess or shipped component.

For optional local parity work, run this importer and Andrew's viewer/tooling separately against the same user-owned disc, then compare only scene identity, actor record indices, model pool/index and X/Z placement metadata. Keep all raw and normalized outputs in ignored local directories. Parity is supplemental; the claims above cite parser spans and retail/runtime evidence independently.

## Testing

Run the synthetic suite with:

```powershell
python -m unittest discover integrations/legaia/tests -v
```

The disc test skips in normal CI. Opt in locally:

```powershell
$env:LEGAIA_DISC_BIN = "C:\path\to\Legend of Legaia.bin"
python -m unittest discover integrations/legaia/tests -v
```

The gated test checks only non-proprietary invariants: successful scene resolution, nonzero and unique actor identities, bounded source spans, deterministic metadata and the metadata-only policy. It never saves extracted bytes.

## Legal and data handling

Users must supply a legally obtained disc. Never commit disc images or sectors, executable bytes, PROT entries, MAN blobs, models, textures, dialogue, RAM snapshots, generated proprietary game code or user-specific paths. The JSON output is designed to contain structural metadata only, but remains ignored by default until intentionally reviewed.

## Unresolved and next step

The importer intentionally leaves vertical position, initial facing, script-derived movement, stable model asset-record identity, interaction/dialogue/story relationships and runtime correlation unresolved. It performs no writes and cannot rebuild or patch a disc.

The approved follow-on read-only inspection surface now lives at `integrations/legaia/inspector`; see `town01-inspector.md`. The next separately approved slice is a read-only PSXRecomp observation bridge and revisioned Legaia layout profile, still without RAM writes or generic runtime title checks.
