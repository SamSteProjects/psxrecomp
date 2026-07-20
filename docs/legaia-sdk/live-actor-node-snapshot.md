# Live actor-node snapshot format

Status: schema and synthetic implementation accepted; no retail snapshot has
been accepted.

`integrations/legaia/schemas/runtime-observation.v1.schema.json` defines a
metadata-only historical observation. It contains profile/protocol/runtime
identity, one observer epoch, scene signals, witness results, a complete actor
chain, before/after boundaries, metrics, diagnostics, and explicit unknowns.

## Traversal safety

The profile drives every address and limit. The observer:

- reads the list-head global as a little-endian KSEG0 pointer;
- validates alignment, main-RAM bounds, and `address + 0x9C` overflow;
- dereferences only confirmed `next_actor` at `+0x00`;
- reads exactly 156 bytes per candidate node;
- tracks visited addresses and rejects self-loops and cycles;
- rejects node, request, aggregate-byte, and wall-clock limits;
- rejects truncated responses and partial traversal; and
- never scans RAM or uses the collision census as actor identity.

The 128-node ceiling is an observer safety bound, not a runtime actor-count
claim. The maximum candidate payload is 19,968 bytes across at most 128
one-node requests.

## Field output

Fields are generated from `actor_fields` in the profile. Confirmed safe scalar
fields include flags, signed X/Y/Z, and 4096-unit heading. Pointer-like fields
report raw value, null/alignment/main-RAM status, unknown executable-range
membership, and `dereferenced: false`. Model, animation, tick, script, and
collision pointers are not followed.

Conditional `.MAP` fields remain applicability-unresolved for every node until
subclass evidence exists. `field_0x50` and `field_0x94` retain neutral names,
Contradictory confidence, and their alternatives.

The schema forbids raw prefix payloads, RAM dumps, executable or BIOS bytes,
host/disc paths, dialogue, assets, screenshots, and save states. Runtime node
addresses and decoded numeric values are permitted structural metadata. No
importer JSON or correlation result is accepted as input.

The CLI is:

```powershell
python integrations/legaia/tools/legaia_observe.py `
  --host 127.0.0.1 `
  --port 4370 `
  --profile integrations/legaia/layouts/scus94254-na-field-v1.json `
  --output "<local-output>\town01-live-snapshot.json"
```

It produces one accepted historical observation or a bounded failure. It has
no continuous, write, force, scan, or correlation mode.
