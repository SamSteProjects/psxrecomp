# Existing actor initial model and animation assignments

`importer/man_assignments.py` provides a private, bounded patch helper for an
existing MAN actor's initial model/animation pair. It is independent of the
editor, project schema, package build service and runtime. Those integrations
are not implied by this helper. It creates no actor and writes no RAM or disc.

## Encoding and pinned evidence

Research reference: `AndrewAltimit/legend-of-legaia-re`, commit
`d6e64c68ede25813d35db20980da82a1a025549b`, read directly from local Git objects.
No reference code or retail data is copied into the runtime.

| Reference source | Git blob | Evidence |
|---|---|---|
| `crates/asset/src/man_section.rs` | `42086e2cf5690dc6958f47f5bbc033894a196d14` | `actor_placement` reads local-count prefix, model and animation bytes; `ActorPlacement::anim_id` documents scene ANM record-plus-one and distinct global association. |
| `crates/web-viewer/src/field_npc.rs` | `331809a531f6caa22956eb796edc275fbde77829` | Existing placements resolve through the scene TMD pool; special models use the global pool. Object-local meshes require corresponding rigid ANM channels. |
| `crates/engine-core/src/scene_resources.rs` | `44d6317ce816335389fff05574a4fccbd6b1df18` | Scene TMDs lead the structural model pool; shared head models use the separate special index range. |

Partition1 record0 is the scene controller and is not assignable. For each
existing actor record1..N, the prefix is one local-count byte, two bytes per
local, then four header bytes. At `record_offset + 1 + 2*local_count`:

| Offset | Meaning |
|---|---|
| +0 | Model selector; below240 indexes the scene TMD bank. |
| +1 | Initial animation selector; nonzero indexes scene ANM record byte-minus-one. |
| +2, +3 | X/Z placement bytes, preserved by this helper. |

The remaining script begins after these four bytes and is preserved exactly.
Model selectors240..255 change to the global pool and set actor flag0x1000000;
their animation bank is PROT0874 rather than the scene descriptor. This helper
rejects them, including changes originating from a global actor. It also rejects
zero-animation originals/targets rather than inventing a rigid pose or changing
draw-mode assumptions.

## API and composition

```python
context = load_man_assignment_context(verified_disc_path, "town01")
choices = context.options(record_index)
decoded, audit = context.patch({record_index: {
    "model_index": selected_pair["model_index"],
    "animation_id": selected_pair["animation_id"],
}})
encoded_span, audit, sizes = context.serialize(edits)
```

The loader hashes/verifies the supported disc within one `_disc_context`,
requires exactly one bounded MAN and scene ANM descriptor, constructs the model
bank from parsed TMD records and retains a request-scoped private source snapshot.
Callers must not construct contexts from HTTP metadata. `provenance()` returns
source hashes/locators and limitations, never payload bytes. `options()` returns
supported donor pairs or an explicit unsupported reason.

Every changed assignment must name a pair present in another existing source
record (the unchanged own pair also remains valid). The source and target models
must resolve in the same scene bank, have equal object counts, and both selected
ANM records must fully decode with exactly that channel count. Record aliases
across any MAN partition are rejected. All edits are validated before any result
is published; rejection leaves the immutable baseline untouched.

Audit entries contain the source decoded MAN hash, structural actor index, exact
decoded offset, original/replacement byte, target pair and donor record indices.
`patch(..., original=...)` optionally requires exact baseline equality. To combine
position edits later, apply assignments to the verified baseline first, then
`patch_man_positions` to the returned decoded bytes, and run one capacity check
after the final encoding. A client-supplied edited buffer is not a source guard.

`serialize()` independently decodes its output and requires the replacement to
fit the originally consumed compressed span. It preserves unused trailing bytes
inside that span, returns the original encoded bytes for a no-op, and rejects
growth instead of relocating subsequent descriptors.

## Compatibility limits

These checks establish initial-header encoding and structural resource bounds.
They do not prove NPC behavior compatibility. Scripts can replace the initial
model or animation, select later clips, address object indices, or set collision
and story state. Equal object counts do not establish anatomical channel meaning,
visual suitability, collision dimensions or script assumptions. The audit labels
script compatibility `unverified`; a future editor must preserve that distinction.

Only the existing pair is borrowed. Locals, script bytes, entity identity,
placement, flags, text, texture resources and animation records are unchanged.
No new model imports, arbitrary clip combinations, global-bank remapping or
native spawning are supported.

## Validation

`test_importer_man_assignments.py` covers exact two-byte changes, composable
position edits, original compressed no-op, full independent decode, invalid
indices/types, unsupported and invented pairs, multi-edit rejection without
partial mutation, aliased records, object/channel mismatches, copied metadata,
and actual compressed growth (63 original bytes versus64 after a valid patch).

An opt-in private retail test (`LEGAIA_DISC_BIN`) verifies an alternative town01
donor pair and its equal-span encoding. The 2026-09-09 local check changed actor5
from model112/animation57 to the existing actor40 pair model92/animation9. Only
decoded offsets4856 and4857 changed. The45338-byte MAN re-encoded to24890 bytes
inside its24894-byte original span and decoded back exactly. Actor1 correctly
remained unsupported because its initial animation selector is zero.

Seven focused tests passed with the private retail test enabled. No generated
payload was written or committed; the ignored evidence file is
`local-output/sdk-20260909/man-assignment-helper-evidence.json`. This candidate
assignment has not been run in the game, and no behavior or visual acceptance is
claimed.
